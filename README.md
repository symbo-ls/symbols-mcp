# symbols-mcp

mcp-name: io.github.symbo-ls/symbols-mcp

MCP server for [Symbols.app](https://symbols.app) — provides documentation search, code generation, conversion, auditing, and framework reference tools for AI coding assistants (Cursor, Claude Code, Windsurf, etc.).

No API keys required. All tools work fully offline using bundled documentation.

---

## Tools

| Tool | Description |
|------|-------------|
| `get_project_rules` | Returns mandatory Symbols.app rules. **Call this first** before any code generation task. |
| `search_symbols_docs` | Keyword search across all bundled Symbols documentation files. |
| `generate_component` | Generate a DOMQL v3 component from a natural language description. |
| `generate_page` | Generate a full page with routing integration. |
| `convert_react` | Convert React/JSX code to Symbols DOMQL v3. |
| `convert_html` | Convert raw HTML/CSS to Symbols DOMQL v3 components. |
| `audit_component` | Audit component code for v3 compliance — returns violations, warnings, and a score. |
| `login` | Log in to Symbols platform with email/password — returns a JWT token for publish/push. |
| `publish` | Publish a version of a Symbols project. Accepts JWT token or API key (`sk_live_...`). |
| `push` | Deploy a project to an environment (production, staging, dev). Accepts JWT token or API key. |
| `detect_environment` | Detect whether the project is local, CDN, JSON runtime, or remote server. |

## Resources

### Skills (documentation)

| URI | Description |
|-----|-------------|
| `symbols://skills/rules` | Strict rules for AI agents working in Symbols/DOMQL v3 projects |
| `symbols://skills/syntax` | Complete DOMQL v3 syntax language reference |
| `symbols://skills/components` | Component reference with flattened props and onX events |
| `symbols://skills/project-structure` | Project folder structure and file conventions |
| `symbols://skills/design-system` | Design system tokens, themes, and configuration |
| `symbols://skills/design-direction` | Modern UI/UX design direction |
| `symbols://skills/patterns` | UI patterns, accessibility, and AI optimization |
| `symbols://skills/migration` | Migration guide (v2→v3, React/Angular/Vue→Symbols) |
| `symbols://skills/audit` | Full audit, enforcement, and feedback framework |
| `symbols://skills/design-to-code` | Design-to-code translation guide |
| `symbols://skills/seo-metadata` | SEO metadata configuration reference |
| `symbols://skills/ssr-brender` | Server-side rendering with brender (SSR/SSG) |
| `symbols://skills/cookbook` | Interactive cookbook with 30+ runnable recipes |
| `symbols://skills/snippets` | Production-ready component snippets |
| `symbols://skills/default-library` | 127+ pre-built components available in all projects |
| `symbols://skills/default-components` | Complete source code of 130+ default template components |
| `symbols://skills/learnings` | Framework internals, technical gotchas, deep runtime knowledge |
| `symbols://skills/running-apps` | 4 ways to run Symbols apps (local, CDN, JSON, remote) |

### Reference (inline)

| URI | Description |
|-----|-------------|
| `symbols://reference/spacing-tokens` | Spacing token table (golden-ratio scale) |
| `symbols://reference/atom-components` | Built-in atom/primitive components |
| `symbols://reference/event-handlers` | Event handler signatures and patterns |

## Prompts

| Prompt | Description |
|--------|-------------|
| `symbols_component_prompt` | Generate a component from a description |
| `symbols_migration_prompt` | Migrate code from React/Angular/Vue |
| `symbols_project_prompt` | Scaffold a complete project |
| `symbols_review_prompt` | Review code for v3 compliance |
| `symbols_convert_html_prompt` | Convert HTML/CSS to DOMQL v3 |
| `symbols_design_review_prompt` | Visual/design audit against the design system |

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

### Transport modes

By default, the server runs over **stdio**. For SSE transport:

```bash
MCP_TRANSPORT=sse MCP_HOST=0.0.0.0 MCP_PORT=8080 uvx symbols-mcp
```
