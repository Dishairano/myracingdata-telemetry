#!/usr/bin/env bash
set -euo pipefail

# Create a new GitHub repository with gh, push current repo, and open a PR for CI changes.
# Requirements:
# - Inside myracingdata-telemetry-capture/ repo (git initialized, main branch present)
# - gh authenticated (gh auth status)
# - git remote 'origin' not yet set, or use FORCE=1 to override
#
# Usage:
#   OWNER=yourname REPO=myracingdata-telemetry CAP_VIS=public bash myracingdata-telemetry-capture/create-gh-repo-and-pr.sh
#   # CAP_VIS can be: public | private | internal (orgs only). Default: public
#
# Optional env vars:
#   FORCE=1        - if set, will reset 'origin' to the new GitHub repo
#   DEFAULT_BASE   - override detected default branch (e.g., main or master)
#
OWNER=${OWNER:-}
REPO=${REPO:-}
CAP_VIS=${CAP_VIS:-public}
FORCE=${FORCE:-}

if [[ -z "$OWNER" || -z "$REPO" ]]; then
  echo "Error: set OWNER and REPO env vars, e.g.: OWNER=yourname REPO=myracingdata-telemetry bash $0"
  exit 1
fi

# Move into repo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
cd "$REPO_ROOT"

# Basic checks
command -v gh >/dev/null 2>&1 || { echo "Error: gh (GitHub CLI) not found"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "Error: git not found"; exit 1; }

gh auth status >/dev/null || { echo "Error: gh not authenticated. Run: gh auth login"; exit 1; }

# Ensure we are in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository. Run this in myracingdata-telemetry-capture directory."
  exit 1
fi

# Determine default branch
BASE="${DEFAULT_BASE:-}"
if [[ -z "$BASE" ]]; then
  BASE=$(git symbolic-ref --short HEAD 2>/dev/null || true)
  BASE=${BASE:-main}
fi

echo "Owner: $OWNER"
echo "Repo:  $REPO"
echo "Base:  $BASE"
echo "Vis:   $CAP_VIS"

# Configure git identity if missing
if ! git config user.name >/dev/null; then git config user.name "Rovo Dev"; fi
if ! git config user.email >/dev/null; then git config user.email "dev@example.com"; fi

# Create GitHub repo (non-interactive)
REPO_SLUG="$OWNER/$REPO"
EXISTS=0
if gh repo view "$REPO_SLUG" >/dev/null 2>&1; then EXISTS=1; fi

if [[ $EXISTS -eq 0 ]]; then
  gh repo create "$REPO_SLUG" --$CAP_VIS --source . --remote origin --push
else
  echo "Repo already exists: $REPO_SLUG"
  if git remote get-url origin >/dev/null 2>&1; then
    if [[ -n "$FORCE" ]]; then
      git remote set-url origin "https://github.com/$REPO_SLUG.git"
    else
      echo "Origin already set. Use FORCE=1 to override.";
    fi
  else
    git remote add origin "https://github.com/$REPO_SLUG.git"
    git push -u origin "$BASE"
  fi
fi

# Ensure main/base branch exists remotely
if ! git ls-remote --exit-code origin "$BASE" >/dev/null 2>&1; then
  git push -u origin "$BASE"
fi

# Invoke PR creation script
if [[ -x "$REPO_ROOT/create-ci-pr.sh" ]]; then
  BASE="$BASE" bash "$REPO_ROOT/create-ci-pr.sh"
else
  echo "create-ci-pr.sh not found or not executable: $REPO_ROOT/create-ci-pr.sh"
  exit 1
fi
