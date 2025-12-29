#!/usr/bin/env bash
set -euo pipefail
# Trigger the Windows EXE build workflow via GitHub CLI.
# Usage: bash myracingdata-telemetry-capture/trigger-workflow.sh
# Optional env: GH_REPO=owner/repo

command -v gh >/dev/null 2>&1 || { echo "Error: gh not found"; exit 1; }
if ! gh auth status >/dev/null 2>&1; then echo "Error: gh auth required"; exit 1; fi

WF="build-windows-exe.yml"

echo "Triggering workflow: $WF"
if [[ -n "${GH_REPO:-}" ]]; then
  gh workflow run "$WF" --repo "$GH_REPO"
else
  gh workflow run "$WF"
fi

echo "Workflow triggered. View runs with:"
echo "  gh run list | head"
