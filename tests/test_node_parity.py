"""The Node server prints the same bytes as the Python server for every part.

Both servers cut the skills with the same splitter, write the same head
(`<!-- section NAME part i of n (N bytes) -->`, N grouped as 45,000) and the
same continuation line, and cut the core into the same 2 parts. The Python
server printed "79,546 chars", the Node one "79546 chars"; a client got two
answers for one call depending on the package it installed.

Driven over stdio JSON-RPC. Skipped when `node` is not installed.
"""

import importlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

server = importlib.import_module("symbols_mcp.server")

ROOT = Path(__file__).resolve().parent.parent
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"
CAP = server.RULES_SAFE_BYTES

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _bytes(text):
    return len(text.encode("utf-8"))


def _node(calls):
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, (name, args) in enumerate(calls, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}}))
    proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    replies = {}
    for line in proc.stdout.splitlines():
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg["result"]
    return [replies[i] for i in range(1, len(calls) + 1)]


def _text(result):
    assert len(result["content"]) == 1
    return result["content"][0]["text"]


def test_every_skill_part_is_the_same_bytes_in_both_servers():
    calls, expected = [], []
    for path in sorted(server.SKILLS_PATH.glob("*.md")):
        n = len(server._split_markdown_parts(path.read_text(encoding="utf-8")))
        for i in range(1, n + 1):
            calls.append(("get_project_rules", {"section": path.stem, "part": i}))
            expected.append(server.get_project_rules(section=path.stem, part=i))
    for tool, name in (("get_cli_reference", "CLI"),):
        n = len(server._split_markdown_parts(server._read_skill(f"{name}.md")))
        for i in range(1, n + 1):
            calls.append((tool, {"part": i}))
            expected.append(getattr(server, tool)(part=i))
    for (name, args), result, want in zip(calls, _node(calls), expected):
        got = _text(result)
        assert got == want, (name, args)
        assert _bytes(got) <= CAP, (name, args, _bytes(got))


def test_the_core_is_two_parts_in_both_servers():
    one, two, zero, three = _node([
        ("get_project_rules", {}), ("get_project_rules", {"part": 2}),
        ("get_project_rules", {"part": 0}), ("get_project_rules", {"part": 3}),
    ])
    p1, p2 = server.get_project_rules(), server.get_project_rules(part=2)
    assert _text(one) == p1  # the same bytes, the same STRICT rules in part 1
    node_p2 = _text(two)
    assert _bytes(node_p2) <= CAP
    # Part 2's index rows carry each server's own section descriptions; the
    # STRICT rules and the heading index before them are the same bytes.
    cut = p2.index("# SECTION INDEX")
    assert node_p2[:cut] == p2[:cut]
    for result in (zero, three):
        assert result.get("isError") and "out of range" in _text(result)
