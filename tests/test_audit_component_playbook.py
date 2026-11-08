"""audit_component names the get_project_rules calls for the audit playbook
instead of inlining AUDIT.md, in both servers.

include_playbook=True appended the whole AUDIT.md (43,751 bytes) to the
report: 44,410 bytes with a clean report, over the 45,000-byte cap from a few
findings on. The Node server appended it to EVERY answer (its schema had no
include_playbook): 44,088 bytes for a one-finding report. Now both servers
return only the findings by default, and include_playbook=True appends the
playbook block: the line "Skip a call that you already made in this
session." and every get_project_rules call for AUDIT.md (each part, in
order). The block is the same bytes in both servers.
tests/test_frame_calls.py runs every call the answers name.
"""

import importlib
import json
import os
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
HEAD = "\n---\n\n## Audit Playbook (AUDIT.md)\n\n"
CODE = "export const PriceCard = {\n  padding: 'A',\n  color: '#ff0000'\n}\n"
FILE = "components/PriceCard.js"
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _bytes(text):
    return len(text.encode("utf-8"))


def _expected_block(text):
    """The playbook block for an AUDIT.md of this text, built from the
    splitter's part count (not from the server's helpers)."""
    n = len(server._split_markdown_parts(text))
    if n == 1:
        lines = ["1. `get_project_rules(section='AUDIT')` — AUDIT.md"]
    else:
        lines = [f"{i}. `get_project_rules(section='AUDIT', part={i})` — AUDIT.md, part {i} of {n}"
                 for i in range(1, n + 1)]
    return HEAD + SKIP + "\n\nThe playbook is not inlined. Make these calls, in this order:\n\n" + "\n".join(lines) + "\n"


def _big_playbook():
    """A synthetic AUDIT.md about 3 times the per-part budget."""
    body = "".join(f"## Phase {i}\n\n" + ("Check every finding of this phase. " * 300) + "\n\n" for i in range(12))
    return "# Symbols Project Audit\n\n" + body


@pytest.fixture
def stub_audit(monkeypatch):
    """No frank-audit subprocess, no network: one finding on the file."""
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    finding = {"ruleId": "FA301", "file": FILE, "line": 3, "severity": "critical", "message": "Raw hex color"}
    monkeypatch.setattr(server, "_run_frank_audit",
                        lambda *a, **k: {"schema": "frank-audit/1.0", "ok": True, "findings": [finding]})


def test_the_default_answer_has_no_playbook(stub_audit):
    out = server.audit_component(CODE, file_path=FILE)
    assert "## Audit Playbook" not in out
    assert "section='AUDIT'" not in out
    assert server._read_skill("AUDIT.md")[:2000] not in out


def test_include_playbook_names_every_call_and_inlines_none(stub_audit):
    plain = server.audit_component(CODE, file_path=FILE)
    out = server.audit_component(CODE, include_playbook=True, file_path=FILE)
    assert out == plain + _expected_block(server._read_skill("AUDIT.md"))
    assert _bytes(out) <= CAP
    assert server._read_skill("AUDIT.md")[:2000] not in out
    calls = re.findall(r"`(get_project_rules\([^`]*\))`", out[len(plain):])
    assert calls
    for call in calls:
        args = dict(re.findall(r"(\w+)=('[^']*'|\d+)", call))
        kwargs = {k: (v.strip("'") if v.startswith("'") else int(v)) for k, v in args.items()}
        assert _bytes(server.get_project_rules(**kwargs)) <= CAP, call


def test_a_playbook_in_parts_names_every_part(stub_audit, monkeypatch, tmp_path):
    big = _big_playbook()
    (tmp_path / "AUDIT.md").write_text(big, encoding="utf-8")
    monkeypatch.setattr(server, "SKILLS_PATH", tmp_path)
    n = len(server._split_markdown_parts(big))
    assert n >= 3
    plain = server.audit_component(CODE, file_path=FILE)
    out = server.audit_component(CODE, include_playbook=True, file_path=FILE)
    assert out == plain + _expected_block(big)
    for i in range(1, n + 1):
        assert _bytes(server.get_project_rules(section="AUDIT", part=i)) <= CAP, i


# ---------------------------------------------------------------- the Node server

def _node(server_js, requests):
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, (method, params) in enumerate(requests, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params}))
    proc = subprocess.run(["node", str(server_js)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    replies = {}
    for line in proc.stdout.splitlines():
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg["result"]
    return [replies[i] for i in range(1, len(requests) + 1)]


def _audit_call(**extra):
    return ("tools/call", {"name": "audit_component",
                           "arguments": {"component_code": CODE, "file_path": FILE, **extra}})


def _text(result):
    assert len(result["content"]) == 1 and not result.get("isError"), result
    return result["content"][0]["text"]


@needs_node
def test_node_schema_takes_include_playbook():
    (listing,) = _node(NODE_SERVER, [("tools/list", {})])
    tool = next(t for t in listing["tools"] if t["name"] == "audit_component")
    prop = tool["inputSchema"]["properties"]["include_playbook"]
    assert prop["type"] == "boolean" and prop["default"] is False
    assert tool["inputSchema"]["required"] == ["component_code"]


@needs_node
def test_node_adds_the_same_block_only_with_include_playbook():
    default, off, on = (_text(r) for r in _node(NODE_SERVER, [
        _audit_call(), _audit_call(include_playbook=False), _audit_call(include_playbook=True)]))
    assert "## Audit Playbook" not in default and "## Detailed Rules Reference" not in default
    assert server._read_skill("AUDIT.md")[:2000] not in default
    assert off == default
    assert on == default + server._playbook_block()
    assert on == default + _expected_block(server._read_skill("AUDIT.md"))
    assert _bytes(on) <= CAP


@needs_node
def test_node_names_every_part_of_a_playbook_in_parts(tmp_path):
    """A scratch copy of the Node server whose skills dir holds a big AUDIT.md
    (the other skills are links to the real ones)."""
    skills = tmp_path / "symbols_mcp" / "skills"
    skills.mkdir(parents=True)
    for path in server.SKILLS_PATH.iterdir():
        if path.name != "AUDIT.md":
            os.symlink(path, skills / path.name)
    big = _big_playbook()
    (skills / "AUDIT.md").write_text(big, encoding="utf-8")
    os.symlink(ROOT / "symbols_mcp" / "checks", tmp_path / "symbols_mcp" / "checks")
    os.symlink(ROOT / "package.json", tmp_path / "package.json")
    (tmp_path / "bin").mkdir()
    shutil.copy(NODE_SERVER, tmp_path / "bin" / "symbols-mcp.cjs")
    n = len(server._split_markdown_parts(big))
    requests = [_audit_call(), _audit_call(include_playbook=True)]
    requests += [("tools/call", {"name": "get_project_rules", "arguments": {"section": "AUDIT", "part": i}})
                 for i in range(1, n + 1)]
    results = _node(tmp_path / "bin" / "symbols-mcp.cjs", requests)
    default, on = _text(results[0]), _text(results[1])
    assert on == default + _expected_block(big)
    for i, result in enumerate(results[2:], start=1):
        assert _bytes(_text(result)) <= CAP, i
