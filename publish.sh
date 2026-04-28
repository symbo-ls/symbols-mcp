#!/usr/bin/env bash
set -e

# Usage: ./publish.sh [patch|minor|major|x.y.z]
# Stores PyPI token in .pypirc (gitignored)

BUMP=${1:-patch}

# Read current version from pyproject.toml
CURRENT=$(grep '^version' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP" in
  patch)   NEW="$MAJOR.$MINOR.$((PATCH + 1))" ;;
  minor)   NEW="$MAJOR.$((MINOR + 1)).0" ;;
  major)   NEW="$((MAJOR + 1)).0.0" ;;
  *.*.*)   NEW="$BUMP" ;;
  *)       echo "Usage: $0 [patch|minor|major|x.y.z]"; exit 1 ;;
esac

echo "Bumping $CURRENT → $NEW"

# Update versions
sed -i '' "s/^version = \"$CURRENT\"/version = \"$NEW\"/" pyproject.toml

# server.json: top-level + pypi entry track pyproject; npm entry tracks package.json
NPM_VERSION=$(grep '"version"' package.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')
python3 - <<EOF
import json
p = "server.json"
d = json.load(open(p))
d["version"] = "$NEW"
for pkg in d.get("packages", []):
    if pkg.get("registryType") == "pypi":
        pkg["version"] = "$NEW"
    elif pkg.get("registryType") == "npm":
        pkg["version"] = "$NPM_VERSION"
json.dump(d, open(p, "w"), indent=2)
open(p, "a").write("\n")
EOF

# Build Python package
rm -f dist/symbols_mcp-${CURRENT}*
uv build

# Publish to PyPI
if [ -f .pypirc ]; then
  source .pypirc
else
  read -rsp "PyPI token: " TOKEN; echo
fi
uv publish --token "$TOKEN"

# Publish to npm
if [ -z "$SKIP_NPM" ]; then
  chmod +x bin/symbols-mcp.js
  npm publish --access public
else
  echo "Skipping npm publish (SKIP_NPM set)"
fi

# Generate .mcpb bundle
./generate-mcpb.sh

# Publish to MCP registry
echo "Publishing to MCP registry..."
mcp-publisher login github
mcp-publisher publish

# Commit, tag and push
git add .
git commit -m "chore: release v$NEW"
git tag "v$NEW"
git push && git push --tags

echo "Done! Published symbols-mcp $NEW"
