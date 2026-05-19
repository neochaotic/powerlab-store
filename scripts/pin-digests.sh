#!/usr/bin/env bash
# pin-digests.sh — resolve every image tag in the catalog to an
# immutable @sha256 digest and rewrite compose files in place.
#
# Run locally on a machine that can pull Docker images, BEFORE pushing
# a PR. CI rejects unpinned images.
#
# Requires: docker (logged in if you hit Docker Hub rate limits) + python3.
# Compatible with macOS (BSD) and Linux (GNU) by delegating the rewrite
# to Python — avoids the BSD/GNU sed regex incompatibilities.
#
# Usage:
#   ./scripts/pin-digests.sh                  # scan Apps/
#   ./scripts/pin-digests.sh Apps/<app-id>/   # scan one app
#
# Exit codes:
#   0 — all images pinned (or already pinned)
#   1 — one or more images failed to resolve
#   2 — invalid invocation

set -euo pipefail

ROOT="${1:-Apps}"

if [[ ! -d "$ROOT" ]]; then
  echo "ERROR: not a directory: $ROOT" >&2
  exit 2
fi

echo "Pinning digests under: $ROOT"

# Pass 1: collect every unique image tag that needs resolving.
TMPLIST="$(mktemp)"
trap 'rm -f "$TMPLIST"' EXIT

skipped=0
while IFS= read -r -d '' f; do
  while IFS= read -r line; do
    img="$(printf '%s' "$line" | python3 -c 'import sys, re; print(re.sub(r"^\s*image:\s*", "", sys.stdin.read().rstrip()))')"
    case "$img" in
      *@sha256:*) skipped=$((skipped + 1)) ;;
      "")          ;;
      *)           printf '%s\n' "$img" >> "$TMPLIST" ;;
    esac
  done < <(grep -E '^[[:space:]]*image:[[:space:]]' "$f" || true)
done < <(find "$ROOT" -name docker-compose.yml -print0)

# Dedup
sort -u "$TMPLIST" -o "$TMPLIST"
total_unique=$(wc -l < "$TMPLIST" | tr -d ' ')

echo "  $total_unique unique image tag(s) to resolve (skipping $skipped already-pinned occurrences)"

# Pass 2: resolve each unique image to a digest, build a JSON map.
PIN_MAP="$(mktemp)"
trap 'rm -f "$TMPLIST" "$PIN_MAP"' EXIT
echo "{}" > "$PIN_MAP"

failed=0
resolved=0
while IFS= read -r img; do
  [[ -z "$img" ]] && continue
  echo "  resolving $img"
  digest=""
  # Docker 29 ignores --format on imagetools inspect; parse the human table.
  raw="$(docker buildx imagetools inspect "$img" 2>/dev/null || true)"
  if [[ -n "$raw" ]]; then
    digest="$(printf '%s' "$raw" | awk '/^Digest:/ {print $2; exit}')"
  fi
  # Fallback: docker pull then inspect RepoDigests
  if [[ -z "$digest" ]] && docker pull -q "$img" >/dev/null 2>&1; then
    digest="$(docker inspect --format='{{index .RepoDigests 0}}' "$img" 2>/dev/null | awk -F'@' '{print $2}')"
  fi
  # Sanity: must start with sha256:
  if [[ -n "$digest" && "${digest}" != sha256:* ]]; then
    echo "    !! unexpected digest format for $img: $digest" >&2
    digest=""
  fi

  if [[ -z "$digest" ]]; then
    echo "    !! could not resolve $img — leaving tag" >&2
    failed=$((failed + 1))
    continue
  fi

  # Append to JSON map via python (handles escaping safely)
  python3 - "$img" "${img}@${digest}" "$PIN_MAP" <<'PYEOF'
import json, sys
img, new, path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as fh:
    d = json.load(fh)
d[img] = new
with open(path, 'w') as fh:
    json.dump(d, fh)
PYEOF
  resolved=$((resolved + 1))
done < "$TMPLIST"

# Pass 3: rewrite all compose files using the JSON map; also flip any
# x-powerlab.security.image_pin: REQUIRES-DIGEST-PIN → pinned IF every
# service in that file now has @sha256.
PIN_MAP="$PIN_MAP" PIN_ROOT="$ROOT" python3 <<'PYEOF'
import json, os, re
from pathlib import Path

with open(os.environ["PIN_MAP"]) as fh:
    digests = json.load(fh)
root = os.environ["PIN_ROOT"]

written = 0
flipped = 0
for cf in Path(root).rglob("docker-compose.yml"):
    text = cf.read_text()
    orig = text

    # 1. Rewrite image references
    for img, new in digests.items():
        pat = r"^(\s*image:\s*)" + re.escape(img) + r"(\s*)$"
        text = re.sub(pat, r"\1" + new + r"\2", text, flags=re.M)

    # 2. If every image: line now has @sha256:, flip image_pin to pinned
    image_lines = re.findall(r"^\s*image:\s*(\S+)", text, flags=re.M)
    all_pinned = bool(image_lines) and all("@sha256:" in i for i in image_lines)
    if all_pinned:
        new_text = re.sub(
            r"(image_pin:\s*)REQUIRES-DIGEST-PIN",
            r"\1pinned",
            text,
        )
        if new_text != text:
            flipped += 1
        text = new_text

    if text != orig:
        cf.write_text(text)
        written += 1

print(f"  rewrote {written} compose file(s); flipped image_pin in {flipped}")
PYEOF

echo ""
echo "Done. resolved=$resolved already-pinned=$skipped failed=$failed"
if [[ "$failed" -gt 0 ]]; then
  echo "Some images failed to resolve — review the messages above." >&2
  exit 1
fi
