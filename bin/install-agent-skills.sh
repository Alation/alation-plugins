#!/usr/bin/env bash
# Install Alation agent skills in the open Agent Skills format.
#
# Downloads agent-skill zips from the latest GitHub release and installs them
# to ~/.agents/skills (user) or .agents/skills (workspace). Each skill is
# self-contained (bundled CLI + run-cli wrapper). Works with Codex, Gemini CLI,
# and any tool that reads the .agents/skills directory.
# Ref: https://agentskills.io/home
#
# Usage:
#   ./install-agent-skills.sh                          # Interactive: prompt for scope
#   ./install-agent-skills.sh --scope user
#   ./install-agent-skills.sh --scope workspace
#
set -euo pipefail

VERSION="0.1.0"
REPO="Alation/alation-plugins"
API_BASE="https://api.github.com/repos/${REPO}"

# --- Defaults -----------------------------------------------------------

SCOPE=""
SKILLS=""
QUIET=false

# --- Colors --------------------------------------------------------------

if [ -t 1 ] && [ "${NO_COLOR:-}" = "" ]; then
  BOLD='\033[1m'
  FAINT='\033[2m'
  RED='\033[31m'
  GREEN='\033[32m'
  YELLOW='\033[33m'
  RESET='\033[0m'
else
  BOLD="" FAINT="" RED="" GREEN="" YELLOW="" RESET=""
fi

# --- Helpers -------------------------------------------------------------

info()  { $QUIET || printf '%b\n' "$*"; }
faint() { $QUIET || printf '%b\n' "${FAINT}$*${RESET}"; }
warn()  { printf '%b\n' "${YELLOW}Warning:${RESET} $*" >&2; }
die()   { printf '%b\n' "${RED}Error:${RESET} $*" >&2; exit 1; }

usage() {
  cat <<EOF
Install Alation agent skills.

Usage: $(basename "$0") [options]

Options:
  --scope <scope>    Installation scope: user (global) or workspace (project)
  --skills <list>    Comma-separated skill names to install (default: all)
  --quiet            Suppress informational output
  --help             Show this help

Scopes:
  user        Install to ~/.agents/skills (available everywhere)
  workspace   Install to .agents/skills in the current directory

Prerequisites: curl and unzip must be available.

Note: Claude Code uses its plugin marketplace for installation.
  Run 'claude plugins install' within Claude Code instead.
EOF
  exit 0
}

# --- Install directory ----------------------------------------------------

install_dir() {
  local scope="$1"
  case "$scope" in
    user)      echo "${HOME}/.agents/skills" ;;
    workspace) echo ".agents/skills" ;;
    *) die "Unknown scope: ${scope}" ;;
  esac
}

# --- GitHub API helpers ---------------------------------------------------

# Fetch JSON from the GitHub API (no auth required for public repos).
gh_api() {
  local url="$1"
  curl -fsSL -H "Accept: application/vnd.github+json" "$url" \
    || die "Failed to fetch ${url}"
}

# Download a release asset by its browser_download_url.
gh_download() {
  local url="$1" dest="$2"
  curl -fsSL -o "$dest" -L "$url" \
    || die "Failed to download $(basename "$dest")"
}

# --- Source skills ---------------------------------------------------------

download_skills_zip() {
  local dest="$1"

  faint "Fetching latest release from ${REPO}..."

  local release_json
  release_json="$(gh_api "${API_BASE}/releases/latest")"

  # Extract asset names and download URLs (one per line: name<TAB>url)
  # Python is a prerequisite (3.10+), so we use it for reliable JSON parsing.
  local assets
  assets="$(echo "$release_json" | python3 -c '
import json, sys
data = json.load(sys.stdin)
for a in data.get("assets", []):
    print(a["name"] + "\t" + a["browser_download_url"])
' 2>/dev/null)" || die "Failed to parse release JSON. Is Python 3 available?"

  # Try combined agent-skills.zip first
  local combined_url
  combined_url="$(echo "$assets" | awk -F'\t' '$1 == "agent-skills.zip" {print $2}')"

  if [ -n "$combined_url" ]; then
    faint "Downloading agent-skills.zip..."
    gh_download "$combined_url" "${dest}/agent-skills.zip"
    unzip -qo "${dest}/agent-skills.zip" -d "$dest"
    rm -f "${dest}/agent-skills.zip"

    # Filter to selected skills if --skills was specified
    if [ -n "$SKILLS" ]; then
      for d in "$dest"/*/; do
        [ -d "$d" ] || continue
        local name
        name="$(basename "$d")"
        if ! echo "$SKILLS" | tr ',' '\n' | grep -qx "$name"; then
          rm -rf "$d"
        fi
      done
    fi
  else
    # Fall back to individual agent-skill-<name>.zip assets
    local selected=()
    local selected_urls=()

    while IFS=$'\t' read -r name url; do
      case "$name" in agent-skill-*)
        if [ -n "$SKILLS" ]; then
          local skill_name="${name#agent-skill-}"
          skill_name="${skill_name%.zip}"
          if echo "$SKILLS" | tr ',' '\n' | grep -qx "$skill_name"; then
            selected+=("$name")
            selected_urls+=("$url")
          fi
        else
          selected+=("$name")
          selected_urls+=("$url")
        fi
        ;;
      esac
    done <<< "$assets"

    [ ${#selected[@]} -gt 0 ] || die "No agent-skill assets found in the latest release."

    faint "Downloading ${#selected[@]} skill(s)..."
    for i in "${!selected[@]}"; do
      gh_download "${selected_urls[$i]}" "${dest}/${selected[$i]}"
    done

    for asset in "${selected[@]}"; do
      unzip -qo "${dest}/${asset}" -d "$dest"
      rm -f "${dest}/${asset}"
    done
  fi

  SOURCE_DIR="$dest"
}

# --- Skill list -----------------------------------------------------------

available_skills_in() {
  local dir="$1"
  for d in "$dir"/*/; do
    [ -f "${d}/SKILL.md" ] && basename "$d"
  done
}

# --- Install --------------------------------------------------------------

install_skill() {
  local skill="$1" source_dir="$2" dest_dir="$3"
  local skill_dest="${dest_dir}/${skill}"

  local action="Installing"
  if [ -d "$skill_dest" ]; then
    action="Replacing"
    rm -rf "$skill_dest"
  fi

  mkdir -p "$dest_dir"

  if [ -d "${source_dir}/${skill}" ]; then
    cp -R "${source_dir}/${skill}" "$skill_dest"
  else
    warn "Skill '${skill}' not found in ${source_dir}, skipping"
    return 1
  fi

  if [ -f "${skill_dest}/scripts/run-cli" ]; then
    chmod +x "${skill_dest}/scripts/run-cli"
  fi

  faint "  ${action} ${skill}"
  return 0
}

# --- Interactive prompt ---------------------------------------------------

prompt_scope() {
  echo ""
  printf '%b\n' "${BOLD}Scope:${RESET}"
  printf '%b\n' "  1) ${BOLD}user${RESET}      - Install to ~/.agents/skills (available everywhere)"
  printf '%b\n' "  2) ${BOLD}workspace${RESET} - Install to .agents/skills (current project only)"
  echo ""
  while true; do
    printf '%b' "Choose scope ${FAINT}[1]${RESET} "
    read -r choice
    case "${choice:-1}" in
      1|user)      SCOPE="user"; break ;;
      2|workspace) SCOPE="workspace"; break ;;
      *) warn "Unknown scope: '${choice}'. Please enter 1 (user) or 2 (workspace)." ;;
    esac
  done
}

# --- Parse arguments ------------------------------------------------------

while [ $# -gt 0 ]; do
  case "$1" in
    --scope)    shift; SCOPE="$1" ;;
    --skills)   shift; SKILLS="$1" ;;
    --quiet)    QUIET=true ;;
    --help|-h)  usage ;;
    --version)  echo "$VERSION"; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

# --- Main -----------------------------------------------------------------

info "${BOLD}Alation Agent Skills Installer${RESET} ${FAINT}v${VERSION}${RESET}"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT
download_skills_zip "$WORK_DIR"

# Validate that we have skills to install
skill_list="$(available_skills_in "$SOURCE_DIR" | tr '\n' ' ')"
skill_count=$(available_skills_in "$SOURCE_DIR" | wc -l | tr -d ' ')
[ "$skill_count" -gt 0 ] || die "No skills found"

# Format skill names in bold red
formatted_skills=""
for s in $skill_list; do
  formatted_skills+="${BOLD}${RED}${s}${RESET} "
done
info "Found ${skill_count} skill(s): ${formatted_skills}"

# Resolve scope
if [ -z "$SCOPE" ]; then
  prompt_scope
fi

# Install
dest="$(install_dir "$SCOPE")"
info ""
info "${BOLD}Installing to ${dest}${RESET}"

count=0
for skill in $(available_skills_in "$SOURCE_DIR"); do
  if install_skill "$skill" "$SOURCE_DIR" "$dest"; then
    count=$((count + 1))
  fi
done

if [ "$count" -eq 0 ]; then
  warn "No skills installed"
else
  info "  ${GREEN}Installed ${count} skill(s)${RESET}"
fi

info ""
info "Restart your agent CLI to pick up new skills."
