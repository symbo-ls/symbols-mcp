"""
Symbols MCP — Documentation search, code generation, conversion and audit tools for Symbols.app.
"""

import os
import json
import logging
import re
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

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
        "Reference assistant for the Symbols.app design-system framework. "
        "Searches Symbols documentation, exposes framework rules, and provides "
        "comprehensive syntax and API reference. Includes tools for generating "
        "components, converting code from React/HTML, auditing DOMQL v3 compliance, "
        "publishing/deploying projects to the Symbols platform, and complete "
        "CLI (@symbo.ls/cli) and SDK (@symbo.ls/sdk) documentation."
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

_V2_PATTERNS = [
    (r"\bextend\s*:", "v2 syntax: use 'extends' (plural) instead of 'extend'"),
    (r"\bchildExtend\s*:", "v2 syntax: use 'childExtends' (plural) instead of 'childExtend'"),
    (r"\bon\s*:\s*\{", "v2 syntax: flatten event handlers with onX prefix (e.g. onClick) instead of on: {} wrapper"),
    (r"\bprops\s*:\s*\{(?!\s*\})", "v2 syntax: flatten props directly on the component instead of props: {} wrapper"),
]

_RULE_CHECKS = [
    (r"\bimport\s+.*\bfrom\s+['\"]\.\/", "FORBIDDEN: No imports between project files — reference components by PascalCase key name"),
    (r"\bexport\s+default\s+\{", "Components should use named exports (export const Name = {}), not default exports"),
    (r"\bfunction\s+\w+\s*\(.*\)\s*\{[\s\S]*?return\s*\{", "Components must be plain objects, not functions that return objects"),
    (r"\bextends\s*:\s*(?!['\"])\w+", "FORBIDDEN: extends must be a quoted string name (extends: 'Name'), not a variable reference — register in components/ and use string lookup (Rule 10)"),
    (r"extends\s*:\s*['\"]Flex['\"]", "Replace extends: 'Flex' with flow: 'x' or flow: 'y' — do NOT just remove it, the element needs flow to stay flex (Rule 26)"),
    (r"extends\s*:\s*['\"]Box['\"]", "Remove extends: 'Box' — every element is already a Box (Rule 26)"),
    (r"extends\s*:\s*['\"]Text['\"]", "Remove extends: 'Text' — any element with text: is already Text (Rule 26)"),
    (r"\bchildExtends\s*:\s*\{", "FORBIDDEN: childExtends must be a quoted string name, not an inline object — register as a named component (Rule 10)"),
    (r"(?:padding|margin|gap|width|height|fontSize|borderRadius|minWidth|maxWidth|minHeight|maxHeight|top|left|right|bottom|letterSpacing|lineHeight|borderWidth|outlineWidth)\s*:\s*['\"]?\d+(?:\.\d+)?px", "FORBIDDEN: No raw px values — use design system tokens (A, B, C, etc.) instead of hardcoded pixels (Rule 28)"),
    (r"(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['\"]#[0-9a-fA-F]", "Use design system color tokens (primary, secondary, white, gray.5) instead of hardcoded hex colors (Rule 27)"),
    (r"(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['\"]rgb", "Use design system color tokens instead of hardcoded rgb/rgba values (Rule 27)"),
    (r"(?:color|background|backgroundColor|borderColor|fill|stroke)\s*:\s*['\"]hsl", "Use design system color tokens instead of hardcoded hsl/hsla values (Rule 27)"),
    (r"<svg[\s>]", "FORBIDDEN: Use the Icon component for SVG icons — store SVGs in designSystem/icons, never inline (Rule 29)"),
    (r"tag\s*:\s*['\"]svg['\"]", "FORBIDDEN: Never use tag: 'svg' — store SVGs in designSystem/icons and use Icon component (Rule 29)"),
    (r"tag\s*:\s*['\"]path['\"]", "FORBIDDEN: Never use tag: 'path' — store SVG paths in designSystem/icons and use Icon component (Rule 29)"),
    (r"extends\s*:\s*['\"]Svg['\"]", "Use Icon component for icons, not Svg — Svg is only for decorative/structural SVGs (Rule 29)"),
    (r"\biconName\s*:", "FORBIDDEN: Use icon: not iconName: — the prop is icon: 'name' matching a key in designSystem/icons (Rule 29)"),
    (r"document\.createElement\b", "FORBIDDEN: No direct DOM manipulation — use DOMQL declarative object syntax instead (Rule 30)"),
    (r"\.querySelector\b", "FORBIDDEN: No DOM queries — reference elements by key name in the DOMQL object tree (Rule 30)"),
    (r"\.appendChild\b", "FORBIDDEN: No direct DOM manipulation — nest children as object keys or use children array (Rule 30)"),
    (r"\.removeChild\b", "FORBIDDEN: No direct DOM manipulation — use if: (el, s) => condition to show/hide (Rule 30)"),
    (r"\.insertBefore\b", "FORBIDDEN: No direct DOM manipulation — use children array ordering (Rule 30)"),
    (r"\.innerHTML\s*=", "FORBIDDEN: No direct DOM manipulation — use text: or html: prop (Rule 30)"),
    (r"\.classList\.", "FORBIDDEN: No direct class manipulation — use isX + '.isX' pattern (Rule 19/30)"),
    (r"\.setAttribute\b", "FORBIDDEN: No direct DOM manipulation — set attributes at root level in DOMQL (Rule 30)"),
    (r"\.addEventListener\b", "FORBIDDEN: No direct event binding — use onX props: onClick, onInput, etc. (Rule 30)"),
    (r"\.style\.\w+\s*=", "FORBIDDEN: No direct style manipulation — use DOMQL CSS-in-props (Rule 30)"),
    (r"html\s*:\s*\(?.*\)?\s*=>\s*", "FORBIDDEN: Never use html: as a function returning markup — use DOMQL children, nesting, text:, and if: instead (Rule 31)"),
    (r"return\s*`<\w+", "FORBIDDEN: Never return HTML template literals — use DOMQL declarative children and nesting (Rule 31)"),
    (r"style\s*=\s*['\"`]", "FORBIDDEN: No inline style= strings in html — use DOMQL CSS-in-props (Rule 31)"),
    (r"window\.innerWidth", "FORBIDDEN: No window.innerWidth checks — use @mobileL, @tabletS responsive breakpoints (Rule 31)"),
    (r"\.parentNode\b", "FORBIDDEN: No DOM traversal — use state and reactive props instead of walking the DOM tree (Rule 32)"),
    (r"\.childNodes\b", "FORBIDDEN: No DOM traversal — use state-driven children with if: props (Rule 32)"),
    (r"\.textContent\b", "FORBIDDEN: No DOM property access — use state and text: prop (Rule 32)"),
    (r"Array\.from\(\w+\.children\)", "FORBIDDEN: No DOM child iteration — use state arrays with children/childExtends and if: filtering (Rule 32)"),
    (r"\.style\.display\s*=", "FORBIDDEN: No style.display toggling — use show:/hide: to toggle visibility or if: to remove from DOM (Rule 32)"),
    (r"\.style\.cssText\s*=", "FORBIDDEN: No direct cssText — use DOMQL CSS-in-props (Rule 32)"),
    (r"\.dataset\.", "FORBIDDEN: No dataset manipulation — use state and attr: for data-* attributes (Rule 32)"),
    (r"\.remove\(\)", "FORBIDDEN: No DOM node removal — use if: (el, s) => condition to conditionally render (Rule 32)"),
    (r"el\.node\.\w+\s*=", "FORBIDDEN: No direct el.node property assignment — use DOMQL props (placeholder:, value:, text:, etc.). Reading el.node is fine (Rule 39), writing is not (Rule 32)"),
    (r"document\.getElementById\b", "FORBIDDEN: No document.getElementById — use el.lookdown('key') to find DOMQL elements (Rule 40)"),
    (r"document\.querySelectorAll\b", "FORBIDDEN: No document.querySelectorAll — use el.lookdownAll('key') to find DOMQL elements (Rule 40)"),
    (r"el\.parent\.state\b", "FORBIDDEN: Never use el.parent.state — with childrenAs: 'state', use s.field directly (Rule 36)"),
    (r"el\.context\.designSystem\b", "FORBIDDEN: Never read designSystem from el.context in props — use token strings directly (Rule 38)"),
    (r"^const\s+\w+\s*=\s*(?:\(|function)", "FORBIDDEN: No module-level helper functions — move to functions/ and call via el.call('fnName') (Rule 33)"),
    (r"^let\s+\w+\s*=", "FORBIDDEN: No module-level variables — use el.scope for local state, functions/ for helpers (Rule 33)"),
    (r"^var\s+\w+\s*=", "FORBIDDEN: No module-level variables — use el.scope for local state, functions/ for helpers (Rule 33)"),
    (r"window\.location\.href\s*=", "FORBIDDEN: No window.location for navigation — use el.router(path, el.getRoot()) (Rule 42)"),
    (r"window\.location\.assign\b", "FORBIDDEN: No window.location for navigation — use el.router(path, el.getRoot()) (Rule 42)"),
    (r"window\.location\.replace\b", "FORBIDDEN: No window.location for navigation — use el.router(path, el.getRoot()) (Rule 42)"),
    (r"attr\s*:\s*\{\s*href\s*:", "FORBIDDEN: Never put href in attr — use extends: 'Link' with href as a direct prop (Rule 41)"),
    (r"\b(?:COLOR|THEME|TYPOGRAPHY|SPACING|TIMING|FONT_FAMILY|ICONS|SHADOW|MEDIA|GRID|ANIMATION|RESET|GRADIENT)\s*[=:{]", "FORBIDDEN: UPPERCASE design system keys are banned — use lowercase (color, theme, typography, spacing, etc.) (Rule 0)"),
]


# ---------------------------------------------------------------------------
# JS source → JSON conversion helpers (mirrors @symbo.ls/frank pipeline)
# ---------------------------------------------------------------------------

# Data sections that the platform stores
_DATA_KEYS = ("components", "pages", "snippets", "functions", "methods",
              "designSystem", "state", "dependencies", "files", "config")

# Sections that get auto-generated schema entries
_CODE_SECTIONS = {"components", "pages", "functions", "methods", "snippets"}


def _parse_js_to_json(source_code: str) -> dict:
    """Parse DOMQL v3 JavaScript source into platform JSON format.

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
    """Run deterministic v3 compliance checks on component code."""
    violations = []
    warnings = []

    for pattern, message in _V2_PATTERNS:
        matches = list(re.finditer(pattern, code))
        for m in matches:
            line_num = code[:m.start()].count("\n") + 1
            violations.append({"line": line_num, "severity": "error", "message": message})

    for pattern, message in _RULE_CHECKS:
        matches = list(re.finditer(pattern, code))
        for m in matches:
            line_num = code[:m.start()].count("\n") + 1
            level = "error" if "FORBIDDEN" in message else "warning"
            target = violations if level == "error" else warnings
            target.append({"line": line_num, "severity": level, "message": message})

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

    Returns the mandatory Symbols.app rules that MUST be followed.
    Violations cause silent failures — black page, nothing renders.

    Call this before: generate_component, generate_page, convert_react,
    convert_html, or any code generation task.
    """
    rules = _load_agent_instructions()
    default_styles = _read_skill("DEFAULT_STYLES.md")
    return f"{rules}\n\n{default_styles}"


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
    """Generate a Symbols.app DOMQL v3 component from a description.

    Returns the rules, syntax reference, component catalog, cookbook examples,
    and default library reference as context. The calling LLM uses this context
    to generate a correct component.

    Args:
        description: What the component should do and look like.
        component_name: PascalCase name for the component.
    """
    context = _read_skills("RULES.md", "COMMON_MISTAKES.md", "COMPONENTS.md", "SYNTAX.md", "COOKBOOK.md", "DEFAULT_LIBRARY.md", "DEFAULT_STYLES.md")
    return f"""# Generate Component: {component_name}

## Description
{description}

## Requirements
- Named export: `export const {component_name} = {{ ... }}`
- DOMQL v3 syntax only (extends, childExtends, flattened props, onX events)
- **MANDATORY: ALL values MUST use design system tokens** — spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl.
- NO imports between files — PascalCase keys auto-extend registered components
- Include responsive breakpoints where appropriate (@tabletS, @mobileL)
- Use the default library components (Button, Avatar, Icon, Field, etc.) via extends
- Use Icon component for SVGs — store icons in designSystem/icons
- NO direct DOM manipulation — all structure via DOMQL declarative syntax
- Follow modern UI/UX: visual hierarchy, confident typography, minimal cognitive load

## Context — Rules, Syntax & Examples

{context}"""


@mcp.tool()
def generate_page(
    description: str,
    page_name: str = "home",
) -> str:
    """Generate a Symbols.app page with routing integration.

    Returns rules, project structure, patterns, snippets, and default library
    reference as context for page generation.

    Args:
        description: What the page should contain and do.
        page_name: camelCase name for the page (used in route map).
    """
    context = _read_skills(
        "RULES.md", "COMMON_MISTAKES.md", "PROJECT_STRUCTURE.md", "SHARED_LIBRARIES.md",
        "PATTERNS.md", "SNIPPETS.md", "DEFAULT_LIBRARY.md", "COMPONENTS.md", "DEFAULT_STYLES.md",
    )
    return f"""# Generate Page: {page_name}

## Description
{description}

## Requirements
- Export as: `export const {page_name} = {{ ... }}`
- Page is a plain object composing components
- Add to pages/index.js route map: `'/{page_name}': {page_name}`
- Use components by PascalCase key (Header, Footer, Hero, etc.)
- **MANDATORY: ALL values MUST use design system tokens** — spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl.
- Use Icon component for SVGs — store icons in designSystem/icons
- NO direct DOM manipulation — all structure via DOMQL declarative syntax
- Include responsive layout adjustments

## Context — Rules, Structure, Patterns & Snippets

{context}"""


@mcp.tool()
def convert_react(source_code: str) -> str:
    """Convert React/JSX code to Symbols.app DOMQL v3.

    Provide React component code and receive the conversion context including
    migration rules, syntax reference, and examples.

    Args:
        source_code: The React/JSX source code to convert.
    """
    context = _read_skills("RULES.md", "MIGRATION.md", "SYNTAX.md", "COMPONENTS.md", "LEARNINGS.md", "DEFAULT_STYLES.md")
    return f"""# Convert React → Symbols DOMQL v3

## Source Code to Convert
```jsx
{source_code}
```

## Conversion Rules
- Function/class components → plain object exports
- JSX → nested object children (PascalCase keys auto-extend)
- import/export between files → REMOVE (reference by key name)
- useState → state: {{ key: val }} + s.update({{ key: newVal }})
- useEffect → onRender (mount), onStateUpdate (deps)
- props → flattened directly on component (no props wrapper)
- onClick={{handler}} → onClick: (event, el, state) => {{}}
- className → use design tokens and theme directly
- map() → children: (el, s) => s.items, childExtends, childProps
- conditional rendering → if: (el, s) => boolean
- CSS modules/styled → CSS-in-props with design tokens
- React.Fragment → not needed, just nest children
- **MANDATORY: ALL values MUST use design system tokens** — ZERO px values, ZERO hex colors, ZERO rgb/hsl
- Use Icon component for SVGs — never inline SVG markup
- NO direct DOM manipulation — all structure via DOMQL declarative syntax

## Context — Migration Guide, Syntax & Rules

{context}"""


@mcp.tool()
def convert_html(source_code: str) -> str:
    """Convert raw HTML/CSS to Symbols.app DOMQL v3 components.

    Provide HTML code and receive the conversion context including component
    catalog, syntax reference, and design system tokens.

    Args:
        source_code: The HTML/CSS source code to convert.
    """
    context = _read_skills("RULES.md", "SYNTAX.md", "COMPONENTS.md", "DESIGN_SYSTEM.md", "SNIPPETS.md", "LEARNINGS.md", "DEFAULT_STYLES.md")
    return f"""# Convert HTML → Symbols DOMQL v3

## Source Code to Convert
```html
{source_code}
```

## Conversion Rules
- <div> → Box, Flex, or Grid (based on layout purpose)
- <span>, <p>, <h1>-<h6> → Text, P, H with tag property
- <a> → Link (has built-in SPA router)
- <button> → Button (has icon/text support)
- <input> → Input, Radio, Checkbox (based on type)
- <img> → Img
- <form> → Form (extends Box with tag: 'form')
- <ul>/<ol> + <li> → children array with childExtends
- CSS classes → flatten as CSS-in-props on the component
- CSS px values → design tokens (16px → 'A', 26px → 'B', 42px → 'C')
- CSS colors → theme color tokens
- media queries → @tabletS, @mobileL, @screenS breakpoints
- id/class attributes → not needed (use key names and themes)
- inline styles → flatten as component properties
- <style> blocks → distribute to component-level properties
- **MANDATORY: ALL values MUST use design system tokens** — ZERO px values, ZERO hex colors, ZERO rgb/hsl
- <svg> icons → Icon component + designSystem/icons — never inline SVG
- NO direct DOM manipulation — all structure via DOMQL declarative syntax

## Context — Syntax, Components & Design System

{context}"""


@mcp.tool()
def audit_component(component_code: str) -> str:
    """Audit a Symbols/DOMQL component for v3 compliance and best practices.

    Runs deterministic checks against v3 rules and returns a structured report
    with violations, warnings, and a compliance score.

    Args:
        component_code: The JavaScript component code to audit.
    """
    result = _audit_code(component_code)
    rules_context = _read_skill("AUDIT.md")

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

    output += f"""
## Detailed Rules Reference

{rules_context}"""

    return output


@mcp.tool()
def get_cli_reference() -> str:
    """Returns the complete Symbols CLI (@symbo.ls/cli) command reference.

    Covers all smbls commands: project setup (init, create, install, eject),
    development (start, build, brender, deploy), sync (fetch, sync, push, publish),
    collaboration (login, collab), project management, file management,
    AI assistant (ask), and utilities (convert, migrate, validate, sdk).
    """
    return _read_skill("CLI.md")


@mcp.tool()
def get_sdk_reference() -> str:
    """Returns the complete Symbols SDK (@symbo.ls/sdk) API reference.

    Covers all SDK services: AuthService, ProjectService, BranchService,
    PullRequestService, CollabService, FileService, DnsService,
    IntegrationService, FeatureFlagService, MetricsService,
    ScreenshotService, TrackingService, AdminService, KvService,
    OrganizationService, PaymentService, PlanService, SubscriptionService,
    and WaitlistService — with method signatures and usage examples.
    """
    return _read_skill("SDK.md")


@mcp.tool()
def convert_to_json(
    source_code: str,
    section: str = "components",
) -> str:
    """Convert DOMQL v3 JavaScript source code to platform JSON format.

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
    """Detect what type of Symbols environment the user is working in.

    Determines whether it's a local project, CDN, JSON runtime, or remote server
    based on project indicators, and returns the appropriate setup guide and code format.

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
    """Strict rules for AI agents working in Symbols/DOMQL v3 projects."""
    return _read_skill("RULES.md")


@mcp.resource("symbols://skills/syntax")
def get_syntax() -> str:
    """Complete DOMQL v3 syntax language reference."""
    return _read_skill("SYNTAX.md")


@mcp.resource("symbols://skills/components")
def get_components() -> str:
    """DOMQL v3 component reference with flattened props and onX events."""
    return _read_skill("COMPONENTS.md")


@mcp.resource("symbols://skills/project-structure")
def get_project_structure() -> str:
    """Symbols project folder structure and file conventions."""
    return _read_skill("PROJECT_STRUCTURE.md")


@mcp.resource("symbols://skills/design-system")
def get_design_system() -> str:
    """Design system tokens, themes and configuration."""
    return _read_skill("DESIGN_SYSTEM.md")


@mcp.resource("symbols://skills/design-direction")
def get_design_direction() -> str:
    """Modern UI/UX design direction for generating Symbols interfaces."""
    return _read_skill("DESIGN_DIRECTION.md")


@mcp.resource("symbols://skills/patterns")
def get_patterns() -> str:
    """UI patterns, accessibility and AI optimization."""
    return _read_skill("PATTERNS.md")


@mcp.resource("symbols://skills/migration")
def get_migration() -> str:
    """Migration guide for v2→v3 and React/Angular/Vue→Symbols."""
    return _read_skill("MIGRATION.md")


@mcp.resource("symbols://skills/audit")
def get_audit() -> str:
    """Full audit, enforcement and feedback framework."""
    return _read_skill("AUDIT.md")


@mcp.resource("symbols://skills/design-to-code")
def get_design_to_code() -> str:
    """Design-to-code translation guide."""
    return _read_skill("DESIGN_TO_CODE.md")


@mcp.resource("symbols://skills/seo-metadata")
def get_seo_metadata() -> str:
    """SEO metadata configuration reference."""
    return _read_skill("SEO-METADATA.md")


@mcp.resource("symbols://skills/ssr-brender")
def get_ssr_brender() -> str:
    """Server-side rendering with brender — SSR/SSG for Symbols apps."""
    return _read_skill("SSR-BRENDER.md")


@mcp.resource("symbols://skills/default-styles")
def get_default_styles() -> str:
    """Default template design system values — typography, spacing, colors, themes, fonts, animations."""
    return _read_skill("DEFAULT_STYLES.md")


@mcp.resource("symbols://skills/cookbook")
def get_cookbook() -> str:
    """Interactive DOMQL v3 cookbook with 30+ runnable recipes."""
    return _read_skill("COOKBOOK.md")


@mcp.resource("symbols://skills/snippets")
def get_snippets() -> str:
    """Production-ready component snippets (headers, heroes, cards, forms, layouts)."""
    return _read_skill("SNIPPETS.md")


@mcp.resource("symbols://skills/default-library")
def get_default_library() -> str:
    """Default library — 127+ pre-built components available in all Symbols projects."""
    return _read_skill("DEFAULT_LIBRARY.md")


@mcp.resource("symbols://skills/default-components")
def get_default_components() -> str:
    """Complete source code of all 130+ default project template components."""
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
    """Symbols CLI (@symbo.ls/cli) — complete command reference for the smbls CLI tool."""
    return _read_skill("CLI.md")


@mcp.resource("symbols://skills/sdk")
def get_sdk() -> str:
    """Symbols SDK (@symbo.ls/sdk) — complete API reference for all SDK services and methods."""
    return _read_skill("SDK.md")


@mcp.resource("symbols://skills/shared-libraries")
def get_shared_libraries() -> str:
    """sharedLibraries — how shared libraries work in Symbols: configuration, runtime merge, precedence, CLI integration."""
    return _read_skill("SHARED_LIBRARIES.md")


@mcp.resource("symbols://skills/common-mistakes")
def get_common_mistakes() -> str:
    """Common mistakes reference — 16 wrong vs correct DOMQL v3 patterns with zero tolerance."""
    return _read_skill("COMMON_MISTAKES.md")


@mcp.resource("symbols://skills/design-personas")
def get_design_personas() -> str:
    """7 design persona prompt templates — Brand Identity, Design Critique, Design Trend, Design System Architect, Figma Matching, Marketing Assets, Presentation."""
    return _read_skill("DESIGN_PERSONAS.md")


@mcp.resource("symbols://reference/spacing-tokens")
def get_spacing_tokens() -> str:
    """Spacing token reference for the Symbols design system."""
    return """# Symbols Spacing Tokens

Ratio-based system (base 16px, ratio 1.618 golden ratio):

| Token | ~px  | Token | ~px  | Token | ~px  |
|-------|------|-------|------|-------|------|
| X     | 3    | A     | 16   | D     | 67   |
| Y     | 6    | A1    | 20   | E     | 109  |
| Z     | 10   | A2    | 22   | F     | 177  |
| Z1    | 12   | B     | 26   |       |      |
| Z2    | 14   | B1    | 32   |       |      |
|       |      | B2    | 36   |       |      |
|       |      | C     | 42   |       |      |
|       |      | C1    | 52   |       |      |
|       |      | C2    | 55   |       |      |

Usage: padding: 'A B', gap: 'C', borderRadius: 'Z', fontSize: 'B1'
Tokens work with padding, margin, gap, width, height, borderRadius, position, and any spacing property.
Negative values: margin: '-Y1 -Z2 - auto'
Math: padding: 'A+V2'
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
    return """# Symbols Event Handlers (v3)

## Lifecycle Events
  onInit: (el, state) => {}              // Once on creation
  onRender: (el, state) => {}            // On each render (return fn for cleanup)
  onUpdate: (el, state) => {}            // On props/state change
  onStateUpdate: (changes, el, state, context) => {}

## DOM Events
  onClick: (event, el, state) => {}
  onInput: (event, el, state) => {}
  onKeydown: (event, el, state) => {}
  onDblclick: (event, el, state) => {}
  onMouseover: (event, el, state) => {}
  onWheel: (event, el, state) => {}
  onSubmit: (event, el, state) => {}
  onLoad: (event, el, state) => {}

## Calling Functions
  onClick: (e, el) => el.call('functionName', args)  // Global function
  onClick: (e, el) => el.scope.localFn(el, s)        // Scope function
  onClick: (e, el) => el.methodName()                  // Element method

## State Updates
  onClick: (e, el, s) => s.update({ count: s.count + 1 })
  onClick: (e, el, s) => s.toggle('isActive')
  onClick: (e, el, s) => s.root.update({ modal: '/add-item' })

## Navigation
  onClick: (e, el) => el.router('/dashboard', el.getRoot())

## Cleanup Pattern
  onRender: (el, s) => {
    const interval = setInterval(() => { /* ... */ }, 1000)
    return () => clearInterval(interval)  // Called on element removal
  }
"""


# ---------------------------------------------------------------------------
# PROMPTS — Reusable prompt templates for common tasks
# ---------------------------------------------------------------------------


@mcp.prompt()
def symbols_component_prompt(description: str, component_name: str = "MyComponent") -> str:
    """Prompt template for generating a Symbols.app component."""
    return f"""Generate a Symbols.app component with these requirements:

Component Name: {component_name}
Description: {description}

Follow these strict rules:
- Use DOMQL v3 syntax ONLY (extends, childExtends, flattened props, onX events)
- Components are plain objects with named exports: export const {component_name} = {{ ... }}
- **MANDATORY: ALL values MUST use design system tokens** — spacing (A, B, C, D), colors (primary, surface, white, gray.5), typography (fontSize: 'B'). ZERO px values, ZERO hex colors, ZERO rgb/hsl
- NO imports between files — reference components by PascalCase key name
- All folders flat — no subfolders
- The project likely has a default library — use Button, Avatar, Icon, Field, etc. via extends
- Include responsive breakpoints (@tabletS, @mobileL) where appropriate
- Follow modern UI/UX: visual hierarchy, minimal cognitive load, confident typography

Output ONLY the JavaScript code."""


@mcp.prompt()
def symbols_migration_prompt(source_framework: str = "React") -> str:
    """Prompt template for migrating code to Symbols.app."""
    return f"""You are migrating {source_framework} code to Symbols.app.

Key conversion rules for {source_framework}:
- Components become plain objects (never functions)
- NO imports between project files
- All folders are flat — no subfolders
- Use extends/childExtends (v3 plural, never v2 singular)
- Flatten all props directly (no props: {{}} wrapper)
- Events use onX prefix (no on: {{}} wrapper)
- **MANDATORY: ALL values MUST use design system tokens** — ZERO px values, ZERO hex colors, ZERO rgb/hsl
- State: state: {{ key: val }} + s.update({{ key: newVal }})
- Effects: onRender for mount, onStateUpdate for dependency changes
- Lists: children: (el, s) => s.items, childrenAs: 'state', childExtends: 'Item'
- The default library provides Button, Avatar, Field, Modal, etc. — use them via extends

Provide the {source_framework} code to convert and I will output clean DOMQL v3."""


@mcp.prompt()
def symbols_project_prompt(description: str) -> str:
    """Prompt template for scaffolding a complete Symbols project."""
    return f"""Create a complete Symbols.app project:

Project Description: {description}

Required structure (symbols/ folder):
- index.js (entry: import create from 'smbls', import context, create(app, context))
- app.js (root app with routes: (pages) => pages)
- config.js ({{ globalTheme: 'dark' }})
- context.js (re-exports: state, pages, designSystem, components, functions, snippets)
- state.js (app state)
- dependencies.js (external packages)
- components/ (PascalCase files, named exports)
- pages/ (dash-case files, camelCase exports, route mapping in index.js)
- functions/ (camelCase, called via el.call())
- designSystem/ (color, theme, typography, spacing, font, icons — ALWAYS lowercase)
- snippets/ (reusable snippets)

The project uses the default library (default.symbo.ls) which provides:
Button, Avatar, Icon, Field, Modal, Badge, Progress, TabSet, and 120+ more components.
Reference these by PascalCase key name — no imports needed.

Rules:
- v3 syntax only — extends, childExtends, flattened props, onX events
- Design tokens for all spacing/colors (padding: 'A', not padding: '16px')
- Components are plain objects, never functions
- No imports between project files
- All folders completely flat

Generate all files with complete, production-ready code."""


@mcp.prompt()
def symbols_review_prompt() -> str:
    """Prompt template for reviewing Symbols/DOMQL code."""
    return """Review this Symbols/DOMQL code for v3 compliance and best practices.

Check for these violations:
1. v2 syntax: extend→extends, childExtend→childExtends, props:{}, on:{}
2. Imports between project files (FORBIDDEN)
3. Function-based components (must be plain objects)
4. Subfolders (must be flat)
5. Hardcoded pixels instead of design tokens
6. Wrong event handler signatures (lifecycle: (el, s), DOM: (event, el, s))
7. Default exports for components (should be named)
8. Standard HTML attrs in attr: {} (should be at root; attr: {} only for data-*/aria-*/custom)
9. props block CSS trying to override component-level CSS (can't)

Provide:
- Issues found with line references
- Corrected code for each issue
- Overall v3 compliance score (1-10)
- Improvement suggestions

Paste your code below:"""


@mcp.prompt()
def symbols_convert_html_prompt() -> str:
    """Prompt template for converting HTML to Symbols.app components."""
    return """Convert the provided HTML/CSS to Symbols.app DOMQL v3 components.

Conversion rules:
- <div> → Box, Flex, or Grid (based on layout)
- <span>/<p>/<h1>-<h6> → Text/P/H with tag property
- <a> → Link (extends: 'Link', href as prop — never attr: { href })
- <button> → Button
- <input> → Input, Radio, Checkbox
- <img> → Img
- <form> → Form
- <ul>/<ol> + <li> → children array with childExtends
- CSS px → design tokens (16px→'A', 26px→'B', 42px→'C')
- CSS colors → theme tokens
- media queries → @tabletS, @mobileL breakpoints
- CSS classes → flatten as component properties
- id/class attrs → not needed

Output clean DOMQL v3 with named exports.

Paste the HTML below:"""


@mcp.prompt()
def symbols_design_review_prompt() -> str:
    """Prompt template for visual/design audit against the design system."""
    return """Review this Symbols component for design system compliance.

Check:
1. Spacing uses tokens (A, B, C...) not pixels
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
