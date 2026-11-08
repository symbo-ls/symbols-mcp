"""Every call that a frame names exists and fits the cap, in both servers.

The frames: the default answers of generate_component, generate_page,
convert_react and convert_html, detect_environment (one answer per
environment it detects) and audit_component(include_playbook=True). They
name the calls to make next instead of inlining skill files. The walk parses
every backticked tool call out of each frame, runs it in the same server
(Python: an in-memory MCP client session; Node: the stdio server) and follows
the `<!-- continues: ... -->` line of each answer to the next part, until no
new call is named. Each call must name a tool of that server, answer with no
error, and send one text block of at most 45,000 UTF-8 bytes (what Claude
Code passes to the model inline). The walk reaches every part of every skill
the frames name.

A backticked call to a name that is no tool of either server is code in the
frame (`el.router(...)`), not a call, unless the name has an underscore: then
it is a tool name with a typo. A named call whose arguments are not all
literals cannot run as written (there is none today): its tool must exist.
The answer of a named call is followed only through its continuation line:
the skill text in it is not a frame. test_the_walk_reports_each_bad_call
plants one call of each kind the walk must catch.
"""

import ast
import asyncio
import importlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

server = importlib.import_module("symbols_mcp.server")

ROOT = Path(__file__).resolve().parent.parent
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"
CAP = server.RULES_SAFE_BYTES
CODE = "export const PriceCard = {\n  padding: 'A',\n  color: '#ff0000'\n}\n"

DETECT_FLAGS = {
    "local_project": {"has_symbols_json": True, "has_symbols_dir": True},
    "cdn": {"has_cdn_import": True},
    "json_runtime": {"has_json_data": True},
    "remote_server": {"has_mermaid_config": True},
    "unknown": {},
}
FRAMES = [
    ("generate_component", {"description": "A pricing card with a title and a button", "component_name": "PriceCard"}),
    ("generate_page", {"description": "A pricing page", "page_name": "pricing"}),
    ("convert_react", {"source_code": "export const A = () => <div className='x'>Hi</div>"}),
    ("convert_html", {"source_code": "<div class='x'><p>Hi</p></div>"}),
    *(("detect_environment", flags) for flags in DETECT_FLAGS.values()),
    ("audit_component", {"component_code": CODE, "file_path": "components/PriceCard.js", "include_playbook": True}),
]

CALL = re.compile(r"`([a-z_]+)\(([^`]*)\)`")
NEXT = re.compile(r"<!-- continues: ([a-z_]+)\(([^)]*)\) \(part \d+ of \d+\) -->")
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _bytes(text):
    return len(text.encode("utf-8"))


def _key(tool, args):
    return f"{tool}({json.dumps(args, sort_keys=True)})"


def _literal_args(argtext):
    """The keyword arguments of a call, or None when one is not a literal."""
    try:
        call = ast.parse(f"f({argtext})", mode="eval").body
        if call.args:
            return None
        return {k.arg: ast.literal_eval(k.value) for k in call.keywords}
    except (SyntaxError, ValueError):
        return None


async def _walk(run, tools, known, frames=FRAMES):
    """Run the frames, every call they name, and each next part.

    `run(calls)` -> [(error, text)]; `tools` are this server's tools, `known`
    the tools of both servers. Returns (problems, ran, templates, per_frame):
    `ran` maps each call run to its answer bytes."""
    problems, ran, templates, per_frame = [], {}, set(), {}

    def fits(where, err, text):
        if err:
            problems.append(f"{where} failed: {text[:300]}")
            return False
        if _bytes(text) > CAP:
            problems.append(f"{where} is {_bytes(text):,} bytes")
        return True

    def calls_in(found, where):
        calls = []
        for tool, argtext in found:
            if tool not in known:
                if "_" in tool:
                    problems.append(f"{where} names {tool}({argtext}): no such tool")
                continue  # code in the frame, not a tool call
            if tool not in tools:
                problems.append(f"{where} names {tool}({argtext}): no such tool in this server")
                continue
            args = _literal_args(argtext)
            if args is None:
                templates.add(f"{tool}({argtext})")
                continue
            calls.append((tool, args))
        return calls

    pending = []
    for (tool, args), (err, text) in zip(frames, await run(frames)):
        where = f"frame {_key(tool, args)}"
        if fits(where, err, text):
            calls = calls_in(CALL.findall(text) + NEXT.findall(text), where)
            per_frame[where] = len(calls)
            pending += calls
    while pending:
        batch = []
        for call in pending:
            if _key(*call) not in ran and call not in batch:
                batch.append(call)
        if not batch:
            break
        pending = []
        for (tool, args), (err, text) in zip(batch, await run(batch)):
            where = _key(tool, args)
            ran[where] = _bytes(text)
            if fits(where, err, text):
                pending += calls_in(NEXT.findall(text), where)
    return problems, ran, templates, per_frame


def _every_part_of_every_named_skill():
    """The calls for both core parts and every part of each skill a frame names."""
    skills = set(server.GENERATE_COMPONENT_SKILLS + server.GENERATE_PAGE_SKILLS
                 + server.CONVERT_REACT_SKILLS + server.CONVERT_HTML_SKILLS + ("AUDIT.md",))
    skills |= {f for files in server.DETECT_ENVIRONMENT_SKILLS.values() for f in files}
    keys = {_key("get_project_rules", {}), _key("get_project_rules", {"part": 2})}
    for fname in skills:
        if not (server.SKILLS_PATH / fname).exists():
            continue
        name, n = fname[:-3], len(server._split_markdown_parts(server._read_skill(fname)))
        keys |= ({_key("get_project_rules", {"section": name})} if n == 1 else
                 {_key("get_project_rules", {"section": name, "part": i}) for i in range(1, n + 1)})
    return keys


def _check(result):
    problems, ran, _, per_frame = result
    assert not problems, "\n".join(problems)
    assert len(per_frame) == len(FRAMES) and all(per_frame.values()), per_frame
    missing = _every_part_of_every_named_skill() - set(ran)
    assert not missing, sorted(missing)


def test_the_walk_reports_each_bad_call():
    """Planted calls: one of each kind the walk must catch, and two it must not run."""
    frame = (
        "1. `get_project_rules(section='GOOD')` 2. `get_project_rules(section='NOPE')` "
        "3. `get_project_rules(full=True)` 4. `audit_project()` 5. `get_project_rule(section='GOOD')` "
        "6. `el.router(path, el.getRoot())` 7. `audit_component(code, file_path)`"
    )
    answers = {
        _key("get_project_rules", {"section": "GOOD"}):
            (False, "<!-- continues: get_project_rules(section='GOOD', part=2) (part 2 of 2) -->"),
        _key("get_project_rules", {"section": "GOOD", "part": 2}): (True, "part 2 is out of range"),
        _key("get_project_rules", {"section": "NOPE"}): (True, "Unknown section 'NOPE'"),
        _key("get_project_rules", {"full": True}): (False, "x" * (CAP + 1)),
    }

    async def run(calls):
        return [(False, frame) if tool == "frame" else answers[_key(tool, args)] for tool, args in calls]

    tools = {"frame", "get_project_rules", "audit_component"}
    problems, ran, templates, _ = asyncio.run(
        _walk(run, tools, tools | {"audit_project"}, frames=[("frame", {})]))
    report = "\n".join(problems)
    assert len(problems) == 5, report
    assert 'get_project_rules({"part": 2, "section": "GOOD"}) failed' in report  # a next part that fails
    assert 'get_project_rules({"section": "NOPE"}) failed' in report  # a named call that fails
    assert f'get_project_rules({{"full": true}}) is {CAP + 1:,} bytes' in report  # too big
    assert "names audit_project(): no such tool in this server" in report  # a tool of the other server
    assert "names get_project_rule(section='GOOD'): no such tool" in report  # a typo
    assert templates == {"audit_component(code, file_path)"}  # not run as written
    assert len(ran) == 4


# ---------------------------------------------------------------- the Python server

def _python_tools():
    return {t.name for t in asyncio.run(server.mcp.list_tools())}


async def _python_walk(known):
    async with create_connected_server_and_client_session(server.mcp) as client:
        tools = {t.name for t in (await client.list_tools()).tools}

        async def run(calls):
            out = []
            for tool, args in calls:
                result = await client.call_tool(tool, args)
                one = len(result.content) == 1 and isinstance(result.content[0], TextContent)
                text = result.content[0].text if one else repr(result.content)
                out.append((bool(result.isError) or not one, text))
            return out

        return await _walk(run, tools, known | tools)


@pytest.fixture
def offline(monkeypatch):
    """audit_component without the frank-audit subprocess or the network."""
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    monkeypatch.setattr(server, "_run_frank_audit",
                        lambda *a, **k: {"schema": "frank-audit/1.0", "ok": True, "findings": []})
    monkeypatch.setattr(server, "_structural_checks", lambda code: [])


def test_the_frames_cover_every_environment():
    detected = {re.search(r"\*\*Detected: (\w+)\*\*", server.detect_environment(**f)).group(1): env
                for env, f in DETECT_FLAGS.items()}
    assert all(k == v for k, v in detected.items())
    assert set(detected) == set(server.DETECT_ENVIRONMENT_SKILLS)


def test_every_call_a_python_frame_names_runs_within_the_cap(offline):
    known = _python_tools() | (_node_tools() if shutil.which("node") else set())
    result = asyncio.run(_python_walk(known))
    _check(result)
    assert _key("audit_project", {}) in result[1]  # named by the audit report


# ---------------------------------------------------------------- the Node server

def _node_rpc(lines):
    init = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}
    proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join([json.dumps(init), *lines]) + "\n",
                          capture_output=True, text=True, timeout=60)
    replies = {}
    for line in proc.stdout.splitlines():
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg
    return replies


def _node_tools():
    reply = _node_rpc([json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})])[1]
    return {t["name"] for t in reply["result"]["tools"]}


async def _node_run(calls):
    replies = _node_rpc([json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                                     "params": {"name": tool, "arguments": args}})
                         for i, (tool, args) in enumerate(calls, start=1)])
    out = []
    for i in range(1, len(calls) + 1):
        msg = replies.get(i, {"error": "no reply"})
        if "error" in msg:
            out.append((True, json.dumps(msg["error"])))
            continue
        content = msg["result"].get("content", [])
        one = len(content) == 1 and content[0].get("type") == "text"
        out.append((bool(msg["result"].get("isError")) or not one,
                    content[0]["text"] if one else json.dumps(msg["result"])))
    return out


@needs_node
def test_every_call_a_node_frame_names_runs_within_the_cap():
    tools = _node_tools()
    _check(asyncio.run(_walk(_node_run, tools, _python_tools() | tools)))
