#!/usr/bin/env bash
# Package the plugin directory as a zip for Claude Desktop / Cowork.
#
# Usage:
#   ./bin/build-plugin-zip.sh
#   ./bin/build-plugin-zip.sh /tmp/custom-output.zip
#
# The zip is written to dist/alation.zip by default.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"
OUTPUT="${1:-$DIST_DIR/alation.zip}"

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"

cd "$REPO_ROOT"
zip -r "$OUTPUT" . \
  -x ".env" \
  -x ".venv/*" \
  -x ".pytest_cache/*" \
  -x "__pycache__/*" \
  -x "*/__pycache__/*" \
  -x "*.pyc" \
  -x ".git/*" \
  -x ".DS_Store" \
  -x "dist/*" \
  -x "bin/*" \
  -x ".github/*" \
  -x ".worktrees/*" \
  -x ".claude/*" \
  -x ".vscode/*"

echo "Built: $OUTPUT  ($(du -h "$OUTPUT" | cut -f1))"
