"""The Node server (`bin/symbols-mcp.cjs`, the npm package and the .mcpb
bundle) exposes the same `audit_component` tool with the same `file_path`
argument. Its checks are regexes, and three of them only make sense for
some files: "components must be plain objects" (a `functions/` file returns
objects from functions by design), "use named exports" (app.js, state.js,
config.js and designSystem files export a default) and "no imports between
project files" (index.js, context.js and app.js are where imports belong).

Driven over stdio JSON-RPC, the way an MCP client talks to it. Skipped when
`node` is not installed.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "bin" / "symbols-mcp.cjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

FUNCTION_RETURNING_AN_OBJECT = """export const cardProps = function cardProps (label) {
  return { padding: 'A', text: label }
}
"""

DEFAULT_EXPORT = "export default { lang: 'en' }\n"

CONTEXT_FILE = """import * as components from './components/index.js'
export default { components }
"""

PLAIN_OBJECTS = "Components must be plain objects"
NAMED_EXPORTS = "Components should use named exports"
NO_IMPORTS = "No imports between project files"


def _rpc(*requests):
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, (method, params) in enumerate(requests, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params}))
    proc = subprocess.run(
        ["node", str(SERVER)], input="\n".join(lines) + "\n",
        capture_output=True, text=True, timeout=60,
    )
    replies = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg
    return replies


def _audit(code, file_path=None):
    args = {"component_code": code}
    if file_path is not None:
        args["file_path"] = file_path
    reply = _rpc(("tools/call", {"name": "audit_component", "arguments": args}))[1]
    text = reply["result"]["content"][0]["text"]
    # The findings end where the rules reference (AUDIT.md) begins.
    return text.split("## Detailed Rules Reference")[0]


def test_schema_declares_the_optional_file_path():
    tools = _rpc(("tools/list", {}))[1]["result"]["tools"]
    tool = next(t for t in tools if t["name"] == "audit_component")
    assert "file_path" in tool["inputSchema"]["properties"]
    assert tool["inputSchema"]["required"] == ["component_code"]


def test_a_functions_file_is_not_a_component():
    assert PLAIN_OBJECTS in _audit(FUNCTION_RETURNING_AN_OBJECT)  # default: a component
    report = _audit(FUNCTION_RETURNING_AN_OBJECT, "functions/cardProps.js")
    assert PLAIN_OBJECTS not in report
    assert "Audited as: `functions/cardProps.js`" in report


@pytest.mark.parametrize("given, audited", [
    ("functions/", "functions/cardProps.js"),
    ("functions", "functions/cardProps.js"),
    ("./symbols/functions/cardProps.js", "functions/cardProps.js"),
    ("/home/me/app/symbols/functions/cardProps.js", "functions/cardProps.js"),
    ("../../etc/passwd.js", "components/cardProps.js"),
])
def test_the_path_is_read_like_the_python_server(given, audited):
    assert f"Audited as: `{audited}`" in _audit(FUNCTION_RETURNING_AN_OBJECT, given)


@pytest.mark.parametrize("path", ["state.js", "app.js", "config.js", "designSystem/color.js", "pages/index.js"])
def test_default_exports_are_fine_outside_components(path):
    assert NAMED_EXPORTS in _audit(DEFAULT_EXPORT)
    assert NAMED_EXPORTS not in _audit(DEFAULT_EXPORT, path)


def test_imports_are_fine_in_the_files_that_aggregate():
    assert NO_IMPORTS in _audit(CONTEXT_FILE)
    assert NO_IMPORTS not in _audit(CONTEXT_FILE, "context.js")
    assert NO_IMPORTS in _audit(CONTEXT_FILE, "components/Card.js")
