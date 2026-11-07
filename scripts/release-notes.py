#!/usr/bin/env python3
"""Build GitHub Release notes from CHANGELOG.md + live HA OTBR upstream notes."""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UPSTREAM_CHANGELOG = (
    "https://raw.githubusercontent.com/home-assistant/addons/master/"
    "openthread_border_router/CHANGELOG.md"
)


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url, headers={"User-Agent": "hassio-otbr-matter-container-release-notes"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode()


def section(text: str, version: str) -> str:
    match = re.search(rf"(?m)^##\s+{re.escape(version)}\s*$", text)
    if not match:
        return ""
    body = text[match.start() :]
    lines = body.splitlines(keepends=True)
    out = [lines[0]]
    for line in lines[1:]:
        if line.startswith("## "):
            break
        out.append(line)
    return "".join(out).rstrip() + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} VERSION")
    version = sys.argv[1]
    local = ""
    changelog = REPO / "CHANGELOG.md"
    if changelog.exists():
        local = section(changelog.read_text(encoding="utf-8"), version)

    upstream = ""
    try:
        upstream = section(fetch(UPSTREAM_CHANGELOG), version)
    except Exception as error:  # noqa: BLE001 — best-effort for release body
        upstream = f"(Could not fetch upstream notes: {error})\n"

    parts: list[str] = []
    if local:
        parts.append(local.rstrip())
    else:
        parts.append(f"## {version}\n")
        parts.append(
            f"- OTBR base image bumped to `homeassistant/*-addon-otbr:{version}`.\n"
        )
    if upstream:
        parts.append("")
        parts.append("### Upstream (Home Assistant OTBR app)")
        parts.append("")
        # Drop the duplicate ## heading from upstream section
        up_lines = upstream.splitlines()
        if up_lines and up_lines[0].startswith("## "):
            parts.extend(up_lines[1:])
        else:
            parts.append(upstream.rstrip())
    parts.append("")
    parts.append("---")
    parts.append(
        f"Image: `ghcr.io/charlestephen/hassio-otbr-matter-container:{version}` "
        f"(also `:latest` on main builds)."
    )
    sys.stdout.write("\n".join(parts).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
