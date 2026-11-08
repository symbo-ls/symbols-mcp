"""The tools whose answer is Markdown text send one text block, no structuredContent.

FastMCP gives every `-> str` tool an automatic output schema and sends the
answer twice: as a TextContent block and as structuredContent
`{"result": "..."}`. Claude Code shows the model the structured copy — the
escaped JSON string, every newline and quote escaped — so a Markdown answer
reached the model as one long JSON line, and longer than the text. The text
tools are registered with `structured_output=False`; the tools whose answer is
JSON data keep their schema.

Every tool is classified here by what its code returns. A new tool fails
test_every_tool_is_classified until it is added to one list.
"""

import asyncio
import importlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

server = importlib.import_module("symbols_mcp.server")

ROOT = Path(__file__).resolve().parent.parent
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"

# Markdown text (the docs, frames, reports and status lines a model reads),
# with the arguments of a call that needs no network.
TEXT_TOOLS = {
    "get_project_rules": {},
    "generate_component": {"description": "a pricing card"},
    "generate_page": {"description": "a pricing page"},
    "convert_react": {"source_code": "export const A = () => <div>Hi</div>"},
    "convert_html": {"source_code": "<div><p>Hi</p></div>"},
    "audit_component": {"component_code": "export const A = { padding: 'A' }"},
    "get_cli_reference": {},
    "get_sdk_reference": {},
    "audit_project": {"phase": "1"},
    "convert_to_json": {"source_code": "export const A = { padding: 'A' }"},
    "detect_environment": {"has_cdn_import": True},
    "login": {"email": "agent@example.test", "password": "not-a-real-password"},
    "list_projects": {},
    "create_project": {"name": "x"},
    "get_project": {"project": "pr_x"},
    "save_to_project": {"project": "pr_x", "changes": "{}"},
    "publish": {"project": "pr_x"},
    "push": {"project": "pr_x"},
}

# JSON data (json.dumps of a result object), schema kept.
DATA_TOOLS = {
    "search_symbols_docs",
    "audit_and_fix_frankability",
    "prescribe_frankability_fixes",
    "apply_frankability_edit_ops",
    "verify_frankability",
    "rollback_frankability",
    "snapshots_frankability",
    "frankability_log",
    "explain_frankability_rule",
    "get_project_context",
}


class _FakeResponse:
    status_code = 401

    def json(self):
        return {"success": False, "error": "invalid credentials"}


class _FakeClient:
    """httpx.AsyncClient stand-in: login answers without the network."""

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, *a, **kw):
        return _FakeResponse()


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(server.httpx, "AsyncClient", _FakeClient)
    monkeypatch.setattr(server, "_run_frank_audit", lambda *a, **kw: {"ok": True, "findings": []})
    monkeypatch.setattr(server, "_structural_checks", lambda code: [])


async def _list_and_call(calls):
    async with create_connected_server_and_client_session(server.mcp) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        results = {name: await client.call_tool(name, args) for name, args in calls.items()}
    return tools, results


def test_every_tool_is_classified():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert len(names) == 28
    assert not set(TEXT_TOOLS) & DATA_TOOLS
    assert names == set(TEXT_TOOLS) | DATA_TOOLS


def test_text_tools_send_one_text_block_and_no_structured_content(offline):
    tools, results = asyncio.run(_list_and_call(TEXT_TOOLS))
    for name in TEXT_TOOLS:
        assert tools[name].outputSchema is None, name
        result = results[name]
        assert not result.isError, (name, result.content)
        assert result.structuredContent is None, name
        assert len(result.content) == 1 and isinstance(result.content[0], TextContent), name
        assert result.content[0].text.strip(), name


def test_data_tools_keep_their_schema(offline, tmp_path):
    (tmp_path / "symbols.json").write_text('{"owner":"o","key":"k"}')
    calls = {"get_project_context": {"cwd": str(tmp_path)}, "search_symbols_docs": {"query": "childrenAs"}}
    tools, results = asyncio.run(_list_and_call(calls))
    for name in DATA_TOOLS:
        assert tools[name].outputSchema, name
    for name in calls:
        structured = results[name].structuredContent
        assert structured and json.loads(structured["result"]), name


def test_an_error_is_one_text_block_too():
    async def run():
        async with create_connected_server_and_client_session(server.mcp) as client:
            return await client.call_tool("get_project_rules", {"section": "NO_SUCH_SECTION"})
    result = asyncio.run(run())
    assert result.isError and result.structuredContent is None
    assert len(result.content) == 1 and "Unknown section" in result.content[0].text


# The Node server (bin/symbols-mcp.cjs: the npm package and the .mcpb bundle)
# sends every answer as one text block and declares no output schema.
NODE_TEXT_TOOLS = {
    name: args for name, args in TEXT_TOOLS.items()
    if name not in {"audit_project"}  # not in the Node server
}


def _node_rpc(requests, env=None):
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, (method, params) in enumerate(requests, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params}))
    proc = subprocess.run(
        ["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
        capture_output=True, text=True, timeout=60, env=env,
    )
    replies = {}
    for line in proc.stdout.splitlines():
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg
    return replies


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_text_tools_send_one_text_block():
    import os
    # login reaches API_BASE; point it at a closed local port so the call
    # fails fast without the network.
    env = {**os.environ, "SYMBOLS_API_URL": "http://127.0.0.1:9"}
    names = list(NODE_TEXT_TOOLS)
    r = _node_rpc([("tools/list", {})] + [("tools/call", {"name": n, "arguments": NODE_TEXT_TOOLS[n]}) for n in names], env)
    tools = {t["name"]: t for t in r[1]["result"]["tools"]}
    assert set(names) <= set(tools)
    for t in tools.values():
        assert "outputSchema" not in t, t["name"]
    for i, name in enumerate(names, start=2):
        result = r[i]["result"]
        assert "structuredContent" not in result, name
        assert len(result["content"]) == 1 and result["content"][0]["type"] == "text", name
