#!/usr/bin/env bash
set -euo pipefail

# Set GitHub Actions code signing secrets for the repository using gh CLI.
# Usage:
#   bash myracingdata-telemetry-capture/set-signing-secrets.sh /path/to/cert.pfx "password"
#
# Requires:
#   - gh authenticated (gh auth status)
#   - repo is the current directory's repo (run inside repo root or set GH_REPO)
# Optional env:
#   - GH_REPO=owner/repo to explicitly target a repository

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <pfx_path> <password>"
  exit 1
fi

PFX_PATH="$1"
PFX_PASS="$2"

command -v gh >/dev/null 2>&1 || { echo "Error: gh not found"; exit 1; }

if [[ -n "${GH_REPO:-}" ]]; then
  export GH_REPO
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: gh not authenticated (gh auth login)"; exit 1
fi

if [[ ! -f "$PFX_PATH" ]]; then
  echo "Error: PFX file not found: $PFX_PATH"; exit 1
fi

# Base64 encode PFX
if command -v base64 >/dev/null 2>&1; then
  PFX_B64=$(base64 -w0 "$PFX_PATH" 2>/dev/null || base64 "$PFX_PATH")
else
  # Fallback using Python
  PFX_B64=$(python - <<'PY'
import base64,sys
p=sys.argv[1]
with open(p,'rb') as f:
    print(base64.b64encode(f.read()).decode('ascii'))
PY
"$PFX_PATH")
fi

# Set secrets
printf "%s" "$PFX_B64" | gh secret set SIGNING_CERT_PFX_B64
printf "%s" "$PFX_PASS" | gh secret set SIGNING_CERT_PASSWORD

echo "Secrets set: SIGNING_CERT_PFX_B64, SIGNING_CERT_PASSWORD"
