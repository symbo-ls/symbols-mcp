#!/usr/bin/env bash
# CI test gate — run by the org test-reusable.yml. Validates the Python
# surface (imports, tool registration, skills bundle) so dependabot's
# Python bumps are actually exercised, not install-only smoked.
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --frozen
uv run pytest -q tests/
