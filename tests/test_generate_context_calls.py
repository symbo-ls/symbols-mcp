"""generate_component / generate_page / convert_react / convert_html list the
get_project_rules calls for their context instead of inlining it.

Each tool inlined whole skill files: 678,000 to 704,000 bytes per answer, 15
times what Claude Code passes to the model inline (it saves an answer over
50,000 chars to a file). The default answer is now the task frame (as before)
plus a Context section: the 2 core parts, then every part of each skill the
tool used to inline, in the same order, from the splitter at call time. The
agent skips the calls already in its context. `full=True` returns the old
one-shot answer. The Node server names the same calls (server.py's skill
lists are canonical).

Known limit, not fixed here: the tools echo the description / source they are
given, so a very large input makes a large answer.
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

TOOLS = {
    "generate_component": ({"description": "A pricing card with a title and a button", "component_name": "PriceCard"},
                           server.GENERATE_COMPONENT_SKILLS, "## Context — Rules, Syntax & Examples"),
    "generate_page": ({"description": "A pricing page", "page_name": "pricing"},
                      server.GENERATE_PAGE_SKILLS, "## Context — Rules, Structure, Patterns & Snippets"),
    "convert_react": ({"source_code": "export const A = () => <div className='x'>Hi</div>"},
                      server.CONVERT_REACT_SKILLS, "## Context — Migration Guide, Syntax & Rules"),
    "convert_html": ({"source_code": "<div class='x'><p>Hi</p></div>"},
                     server.CONVERT_HTML_SKILLS, "## Context — Syntax, Components & Design System"),
}

CALL = re.compile(r"^\d+\. `(get_project_rules\([^`]*\))` — ", re.M)


def _bytes(text):
    return len(text.encode("utf-8"))


def _expected_calls(skills):
    calls = ["get_project_rules()", "get_project_rules(part=2)"]
    for fname in skills:
        name = fname[:-3]
        n = len(server._split_markdown_parts(server._read_skill(fname)))
        calls += [f"get_project_rules(section='{name}')"] if n == 1 else [
            f"get_project_rules(section='{name}', part={i})" for i in range(1, n + 1)
        ]
    return calls


def _run(call):
    """Run one listed call: get_project_rules(...) with its literal arguments."""
    args = dict(re.findall(r"(\w+)=('[^']*'|\d+)", call))
    kwargs = {k: (v.strip("'") if v.startswith("'") else int(v)) for k, v in args.items()}
    return server.get_project_rules(**kwargs)


def _answer(name, **extra):
    args, _, _ = TOOLS[name]
    return getattr(server, name)(**args, **extra)


@pytest.mark.parametrize("name", TOOLS)
def test_the_default_answer_fits_the_cap(name):
    out = _answer(name)
    assert _bytes(out) <= CAP, (name, _bytes(out))


@pytest.mark.parametrize("name", TOOLS)
def test_the_context_lists_the_core_then_every_part_of_each_skill_in_order(name):
    _, skills, heading = TOOLS[name]
    out = _answer(name)
    assert out.count(heading) == 1
    context = out[out.index(heading):]
    assert CALL.findall(context) == _expected_calls(skills)
    assert "Skip a call whose answer is already in your context" in context
    for fname in skills:  # nothing is inlined
        assert server._read_skill(fname)[:2000] not in out, fname


@pytest.mark.parametrize("name", TOOLS)
def test_every_listed_call_runs_and_fits_the_cap(name):
    out = _answer(name)
    for call in CALL.findall(out):
        answer = _run(call)
        assert _bytes(answer) <= CAP, (call, _bytes(answer))


@pytest.mark.parametrize("name", TOOLS)
def test_full_true_is_the_one_shot_answer(name):
    _, skills, heading = TOOLS[name]
    full = _answer(name, full=True)
    frame = _answer(name).split(heading)[0]
    assert full == frame + heading + "\n\n" + server._read_skills(*skills)
    assert _bytes(full) > CAP  # why the default lists calls


@pytest.mark.parametrize("name", TOOLS)
def test_the_tool_takes_full(name):
    import asyncio
    tool = next(t for t in asyncio.run(server.mcp.list_tools()) if t.name == name)
    assert tool.inputSchema["properties"]["full"]["default"] is False
    assert "full" not in tool.inputSchema.get("required", [])


def _node(requests):
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, (name, args) in enumerate(requests, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}}))
    proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    replies = {}
    for line in proc.stdout.splitlines():
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg["result"]
    return [replies[i] for i in range(1, len(requests) + 1)]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_lists_the_same_calls_and_each_fits_the_cap():
    names = list(TOOLS)
    answers = _node([(n, TOOLS[n][0]) for n in names])
    calls = []
    for name, result in zip(names, answers):
        text = result["content"][0]["text"]
        assert _bytes(text) <= CAP, (name, _bytes(text))
        listed = CALL.findall(text)
        assert listed == CALL.findall(_answer(name)), name  # the Python list, the Python order
        calls += [c for c in listed if c not in calls]
    # every listed call runs on the Node server and fits the cap
    def args_of(call):
        found = dict(re.findall(r"(\w+)=('[^']*'|\d+)", call))
        return {k: (v.strip("'") if v.startswith("'") else int(v)) for k, v in found.items()}
    for call, result in zip(calls, _node([("get_project_rules", args_of(c)) for c in calls])):
        assert not result.get("isError"), (call, result["content"][0]["text"][:200])
        assert _bytes(result["content"][0]["text"]) <= CAP, call


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_full_true_inlines_the_python_skill_lists():
    names = list(TOOLS)
    answers = _node([(n, {**TOOLS[n][0], "full": True}) for n in names])
    for name, result in zip(names, answers):
        _, skills, heading = TOOLS[name]
        text = result["content"][0]["text"]
        assert heading + "\n\n" + server._read_skills(*skills) in text, name
