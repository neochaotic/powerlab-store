#!/usr/bin/env python3
"""
validate.py — security + schema gate for powerlab-store.

Run on every PR. Exits non-zero if any app violates the catalog posture
defined in docs/curation-criteria.md and docs/schema.md.

Per-app checks:
  Schema:
    - valid YAML, has top-level `services`
    - top-level `x-powerlab` block exists
    - x-powerlab.store_app_id matches the directory name
    - x-powerlab required fields present: title, tagline, category,
      port_map (or headless=true), source, icon, security
    - category is in the closed enum

  Files:
    - icon.svg OR icon.png present at app dir root
    - description.md present
    - NO *.sh file at ANY depth
    - NO hooks/ directory
    - NO exports.sh

  Compose hardening (grep-level — check-safety.sh runs the structured
  version):
    - no privileged: true
    - no docker.sock mount
    - no network_mode: host
    - no env_file:
    - no ipc: host / pid: host
    - no cap_add: ALL|SYS_ADMIN

  Image source trust:
    - every services.*.image has an `@sha256:` digest (strict day 1)
    - the image prefix is in the trusted-registry whitelist OR the PR
      adds it via a separate review path
    - no getumbrel/*, bigbear*, casaos* images
    - no :latest tag

  Compose command/entrypoint:
    - no curl|sh, wget|sh, bash -c '<inline>', eval, base64-pipe-bash

Usage:
  ./scripts/validate.py                # scan Apps/
  ./scripts/validate.py <path/to/Apps> # custom root
  ./scripts/validate.py --json         # machine-readable output

Exit codes:
  0  — all apps pass
  1  — one or more apps fail
  2  — invalid invocation
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "validate.py requires PyYAML. Install with: pip install pyyaml\n"
    )
    sys.exit(2)


# --------------------------------------------------------------------- config

CATEGORIES = {
    "AI & ML",
    "Database",
    "Developer",
    "Files & Sync",
    "Finance",
    "Media",
    "Network & VPN",
    "Productivity",
    "Smart home",
    "System",
}

REQUIRED_XPOWERLAB_FIELDS = {
    "store_app_id",
    "title",
    "tagline",
    "category",
    "source",
    "icon",
    "security",
}

# port_map is required UNLESS headless=true.

# Registry trust whitelist. A PR adding a new prefix needs explicit
# maintainer review (docs/curation-criteria.md "Allowed registries").
TRUSTED_REGISTRY_PREFIXES = (
    "docker.io/library/",
    "docker.io/nextcloud/",
    "docker.io/jellyfin/",
    "docker.io/homeassistant/",
    "docker.io/linuxserver/",      # alternative form
    "docker.io/grafana/",
    "docker.io/prom/",
    "docker.io/postgres",          # also docker.io/library/postgres
    "docker.io/redis",
    "ghcr.io/",                    # any verified GHCR org; PR review checks "verified"
    "lscr.io/linuxserver/",        # LinuxServer canonical
    "quay.io/",                    # any verified quay org; PR review checks "verified"
    "registry.k8s.io/",
    "gcr.io/distroless/",
    "mcr.microsoft.com/",
)

REJECTED_IMAGE_SUBSTRINGS = (
    "getumbrel/",
    "bigbear",
    "casaos",
)

# Compose-content RCE patterns.
RCE_PATTERNS = [
    (re.compile(r"\|\s*(sh|bash)\b"),        "pipe-to-shell (curl|sh, wget|bash)"),
    (re.compile(r"\b(bash|sh)\s+-c\s+['\"]"), "inline shell -c '...'"),
    (re.compile(r"\beval\s+"),                "eval"),
    (re.compile(r"base64\s+-d\s*\|\s*(sh|bash)"), "base64 | shell"),
    (re.compile(r"https?://\S+\s*\|\s*(sh|bash)"), "fetch | shell"),
]

# Hardening rejections (compose-level grep; check-safety.sh has the
# structured version).
HARDENING_REJECTIONS = [
    (re.compile(r"^\s*privileged:\s*true",      re.M), "privileged: true"),
    (re.compile(r"docker\.sock"),                       "docker.sock mount"),
    (re.compile(r"^\s*network_mode:\s*['\"]?host", re.M), "network_mode: host"),
    (re.compile(r"^\s*pid:\s*['\"]?host",       re.M), "pid: host"),
    (re.compile(r"^\s*ipc:\s*['\"]?host",       re.M), "ipc: host"),
    (re.compile(r"^\s*env_file:",               re.M), "env_file (forbidden)"),
    (re.compile(r"/DATA/AppData|\$AppID|\$\{?APP_DATA_DIR"),
                                                "unrewritten upstream volume path"),
]

ICON_MAX_BYTES = 100 * 1024  # 100KB


# --------------------------------------------------------------------- helpers


def is_trusted_image(image_path: str) -> bool:
    # image_path is the value of services.*.image, possibly with tag/digest
    base = image_path.split("@", 1)[0].split(":", 1)[0]

    # Normalize bare names to docker.io/library form
    if "/" not in base:
        base = f"docker.io/library/{base}"
    elif base.count("/") == 1 and not base.startswith(("ghcr.io/", "lscr.io/",
                                                       "quay.io/", "registry.k8s.io/",
                                                       "gcr.io/", "mcr.microsoft.com/",
                                                       "docker.io/")):
        # foo/bar → docker.io/foo/bar
        base = f"docker.io/{base}"
    elif base.startswith("docker.io/") and base.count("/") == 1:
        # docker.io/foo → docker.io/library/foo
        suffix = base.split("/", 1)[1]
        base = f"docker.io/library/{suffix}"

    return any(base.startswith(p) for p in TRUSTED_REGISTRY_PREFIXES)


def find_apps(root: Path) -> Iterable[Path]:
    return sorted(p for p in root.glob("*/docker-compose.yml") if p.is_file())


def validate_app(compose_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    app_dir = compose_path.parent
    app_id = app_dir.name
    raw = compose_path.read_text(errors="ignore")

    # YAML parse
    try:
        docs = list(yaml.safe_load_all(raw))
        compose = docs[0] if docs else None
    except Exception as e:
        errors.append(f"invalid YAML: {e}")
        return errors, warnings

    if not isinstance(compose, dict):
        errors.append("compose root is not a mapping")
        return errors, warnings

    if "services" not in compose:
        errors.append("no services block")

    # x-powerlab block
    xp = compose.get("x-powerlab")
    if not isinstance(xp, dict):
        errors.append("missing or invalid x-powerlab block")
        # Still run file + hardening checks so the report is complete.
        xp = {}

    # store_app_id matches dir
    if xp.get("store_app_id") and xp["store_app_id"] != app_id:
        errors.append(
            f"x-powerlab.store_app_id={xp['store_app_id']!r} "
            f"does not match directory name {app_id!r}"
        )

    # Required x-powerlab fields
    for f in REQUIRED_XPOWERLAB_FIELDS:
        if f not in xp:
            errors.append(f"x-powerlab.{f} missing")

    # category enum
    cat = xp.get("category")
    if cat and cat not in CATEGORIES:
        errors.append(
            f"x-powerlab.category={cat!r} is not in the closed enum "
            f"{sorted(CATEGORIES)}"
        )

    # port_map vs headless
    if not xp.get("headless") and not xp.get("port_map"):
        errors.append("x-powerlab.port_map missing (set headless:true if intentional)")

    # File checks
    has_svg = (app_dir / "icon.svg").is_file()
    has_png = (app_dir / "icon.png").is_file()
    if not (has_svg or has_png):
        errors.append("icon.svg or icon.png missing")
    else:
        icon_path = app_dir / ("icon.svg" if has_svg else "icon.png")
        if icon_path.stat().st_size > ICON_MAX_BYTES:
            errors.append(
                f"{icon_path.name} is {icon_path.stat().st_size} bytes > "
                f"{ICON_MAX_BYTES} cap"
            )

    if not (app_dir / "description.md").is_file():
        errors.append("description.md missing")

    if (app_dir / "hooks").is_dir():
        errors.append("hooks/ directory present (forbidden)")

    if (app_dir / "exports.sh").is_file():
        errors.append("exports.sh present (forbidden)")

    # Recursive .sh scan
    for sh in app_dir.rglob("*.sh"):
        errors.append(f"forbidden shell file present: {sh.relative_to(app_dir)}")

    # Compose-text grep — hardening
    for pat, label in HARDENING_REJECTIONS:
        if pat.search(raw):
            errors.append(f"compose contains: {label}")

    # Compose-text grep — RCE patterns in command/entrypoint
    services = compose.get("services") or {}
    if isinstance(services, dict):
        for svc_name, svc in services.items():
            if not isinstance(svc, dict):
                continue

            for key in ("command", "entrypoint"):
                val = svc.get(key)
                if val is None:
                    continue
                text = " ".join(val) if isinstance(val, list) else str(val)
                for pat, label in RCE_PATTERNS:
                    if pat.search(text):
                        errors.append(
                            f"services.{svc_name}.{key} contains forbidden "
                            f"pattern ({label}): {text!r}"
                        )

            # cap_add: ALL|SYS_ADMIN
            caps = svc.get("cap_add") or []
            if isinstance(caps, list):
                for c in caps:
                    if isinstance(c, str) and c.upper() in {"ALL", "SYS_ADMIN"}:
                        errors.append(
                            f"services.{svc_name}.cap_add contains {c} "
                            "(kernel-equivalent privileges)"
                        )

            # Image trust + pinning
            img = svc.get("image", "")
            if not img:
                errors.append(f"services.{svc_name} has no image")
                continue

            img_low = img.lower()
            for rej in REJECTED_IMAGE_SUBSTRINGS:
                if rej in img_low:
                    errors.append(
                        f"services.{svc_name}.image={img!r} matches rejected "
                        f"substring {rej!r}"
                    )

            # Digest pinning — strict day 1
            if "@sha256:" not in img:
                errors.append(
                    f"services.{svc_name}.image={img!r} is not digest-pinned "
                    "(run scripts/pin-digests.sh)"
                )

            # Latest tag
            tag_part = img.split("@", 1)[0]
            if ":" in tag_part:
                tag = tag_part.rsplit(":", 1)[1]
                if tag == "latest":
                    errors.append(
                        f"services.{svc_name}.image={img!r} uses :latest "
                        "(forbidden; pin a real tag + digest)"
                    )

            # Registry trust
            if not is_trusted_image(img):
                errors.append(
                    f"services.{svc_name}.image={img!r} is not from a trusted "
                    "registry (see docs/curation-criteria.md)"
                )

    # security.image_pin sanity
    sec = xp.get("security") or {}
    if isinstance(sec, dict):
        if sec.get("image_pin") == "REQUIRES-DIGEST-PIN":
            errors.append(
                "x-powerlab.security.image_pin is still REQUIRES-DIGEST-PIN "
                "(run scripts/pin-digests.sh and set to 'pinned')"
            )
        elif sec.get("image_pin") and sec["image_pin"] != "pinned":
            warnings.append(
                f"x-powerlab.security.image_pin={sec['image_pin']!r} "
                "(expected: 'pinned')"
            )
        if not sec.get("audit_notes"):
            warnings.append("x-powerlab.security.audit_notes is empty")

    return errors, warnings


# --------------------------------------------------------------------- main


def main(argv: list[str]) -> int:
    args = argv[1:]
    as_json = False
    if "--json" in args:
        as_json = True
        args.remove("--json")
    root = Path(args[0]) if args else Path("Apps")

    if not root.is_dir():
        sys.stderr.write(f"ERROR: not a directory: {root}\n")
        return 2

    apps = list(find_apps(root))
    if not apps:
        sys.stderr.write(f"INFO: no apps found under {root}\n")
        return 0  # empty catalog is valid; CI shouldn't fail on empty repo

    results = []
    total_errors = 0
    total_warnings = 0
    for compose in apps:
        errors, warnings = validate_app(compose)
        results.append(
            {
                "app": compose.parent.name,
                "errors": errors,
                "warnings": warnings,
            }
        )
        total_errors += len(errors)
        total_warnings += len(warnings)

    if as_json:
        print(json.dumps({
            "apps_scanned": len(apps),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "results": results,
        }, indent=2))
    else:
        print(f"Validated {len(apps)} app(s)")
        for r in results:
            if r["errors"] or r["warnings"]:
                print(f"\n[{r['app']}]")
                for w in r["warnings"]:
                    print(f"  WARN: {w}")
                for e in r["errors"]:
                    print(f"  FAIL: {e}")

        print(
            f"\nTotals: {total_errors} error(s), {total_warnings} warning(s) "
            f"across {len(apps)} app(s)"
        )

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
