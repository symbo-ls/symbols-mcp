"""get_cli_reference — the CLI reference in parts.

CLI.md is larger than one tool result can carry. The tool sent the whole file
(107 193 chars on 2026-11-08) in one answer: above RULES_SAFE_CHARS and above Claude Code's
MAX_MCP_OUTPUT_TOKENS cap (25 000 tokens ≈ 100k chars), so Claude Code
replaced it with a file path and the reference never reached the model. The
tool now serves the parts _split_markdown_parts makes, the same parts as
get_project_rules(section='CLI'), and each part but the last names the next
call in the tool the caller used.
"""

import asyncio
import importlib

import pytest

server = importlib.import_module("symbols_mcp.server")

CLI_TEXT = server._read_skill("CLI.md")
PARTS = server._split_markdown_parts(CLI_TEXT)
CAP = server.RULES_SAFE_CHARS + 200  # the body + the head and continuation lines


def _body(out):
    """The CLI.md text of one served part: the head line and the continuation line dropped."""
    head, _, rest = out.partition(" -->\n")
    assert head.startswith("<!-- section CLI"), head
    body, sep, _ = rest.rpartition("\n\n<!-- continues: ")
    return body if sep else rest


def test_cli_md_is_above_the_cap_so_it_comes_in_parts():
    # Without a second part the continuation tests below check nothing.
    assert len(CLI_TEXT) > server.RULES_SAFE_CHARS
    assert len(PARTS) >= 2


@pytest.mark.parametrize("i", range(1, len(PARTS) + 1))
def test_every_part_is_under_the_cap(i):
    out = server.get_cli_reference(part=i)
    assert len(out) <= CAP, (i, len(out))


def test_the_parts_rejoin_to_cli_md():
    bodies = [_body(server.get_cli_reference(part=i)) for i in range(1, len(PARTS) + 1)]
    assert "\n".join(bodies) == CLI_TEXT


def test_the_no_argument_call_is_part_1():
    assert server.get_cli_reference() == server.get_cli_reference(part=1)


def test_every_part_but_the_last_names_the_next_part():
    n = len(PARTS)
    for i in range(1, n):
        out = server.get_cli_reference(part=i)
        assert out.endswith(f"\n\n<!-- continues: get_cli_reference(part={i + 1}) (of {n}) -->\n"), i
    assert "<!-- continues:" not in server.get_cli_reference(part=n)


@pytest.mark.parametrize("bad", [0, len(PARTS) + 1])
def test_a_part_out_of_range_is_a_clear_error(bad):
    with pytest.raises(ValueError, match=rf"part={bad} is out of range\. Use part=1\.\.{len(PARTS)}\."):
        server.get_cli_reference(part=bad)


@pytest.mark.parametrize("i", range(1, len(PARTS) + 1))
def test_get_project_rules_cli_serves_the_same_parts(i):
    # get_project_rules(section='CLI', part=N) keeps working as it was; the two
    # tools differ only in the call their continuation line names.
    ours = server.get_cli_reference(part=i)
    theirs = server.get_project_rules(section="CLI", part=i)
    assert ours.replace("get_cli_reference(part=", "get_project_rules(section='CLI', part=") == theirs


def test_tool_schema_has_an_optional_part():
    tools = asyncio.run(server.mcp.list_tools())
    tool = next(t for t in tools if t.name == "get_cli_reference")
    props = tool.inputSchema.get("properties", {})
    assert set(props) == {"part"}
    assert props["part"].get("default") == 1
    assert not tool.inputSchema.get("required")  # the zero-argument call stays valid
    assert "in parts" in tool.description
    # The description names the token variable the CLI reads (see
    # test_cli_doc_env_var.py): SYMBOLS_TOKEN, never SYMBOLS_AUTH_TOKEN.
    assert "SYMBOLS_AUTH_TOKEN" not in tool.description
