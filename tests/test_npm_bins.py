"""`npx @symbo.ls/mcp <subcommand>` needs a bin named after the package.

npx runs the bin whose name is the package name without its scope (`mcp`);
a package whose bins are all named otherwise fails with "could not
determine executable to run" — so `npx -y @symbo.ls/mcp symbols-audit
./symbols` and `npx -y @symbo.ls/mcp init-rules`, as documented, failed.
The `mcp` bin is the server entry, which dispatches the subcommands; the
named bins stay for `npx -p @symbo.ls/mcp <bin>` and global installs.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PKG = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))


def test_a_bin_is_named_after_the_unscoped_package():
    unscoped = PKG["name"].split("/")[-1]
    assert unscoped == "mcp"
    assert PKG["bin"].get("mcp") == "./bin/symbols-mcp.cjs"


def test_the_named_bins_stay():
    for name in ("symbols-mcp", "symbols-audit", "symbols-mcp-init-rules"):
        assert name in PKG["bin"], name


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_the_entry_dispatches_symbols_audit():
    # The dispatcher must run bin/symbols-audit.cjs (which answers about the
    # path) instead of starting the stdio server (which would wait on stdin).
    r = subprocess.run(
        ["node", str(ROOT / "bin" / "symbols-mcp.cjs"), "symbols-audit", "/nonexistent/symbols"],
        capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
    )
    assert "Project path does not exist" in r.stdout + r.stderr, (r.stdout + r.stderr)[:500]


DOCS = ["README.md", "SETUP.md", "symbols_mcp/skills/AUDIT.md",
        "templates/agent-rules/CLAUDE.md", "templates/agent-rules/AGENTS.md",
        "templates/agent-rules/.clinerules", "templates/agent-rules/.windsurfrules",
        "templates/agent-rules/.cursor/rules/symbols.md"]


@pytest.mark.parametrize("doc", DOCS)
def test_docs_show_the_npx_p_form_of_symbols_audit(doc):
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert "symbols-audit" in text
    assert "npx -y -p @symbo.ls/mcp symbols-audit" in text, doc
