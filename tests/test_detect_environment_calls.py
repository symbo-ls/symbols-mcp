"""detect_environment names the get_project_rules calls for its reference
skills instead of inlining them.

It inlined whole skill files: PROJECT_STRUCTURE + SHARED_LIBRARIES for a local
project (58,077 bytes per answer; 61,071 on the larger docs skills; the Node
server inlined RUNNING_APPS + SHARED_LIBRARIES, 56,595 bytes), RUNNING_APPS for
every other environment. Over 50,000 chars, Claude Code saves the answer to a
file and the model gets a 2,000-char preview. Now each answer ends with a
References block: the skip line and one line per reference skill (its parts
and bytes, what it holds, its first call). The Node server prints the same
bytes (server.py is canonical, DETECT_ENVIRONMENT_SKILLS included).
tests/test_frame_calls.py runs every call the answers name.
"""

import importlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

server = importlib.import_module("symbols_mcp.server")

ROOT = Path(__file__).resolve().parent.parent
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"
CAP = server.RULES_SAFE_BYTES
SKIP = "Skip a call that you already made in this session."
LOCAL = ["PROJECT_STRUCTURE", "SHARED_LIBRARIES"]
OTHER = ["RUNNING_APPS"]

# Every branch of the classification: (flags, env, confidence, named skills)
CASES = [
    ({"has_mermaid_config": True}, "remote_server", "high", OTHER),
    ({"has_json_data": True}, "json_runtime", "high", OTHER),
    ({"has_symbols_json": True, "has_symbols_dir": True}, "local_project", "high", LOCAL),
    ({"has_symbols_dir": True}, "local_project", "medium", LOCAL),
    ({"has_package_json": True, "has_symbols_json": True}, "local_project", "medium", LOCAL),
    ({"has_cdn_import": True}, "cdn", "high", OTHER),
    ({"has_iife_script": True}, "cdn", "high", OTHER),
    ({"has_package_json": True}, "local_project", "low", LOCAL),
    ({"file_list": "index.html, app.js"}, "cdn", "medium", OTHER),
    ({}, "unknown", "low", OTHER),
    ({"file_list": "README.md"}, "unknown", "low", OTHER),
]
IDS = [f"{env}-{conf}-{i}" for i, (_, env, conf, _) in enumerate(CASES)]


def _bytes(text):
    return len(text.encode("utf-8"))


@pytest.mark.parametrize("flags,env,confidence,skills", CASES, ids=IDS)
def test_the_answer_names_the_references_and_inlines_none(flags, env, confidence, skills):
    out = server.detect_environment(**flags)
    assert _bytes(out) <= CAP, _bytes(out)
    assert f"**Detected: {env}** (confidence: {confidence})" in out
    refs = out[out.index("### References"):]
    assert out.count("### References") == 1 and refs.count(SKIP) == 1
    assert re.findall(r"^- `([A-Z_]+)` \(", refs, re.M) == skills
    for name in skills:
        assert f"`get_project_rules(section='{name}'" in refs, name
    for fname in ("RUNNING_APPS.md", "PROJECT_STRUCTURE.md", "SHARED_LIBRARIES.md"):
        assert server._read_skill(fname)[:2000] not in out, fname


def test_every_environment_has_its_reference_skills():
    assert set(server.DETECT_ENVIRONMENT_SKILLS) == {env for _, env, _, _ in CASES}
    for env, skills in server.DETECT_ENVIRONMENT_SKILLS.items():
        for fname in skills:
            assert (server.SKILLS_PATH / fname).exists(), (env, fname)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_prints_the_same_bytes():
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, (flags, _, _, _) in enumerate(CASES, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                                 "params": {"name": "detect_environment", "arguments": flags}}))
    proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    replies = {}
    for line in proc.stdout.splitlines():
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg["result"]
    for i, (flags, _, _, _) in enumerate(CASES, start=1):
        result = replies[i]
        assert len(result["content"]) == 1 and not result.get("isError"), flags
        assert result["content"][0]["text"] == server.detect_environment(**flags), flags
