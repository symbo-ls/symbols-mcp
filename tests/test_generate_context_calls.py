"""generate_component / generate_page / convert_react / convert_html name the
get_project_rules calls for their context instead of inlining it, in two
groups.

Each tool inlined whole skill files: 678,000 to 704,000 bytes per answer, 15
times what Claude Code passes to the model inline (it saves an answer over
50,000 chars to a file). The default answer is now the task frame (as before)
and a Context section:
- "Before you write code": every call for the 2 core parts and every part of
  SYNTAX, COMPONENTS and FRANKABILITY (convert_react: and MIGRATION);
- "When the task needs it": one line per other skill of the tool's list, in
  the list's order: its name, its parts and bytes, what it holds (its
  RULES_SECTIONS description, else the skill file's `# ` title) and its first
  exact call; each part names the next.
The section carries the line "Skip a call that you already made in this
session." `full=True` returns the old one-shot answer. The Node server prints
the same bytes as this server for every answer (server.py is canonical).
tests/test_frame_calls.py runs every call the answers name.

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
SKIP = "Skip a call that you already made in this session."
BEFORE = ("SYNTAX.md", "COMPONENTS.md", "FRANKABILITY.md")

TOOLS = {
    "generate_component": ({"description": "A pricing card with a title and a button", "component_name": "PriceCard"},
                           server.GENERATE_COMPONENT_SKILLS, BEFORE, "## Context — Rules, Syntax & Examples"),
    "generate_page": ({"description": "A pricing page", "page_name": "pricing"},
                      server.GENERATE_PAGE_SKILLS, BEFORE, "## Context — Rules, Structure, Patterns & Snippets"),
    "convert_react": ({"source_code": "export const A = () => <div className='x'>Hi</div>"},
                      server.CONVERT_REACT_SKILLS, BEFORE + ("MIGRATION.md",), "## Context — Migration Guide, Syntax & Rules"),
    "convert_html": ({"source_code": "<div class='x'><p>Hi</p></div>"},
                     server.CONVERT_HTML_SKILLS, BEFORE, "## Context — Syntax, Components & Design System"),
}

CALL = re.compile(r"^\d+\. `(get_project_rules\([^`]*\))` — ", re.M)
LINE = re.compile(r"^- `([A-Z_]+)` \(.*$", re.M)


def _bytes(text):
    return len(text.encode("utf-8"))


def _parts(fname):
    return len(server._split_markdown_parts(server._read_skill(fname)))


def _expected_before(before):
    calls = ["get_project_rules()", "get_project_rules(part=2)"]
    for fname in before:
        name, n = fname[:-3], _parts(fname)
        calls += [f"get_project_rules(section='{name}')"] if n == 1 else [
            f"get_project_rules(section='{name}', part={i})" for i in range(1, n + 1)
        ]
    return calls


def _expected_line(fname):
    name, text, n = fname[:-3], server._read_skill(fname), _parts(fname)
    desc = dict((s, d) for s, _, d in server.RULES_SECTIONS).get(name)
    if desc is None:
        desc = next(line[2:].strip() for line in text.split("\n") if line.startswith("# "))
    size = f"{n} part{'s' if n > 1 else ''}, {_bytes(text):,} bytes"
    call = (f"Call: `get_project_rules(section='{name}')`." if n == 1
            else f"First call: `get_project_rules(section='{name}', part=1)`.")
    return f"- `{name}` ({size}): {desc}. {call}"


def _answer(name, **extra):
    args = TOOLS[name][0]
    return getattr(server, name)(**args, **extra)


def _groups(name):
    out = _answer(name)
    heading = TOOLS[name][3]
    context = out[out.index(heading):]
    before = context[context.index("### Before you write code"):context.index("### When the task needs it")]
    later = context[context.index("### When the task needs it"):]
    return out, context, before, later


@pytest.mark.parametrize("name", TOOLS)
def test_the_default_answer_fits_the_cap(name):
    out = _answer(name)
    assert _bytes(out) <= CAP, (name, _bytes(out))


@pytest.mark.parametrize("name", TOOLS)
def test_the_skip_line_and_the_two_groups_in_order(name):
    out, context, _, _ = _groups(name)
    assert out.count(TOOLS[name][3]) == 1
    assert context.count(SKIP) == 1
    assert context.index(SKIP) < context.index("### Before you write code") < context.index("### When the task needs it")


@pytest.mark.parametrize("name", TOOLS)
def test_before_code_names_every_call_of_the_core_and_the_minimum_skills(name):
    _, _, before, _ = _groups(name)
    assert CALL.findall(before) == _expected_before(TOOLS[name][2])


@pytest.mark.parametrize("name", TOOLS)
def test_one_line_per_other_skill_in_the_list_order(name):
    _, _, before, later = _groups(name)
    _, skills, first, _ = TOOLS[name]
    expected = [f for f in skills if f not in first]
    assert LINE.findall(later) == [f[:-3] for f in expected]
    lines = [line for line in later.split("\n") if line.startswith("- `")]
    assert lines == [_expected_line(f) for f in expected]
    assert not CALL.findall(later)  # the later skills are one line each, not every part


@pytest.mark.parametrize("name", TOOLS)
def test_every_named_call_runs_and_fits_the_cap(name):
    out = _answer(name)
    calls = re.findall(r"`(get_project_rules\([^`]*\))`", out)
    assert calls
    for call in calls:
        args = dict(re.findall(r"(\w+)=('[^']*'|\d+)", call))
        kwargs = {k: (v.strip("'") if v.startswith("'") else int(v)) for k, v in args.items()}
        answer = server.get_project_rules(**kwargs)
        assert _bytes(answer) <= CAP, (call, _bytes(answer))


@pytest.mark.parametrize("name", TOOLS)
def test_nothing_is_inlined(name):
    out = _answer(name)
    for fname in TOOLS[name][1] + TOOLS[name][2]:
        assert server._read_skill(fname)[:2000] not in out, fname


@pytest.mark.parametrize("name", TOOLS)
def test_full_true_is_the_one_shot_answer(name):
    _, skills, _, heading = TOOLS[name]
    full = _answer(name, full=True)
    frame = _answer(name).split(heading)[0]
    assert full == frame + heading + "\n\n" + server._read_skills(*skills)
    assert _bytes(full) > CAP  # why the default names calls


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


# Inputs with the characters a port can get wrong: backticks, `${`, a backslash.
ODD = {
    "generate_component": [{"description": "A `card` with ${price} and a \\ slash", "component_name": "PriceCard"},
                           {"description": "no name given"}],
    "generate_page": [{"description": "A `page` with ${x}", "page_name": "pricing"}, {"description": "no name"}],
    "convert_react": [{"source_code": "export const A = () => <div className={`x ${y}`}>\\n</div>"}],
    "convert_html": [{"source_code": "<p class='x'>${a} `b` \\c</p>"}],
}


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_node_prints_the_same_bytes():
    requests = [(n, a) for n in TOOLS for a in [TOOLS[n][0], *ODD[n]]]
    for (name, args), result in zip(requests, _node(requests)):
        assert len(result["content"]) == 1 and not result.get("isError"), (name, args)
        assert result["content"][0]["text"] == getattr(server, name)(**args), (name, args)


# One tool per run: a full=True answer is several hundred thousand chars.
@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("name", TOOLS)
def test_node_full_true_is_the_same_bytes(name):
    args = {**ODD[name][0], "full": True}
    (result,) = _node([(name, args)])
    assert result["content"][0]["text"] == getattr(server, name)(**args), name
