#!/usr/bin/env bash
set -e

# Install mcpb CLI if needed
if ! command -v mcpb &> /dev/null; then
  echo "Installing mcpb..."
  npm install -g @anthropic-ai/mcpb
fi

# Sync version from pyproject.toml into manifest.json
VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" manifest.json

# Pack the .mcpb bundle
mcpb pack

echo "Generated symbols-mcp-${VERSION}.mcpb"
