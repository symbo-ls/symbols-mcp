"""get_project_rules() — the core in exactly 2 parts, binding first.

The one-answer core was 79,571 bytes (78,066 chars): Claude Code saved it to a
file ("exceeds maximum allowed tokens"), so the STRICT rules never reached the
model. Now get_project_rules() is part 1 and get_project_rules(part=2) is part
2, each at most RULES_SAFE_BYTES (45,000 UTF-8 bytes). Part 1 opens with the
list of every STRICT rule heading, each marked with the part that holds its
full text; then the reuse directive, the frankability checklist, the RULES
preamble and the STRICT rules in RULES.md order, as many as fit. Part 2: the
rest of the STRICT rules, then the reference (all rule headings, the SECTION
INDEX, the NEXT STEP table). Nothing of the old core is dropped.
"""

import importlib
import re

import pytest

server = importlib.import_module("symbols_mcp.server")

CAP = server.RULES_SAFE_BYTES
P1, P2 = server.get_project_rules(), server.get_project_rules(part=2)


def _bytes(text):
    return len(text.encode("utf-8"))


def _rules_md():
    """RULES.md read here, apart from the server: the preamble, the STRICT
    rules as (heading, body) in file order, and every rule heading."""
    text = server._read_skill("RULES.md")
    starts = [m.start() for m in re.finditer(r"^## Rule ", text, flags=re.M)]
    preamble = text[: starts[0]].rstrip()
    rules = []
    for a, b in zip(starts, starts[1:] + [len(text)]):
        body = text[a:b].rstrip()
        rules.append((body.split("\n", 1)[0][3:].strip(), body))
    return preamble, [r for r in rules if "STRICT" in r[0]], [h for h, _ in rules]


PREAMBLE, STRICT, HEADINGS = _rules_md()


def _listing(part1):
    """The STRICT list: the first block after the header's `---`."""
    block = part1.split("\n\n---\n\n")[1]
    assert block.startswith("# STRICT RULES — all "), block[:80]
    return [l for l in block.split("\n") if l.startswith("- (part ")]


def test_there_are_strict_rules_to_check():
    assert len(STRICT) == 14  # RULES.md today; update with the skill


def test_exactly_two_parts_each_under_the_cap():
    assert server._rules_core_parts() == [P1, P2]
    for i, part in enumerate((P1, P2), 1):
        assert _bytes(part) <= CAP, (i, _bytes(part))


@pytest.mark.parametrize("bad", [0, 3, -1])
def test_a_core_part_out_of_range_is_a_clear_error(bad):
    with pytest.raises(ValueError, match=rf"part={bad} is out of range"):
        server.get_project_rules(part=bad)


def test_part_1_opens_with_the_marked_list_of_every_strict_rule():
    header = P1.split("\n\n---\n\n")[0]
    assert header.startswith("# SYMBOLS / DOMQL RULES — CORE, PART 1 OF 2")
    # the header says part 2 carries binding rules and names the call for it
    assert "binding rules" in header and "`get_project_rules(part=2)`" in header
    rows = _listing(P1)
    assert len(rows) == len(STRICT)
    for row, (heading, _) in zip(rows, STRICT):
        assert row in (f"- (part 1) {heading}", f"- (part 2) {heading}"), row


def test_each_strict_rule_is_in_full_once_where_its_marker_says():
    rows = _listing(P1)
    for row, (heading, body) in zip(rows, STRICT):
        in1, in2 = P1.count(body), P2.count(body)
        assert in1 + in2 == 1, (heading, in1, in2)
        assert (in1 == 1) == row.startswith("- (part 1) "), heading
        # and once in the list
        assert sum(r.endswith(f") {heading}") for r in rows) == 1


def test_part_1_order_and_its_strict_rules_are_a_prefix_up_to_the_cap():
    reuse = server._read_skill("REUSE.md")
    frank = server._read_skill("FRANKABILITY.md")
    checklist = frank[frank.index("\n## Quick reference") + 1:].rstrip()
    first_strict = STRICT[0][1]
    at = [P1.index(x) for x in (_listing(P1)[0], reuse, checklist, PREAMBLE, first_strict)]
    assert at == sorted(at), at
    k = sum(1 for _, body in STRICT if body in P1)
    assert all(body in P1 for _, body in STRICT[:k])  # a prefix, in RULES.md order
    if k < len(STRICT):
        # greedy: the next STRICT rule would not have fit in part 1
        assert _bytes(P1) + _bytes(STRICT[k][1]) + 2 > CAP
    assert P1.endswith("\n\n<!-- continues: get_project_rules(part=2) (part 2 of 2) -->\n")


def test_part_2_holds_the_rest_then_the_reference():
    assert P2.startswith("# SYMBOLS / DOMQL RULES — CORE, PART 2 OF 2")
    rest = [body for _, body in STRICT if body in P2]
    assert rest, "part 2 holds no STRICT rule; the part 1 header would be wrong"
    index = P2.index("# RULES — ALL RULE HEADINGS")
    sections = P2.index("# SECTION INDEX")
    next_step = P2.index("# NEXT STEP")
    assert max(P2.index(b) for b in rest) < index < sections < next_step
    assert "<!-- continues:" not in P2


def test_the_reference_is_only_in_part_2():
    for marker in ("# RULES — ALL RULE HEADINGS", "# SECTION INDEX", "# NEXT STEP"):
        assert marker not in P1 and marker in P2, marker
    for name, _, desc in server.RULES_SECTIONS:
        assert f"| {name} |" not in P1
    for task, _ in server.RULES_NEXT_STEP:
        assert f"| {task} |" not in P1


def test_nothing_of_the_old_core_is_dropped():
    both = P1 + P2
    reuse = server._read_skill("REUSE.md")
    frank = server._read_skill("FRANKABILITY.md")
    checklist = frank[frank.index("\n## Quick reference") + 1:].rstrip()
    for block in (reuse, checklist, PREAMBLE):
        assert block in P1
    for _, body in STRICT:
        assert body in both
    for heading in HEADINGS:  # the all-rule heading index
        row = f"- **{heading}**" if "STRICT" in heading else f"- {heading} — full text: `section='RULES'`"
        assert row in P2, heading
    for name, _, desc in server.RULES_SECTIONS:
        assert f"| {name} |" in P2 and desc in P2, name
    for task, secs in server.RULES_NEXT_STEP:
        assert f"| {task} | {secs} |" in P2, task
    stamp = server._runtime_checked_line().strip()
    assert stamp and stamp in P1.split("\n\n---\n\n")[0]  # in the header, before the bundle
