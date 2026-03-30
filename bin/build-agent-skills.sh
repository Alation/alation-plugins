#!/usr/bin/env bash
# Package each Alation skill as a portable Agent Skill (agentskills.io spec).
#
# Each skill gets:
#   - SKILL.md with `python -m cli` rewritten to `scripts/run-cli`
#   - references/ (if any)
#   - scripts/cli/  (full CLI package)
#   - scripts/run-cli  (wrapper script)
#
# Usage:
#   ./bin/build-agent-skills.sh              # Build all skills
#   ./bin/build-agent-skills.sh ask explore  # Build specific skills
#
# Output: dist/agent-skills/<skill-name>/  (directories)
#         dist/agent-skills/agent-skill-<skill-name>.zip  (zipped for distribution)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
CLI_DIR="$REPO_ROOT/cli"
DIST_DIR="$REPO_ROOT/dist/agent-skills"

build_one() {
  local skill_name="$1"
  local skill_src="$SKILLS_DIR/$skill_name"
  local skill_dst="$DIST_DIR/$skill_name"

  if [ ! -d "$skill_src" ]; then
    echo "Error: skill '$skill_name' not found at $skill_src" >&2
    return 1
  fi

  if [ ! -f "$skill_src/SKILL.md" ]; then
    echo "Error: $skill_src/SKILL.md not found" >&2
    return 1
  fi

  echo "Building agent skill: $skill_name"

  # Clean and create output directory
  rm -rf "$skill_dst"
  mkdir -p "$skill_dst/scripts"

  # Copy SKILL.md with CLI references rewritten
  sed 's|python -m cli|scripts/run-cli|g' "$skill_src/SKILL.md" > "$skill_dst/SKILL.md"

  # Copy references/ if present (also rewrite CLI references)
  if [ -d "$skill_src/references" ]; then
    mkdir -p "$skill_dst/references"
    for ref_file in "$skill_src/references"/*; do
      [ -f "$ref_file" ] || continue
      if [[ "$ref_file" == *.md ]]; then
        sed 's|python -m cli|scripts/run-cli|g' "$ref_file" > "$skill_dst/references/$(basename "$ref_file")"
      else
        cp "$ref_file" "$skill_dst/references/$(basename "$ref_file")"
      fi
    done
  fi

  # Copy CLI package (excluding __pycache__)
  rsync -a --exclude='__pycache__' "$CLI_DIR/" "$skill_dst/scripts/cli/"

  # Create wrapper script
  cat > "$skill_dst/scripts/run-cli" <<'WRAPPER'
#!/usr/bin/env bash
# Portable CLI wrapper — finds Python 3.10+ and runs the bundled CLI.
# The CLI uses modern Python syntax (dict | None, match/case) requiring 3.10+.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Find a suitable Python 3.10+ interpreter
find_python() {
  for candidate in python3 python3.13 python3.12 python3.11 python3.10; do
    local py
    py="$(command -v "$candidate" 2>/dev/null)" || continue
    local ver
    ver="$("$py" -c 'import sys; print(sys.version_info[:2] >= (3,10))' 2>/dev/null)" || continue
    if [ "$ver" = "True" ]; then
      echo "$py"
      return 0
    fi
  done
  # Also check common Homebrew / uv / pyenv paths
  for path in /opt/homebrew/bin/python3 "$HOME/.local/bin/python3" "$HOME/.pyenv/shims/python3"; do
    [ -x "$path" ] || continue
    local ver
    ver="$("$path" -c 'import sys; print(sys.version_info[:2] >= (3,10))' 2>/dev/null)" || continue
    if [ "$ver" = "True" ]; then
      echo "$path"
      return 0
    fi
  done
  return 1
}

PYTHON="$(find_python)" || { echo "Error: Python 3.10+ is required but not found." >&2; exit 1; }
PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON" -m cli "$@"
WRAPPER
  chmod +x "$skill_dst/scripts/run-cli"

  # Create zip for distribution (prefixed so release assets are distinguishable from plugins)
  local zip_name="agent-skill-${skill_name}.zip"
  rm -f "$DIST_DIR/$zip_name"
  (cd "$DIST_DIR" && zip -rq "$zip_name" "$skill_name/")

  echo "  -> $skill_dst/"
  echo "  -> $DIST_DIR/$zip_name"
}

# Determine which skills to build
if [ $# -eq 0 ]; then
  skills=()
  for d in "$SKILLS_DIR"/*/; do
    [ -d "$d" ] && skills+=("$(basename "$d")")
  done
else
  skills=("$@")
fi

mkdir -p "$DIST_DIR"

for skill_name in "${skills[@]}"; do
  build_one "$skill_name"
done

echo ""
echo "Built ${#skills[@]} agent skill(s) in $DIST_DIR"
