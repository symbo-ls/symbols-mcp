"""Smoke suite — validates that a Python dependency bump leaves the server
importable and its tool surface intact. This is the gate CI runs via
scripts/test.sh; it deliberately avoids network and stdio transport."""

import importlib
from pathlib import Path

import symbols_mcp


def test_package_imports():
    assert symbols_mcp is not None


def test_server_module_imports_and_builds_fastmcp():
    server = importlib.import_module("symbols_mcp.server")
    assert server.mcp is not None
    assert server.mcp.name


def test_tool_surface_registered():
    server = importlib.import_module("symbols_mcp.server")
    import asyncio

    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    # Core tools the org's agents depend on — a dep bump that silently drops
    # tool registration must fail here.
    expected = {"get_project_context", "get_project_rules", "audit_component"}
    missing = expected - names
    assert not missing, f"missing tools: {missing}"
    assert len(names) >= 10


def test_skills_bundle_present():
    skills = Path(symbols_mcp.__file__).parent / "skills"
    md = list(skills.glob("*.md"))
    assert len(md) >= 5, f"skills bundle looks empty: {len(md)} .md files"
