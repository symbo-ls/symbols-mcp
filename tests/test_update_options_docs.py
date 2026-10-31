"""The update-option tables in SYNTAX.md list what smbls v4 reads, and nothing else.

`s.update` / `s.replace` / `s.set` and `el.update` take an options object.
The v3 runtime read many keys there (`onlyUpdate`, `preventUpdate`, ...);
the v4 runtime (the signal store) reads three. A table that still lists the
v3 keys sends an agent to write `{ preventUpdate: true }` and expect the
owner's `onUpdate` to stay quiet, which it does not. This test keeps the two
tables ("### State Update Options", "### Element Update Options") equal to
the v4 list below, keeps the `s.quietUpdate` row in step with `quiet`, and
fails when a code example in any skill passes a v3 key to a write call."""

import importlib
import re
from pathlib import Path

server = importlib.import_module("symbols_mcp.server")

SKILLS_DIR = Path(server.__file__).parent / "skills"

# What smbls v4 reads (smbls source: packages/signal/src/store.js storeUpdate /
# storeReplace, packages/state/src/methods.js set, packages/element/src/update.js).
# Each option has a behaviour test in smbls that fails when its reader is removed:
#   quiet                            -> packages/element/__tests__/stateUpdateOptions.test.js
#   preventBeforeStateUpdateListener -> packages/element/__tests__/stateUpdateOptions.test.js
#                                       (update() also in packages/element/__tests__/stateLifecycleHooks.test.js)
#   preventListeners                 -> packages/element/__tests__/elementUpdateOptions.test.js
#                                       (with the opts object as the hooks' 4th argument)
# The "keep a state write from running onUpdate" list under the State table is pinned by
# stateUpdateOptions.test.js (quiet), onUpdateContract.test.js (a write runs only its
# owner's onUpdate) and onStateUpdate.test.js (stateDeps), all in packages/element/__tests__/.
# Change a set below only together with those tests.
V4_STATE_OPTIONS = {"quiet", "preventBeforeStateUpdateListener"}
V4_ELEMENT_OPTIONS = {"preventListeners"}

# v3 options with no reader in smbls packages/ or plugins/ source. The same two
# smbls test files pin that a write passing one still runs `onUpdate`.
DEAD_OPTIONS = {
    "onlyUpdate",
    "preventUpdate",
    "preventStateUpdate",
    "preventUpdateListener",
    "preventUpdateAfter",
    "lazyLoad",
    "isForced",
    "preventContentUpdate",
    "preventRecursive",
    "preventDefineUpdate",
}

WRITE_CALL = re.compile(
    r"\.\$?(update|replace|set|setProps|quietUpdate|quietReplace|rootUpdate|parentUpdate)\("
)


def _syntax() -> str:
    return server._read_skill("SYNTAX.md")


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
            if line.strip() == marker:
                start = i
            continue
        depth = len(line) - len(line.lstrip("#"))
        if 0 < depth <= level and line[depth:depth + 1] == " ":
            end = i
            break
    assert start is not None, f"heading not found: {marker!r}"
    return "\n".join(lines[start:end])


def _table_rows(block: str) -> list:
    """First-column cells of every Markdown table row in a block, without
    backticks; the header row and the separator row are left out."""
    rows = []
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set(cells[0]) <= set("-: "):
            continue  # separator
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if nxt.startswith("|") and set(nxt.replace("|", "").strip()) <= set("-: "):
            continue  # header (the row above the separator)
        rows.append(cells[0].strip("`"))
    return rows


def _option_rows(heading: str) -> list:
    rows = _table_rows(_block(_syntax(), heading, 3))
    assert rows, f"no table rows under ### {heading}"
    return rows


def test_state_update_options_table_lists_what_v4_reads():
    rows = _option_rows("State Update Options")
    assert len(rows) == len(set(rows)), rows
    assert set(rows) == V4_STATE_OPTIONS, (
        f"not read by v4: {sorted(set(rows) - V4_STATE_OPTIONS)}; "
        f"read by v4 but no row: {sorted(V4_STATE_OPTIONS - set(rows))}"
    )


def test_element_update_options_table_lists_what_v4_reads():
    rows = _option_rows("Element Update Options")
    assert len(rows) == len(set(rows)), rows
    assert set(rows) == V4_ELEMENT_OPTIONS, (
        f"not read by v4: {sorted(set(rows) - V4_ELEMENT_OPTIONS)}; "
        f"read by v4 but no row: {sorted(V4_ELEMENT_OPTIONS - set(rows))}"
    )


def test_no_v3_option_is_a_table_row():
    for heading in ("State Update Options", "Element Update Options"):
        dead = sorted(DEAD_OPTIONS & set(_option_rows(heading)))
        assert not dead, f"### {heading} lists v3 options v4 does not read: {dead}"


def test_each_table_section_says_the_v3_options_have_no_effect():
    for heading in ("State Update Options", "Element Update Options"):
        block = _block(_syntax(), heading, 3)
        assert "no effect" in block, heading


def test_quiet_update_row_matches_the_quiet_option():
    methods = _block(_syntax(), "State Methods — Full Reference", 2)
    row = next(
        (line for line in methods.splitlines() if line.startswith("| `s.quietUpdate(")),
        None,
    )
    assert row, "no s.quietUpdate row in ## State Methods — Full Reference"
    assert "quiet: true" in row, row
    assert "onUpdate" in row, row
    assert "without triggering listeners" not in row, row


def _fences(text: str):
    """The body of every fenced code block in a Markdown text."""
    body = None
    for line in text.splitlines():
        if line.startswith("```"):
            if body is None:
                body = []
            else:
                yield "\n".join(body)
                body = None
            continue
        if body is not None:
            body.append(line)


def _write_call_options(code: str):
    """(call, text after the first top-level comma) for each write call in code."""
    for m in WRITE_CALL.finditer(code):
        depth, comma, j = 1, None, m.end()
        while j < len(code) and depth:
            c = code[j]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == "," and depth == 1 and comma is None:
                comma = j
            j += 1
        if comma is not None:
            yield m.group(0), code[comma + 1:j - 1]


def test_no_skill_example_passes_a_v3_option_to_a_write_call():
    found = []
    for path in sorted(SKILLS_DIR.glob("*.md")):
        for code in _fences(path.read_text(encoding="utf-8")):
            for call, options in _write_call_options(code):
                for name in sorted(DEAD_OPTIONS):
                    if re.search(rf"\b{name}\s*:", options):
                        found.append(f"{path.name}: {call} ... {name}")
    assert not found, found


def test_the_v4_and_v3_lists_do_not_overlap():
    assert not (V4_STATE_OPTIONS | V4_ELEMENT_OPTIONS) & DEAD_OPTIONS
