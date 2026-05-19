#!/usr/bin/env bash
# pin-digests.sh — resolve every image tag in the catalog to an
# immutable @sha256 digest and rewrite compose files in place.
#
# Run locally on a machine that can pull Docker images, BEFORE pushing
# a PR. CI rejects unpinned images.
#
# Requires: docker (logged in if you hit Docker Hub rate limits).
# Compatible with BSD sed (macOS) and GNU sed (Linux).
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

# Detect BSD vs GNU sed
if sed --version 2>/dev/null | grep -q GNU; then
  SED_INPLACE=(sed -i)
else
  SED_INPLACE=(sed -i '')
fi

changed=0
skipped=0
failed=0

echo "Pinning digests under: $ROOT"

while IFS= read -r -d '' f; do
  while IFS= read -r line; do
    img="$(printf '%s' "$line" | sed -E 's/^[[:space:]]*image:[[:space:]]*//')"
    case "$img" in
      *@sha256:*)
        skipped=$((skipped + 1))
        continue
        ;;
    esac

    echo "  resolving $img"
    digest=""
    if digest_attempt="$(docker buildx imagetools inspect "$img" --format '{{.Manifest.Digest}}' 2>/dev/null)"; then
      digest="$digest_attempt"
    elif docker pull -q "$img" >/dev/null 2>&1; then
      digest="$(docker inspect --format='{{index .RepoDigests 0}}' "$img" 2>/dev/null | sed -E 's/.*@//')"
    fi

    if [[ -z "$digest" ]]; then
      echo "  !! could not resolve $img — leaving tag" >&2
      failed=$((failed + 1))
      continue
    fi

    esc_img="$(printf '%s' "$img" | sed -e 's/[\/&]/\\&/g')"
    esc_new="$(printf '%s' "${img}@${digest}" | sed -e 's/[\/&]/\\&/g')"
    "${SED_INPLACE[@]}" -E "s|image:[[:space:]]*${esc_img}([[:space:]]|$)|image: ${esc_new}\\1|" "$f"
    changed=$((changed + 1))
  done < <(grep -E '^[[:space:]]*image:[[:space:]]' "$f" || true)
done < <(find "$ROOT" -name docker-compose.yml -print0)

echo ""
echo "Done. pinned=$changed already-pinned=$skipped failed=$failed"
if [[ "$failed" -gt 0 ]]; then
  echo "Some images failed to resolve — review the messages above." >&2
  exit 1
fi
