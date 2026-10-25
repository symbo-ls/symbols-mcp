"""search_symbols_docs ranks sections, not files.

The old search returned the first skill file (directory order) in which ANY
query word appeared: "prepareDesignSystem pages false object" came back as
RUNNING_APPS.md and REUSE.md, which never name `prepareDesignSystem`. Each
query below names the section an agent needs; the Python server and the Node
server (`bin/symbols-mcp.cjs`, a port of the same ranking) must both find it.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from symbols_mcp.docs_search import DocsIndex, parse_query, split_sections

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "symbols_mcp" / "skills"
SERVER = ROOT / "bin" / "symbols-mcp.cjs"

# query -> (file, a part of the section heading path) the top result has
TOP = [
    ("prepareDesignSystem pages false object", "CLI.md", "Dev / build / deploy"),
    ("treeShakeIcons", "CLI.md", "size options"),
    ("keepSamePage", "SYNTAX.md", "keepSamePage"),
    ("modulePreload strict", "CLI.md", "Dev / build / deploy"),
    ("childrenAs state", "SYNTAX.md", "childrenAs"),
    ("polyglot addressLang", "SYNTAX.md", "The start language"),
    ("breakpointsFrom vw container", "SYNTAX.md", "Breakpoints that follow a container"),
    ("fetch.early script early.js", "SYNTAX.md", "Early requests"),
    ("fetchRunsOf", "SYNTAX.md", "fetch.seed"),
    ("Icon viewBox wide logo fit", "DESIGN_SYSTEM.md", "icons"),
]
# query -> (file, section part) somewhere in the top 3
IN_TOP_3 = [
    ("fetch.seed isStale", "SYNTAX.md", "fetch.seed"),
    ("onWindowResize", "FRANKABILITY_CATALOG.md", "FA503"),
    ("how to navigate el.router", "RULES.md", "window.location"),
]

INDEX = DocsIndex(SKILLS)


@pytest.mark.parametrize("query,file,section", TOP)
def test_the_top_section(query, file, section):
    top = INDEX.search(query, 3)[0]
    assert (top["file"], section in top["section"]) == (file, True), top["section"]


@pytest.mark.parametrize("query,file,section", IN_TOP_3)
def test_in_the_top_three(query, file, section):
    results = INDEX.search(query, 3)
    assert any(r["file"] == file and section in r["section"] for r in results), [(r["file"], r["section"]) for r in results]


def test_the_failing_query_no_longer_returns_files_that_never_name_the_option():
    for r in INDEX.search("prepareDesignSystem pages false object", 5):
        text = (SKILLS / r["file"]).read_text(encoding="utf-8")
        assert "prepareDesignSystem" in text, r["file"]


def test_results_carry_file_section_line_and_snippet_at_most_two_per_file():
    results = INDEX.search("fetch early adopt", 5)
    assert 1 <= len(results) <= 5
    for r in results:
        assert set(r) >= {"file", "section", "line", "snippet", "score"}
        lines = (SKILLS / r["file"]).read_text(encoding="utf-8").split("\n")
        assert lines[r["line"] - 1].startswith("#") or r["line"] == 1
    files = [r["file"] for r in results]
    assert all(files.count(f) <= 2 for f in files)


def test_parse_query_keeps_identifiers_and_drops_stop_words():
    terms = {t.text: t for t in parse_query("how to use `fetch.early` with p_limit and prepareDesignSystem()")}
    assert set(terms) == {"fetch.early", "p_limit", "preparedesignsystem"}
    assert all(t.identifier for t in terms.values())
    assert terms["fetch.early"].parts == ["fetch", "early"]
    assert [t.text for t in parse_query("vw cqw")] == ["vw", "cqw"]


def test_headings_inside_code_fences_do_not_split():
    md = "# Title\n\ntext\n\n```sh\n# not a heading\n```\n\n## Next\n\nmore\n"
    sections = split_sections("X.md", md)
    assert [s.heading for s in sections] == ["Title", "Title > Next"]
    assert sections[1].line == 9


def test_a_section_missing_the_option_name_ranks_below_one_that_has_it(tmp_path):
    (tmp_path / "A.md").write_text("# A\n\npages false object pages false object pages false object\n", encoding="utf-8")
    (tmp_path / "B.md").write_text("# B\n\n`prepareDesignSystem: { pages: false }` object\n", encoding="utf-8")
    results = DocsIndex(tmp_path).search("prepareDesignSystem pages false object")
    assert results[0]["file"] == "B.md"


def test_an_empty_query_finds_nothing():
    assert INDEX.search("   ") == []
    assert INDEX.search("the and of") == []


def _node_search(queries):
    lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})]
    for i, q in enumerate(queries, start=1):
        lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": "search_symbols_docs", "arguments": {"query": q, "max_results": 3}}}))
    proc = subprocess.run(["node", str(SERVER)], input="\n".join(lines) + "\n", capture_output=True, text=True, timeout=120)
    replies = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            msg = json.loads(line)
            replies[msg.get("id")] = msg
    out = []
    for i in range(1, len(queries) + 1):
        text = replies[i]["result"]["content"][0]["text"]
        out.append(json.loads(text) if text.startswith("[") else [])
    return out


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_the_node_server_ranks_the_same():
    queries = [q for q, _, _ in TOP + IN_TOP_3]
    node = _node_search(queries)
    for q, results in zip(queries, node):
        py = INDEX.search(q, 3)
        assert [(r["file"], r["section"], r["line"]) for r in results] == [(r["file"], r["section"], r["line"]) for r in py], q
        assert [r["snippet"] for r in results] == [r["snippet"] for r in py], q
