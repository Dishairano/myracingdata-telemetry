#!/usr/bin/env bash
set -euo pipefail
# Create and push a version tag to trigger Release (vX.Y.Z)
# Usage: VERSION=v1.0.0 bash myracingdata-telemetry-capture/publish-release-tag.sh

VERSION=${VERSION:-}
if [[ -z "$VERSION" ]]; then echo "Set VERSION env, e.g., VERSION=v1.0.0"; exit 1; fi

git tag "$VERSION" || { echo "Tag already exists locally?"; exit 1; }
git push origin "$VERSION"

echo "Pushed tag $VERSION. GitHub Actions will create a Release with artifacts."
