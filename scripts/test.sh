#!/usr/bin/env bash
# CI test gate — run by the org test-reusable.yml. Validates the Python
# surface (imports, tool registration, skills bundle) so dependabot's
# Python bumps are actually exercised, not install-only smoked.
#
# The shared runner image is node/bun-oriented and ships no `uv`
# ("uv: command not found", exit 127 — 2026-08-02), so resolve one in
# order of preference. uv is strongly preferred over a plain venv
# because it provisions the interpreter this project requires
# (>=3.10) by itself; a runner whose system python3 is older can still
# run the suite that way.
set -euo pipefail
cd "$(dirname "$0")/.."

UV=""
if command -v uv >/dev/null 2>&1; then
  UV="uv"
elif python3 -m uv --version >/dev/null 2>&1; then
  UV="python3 -m uv"
elif python3 -m pip install --quiet --disable-pip-version-check uv >/dev/null 2>&1 \
  && python3 -m uv --version >/dev/null 2>&1; then
  UV="python3 -m uv"
fi

if [ -n "$UV" ]; then
  $UV sync --frozen
  exec $UV run pytest -q tests/
fi

# No uv available. The venv fallback can only work when the system
# interpreter already satisfies requires-python — fail loudly rather
# than reporting a green check that ran nothing.
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "unknown")
  echo "::error::Cannot run the Python suite: uv is unavailable and python3 is ${PYV} (<3.10)."
  echo "::error::Install uv on the runner (pip install uv) or provide python3 >=3.10."
  exit 1
fi

echo "uv unavailable; falling back to venv + pytest"
rm -rf .venv-ci
python3 -m venv .venv-ci
# shellcheck disable=SC1091
. .venv-ci/bin/activate
python -m pip install --quiet --disable-pip-version-check --upgrade pip
python -m pip install --quiet --disable-pip-version-check -e .
python -m pip install --quiet --disable-pip-version-check pytest
exec python -m pytest -q tests/
