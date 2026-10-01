"""The CLI reference names the token env var the CLI really reads.

Moved here from smbls packages/cli/__tests__/authEnvVarNamePin.test.js (the
doc half of FW-SMBLS-CLI-TOKEN-ENV-IGNORED-AND-PUSH-NONIDEMPOTENT-1, defect
2): the doc lives in this repo, and a clean smbls export cannot reach it. The
code half stays in smbls: credentialManager.js#getAuthToken reads
SYMBOLS_TOKEN (or SMBLS_TOKEN), never SYMBOLS_AUTH_TOKEN. An agent that
followed the old doc set a variable the CLI never looks at.
"""
from pathlib import Path

CLI_DOC = Path(__file__).resolve().parent.parent / "symbols_mcp" / "skills" / "CLI.md"


def test_cli_doc_names_symbols_token():
    assert "SYMBOLS_TOKEN" in CLI_DOC.read_text(encoding="utf-8")


def test_cli_doc_never_names_symbols_auth_token():
    assert "SYMBOLS_AUTH_TOKEN" not in CLI_DOC.read_text(encoding="utf-8")
