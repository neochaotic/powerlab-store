#!/usr/bin/env bash
# check-safety.sh — compose-level security lint for powerlab-store.
#
# Mirror of powerlab core's scripts/check-catalog-app-safety.sh, hardened
# for STRICT DAY 1 (no warn-only ratchet — the store starts clean).
#
# Rejection classes (each a hard fail):
#   - privileged: true                    — full host access
#   - /var/run/docker.sock mount          — container can control Docker
#   - network_mode: host                  — bypass network namespace
#   - pid: host / ipc: host               — bypass process/IPC isolation
#   - cap_add: ALL / SYS_ADMIN            — kernel-equivalent privileges
#   - bind-mount of system paths (/etc, /var/lib, /usr, /root, /home,
#     /boot, /sys, /proc) — escape from the app's data dir
#
# Allowed (looks suspicious, isn't):
#   - cap_drop: ALL                       — defensive, the opposite
#   - bind-mount of ${POWERLAB_APP_DATA}/... — canonical app data
#   - bind-mount of /DATA/PowerLabAppData/... — production absolute form
#   - bind-mount of /tmp/powerlab-data/...    — macOS dev-mode form
#   - Named volumes (no leading /)
#
# Usage:
#   ./scripts/check-safety.sh                # scan every Apps/*/docker-compose.yml
#   ./scripts/check-safety.sh <path>          # scan a single compose file
#
# Exit codes:
#   0 — pass (no findings)
#   1 — findings detected
#   2 — invalid invocation

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG_DIR="$REPO_ROOT/Apps"

scan_file() {
  local f="$1"
  local relpath="${f#"$REPO_ROOT"/}"

  if grep -qE '^\s*privileged:\s*true' "$f"; then
    echo "$relpath: privileged: true is not allowed (full host access)"
  fi

  if grep -q '/var/run/docker.sock' "$f"; then
    echo "$relpath: /var/run/docker.sock mount is not allowed (container could control Docker)"
  fi

  if grep -qE "^[[:space:]]*network_mode:[[:space:]]*['\"]?host['\"]?[[:space:]]*\$" "$f"; then
    echo "$relpath: network_mode: host is not allowed (bypasses network namespace)"
  fi

  if grep -qE "^[[:space:]]*pid:[[:space:]]*['\"]?host['\"]?[[:space:]]*\$" "$f"; then
    echo "$relpath: pid: host is not allowed (bypasses process namespace)"
  fi

  if grep -qE "^[[:space:]]*ipc:[[:space:]]*['\"]?host['\"]?[[:space:]]*\$" "$f"; then
    echo "$relpath: ipc: host is not allowed (bypasses IPC namespace)"
  fi

  # cap_add: ALL or SYS_ADMIN — must distinguish from cap_drop.
  # Extract just the cap_add block.
  if awk '
    /^[[:space:]]*cap_add:/ {in_add=1; n=0; next}
    in_add && /^[[:space:]]*cap_drop:/ {in_add=0; next}
    in_add && /^[[:space:]]*[a-zA-Z_]+:/ && !/^[[:space:]]*-/ {in_add=0}
    in_add { n++; print }
    n > 12 {in_add=0}
  ' "$f" | grep -qE '^\s*-\s*"?(ALL|SYS_ADMIN)"?'; then
    if grep -q "ALL" "$f"; then
      echo "$relpath: cap_add: ALL is not allowed (kernel-equivalent privileges)"
    fi
    if grep -q "SYS_ADMIN" "$f"; then
      echo "$relpath: cap_add: SYS_ADMIN is not allowed (kernel-equivalent privileges)"
    fi
  fi

  # env_file is banned per ADR-0039 (indirect bash-via-env vector)
  if grep -qE '^\s*env_file:' "$f"; then
    echo "$relpath: env_file directive is not allowed (indirect bash-via-env injection)"
  fi

  # System-path bind mounts. Forbidden source roots: /etc, /var/lib,
  # /usr, /root, /home, /boot, /sys, /proc. Allowed: ${POWERLAB_APP_DATA},
  # /DATA/PowerLabAppData/*, /tmp/powerlab-data/*, named volumes.
  local forbidden_roots='^[[:space:]]*-[[:space:]]*("?)(/etc|/var/lib|/usr|/root|/home|/boot|/sys|/proc)(/[^:]*)?:'
  if grep -E "$forbidden_roots" "$f" | grep -vE '^[[:space:]]*-[[:space:]]*"?(/DATA/PowerLabAppData|/tmp/powerlab-data|\$\{?POWERLAB_APP_DATA)'; then
    grep -nE "$forbidden_roots" "$f" | grep -vE '^[0-9]+:[[:space:]]*-[[:space:]]*"?(/DATA/PowerLabAppData|/tmp/powerlab-data|\$\{?POWERLAB_APP_DATA)' | while IFS= read -r line; do
      local lineno src
      lineno="${line%%:*}"
      src="$(echo "$line" | grep -oE '/(etc|var/lib|usr|root|home|boot|sys|proc)[^:]*' | head -1)"
      echo "$relpath:$lineno: bind-mount of system path '$src' is not allowed (escape from app data dir)"
    done
  fi
}

main() {
  local files=()
  if [[ $# -gt 0 ]]; then
    files=("$@")
  else
    if [[ ! -d "$CATALOG_DIR" ]]; then
      echo "INFO: no $CATALOG_DIR — nothing to scan" >&2
      exit 0
    fi
    while IFS= read -r f; do
      files+=("$f")
    done < <(find "$CATALOG_DIR" -name "docker-compose.yml")
  fi

  if [[ "${#files[@]}" -eq 0 ]]; then
    echo "INFO: no docker-compose.yml files found to scan" >&2
    exit 0
  fi

  local total_findings=0
  local files_with_findings=0
  for f in "${files[@]}"; do
    local out
    out="$(scan_file "$f")"
    if [[ -n "$out" ]]; then
      echo "$out"
      files_with_findings=$(( files_with_findings + 1 ))
      total_findings=$(( total_findings + $(echo "$out" | wc -l) ))
    fi
  done

  if [[ "$total_findings" -eq 0 ]]; then
    echo "OK: 0 safety findings across ${#files[@]} catalog file(s)" >&2
    exit 0
  fi

  echo "" >&2
  echo "FAIL: $total_findings safety finding(s) across $files_with_findings catalog file(s)" >&2
  echo "Strict mode (no warn-only ratchet); see docs/curation-criteria.md" >&2
  exit 1
}

main "$@"
