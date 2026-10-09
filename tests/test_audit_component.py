"""audit_component audits ONE file where it lives in the project.

The inline validator writes the code into a throwaway project and runs
@symbo.ls/frank-audit over it. It used to write every file to
`components/Inline.js` next to an empty `state.js`, so:

- a `functions/` file was audited as a component: FA903 ("exported as a
  function — components must be plain objects") on every export, and FA009
  (file name vs export name) against the synthetic name `Inline`;
- every call reported FA008 (`components/` has no index.js) and FA010 (no
  context.js) — findings about the throwaway project, not about the code.

Now `file_path` places the code where it lives (folder-dependent rules apply
only where they make sense), the default file is named after the code's
first export, and a finding about any OTHER file of the throwaway project is
dropped: one file cannot answer for the project's index.js or context.js.

The unit tests stub the frank-audit subprocess. The integration tests run
the real CLI and skip when it is not installed.
"""

import asyncio
import importlib
import json
import os
import subprocess
from pathlib import Path

import pytest

server = importlib.import_module("symbols_mcp.server")

FUNCTIONS_FILE = """export const formatPrice = function formatPrice (value, currency) {
  const n = Number(value) || 0
  return n.toFixed(2) + ' ' + (currency || '')
}

export const goToTab = function goToTab (tab) {
  this.state.update({ tab })
}
"""

COMPONENT_FILE = """export const PriceCard = {
  padding: 'A',
  Title: { tag: 'h3', text: '{{ pricing.title | polyglot }}' }
}
"""

COMPONENT_AS_FUNCTION = """export const Card = (label) => ({
  padding: 'A',
  text: label
})
"""

HARNESS_RULES = {"FA008", "FA009", "FA010"}


# ---------------------------------------------------------------------------
# Where the code is placed
# ---------------------------------------------------------------------------

def test_default_path_is_a_component_named_after_the_first_export():
    rel, note = server._inline_audit_path(COMPONENT_FILE, "")
    assert rel == "components/PriceCard.js"
    assert note is None


def test_default_path_without_a_named_export_is_inline():
    rel, _ = server._inline_audit_path("export default { padding: 'A' }", "")
    assert rel == "components/Inline.js"


@pytest.mark.parametrize("given, expected", [
    ("functions/listQuerySet.js", "functions/listQuerySet.js"),
    ("./functions/listQuerySet.js", "functions/listQuerySet.js"),
    ("symbols/functions/listQuerySet.js", "functions/listQuerySet.js"),
    ("functions\\listQuerySet.js", "functions/listQuerySet.js"),
    ("functions/listQuerySet", "functions/listQuerySet.js"),
    ("pages/main.js", "pages/main.js"),
    ("designSystem/color.js", "designSystem/color.js"),
    ("app.js", "app.js"),
    ("state.js", "state.js"),
    ("components/admin/Table.js", "components/admin/Table.js"),
    ("/Users/me/project/symbols/components/SiteCover.js", "components/SiteCover.js"),
])
def test_file_path_is_project_relative(given, expected):
    rel, note = server._inline_audit_path(COMPONENT_FILE, given)
    assert rel == expected
    assert note is None


@pytest.mark.parametrize("folder", ["functions", "functions/", "./functions/"])
def test_a_folder_names_the_kind_and_the_export_names_the_file(folder):
    rel, _ = server._inline_audit_path(FUNCTIONS_FILE, folder)
    assert rel == "functions/formatPrice.js"


def test_absolute_path_reads_the_projects_own_symbols_dir(tmp_path):
    (tmp_path / "symbols.json").write_text(json.dumps({"owner": "o", "key": "k", "dir": "./src"}))
    target = tmp_path / "src" / "functions" / "listQuerySet.js"
    rel, note = server._inline_audit_path(FUNCTIONS_FILE, str(target))
    assert rel == "functions/listQuerySet.js"
    assert note is None


@pytest.mark.parametrize("bad", ["../../etc/passwd.js", "functions/../../x.js", ".."])
def test_a_path_that_leaves_the_project_is_refused(bad):
    rel, note = server._inline_audit_path(COMPONENT_FILE, bad)
    assert rel == "components/PriceCard.js"
    assert note and "file_path" in note


# ---------------------------------------------------------------------------
# What reaches frank-audit, and which findings come back (CLI stubbed)
# ---------------------------------------------------------------------------

def _payload(*findings):
    return {"schema": "frank-audit/1.0", "ok": True, "findings": list(findings)}


def _finding(rule, file, line=1, severity="critical"):
    return {"ruleId": rule, "file": file, "line": line, "severity": severity, "message": f"{rule} on {file}"}


def test_cli_audit_places_the_code_and_keeps_only_its_findings(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    seen = {}

    def fake_run(*args, **kwargs):
        root = Path(args[1])
        seen["files"] = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.js"))
        seen["code"] = (root / "functions" / "listQuerySet.js").read_text(encoding="utf-8")
        return _payload(
            _finding("FA008", "functions/index.js", 0),
            _finding("FA010", "context.js"),
            _finding("FA401", "functions/listQuerySet.js", 4),
            _finding("FA303", os.path.join(str(root), "functions", "listQuerySet.js"), 6, "systemic"),
        )

    monkeypatch.setattr(server, "_run_frank_audit", fake_run)
    result = server._audit_code(FUNCTIONS_FILE, "functions/listQuerySet.js")

    assert "functions/listQuerySet.js" in seen["files"]
    assert "state.js" in seen["files"]
    assert not any(f.startswith("components/") for f in seen["files"])
    assert seen["code"] == FUNCTIONS_FILE
    messages = [v["message"] for v in result["violations"] + result["warnings"]]
    assert any("[FA401]" in m for m in messages)
    assert any("[FA303]" in m for m in messages)  # an absolute path to the audited file is the file
    assert not any("[FA008]" in m or "[FA010]" in m for m in messages)
    assert result["file"] == "functions/listQuerySet.js"


def test_auditing_state_js_writes_no_second_state_file(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    seen = {}

    def fake_run(*args, **kwargs):
        seen["state"] = (Path(args[1]) / "state.js").read_text(encoding="utf-8")
        return _payload()

    monkeypatch.setattr(server, "_run_frank_audit", fake_run)
    server._audit_code("export default { open: false }\n", "state.js")
    assert seen["state"] == "export default { open: false }\n"


def test_http_audit_sends_the_file_and_its_slot(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", "http://frank-audit.test")
    sent = {}

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return _payload(
                _finding("FA010", "functions/listQuerySet.js/context.js"),
                _finding("FA008", "functions/index.js", 0),
                _finding("FA401", "functions/listQuerySet.js", 4),
            )

    def fake_post(url, json=None, timeout=None):
        sent["url"] = url
        sent["body"] = json
        return _Resp()

    monkeypatch.setattr(server.httpx, "post", fake_post)
    result = server._audit_code(FUNCTIONS_FILE, "functions/listQuerySet.js")

    assert sent["url"].endswith("/audit-content")
    assert sent["body"]["file"] == "functions/listQuerySet.js"
    assert sent["body"]["slot"] == "functions"
    messages = [v["message"] for v in result["violations"] + result["warnings"]]
    assert messages == ["[FA401] FA401 on functions/listQuerySet.js"]


@pytest.mark.parametrize("rel, slot", [
    ("components/SiteCover.js", "components"),
    ("components/admin/Table.js", "components"),
    ("functions/x.js", "functions"),
    ("pages/main.js", "pages"),
    ("designSystem/color.js", "designSystem"),
    ("app.js", "app"),
    ("state.js", "state"),
    ("early.js", "orphan"),
    ("lib/helpers.js", "orphan"),
])
def test_slot_follows_frank_discovery(rel, slot):
    assert server._frank_slot(rel) == slot


def test_report_names_the_audited_path(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    monkeypatch.setattr(server, "_run_frank_audit", lambda *a, **k: _payload())
    out = server.audit_component(FUNCTIONS_FILE, file_path="functions/listQuerySet.js")
    assert "Audited as: `functions/listQuerySet.js`" in out
    out = server.audit_component(COMPONENT_FILE)
    assert "Audited as: `components/PriceCard.js`" in out
    assert "file_path" in out  # the default placement says how to name the real file


def test_report_explains_a_refused_path(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    monkeypatch.setattr(server, "_run_frank_audit", lambda *a, **k: _payload())
    out = server.audit_component(COMPONENT_FILE, file_path="../../etc/passwd.js")
    assert "Audited as: `components/PriceCard.js`" in out
    assert "outside the project" in out


def test_tool_schema_adds_an_optional_file_path():
    tools = asyncio.run(server.mcp.list_tools())
    tool = next(t for t in tools if t.name == "audit_component")
    props = tool.inputSchema.get("properties", {})
    assert {"component_code", "include_playbook", "file_path"} <= set(props)
    assert tool.inputSchema.get("required") == ["component_code"]


# ---------------------------------------------------------------------------
# The real frank-audit CLI (skipped when it is not installed)
# ---------------------------------------------------------------------------

def _frank_audit_runs() -> bool:
    try:
        r = subprocess.run([server.FRANK_AUDIT_BIN, "help"], capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


needs_frank_audit = pytest.mark.skipif(not _frank_audit_runs(), reason="frank-audit CLI not installed")


def _rules(result):
    return {m["message"].split("]")[0].lstrip("[") for m in result["violations"] + result["warnings"]}


@needs_frank_audit
def test_real_functions_file_gets_no_component_or_harness_findings(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    result = server._audit_code(FUNCTIONS_FILE, "functions/formatPrice.js")
    assert not result.get("unavailable"), result
    rules = _rules(result)
    assert "FA903" not in rules
    assert not (rules & HARNESS_RULES), rules


@needs_frank_audit
def test_real_default_component_audit_has_no_harness_findings(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    result = server._audit_code(COMPONENT_FILE)
    assert not result.get("unavailable"), result
    assert not (_rules(result) & HARNESS_RULES), _rules(result)


@needs_frank_audit
def test_real_component_rules_still_apply_in_components(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    # A component written as a function is still caught where components live.
    assert "FA903" in _rules(server._audit_code(COMPONENT_AS_FUNCTION, "components/Card.js"))
    # A component file whose export does not match its name is still caught.
    assert "FA009" in _rules(server._audit_code(COMPONENT_FILE, "components/Header.js"))
    # The same function file outside components/ is not.
    assert "FA903" not in _rules(server._audit_code(COMPONENT_AS_FUNCTION, "functions/Card.js"))
