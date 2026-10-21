"""The polyglot setup examples never import the plugin.

The runtime registers @symbo.ls/polyglot and its functions from
`context.polyglot` (FRAMEWORK §6). A project that imports the plugin gets it
stubbed under `smbls push`: the payload ships `plugins: [""]` and a phantom
`functions.polyglot`. SYNTAX and RULES still showed the import in their
Setup examples, against §6; an agent copies the example, not the rule. The
project generator also told agents to put framework plugins in
dependencies.js, which is the runtime importmap only (FA209)."""

import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parent.parent / "symbols_mcp" / "skills"
SERVER = Path(__file__).resolve().parent.parent / "symbols_mcp" / "server.py"


def _code_blocks(text):
    return re.findall(r"```js\n(.*?)```", text, re.S)


def test_setup_examples_do_not_import_polyglot():
    for name in ("SYNTAX.md", "RULES.md"):
        for block in _code_blocks((SKILLS / name).read_text()):
            if "context.polyglot" not in block:
                continue
            if "❌" in block:
                continue  # a marked wrong example
            assert "@symbo.ls/polyglot" not in block, f"{name}: a polyglot setup example imports the plugin"
            assert "polyglotPlugin" not in block, f"{name}: a polyglot setup example wires polyglotPlugin"


def test_generator_keeps_framework_plugins_out_of_dependencies():
    text = SERVER.read_text()
    line = next(l for l in text.splitlines() if l.lstrip().startswith("- dependencies.js"))
    assert "polyglotPlugin" not in line and "fetchPlugin" not in line
