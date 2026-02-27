"""
Symbols MCP — Documentation search and reference tools for Symbols/DOMQL v3.
"""

import os
import json
import logging
import re
from pathlib import Path

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
        "Reference assistant for the Symbols/DOMQL v3 design-system framework. "
        "Searches Symbols documentation, exposes framework rules, and provides "
        "comprehensive syntax and API reference."
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


def _load_agent_instructions() -> str:
    """Load the upfront AI agent instructions from AGENT_INSTRUCTIONS.md."""
    path = SKILLS_PATH / "AGENT_INSTRUCTIONS.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return _read_skill("CLAUDE.md")


# ---------------------------------------------------------------------------
# TOOLS
# ---------------------------------------------------------------------------


@mcp.tool()
def get_project_rules() -> str:
    """ALWAYS call this first before any generate_* tool.

    Returns the mandatory Symbols/DOMQL v3 rules that MUST be followed.
    Violations cause silent failures — black page, nothing renders.

    Call this before: generate_project, generate_component, generate_page,
    convert_to_symbols, or any code generation task.
    """
    return _load_agent_instructions()


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


# ---------------------------------------------------------------------------
# RESOURCES — Expose skills documentation as browsable resources
# ---------------------------------------------------------------------------


@mcp.resource("symbols://skills/domql-v3-reference")
def get_domql_v3_reference() -> str:
    """Complete DOMQL v3 syntax reference and rules."""
    return _read_skill("CLAUDE.md")


@mcp.resource("symbols://skills/project-structure")
def get_project_structure() -> str:
    """Symbols project folder structure and file conventions."""
    return _read_skill("SYMBOLS_LOCAL_INSTRUCTIONS.md")


@mcp.resource("symbols://skills/design-direction")
def get_design_direction() -> str:
    """Modern UI/UX design direction for generating Symbols interfaces."""
    return _read_skill("DESIGN_DIRECTION.md")


@mcp.resource("symbols://skills/migration-guide")
def get_migration_guide() -> str:
    """Guide for migrating React/Angular/Vue apps to Symbols/DOMQL v3."""
    return _read_skill("MIGRATE_TO_SYMBOLS.md")


@mcp.resource("symbols://skills/v2-to-v3-migration")
def get_v2_v3_migration() -> str:
    """DOMQL v2 to v3 migration changes and examples."""
    return _read_skill("DOMQL_v2-v3_MIGRATION.md")


@mcp.resource("symbols://skills/quickstart")
def get_quickstart() -> str:
    """Symbols CLI setup and usage quickstart guide."""
    return _read_skill("QUICKSTART.md")


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
    """Event handler reference for Symbols/DOMQL v3."""
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
    """Prompt template for generating a Symbols/DOMQL v3 component."""
    return f"""Generate a Symbols/DOMQL v3 component with these requirements:

Component Name: {component_name}
Description: {description}

Follow these strict rules:
- Use DOMQL v3 syntax ONLY (extends, childExtends, flattened props, onX events)
- Components are plain objects with named exports: export const {component_name} = {{ ... }}
- Use design-system tokens for spacing (A, B, C), colors, typography
- NO imports between files — reference components by PascalCase key name
- All folders flat — no subfolders
- Include responsive breakpoints (@mobile, @tablet) where appropriate
- Follow modern UI/UX: visual hierarchy, minimal cognitive load, confident typography

Output ONLY the JavaScript code."""


@mcp.prompt()
def symbols_migration_prompt(source_framework: str = "React") -> str:
    """Prompt template for migrating code to Symbols/DOMQL v3."""
    return f"""You are migrating {source_framework} code to Symbols/DOMQL v3.

Key conversion rules for {source_framework}:
- Components become plain objects (never functions)
- NO imports between project files
- All folders are flat — no subfolders
- Use extends/childExtends (v3 plural, never v2 singular)
- Flatten all props directly (no props: {{}} wrapper)
- Events use onX prefix (no on: {{}} wrapper)
- Use design-system tokens for spacing/colors
- State: state: {{ key: val }} + s.update({{ key: newVal }})
- Effects: onRender for mount, onStateUpdate for dependency changes
- Lists: children: (el, s) => s.items, childrenAs: 'state', childExtends: 'Item'

Provide the {source_framework} code to convert and I will output clean DOMQL v3."""


@mcp.prompt()
def symbols_project_prompt(description: str) -> str:
    """Prompt template for scaffolding a complete Symbols project."""
    return f"""Create a complete Symbols/DOMQL v3 project:

Project Description: {description}

Required structure (smbls/ folder):
- index.js (root export)
- config.js (platform config)
- vars.js (global constants)
- dependencies.js (external packages)
- components/ (PascalCase files, named exports)
- pages/ (dash-case files, camelCase exports, route mapping in index.js)
- functions/ (camelCase, called via el.call())
- designSystem/ (color, spacing, typography, theme, icons)
- state/ (default exports)

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
6. Wrong event handler signatures
7. Default exports for components (should be named)

Provide:
- Issues found with line references
- Corrected code for each issue
- Overall v3 compliance score (1-10)
- Improvement suggestions

Paste your code below:"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """Run the Symbols MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
