#!/usr/bin/env bash
# build-index.sh — generate index.json from Apps/.
#
# index.json is the catalog manifest consumed by PowerLab core (and any
# other compatible runtime). It carries:
#   - schema version
#   - store version (read from VERSION file or first CLI arg)
#   - min_powerlab_version (compat protocol)
#   - per-app summary derived from x-powerlab blocks
#   - sha256 of each docker-compose.yml + icon
#
# Run pre-release; commit the generated index.json in the same release
# commit. (No tarball — operators / core pull raw files from
# raw.githubusercontent.com or shallow-clone the tag.)
#
# Requires: python3 (uses scripts/validate.py's yaml + json deps).
#
# Usage:
#   ./scripts/build-index.sh                # uses VERSION file
#   ./scripts/build-index.sh 0.1.0          # explicit version
#
# Exit codes:
#   0 — index.json written
#   1 — validation failed (catalog has errors)
#   2 — invalid invocation

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  if [[ -f VERSION ]]; then
    VERSION="$(cat VERSION | tr -d '[:space:]')"
  else
    echo "ERROR: no VERSION file and no version argument given" >&2
    exit 2
  fi
fi

# Strip leading 'v' if present
VERSION="${VERSION#v}"

echo "Building index.json for store v${VERSION}"

# Re-validate before building (defense in depth — the index should never
# point at an invalid app)
python3 scripts/validate.py Apps/ >/dev/null

python3 - "$VERSION" <<'PYEOF'
import hashlib
import json
import sys
from pathlib import Path

import yaml

version = sys.argv[1]
apps_root = Path("Apps")

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

apps = []
for compose_path in sorted(apps_root.glob("*/docker-compose.yml")):
    app_dir = compose_path.parent
    app_id = app_dir.name
    compose = yaml.safe_load(compose_path.read_text())
    xp = compose.get("x-powerlab", {}) or {}

    icon_path = None
    for candidate in ("icon.svg", "icon.png"):
        p = app_dir / candidate
        if p.is_file():
            icon_path = p
            break

    entry = {
        "store_app_id": xp.get("store_app_id", app_id),
        "title": xp.get("title", ""),
        "tagline": xp.get("tagline", ""),
        "category": xp.get("category", ""),
        "headless": bool(xp.get("headless", False)),
        "port_map": xp.get("port_map", []),
        "source": xp.get("source", {}),
        "icon": {
            "file": xp.get("icon", {}).get("file", icon_path.name if icon_path else ""),
            "license": xp.get("icon", {}).get("license", ""),
            "attribution": xp.get("icon", {}).get("attribution", ""),
            "sha256": sha256(icon_path) if icon_path else "",
        },
        "compose_sha256": sha256(compose_path),
        "arch": xp.get("arch", ["amd64", "arm64"]),
        "resource_hints": xp.get("resource_hints", {}),
    }
    apps.append(entry)

index = {
    "schema_version": "1",
    "store_version": version,
    "min_powerlab_version": "0.7.0",
    "apps_count": len(apps),
    "apps": apps,
}

Path("index.json").write_text(json.dumps(index, indent=2) + "\n")
print(f"Wrote index.json — {len(apps)} app(s)")
PYEOF
