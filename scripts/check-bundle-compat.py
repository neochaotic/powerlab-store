#!/usr/bin/env python3
"""
check-bundle-compat.py — verify every Apps/<id>/docker-compose.yml will
survive the bundle-store.sh format conversion and produce a valid
x-powerlab block readable by PowerLab core's app-management backend.

This is the store↔core contract test. It runs on every PR so that format
regressions are caught before they reach bundle-store.sh at release time.

Conversion rules mirrored from scripts/bundle-store.sh:
  title:   flat string      → {en_us: string}   (must be non-empty string)
  tagline: flat string      → {en_us: string}   (must be non-empty string)
  port_map: list of objects → "host_port"        (must have ≥1 http/https entry,
                                                   OR headless: true)
  icon:    {file: ...}      → raw.githubusercontent URL  (file must exist on disk)

Exit 0 — all apps compatible
Exit 1 — one or more apps would fail conversion
"""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
APPS = ROOT / "Apps"


def check_app(compose_path: Path) -> list[str]:
    """Return list of error strings for this app (empty = OK)."""
    app_id = compose_path.parent.name
    errors: list[str] = []

    try:
        doc = yaml.safe_load(compose_path.read_text())
    except Exception as e:
        return [f"yaml parse error: {e}"]

    xp = doc.get("x-powerlab")
    if not isinstance(xp, dict):
        return ["missing x-powerlab block"]

    # title: must be a plain string so conversion wraps it
    title = xp.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append(
            f"title must be a non-empty flat string for bundle conversion; got {type(title).__name__!r}"
        )

    # tagline: same
    tagline = xp.get("tagline")
    if not isinstance(tagline, str) or not tagline.strip():
        errors.append(
            f"tagline must be a non-empty flat string for bundle conversion; got {type(tagline).__name__!r}"
        )

    # port_map: must yield a host port after conversion, OR headless
    headless = bool(xp.get("headless"))
    pm = xp.get("port_map")
    if not headless:
        if not isinstance(pm, list) or not pm:
            errors.append(
                "port_map must be a non-empty list (or headless: true)"
            )
        else:
            http_ports = [
                e for e in pm
                if isinstance(e, dict)
                and (e.get("protocol") or "http").lower() in ("http", "https")
                and e.get("host")
            ]
            if not http_ports:
                errors.append(
                    "port_map has no http/https entry with a host port — "
                    "bundle conversion would produce empty port_map"
                )

    # icon: must be {file: ...} with an existing file on disk
    icon = xp.get("icon")
    if not isinstance(icon, dict):
        errors.append(
            f"icon must be a dict with a 'file' key for bundle conversion; got {type(icon).__name__!r}"
        )
    else:
        icon_file = icon.get("file")
        if not icon_file:
            errors.append("icon.file is empty")
        else:
            icon_path = compose_path.parent / icon_file
            if not icon_path.is_file():
                errors.append(
                    f"icon.file={icon_file!r} does not exist on disk "
                    f"(bundle-store.sh builds the icon URL from this filename)"
                )

    return [f"{app_id}: {e}" for e in errors]


def main() -> int:
    if not APPS.is_dir():
        print("ERROR: Apps/ directory not found", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    checked = 0

    for compose_path in sorted(APPS.glob("*/docker-compose.yml")):
        errs = check_app(compose_path)
        all_errors.extend(errs)
        checked += 1

    if all_errors:
        print(f"FAIL: {len(all_errors)} bundle-compat error(s) in {checked} apps:\n")
        for e in all_errors:
            print(f"  {e}")
        print(
            "\nThese apps would produce invalid output when bundle-store.sh converts them "
            "for PowerLab core. Fix the x-powerlab block to match the store schema."
        )
        return 1

    print(f"OK: {checked} apps are bundle-compatible with PowerLab core")
    return 0


if __name__ == "__main__":
    sys.exit(main())
