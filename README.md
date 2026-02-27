# symbols-mcp

MCP server for [Symbols/DOMQL v3](https://symbols.so) — provides documentation search and framework reference tools for AI coding assistants (Cursor, Claude Code, Windsurf, etc.).

No API keys required. All tools work fully offline using bundled documentation.

---

## Tools

- **`get_project_rules`** — Returns mandatory Symbols/DOMQL v3 rules. Call this before any code generation task.
- **`search_symbols_docs`** — Keyword search across all bundled Symbols documentation files.

## Resources

- `symbols://skills/domql-v3-reference` — Complete DOMQL v3 syntax reference
- `symbols://skills/project-structure` — Project folder structure and file conventions
- `symbols://skills/design-direction` — UI/UX design direction
- `symbols://skills/migration-guide` — React/Angular/Vue → Symbols migration guide
- `symbols://skills/v2-to-v3-migration` — DOMQL v2 → v3 changes
- `symbols://skills/quickstart` — CLI quickstart
- `symbols://reference/spacing-tokens` — Spacing token reference
- `symbols://reference/atom-components` — Built-in atom components
- `symbols://reference/event-handlers` — Event handler reference

## Prompts

- `symbols_component_prompt` — Template for generating a component
- `symbols_migration_prompt` — Template for migrating framework code
- `symbols_project_prompt` — Template for scaffolding a full project
- `symbols_review_prompt` — Template for reviewing Symbols code

---

## Installation

```bash
pip install symbols-mcp
```

Or with `uv`:

```bash
uvx symbols-mcp
```

## Configuration

Add to your MCP client config (e.g. `mcp.json`):

```json
{
  "mcpServers": {
    "symbols": {
      "command": "uvx",
      "args": ["symbols-mcp"]
    }
  }
}
```

### Custom skills directory

To point at a different skills folder:

```json
{
  "mcpServers": {
    "symbols": {
      "command": "uvx",
      "args": ["symbols-mcp"],
      "env": {
        "SYMBOLS_SKILLS_DIR": "/path/to/your/skills"
      }
    }
  }
}
```
