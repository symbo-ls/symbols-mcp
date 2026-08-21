"""get_project_rules — compact core + on-demand sections.

Guards MCP-RULES-BUNDLE-EXCEEDS-TOOL-LIMIT-1: the legacy one-shot bundle
(~590k chars) exceeded Claude Code's MAX_MCP_OUTPUT_TOKENS cap (25 000
tokens ≈ 100k chars) and was truncated to a file path, so the rules never
reached the model. Every response of the tool must now stay under
RULES_SAFE_CHARS, every section must be fetchable, and the legacy full
bundle must still be available behind `full=True`."""

import asyncio
import importlib

import pytest

server = importlib.import_module("symbols_mcp.server")

EXPECTED_SECTIONS = [
    "FRAMEWORK", "DESIGN_SYSTEM", "RULES", "COMPONENTS", "DEFAULT_COMPONENTS",
    "SYNTAX", "PATTERNS", "SNIPPETS", "SHARED_LIBRARIES", "WORKSPACE",
    "FRANKABILITY", "FRANKABILITY_CATALOG", "FRANK_FIX_WORKFLOW",
    "COMMON_MISTAKES", "LEARNINGS", "DEFAULT_PROJECT",
]


def test_safe_cap_is_below_claude_code_default():
    # Claude Code MAX_MCP_OUTPUT_TOKENS default = 25 000 tokens ≈ 100 000 chars.
    assert server.RULES_SAFE_CHARS <= 80_000


def test_core_bundle_under_cap_and_has_required_parts():
    core = server.get_project_rules()
    assert len(core) <= server.RULES_SAFE_CHARS, len(core)
    assert "BUILT-IN COMPONENTS — REUSE" in core          # reuse directive (skills/REUSE.md)
    assert "CRITICAL: Canonical syntax" in core            # RULES preamble
    assert "RULES — STRICT RULES IN FULL" in core
    assert "## Rule 27 — STRICT" in core                   # a STRICT rule body
    assert "FRANKABILITY — HARD CHECKLIST" in core
    assert "SECTION INDEX" in core
    assert "NEXT STEP" in core
    assert "get_project_rules(section='SYNTAX')" in core


def test_index_lists_all_16_sections():
    core = server.get_project_rules()
    names = [n for n, _, _ in server.RULES_SECTIONS]
    assert names == EXPECTED_SECTIONS
    for name in EXPECTED_SECTIONS:
        assert f"| {name} |" in core, name


@pytest.mark.parametrize("name", EXPECTED_SECTIONS)
def test_every_section_fetchable_under_cap(name):
    parts = server._rules_section_parts(name)
    joined = []
    for i in range(1, len(parts) + 1):
        out = server.get_project_rules(section=name, part=i)
        assert len(out) <= server.RULES_SAFE_CHARS + 200, (name, i, len(out))
        assert f"<!-- section {name}" in out
        joined.append(parts[i - 1])
    fname = server._RULES_SECTION_BY_NAME[name][0]
    # parts re-assemble to the original skill text (split only at '## ' lines)
    assert "\n".join(joined) == server._read_skill(fname)


def test_section_name_is_case_insensitive_and_md_optional():
    a = server.get_project_rules(section="syntax")
    b = server.get_project_rules(section="SYNTAX.md")
    assert a == b


def test_multi_part_section_continuation_hint():
    parts = server._rules_section_parts("RULES")
    assert len(parts) >= 2  # RULES.md is above the cap and is served in parts
    first = server.get_project_rules(section="RULES", part=1)
    assert "part=2" in first
    last = server.get_project_rules(section="RULES", part=len(parts))
    assert "continues" not in last


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


def test_multi_section_request_refuses_over_cap():
    small = server.get_project_rules(section="COMPONENTS, SNIPPETS")
    assert "<!-- section COMPONENTS" in small and "<!-- section SNIPPETS" in small
    with pytest.raises(ValueError, match="safe cap|more than one part"):
        server.get_project_rules(section="FRAMEWORK,DESIGN_SYSTEM,RULES")


def test_other_skills_fetchable_by_name():
    out = server.get_project_rules(section="CLI")
    assert "<!-- section CLI" in out


def test_legacy_full_bundle_still_works():
    full = server.get_project_rules(full=True)
    assert len(full) > 400_000
    for name, fname, _ in server.RULES_SECTIONS:
        assert server._read_skill(fname) in full, name


def test_tool_schema_is_backward_compatible():
    tools = asyncio.run(server.mcp.list_tools())
    tool = next(t for t in tools if t.name == "get_project_rules")
    props = tool.inputSchema.get("properties", {})
    assert set(props) == {"section", "part", "full"}
    assert not tool.inputSchema.get("required")  # zero-arg call still valid


def test_project_context_next_step_points_to_compact_rules(tmp_path):
    (tmp_path / "symbols.json").write_text('{"owner":"o","key":"k"}')
    import json
    res = json.loads(server.get_project_context(str(tmp_path)))
    assert "get_project_rules()" in res["next_step"]
    assert "section='SYNTAX'" in res["next_step"]
