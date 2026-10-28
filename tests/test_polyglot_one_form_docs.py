"""Translations reach polyglot through one declaration.

The runtime starts the polyglot plugin only from `context.polyglot` and reads
static strings only from `polyglot.translations`. PROJECT_STRUCTURE showed
`export default { lang, … }` in context.js, and PATTERNS and AUDIT named
"root-level `lang.js`" as a second source next to `context.polyglot`. A
project that followed them declared no polyglot: every `{{ key | polyglot }}`
rendered an empty string and `el.call('polyglot', key)` returned undefined
(23 of 24 App Store apps, 2026-10-28). The docs teach one form,
`polyglot: { defaultLang, languages, translations: lang }`;
tests/runtime_examples checks it translates and the bare key does not."""

import re
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "symbols_mcp" / "skills"
ONE_FORM = re.compile(r"polyglot:\s*\{\s*defaultLang:[^{}]*\blanguages:[^{}]*\btranslations:\s*lang\s*\}")
# `lang` as a shorthand property of an object the file exports by default:
# `export default { lang, cases, … }` or `{ …, lang }`.
BARE_LANG = re.compile(r"export default \{[^}]*?(?:\{|,)\s*lang\s*(?:,|\})|export default \{\s*lang\s*(?:,|\})")


def _code_blocks(text):
    return re.findall(r"```js\n(.*?)```", text, re.S)


def _docs():
    return sorted(SKILLS.glob("*.md"))


def test_no_example_passes_lang_as_a_bare_context_key():
    for doc in _docs():
        for block in _code_blocks(doc.read_text(encoding="utf-8")):
            if "❌" in block or "WRONG" in block:
                continue  # a marked wrong example
            assert not BARE_LANG.search(block), f"{doc.name}: an example exports `lang` as a bare key; polyglot reads polyglot.translations"


def test_no_prose_offers_root_lang_js_as_a_second_source():
    for doc in _docs():
        text = doc.read_text(encoding="utf-8")
        assert not re.search(r"\bor root-level `lang\.js`", text), f"{doc.name}: names root-level lang.js as a second source"
        assert "OR set context.polyglot.translations" not in text, f"{doc.name}: offers two forms"


@pytest.mark.parametrize("name", ["PROJECT_STRUCTURE.md", "PATTERNS.md"])
def test_the_setup_example_declares_the_one_form(name):
    blocks = [b for b in _code_blocks((SKILLS / name).read_text(encoding="utf-8")) if "lang.js" in b]
    assert any(ONE_FORM.search(b) for b in blocks), f"{name}: no lang.js example declares polyglot: {{ defaultLang, languages, translations: lang }}"


@pytest.mark.parametrize("name", ["PROJECT_STRUCTURE.md", "PATTERNS.md"])
def test_the_prose_says_what_a_missing_declaration_does(name):
    text = (SKILLS / name).read_text(encoding="utf-8")
    assert "A bare `lang` key in the context is not read" in text
    assert "renders an empty string" in text
