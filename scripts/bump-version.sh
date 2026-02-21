#!/bin/bash
set -euo pipefail

# Release flow:
#   1. This script stamps the version into manifest.json and commits it,
#      so the repo is always the source of truth (no build-time patching).
#   2. A bare semver tag (no "v" prefix) is created and pushed.
#   3. The tag push triggers .github/workflows/release.yml, which zips
#      the component as-is and creates a GitHub Release with auto-generated notes.
#
# Usage: ./scripts/bump-version.sh 0.6.0

VERSION="${1:?Usage: $0 <version>}"
MANIFEST="custom_components/additional_ca/manifest.json"

jq --arg v "$VERSION" '.version = $v' "$MANIFEST" > tmp.json
mv tmp.json "$MANIFEST"

git add "$MANIFEST"
git commit -m "chore: bump version to $VERSION"
git tag "$VERSION"
git push && git push --tags
