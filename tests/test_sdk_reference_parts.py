"""get_sdk_reference — the SDK reference in parts, like get_cli_reference.

SDK.md (48,900 bytes) went out whole: live in Claude Code 2.1.319 the
48,697-char answer came back as "Output too large (48.9KB). Full output saved
to …" with a 2,000-char preview, so the reference never reached the model.
The tool now takes `part` and serves the parts _split_markdown_parts makes —
at most RULES_SAFE_BYTES (45,000 UTF-8 bytes) per answer, head and
continuation lines included — the same parts as
get_project_rules(section='SDK'); each part but the last names the next call.
"""

import asyncio
import importlib

import pytest

server = importlib.import_module("symbols_mcp.server")

SDK_TEXT = server._read_skill("SDK.md")
PARTS = server._split_markdown_parts(SDK_TEXT)
CAP = server.RULES_SAFE_BYTES


def _bytes(text):
    return len(text.encode("utf-8"))


def _body(out):
    head, _, rest = out.partition(" -->\n")
    assert head.startswith("<!-- section SDK"), head
    body, sep, _ = rest.rpartition("\n\n<!-- continues: ")
    return body if sep else rest


def test_sdk_md_is_above_the_cap_so_it_comes_in_parts():
    assert _bytes(SDK_TEXT) > CAP
    assert len(PARTS) >= 2


@pytest.mark.parametrize("i", range(1, len(PARTS) + 1))
def test_every_part_is_under_the_cap(i):
    out = server.get_sdk_reference(part=i)
    assert _bytes(out) <= CAP, (i, _bytes(out))


def test_the_parts_rejoin_to_sdk_md():
    bodies = [_body(server.get_sdk_reference(part=i)) for i in range(1, len(PARTS) + 1)]
    assert "\n".join(bodies) == SDK_TEXT


def test_the_no_argument_call_is_part_1():
    assert server.get_sdk_reference() == server.get_sdk_reference(part=1)


def test_every_part_but_the_last_names_the_next_part():
    n = len(PARTS)
    for i in range(1, n):
        assert server.get_sdk_reference(part=i).endswith(
            f"\n\n<!-- continues: get_sdk_reference(part={i + 1}) (part {i + 1} of {n}) -->\n"
        ), i
    assert "<!-- continues:" not in server.get_sdk_reference(part=n)


@pytest.mark.parametrize("bad", [0, len(PARTS) + 1])
def test_a_part_out_of_range_is_a_clear_error(bad):
    with pytest.raises(ValueError, match=rf"part={bad} is out of range\. Use part=1\.\.{len(PARTS)}\."):
        server.get_sdk_reference(part=bad)


@pytest.mark.parametrize("i", range(1, len(PARTS) + 1))
def test_get_project_rules_sdk_serves_the_same_parts(i):
    ours = server.get_sdk_reference(part=i)
    theirs = server.get_project_rules(section="SDK", part=i)
    assert ours.replace("get_sdk_reference(part=", "get_project_rules(section='SDK', part=") == theirs


def test_tool_schema_has_an_optional_part():
    tools = asyncio.run(server.mcp.list_tools())
    tool = next(t for t in tools if t.name == "get_sdk_reference")
    props = tool.inputSchema.get("properties", {})
    assert set(props) == {"part"}
    assert props["part"].get("default") == 1
    assert not tool.inputSchema.get("required")
    assert "in parts" in tool.description and "45,000" in tool.description
