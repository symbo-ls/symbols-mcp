#!/usr/bin/env bash
set -e

# Usage: ./publish.sh [patch|minor|major|x.y.z]
# Stores PyPI token in .pypi_token (gitignored)

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
sed -i '' "s/\"version\": \"$CURRENT\"/\"version\": \"$NEW\"/g" server.json
sed -i '' "s/\"version\": \"$CURRENT\"/\"version\": \"$NEW\"/" package.json

# Build Python package
rm -f dist/symbols_mcp-${CURRENT}*
uv build

# Publish to PyPI
if [ -f .pypi_token ]; then
  TOKEN=$(cat .pypi_token)
else
  read -rsp "PyPI token: " TOKEN; echo
fi
uv publish --token "$TOKEN"

# Publish to npm
chmod +x bin/symbols-mcp.js
npm publish --access public

# Generate .mcpb bundle
./generate-mcpb.sh

# Publish to MCP registry
echo "Publishing to MCP registry..."
mcp-publisher publish

echo "Done! Published symbols-mcp $NEW"
