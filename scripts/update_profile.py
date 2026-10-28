#!/usr/bin/env python3
"""Automatically updates the Recently Updated Public Projects table in README.md."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

USERNAME = "spelech"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def fetch_public_repos() -> list[dict]:
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed&direction=desc"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "spelech-profile-updater",
            **(
                {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
                if os.environ.get("GITHUB_TOKEN")
                else {}
            ),
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        repos = json.loads(resp.read().decode("utf-8"))
    return [
        r
        for r in repos
        if not r.get("private")
        and not r.get("fork")
        and not r.get("archived")
        and r.get("name") != USERNAME
    ]


def build_recent_table(repos: list[dict], limit: int = 8) -> str:
    lines = [
        "| Repository | Primary Stack | Docs | Last Push (UTC) | Description |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]
    for r in repos[:limit]:
        name = r["name"]
        url = r["html_url"]
        lang = r.get("language") or "Multi"
        pushed = (r.get("pushed_at") or "")[:10]
        desc = (r.get("description") or "").replace("|", "\\|")
        homepage = (r.get("homepage") or "").strip()
        docs_cell = f"[Docs]({homepage})" if homepage else "—"
        lines.append(
            f"| **[{name}]({url})** | `{lang}` | {docs_cell} | `{pushed}` | {desc} |"
        )
    return "\n".join(lines)


def main() -> None:
    repos = fetch_public_repos()
    table_md = build_recent_table(repos)
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(<!-- RECENT_ACTIVITY:START -->).*?(<!-- RECENT_ACTIVITY:END -->)",
        re.DOTALL,
    )
    updated = pattern.sub(rf"\1\n{table_md}\n\2", content)
    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")
        print("Updated README.md with latest activity.")
    else:
        print("README.md is already up to date.")


if __name__ == "__main__":
    main()
