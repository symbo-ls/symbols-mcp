"""audit_component checks the SHAPE rules a regex cannot see.

xma.info found audits passing code that broke three STRICT rules:

- Rule 19: one condition repeated across several CSS props of an element
  (up to six props, 11 elements) instead of an `isX` + `'.isX'` block;
- Rule 65: links and cards with `:hover` but no `:active`;
- Rule 68: 17 call sites overriding a built-in Button's padding.

One module, symbols_mcp/checks/structural.cjs, runs in both servers (the
Python one through `node`). Every finding is a warning naming the rule by
its current RULES.md number. Fixtures below follow the report's examples;
the clean ones are the forms the rules ask for. The existing validator
fixtures must stay clean.

A fourth report item — a reactive `fill`/`color`/`background` under a
`:hover` block for the same property — is NOT a check: the runtime emits
that block's declaration with `!important`, so the hover wins (pinned by
tests/runtime_examples/run.mjs, case reactiveBaseBlocksWin).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from symbols_mcp import server

ROOT = Path(__file__).resolve().parent.parent
NODE_SERVER = ROOT / "bin" / "symbols-mcp.cjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

REPEATED_CONDITION = """export const Tab = {
  extends: 'Link',
  padding: 'A B',
  color: (el, s) => s.root.tab === el.key ? 'title' : 'caption',
  fontWeight: (el, s) => (s.root.tab === el.key) ? '600' : '400',
  borderColor: (e, st) => st.root.tab === e.key ? 'primary' : 'transparent',
  opacity: (el, s) => { return s.root.tab === el.key ? 1 : 0.6 },
  ':hover': { color: 'title' },
  ':active': { color: 'title' }
}
"""

ISX_FORM = """export const Tab = {
  extends: 'Link',
  color: 'caption',
  isActive: (el, s) => s.root.tab === el.key,
  '.isActive': { color: 'title', fontWeight: '600', borderColor: 'primary' },
  ':hover': { color: 'title' },
  ':active': { color: 'title' },
  text: (el, s) => s.root.tab === el.key ? 'On' : 'Off',
  hide: (el, s) => s.root.tab === el.key ? false : true
}
"""

TWO_PROPS_SHARE = """export const Chip = {
  color: (el, s) => s.on ? 'title' : 'caption',
  background: (el, s) => s.on ? 'gray1' : 'transparent',
  opacity: (el, s) => s.busy ? 0.5 : 1
}
"""

HOVER_NO_ACTIVE = """export const FooterLink = {
  extends: 'Link',
  color: 'caption',
  ':hover': { color: 'title' }
}

export const ProductCard = {
  onClick: (e, el) => el.call('openProduct', el.key),
  ':hover': { background: 'gray1' }
}

export const List = {
  More: { extends: 'Button', text: 'More', ':hover': { background: 'gray1' } }
}
"""

HOVER_AND_ACTIVE = """export const FooterLink = {
  extends: 'Link',
  ':hover': { color: 'title' },
  ':active': { color: 'caption' }
}

export const Panel = { ':hover': { background: 'gray1' } }

export const Row = {
  Cta: { extends: 'PillLink', href: '/x', ':hover': { background: 'gray1' } },
  ShopLink: { href: '/shop', ':hover': { color: 'title' } }
}
"""

BUTTON_PADDING = """export const Toolbar = {
  Button: { text: 'Save', padding: 'Z A' },
  Close: { extends: 'IconButton', icon: 'x', height: 'B' },
  Button_more: { text: 'More', minHeight: 'C', paddingInline: 'A' }
}
"""

BUTTON_CLEAN = """export const CompactButton = {
  extends: 'Button',
  minHeight: 'controlHCompact',
  padding: '0 Z',
  ':hover': { background: 'gray1' },
  ':active': { background: 'gray2' }
}

export const Toolbar = {
  CompactButton: { text: 'Save' },
  Button: { text: 'Save', width: '100%', theme: 'primary' },
  Badge: { extends: 'Flex', padding: 'X Z' }
}
"""

# The fixtures of the other validator tests (Python and Node).
EXISTING = [
    """export const PriceCard = {
  padding: 'A',
  Title: { tag: 'h3', text: '{{ pricing.title | polyglot }}' }
}
""",
    """export const formatPrice = function formatPrice (value, currency) {
  const n = Number(value) || 0
  return n.toFixed(2) + ' ' + (currency || '')
}
""",
    """export const Card = (label) => ({
  padding: 'A',
  text: label
})
""",
    """export const cardProps = function cardProps (label) {
  return { padding: 'A', text: label }
}
""",
    "export default { lang: 'en' }\n",
]


def _python(code):
    return server._structural_checks(code)


def _rules(found):
    return [f["message"].split("]")[0].lstrip("[") for f in found]


def test_rule_19_one_condition_on_four_props():
    found = _python(REPEATED_CONDITION)
    assert _rules(found) == ["Rule 19"]
    msg = found[0]["message"]
    assert "s.root.tab === el.key" in msg
    assert "4 CSS props (color, fontWeight, borderColor, opacity)" in msg
    assert found[0]["line"] == 4


def test_rule_19_quiet_for_isx_text_and_two_props():
    assert _python(ISX_FORM) == []
    assert _python(TWO_PROPS_SHARE) == []


def test_rule_65_hover_without_active():
    found = _python(HOVER_NO_ACTIVE)
    assert _rules(found) == ["Rule 65", "Rule 65", "Rule 65"]
    assert [f["line"] for f in found] == [4, 9, 13]
    assert "List › More" in found[2]["message"]


def test_rule_65_quiet_with_active_static_or_project_base():
    assert _python(HOVER_AND_ACTIVE) == []


def test_rule_68_button_call_sites():
    found = _python(BUTTON_PADDING)
    assert _rules(found) == ["Rule 68", "Rule 68", "Rule 68"]
    assert "overrides padding" in found[0]["message"]
    assert "IconButton call site overrides height" in found[1]["message"]
    assert "overrides minHeight, paddingInline" in found[2]["message"]


def test_rule_68_quiet_for_a_variant_and_other_props():
    assert _python(BUTTON_CLEAN) == []


@pytest.mark.parametrize("code", EXISTING)
def test_existing_fixtures_stay_clean(code):
    assert _python(code) == []


def test_python_report_lists_the_warnings(monkeypatch):
    monkeypatch.setattr(server, "FRANK_AUDIT_URL", None)
    monkeypatch.setattr(server, "_run_frank_audit", lambda *a, **k: {"ok": True, "findings": []})
    out = server.audit_component(REPEATED_CONDITION + HOVER_NO_ACTIVE + BUTTON_PADDING)
    warnings = out.split("## Warnings")[1]
    assert warnings.count("[Rule 19]") == 1
    assert warnings.count("[Rule 65]") == 3
    assert warnings.count("[Rule 68]") == 3
    assert "0 errors, 7 warnings" in out


def _node_audit(code):
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "audit_component", "arguments": {"component_code": code}}}),
    ]
    proc = subprocess.run(["node", str(NODE_SERVER)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, timeout=60)
    reply = next(json.loads(l) for l in proc.stdout.split("\n") if l.startswith("{") and '"id":1' in l)
    return reply["result"]["content"][0]["text"]


@pytest.mark.parametrize("code", [REPEATED_CONDITION, HOVER_NO_ACTIVE, BUTTON_PADDING, ISX_FORM, BUTTON_CLEAN])
def test_node_server_reports_the_same_findings(code):
    text = _node_audit(code)
    for f in _python(code):
        assert f["message"] in text
    for rule in ("[Rule 19]", "[Rule 65]", "[Rule 68]"):
        assert text.count(rule) == sum(1 for f in _python(code) if f["message"].startswith(rule))
