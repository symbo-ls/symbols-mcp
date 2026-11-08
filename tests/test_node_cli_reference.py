"""The Node server (`bin/symbols-mcp.cjs`, the npm package and the .mcpb
bundle) serves get_cli_reference in parts, like the Python server: CLI.md is
above Claude Code's MAX_MCP_OUTPUT_TOKENS cap, so the whole file in one answer
never reached the model.

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

CAP = 80_000 + 200  # RULES_SAFE_CHARS + the head and continuation lines


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


def _call(arguments):
    return ("tools/call", {"name": "get_cli_reference", "arguments": arguments})


def test_get_cli_reference_takes_a_part_and_each_part_fits_the_cap():
    r = _rpc(("tools/list", {}), _call({}), _call({"part": 1}), _call({"part": 2}), _call({"part": 0}))
    tool = next(t for t in r[1]["result"]["tools"] if t["name"] == "get_cli_reference")
    part = tool["inputSchema"]["properties"]["part"]
    assert part["type"] == "number" and part.get("default") == 1
    assert not tool["inputSchema"].get("required")

    no_arg, first, second, zero = (r[i]["result"] for i in (2, 3, 4, 5))
    assert no_arg["content"][0]["text"] == first["content"][0]["text"]
    assert "<!-- continues: get_cli_reference(part=2)" in first["content"][0]["text"]
    assert not second.get("isError")
    text = second["content"][0]["text"]
    assert text.startswith("<!-- section CLI part 2/")
    assert len(text) <= CAP, len(text)
    # part 0 is out of range here, as in the Python server
    assert zero.get("isError") and "out of range" in zero["content"][0]["text"]
