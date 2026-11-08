"""The Node server (`bin/symbols-mcp.cjs`, the npm package and the .mcpb
bundle) serves get_cli_reference in parts, like the Python server: CLI.md is
above the inline cap, so the whole file in one answer never reached the model.

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

CAP = 45_000  # RULES_SAFE_BYTES: the whole answer, head and continuation lines included


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


@pytest.mark.parametrize("tool,name", [("get_cli_reference", "CLI")])
def test_the_reference_takes_a_part_and_each_part_fits_the_cap(tool, name):
    def call(arguments):
        return ("tools/call", {"name": tool, "arguments": arguments})

    r = _rpc(("tools/list", {}), call({}), call({"part": 1}), call({"part": 2}), call({"part": 0}))
    spec = next(t for t in r[1]["result"]["tools"] if t["name"] == tool)
    part = spec["inputSchema"]["properties"]["part"]
    assert part["type"] == "number" and part.get("default") == 1
    assert not spec["inputSchema"].get("required")

    no_arg, first, second, zero = (r[i]["result"] for i in (2, 3, 4, 5))
    assert no_arg["content"][0]["text"] == first["content"][0]["text"]
    assert f"<!-- continues: {tool}(part=2) (part 2 of " in first["content"][0]["text"]
    assert not second.get("isError")
    for result in (first, second):
        text = result["content"][0]["text"]
        assert len(text.encode("utf-8")) <= CAP, len(text.encode("utf-8"))
    assert second["content"][0]["text"].startswith(f"<!-- section {name} part 2 of ")
    # part 0 is out of range here, as in the Python server
    assert zero.get("isError") and "out of range" in zero["content"][0]["text"]
