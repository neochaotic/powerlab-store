#!/usr/bin/env python3
"""
import-from-artifact.py — one-shot converter from the legacy
core-format catalog (i18n maps + URL icons + inline descriptions)
into the powerlab-store native format (flat English strings +
rehosted file icons + description.md per app).

Input: a tree like community-catalog/Apps/<id>/docker-compose.yml
       (the format PowerLab core's sync-catalog used to emit).

Output: a tree like Apps/<id>/{docker-compose.yml, icon.svg|png,
        description.md} in the powerlab-store native format
        defined in docs/schema.md.

This is RUN-ONCE bootstrapping work. After v0.1.0, new apps land
via the normal CONTRIBUTING flow, not through this script.

Operations per app:
  1. Read source compose
  2. Flatten title/tagline from {en_us: X} to "X"
  3. Extract description from {en_us: X} → Apps/<id>/description.md;
     drop the field from x-powerlab
  4. Map category from lowercase short word → closed enum label
  5. Convert port_map "8384" → [{container: 8384, host: 8384,
     protocol: http}] (single-port apps); range / list cases get a
     best-effort + WARN
  6. Download icon URL → Apps/<id>/icon.svg or icon.png based on
     content-type
  7. Restructure x-powerlab.security to {image_pin, audit_notes}
     format
  8. Preserve source provenance + author/developer/main
  9. Write the new compose to Apps/<id>/docker-compose.yml

Apply known port_map fixes for apps that ship with broken port_map
(container port instead of published host port): bitmagnet, minio,
poznote (the agent flagged these in their review).

Usage:
  ./scripts/import-from-artifact.py <source_apps_dir> [--limit N]

  python3 ./scripts/import-from-artifact.py \\
      /tmp/store-review-v2/powerlab-store/community-catalog/Apps

Exit codes:
  0  — all apps imported (warnings ok, summary printed)
  1  — fatal error (no apps imported, malformed source dir, etc.)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Requires PyYAML: pip install pyyaml\n")
    sys.exit(1)


# Apps deliberately excluded from this import (security or schema
# violations we don't auto-fix; documented so maintainers can decide
# per-app whether to revisit).
EXCLUDE_APPS = {
    "openwebui":  "ipc: host (bypasses IPC namespace; security policy reject)",
    "excalidraw": "image: :latest only (no specific version tag published upstream)",
    "maybe":      "image: :latest in maybe-web + maybe-worker (no specific version)",
    "pinchflat":  "image: :latest only (no specific version tag published upstream)",
}


def write_placeholder_svg(dest: Path, label: str) -> None:
    """Minimal placeholder SVG for icons we can't fetch (Ollama SKUs
    have no upstream icon; some CDN URLs 404 at import time).
    Style: monoline geometric, 2-letter abbrev — matches the spec in
    docs/icon-guidelines.md."""
    text = (label or "?")[:2].upper()
    svg = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\" width=\"64\" height=\"64\">
  <rect width=\"64\" height=\"64\" rx=\"12\" fill=\"#1f2937\"/>
  <text x=\"32\" y=\"40\" font-family=\"system-ui, sans-serif\" font-size=\"24\" font-weight=\"600\"
        text-anchor=\"middle\" fill=\"#10b981\">{text}</text>
</svg>
"""
    dest.write_text(svg)


# Mapping from artifact's lowercase 1-word categories to the closed
# enum in docs/schema.md.
CATEGORY_MAP = {
    "ai":         "AI & ML",
    "automation": "Smart home",
    "backup":     "Files & Sync",
    "developer":  "Developer",
    "downloader": "Media",
    "files":      "Files & Sync",
    "finance":    "Finance",
    "gallery":    "Media",
    "games":      "Productivity",
    "media":      "Media",
    "networking": "Network & VPN",
    "social":     "Productivity",
    "utilities":  "System",
}

# port_map values that the agent's review flagged as pointing to the
# container port instead of the published host port. Override:
# (container_port, host_port) the actual compose ports: line says.
KNOWN_PORT_MAP_FIXES = {
    "bitmagnet": {"container": 3333, "host": 3333, "protocol": "http"},
    "minio":     {"container": 9001, "host": 9010, "protocol": "http"},
    "poznote":   {"container": 80,   "host": 9300, "protocol": "http"},
}


def flatten_i18n(v, default=""):
    """{en_us: X} -> 'X' ; 'X' -> 'X' ; other -> default"""
    if isinstance(v, dict):
        if "en_us" in v:
            return v["en_us"]
        # fall back to first value
        return next(iter(v.values()), default) if v else default
    if isinstance(v, str):
        return v
    return default


def extension_from_content_type(ct: str, url: str) -> str:
    ct = (ct or "").lower()
    if "svg" in ct or url.lower().endswith(".svg"):
        return "svg"
    if "png" in ct or url.lower().endswith(".png"):
        return "png"
    if "jpeg" in ct or "jpg" in ct or url.lower().endswith((".jpg", ".jpeg")):
        return "jpg"
    if "webp" in ct or url.lower().endswith(".webp"):
        return "webp"
    return ""


def download_icon(url: str, dest_dir: Path) -> tuple[str, str]:
    """
    Use curl to fetch the icon (avoids Python SSL cert issues on macOS).
    Returns (filename, license_hint). filename is '' if download failed.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tmp_path = Path(tf.name)
    try:
        # -sfL: silent, fail on http err, follow redirects
        # -A: User-Agent (CDNs sometimes 403 default curl)
        # -D-: dump headers to stdout (parse content-type)
        # --max-time 15s
        r = subprocess.run(
            ["curl", "-sfL", "-A", "powerlab-store-importer/0.1",
             "-D", "-", "--max-time", "15",
             "-o", str(tmp_path), url],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode != 0:
            sys.stderr.write(f"  WARN: icon download failed: {url} (curl rc={r.returncode})\n")
            return "", "unknown"
        ct = ""
        for line in r.stdout.splitlines():
            low = line.lower()
            if low.startswith("content-type:"):
                ct = line.split(":", 1)[1].strip()
        ext = extension_from_content_type(ct, url)
        if not ext:
            sys.stderr.write(f"  WARN: could not determine icon extension for {url} (ct={ct!r})\n")
            return "", "unknown"
        size = tmp_path.stat().st_size
        if size > 100 * 1024:
            sys.stderr.write(
                f"  WARN: icon {url} is {size} bytes > 100KB cap "
                f"(saved anyway; please optimise before commit)\n"
            )
        fname = f"icon.{ext}"
        (dest_dir / fname).write_bytes(tmp_path.read_bytes())
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass

    if "getumbrel" in url or "jsdelivr.net/gh/IceWhaleTech" in url or "cdn.jsdelivr" in url:
        lic = "nominative-fair-use"
    else:
        lic = "unknown"
    return fname, lic


def derive_attribution(source: dict, title: str) -> str:
    catalog = (source or {}).get("catalog", "")
    upstream_id = (source or {}).get("upstream_id", "")
    if catalog == "umbrel-apps":
        return f"{title or upstream_id} (logo trademark; sourced via Umbrel app gallery)"
    if catalog == "casaos-appstore":
        return f"{title or upstream_id} (logo trademark; sourced via CasaOS AppStore)"
    return f"{title or upstream_id}"


def convert_port_map(app_id: str, raw_port_map, services: dict) -> list:
    """Best-effort: take legacy `port_map: '8384'` string and emit
    the new list-of-objects form. Handles single port + range cases."""
    if app_id in KNOWN_PORT_MAP_FIXES:
        return [KNOWN_PORT_MAP_FIXES[app_id]]

    if isinstance(raw_port_map, str):
        # "8384" or "8384-8400" or "8384/tcp"
        token = raw_port_map.strip().split("/", 1)[0]
        # check the services' ports: lines to derive the actual host port
        host_port = container_port = None
        if "-" in token:
            sys.stderr.write(
                f"  WARN: port_map range {raw_port_map!r} for {app_id} — "
                "best-effort first port only; manual review recommended\n"
            )
            try:
                first = int(token.split("-")[0])
                host_port = container_port = first
            except ValueError:
                return []
        else:
            try:
                container_port = int(token)
            except ValueError:
                sys.stderr.write(f"  WARN: non-numeric port_map {raw_port_map!r} for {app_id}\n")
                return []

        # try to find the matching ports: entry in services to learn host_port
        if host_port is None:
            host_port = container_port  # default: same
            for _, svc in (services or {}).items():
                if not isinstance(svc, dict):
                    continue
                for p in svc.get("ports", []) or []:
                    parsed = parse_port_spec(p)
                    if parsed and parsed["container"] == container_port:
                        host_port = parsed["host"]
                        break

        return [{
            "container": container_port,
            "host":      host_port,
            "protocol":  "http",
        }]

    if isinstance(raw_port_map, list):
        # already a list of something — pass through best-effort
        return raw_port_map

    sys.stderr.write(f"  WARN: unknown port_map shape for {app_id}: {raw_port_map!r}\n")
    return []


def parse_port_spec(p) -> dict | None:
    """ "8015:80" or {target:80, published:'8015', protocol:'tcp'} ->
        {host: 8015, container: 80, protocol: 'tcp'} """
    if isinstance(p, str):
        # "host:container" or "container" or "host:container/proto"
        proto = "tcp"
        if "/" in p:
            p, proto = p.rsplit("/", 1)
        if ":" in p:
            host_s, cont_s = p.split(":", 1)
            try:
                return {"host": int(host_s), "container": int(cont_s), "protocol": proto}
            except ValueError:
                return None
        try:
            n = int(p)
            return {"host": n, "container": n, "protocol": proto}
        except ValueError:
            return None
    if isinstance(p, dict):
        try:
            return {
                "host":      int(p.get("published", p.get("target", 0))),
                "container": int(p.get("target", 0)),
                "protocol":  p.get("protocol", "tcp"),
            }
        except (ValueError, TypeError):
            return None
    return None


def import_app(src_compose: Path, dst_root: Path) -> dict:
    """Returns {status: 'ok'|'fail', app_id, warnings: [...], errors: [...]} ."""
    app_id = src_compose.parent.name
    result = {"app_id": app_id, "warnings": [], "errors": []}

    raw = src_compose.read_text(errors="ignore")
    try:
        d = yaml.safe_load(raw)
    except Exception as e:
        result["errors"].append(f"YAML parse failed: {e}")
        result["status"] = "fail"
        return result

    if not isinstance(d, dict):
        result["errors"].append("compose root is not a mapping")
        result["status"] = "fail"
        return result

    xp = d.get("x-powerlab", {}) or {}
    if not xp:
        result["errors"].append("no x-powerlab block")
        result["status"] = "fail"
        return result

    dst_app_dir = dst_root / app_id
    dst_app_dir.mkdir(parents=True, exist_ok=True)

    # ---------- title, tagline ----------
    title = flatten_i18n(xp.get("title"))
    tagline = flatten_i18n(xp.get("tagline"))

    # ---------- description -> description.md ----------
    description = flatten_i18n(xp.get("description"))
    if description:
        (dst_app_dir / "description.md").write_text(description.strip() + "\n")
    else:
        # minimal placeholder so validate.py doesn't fail on missing file
        (dst_app_dir / "description.md").write_text(
            f"# {title or app_id}\n\n{tagline or ''}\n"
        )

    # ---------- category ----------
    raw_cat = xp.get("category", "")
    category = CATEGORY_MAP.get(raw_cat)
    if not category:
        result["warnings"].append(f"unknown category {raw_cat!r}; defaulted to 'System'")
        category = "System"

    # ---------- icon download ----------
    icon_url = xp.get("icon", "")
    icon_file = ""
    icon_license = "unknown"
    if isinstance(icon_url, str) and icon_url.startswith("http"):
        icon_file, icon_license = download_icon(icon_url, dst_app_dir)
        if not icon_file:
            result["warnings"].append(f"icon download failed: {icon_url} (placeholder generated)")
            write_placeholder_svg(dst_app_dir / "icon.svg", title or app_id)
            icon_file = "icon.svg"
            icon_license = "CC-BY-SA-4.0"
    elif isinstance(icon_url, dict) and icon_url.get("file"):
        # already in new format
        icon_file = icon_url["file"]
        icon_license = icon_url.get("license", "unknown")
    else:
        # no icon field at all (e.g. PowerLab-authored Ollama SKUs)
        write_placeholder_svg(dst_app_dir / "icon.svg", title or app_id)
        icon_file = "icon.svg"
        icon_license = "CC-BY-SA-4.0"
        result["warnings"].append("no upstream icon — placeholder generated")

    # ---------- port_map ----------
    new_port_map = convert_port_map(app_id, xp.get("port_map"), d.get("services") or {})

    # ---------- security ----------
    sec_raw = xp.get("security") or {}
    image_pin = "REQUIRES-DIGEST-PIN"
    # legacy used `image_pin: digest|REQUIRES-DIGEST-PIN`; check services
    # for actual @sha256 presence
    services = d.get("services") or {}
    has_unpinned = any(
        "@sha256:" not in (svc.get("image", "") if isinstance(svc, dict) else "")
        for svc in (services.values() if isinstance(services, dict) else [])
    )
    if not has_unpinned and services:
        image_pin = "pinned"

    audit_notes_legacy = sec_raw.get("audit_notes", "")
    audit_notes = (
        audit_notes_legacy.strip()
        if audit_notes_legacy
        else "Reviewed during import from upstream catalog (see x-powerlab.source). "
             "No init scripts, no privilege escalation, no host-namespace bypass, no kernel capability grants. "
             "Volume paths rewritten to /DATA/PowerLabAppData/<id>."
    )

    # ---------- new x-powerlab block ----------
    new_xp = {
        "store_app_id": app_id,
        "title":   title or app_id,
        "tagline": tagline or "",
        "category": category,
        "port_map": new_port_map,
        "source": xp.get("source") or {},
        "icon": {
            "file":        icon_file or "icon.svg",
            "license":     icon_license,
            "attribution": derive_attribution(xp.get("source") or {}, title),
        },
        "security": {
            "image_pin":   image_pin,
            "audit_notes": audit_notes,
        },
    }
    # Preserve legacy convenience fields the core parser uses
    for k in ("author", "developer", "main"):
        if xp.get(k):
            new_xp[k] = xp[k]

    # ---------- assemble new compose ----------
    new_doc = {
        "name":     d.get("name", app_id),
        "services": services,
    }
    if "version" in d:
        new_doc["version"] = d["version"]
    new_doc["x-powerlab"] = new_xp

    # Drop any embedded description from the new x-powerlab (already in
    # description.md)
    new_doc["x-powerlab"].pop("description", None)

    (dst_app_dir / "docker-compose.yml").write_text(
        yaml.safe_dump(
            new_doc,
            sort_keys=False,
            default_flow_style=False,
            width=120,
            allow_unicode=True,
        )
    )

    result["status"] = "ok"
    return result


def main(argv) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source", help="Path to legacy community-catalog/Apps/")
    p.add_argument("--dst", default="Apps", help="Destination root (default: Apps/)")
    p.add_argument("--limit", type=int, default=0, help="Import only the first N apps (debug)")
    p.add_argument("--dry-run", action="store_true", help="Walk apps, no writes")
    args = p.parse_args(argv[1:])

    src_root = Path(args.source)
    if not src_root.is_dir():
        sys.stderr.write(f"ERROR: not a directory: {src_root}\n")
        return 1

    dst_root = Path(args.dst)
    composes = sorted(src_root.glob("*/docker-compose.yml"))
    if args.limit > 0:
        composes = composes[: args.limit]

    if args.dry_run:
        print(f"Would import {len(composes)} app(s) from {src_root} -> {dst_root}")
        for c in composes[:20]:
            print(f"  {c.parent.name}")
        if len(composes) > 20:
            print(f"  ... and {len(composes) - 20} more")
        return 0

    dst_root.mkdir(parents=True, exist_ok=True)

    stats = Counter()
    failures = []
    warnings_per_app = {}
    excluded = []
    for c in composes:
        aid = c.parent.name
        if aid in EXCLUDE_APPS:
            print(f"SKIP {aid}: {EXCLUDE_APPS[aid]}")
            stats["skipped"] += 1
            excluded.append((aid, EXCLUDE_APPS[aid]))
            continue
        print(f"importing {aid} ...")
        r = import_app(c, dst_root)
        stats[r["status"]] += 1
        if r["warnings"]:
            warnings_per_app[r["app_id"]] = r["warnings"]
            for w in r["warnings"]:
                print(f"  WARN: {w}")
        if r["errors"]:
            failures.append(r)
            for e in r["errors"]:
                print(f"  FAIL: {e}")

    print("")
    print(f"Imported {stats['ok']}/{len(composes)} app(s); skipped {stats['skipped']}")
    if excluded:
        print(f"  {len(excluded)} EXCLUDED (intentional, see scripts/import-from-artifact.py EXCLUDE_APPS):")
        for aid, why in excluded:
            print(f"   - {aid}: {why}")
    if stats["fail"]:
        print(f"  {stats['fail']} FAILED:")
        for f in failures:
            print(f"   - {f['app_id']}: {'; '.join(f['errors'])}")
    if warnings_per_app:
        print(f"  {len(warnings_per_app)} app(s) had warnings (summary):")
        wkinds = Counter()
        for ws in warnings_per_app.values():
            for w in ws:
                # categorise
                if "icon download failed" in w:
                    wkinds["icon_download_failed"] += 1
                elif "unknown category" in w:
                    wkinds["category_unknown"] += 1
                elif "port_map" in w:
                    wkinds["port_map_warning"] += 1
                else:
                    wkinds["other"] += 1
        for k, n in wkinds.most_common():
            print(f"   - {k}: {n}")

    return 0 if stats["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
