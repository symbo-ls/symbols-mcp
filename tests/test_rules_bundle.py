"""get_project_rules — the core in 2 parts + on-demand sections.

Guards MCP-RULES-BUNDLE-EXCEEDS-TOOL-LIMIT-1 and its follow-up. The legacy
one-shot bundle (~590k chars) was saved to a file by Claude Code, so the rules
never reached the model. The 80,000-char cap that replaced it was still too
high: measured live in Claude Code 2.1.319, an answer over 50,000 (the client
constant `mC=50000`, on the string the client receives) is saved to a file with
a 2,000-char preview, and one over 25,000 tokens gets "exceeds maximum allowed
tokens". The 78,066-char core and the 74,073-char RULES part 1 got that notice.
Every answer of the tool now stays at or under RULES_SAFE_BYTES (45,000 UTF-8
bytes), head and continuation lines included; every section is fetchable; the
legacy full bundle is still there behind `full=True`. The core itself is
tests/test_core_parts.py; the splitter is tests/test_markdown_parts.py."""

import asyncio
import importlib
import json

import pytest

server = importlib.import_module("symbols_mcp.server")

EXPECTED_SECTIONS = [
    "FRAMEWORK", "DESIGN_SYSTEM", "RULES", "COMPONENTS", "DEFAULT_COMPONENTS",
    "SYNTAX", "PATTERNS", "SNIPPETS", "SHARED_LIBRARIES", "WORKSPACE",
    "FRANKABILITY", "FRANKABILITY_CATALOG", "FRANK_FIX_WORKFLOW",
    "COMMON_MISTAKES", "LEARNINGS", "DEFAULT_PROJECT",
]

CAP = server.RULES_SAFE_BYTES


def _bytes(text):
    return len(text.encode("utf-8"))


def test_the_cap_is_45000_bytes_under_both_client_limits():
    # Claude Code saves an answer over 50,000 chars (or 25,000 tokens) to a file.
    assert server.RULES_SAFE_BYTES == 45_000
    # The splitter packs a part's body to the budget; the head and continuation
    # lines get the rest, so the whole answer fits the cap.
    assert server.RULES_PART_BUDGET + server.RULES_PART_FRAME_BYTES == server.RULES_SAFE_BYTES
    assert not hasattr(server, "RULES_SAFE_CHARS")


def test_index_lists_all_16_sections():
    names = [n for n, _, _ in server.RULES_SECTIONS]
    assert names == EXPECTED_SECTIONS
    reference = server.get_project_rules(part=2)  # the SECTION INDEX is in core part 2
    for name in EXPECTED_SECTIONS:
        assert f"| {name} |" in reference, name


def test_index_states_sizes_in_bytes_and_the_real_part_counts():
    reference = server.get_project_rules(part=2)
    assert "| Section | Bytes | Parts |" in reference
    for name, fname, _ in server.RULES_SECTIONS:
        text = server._read_skill(fname)
        parts = len(server._split_markdown_parts(text))
        assert f"| {name} | {_bytes(text):,} | {parts} |" in reference, name


@pytest.mark.parametrize("name", EXPECTED_SECTIONS)
def test_every_section_fetchable_under_cap(name):
    parts = server._rules_section_parts(name)
    for i in range(1, len(parts) + 1):
        out = server.get_project_rules(section=name, part=i)
        assert _bytes(out) <= CAP, (name, i, _bytes(out))
        assert out.startswith(f"<!-- section {name}")
    fname = server._RULES_SECTION_BY_NAME[name][0]
    # the parts re-join to the skill text exactly
    assert "\n".join(parts) == server._read_skill(fname)


def test_section_name_is_case_insensitive_and_md_optional():
    a = server.get_project_rules(section="syntax")
    b = server.get_project_rules(section="SYNTAX.md")
    assert a == b


def test_multi_part_section_continuation_hint():
    parts = server._rules_section_parts("RULES")
    n = len(parts)
    assert n >= 2  # RULES.md is above the cap and is served in parts
    first = server.get_project_rules(section="RULES", part=1)
    assert first.endswith(
        f"\n\n<!-- continues: get_project_rules(section='RULES', part=2) (part 2 of {n}) -->\n"
    )
    last = server.get_project_rules(section="RULES", part=n)
    assert "<!-- continues:" not in last


def test_unknown_section_is_a_clear_error():
    with pytest.raises(ValueError) as exc:
        server.get_project_rules(section="NOPE")
    msg = str(exc.value)
    assert "Unknown section 'NOPE'" in msg
    for name in EXPECTED_SECTIONS:
        assert name in msg


def test_part_out_of_range_is_a_clear_error():
    with pytest.raises(ValueError, match="out of range"):
        server.get_project_rules(section="SYNTAX", part=9)


def test_multi_section_request_fits_the_cap_or_refuses():
    small = server.get_project_rules(section="SNIPPETS, DEFAULT_PROJECT")
    assert "<!-- section SNIPPETS (" in small and "<!-- section DEFAULT_PROJECT (" in small
    assert _bytes(small) <= CAP
    # two one-part sections whose sum is above the cap
    with pytest.raises(ValueError, match="45,000-byte cap"):
        server.get_project_rules(section="COMPONENTS, PATTERNS")
    with pytest.raises(ValueError, match="more than one part"):
        server.get_project_rules(section="FRAMEWORK,DESIGN_SYSTEM,RULES")


def test_other_skills_fetchable_by_name():
    out = server.get_project_rules(section="CLI")
    assert out.startswith("<!-- section CLI part 1 of ")


# The skills outside the 16 bundle sections (CLI, SDK, MODERN_STACK, AUDIT, …)
# are fetchable by name too, so they get the same cap.
OTHER_SKILLS = sorted(
    p.stem for p in server.SKILLS_PATH.glob("*.md") if p.stem not in server._RULES_SECTION_BY_NAME
)


def test_other_skills_are_listed():
    assert {"CLI", "SDK", "MODERN_STACK", "AUDIT"} <= set(OTHER_SKILLS)


@pytest.mark.parametrize("name", OTHER_SKILLS)
def test_every_other_skill_fetchable_under_cap(name):
    parts = server._split_markdown_parts(server._read_skill(f"{name}.md"))
    for i in range(1, len(parts) + 1):
        out = server.get_project_rules(section=name, part=i)
        assert _bytes(out) <= CAP, (name, i, _bytes(out))
        assert out.startswith(f"<!-- section {name}")


# The skills outside the 16 bundle sections (CLI, SDK, MODERN_STACK, AUDIT, …)
# are fetchable by name too, so they get the same cap. The splitter cuts only at
# `## ` lines and never truncates: a single `## ` block above the cap is served
# whole, and must fail here, not in a client.
OTHER_SKILLS = sorted(
    p.stem for p in server.SKILLS_PATH.glob("*.md") if p.stem not in server._RULES_SECTION_BY_NAME
)


def test_other_skills_are_listed():
    assert {"CLI", "SDK", "MODERN_STACK", "AUDIT"} <= set(OTHER_SKILLS)


@pytest.mark.parametrize("name", OTHER_SKILLS)
def test_every_other_skill_fetchable_under_cap(name):
    parts = server._split_markdown_parts(server._read_skill(f"{name}.md"))
    for i in range(1, len(parts) + 1):
        out = server.get_project_rules(section=name, part=i)
        assert len(out) <= server.RULES_SAFE_CHARS + 200, (name, i, len(out))
        assert f"<!-- section {name}" in out


def test_legacy_full_bundle_still_works():
    full = server.get_project_rules(full=True)
    assert len(full) > 400_000
    for name, fname, _ in server.RULES_SECTIONS:
        assert server._read_skill(fname) in full, name
    # the index names its real size
    assert f"({_bytes(full):,} bytes)" in server.get_project_rules(part=2)


def test_tool_schema_is_backward_compatible():
    tools = asyncio.run(server.mcp.list_tools())
    tool = next(t for t in tools if t.name == "get_project_rules")
    props = tool.inputSchema.get("properties", {})
    assert set(props) == {"section", "part", "full"}
    assert not tool.inputSchema.get("required")  # zero-arg call still valid


def test_project_context_next_step_names_both_core_parts(tmp_path):
    (tmp_path / "symbols.json").write_text('{"owner":"o","key":"k"}')
    res = json.loads(server.get_project_context(str(tmp_path)))
    assert "get_project_rules()" in res["next_step"]
    assert "get_project_rules(part=2)" in res["next_step"]
    assert "section='SYNTAX'" in res["next_step"]
    assert "80k" not in res["next_step"]
