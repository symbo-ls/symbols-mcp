"""@symbo.ls/fetch REST contract in the served skills.

The REST adapter reads a response as JSON, text, a Blob, an ArrayBuffer, a
ReadableStream or the raw Response (`responseType`), sends FormData / Blob /
ArrayBuffer / URLSearchParams / ReadableStream bodies as they are, and merges
per-call `headers` over the configured ones. An agent that never reads this
concludes the plugin cannot stream or upload and reaches for a raw `fetch`
(FA402). The skills every tool serves must name the contract where an agent
looks for it: SYNTAX → Data Fetching, FRAMEWORK → Imperative, and Rule 47 —
which is STRICT, so it ships in the core bundle.

The skills are customer-facing: the new text carries no internal tracking
names."""

import importlib

server = importlib.import_module("symbols_mcp.server")

RESPONSE_TYPES = ["auto", "json", "text", "blob", "arrayBuffer", "stream", "response"]
INTERNAL_TERMS = ["BUG-24", "bigbrother", "f17a887b6", "RELMAN", "fleetd", "board.py", "tickets/t/"]


def _block(text: str, heading: str, level: int) -> str:
    """One skill block: from its `#`*level heading to the next heading of the
    same or a higher level. Lines inside code fences never count as headings."""
    lines = text.splitlines()
    marker = "#" * level + " " + heading
    start = end = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if start is None:
            if line.startswith(marker):
                start = i
            continue
        depth = len(line) - len(line.lstrip("#"))
        if 0 < depth <= level and line[depth:depth + 1] == " ":
            end = i
            break
    assert start is not None, f"heading not found: {marker!r}"
    return "\n".join(lines[start:end])


def _syntax_data_fetching() -> str:
    return _block(server._read_skill("SYNTAX.md"), "Data Fetching", 2)


def _framework_imperative() -> str:
    return _block(server._read_skill("FRAMEWORK.md"), "Imperative", 3)


def _framework_anti_patterns() -> str:
    return _block(server._read_skill("FRAMEWORK.md"), "Anti-patterns", 3)


def _rule_47(text: str) -> str:
    return _block(text, "Rule 47 ", 2)


def test_syntax_data_fetching_documents_response_types_and_bodies():
    block = _syntax_data_fetching()
    assert "responseType" in block
    for value in RESPONSE_TYPES:
        assert f"'{value}'" in block, value
    # the three worked examples: one SSE read, one Blob download, one FormData upload
    assert "responseType: 'stream'" in block and "getReader" in block
    assert "responseType: 'blob'" in block and "createObjectURL" in block
    assert "new FormData()" in block
    # the two gotchas that decide whether a declarative call works
    assert "`as`" in block
    assert "never cached" in block
    # per-call headers merge over the configured ones
    assert "per-call" in block.lower()


def test_framework_imperative_list_names_response_type():
    block = _framework_imperative()
    assert "responseType" in block
    for value in ("blob", "stream"):
        assert f"'{value}'" in block, value
    assert "FormData" in block


def test_framework_anti_pattern_points_stream_binary_multipart_at_the_plugin():
    block = _framework_anti_patterns()
    assert "responseType" in block
    for word in ("streaming", "binary", "multipart"):
        assert word in block.lower(), word


def test_rule_47_sends_streaming_binary_multipart_through_the_plugin():
    rule = _rule_47(server._read_skill("RULES.md"))
    lowered = rule.lower()
    for word in ("streaming", "binary", "multipart"):
        assert word in lowered, word
    assert "responseType" in rule and "FormData" in rule


def test_core_bundle_carries_the_rule_47_contract():
    # Rule 47 is STRICT, so an agent sees it in the first get_project_rules() reply.
    rule = _rule_47(server.get_project_rules())
    assert "responseType" in rule
    assert "multipart" in rule.lower()


def test_new_fetch_text_stays_customer_facing():
    blocks = {
        "SYNTAX Data Fetching": _syntax_data_fetching(),
        "FRAMEWORK Imperative": _framework_imperative(),
        "FRAMEWORK Anti-patterns": _framework_anti_patterns(),
        "RULES Rule 47": _rule_47(server._read_skill("RULES.md")),
    }
    for name, text in blocks.items():
        for term in INTERNAL_TERMS:
            assert term not in text, (name, term)
