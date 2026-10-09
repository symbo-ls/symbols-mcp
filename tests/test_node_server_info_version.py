"""The Node server reports the package version in initialize.serverInfo.

It answered '1.0.15' (a hand-kept constant) while the package was 3.14.77x,
so a client could not tell which release it was talking to.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "bin" / "symbols-mcp.cjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def test_server_info_version_is_package_version():
    pkg_version = json.loads((ROOT / "package.json").read_text())["version"]
    line = json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                       "params": {"protocolVersion": "2025-03-26"}})
    proc = subprocess.run(["node", str(SERVER)], input=line + "\n",
                          capture_output=True, text=True, timeout=30)
    replies = [json.loads(l) for l in proc.stdout.split("\n") if l.startswith("{")]
    assert replies and replies[0]["id"] == 0
    info = replies[0]["result"]["serverInfo"]
    assert info["name"] == "Symbols MCP"
    assert info["version"] == pkg_version
    assert info["version"] != "1.0.15"
