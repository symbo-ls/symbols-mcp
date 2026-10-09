"""The Node server answers every request before it exits on stdin close.

A client that writes its requests and closes stdin (a script, a CI probe)
got a cut reply for a large result: the server exited on close while a
macOS stdout pipe still held the tail of the full rules bundle.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "bin" / "symbols-mcp.cjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


@pytest.mark.parametrize("run", range(3))
def test_large_reply_is_complete_after_stdin_closes(run):
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "get_project_rules", "arguments": {"full": True}}}),
    ]
    proc = subprocess.run(["node", str(SERVER)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    replies = [json.loads(l) for l in proc.stdout.split("\n") if l.startswith("{")]
    assert [r["id"] for r in replies] == [0, 1]
    assert len(replies[1]["result"]["content"][0]["text"]) > 300_000
