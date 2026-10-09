"""The rules name the smbls build their key examples were checked against.

symbols_mcp/skills/runtime-checked.json is written by
scripts/check-runtime-examples.sh only after tests/runtime_examples/run.mjs
passes on a built smbls. Both core bundles (Python and Node) quote it.

With SYMBOLS_SMBLS_TREE pointing at a smbls checkout whose
packages/smbls/dist is built, the examples run here too, and a stamp that
names another smbls version fails: re-run the script and fix the docs it
flags. Without the variable that half is skipped.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from symbols_mcp import server

ROOT = Path(__file__).resolve().parent.parent
STAMP = ROOT / "symbols_mcp" / "skills" / "runtime-checked.json"
RUNNER = ROOT / "tests" / "runtime_examples" / "run.mjs"
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"
TREE = os.environ.get("SYMBOLS_SMBLS_TREE", "")


def _stamp():
    return json.loads(STAMP.read_text(encoding="utf-8"))


def test_stamp_is_well_formed():
    stamp = _stamp()
    assert re.fullmatch(r"\d+\.\d+\.\d+", stamp["smbls"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp["checked"])
    assert {"isxRootState", "vars", "stateDeps"} <= set(stamp["examples"])


def test_python_core_bundle_names_the_runtime():
    stamp = _stamp()
    core = server._rules_core_bundle()
    line = f"checked against smbls {stamp['smbls']} ({stamp['checked']})"
    assert line in core
    assert core.index(line) < core.index("---")  # in the header, before the bundle


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_core_bundle_names_the_runtime():
    stamp = _stamp()
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "get_project_rules", "arguments": {}}}),
    ]
    proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    reply = next(json.loads(l) for l in proc.stdout.split("\n") if l.startswith("{") and '"id":1' in l)
    text = reply["result"]["content"][0]["text"]
    assert f"checked against smbls {stamp['smbls']} ({stamp['checked']})" in text


def test_missing_stamp_drops_the_line(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "SKILLS_PATH", tmp_path)
    assert server._runtime_checked_line() == ""


@pytest.mark.skipif(not TREE, reason="set SYMBOLS_SMBLS_TREE to a smbls checkout with dist built")
@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_documented_examples_run_on_the_built_runtime():
    proc = subprocess.run(["node", str(RUNNER), TREE], capture_output=True, text=True, timeout=300)
    out = proc.stdout.strip().splitlines()
    assert out, proc.stderr
    result = json.loads(out[-1])
    failed = [c for c in result["cases"] if not c["ok"]]
    assert not failed, failed
    assert result["smbls"]["version"] == _stamp()["smbls"], (
        "runtime-checked.json names another smbls version; "
        "run scripts/check-runtime-examples.sh <smbls-tree> and commit the stamp"
    )
