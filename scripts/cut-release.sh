#!/usr/bin/env bash
# cut-release.sh — release preparation script for powerlab-store.
#
# This is the MANDATORY pre-tag step. Mirrors powerlab core's
# prepare-release.sh discipline (memory anchor:
# feedback_always_run_prepare_release_before_tag). Skipping it leaves
# VERSION + index.json stale and causes downstream confusion.
#
# Sequence:
#   1. validate Apps/ (strict — refuses to cut a release with errors)
#   2. bump VERSION file
#   3. regenerate index.json with the new version stamped in
#   4. roll up .changes/unreleased/ fragments into CHANGELOG.md
#      (via changie batch + merge; only if changie is installed)
#   5. stage VERSION + index.json + CHANGELOG.md + .changes/
#
# Then the operator commits + tags + pushes. The release.yml workflow
# fires on the tag push.
#
# Usage:
#   ./scripts/cut-release.sh 0.1.0
#
# Exit codes:
#   0 — staged and ready to commit
#   1 — validation failed
#   2 — invalid invocation

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "ERROR: usage: ./scripts/cut-release.sh <X.Y.Z>" >&2
  exit 2
fi

# Strip leading 'v' if present
VERSION="${VERSION#v}"

# Sanity check format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9.]+)?$ ]]; then
  echo "ERROR: version must be semver (X.Y.Z or X.Y.Z-suffix), got: $VERSION" >&2
  exit 2
fi

echo "=== powerlab-store release preparation: v${VERSION} ==="

echo ""
echo "[1/5] Validating Apps/ (strict mode)..."
python3 scripts/validate.py Apps/

echo ""
echo "[2/5] Updating VERSION file..."
echo "$VERSION" > VERSION

echo ""
echo "[3/5] Regenerating index.json..."
./scripts/build-index.sh "$VERSION"

echo ""
echo "[4/5] Rolling up changie fragments (if changie present)..."
if command -v changie >/dev/null 2>&1; then
  changie batch "$VERSION"
  changie merge
else
  echo "  (changie not installed; skipping. Install with: go install github.com/miniscruff/changie@latest)"
fi

echo ""
echo "[5/5] Staging release files..."
git add VERSION index.json
[[ -f CHANGELOG.md ]] && git add CHANGELOG.md
[[ -d .changes ]] && git add .changes

echo ""
echo "=== Release v${VERSION} prepared. Next steps: ==="
echo ""
echo "  git status                                 # review staged changes"
echo "  git commit -m 'chore(release): v${VERSION}'"
echo "  git push origin main"
echo "  git tag v${VERSION} -m 'powerlab-store v${VERSION}'"
echo "  git push origin v${VERSION}"
echo ""
echo "The release.yml workflow will fire on tag push and create the GitHub release."
