"""The splitter behind every answer served in parts.

The old splitter cut only at `## ` lines and counted chars. A `## ` block
above the cap was served whole (CLI.md's command map: 79,546 chars), a `## `
line inside a fenced code block was a cut point, and the head counted chars
while the client limit falls on the received string. Now: parts of at most
RULES_PART_BUDGET UTF-8 bytes, cut before `## `, then `### `, then `#### `
lines, never before a heading line inside a fence, never inside a table;
greedy, in order, never truncated; the parts re-join with "\\n" to the source.
"""

import importlib
import re

import pytest

server = importlib.import_module("symbols_mcp.server")

SKILLS = sorted(p.stem for p in server.SKILLS_PATH.glob("*.md"))
BUDGET = server.RULES_PART_BUDGET


def _bytes(text):
    return len(text.encode("utf-8"))


def _fence_open_lines(lines):
    """For each line index, whether a fenced code block is open just before it
    (an independent reading of CommonMark fences: 3+ backticks or tildes; the
    same char, at least as long, closes it)."""
    state = []
    fence = None
    for line in lines:
        state.append(fence is not None)
        if fence is None:
            m = re.match(r"\s*(`{3,}|~{3,})(.*)$", line)
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = m.group(1)
        else:
            s = line.strip()
            if s and set(s) == {fence[0]} and len(s) >= len(fence):
                fence = None
    return state


def _cut_lines(parts):
    """The line index (in the source) where each part after the first starts."""
    cuts, at = [], 0
    for p in parts[:-1]:
        at += p.count("\n") + 1
        cuts.append(at)
    return cuts


def _is_table_row(line):
    return line.lstrip().startswith("|")


@pytest.mark.parametrize("name", SKILLS)
def test_parts_rejoin_fit_the_budget_and_never_cut_inside_a_fence_or_a_table(name):
    text = server._read_skill(f"{name}.md")
    parts = server._split_markdown_parts(text)
    assert "\n".join(parts) == text
    for i, p in enumerate(parts, 1):
        assert _bytes(p) <= BUDGET, (name, i, _bytes(p))
    lines = text.split("\n")
    in_fence = _fence_open_lines(lines)
    for cut in _cut_lines(parts):
        line = lines[cut]
        assert re.match(r"#{2,4} ", line), (name, cut, line)
        assert not in_fence[cut], (name, cut, line)
        assert not (_is_table_row(lines[cut - 1]) and _is_table_row(line)), (name, cut)


@pytest.mark.parametrize("name", SKILLS)
def test_packing_is_greedy(name):
    # A part ends only where the next block would not fit: the part plus the
    # next part's first block is above the budget.
    text = server._read_skill(f"{name}.md")
    parts = server._split_markdown_parts(text)
    if len(parts) == 1:
        return
    blocks = server._markdown_blocks(text.split("\n"), 2, BUDGET)
    j = 0
    for part in parts[:-1]:
        acc = []
        while "\n".join(acc) != part:
            assert j < len(blocks) and len("\n".join(acc)) < len(part), (name, j)
            acc.append(blocks[j])
            j += 1
        assert _bytes(part) + 1 + _bytes(blocks[j]) > BUDGET, (name, j)


def test_cli_md_needs_the_lower_levels():
    # "## Top-level command map" is above the budget, and inside it
    # "### Dev / build / deploy" is too: the splitter cuts at `####` there.
    text = server._read_skill("CLI.md")
    parts = server._split_markdown_parts(text)
    starts = [p.split("\n", 1)[0] for p in parts[1:]]
    assert any(s.startswith(("### ", "#### ")) for s in starts), starts


def _doc(*blocks):
    return "\n".join(blocks)


def test_a_block_above_the_limit_is_cut_at_the_next_level():
    h2 = _doc("## Big", "intro", "### One", "a" * 60, "### Two", "b" * 60, "#### Deep", "c" * 60)
    text = _doc("# Title", "## Small", "x", h2)
    parts = server._split_markdown_parts(text, limit=100)
    assert "\n".join(parts) == text
    assert all(_bytes(p) <= 100 for p in parts), [_bytes(p) for p in parts]
    # "## Big" (221 bytes) is cut at `### `; its "### Two" block (139 bytes) at `#### `.
    assert [p.split("\n", 1)[0] for p in parts] == ["# Title", "### Two", "#### Deep"]


def test_a_heading_inside_a_fence_is_no_cut_point():
    fenced = _doc("```md", "## Not a heading", "y" * 80, "## Also not", "```")
    text = _doc("## A", "a" * 50, fenced, "## B", "b" * 50)
    parts = server._split_markdown_parts(text, limit=120)
    assert "\n".join(parts) == text
    for p in parts:
        assert not p.startswith("## Not") and not p.startswith("## Also")
    # a longer fence closes only on a run at least as long
    text = _doc("## A", "````", "```", "## inside", "```", "````", "## B", "b" * 60)
    parts = server._split_markdown_parts(text, limit=40)
    assert [p.split("\n", 1)[0] for p in parts] == ["## A", "## B"]


def test_inline_code_is_not_a_fence():
    text = _doc("## A", "```x``` is inline code", "## B", "b" * 60)
    parts = server._split_markdown_parts(text, limit=40)
    assert [p.split("\n", 1)[0] for p in parts] == ["## A", "## B"]


def test_a_block_with_no_cut_point_is_served_whole():
    text = _doc("## A", "a" * 30, "## Huge", "z" * 500)
    parts = server._split_markdown_parts(text, limit=100)
    assert parts == ["## A\n" + "a" * 30, "## Huge\n" + "z" * 500]


def test_the_limit_counts_utf8_bytes():
    # 30 Georgian letters: 30 chars, 90 bytes.
    ka = "ა" * 30
    text = _doc("## A", ka, "## B", ka)
    assert len(text) < 80 < _bytes(text)
    parts = server._split_markdown_parts(text, limit=100)
    assert len(parts) == 2


def test_head_and_continuation_lines():
    parts = ["## A\nalpha", "## B\nბეტა"]
    call = lambda n: f"get_project_rules(section='X', part={n})"  # noqa: E731
    first = server._skill_part_response("X", parts, 1, call)
    assert first == (
        "<!-- section X part 1 of 2 (10 bytes) -->\n## A\nalpha"
        "\n\n<!-- continues: get_project_rules(section='X', part=2) (part 2 of 2) -->\n"
    )
    second = server._skill_part_response("X", parts, 2, call)
    assert second == f"<!-- section X part 2 of 2 ({_bytes(parts[1])} bytes) -->\n## B\nბეტა"
    one = server._skill_part_response("Y", ["x" * 1234], 1, call)
    assert one.startswith("<!-- section Y (1,234 bytes) -->\n")
    for bad in (0, 3):
        with pytest.raises(ValueError, match=rf"part={bad} is out of range\. Use part=1\.\.2\."):
            server._skill_part_response("X", parts, bad, call)
