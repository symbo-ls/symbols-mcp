"""
Symbols MCP — Documentation search, code generation, conversion and audit tools for Symbols.app.
"""

import os
import json
import logging
import re
import subprocess
import shutil
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP, Context

# ---------------------------------------------------------------------------
# frank-audit subprocess bridge
# ---------------------------------------------------------------------------
# All audit / fix / verify / prescription work delegates to the
# @symbo.ls/frank-audit Node CLI. Single source of truth for Symbols
# project audit rules across stdio (this server) and HTTPS (the Node
# proxy). When the CLI is unreachable, audit_component / audit_project
# return a structured error rather than silently downgrading to the old
# regex path.

FRANK_AUDIT_BIN = os.getenv("FRANK_AUDIT_BIN", "frank-audit")
FRANK_AUDIT_URL = os.getenv("FRANK_AUDIT_URL")  # optional HTTP fallback

def _run_frank_audit(*args, stdin_data=None, timeout=120):
    """Shell out to frank-audit CLI. Returns parsed JSON dict.

    On error, returns { "ok": False, "error": {...} } in the same envelope
    shape frank-audit emits — callers can treat success and failure
    uniformly.
    """
    cmd = [FRANK_AUDIT_BIN, *args]
    if "--json" not in args:
        cmd.append("--json")
    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {
            "schema": "frank-audit/1.0",
            "ok": False,
            "error": {
                "code": "E_FRANK_AUDIT_NOT_FOUND",
                "message": f"frank-audit CLI not found (looked for: {FRANK_AUDIT_BIN}). Install with: npm i -g @symbo.ls/frank-audit",
                "category": "user-error",
                "retryable": False,
            },
        }
    except subprocess.TimeoutExpired:
        return {
            "schema": "frank-audit/1.0",
            "ok": False,
            "error": {
                "code": "E_FRANK_AUDIT_TIMEOUT",
                "message": f"frank-audit timed out after {timeout}s",
                "category": "transient",
                "retryable": True,
            },
        }
    if result.returncode != 0 and not result.stdout:
        return {
            "schema": "frank-audit/1.0",
            "ok": False,
            "error": {
                "code": "E_FRANK_AUDIT_FAILED",
                "message": f"frank-audit exited {result.returncode}: {result.stderr[:500]}",
                "category": "permanent",
                "retryable": False,
            },
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {
            "schema": "frank-audit/1.0",
            "ok": False,
            "error": {
                "code": "E_FRANK_AUDIT_BAD_OUTPUT",
                "message": f"frank-audit emitted invalid JSON: {e}",
                "category": "internal",
                "retryable": False,
                "details": {"stdout": result.stdout[:500], "stderr": result.stderr[:500]},
            },
        }

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SKILLS_DIR = os.getenv("SYMBOLS_SKILLS_DIR", str(Path(__file__).resolve().parent / "skills"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("symbols-mcp")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Symbols",
    instructions=(
        # ── MUST-CALL SEQUENCE for any Symbols.app / DOMQL work ──────────────────
        "When the user works in a Symbols project (or asks for Symbols/DOMQL code, design system "
        "work, audits, publishing, anything related), follow this sequence — do NOT skip steps:\n\n"
        "1. **`get_project_context`** FIRST — resolves owner/key/env from cwd's symbols.json. "
        "Treat its `next_step` field as the source of truth for what to do next. Missing owner/key/token "
        "are NEVER hardcoded — surface a `🟢 ASK USER` block.\n"
        "2. **`get_project_rules`** before generating ANY component or page — bundles RULES + FRAMEWORK + "
        "DESIGN_SYSTEM + DEFAULT_PROJECT into one read.\n"
        "3. **`generate_component` / `generate_page`** for new code — these return a prompt + the right context bundle.\n"
        "4. **`audit_component(code)`** after each component — inline validator, returns ~1K of violations. "
        "Pass `include_playbook=True` only if you don't already have AUDIT.md.\n"
        "5. **`audit_project()`** when the user asks for a full project audit — returns the multi-phase playbook. "
        "Pair with `bin/symbols-audit <symbols-dir>` (CLI shipped in this package) for the static-audit phase.\n\n"
        # ── HARD RULES — agents MUST treat these as preconditions, not goals ────
        "Hard rules every output must respect (full list in RULES.md, get via get_project_rules):\n"
        "- Flat element API: props live at `el.X` (NEVER `el.props.X`); events at `el.onClick` (NEVER `on: {}`); "
        "reactive functions take `(el, s)` (NEVER `({ props, state })`).\n"
        "- Lowercase child keys NEVER render. PascalCase only.\n"
        "- **Auto-extend by key** — `Header: { extends: 'Navbar' }` should usually be `Navbar: {}`. "
        "Rename the wrapper key to the component name and drop `extends`. Multi-instance → suffix `_N` "
        "(`Navbar_1`, `Navbar_2`). Keep `extends:` only for genuinely distinct semantic labels, "
        "multi-base composition (`extends: ['Hgroup', 'Form']`), or nested-child chains (`'AppShell > Sidebar'`).\n"
        "- ALL values use design-system tokens. NO raw px/hex/rgb/hsl/ms. Sequence families "
        "(typography / spacing / timing) share the letter alphabet but each generates its own values from "
        "`{ base, ratio }` — `fontSize: 'B'` ≠ `padding: 'B'` ≠ `transition: 'B'`. NO custom-named spacing tokens.\n"
        "- Polyglot for ALL user-facing strings (`'{{ key | polyglot }}'`). NO `t` or `tr` function exists.\n"
        "- Declarative `fetch:` prop (@symbo.ls/fetch). NEVER raw `window.fetch` / `axios` in a component.\n"
        "- `metadata: {…}` via @symbo.ls/helmet. NEVER `document.title = …` or `<head>` injection.\n"
        "- `el.router(path, el.getRoot())` for navigation. NEVER `window.location.*`.\n"
        "- `changeGlobalTheme()` from `smbls`. NEVER `setAttribute('data-theme')` from project code.\n"
        "- Icons via `Icon` component referencing `designSystem.icons`. `html: '<svg ...>'` is BANNED (Rule 62 — "
        "breaks theme color resolution, breaks Brender SSR, breaks sprite deduping).\n"
        "- NO imports between project files. Reference components by PascalCase key, call functions via `el.call('fn', …)`.\n"
        "- NO direct DOM manipulation (`document.querySelector`, `addEventListener`, `classList`, `innerHTML`, "
        "`setAttribute`, `el.node.style.X = …`, `parentNode` traversal — all forbidden).\n"
        "- **Frankability** (so frank.toJSON survives serialization): mutable module-state (`let`/`var`) lives in "
        "`globalScope.js`, not at the top of a component file. Helpers/constants used in 2+ files live in "
        "`globalScope.js`. Constants used by one component live as `scope: { X }` on the component. Factory "
        "closures must surface captures via `scope: { X }` on the returned object. Files must live in "
        "frank-discovered slots (`components/`, `pages/`, `functions/`, `methods/`, `snippets/`, `designSystem/`, "
        "`files/`, `assets/`) — `utils/` / `lib/` / `helpers/` are silently dropped from publish. See "
        "FRANKABILITY.md (`symbols://skills/frankability`) for the full rule reference and verify with "
        "`smbls frank-audit` to see findings (and `--fix` for verify-or-rollback auto-fixes) before shipping.\n\n"
        # ── BOOTSTRAPPING NOTE ─────────────────────────────────────────────────
        "If the project root has no `CLAUDE.md` / `.cursor/rules/` / `.windsurfrules` / `.clinerules`, "
        "suggest the user run `npx @symbo.ls/mcp init-rules` (or equivalent) to drop editor-specific rule "
        "files that auto-load these instructions on every future session — so the agent doesn't have to be "
        "reminded with 'use symbols-mcp' each time."
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SKILLS_PATH = Path(SKILLS_DIR)


def _read_skill(filename: str) -> str:
    """Read a skill markdown file from the skills directory."""
    path = SKILLS_PATH / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"Skill file '{filename}' not found at {path}"


def _read_skills(*filenames: str) -> str:
    """Read and concatenate multiple skill files."""
    parts = []
    for f in filenames:
        content = _read_skill(f)
        if not content.startswith("Skill file"):
            parts.append(content)
    return "\n\n---\n\n".join(parts)


def _load_agent_instructions() -> str:
    """Load the upfront AI agent instructions from RULES.md."""
    return _read_skill("RULES.md")


# ---------------------------------------------------------------------------
# Audit helpers (deterministic rule checking)
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# JS source → JSON conversion helpers (mirrors @symbo.ls/frank pipeline)
# ---------------------------------------------------------------------------

# Data sections that the platform stores
_DATA_KEYS = ("components", "pages", "snippets", "functions", "methods",
              "designSystem", "state", "dependencies", "files", "config")

# Sections that get auto-generated schema entries
_CODE_SECTIONS = {"components", "pages", "functions", "methods", "snippets"}


def _parse_js_to_json(source_code: str) -> dict:
    """Parse DOMQL JavaScript source into platform JSON format.

    Handles export const/default statements and converts JS object literals
    to Python dicts. Functions are stringified as the platform expects.

    This mirrors what @symbo.ls/frank toJSON does: parse source files into
    a structured JSON object with components, pages, designSystem, etc.
    """
    result: dict = {}

    # Strip import statements (DOMQL doesn't use imports between files)
    code = re.sub(r"^\s*import\s+.*$", "", source_code, flags=re.MULTILINE)

    # Try to parse as JSON directly first (already converted)
    stripped = code.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Extract named exports: export const Name = { ... }
    # We find the name and capture everything after the = as raw JS
    export_pattern = re.compile(
        r"export\s+const\s+(\w+)\s*=\s*",
        re.MULTILINE,
    )

    matches = list(export_pattern.finditer(code))
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        # Find the matching closing brace by counting depth
        end = _find_object_end(code, start)
        if end == -1:
            continue
        raw_obj = code[start:end]
        result[name] = raw_obj.strip()

    # Extract default export: export default { ... }
    default_match = re.search(r"export\s+default\s+", code)
    if default_match and not matches:
        start = default_match.end()
        end = _find_object_end(code, start)
        if end != -1:
            raw_obj = code[start:end].strip()
            result["__default__"] = raw_obj

    return result


def _find_object_end(code: str, start: int) -> int:
    """Find the end position of a JS object/array literal starting at `start`."""
    if start >= len(code):
        return -1

    # Skip whitespace to find opening brace/bracket
    i = start
    while i < len(code) and code[i] in " \t\n\r":
        i += 1

    if i >= len(code) or code[i] not in "{[":
        return -1

    opener = code[i]
    closer = "}" if opener == "{" else "]"
    depth = 1
    i += 1
    in_string = None
    in_template = False
    escaped = False

    while i < len(code) and depth > 0:
        ch = code[i]

        if escaped:
            escaped = False
            i += 1
            continue

        if ch == "\\":
            escaped = True
            i += 1
            continue

        if in_string:
            if ch == in_string:
                in_string = None
            i += 1
            continue

        if in_template:
            if ch == "`":
                in_template = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = ch
        elif ch == "`":
            in_template = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1

        i += 1

    return i if depth == 0 else -1


def _js_obj_to_json(raw_js: str) -> str | dict:
    """Best-effort convert a JS object literal string to JSON-compatible format.

    Handles: unquoted keys, trailing commas, single quotes, arrow functions (stringified),
    template literals, shorthand methods.
    """
    s = raw_js.strip()

    # Stringify function values: (args) => { ... } or function(...) { ... }
    # Replace with their string representation
    s = _stringify_functions_in_js(s)

    # Convert single quotes to double quotes (outside of already-double-quoted strings)
    s = _normalize_quotes(s)

    # Quote unquoted keys: { foo: ... } → { "foo": ... }
    s = re.sub(
        r'(?<=[\{,\n])\s*([a-zA-Z_$][\w$]*)\s*:',
        lambda m: f' "{m.group(1)}":',
        s,
    )
    # Also handle @-prefixed keys (breakpoints like @mobileL)
    s = re.sub(
        r'(?<=[\{,\n])\s*(@[\w$]+)\s*:',
        lambda m: f' "{m.group(1)}":',
        s,
    )

    # Remove trailing commas before } or ]
    s = re.sub(r",\s*([}\]])", r"\1", s)

    # Try parsing
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Return as raw string if we can't parse
        return s


def _stringify_functions_in_js(code: str) -> str:
    """Find arrow functions and regular functions in JS and replace with their string form."""
    result = []
    i = 0
    while i < len(code):
        # Check for arrow function patterns: (...) => or word =>
        arrow_match = re.match(
            r'(\([^)]*\)\s*=>|\w+\s*=>)\s*',
            code[i:],
        )
        # Check for function keyword
        func_match = re.match(r'function\s*\w*\s*\(', code[i:])

        if arrow_match and _is_value_position(code, i):
            fn_start = i
            fn_end = _find_function_end(code, i, is_arrow=True)
            if fn_end > i:
                fn_body = code[fn_start:fn_end].strip()
                result.append(json.dumps(fn_body))
                i = fn_end
                continue

        if func_match and _is_value_position(code, i):
            fn_start = i
            fn_end = _find_function_end(code, i, is_arrow=False)
            if fn_end > i:
                fn_body = code[fn_start:fn_end].strip()
                result.append(json.dumps(fn_body))
                i = fn_end
                continue

        result.append(code[i])
        i += 1

    return "".join(result)


def _is_value_position(code: str, pos: int) -> bool:
    """Check if position is in a value context (after : or = or , or [ )."""
    j = pos - 1
    while j >= 0 and code[j] in " \t\n\r":
        j -= 1
    return j >= 0 and code[j] in ":=,["


def _find_function_end(code: str, start: int, is_arrow: bool) -> int:
    """Find end of a function expression."""
    i = start
    # Skip to arrow or opening brace
    if is_arrow:
        arrow_pos = code.find("=>", i)
        if arrow_pos == -1:
            return -1
        i = arrow_pos + 2
        # Skip whitespace
        while i < len(code) and code[i] in " \t\n\r":
            i += 1
        if i < len(code) and code[i] == "{":
            return _find_object_end(code, i)
        # Single expression arrow: find end (next comma or closing brace at same depth)
        depth = 0
        while i < len(code):
            ch = code[i]
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                if depth == 0:
                    return i
                depth -= 1
            elif ch == "," and depth == 0:
                return i
            i += 1
        return i
    else:
        # function(...) { ... } — find opening brace then match it
        brace = code.find("{", i)
        if brace == -1:
            return -1
        return _find_object_end(code, brace)


def _normalize_quotes(s: str) -> str:
    """Convert single-quoted strings to double-quoted strings."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == "'":
            # Find matching closing single quote
            j = i + 1
            while j < len(s):
                if s[j] == "\\" and j + 1 < len(s):
                    j += 2
                    continue
                if s[j] == "'":
                    break
                j += 1
            inner = s[i + 1:j].replace('"', '\\"')
            result.append(f'"{inner}"')
            i = j + 1
        elif s[i] == '"':
            # Skip double-quoted strings as-is
            j = i + 1
            while j < len(s):
                if s[j] == "\\" and j + 1 < len(s):
                    j += 2
                    continue
                if s[j] == '"':
                    break
                j += 1
            result.append(s[i:j + 1])
            i = j + 1
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


def _encode_schema_code(code_str: str) -> str:
    """Encode code for schema storage (frank format: newline→/////n, backtick→/////tilde)."""
    return code_str.replace("\n", "/////n").replace("`", "/////tilde")


def _build_schema_item(section: str, key: str, value: str | dict) -> dict:
    """Build a schema metadata entry for a code-backed item (mirrors frank's buildSchemaItemFromData)."""
    code_str = value if isinstance(value, str) else json.dumps(value, indent=2, default=str)
    item: dict = {
        "title": key,
        "key": key,
        "type": section,
        "code": _encode_schema_code(f"export default {code_str}"),
    }
    if section in ("components", "pages"):
        item.update({"settings": {"gridOptions": {}}, "props": {}, "interactivity": [], "dataTypes": [], "error": None})
    return item


def _build_changes_and_schema(data: dict) -> tuple[list, list, list]:
    """Build coarse changes, granular changes, and orders from project data.

    Mirrors the CLI push pipeline: frank → computeCoarseChanges → preprocessChanges.

    Returns (changes, granular_changes, orders).
    """
    changes = []
    granular = []
    orders = []

    for section_key, section_data in data.items():
        if section_key not in _DATA_KEYS:
            continue
        if not isinstance(section_data, dict):
            # Scalar or list values (e.g., state, dependencies)
            changes.append(["update", [section_key], section_data])
            granular.append(["update", [section_key], section_data])
            continue

        section_item_keys = []

        for item_key, item_value in section_data.items():
            path = [section_key, item_key]
            changes.append(["update", path, item_value])
            section_item_keys.append(item_key)

            # Build granular changes for nested objects
            if isinstance(item_value, dict):
                item_keys = []
                for prop_key, prop_value in item_value.items():
                    granular.append(["update", path + [prop_key], prop_value])
                    item_keys.append(prop_key)
                if item_keys:
                    orders.append({"path": path, "keys": item_keys})
            else:
                granular.append(["update", path, item_value])

            # Auto-generate schema for code sections
            if section_key in _CODE_SECTIONS:
                schema_item = _build_schema_item(section_key, item_key, item_value)
                schema_path = ["schema", section_key, item_key]
                changes.append(["update", schema_path, schema_item])
                # Delete old schema.code to force regeneration
                granular.append(["delete", schema_path + ["code"]])
                for sk, sv in schema_item.items():
                    granular.append(["update", schema_path + [sk], sv])

        if section_item_keys:
            orders.append({"path": [section_key], "keys": section_item_keys})

    return changes, granular, orders


def _audit_code(code: str) -> dict:
    """Run frank-audit's content audit on a single source string.

    Delegates to @symbo.ls/frank-audit (Node CLI) — single source of truth
    for Symbols audit rules. Falls back to an empty-result structure if
    frank-audit is unreachable, with a clear `unavailable` flag so callers
    can warn the user rather than silently passing.
    """
    # Use audit-content via the CLI: stdin = code, args ask for the inline
    # form. Older frank-audit versions don't expose a CLI subcommand for
    # pure content (stdin in), so we work around by writing to a temp file.
    # New (preferred): use the HTTP server's /audit-content endpoint when
    # FRANK_AUDIT_URL is set. Otherwise temp-file via the fs CLI.
    import tempfile
    if FRANK_AUDIT_URL:
        try:
            r = httpx.post(f"{FRANK_AUDIT_URL}/audit-content", json={"code": code, "file": "<inline>"}, timeout=15)
            r.raise_for_status()
            payload = r.json()
            return _convert_findings_to_legacy(payload)
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("frank-audit HTTP audit-content failed: %s", e)
            # fall through to CLI

    # Write code to a temp file in a dummy components/ dir so the CLI sees it
    with tempfile.TemporaryDirectory(prefix="frank-audit-") as tmp:
        comp_dir = Path(tmp) / "components"
        comp_dir.mkdir()
        (comp_dir / "Inline.js").write_text(code, encoding="utf-8")
        (Path(tmp) / "state.js").write_text("export default {}", encoding="utf-8")
        result = _run_frank_audit("audit", str(tmp))

    return _convert_findings_to_legacy(result)


def _convert_findings_to_legacy(payload: dict) -> dict:
    """Convert frank-audit JSON payload to the legacy {violations,warnings,score}
    shape audit_component callers expect."""
    if payload.get("ok") is False:
        err = payload.get("error", {})
        return {
            "passed": False,
            "score": 0,
            "violations": [{
                "line": 0,
                "severity": "error",
                "message": f"[frank-audit unavailable: {err.get('code', 'unknown')}] {err.get('message', '')}",
            }],
            "warnings": [],
            "summary": f"frank-audit unavailable: {err.get('code', 'unknown')}",
            "unavailable": True,
        }
    findings = payload.get("findings", [])
    violations = []
    warnings = []
    for f in findings:
        sev = f.get("severity")
        entry = {
            "line": f.get("line", 0),
            "severity": "error" if sev == "critical" else "warning",
            "message": f"[{f.get('ruleId')}] {f.get('message')}",
        }
        if sev == "critical":
            violations.append(entry)
        else:
            warnings.append(entry)
    total_issues = len(violations) + len(warnings)
    score = max(1, 10 - total_issues)
    return {
        "passed": len(violations) == 0,
        "score": score,
        "violations": violations,
        "warnings": warnings,
        "summary": f"{len(violations)} errors, {len(warnings)} warnings — compliance score: {score}/10",
    }


# ---------------------------------------------------------------------------
# TOOLS
# ---------------------------------------------------------------------------


@mcp.tool()
def get_project_rules() -> str:
    """ALWAYS call this first before any generate_* tool.

    Returns the mandatory Symbols.app rules that MUST be followed:
    - FRAMEWORK.md (authoritative — project structure, plugins, theming, SSR, publish)
    - DESIGN_SYSTEM.md (authoritative — design-system contract + token catalog)
    - RULES.md (62 strict rules — flat API, signal reactivity, design tokens, polyglot, fetch, helmet, theme, reusability, icons)
    - FRANKABILITY.md (every `@symbo.ls/frank-audit` rule with wrong vs canonical examples — patterns that survive frank.toJSON serialization, so generated code is provably frankable from the start)
    - FRANK_FIX_WORKFLOW.md (LLM reference card for the prescription → edit-op flow — the strict 8-kind contract for `apply_frankability_edit_ops`)
    - DEFAULT_PROJECT.md (recommended baseline design-system values + the default-library catalog)

    Violations cause silent failures — black page, nothing renders, or a working app
    with degraded UX you'll later have to rebuild.

    Call this before: generate_component, generate_page, convert_react, convert_html,
    or any code generation task.
    """
    framework = _read_skill("FRAMEWORK.md")
    design_system = _read_skill("DESIGN_SYSTEM.md")
    rules = _load_agent_instructions()
    frankability = _read_skill("FRANKABILITY.md")
    frank_fix_workflow = _read_skill("FRANK_FIX_WORKFLOW.md")
    default_project = _read_skill("DEFAULT_PROJECT.md")
    return f"{framework}\n\n---\n\n{design_system}\n\n---\n\n{rules}\n\n---\n\n{frankability}\n\n---\n\n{frank_fix_workflow}\n\n---\n\n{default_project}"


@mcp.tool()
async def search_symbols_docs(
    query: str,
    max_results: int = 3,
) -> str:
    """Search the Symbols documentation knowledge base for relevant information.

    Args:
        query: Natural language search query about Symbols/DOMQL.
        max_results: Maximum number of results to return (1-5).
    """
    keywords = [w for w in re.split(r"\s+", query.lower()) if len(w) > 2]
    if not keywords:
        keywords = [query.lower()]

    results = []
    for fname in SKILLS_PATH.glob("*.md"):
        content = fname.read_text(encoding="utf-8")
        content_lower = content.lower()
        if not any(kw in content_lower for kw in keywords):
            continue
        lines = content.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                start = max(0, i - 2)
                end = min(len(lines), i + 20)
                snippet = "\n".join(lines[start:end])
                results.append({"file": fname.name, "snippet": snippet})
                break
        if len(results) >= max_results:
            break

    if results:
        return json.dumps(results[:max_results], indent=2)
    return f"No results found for '{query}'. Try a different search term."


@mcp.tool()
def generate_component(
    description: str,
    component_name: str = "MyComponent",
) -> str:
    """Generate a Symbols.app DOMQL component from a description.

    Returns the rules, syntax reference, component catalog, cookbook examples,
    and default library reference as context. The calling LLM uses this context
    to generate a correct, compliant component.

    Args:
        description: What the component should do and look like.
        component_name: PascalCase name for the component.
    """
    context = _read_skills("FRAMEWORK.md", "DESIGN_SYSTEM.md", "RULES.md", "COMMON_MISTAKES.md", "COMPONENTS.md", "SYNTAX.md", "MODERN_STACK.md", "FRANKABILITY.md", "COOKBOOK.md", "DEFAULT_PROJECT.md")
    return f"""# Generate Component: {component_name}

## Description
{description}

## Requirements (STRICT — read FRAMEWORK.md and DESIGN_SYSTEM.md before generating)

### Identity & syntax
- Named export: `export const {component_name} = {{ ... }}`. Plain object — never function/class.
- Flat element API: props on the element (no `props: {{}}` wrapper). Event handlers flat top-level (`onClick`, `onInit`, NEVER `on: {{}}`). Reactive prop functions take `(el, s)` — NEVER `({{ props, state }})`.
- ⚠️ **PascalCase child keys ONLY** — lowercase keys (`h1:`, `nav:`, `form:`, `hgroup:`) NEVER render. #1 cause of "missing content" (Rule 6).
- NO imports between project files — PascalCase keys auto-extend registered components, functions called via `el.call('fnName', …)` (Rule 2/8/33).

### Reusability — MANDATORY (Rule 6 / Rule 61)
- **Auto-extend by key.** `Header: {{ extends: 'Navbar' }}` should almost always be `Navbar: {{}}`. Rename the wrapper key to match the component — DOMQL extends by key automatically. Multi-instance → `Navbar_1`, `Navbar_2` (the part before `_` auto-extends). Keep `extends:` only for (a) genuinely distinct semantic labels (`SidebarNav: {{ extends: 'Navbar' }}` IF the project really uses both names), (b) multi-base composition (`extends: ['Hgroup', 'Form']`), or (c) nested-child chains (`extends: 'AppShell > Sidebar'`). This is the most common boilerplate in Symbols code.
- **Extract every duplicated shape** to `components/<Name>.js`. Repeated PascalCase blocks = candidates for extraction.
- For lists/groups of similar children → `childExtends: 'Name'` (+ `childrenAs: 'state'` if data-driven; preferred for reusability).
- For shared per-child overrides → `childProps: {{ … }}` on the parent.
- NEVER inline-object `childExtends: {{ tag: 'button', ... }}` — must be a quoted string referencing a registered component (frank serialization breaks otherwise).

### Design system — STRICT (Rules 27/28)
- ALL values MUST use design system tokens. ZERO px, ZERO hex/rgb/hsl, ZERO raw ms.
- **Sequence families share letter alphabets but NOT values.** Typography (`fontSize`), spacing (`padding`/`margin`/`gap`/`width`/`height`/etc.), and timing (`transition` duration) each generate their own sequence from `{{ base, ratio }}`. `fontSize: 'B'` ≈ 25px, `padding: 'B'` ≈ 26px, `transition: 'B'` ≈ 200ms — same letter, different values per family. There are NO custom-named spacing/typography/timing tokens — only the generated sequence + sub-tokens (`A1`, `A2`, `B1`, etc.).
- Name-based families: colors (`'primary'`, `'surface'`, `'gray.5'`, `'blue.7'`, `'gray+20'`), themes, gradients, shadows, icons.
- Color modifiers: `.N` is alpha (`'white.5'` = 50% opacity), `+N` lightens, `-N` darkens (both lightness, NOT raw RGB), `=N` absolute lightness %.
- **Icons (Rule 29 / Rule 62 — CRITICAL):** ALWAYS render via the `Icon` component referencing `designSystem.icons` by name (`{{ extends: 'Icon', icon: 'name' }}`). NEVER `html: '<svg ...>'` (BANNED — bypasses design system, breaks Brender SSR, breaks theme color resolution, breaks sprite deduping). NEVER `tag: 'svg'`, NEVER `tag: 'path'` / `tag: 'circle'` / `tag: 'rect'`. NEVER `extends: 'Svg'` for an icon (`Svg` is reserved for non-icon backgrounds). Every SVG, no exceptions, lives in `designSystem/icons.js`.

### Modern stack — MANDATORY
- **Polyglot (Rule 48):** All user-facing text via `'{{{{ key | polyglot }}}}'` template (reactive). Imperative: `(el) => el.call('polyglot', 'key')`. **NO `t` or `tr` function exists** — only `polyglot`. No exceptions for short strings (Submit/OK/Cancel/Loading).
- **Fetch (Rule 47):** Declarative `fetch:` prop (`@symbo.ls/fetch`). NEVER `window.fetch`/`axios` in components.
- **Helmet (Rule 49):** Page-level `metadata: {{ title, description, ... }}`. NEVER `document.title = …`.
- **Router (Rule 42):** `el.router(path, el.getRoot())`. NEVER `window.location.*`.
- **Theme (Rule 50):** `changeGlobalTheme(theme, targetConfig?)` imported from `smbls`. NEVER `setAttribute('data-theme', …)`.

### DOM manipulation — BANNED (Rules 30/32/40)
- NEVER: `document.querySelector`, `getElementById`, `addEventListener`, `classList.toggle`, `innerHTML =`, `setAttribute`, `parentNode` traversal, `el.node.style.X = …`, `XMLHttpRequest`, `EventSource`/`WebSocket` at top level.
- Element traversal: `el.lookdown('Key')`, `el.lookup('Key')`, `el.lookdownAll('Key')`, `el.getRoot()` — NEVER browser DOM queries.

### Conditional rendering / animation
- For tabs/views use `show:`/`hide:` (keeps in DOM). For conditional content use `if:` (removes from DOM, **destructive — kills CSS transitions, focus, scroll, video playback**).
- Use `.isX` + `'.isX'` block for grouped conditional CSS (fully reactive — block re-applies when `isX` state changes).

### Layout
- `flow:` / `align:` are valid shorthands (`flow: 'y'` ≡ `flexFlow: 'column'`).
- Built-in atoms (Box, Flex, Grid, Hgroup, Form, Text, Img, Iframe, Svg, Picture, Video, Link, Button, Input, etc.) auto-apply when key matches — NEVER `extends: 'Flex'` / `'Box'` / `'Text'` (just name the key `Flex: {{...}}` etc.).
- Include responsive breakpoints (`@tabletS`, `@mobileL`, `@dark`, `@light`).

### Aesthetics
- Follow modern UI/UX: visual hierarchy, confident typography, minimal cognitive load.

## Context — Rules, Syntax & Examples

{context}"""


@mcp.tool()
def generate_page(
    description: str,
    page_name: str = "home",
) -> str:
    """Generate a Symbols.app DOMQL page with routing + helmet metadata + fetch integration.

    Returns rules, project structure, patterns, snippets, and default library
    reference as context for page generation.

    Args:
        description: What the page should contain and do.
        page_name: camelCase name for the page (used in route map).
    """
    context = _read_skills(
        "FRAMEWORK.md", "DESIGN_SYSTEM.md",
        "RULES.md", "COMMON_MISTAKES.md", "PROJECT_STRUCTURE.md", "SHARED_LIBRARIES.md",
        "MODERN_STACK.md", "FRANKABILITY.md",
        "PATTERNS.md", "SNIPPETS.md", "COMPONENTS.md", "DEFAULT_PROJECT.md",
    )
    return f"""# Generate Page: {page_name}

## Description
{description}

## Requirements (STRICT — read FRAMEWORK.md and DESIGN_SYSTEM.md before generating)

### Identity & registration
- Export: `export const {page_name} = {{ ... }}`, extending `'Page'` (NEVER `'Flex'` / `'Box'`).
- Add to `pages/index.js` route map: `'/{page_name}': {page_name}`. (`pages/index.js` is the ONLY file allowed to import siblings.)
- Page is a plain object composing components by PascalCase key — no imports between project files.

### Syntax (same rules as components)
- Flat element API; reactive prop functions `(el, s)`; flat `onX` events; lowercase child keys NEVER render.
- NO `props: {{}}` / `on: {{}}` / `({{ props, state }})` destructured signatures.

### Reusability — MANDATORY (Rule 6 / Rule 61)
- **Auto-extend by key.** `Header: {{ extends: 'Navbar' }}` should almost always be `Navbar: {{}}`. Rename the wrapper key to match the component. Multi-instance → `Navbar_1`, `Navbar_2`. Keep `extends:` only for genuinely distinct semantic labels, multi-base composition, or nested-child chains.
- Extract every duplicated shape across pages to `components/<Name>.js`. NEVER duplicate inline.
- `childExtends: 'Name'` for lists/groups; `childProps: {{ … }}` for shared per-child overrides.

### Design system — STRICT
- ALL values from design system tokens. ZERO px, hex, rgb, hsl, raw durations.
- **Icons (Rule 29 / Rule 62 — CRITICAL):** every SVG goes in `designSystem/icons.js` and is rendered via `{{ extends: 'Icon', icon: 'name' }}`. NEVER `html: '<svg ...>'`, NEVER `tag: 'svg'` / `tag: 'path'`, NEVER `extends: 'Svg'` for an icon.

### Modern stack — MANDATORY
- **Helmet (Rule 49):** `metadata: {{ title, description, 'og:image', ... }}` (or `metadata: (el, s) => ({{ ... }})` for dynamic). NEVER `document.title = …`.
- **Fetch (Rule 47):** Declarative `fetch: {{ from: 'table', cache: '5m', ... }}` (or array for parallel). Configure adapter once in `config.js`: `db: {{ adapter: 'supabase', url, key }}`. NEVER `window.fetch`/`axios`.
- **Polyglot (Rule 48):** ALL user-facing text via `'{{{{ heading | polyglot }}}}'` template. Imperative: `el.call('polyglot', 'key')`. NO `t` or `tr` function — only `polyglot`.
- **Router (Rule 42):** `el.router(path, el.getRoot())`. NEVER `window.location`. Param routes (`/blog/:id`) populate `state.params`.
- **Theme (Rule 50):** `changeGlobalTheme(theme, targetConfig?)` imported from `smbls`. NEVER `setAttribute('data-theme')`.

### DOM bans (Rules 30/40/42)
- NEVER `document.*`, `addEventListener`, `classList`, `innerHTML`, `setAttribute`, `parentNode`, `el.node.style.X = …`, `XMLHttpRequest`, raw `EventSource`/`WebSocket`.

### Conditional rendering
- Tabs/views: `show:` / `hide:` (keeps in DOM). Conditional content: `if:` (removes from DOM — destructive: kills CSS transitions, focus, scroll, video).
- Grouped reactive CSS: `isX: (el, s) => …` + `'.isX': {{ … }}` block (re-applies when state changes).

### Layout / responsive
- `flow:` / `align:` valid; built-in atoms auto-apply by key. Responsive breakpoints `@tabletS`, `@mobileL`, `@dark`, `@light`.

## Context — Rules, Structure, Patterns & Snippets

{context}"""


@mcp.tool()
def convert_react(source_code: str) -> str:
    """Convert React/JSX code to Symbols.app DOMQL.

    Provide React component code and receive the conversion context including
    migration rules, syntax reference, and examples.

    Args:
        source_code: The React/JSX source code to convert.
    """
    context = _read_skills("FRAMEWORK.md", "DESIGN_SYSTEM.md", "RULES.md", "MIGRATION.md", "SYNTAX.md", "MODERN_STACK.md", "FRANKABILITY.md", "COMPONENTS.md", "LEARNINGS.md", "DEFAULT_PROJECT.md")
    return f"""# Convert React → Symbols DOMQL

## Source Code to Convert
```jsx
{source_code}
```

## Conversion Rules (DOMQL — STRICT)
- Function/class components → plain object exports (`export const X = {{ ... }}`)
- JSX → nested object children (PascalCase keys auto-extend registered components)
- import/export between project files → REMOVE (reference by string key, call functions via `el.call('fn', …)`)
- useState → `state: {{ key: val }}`; updates via `s.update({{ key: newVal }})`
- useReducer → `s.apply(fn)` / `s.applyFunction(fn)`
- useEffect mount → `onInit` (before DOM) or `onRender` (after DOM). For data-loading effects, prefer the declarative `fetch:` prop (Rule 47).
- useEffect deps → `onStateUpdate(changes, el, s, ctx)` or signal-based reactive prop functions (the framework auto-tracks reads).
- useMemo / useCallback → not needed; reactive prop functions are memoized by signal subscription.
- props → flat on the component (NO `props: {{}}` wrapper — FORBIDDEN)
- onClick={{handler}} → `onClick: (e, el, s) => {{ … }}` (flat top-level, NEVER `on: {{ click }}`)
- className / styled-components → DOMQL CSS-in-props with **design system tokens only** (Rule 27/28). ZERO px, hex, rgb, hsl.
- .map() → `children: (el, s) => s.items, childExtends: 'ItemName', childrenAs: 'state'`
- conditional rendering → `if: (el, s) => boolean` (removes from DOM) or `show:`/`hide:` (keeps in DOM, for tabs)
- React.Fragment / `<>...</>` → not needed; just nest object keys.
- React Router `<Link>` / `useNavigate()` → `extends: 'Link'` with `href`; programmatic navigation via `el.router(path, el.getRoot())` (Rule 41/42)
- React Helmet / Next `<Head>` → page-level `metadata: {{ title, description, ... }}` via @symbo.ls/helmet (Rule 49)
- fetch / axios / SWR / TanStack Query → declarative `fetch: {{ from, cache, transform, … }}` via @symbo.ls/fetch (Rule 47). Caching/dedup/retry/refetch-on-focus are built in — DO NOT reimplement them.
- i18next / react-intl → `@symbo.ls/polyglot` with `'{{{{ key | polyglot }}}}'` template, `el.call('polyglot', 'key')`, `el.call('setLang', 'ka')` (Rule 48)
- localStorage state → state + fetch plugin's `local` adapter, or polyglot's `setLang` for language. NEVER raw `localStorage.setItem` in components.
- Theme switcher / dark mode → `changeGlobalTheme()` from @symbo.ls/scratch (Rule 50). NEVER `setAttribute('data-theme', …)` directly.
- **MANDATORY: ALL values MUST use design system tokens** — ZERO px values, ZERO hex colors, ZERO rgb/hsl
- Use `Icon` component for SVGs — never inline SVG markup, never `tag: 'svg'` (Rule 29)
- NO direct DOM manipulation — banned: `document.*`, `addEventListener`, `classList`, `innerHTML`, `setAttribute`, `el.node.style.X = …`, `parentNode`/`children` traversal (Rule 30/32/40)

## Context — Migration Guide, Syntax & Rules

{context}"""


@mcp.tool()
def convert_html(source_code: str) -> str:
    """Convert raw HTML/CSS to Symbols.app DOMQL components.

    Provide HTML code and receive the conversion context including component
    catalog, syntax reference, and design system tokens.

    Args:
        source_code: The HTML/CSS source code to convert.
    """
    context = _read_skills("FRAMEWORK.md", "DESIGN_SYSTEM.md", "RULES.md", "SYNTAX.md", "MODERN_STACK.md", "FRANKABILITY.md", "COMPONENTS.md", "SNIPPETS.md", "LEARNINGS.md", "DEFAULT_PROJECT.md")
    return f"""# Convert HTML → Symbols DOMQL

## Source Code to Convert
```html
{source_code}
```

## Conversion Rules (DOMQL — STRICT)
- `<div>` with flex/grid → drop the wrapper; use `flow: 'x'`/`flow: 'y'` (replaces `extends: 'Flex'`) or `display: 'grid'` directly. Plain wrappers don't need `extends: 'Box'`.
- `<span>`, `<p>`, `<h1>`-`<h6>` → keep semantic via `tag` (`P`, `H1`–`H6` exist as default-library components).
- `<a>` → `extends: 'Link'` with `href` at root (NEVER inside `attr: {{}}`). For SPA navigation: `onClick: (e, el) => {{ e.preventDefault(); el.router(href, el.getRoot()) }}`.
- `<button>` → `extends: 'Button'` (supports `icon` + `text`).
- `<input>` → `Input`, `Radio`, `Checkbox` based on type. Standard HTML attrs (placeholder, type, name, value, disabled) flat at root — NOT inside `attr: {{}}`.
- `<img>` → `Img` (or `Picture` containing `Img`; `<picture>` does NOT support `src`).
- `<form>` → `Form` (or `tag: 'form'`).
- `<ul>`/`<ol>` + `<li>` → `children` array + `childExtends: 'ItemName'`.
- CSS classes → flatten as CSS-in-props on the component (no className prop).
- CSS px values → design-system sequence tokens. **`fontSize` uses the typography sequence; `padding`/`margin`/`gap`/`width`/`height`/etc. use the spacing sequence; `transition` duration uses the timing sequence — same letters, DIFFERENT values per family.** Default mappings: spacing `A`≈16px, `B`≈26px, `C`≈42px (golden ratio); typography `A`≈16px, `B`≈20px, `C`≈25px (major-third). Sub-tokens (`Z1`, `Z2`, `A1`, `A2`, etc.) are minor increments within each family. NO custom-named spacing tokens.
- CSS colors → theme color tokens (`primary`, `surface`, `gray.5`, `blue+20`, `white.7`). NEVER hex/rgb/hsl.
- Durations → `designSystem.timing` tokens.
- Media queries → `@tabletS`, `@mobileL`, `@screenS`, `@dark`, `@light` (NEVER chain selectors — Rule 44).
- id/class attributes → not needed (PascalCase keys serve as identifiers; cases.js handles conditional classes).
- inline styles → flatten as component properties (or `style: {{…}}` only for raw CSS escape hatches).
- `<style>` blocks → distribute to component-level CSS-in-props.
- `<svg>` icons → `Icon` component + `designSystem/icons` — NEVER `tag: 'svg'`, NEVER inline SVG markup, NEVER nest `<path>` (Rule 29).
- Hardcoded user-facing text → polyglot `'{{{{ key | polyglot }}}}'` template (Rule 48).
- jQuery / vanilla JS event listeners → flat `onClick`/`onInput`/`onSubmit` props on the element. NO `addEventListener`.
- Hardcoded data fetches → declarative `fetch:` prop via @symbo.ls/fetch (Rule 47).
- `<head>` `<title>`, `<meta>` → page/app-level `metadata: {{…}}` via @symbo.ls/helmet (Rule 49).
- **MANDATORY: ALL values MUST use design system tokens** — ZERO px values, ZERO hex colors, ZERO rgb/hsl, ZERO raw durations.
- NO direct DOM manipulation — all structure via DOMQL declarative syntax (Rule 30/32/40).

## Context — Syntax, Components & Design System

{context}"""


@mcp.tool()
def audit_component(component_code: str, include_playbook: bool = False) -> str:
    """Inline VALIDATOR for a single Symbols/DOMQL component string.

    Runs the deterministic ruleset (flat element API, signal reactivity, design system
    tokens, declarative fetch/polyglot/helmet/router, no DOM manipulation, Rule 62 icon ban)
    against an in-memory string of code. Returns a tight report with violations + warnings.

    Use this:
    - During generation, to verify a freshly-generated component before saving
    - In any client without shell access (claude.ai web, hosted MCP) where the CLI
      is unreachable
    - On a single file's contents, not a whole project

    Adjacent tools — call these for different scopes:
    - `audit_project()` — returns the MULTI-PHASE PROJECT AUDIT PLAYBOOK (instructions
      for the agent to follow). Use when the user asks for a full project audit.
    - `bin/symbols-audit <symbols-dir>` (CLI, ships with this package) — filesystem
      regex sweep across an entire project. Use during the playbook's static-audit phase.

    By default returns ONLY the findings (≈1–2K chars). Pass `include_playbook=True`
    to also dump the AUDIT.md playbook in the same response when you don't already have it.

    Args:
        component_code: The JavaScript/DOMQL source string to validate.
        include_playbook: Append the full audit playbook to the response. Default False
                          to keep responses small. Default agents should NOT set this —
                          call `audit_project()` separately if the playbook is needed.
    """
    result = _audit_code(component_code)

    output = f"""# Audit Report

## Summary
{result['summary']}
Passed: {'Yes' if result['passed'] else 'No'}

## Violations (Errors)
"""
    if result["violations"]:
        for v in result["violations"]:
            output += f"- **Line {v['line']}**: {v['message']}\n"
    else:
        output += "No violations found.\n"

    output += "\n## Warnings\n"
    if result["warnings"]:
        for w in result["warnings"]:
            output += f"- **Line {w['line']}**: {w['message']}\n"
    else:
        output += "No warnings.\n"

    if result["violations"]:
        output += """
## MANDATORY ACTION

**Every violation above MUST be fixed to 100%. There is NO concept of "known debt", "accepted violations", or "95% fixed" in Symbols. ALL violations must reach 100% resolution — zero exceptions. Do NOT label any violation as "known debt" or defer it. Rewrite every occurrence using proper DOMQL syntax.**

"""

    output += "\n## Next steps\n"
    output += "- For a full project audit (filesystem-wide regex + chrome-mcp UI tests + iteration to convergence), call `audit_project()` to get the playbook.\n"
    output += "- For the framework rules in detail, call `get_project_rules()`.\n"

    if include_playbook:
        output += "\n---\n\n## Audit Playbook (AUDIT.md)\n\n"
        output += _read_skill("AUDIT.md")

    return output


@mcp.tool()
async def audit_and_fix_frankability(
    symbols_dir: str,
    mode: str = "report",
    aggressive: bool = False,
    max_iterations: int = 20,
    ctx: Context = None,
) -> str:
    """Run frank-audit and optionally apply fixes — supports a sampling-driven
    LLM loop that resolves findings the mechanical fixer can't safely handle.

    Modes:
      'report'    — run audit, list findings, do not modify files
      'safe-fix'  — apply mechanical fixes with verify-or-rollback safety
                    (every applied fix is verified against frank.toJSON; regressions roll back)
      'full'      — run safe-fix first, THEN drive an LLM loop via MCP sampling
                    over the remaining prescriptions:
                      1. prescribe_frankability_fixes(dir) → JSON prescriptions
                      2. for each prescription (capped by max_iterations):
                         a. ctx.session.create_message() with the strict
                            edit-op contract prompt
                         b. parse the LLM's JSON response
                         c. apply_frankability_edit_ops with verify-or-rollback
                         d. one retry on malformed JSON
                      3. report aggregate (mechanical + LLM fixes)
                    Requires the host to support MCP sampling (Claude Code does;
                    some hosts don't — falls back gracefully to safe-fix mode
                    with a warning when ctx.session is unavailable).

    Args:
        symbols_dir: Absolute path to the symbols/ directory.
        mode: 'report' | 'safe-fix' | 'full'
        aggressive: With safe-fix or full, also apply medium-confidence fixes.
        max_iterations: Cap on LLM-driven prescriptions in 'full' mode (default 20).

    Returns: JSON-stringified result with schema, opId, findings, applied/skipped,
             rolledBack, baseline, finalState, and (in 'full' mode) llmRounds[].
    """
    if mode not in ("report", "safe-fix", "full"):
        return json.dumps({"ok": False, "error": {"code": "E_BAD_MODE", "message": "mode must be 'report' | 'safe-fix' | 'full'"}})

    audit_result = _run_frank_audit("audit", symbols_dir)
    if audit_result.get("ok") is False:
        return json.dumps(audit_result, indent=2)

    if mode == "report":
        return json.dumps(audit_result, indent=2)

    # safe-fix and full both run the mechanical fix first
    fix_args = ["fix", symbols_dir]
    if aggressive:
        fix_args.append("--aggressive")
    fix_result = _run_frank_audit(*fix_args)
    if fix_result.get("ok") is False:
        return json.dumps(fix_result, indent=2)

    if mode == "safe-fix":
        return json.dumps(fix_result, indent=2)

    # mode == "full": LLM-driven prescription loop via MCP sampling
    if ctx is None or not hasattr(ctx, "session") or ctx.session is None:
        # Sampling unavailable — return safe-fix result with a note
        fix_result["llmLoopSkipped"] = "MCP sampling not available in this host; call prescribe_frankability_fixes + apply_frankability_edit_ops manually"
        return json.dumps(fix_result, indent=2)

    rx_payload = _run_frank_audit("prescriptions", symbols_dir)
    if rx_payload.get("ok") is False:
        return json.dumps({**fix_result, "prescriptionsError": rx_payload.get("error")}, indent=2)

    prescriptions = rx_payload.get("prescriptions", [])[:max_iterations]
    llm_rounds = []
    llm_applied = 0
    llm_skipped = 0
    llm_errors = 0

    for rx in prescriptions:
        round_result = await _run_llm_prescription_round(symbols_dir, rx, ctx)
        llm_rounds.append(round_result)
        if round_result.get("status") == "applied":
            llm_applied += 1
        elif round_result.get("status") == "skipped":
            llm_skipped += 1
        else:
            llm_errors += 1

    return json.dumps({
        **fix_result,
        "llmRounds": llm_rounds,
        "llmSummary": {
            "prescriptionsConsidered": len(prescriptions),
            "applied": llm_applied,
            "skipped": llm_skipped,
            "errors": llm_errors,
        },
    }, indent=2)


def _build_prescription_prompt(rx: dict) -> str:
    """The LLM-facing prompt for one prescription. Strict JSON output expected."""
    finding = rx.get("finding", {})
    src = rx.get("sourceContext") or []
    related = rx.get("relatedFiles") or []

    src_lines = "\n".join(
        f"{l['line']:>5}  {'> ' if l.get('isFinding') else '  '}{l['text']}"
        for l in src
    ) if src else "(no source context available)"

    related_lines = "\n".join(
        f"  - {r['file']}:{r['line']} ({r['role']})"
        for r in related[:8]
    ) if related else "  (none)"

    return f"""You are applying ONE Symbols-project fix. Return JSON only.

# Finding
Rule: {finding.get('ruleId')} ({finding.get('ruleName', '')})
File: {finding.get('file')}:{finding.get('line')}
Severity: {finding.get('severity')} · Confidence: {finding.get('confidence')} · Risk: {finding.get('risk')}
Message: {finding.get('message')}
Refusal reason: {finding.get('refusalReason') or '(automated fixer refused — needs LLM judgment)'}

# Source context
{src_lines}

# Related files
{related_lines}

# Edit-op contract (STRICT — return ONLY this shape)
{{
  "ops": [
    // one or more of these op kinds:
    {{ "kind": "removeImport",       "file": "...", "specifier": "...", "source": "..." }},
    {{ "kind": "moveFile",           "from": "...", "to": "..." }},
    {{ "kind": "addToIndexFile",     "dir": "...", "filename": "..." }},
    {{ "kind": "addToGlobalScope",   "name": "...", "value": <json>, "valueIsCode": false }},
    {{ "kind": "removeTopLevelDecl", "file": "...", "name": "..." }},
    {{ "kind": "addElementScope",    "file": "...", "componentName": "...", "key": "...", "value": <json>, "valueIsCode": false }},
    {{ "kind": "replaceTokenValue",  "file": "...", "line": <n>, "oldValue": "...", "newValue": "..." }},
    {{ "kind": "skip",               "reason": "..." }}
  ],
  "reasoning": "one sentence on what you decided and why"
}}

Decision protocol:
- If you can determine a safe fix → emit ops that resolve the finding.
- If intent is unclear or context is insufficient → emit a single skip op with a reason.
- NEVER return prose outside the JSON. NEVER invent op kinds. NEVER embed JS in `value` unless you also set `valueIsCode: true`.

Frank-audit will validate every op before applying. Verify-or-rollback runs after — you don't need to verify yourself."""


async def _run_llm_prescription_round(symbols_dir: str, rx: dict, ctx) -> dict:
    """One sampling round: prompt the LLM, parse, validate, apply. Returns
    a structured round-result for the caller's report."""
    from mcp.types import SamplingMessage, TextContent

    prompt = _build_prescription_prompt(rx)
    rx_id = rx.get("id", "unknown")

    # Sampling call. One retry on malformed JSON (max 2 attempts total).
    parsed_ops = None
    last_error = None
    raw_response = None
    for attempt in range(2):
        try:
            msg = SamplingMessage(role="user", content=TextContent(type="text", text=prompt))
            result = await ctx.session.create_message(
                messages=[msg],
                max_tokens=2000,
                system_prompt="You are a focused codemod. Output only the JSON object specified. No prose.",
            )
            raw_response = result.content.text if hasattr(result.content, "text") else str(result.content)
            try:
                parsed_ops = json.loads(raw_response)
                break
            except json.JSONDecodeError as e:
                last_error = f"malformed JSON: {e}"
                if attempt == 0:
                    # Re-prompt with the validator error
                    prompt = prompt + f"\n\n# Your previous output was invalid JSON: {e}. Return JSON only."
                    continue
        except Exception as e:  # pylint: disable=broad-except
            last_error = f"sampling failed: {e}"
            break

    if parsed_ops is None:
        return {"prescriptionId": rx_id, "status": "error", "reason": last_error or "sampling produced no ops"}

    ops = parsed_ops.get("ops") if isinstance(parsed_ops, dict) else parsed_ops
    if not isinstance(ops, list) or not ops:
        return {"prescriptionId": rx_id, "status": "error", "reason": "LLM emitted no ops"}

    # Special case: single skip op
    if len(ops) == 1 and ops[0].get("kind") == "skip":
        return {
            "prescriptionId": rx_id,
            "status": "skipped",
            "reason": ops[0].get("reason", "LLM declined to fix"),
            "llmReasoning": parsed_ops.get("reasoning"),
        }

    # Apply via subprocess. Write to temp file.
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump({"ops": ops}, tmp)
        ops_path = tmp.name
    try:
        apply_result = _run_frank_audit("apply-edits", symbols_dir, "--ops", ops_path)
    finally:
        try: os.unlink(ops_path)
        except OSError: pass

    if apply_result.get("ok") is False:
        return {
            "prescriptionId": rx_id,
            "status": "error",
            "reason": apply_result.get("error", {}).get("message", "apply-edits failed"),
            "llmReasoning": parsed_ops.get("reasoning"),
        }
    if apply_result.get("rolledBack"):
        return {
            "prescriptionId": rx_id,
            "status": "skipped",
            "reason": "applied edit ops would have regressed against baseline — rolled back",
            "llmReasoning": parsed_ops.get("reasoning"),
            "baseline": apply_result.get("baseline"),
            "finalState": apply_result.get("finalState"),
        }
    return {
        "prescriptionId": rx_id,
        "status": "applied",
        "applied": apply_result.get("applied"),
        "skipped": len(apply_result.get("skipped", [])),
        "llmReasoning": parsed_ops.get("reasoning"),
        "opCount": len(ops),
    }


@mcp.tool()
def prescribe_frankability_fixes(symbols_dir: str) -> str:
    """Generate LLM-ready prescriptions for frank-audit findings that can't be auto-fixed.

    Each prescription contains:
      - finding (rule, file, line, refusal reason)
      - sourceContext (~30 lines around the finding)
      - relatedFiles (other places that mention the same symbol)
      - **proposedOps** — array of edit ops the rule's helper logic produced
        (e.g. FA304 already mapped 36px → 'C2' from the project's spacing
        scale; FA301 already matched the closest palette token). The agent
        can submit these verbatim to apply_frankability_edit_ops, or modify
        before submitting.
      - explanation (the rule's docs)
      - safetyCheck (verify command run after apply)

    Workflow for the agent:
      1. Call this tool to get prescriptions.
      2. Inspect each `proposedOps` array. Either submit verbatim or modify.
         For findings with no proposedOps (structural refactors like FA2xx
         multifile-helpers, FA5xx DOM bans), construct your own ops from
         the 12 strict op kinds:
           removeImport | moveFile | addToIndexFile | addToGlobalScope |
           removeTopLevelDecl | addElementScope | replaceTokenValue |
           renameObjectKey | removeObjectKey | setObjectProperty |
           addDesignToken | skip
      3. Call apply_frankability_edit_ops(symbols_dir, ops) — frank-audit
         validates every op, snapshots, applies, runs verify, rolls back on
         regression. Failed ops return structured details (E_OLDVALUE_NOT_FOUND
         with actualLine, E_KEY_NOT_FOUND with availableKeys, etc.) so you
         can retry intelligently.
      4. Repeat until prescriptions are exhausted or no progress.

    Args:
        symbols_dir: Absolute path to the symbols/ directory.

    Returns: JSON with schema version, opId, list of prescriptions.
    """
    return json.dumps(_run_frank_audit("prescriptions", symbols_dir), indent=2)


@mcp.tool()
def apply_frankability_edit_ops(symbols_dir: str, ops_json: str) -> str:
    """Apply LLM-generated edit ops to a Symbols project with verify-or-rollback.

    Pass `ops_json` as a JSON string of either:
      - { "ops": [...] }
      - or just an array of op objects.

    Each op must be one of the 8 strict kinds (see prescribe_frankability_fixes).
    The applier validates every op, snapshots affected files, applies, runs
    frank.toJSON to verify, and rolls back if the result regresses against
    the pre-apply state.

    Args:
        symbols_dir: Absolute path to the symbols/ directory.
        ops_json: JSON string containing the edit ops.

    Returns: JSON with applied/skipped/rolledBack/baseline/finalState.
    """
    import tempfile
    try:
        ops = json.loads(ops_json)
    except json.JSONDecodeError as e:
        return json.dumps({"ok": False, "error": {"code": "E_BAD_JSON", "message": f"ops_json is not valid JSON: {e}"}})
    # Write to temp file for the CLI
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(ops, tmp)
        ops_path = tmp.name
    try:
        return json.dumps(_run_frank_audit("apply-edits", symbols_dir, "--ops", ops_path), indent=2)
    finally:
        try: os.unlink(ops_path)
        except OSError: pass


@mcp.tool()
def verify_frankability(symbols_dir: str) -> str:
    """Verify a Symbols project bundles cleanly via frank.toJSON.

    Independent of audit/fix — runs the same round-trip that apply-edits uses
    after every mutation, but as a standalone check. Useful for the agent to
    confirm a project is in a known-good state before starting a fix loop, or
    after a series of manual edits.

    Returns: JSON with { ok, bundleable, scanIssues, ... }.
    """
    return json.dumps(_run_frank_audit("verify", symbols_dir), indent=2)


@mcp.tool()
def rollback_frankability(symbols_dir: str, op_id: str) -> str:
    """Restore a Symbols project to its state before a specific op ran.

    Every apply-edits run snapshots affected files under
    `<symbols_dir>/.frank-audit/snapshots/<opId>/` before mutating. Use this
    to undo a specific op (or a chain by walking backwards through opIds
    listed by `snapshots_frankability`).

    Args:
        symbols_dir: Absolute path to the symbols/ directory.
        op_id: The opId to roll back to (from a prior apply-edits result).

    Returns: JSON with { ok, restored: [...filePaths], opId }.
    """
    return json.dumps(_run_frank_audit("rollback", op_id, symbols_dir), indent=2)


@mcp.tool()
def snapshots_frankability(symbols_dir: str) -> str:
    """List recent snapshotted opIds for a Symbols project.

    Each entry corresponds to a frank-audit op that wrote files. Pass an
    opId to `rollback_frankability` to restore that op's pre-state.

    Returns: JSON with { ok, opIds: [{ opId, timestamp, files }] }.
    """
    return json.dumps(_run_frank_audit("snapshots", symbols_dir), indent=2)


@mcp.tool()
def frankability_log(symbols_dir: str, limit: int = 50) -> str:
    """Tail the audit log for a Symbols project.

    Returns the most recent NDJSON entries from `<symbols_dir>/.frank-audit/log`.
    Each entry records audit/fix/apply-edits/rollback events with opId,
    timestamp, and outcome — useful for understanding history without
    re-running ops.

    Args:
        symbols_dir: Absolute path to the symbols/ directory.
        limit: Maximum number of entries to return (default 50).

    Returns: JSON with { ok, entries: [...] }.
    """
    return json.dumps(_run_frank_audit("log", "--limit", str(limit), symbols_dir), indent=2)


@mcp.tool()
def explain_frankability_rule(rule_id: str) -> str:
    """Return the documentation block for a specific frank-audit rule.

    Each rule (FA001 through FA902) has an `explain()` method that returns a
    human-readable description, examples of the bad/good patterns, and the
    rationale. Use this when an agent encounters an unfamiliar finding and
    needs context before deciding on a fix.

    Args:
        rule_id: The rule ID (e.g. 'FA301', 'FA806').

    Returns: JSON with { ok, ruleId, name, severity, description, explanation }.
    """
    return json.dumps(_run_frank_audit("explain", rule_id), indent=2)


@mcp.tool()
def get_cli_reference() -> str:
    """Returns the complete `smbls` CLI reference (`@symbo.ls/cli`).

    Mirrors `smbls/CLI_FOR_MCP.md`. Covers: configuration files (symbols.json, .symbols_local/),
    API URL resolution order + env-var overrides, common flag conventions, full command map
    (project lifecycle, auth, sync, project mgmt, workspace ops, files & assets, integrations,
    GitHub, Frank JSON↔FS, dev/build/deploy, code transformation, SDK proxy, ask),
    publish flow (one-shot + granular), MCP/agent usage rules (--non-interactive + --yes
    + SYMBOLS_API_CHANNEL + SYMBOLS_AUTH_TOKEN), error-handling contracts (AUTH_REQUIRED,
    ECONNREFUSED, missing app key), source-file map, and CLI-specific anti-patterns.
    """
    return _read_skill("CLI.md")


@mcp.tool()
def get_sdk_reference() -> str:
    """Returns the complete `@symbo.ls/sdk` API reference (3.14.0).

    Mirrors `sdk/SDK_FOR_MCP.md`. Covers all 24 services with full method lists:
    auth, collab, project, plan, subscription, file, payment, dns, branch, pullRequest,
    admin, screenshot, tracking, waitlist, metrics, integration, featureFlag, organization,
    workspace, workspaceData (typed wrapper for /workspace/*), kv, allocationRule,
    sharedAsset, credits. Plus: SDK class lifecycle, BaseService contract, TokenManager
    (singleton, auto-refresh), environment matrix (channel URLs), root event bus
    (sdk.rootBus with last-payload replay), validation surface, federation primitive
    (multi-Supabase registry), permissions reference (ROLE_PERMISSIONS,
    PROJECT_ROLE_PERMISSIONS, TIER_FEATURES), error handling contract, and MCP integration notes.
    """
    return _read_skill("SDK.md")


@mcp.tool()
def audit_project(phase: str = "all") -> str:
    """Returns the multi-phase PROJECT AUDIT PLAYBOOK (instructions for the agent).

    Strict mode is the default. Strict means EXHAUSTIVE — the agent does not stop
    until every finding is `resolved`, `framework_bug` (in framework_audit_results.md),
    or an active `🟢 ASK USER` block awaiting user input. No finding stays `open`.

    Two CLI flags (default ON in strict mode, both opt-out via --no-...):
    - `--deep-fix`: agent does NOT stop at first blocker (missing project key,
      auth-protected route, missing CLI subcommand). Surfaces ASK-USER blocks or
      runs documented fallbacks (e.g. publish blocked → local frank+brender preview).
    - `--deep-framework-audit`: every framework_bug entry includes a Read+Grep trace
      into smbls/ source identifying the suspected function, plus a suggested patch.

    Two report files the CLI emits + the agent appends to:
    - `audit/symbols_audit_results.md` — PROJECT findings + resolutions
    - `audit/framework_audit_results.md` — FRAMEWORK bugs + repro + smbls/ trace +
      suggested patch (each entry must be debuggable by someone who's never seen
      the code; vague "doesn't work" entries are not acceptable in strict mode)

    Findings have an `origin` field (project | framework | shared) classified by
    `bin/symbols-audit` heuristically, then refined by the agent during Phase 2.

    This tool is a **playbook getter**, not an executor. The agent runs the playbook
    itself using:
    - `get_project_context` — call FIRST to resolve owner/key/env. Missing values
      surface as `🟢 ASK USER` blocks (NEVER hardcoded).
    - `bin/symbols-audit <symbols-dir>` — deterministic regex sweep + dual-report
      template emission. Strict + deep modes default ON.
    - `audit_component(code)` — inline single-component validator (no filesystem).
    - chrome-mcp tools — for the Phase 3c local-vs-remote UI testing protocol.

    Phase summary:
    - Phase 0: setup + baseline metrics + project-context resolution. Missing
      owner/key resolved here via ASK-USER (not deferred).
    - Phase 1: static audit via `bin/symbols-audit` (creates findings.json +
      symbols_audit_results.md + framework_audit_results.md templates).
    - Phase 2: fix loop with self-test. 3 failed fix attempts → finding becomes
      framework_bug with deep-audit trace. Continue, never stop on first bug.
    - Phase 3a: build gates with fallbacks for missing CLI subcommands.
    - Phase 3b: publish to staging WITH FALLBACK LADDER. If publish is blocked
      (missing key, AUTH_REQUIRED, env doesn't exist), agent surfaces ASK-USER
      AND/OR falls back to local `frank to-json` + `brender` + http.server preview
      so Phase 3c still has a viewable artifact. NEVER silently skip publish.
    - Phase 3c: STRICT UI testing — local-vs-(remote OR localfallback) side-by-side,
      click every clickable, icon rendering verification per Rule 62, theme/lang/
      active-nav/forms/responsive.
    - Phase 4: iterate until two consecutive runs converge — zero open findings,
      zero pending ASK-USER, viewable artifact exists. Deep-fix loop re-visits
      framework_bug entries to strengthen them and retries blockers.
    - Phase 5: report = record of resolutions, NOT a TODO list. Strict mode
      forbids "Recommended follow-up tasks" as a terminal state.

    Transport awareness: this playbook assumes stdio MCP transport (filesystem
    access). For SSE/HTTPS/CDN, the agent surfaces filesystem-dependent steps as
    shell commands the user runs locally, then resumes Phase 2/3 with pasted
    output. `audit_component` and `audit_project` are stateless and work over
    any transport; `get_project_context` and `bin/symbols-audit` are stdio-only.

    Output artifacts created in <project>/audit/: findings.json, symbols_audit_results.md (framework bugs), runs/, report.md.

    Use this when the user asks to audit, validate, refactor for compliance, or 'make my project publish-ready in one shot'. Returns the entire playbook so the agent has the full context. Pair with the bundled `bin/symbols-audit` CLI for the deterministic regex pass.

    Args:
        phase: 'all' (full playbook — default) | '0' | '1' | '2' | '3' | '4' | '5' (just one phase's section)
    """
    full = _read_skill("AUDIT.md")
    if phase == "all":
        return full
    # Extract a specific phase by header
    phase_headers = {
        "0": "## Phase 0",
        "1": "## Phase 1",
        "2": "## Phase 2",
        "3": "## Phase 3",
        "4": "## Phase 4",
        "5": "## Phase 5",
    }
    header = phase_headers.get(phase)
    if not header:
        return f"Unknown phase: {phase}. Use 'all' or 0-5.\n\n{full[:500]}..."
    start = full.find(header)
    if start == -1:
        return f"Phase {phase} not found in playbook. Returning full playbook.\n\n{full}"
    # Find the next ## or end
    next_header = full.find("\n## ", start + 1)
    section = full[start:next_header] if next_header > 0 else full[start:]
    return f"# Symbols Project Audit — Phase {phase}\n\n{section}\n\n---\n\n> For the full playbook, call audit_project() with phase='all'."


@mcp.tool()
def convert_to_json(
    source_code: str,
    section: str = "components",
) -> str:
    """Convert DOMQL JavaScript source code to platform JSON format.

    Parses export statements from generated component/page code and converts
    them into the structured JSON the Symbols platform expects. Functions are
    automatically stringified (as the platform stores them as strings).

    Use this after generate_component or generate_page to get JSON that can
    be passed directly to save_to_project.

    Mirrors the @symbo.ls/frank toJSON + stringifyFunctions pipeline that the
    CLI uses when running `smbls push`.

    Args:
        source_code: JavaScript source code with export const/default statements.
        section: Target section — "components", "pages", "functions", "snippets",
                 "designSystem", "state". Determines how exports are categorized.
    """
    parsed = _parse_js_to_json(source_code)

    if not parsed:
        return "Could not parse any exports from the source code. Make sure it contains `export const Name = { ... }` or `export default { ... }`."

    # Build the project data structure
    result: dict = {}

    for name, raw_value in parsed.items():
        # Convert raw JS object literal to JSON
        if isinstance(raw_value, str):
            converted = _js_obj_to_json(raw_value)
        else:
            converted = raw_value

        if name == "__default__":
            # Default export — use as the entire section value
            if section in ("designSystem", "state", "dependencies", "config"):
                result[section] = converted
            else:
                result.setdefault(section, {})["default"] = converted
        else:
            result.setdefault(section, {})[name] = converted

    # Return as formatted JSON ready for save_to_project
    output = json.dumps(result, indent=2, default=str)

    sections = list(result.keys())
    items = []
    for sec in sections:
        if isinstance(result[sec], dict):
            items.extend(result[sec].keys())

    return f"""# Converted to Platform JSON

**Section:** {', '.join(sections)}
**Items:** {', '.join(items) if items else 'default export'}

```json
{output}
```

This JSON is ready to use with `save_to_project`. Pass the JSON object above as the `changes` parameter.

**Full flow:**
1. `convert_to_json` (done) → structured JSON
2. `save_to_project` → push to platform (creates new version)
3. `publish` → make version live
4. `push` → deploy to environment (production/staging/dev)"""


@mcp.tool()
def detect_environment(
    has_symbols_json: bool = False,
    has_symbols_dir: bool = False,
    has_package_json: bool = False,
    has_cdn_import: bool = False,
    has_iife_script: bool = False,
    has_json_data: bool = False,
    has_mermaid_config: bool = False,
    file_list: str = "",
) -> str:
    """[Legacy] Detect Symbols environment from caller-supplied file flags.

    **Prefer `get_project_context`** — it does the same classification by inspecting
    the filesystem directly (no caller-supplied flags needed) AND returns project
    owner/key/auth state in the same call.

    Kept for backward compatibility with older agent prompts. New code should call
    `get_project_context(cwd)` instead — its response includes `env_type`,
    `env_evidence`, and `env_guidance` fields equivalent to this tool's output,
    plus `owner`, `key`, `token_present`, and `next_step` guidance.

    Args:
        has_symbols_json: Whether symbols.json exists in the project root.
        has_symbols_dir: Whether a symbols/ directory exists with components/, pages/, etc.
        has_package_json: Whether package.json exists with smbls dependency.
        has_cdn_import: Whether HTML files contain CDN imports (esm.sh/smbls, etc.).
        has_iife_script: Whether HTML files use script src smbls (IIFE global).
        has_json_data: Whether the project uses frank-generated JSON data files.
        has_mermaid_config: Whether mermaid/wrangler config or GATEWAY_URL/JSON_PATH env vars are present.
        file_list: Comma-separated list of key files in the project root.
    """
    env_type = "unknown"
    confidence = "low"

    if has_mermaid_config:
        env_type = "remote_server"
        confidence = "high"
    elif has_json_data:
        env_type = "json_runtime"
        confidence = "high"
    elif has_symbols_json and has_symbols_dir:
        env_type = "local_project"
        confidence = "high"
    elif has_symbols_dir or (has_package_json and has_symbols_json):
        env_type = "local_project"
        confidence = "medium"
    elif has_cdn_import or has_iife_script:
        env_type = "cdn"
        confidence = "high"
    elif has_package_json:
        env_type = "local_project"
        confidence = "low"
    elif file_list:
        files = file_list.lower()
        if "index.html" in files and "package.json" not in files and "symbols.json" not in files:
            env_type = "cdn"
            confidence = "medium"

    full_guide = _read_skill("RUNNING_APPS.md")
    output = f"# Environment Detection\n\n**Detected: {env_type}** (confidence: {confidence})\n\n"

    if env_type == "local_project":
        structure_guide = _read_skill("PROJECT_STRUCTURE.md")
        shared_libs_guide = _read_skill("SHARED_LIBRARIES.md")
        output += "## Your Environment: Local Project\n\n"
        output += "You're working in a standard Symbols project with file-based structure.\n\n"
        output += "### Code Format\n"
        output += "- Components: `export const Name = { extends: 'Flex', ... }` in `components/`\n"
        output += "- Pages: `export const pageName = { extends: 'Page', ... }` in `pages/`\n"
        output += "- State: `export default { key: value }` in `state.js`\n"
        output += "- Functions: `export const fn = function() {}` in `functions/`\n"
        output += "- No imports between files (except pages/index.js)\n\n"
        output += "### Commands\n"
        output += "```bash\nnpm start          # dev server\nsmbls build        # production build\nsmbls push         # deploy to platform\nsmbls deploy       # deploy to provider\n```\n\n"
        output += f"### Full Project Structure Reference\n\n{structure_guide}"
        output += f"\n\n### Shared Libraries Reference\n\n{shared_libs_guide}"
    elif env_type == "cdn":
        cdn_guide = _read_skill("RUNNING_APPS.md")
        output += "## Your Environment: CDN (Browser-Only)\n\n"
        output += "You're running Symbols directly in the browser via CDN import.\n\n"
        output += "### Code Format\n"
        output += "- Single HTML file with `<script type=\"module\">`\n"
        output += "- Import: `import { create } from 'https://esm.sh/smbls'`\n"
        output += "- Define app as inline object tree\n"
        output += "- Mount: `create(App, { designSystem, components, functions, state })`\n"
        output += "- Components defined as JS variables (no file-based registry)\n\n"
        output += "### Limitations\n"
        output += "- No file-based routing (use tab/view switching)\n"
        output += "- No SSR\n"
        output += "- `childExtends: 'Name'` needs components passed to `create()`\n\n"
        output += f"### Full CDN Reference\n\n{cdn_guide}"
    elif env_type == "json_runtime":
        output += "## Your Environment: JSON Runtime (Frank)\n\n"
        output += "You're running Symbols from serialized JSON project data.\n\n"
        output += "### Code Format\n"
        output += "- Project data is a JSON object with components, pages, designSystem, state, functions\n"
        output += "- Functions are serialized as strings\n"
        output += "- Convert with: `smbls frank to-json ./symbols` or `toJSON({ entry: './symbols' })`\n"
        output += "- Reverse with: `smbls frank to-fs data.json -o ./output` or `toFS(data, './output')`\n"
        output += "- Can be loaded by Mermaid server via JSON_PATH env var\n\n"
        output += f"### Full Reference\n\n{full_guide}"
    elif env_type == "remote_server":
        output += "## Your Environment: Remote Symbols Server (Mermaid)\n\n"
        output += "You're working with the Mermaid rendering server for hosted Symbols apps.\n\n"
        output += "### URL Patterns\n"
        output += "- Production: `https://app.user.preview.symbols.app/`\n"
        output += "- Development: `https://app.user.preview.dev.symbols.app/`\n"
        output += "- Staging: `https://app.user.preview.staging.symbols.app/`\n"
        output += "- Legacy: `https://app.symbo.ls/`\n"
        output += "- Custom domains supported\n\n"
        output += "### Deployment\n"
        output += "```bash\nsmbls push    # deploy to Symbols platform\n```\n\n"
        output += f"### Full Reference\n\n{full_guide}"
    else:
        output += "## Could Not Determine Environment\n\n"
        output += "Provide more details about your project files to get specific guidance.\n\n"
        output += f"### All 4 Ways to Run Symbols Apps\n\n{full_guide}"

    return output


# ---------------------------------------------------------------------------
# Project context — read symbols.json from cwd or a given path
# ---------------------------------------------------------------------------

def _find_symbols_json(start: Path) -> Path | None:
    """Walk up from start looking for symbols.json. Stops at filesystem root."""
    cur = start.resolve()
    seen = set()
    while cur not in seen:
        seen.add(cur)
        candidate = cur / "symbols.json"
        if candidate.is_file():
            return candidate
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent
    return None


def _detect_env_type(project_root: Path, symbols_dir: Path | None) -> dict:
    """Classify a project as local | cdn | json_runtime | remote_server | unknown.

    Cheap filesystem inspection — no network, no expensive walks.
    """
    evidence: list[str] = []

    has_symbols_dir = symbols_dir is not None and symbols_dir.exists() and symbols_dir.is_dir()
    if has_symbols_dir:
        evidence.append("symbols/ directory exists")

    pkg_json = project_root / "package.json"
    has_smbls_dep = False
    if pkg_json.is_file():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "smbls" in deps or any(k.startswith("@symbo.ls/") for k in deps):
                has_smbls_dep = True
                evidence.append("package.json depends on smbls / @symbo.ls/*")
        except Exception:
            pass

    has_cdn_marker = False
    has_iife_marker = False
    has_mermaid_marker = False
    for html in list(project_root.glob("*.html"))[:8]:
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "esm.sh/smbls" in text or "esm.sh/@symbo.ls" in text:
            has_cdn_marker = True
        if "/smbls.iife" in text or 'window.smbls' in text:
            has_iife_marker = True

    wrangler = project_root / "wrangler.toml"
    if wrangler.is_file():
        try:
            wt = wrangler.read_text(encoding="utf-8", errors="ignore")
            if "GATEWAY_URL" in wt or "JSON_PATH" in wt or "mermaid" in wt.lower():
                has_mermaid_marker = True
                evidence.append("wrangler.toml configures mermaid gateway")
        except Exception:
            pass

    if has_cdn_marker:
        evidence.append("HTML imports from esm.sh/smbls")
    if has_iife_marker:
        evidence.append("HTML loads smbls IIFE bundle")

    has_json_data = any((project_root / "data").glob("*.json")) if (project_root / "data").is_dir() else False
    if not has_json_data:
        sj = project_root / "symbols.json"
        if sj.is_file():
            try:
                blob = json.loads(sj.read_text(encoding="utf-8"))
                if "components" in blob or "pages" in blob:
                    has_json_data = True
                    evidence.append("symbols.json contains compiled components/pages JSON")
            except Exception:
                pass

    if has_mermaid_marker:
        env_type = "remote_server"
    elif has_json_data:
        env_type = "json_runtime"
    elif has_symbols_dir and has_smbls_dep:
        env_type = "local"
    elif has_cdn_marker or has_iife_marker:
        env_type = "cdn"
    elif has_symbols_dir:
        env_type = "local"
    else:
        env_type = "unknown"

    guidance = {
        "local": "Local Symbols project. Run with `smbls start` (parcel/vite/esbuild/webpack — see bundler field). Push with `smbls push <env>`.",
        "cdn": "CDN-loaded Symbols. Edit components in your HTML/JS — no build step. See symbols://skills/running-apps for hosted CDN setup.",
        "json_runtime": "Pre-compiled JSON runtime (frank-built). Components/pages are statically generated. Modify source then re-run frank.",
        "remote_server": "Remote Symbols server (mermaid). Routing via {project}.{owner}.preview.symbols.app. Edits propagate via `smbls push`.",
        "unknown": "Could not classify the environment. Inspect file_list manually or ask the user.",
    }[env_type]

    return {
        "env_type": env_type,
        "env_evidence": evidence,
        "env_guidance": guidance,
    }


@mcp.tool()
def get_project_context(cwd: str = "") -> str:
    """Read the current Symbols project context — START HERE for any Symbols task.

    Walks up from `cwd` (or the MCP process's working directory) looking for `symbols.json`,
    parses it, classifies the environment from filesystem signals, and returns a single
    JSON payload with everything an agent needs to begin work.

    Returns:
    - **owner**, **key**, **dir**, **bundler**, **sharedLibraries**, **brender** — from symbols.json
    - **project_root** — absolute path of the project root
    - **symbols_dir** — absolute path of the symbols/ source dir (or null)
    - **env_type** — `local | cdn | json_runtime | remote_server | unknown`
    - **env_evidence** — the filesystem signals that produced the classification
    - **env_guidance** — one-line guidance for that env type
    - **token_present** — whether `SYMBOLS_TOKEN` env var or `~/.smblsrc` token exists
    - **api_base** — the Symbols API base URL (defaults to https://api.symbols.app)
    - **next_step** — what the agent should do next (ask user / log in / proceed)

    **ALWAYS call this first** for any Symbols-project task. It replaces the older
    `detect_environment` tool (which required the caller to pre-compute file flags).

    Use this BEFORE calling any auth-required tool (save_to_project, publish, push,
    get_project) — combine with `token_present` to know whether to prompt for `login`.

    Never hardcode owner/key/credentials. If `next_step` says "ask the user", ASK.

    Args:
        cwd: Directory to start searching from. Defaults to the MCP server's process cwd.
             Pass an absolute path when the agent's cwd differs from the project root.
    """
    start = Path(cwd) if cwd else Path.cwd()
    if not start.exists():
        return json.dumps({
            "found": False,
            "error": f"path does not exist: {start}",
            "next_step": "Confirm the project path with the user.",
        }, indent=2)

    found = _find_symbols_json(start)
    if not found:
        return json.dumps({
            "found": False,
            "searched_from": str(start.resolve()),
            "env_type": "unknown",
            "next_step": (
                "No symbols.json found in or above this directory. Either: "
                "(a) the user is not inside a Symbols project — ask them to navigate to one or run `smbls init`; "
                "(b) the user wants to scaffold a new project — run `smbls init` or call `create_project`; "
                "(c) for auth-required tools, ask the user for the project owner+key, then call `list_projects` after `login`."
            ),
        }, indent=2)

    try:
        data = json.loads(found.read_text(encoding="utf-8"))
    except Exception as e:
        return json.dumps({
            "found": True,
            "resolved_path": str(found),
            "error": f"failed to parse symbols.json: {e}",
            "next_step": "Inspect symbols.json manually — it is malformed JSON.",
        }, indent=2)

    owner = data.get("owner")
    key = data.get("key")
    token_present = bool(os.getenv("SYMBOLS_TOKEN"))
    smblsrc = Path.home() / ".smblsrc"
    if not token_present and smblsrc.is_file():
        try:
            rc = json.loads(smblsrc.read_text(encoding="utf-8"))
            token_present = bool(rc.get("token"))
        except Exception:
            pass

    project_root = found.parent
    raw_dir = data.get("dir", "./symbols")
    symbols_dir = (project_root / raw_dir).resolve()
    env = _detect_env_type(project_root, symbols_dir)

    result: dict = {
        "found": True,
        "resolved_path": str(found),
        "project_root": str(project_root),
        "symbols_dir": str(symbols_dir) if symbols_dir.exists() else None,
        "owner": owner,
        "key": key,
        "dir": raw_dir,
        "bundler": data.get("bundler"),
        "sharedLibraries": data.get("sharedLibraries", []),
        "brender": bool(data.get("brender")),
        "api_base": API_BASE,
        "token_present": token_present,
        **env,
    }

    missing = []
    if not owner:
        missing.append("owner")
    if not key:
        missing.append("key")

    if missing:
        result["next_step"] = (
            f"symbols.json is missing required field(s): {', '.join(missing)}. "
            "Ask the user for the missing value(s) — never invent or hardcode them. "
            "If the project is new, suggest `smbls init` or `create_project`."
        )
    elif not token_present:
        result["next_step"] = (
            "Project context found, but no auth token is cached. For any tool that "
            "requires authentication (save_to_project, publish, push, get_project), "
            "ask the user to log in: call `login(email, password)` or set SYMBOLS_TOKEN. "
            "Never hardcode or assume credentials."
        )
    else:
        result["next_step"] = (
            "Project context resolved AND token is available. You can call auth-required "
            "tools directly — pass owner/key from this context."
        )

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

API_BASE = os.getenv("SYMBOLS_API_URL", "https://api.symbols.app")

_AUTH_HELP = """To authenticate, provide one of:
- **token**: JWT from `smbls login` (stored in ~/.smblsrc) or env var SYMBOLS_TOKEN
- **api_key**: API key (sk_live_...) from your project's integration settings

To get a token:
1. Run `smbls login` in your terminal, or
2. Use the `login` tool with your email and password

Your project can be identified by either:
- **project_id**: MongoDB ObjectId (from project settings or symbols.json)
- **project_key**: Project key (pr_xxxx, found in symbols.json or project URL)"""


def _auth_header(token: str = "", api_key: str = "") -> dict:
    """Build Authorization header from token or API key."""
    if api_key:
        return {"Authorization": f"ApiKey {api_key}", "Content-Type": "application/json"}
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return {}


async def _api_request(method: str, path: str, token: str = "", api_key: str = "", body: dict | None = None) -> dict:
    """Make an authenticated request to the Symbols API.

    All SDK endpoints use /core prefix (e.g. /core/projects, /core/auth/login).
    """
    headers = _auth_header(token, api_key)
    if not headers:
        return {"success": False, "error": "No credentials provided", "message": _AUTH_HELP}
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{API_BASE}{path}"
        if method == "POST":
            resp = await client.post(url, headers=headers, json=body or {})
        elif method == "GET":
            resp = await client.get(url, headers=headers)
        elif method == "PATCH":
            resp = await client.patch(url, headers=headers, json=body or {})
        elif method == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
    try:
        return resp.json()
    except Exception:
        return {"success": False, "error": f"HTTP {resp.status_code}", "message": resp.text}


async def _resolve_project_id(project: str, token: str = "", api_key: str = "") -> tuple[str, str | None]:
    """Resolve a project key (pr_xxxx) or ID to (project_id, error).

    Returns (project_id, None) on success or ("", error_message) on failure.
    """
    if not project:
        return "", "Project identifier is required."
    # If it looks like a key (starts with pr_ or contains non-hex chars), resolve via API
    is_key = project.startswith("pr_") or not all(c in "0123456789abcdef" for c in project)
    if is_key:
        result = await _api_request("GET", f"/core/projects/key/{project}", token=token, api_key=api_key)
        if result.get("success"):
            data = result.get("data", {})
            return data.get("_id", ""), None
        return "", f"Project '{project}' not found: {result.get('error', 'unknown error')}"
    return project, None


# ---------------------------------------------------------------------------
# TOOLS — Auth, Projects, Save, Publish & Push
# ---------------------------------------------------------------------------


@mcp.tool()
async def login(
    email: str,
    password: str,
) -> str:
    """Log in to the Symbols platform and get an access token.

    Use this when the user needs to authenticate before any project operation.
    Returns a JWT token that can be used with all project tools.

    Args:
        email: Symbols account email address.
        password: Symbols account password.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/core/auth/login",
            headers={"Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
    try:
        result = resp.json()
    except Exception:
        return f"Login failed: HTTP {resp.status_code}"

    if result.get("success"):
        data = result.get("data", {})
        tokens = data.get("tokens", {})
        user = data.get("user", {})
        token = tokens.get("accessToken", "")
        return (
            f"Logged in as {user.get('name', user.get('email', 'unknown'))}.\n"
            f"Token: {token}\n"
            f"Expires: {tokens.get('accessTokenExp', {}).get('expiresAt', 'unknown')}\n\n"
            f"Use this token with project, save, publish and push tools."
        )
    else:
        error = result.get("error", result.get("message", "Unknown error"))
        return f"Login failed: {error}"


@mcp.tool()
async def list_projects(
    token: str = "",
    api_key: str = "",
) -> str:
    """List the user's Symbols projects.

    Returns project names, keys, and IDs so the user can choose which project
    to save to or publish. Requires authentication.

    Args:
        token: JWT access token from login.
        api_key: API key (sk_live_...) from project integration settings.
    """
    if not token and not api_key:
        return f"Authentication required.\n\n{_AUTH_HELP}"

    result = await _api_request("GET", "/core/projects", token=token, api_key=api_key)

    if result.get("success"):
        projects = result.get("data", [])
        if not projects:
            return "No projects found. Use `create_project` to create one."
        lines = ["# Your Projects\n"]
        for p in projects:
            name = p.get("name", "Untitled")
            key = p.get("key", "—")
            pid = p.get("_id", "")
            visibility = p.get("visibility", "private")
            lines.append(f"- **{name}** — key: `{key}`, id: `{pid}`, visibility: {visibility}")
        return "\n".join(lines)
    else:
        error = result.get("error", "Unknown error")
        return f"Failed to list projects: {error}"


@mcp.tool()
async def create_project(
    name: str,
    key: str = "",
    token: str = "",
    api_key: str = "",
    visibility: str = "private",
    language: str = "javascript",
) -> str:
    """Create a new Symbols project on the platform.

    Use this when the user wants to save generated components to a new project.
    Returns the project ID and key for use with save_to_project and publish.

    Args:
        name: Project display name.
        key: Project key (pr_xxxx format). Auto-generated from name if empty.
        token: JWT access token from login.
        api_key: API key (sk_live_...) from project integration settings.
        visibility: Project visibility — "private", "public", or "password-protected".
        language: Project language (default: "javascript").
    """
    if not token and not api_key:
        return f"Authentication required.\n\n{_AUTH_HELP}"

    body: dict = {"name": name, "visibility": visibility, "language": language}
    if key:
        body["key"] = key

    result = await _api_request("POST", "/core/projects", token=token, api_key=api_key, body=body)

    if result.get("success"):
        data = result.get("data", {})
        return (
            f"Project created successfully.\n"
            f"Name: {data.get('name', name)}\n"
            f"Key: `{data.get('key', 'unknown')}`\n"
            f"ID: `{data.get('_id', 'unknown')}`\n\n"
            f"Use this project key/ID with `save_to_project` to push your components."
        )
    else:
        error = result.get("error", "Unknown error")
        message = result.get("message", "")
        return f"Create failed: {error}\n{message}"


@mcp.tool()
async def get_project(
    project: str,
    token: str = "",
    api_key: str = "",
    branch: str = "main",
) -> str:
    """Get a Symbols project's current data (components, pages, designSystem, state).

    Use this to inspect what's already in a project before saving changes.

    Args:
        project: Project key (pr_xxxx) or project ID.
        token: JWT access token from login.
        api_key: API key (sk_live_...) from project integration settings.
        branch: Branch to read from (default: "main").
    """
    if not token and not api_key:
        return f"Authentication required.\n\n{_AUTH_HELP}"

    is_key = project.startswith("pr_") or not all(c in "0123456789abcdef" for c in project)
    if is_key:
        path = f"/core/projects/key/{project}/data?branch={branch}&version=latest"
    else:
        path = f"/core/projects/{project}/data?branch={branch}&version=latest"

    result = await _api_request("GET", path, token=token, api_key=api_key)

    if result.get("success"):
        data = result.get("data", {})
        # Summarize the project data
        components = data.get("components", {})
        pages = data.get("pages", {})
        ds = data.get("designSystem", {})
        state = data.get("state", {})
        functions = data.get("functions", {})

        lines = [f"# Project Data (branch: {branch})\n"]
        lines.append(f"**Components ({len(components)}):** {', '.join(list(components.keys())[:20]) or 'none'}")
        lines.append(f"**Pages ({len(pages)}):** {', '.join(list(pages.keys())[:20]) or 'none'}")
        lines.append(f"**Design System keys:** {', '.join(list(ds.keys())[:15]) or 'none'}")
        lines.append(f"**State keys:** {', '.join(list(state.keys())[:15]) or 'none'}")
        lines.append(f"**Functions ({len(functions)}):** {', '.join(list(functions.keys())[:15]) or 'none'}")
        lines.append(f"\n---\n\nFull data:\n```json\n{json.dumps(data, indent=2, default=str)[:8000]}\n```")
        return "\n".join(lines)
    else:
        error = result.get("error", "Unknown error")
        return f"Failed to get project data: {error}"


@mcp.tool()
async def save_to_project(
    project: str,
    changes: str,
    token: str = "",
    api_key: str = "",
    message: str = "",
    branch: str = "main",
) -> str:
    """Save components, pages, or design system data to a Symbols project.

    This applies changes to the project and creates a new version.
    Use after generate_component/generate_page to persist the output.

    The changes parameter is a JSON string with the data to merge into the project.
    Structure mirrors the project data format:

    ```json
    {
      "components": {
        "Header": {
          "extends": "Flex",
          "props": { "flow": "x", "gap": "B", "padding": "A B" },
          "Logo": { "extends": "Icon", "props": { "name": "logo" } },
          "Nav": { "extends": "Flex", "gap": "A" }
        }
      },
      "pages": {
        "home": {
          "extends": "Page",
          "Header": {},
          "Hero": { "extends": "Flex" }
        }
      },
      "designSystem": { ... },
      "state": { ... },
      "functions": { ... }
    }
    ```

    Only include the sections you want to update — omitted sections are left unchanged.

    Args:
        project: Project key (pr_xxxx) or project ID.
        changes: JSON string with project data to save (components, pages, designSystem, state, functions).
        token: JWT access token from login.
        api_key: API key (sk_live_...) from project integration settings.
        message: Version commit message describing the changes.
        branch: Branch to save to (default: "main").
    """
    if not token and not api_key:
        return f"Authentication required.\n\n{_AUTH_HELP}"

    # Parse the changes JSON
    try:
        changes_data = json.loads(changes)
    except json.JSONDecodeError as e:
        return f"Invalid JSON in changes: {e}"

    if not isinstance(changes_data, dict):
        return "Changes must be a JSON object with keys like components, pages, designSystem, state, functions."

    # Resolve project ID
    project_id, err = await _resolve_project_id(project, token=token, api_key=api_key)
    if err:
        return err

    # Build change tuples, granular changes, and orders (mirrors CLI push pipeline)
    changes_tuples, granular_changes, orders = _build_changes_and_schema(changes_data)

    if not changes_tuples:
        return "No valid changes found. Include at least one data section (components, pages, designSystem, state, functions, etc.)."

    body: dict = {
        "changes": changes_tuples,
        "granularChanges": granular_changes,
        "orders": orders,
        "message": message or "Updated via Symbols MCP",
        "branch": branch,
        "type": "patch",
    }

    result = await _api_request(
        "POST", f"/core/projects/{project_id}/changes",
        token=token, api_key=api_key, body=body,
    )

    if result.get("success"):
        data = result.get("data", {})
        version = data.get("value", data.get("version", data.get("id", "unknown")))
        saved_sections = list(changes_data.keys())
        return (
            f"Saved to project `{project}` successfully.\n"
            f"Version: {version}\n"
            f"Branch: {branch}\n"
            f"Sections updated: {', '.join(saved_sections)}\n\n"
            f"Use `publish` to make this version live, or `push` to deploy to an environment."
        )
    else:
        error = result.get("error", "Unknown error")
        message_text = result.get("message", "")
        return f"Save failed: {error}\n{message_text}"


@mcp.tool()
async def publish(
    project: str,
    token: str = "",
    api_key: str = "",
    version: str = "",
    branch: str = "main",
) -> str:
    """Publish a version of a Symbols project to the platform.

    Makes the specified version (or latest) the published/live version.
    Call save_to_project first to save your changes, then publish to make them live.

    Requires authentication — provide either token or api_key.

    Args:
        project: Project ID (MongoDB ObjectId) or project key (pr_xxxx).
        token: JWT access token from login or ~/.smblsrc.
        api_key: API key (sk_live_...) from project integration settings. Alternative to token.
        version: Version string or version ID to publish. Leave empty for latest.
        branch: Branch to publish from (default: "main").
    """
    if not token and not api_key:
        return f"Authentication required.\n\n{_AUTH_HELP}"

    project_id, err = await _resolve_project_id(project, token=token, api_key=api_key)
    if err:
        return err

    body = {"branch": branch}
    if version:
        body["version"] = version

    result = await _api_request(
        "POST", f"/core/projects/{project_id}/publish",
        token=token, api_key=api_key, body=body,
    )

    if result.get("success"):
        data = result.get("data", {})
        return f"Published successfully.\nVersion: {data.get('value', data.get('id', 'unknown'))}"
    else:
        error = result.get("error", "Unknown error")
        message = result.get("message", "")
        return f"Publish failed: {error}\n{message}"


@mcp.tool()
async def push(
    project: str,
    token: str = "",
    api_key: str = "",
    environment: str = "production",
    mode: str = "published",
    version: str = "",
    branch: str = "main",
) -> str:
    """Push/deploy a Symbols project to a specific environment.

    Deploys the project to a target environment (production, staging, dev).
    Call publish first to set the live version, then push to deploy.

    Requires authentication — provide either token or api_key.

    Args:
        project: Project ID (MongoDB ObjectId) or project key (pr_xxxx).
        token: JWT access token from login or ~/.smblsrc.
        api_key: API key (sk_live_...) from project integration settings. Alternative to token.
        environment: Target environment key (e.g. "production", "staging", "dev").
        mode: Deploy mode — "latest" (newest from branch), "published" (current published version), "version" (specific version), or "branch" (track a branch).
        version: Required when mode is "version" — the version string or ID to deploy.
        branch: Branch to deploy from when mode is "latest" or "branch" (default: "main").
    """
    if not token and not api_key:
        return f"Authentication required.\n\n{_AUTH_HELP}"

    project_id, err = await _resolve_project_id(project, token=token, api_key=api_key)
    if err:
        return err

    body: dict = {"mode": mode, "branch": branch}
    if version:
        body["version"] = version

    result = await _api_request(
        "POST", f"/core/projects/{project_id}/environments/{environment}/publish",
        token=token, api_key=api_key, body=body,
    )

    if result.get("success"):
        data = result.get("data", {})
        config = data.get("config", {})
        return (
            f"Pushed to {data.get('key', environment)} successfully.\n"
            f"Mode: {config.get('mode', mode)}\n"
            f"Version: {config.get('version', 'latest')}\n"
            f"Branch: {config.get('branch', branch)}"
        )
    else:
        error = result.get("error", "Unknown error")
        message = result.get("message", "")
        return f"Push failed: {error}\n{message}"


# ---------------------------------------------------------------------------
# RESOURCES — Expose skills documentation as browsable resources
# ---------------------------------------------------------------------------


@mcp.resource("symbols://skills/rules")
def get_rules() -> str:
    """Strict rules for AI agents working in Symbols/DOMQL projects (modern smbls stack: signal reactivity, design system tokens, declarative fetch, polyglot, helmet, router)."""
    return _read_skill("RULES.md")


@mcp.resource("symbols://skills/syntax")
def get_syntax() -> str:
    """Complete DOMQL syntax language reference — flat element API, signal reactivity, (el, s) prop functions, flat onX events."""
    return _read_skill("SYNTAX.md")


@mcp.resource("symbols://skills/components")
def get_components() -> str:
    """DOMQL component reference — flat props on the element, flat onX events (NEVER on: {} or props: {} wrappers)."""
    return _read_skill("COMPONENTS.md")


@mcp.resource("symbols://skills/project-structure")
def get_project_structure() -> str:
    """Symbols project folder structure and file conventions."""
    return _read_skill("PROJECT_STRUCTURE.md")


@mcp.resource("symbols://skills/design-system")
def get_design_system() -> str:
    """**AUTHORITATIVE DESIGN-SYSTEM REFERENCE** — single canonical doc covering: (1) the runtime contract — theming pipeline (resolveAndApplyTheme, prepareDesignSystem, createElement), multi-app isolation (createConfig({cleanBase:true}), pushConfig/popConfig, cssPrefix derivation, themeRoot), `changeGlobalTheme(theme, targetConfig?)`, async boundaries, project rules. (2) The token catalog — color (full grammar `<name>(.alpha)?(<+N|-N|=N>)?` where `.N` is ALPHA not shade, `+N`/`-N` are lightness modifiers, `=N` is absolute lightness %), gradient, theme (surface/priority/state), typography (ratio scale), spacing (golden-ratio), timing, animation, media (breakpoints), icons (Icon component required — `html: '<svg ...>'` for icons is BANNED), cases, vars, fonts. (3) CSS-in-props shorthands. (4) Full configuration reference. (5) Common mistakes. Includes branded-core-token caveat. Read this FIRST for any design-system, theming, or token-related work."""
    return _read_skill("DESIGN_SYSTEM.md")


@mcp.resource("symbols://skills/design")
def get_design() -> str:
    """Consolidated design discipline — three parts: (1) UI/UX direction (perceptual goals, hierarchy, motion, accessibility), (2) design-to-code translator role (visual specs → DOMQL), (3) seven design personas (brand identity, critique, trend, system architect, Figma, marketing, presentation). Use Part 1 to evaluate every UI; Part 2 when given visual input; Part 3 when explicitly asked for specialist design work."""
    return _read_skill("DESIGN.md")


@mcp.resource("symbols://skills/patterns")
def get_patterns() -> str:
    """UI patterns, accessibility and AI optimization."""
    return _read_skill("PATTERNS.md")


@mcp.resource("symbols://skills/migration")
def get_migration() -> str:
    """Migration guide for legacy projects and React/Angular/Vue → Symbols (modern smbls stack)."""
    return _read_skill("MIGRATION.md")


@mcp.resource("symbols://skills/audit")
def get_audit() -> str:
    """**EXECUTABLE PROJECT AUDIT PLAYBOOK.** Phased plan agent can run end-to-end on any Symbols project: static audit (bin/symbols-audit CLI, strict-by-default), fix loop with self-test, build/publish/STRICT UI testing via chrome-mcp (local-vs-remote side-by-side, click every clickable, icon rendering verification per Rule 62, theme/lang/active-nav/forms/responsive), triple-iterate to convergence. Logs framework bugs to audit/symbols_audit_results.md. Final output: audit/report.md. Includes severity classification, common publish-time failures table, pre-publish checklist."""
    return _read_skill("AUDIT.md")


@mcp.resource("symbols://skills/cookbook")
def get_cookbook() -> str:
    """Interactive DOMQL cookbook with runnable recipes (uses fetch:, polyglot, helmet, router from the modern smbls stack)."""
    return _read_skill("COOKBOOK.md")


@mcp.resource("symbols://skills/snippets")
def get_snippets() -> str:
    """Production-ready component snippets (headers, heroes, cards, forms, layouts)."""
    return _read_skill("SNIPPETS.md")


@mcp.resource("symbols://skills/default-project")
def get_default_project() -> str:
    """Default Symbols project template — 127+ pre-built components catalog AND the recommended pre-configured design system tokens (typography, spacing, color, theme, font_family, timing, animation, cases)."""
    return _read_skill("DEFAULT_PROJECT.md")


@mcp.resource("symbols://skills/default-components")
def get_default_components() -> str:
    """Complete source code of all 130+ default project template components (heavy — load on demand only when looking up a specific component's implementation)."""
    return _read_skill("DEFAULT_COMPONENTS.md")


@mcp.resource("symbols://skills/learnings")
def get_learnings() -> str:
    """Framework internals, technical gotchas, and deep runtime knowledge."""
    return _read_skill("LEARNINGS.md")


@mcp.resource("symbols://skills/running-apps")
def get_running_apps() -> str:
    """4 ways to run Symbols apps — local project, CDN, JSON runtime (Frank), remote server."""
    return _read_skill("RUNNING_APPS.md")


@mcp.resource("symbols://skills/cli")
def get_cli() -> str:
    """`smbls` CLI (`@symbo.ls/cli`) — full command surface, configuration, MCP/agent usage rules, error contracts. Authoritative; mirrors smbls/CLI_FOR_MCP.md."""
    return _read_skill("CLI.md")


@mcp.resource("symbols://skills/sdk")
def get_sdk() -> str:
    """`@symbo.ls/sdk` (3.14.0) — all 24 services + lifecycle, BaseService contract, TokenManager, environment matrix, rootBus, validation surface, federation primitive, permissions reference. Authoritative; mirrors sdk/SDK_FOR_MCP.md."""
    return _read_skill("SDK.md")


@mcp.resource("symbols://skills/modern-stack")
def get_modern_stack() -> str:
    """Modern smbls stack — the canonical declarative APIs for fetch (@symbo.ls/fetch), polyglot (@symbo.ls/polyglot), helmet (@symbo.ls/helmet), router (@symbo.ls/router), theme via @symbo.ls/scratch, and SSR via @symbo.ls/brender. Includes wiring, usage, and forbidden alternatives. Read this when generating any non-trivial Symbols project."""
    return _read_skill("MODERN_STACK.md")


@mcp.resource("symbols://skills/framework")
def get_framework() -> str:
    """**AUTHORITATIVE FRAMEWORK REFERENCE.** Single source of truth for project structure, plugin usage, theming, SSR, JSON↔FS compilation, publishing pipeline, three router patterns (A preferred, B/C legacy), common publish-time failures table, legacy-project migration. Mirrors smbls/FOR_MCP.md from the smbls repo. Read this FIRST for any non-trivial Symbols work; cross-reference DESIGN_SYSTEM.md for the design-system contract + token catalog."""
    return _read_skill("FRAMEWORK.md")


@mcp.resource("symbols://skills/shared-libraries")
def get_shared_libraries() -> str:
    """sharedLibraries — how shared libraries work in Symbols: configuration, runtime merge, precedence, CLI integration."""
    return _read_skill("SHARED_LIBRARIES.md")


@mcp.resource("symbols://skills/common-mistakes")
def get_common_mistakes() -> str:
    """Common mistakes reference — wrong vs correct DOMQL patterns (flat el.X, flat onX, design tokens, polyglot, fetch, helmet) with zero tolerance."""
    return _read_skill("COMMON_MISTAKES.md")


@mcp.resource("symbols://skills/frankability")
def get_frankability() -> str:
    """**FRANKABILITY CONTRACT** — patterns that survive `frank.toJSON` serialization. Lists every rule from `@symbo.ls/frank-audit` (sibling-imports, module-scope state, factory closures, flat-syntax, scope movers) with the wrong pattern and the canonical replacement. Read this before generating any component or page so the output starts frankable. Frank's bundle-time fixer recovers many violations automatically; frank-audit (`smbls frank-audit` / `--fix`) cleans the source so what you commit matches what ships."""
    return _read_skill("FRANKABILITY.md")


@mcp.resource("symbols://skills/frank-fix-workflow")
def get_frank_fix_workflow() -> str:
    """**LLM REFERENCE CARD** for the frank-audit prescription → edit-op flow. Documents the 3-tool sequence (`audit_and_fix_frankability` → `prescribe_frankability_fixes` → `apply_frankability_edit_ops`), the strict 8-kind edit-op JSON contract (`removeImport`, `moveFile`, `addToIndexFile`, `addToGlobalScope`, `removeTopLevelDecl`, `addElementScope`, `replaceTokenValue`, `skip`), the decision protocol per prescription, validation feedback codes, the verify-or-rollback safety guarantee, and a worked FA205 factory-closure example. Read this when answering frank-audit prescriptions — the orchestrator parses your reply as a single JSON object."""
    return _read_skill("FRANK_FIX_WORKFLOW.md")


@mcp.resource("symbols://reference/spacing-tokens")
def get_spacing_tokens() -> str:
    """Spacing token reference for the Symbols design system."""
    return """# Symbols Spacing Tokens

Ratio-based system (base 16px, ratio 1.618 golden ratio).

Each sub-step (A → A1 → A2 → A3 → B) is one smooth tone increase.
To increase slightly: go up one sub-step. To increase moderately: go up one letter.

Scale: ... X < X1 < X2 < Z < Z1 < Z2 < A < A1 < A2 < A3 < B < B1 < B2 < B3 < C ...

| Token | ~px  | Token | ~px  | Token | ~px  |
|-------|------|-------|------|-------|------|
| X     | 3    | A     | 16   | C     | 42   |
| X1    | 4    | A1    | 20   | C1    | 52   |
| X2    | 5    | A2    | 22   | C2    | 55   |
| Z     | 10   | A3    | 24   | D     | 67   |
| Z1    | 12   | B     | 26   | E     | 109  |
| Z2    | 14   | B1    | 32   | F     | 177  |
|       |      | B2    | 36   |       |      |
|       |      | B3    | 39   |       |      |

Usage: padding: 'A B', gap: 'C', borderRadius: 'Z', fontSize: 'B1'
Tokens work with padding, margin, gap, width, height, borderRadius, position, and any spacing property.
Negative values: margin: '-Y1 -Z2 - auto'
Math: padding: 'A+Z2'
"""


@mcp.resource("symbols://reference/atom-components")
def get_atom_components() -> str:
    """Built-in primitive atom components in Symbols."""
    return """# Symbols Atom Components (Primitives)

| Atom       | HTML Tag   | Description                   |
|------------|------------|-------------------------------|
| Text       | <span>     | Text content                  |
| Box        | <div>      | Generic container             |
| Flex       | <div>      | Flexbox container             |
| Grid       | <div>      | CSS Grid container            |
| Link       | <a>        | Anchor with built-in router   |
| Input      | <input>    | Form input                    |
| Radio      | <input>    | Radio button                  |
| Checkbox   | <input>    | Checkbox                      |
| Svg        | <svg>      | SVG container                 |
| Icon       | <svg>      | Icon from icon sprite         |
| IconText   | <div>      | Icon + text combination       |
| Button     | <button>   | Button with icon/text support |
| Img        | <img>      | Image element                 |
| Iframe     | <iframe>   | Embedded frame                |
| Video      | <video>    | Video element                 |

Usage examples:
  { Box: { padding: 'A', background: 'surface' } }
  { Flex: { flow: 'y', gap: 'B', align: 'center center' } }
  { Grid: { columns: 'repeat(3, 1fr)', gap: 'A' } }
  { Link: { text: 'Click here', href: '/dashboard' } }
  { Button: { text: 'Submit', theme: 'primary', icon: 'check' } }
  { Icon: { name: 'chevronLeft' } }
  { Img: { src: 'photo.png', boxSize: 'D D' } }
"""


@mcp.resource("symbols://reference/event-handlers")
def get_event_handlers() -> str:
    """Event handler reference for Symbols.app."""
    return """# Symbols Event Handlers (DOMQL)

All event handlers are flat top-level keys (`onClick`, `onInit`, …). NEVER use `on: {}` wrapper (FORBIDDEN). NEVER read `el.on.X` at runtime (FORBIDDEN) — read `el.onClick` flat.

## Lifecycle Events — signature: (el, state, context, options?)
  onInit:           (el, s, ctx) => {}     // Before DOM creation
  onAttachNode:     (el, s, ctx) => {}     // DOM created, not yet attached
  onCreate:         (el, s, ctx) => {}     // Full setup done (children, events, effects)
  onComplete:       (el, s, ctx) => {}     // Alias of onCreate
  onRender:         (el, s, ctx) => {}     // After initial render
  onRenderRouter:   (el, s, ctx) => {}     // Router-specific post-render
  onUpdate:         (el, s, ctx) => {}     // After el.update()
  onBeforeUpdate:   (changes, el, s, ctx) => {}   // Return false to cancel
  onStateUpdate:    (changes, el, s, ctx) => {}
  onBeforeStateUpdate: (changes, el, s, ctx) => {}// Return false to cancel
  onFrame:          (el, s, ctx) => {}     // requestAnimationFrame loop

## DOM Events — signature: (event, el, state)
  onClick:     (e, el, s) => {}
  onInput:     (e, el, s) => {}
  onChange:    (e, el, s) => {}
  onKeydown:   (e, el, s) => {}
  onKeyup:     (e, el, s) => {}
  onDblclick:  (e, el, s) => {}
  onMouseover: (e, el, s) => {}
  onMouseout:  (e, el, s) => {}
  onWheel:     (e, el, s) => {}
  onSubmit:    (e, el, s) => {}
  onBlur:      (e, el, s) => {}
  onFocus:     (e, el, s) => {}
  onScroll:    (e, el, s) => {}
  onLoad:      (e, el, s) => {}
  // any onCustomEvent — detected structurally

## Calling Functions — el.call lookup: methods → functions → utils → element prototype
  onClick: (e, el)    => el.call('saveDraft', payload)    // registered function
  onClick: (e, el, s) => el.call('findUser', s).save()    // chained
  onInit:  (el)       => { this.call('warmup') }           // inside lifecycle, this-bound

## State Updates (signal-based, batched)
  onClick: (e, el, s) => s.update({ count: s.count + 1 })
  onClick: (e, el, s) => s.toggle('isActive')
  onClick: (e, el, s) => s.rootUpdate({ modal: '/add-item' })
  onClick: (e, el, s) => s.setByPath('user.profile.name', 'Nika')

## Navigation
  onClick: (e, el)    => { e.preventDefault(); el.router('/dashboard', el.getRoot()) }

## Cleanup Pattern (return cleanup from lifecycle)
  onRender: (el, s) => {
    const interval = setInterval(() => { /* ... */ }, 1000)
    return () => clearInterval(interval)   // called on element removal
  }

## Polyglot
  onClick: (e, el) => el.call('setLang', 'ka')
  text:    '{{ hello | polyglot }}'                    // reactive (template re-evaluates on lang change)

## Theme (NEVER setAttribute('data-theme', ...) directly)
  import { changeGlobalTheme } from 'smbls'                // import path is `smbls`, NOT `@symbo.ls/scratch`
  // Wrap in a registered project function so it's import-safe across frank serialization:
  // functions/switchTheme.js → export function switchTheme () {{ changeGlobalTheme(next, this.context.designSystem) }}
  onClick: (e, el) => el.call('switchTheme')
"""


# ---------------------------------------------------------------------------
# PROMPTS — Reusable prompt templates for common tasks
# ---------------------------------------------------------------------------


@mcp.prompt()
def symbols_component_prompt(description: str, component_name: str = "MyComponent") -> str:
    """Prompt template for generating a Symbols.app DOMQL component."""
    return f"""Generate a Symbols.app DOMQL component with these requirements:

Component Name: {component_name}
Description: {description}

Follow these strict rules:
- Use DOMQL syntax ONLY — flat element API, no `props: {{}}` wrapper, no `on: {{}}` wrapper, reactive prop functions are `(el, s)` (NEVER `({{ props, state }})`).
- Components are plain objects with named exports: `export const {component_name} = {{ ... }}`
- **MANDATORY: ALL values MUST use design system tokens.** ZERO px, ZERO hex/rgb/hsl, ZERO raw ms. Sequence families (typography, spacing, timing) share the letter alphabet but each generates its own values from base × ratio — `fontSize: 'B'` ≠ `padding: 'B'` ≠ `transition: 'B'`. NO custom-named spacing tokens — only the generated sequence + sub-tokens (`A1`, `A2`, …). Name-based families: colors (`primary`, `surface`, `gray.5`, `blue.7`, `gray+20`), themes, gradients, shadows.
- **MANDATORY: All user-facing text via polyglot** — `'{{{{ key | polyglot }}}}'` template or `(el) => el.call('polyglot', 'key')`. NEVER hardcode user-facing strings.
- **MANDATORY: All data fetching via declarative `fetch:` prop** (@symbo.ls/fetch). NEVER `window.fetch` / `axios` in components.
- **MANDATORY: All metadata via `metadata: {{...}}`** (@symbo.ls/helmet). NEVER `document.title = …` or `<head>` injection.
- **MANDATORY: All navigation via `el.router(path, el.getRoot())`**. NEVER `window.location`.
- NO imports between project files — reference components by PascalCase key, call functions via `el.call('fnName', …)`.
- All folders flat — no subfolders.
- Use the default library — Button, Avatar, Icon, Field, Modal, etc. via `extends: 'Name'`.
- Include responsive breakpoints (`@tabletS`, `@mobileL`).
- Follow modern UI/UX: visual hierarchy, minimal cognitive load, confident typography.
- NO direct DOM manipulation — banned: `document.*`, `el.node.style.X = …`, `addEventListener`, `classList`, `innerHTML`, `setAttribute`, `parentNode`/`children` traversal.

Output ONLY the JavaScript code."""


@mcp.prompt()
def symbols_migration_prompt(source_framework: str = "React") -> str:
    """Prompt template for migrating code to Symbols.app DOMQL."""
    return f"""You are migrating {source_framework} code to Symbols.app DOMQL (modern smbls stack).

Key conversion rules for {source_framework}:
- Components become plain objects (never functions / classes)
- NO imports between project files (only `pages/index.js` imports page modules)
- All folders are flat — no subfolders
- Use `extends`/`childExtends` (always plural — singular forms are forbidden)
- Flat element API: props are flat on the element (no `props: {{}}` wrapper, no `el.props.X` reads)
- Events use flat `onX` (no `on: {{}}` wrapper, no `el.on.X` reads). DOM events: `(e, el, s)`. Lifecycle: `(el, s, ctx)`.
- Reactive prop functions are `(el, s)` — NEVER `({{ props, state }})` (FORBIDDEN)
- **MANDATORY: ALL values MUST use design system tokens** — ZERO px, hex, rgb, hsl, ZERO raw durations
- State: `state: {{ key: val }}` + `s.update({{ key: newVal }})`. Signal-backed reactive store.
- Effects: prefer signal-driven reactive prop functions over imperative `onRender`. For initial setup use `onInit`. For state-driven side effects use `onStateUpdate(changes, el, s, ctx)`.
- Lists: `children: (el, s) => s.items, childrenAs: 'state', childExtends: 'Item'`
- Data fetching: use the declarative `fetch:` prop (@symbo.ls/fetch). Caching, dedup, retry, refetch-on-focus are built in. NEVER reimplement them with `window.fetch`/`axios`.
- Translations: use polyglot — `'{{{{ key | polyglot }}}}'` or `el.call('polyglot', 'key')`. NEVER hardcoded English.
- SEO/metadata: `metadata: {{...}}` per page (@symbo.ls/helmet) — NEVER `document.title` writes or `<head>` injection.
- Routing: `el.router(path, el.getRoot())` — NEVER `window.location.*`.
- Theme: `changeGlobalTheme()` from @symbo.ls/scratch — NEVER `setAttribute('data-theme', …)`.
- The default library provides Button, Avatar, Field, Modal, etc. — use them via `extends: 'Name'`.

Provide the {source_framework} code to convert and I will output clean DOMQL."""


@mcp.prompt()
def symbols_project_prompt(description: str) -> str:
    """Prompt template for scaffolding a complete Symbols project."""
    return f"""Create a complete Symbols.app project (DOMQL + modern smbls stack):

Project Description: {description}

Required structure (symbols/ folder):
- index.js (entry: import create from 'smbls', import context, create(app, context))
- app.js (root app with routes: (pages) => pages, app-level metadata via @symbo.ls/helmet)
- config.js (theme defaults, router config, db adapter for @symbo.ls/fetch)
- context.js (re-exports: state, pages, designSystem, components, functions, methods, snippets, plugins, polyglot)
- state.js (app state — defaults like {{ lang: 'en', theme: 'auto' }})
- dependencies.js (external packages, plugin imports — fetchPlugin, polyglotPlugin, helmetPlugin, routerPlugin)
- components/ (PascalCase files, named exports — flat, no subfolders)
- pages/ (dash-case files, camelCase exports, route mapping in pages/index.js — only file allowed to import siblings)
- functions/ (camelCase, called via el.call() — NEVER imported into components)
- methods/ (camelCase, called via this.call() / el.call() in lifecycle methods)
- designSystem/ (color, theme, typography, spacing, font, icons, svg_data — ALWAYS lowercase keys)
- snippets/ (reusable snippets)
- cases.js (root-level — global conditional cases for `.isX` / `$isX` patterns)

The project uses the default library (default.symbo.ls) which provides Button, Avatar, Icon, Field, Modal, Badge, Progress, TabSet, and 120+ more components — reference by PascalCase key, no imports needed.

Modern stack (configure in context):
- @symbo.ls/router for SPA routing — `el.router(path, el.getRoot())` (Rule 42)
- @symbo.ls/fetch for declarative data — `db: {{ adapter: 'supabase'|'rest'|'local', ... }}` + `fetch:` prop on elements (Rule 47)
- @symbo.ls/polyglot for translations — `'{{{{ key | polyglot }}}}'` template (reactive) + `el.call('polyglot', 'key')` (imperative). NO `t` or `tr` function exists. (Rule 48)
- @symbo.ls/helmet for SEO — page-level `metadata: {{...}}` (Rule 49)
- @symbo.ls/scratch + `changeGlobalTheme()` for theme (Rule 50)

Rules:
- DOMQL syntax only — flat element API, flat onX events, reactive functions `(el, s)`. NO `props: {{}}`, NO `on: {{}}`, NO `({{ props }})`.
- Design tokens for ALL values — `padding: 'A'` not `'16px'`. NO hex, NO rgb, NO hsl. Each ratio family (typography, spacing, timing) has its own sequence: same letter resolves to different values (`fontSize: 'B'` ≠ `padding: 'B'` ≠ `transition: 'B'`). No custom-named spacing tokens.
- Components are plain objects, never functions / classes.
- No imports between project files (only `pages/index.js`).
- All folders completely flat — no subfolders.
- All user-facing text wrapped in polyglot.
- All data fetching via declarative `fetch:` prop.
- All metadata via @symbo.ls/helmet.
- All navigation via `el.router()`.
- NO direct DOM manipulation (banned: `document.*`, `addEventListener`, `classList`, `innerHTML`, `setAttribute`, etc.).

Generate all files with complete, production-ready code."""


@mcp.prompt()
def symbols_review_prompt() -> str:
    """Prompt template for reviewing Symbols/DOMQL code."""
    return """Review this Symbols/DOMQL code for compliance and best practices.

Check for these violations:
1. Forbidden syntax leftovers: `extend` → `extends`, `childExtend` → `childExtends`, `props: {}` wrapper, `on: {}` wrapper, `el.props.X` reads, `el.on.X` reads, reactive prop signature `({ props, state })` instead of `(el, s)`
2. Imports between project files (FORBIDDEN — only `pages/index.js` may import sibling pages)
3. Function-based / class-based components (must be plain objects)
4. Subfolders inside components/, pages/, functions/, methods/, designSystem/, snippets/
5. Hardcoded values: pixels, hex/rgb/hsl colors, raw durations (must be design system tokens)
6. Wrong event signatures — DOM events: `(e, el, s)`, lifecycle: `(el, s, ctx)`, before/state-update: `(changes, el, s, ctx)`
7. Default exports for components (must be named: `export const X = {...}`)
8. Standard HTML attrs wrapped in `attr: {}` (must be flat at root; `attr: {}` only for non-standard / custom attrs)
9. Hardcoded user-facing strings (must use polyglot — `'{{ key | polyglot }}'` or `el.call('polyglot', 'key')`)
10. Raw `window.fetch` / `axios` in components (must use declarative `fetch:` prop via @symbo.ls/fetch)
11. `document.title = …` / `<head>` injection (must use @symbo.ls/helmet `metadata: {...}`)
12. `window.location.*` for navigation (must use `el.router(path, el.getRoot())`)
13. `setAttribute('data-theme', ...)` / `matchMedia('(prefers-color-scheme: dark)')` (must use `changeGlobalTheme()` from @symbo.ls/scratch)
14. Direct DOM manipulation: `document.querySelector`, `getElementById`, `addEventListener`, `classList.toggle`, `innerHTML`, `appendChild`, `parentNode`/`children` traversal, `style.X = …`
15. Module-level helper variables / functions outside the export (lost during platform serialization — move to functions/ + el.call)
16. Inline `<svg>` markup in components (must use Icon component + designSystem/icons)
17. `extends: 'Flex'` / `extends: 'Box'` / `extends: 'Text'` (replace with `flow:`/`align:`)
18. Pages extending `'Flex'` instead of `'Page'`
19. Chained CSS selectors `'@dark :hover'` (must nest separately)
20. UPPERCASE design system keys (`COLOR`, `THEME`) (must be lowercase)

Provide:
- Issues found with line references and rule numbers (RULES.md Rule N)
- Corrected code for each issue
- Overall compliance score (1-10)
- Improvement suggestions

Paste your code below:"""


@mcp.prompt()
def symbols_convert_html_prompt() -> str:
    """Prompt template for converting HTML to Symbols.app DOMQL components."""
    return """Convert the provided HTML/CSS to Symbols.app DOMQL components.

Conversion rules:
- `<div>` with flex → drop wrapper, add `flow: 'x'`/`flow: 'y'` (NEVER `extends: 'Flex'`); `<div>` with grid → `display: 'grid'`. Plain wrappers don't need any extends.
- `<span>` / `<p>` / `<h1>`-`<h6>` → keep semantic via `tag` (P, H1–H6 exist).
- `<a>` → `extends: 'Link'`, `href` flat at root (NEVER `attr: { href }`).
- `<button>` → `extends: 'Button'` (supports `icon`/`text`).
- `<input>` → `Input` / `Radio` / `Checkbox` based on type. Standard HTML attrs (placeholder, type, value, disabled, required) flat at root, NOT in `attr: {}`.
- `<img>` → `Img`.
- `<form>` → `Form` (or `tag: 'form'`).
- `<ul>` / `<ol>` + `<li>` → `children` array + `childExtends: 'ItemName'`.
- CSS px → design-system sequence tokens. **Each family (typography, spacing, timing) generates its own values from `{ base, ratio }`** — same letter resolves to different values across families. Default spacing scale (`base:16, ratio:1.618`): `A`≈16px, `B`≈26px, `C`≈42px. Default typography (`base:16, ratio:1.25`): `A`≈16px, `B`≈20px, `C`≈25px. Sub-tokens (`A1`, `A2`, etc.) for in-between within each family. Pick the sequence that matches the prop, NOT a custom-named token.
- CSS colors → theme tokens (`primary`, `surface`, `gray.5`, `blue+20`). NEVER hex / rgb / hsl.
- Durations → timing-sequence tokens (`transition: 'B'` ≈ 200ms, NOT raw `200ms`).
- Media queries → `@tabletS`, `@mobileL`, `@dark`, `@light` (NEVER chain selectors).
- CSS classes → flatten as component properties (no className prop).
- id/class attrs → not needed (PascalCase keys + cases.js handle it).
- Hardcoded user-facing text → polyglot template `'{{ key | polyglot }}'`.
- Raw event handlers (`onclick="..."`, `addEventListener`) → flat `onClick`/`onInput` props on the element.
- `<head>` `<title>` / `<meta>` → page-level `metadata: {...}` via @symbo.ls/helmet.
- Hardcoded data fetches / `<script>` tags doing API calls → declarative `fetch:` prop via @symbo.ls/fetch.
- `<svg>` icons → `Icon` component + `designSystem/icons` (NEVER inline SVG, NEVER `tag: 'svg'`).

Output clean DOMQL with named exports — flat element API, no `props: {}` / `on: {}` / `({ props })`. Named exports only.

Paste the HTML below:"""


@mcp.prompt()
def symbols_design_review_prompt() -> str:
    """Prompt template for visual/design audit against the design system."""
    return """Review this Symbols component for design system compliance.

Check:
1. Spacing/typography/timing use the **right sequence per family** — `padding`/`margin`/`gap`/`width` etc. from spacing scale; `fontSize`/`lineHeight` from typography scale; `transition` duration from timing scale. Same letter (e.g. `'B'`) resolves to different values per family — that's expected. NO raw px / ms / hex / rgb / hsl. NO custom-named spacing tokens (only the generated sequence + sub-tokens).
2. Colors come from theme, not hardcoded hex/rgb
3. Typography uses design system scale (fontSize tokens)
4. Responsive breakpoints present (@tabletS, @mobileL)
5. Visual hierarchy is clear (heading sizes, spacing rhythm)
6. Interactive elements have hover/focus/active states
7. Accessibility: focus-visible, ARIA attributes where needed
8. Consistent use of theme variants (primary, secondary, card, dialog)
9. Layout uses Flex/Grid with proper alignment tokens

Provide design improvement suggestions with corrected code.

Paste your component code below:"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """Run the Symbols MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8080"))

    if transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
