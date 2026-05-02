# symbols-mcp

mcp-name: io.github.symbo-ls/symbols-mcp

MCP server for [Symbols.app](https://symbols.app) — provides documentation search, code generation, conversion, auditing, project management, publishing/deployment, and CLI/SDK reference tools for AI coding assistants (Cursor, Claude Code, Windsurf, claude.ai, etc.).

Targets the modern **smbls** stack — flat element API, signal-based reactivity, declarative `fetch:` (`@symbo.ls/fetch`), polyglot translations (`@symbo.ls/polyglot`), helmet metadata (`@symbo.ls/helmet`), SPA routing via `el.router(...)`, theme via `@symbo.ls/scratch`, and SSR via `@symbo.ls/brender`.

No API keys required for documentation tools. Project management tools require a Symbols account (login or API key).

---

## Tools

### Context — start here

| Tool | Description |
|------|-------------|
| `get_project_context` | **CALL FIRST.** Walks up from cwd to find `symbols.json`, returns owner, key, dir, bundler, sharedLibraries, brender, env_type (local/cdn/json_runtime/remote_server), env_evidence, env_guidance, token_present, and a `next_step` hint telling the agent what to do (ask user, log in, or proceed). Replaces the older `detect_environment` for new code. |
| `get_project_rules` | Bundled mandatory ruleset (FRAMEWORK + DESIGN_SYSTEM + RULES + DEFAULT_PROJECT, ≈180K chars). Call before any code generation task. |
| `get_cli_reference` | Complete Symbols CLI (`@symbo.ls/cli`) command reference. |
| `get_sdk_reference` | Complete Symbols SDK (`@symbo.ls/sdk`) API reference. |
| `search_symbols_docs` | Keyword search across all bundled Symbols documentation files. |
| `detect_environment` | _[Legacy]_ Caller-supplied flags variant of env classification. Prefer `get_project_context`. |

### Generation & conversion

| Tool | Description |
|------|-------------|
| `generate_component` | Generate a DOMQL component from a natural language description. Returns prompt + bundled context (≈300K chars). |
| `generate_page` | Generate a full page with routing, helmet metadata, and declarative `fetch:` integration. |
| `convert_react` | Convert React/JSX code to Symbols DOMQL (modern smbls stack). |
| `convert_html` | Convert raw HTML/CSS to Symbols DOMQL components. |
| `convert_to_json` | Convert DOMQL JS source to platform JSON (mirrors frank's toJSON pipeline). Use after `generate_component` / `generate_page` to feed `save_to_project`. |

### Audit

| Tool | Description |
|------|-------------|
| `audit_component` | **Inline VALIDATOR** for a single component string. Returns violations + warnings (≈1K chars). Use during generation. Pass `include_playbook=True` to also dump the AUDIT.md playbook. |
| `audit_project` | Returns the **multi-phase project audit PLAYBOOK** (instructions for the agent — Phase 0 setup → Phase 5 report). Pair with `bin/symbols-audit` CLI for the static-audit phase. |

For filesystem-wide audits the package ships a CLI: `npx -y @symbo.ls/mcp symbols-audit <symbols-dir>` (strict by default, exit 1 on findings). Under the hood it runs `frank-audit audit --strict` — the audit core is now [`@symbo.ls/frank-audit`](https://github.com/symbo-ls/smbls/tree/main/plugins/frank-audit), the AST-based engine that owns the canonical 59-rule registry, prescription generation, and verify-or-rollback fixers.

`lib/audit.js` is preserved as a backward-compat shim that delegates to frank-audit (subprocess CLI, or the `/audit-content` HTTP endpoint when `FRANK_AUDIT_URL` is set). The legacy programmatic API stays callable for non-CLI consumers (the `@symbo.ls/cli`, the MCP HTTP worker, web/edge clients):

```js
const {
  auditContent,         // audit one component string (delegates to frank-audit)
  auditFiles,           // audit a list of {path, content}
  auditDirectory,       // walk a symbols/ dir via `frank-audit audit <dir>`
  mergeFindings,        // preserve status across runs
  summarize,            // breakdown by severity / category / origin
} = require('@symbo.ls/mcp/lib/audit')
```

Findings drift vs the old regex output is expected and correct — frank-audit detects more issues with higher accuracy. Field names stay the same (file, line, rule, severity, category, snippet, suggested_fix). To inspect the rule registry, query frank-audit directly: `npx frank-audit explain <id>`.

### Project Management & Publishing

| Tool | Description |
|------|-------------|
| `login` | Log in to Symbols platform — returns a JWT token. |
| `list_projects` | List the user's projects (names, keys, IDs) to choose from. |
| `create_project` | Create a new Symbols project on the platform. |
| `get_project` | Get a project's current data (components, pages, design system, state). |
| `save_to_project` | Save components/pages/data to a project — creates a new version with change tuples, granular changes, orders, and auto-generated schema entries. |
| `publish` | Publish a version (make it live). |
| `push` | Deploy a project to an environment (production, staging, dev). |

### End-to-End Flow (from any MCP client)

```
1. get_project_context  → resolve owner/key/env/auth state from cwd's symbols.json
2. generate_component   → JS source code
3. audit_component      → inline check (saves a roundtrip if violations exist)
4. convert_to_json      → platform JSON
5. login                → only if token_present was false in step 1
6. create_project       → (if new project needed)
   list_projects        → (or pick existing)
7. save_to_project      → push JSON to platform (creates version)
8. publish              → make version live
7. push                → deploy to environment
```

## Resources

### Skills (documentation)

| URI | Description |
|-----|-------------|
| `symbols://skills/framework` | **Authoritative framework reference** — project structure, plugins, theming, SSR, publish pipeline (mirrors `smbls/FOR_MCP.md`) |
| `symbols://skills/rules` | 62 strict rules for AI agents working in Symbols/DOMQL projects |
| `symbols://skills/syntax` | Complete DOMQL syntax language reference (flat API, signal reactivity) |
| `symbols://skills/modern-stack` | Modern smbls stack — fetch, polyglot, helmet (full metadata catalog), router, scratch theme runtime, brender SSR |
| `symbols://skills/components` | DOMQL component reference (flat props on element, flat onX events) |
| `symbols://skills/project-structure` | Project folder structure and file conventions |
| `symbols://skills/shared-libraries` | sharedLibraries pattern — config, runtime merge, precedence |
| `symbols://skills/design-system` | Design system contract + token catalog (colors, theme, typography, spacing, etc.) |
| `symbols://skills/design` | UI/UX direction + design-to-code translator + 7 specialist personas (consolidated) |
| `symbols://skills/patterns` | UI patterns, accessibility, AI optimization |
| `symbols://skills/migration` | Migration guide for legacy projects + React/Angular/Vue → Symbols |
| `symbols://skills/audit` | Full audit playbook (Phase 0–5, executable end-to-end) |
| `symbols://skills/common-mistakes` | Wrong vs correct DOMQL patterns with zero-tolerance enforcement |
| `symbols://skills/frankability` | Patterns that survive `frank.toJSON` — every `@symbo.ls/frank-audit` rule with wrong vs canonical examples |
| `symbols://skills/learnings` | Framework internals, technical gotchas, deep runtime knowledge |
| `symbols://skills/cookbook` | Cookbook of small reactive recipes (toggle, fetch, modal, tabs, etc.) |
| `symbols://skills/snippets` | Production-ready component snippets (nav, hero, pricing card, footer, etc.) |
| `symbols://skills/default-project` | Default starter — library catalog (127+ components) + pre-configured design system tokens |
| `symbols://skills/default-components` | Complete source code of 130+ default template components (heavy reference, on demand) |
| `symbols://skills/running-apps` | 4 ways to run Symbols apps (local, CDN, JSON, remote) |
| `symbols://skills/cli` | Symbols CLI (`@symbo.ls/cli`) complete command reference |
| `symbols://skills/sdk` | Symbols SDK (`@symbo.ls/sdk`) complete API reference |

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
| `symbols_review_prompt` | Review code for compliance |
| `symbols_convert_html_prompt` | Convert HTML/CSS to DOMQL |
| `symbols_design_review_prompt` | Visual/design audit against the design system |

---

## Quickstart

Two commands and a one-line config — works for every major MCP client.

### 1. Install

Pick whichever runtime you have:

```bash
uvx symbols-mcp           # uv  — recommended, zero install
pip install symbols-mcp   # pip — global binary
npx -y @symbo.ls/mcp      # npm — Node-friendly wrapper
```

### 2. Configure your editor

The standard MCP config snippet (works for **Claude Code**, **Claude Desktop**, **Cursor**, **Windsurf**, **Cline**, **Continue**, **Zed**, **Goose**, **Gemini CLI** — wrap it in whatever shape that editor expects):

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"]
    }
  }
}
```

`--refresh` pulls the latest from PyPI on every launch (~1–2s startup tax — drop it for pinned/offline runs).

### 3. Verify

In your editor's chat, ask the assistant:

> Use `symbols-mcp` to call `get_project_rules`, then summarize the modern stack rules.

If that returns a long ruleset, you're set. Try `audit_component` on a deliberately broken snippet to confirm Rule 62 (the banned inline-SVG-for-icon rule) fires.

---

## Auto-bootstrapping a Symbols project — no more "use symbols-mcp" reminders

Once `symbols-mcp` is configured in your editor, drop project-level rule files so every editor auto-loads the framework rules on every chat:

```bash
# from your Symbols project root
npx -y @symbo.ls/mcp init-rules
```

Writes `CLAUDE.md`, `.cursor/rules/symbols.md`, `.windsurfrules`, `.clinerules`, and `AGENTS.md` — each tailored to its editor, all pointing at the symbols-mcp tools (`get_project_context`, `get_project_rules`, `generate_component`, `audit_component`, etc.). Idempotent; pass `--force` to overwrite or `--only=cursor,claude` to scope.

Combined with the MCP server's `instructions` field (auto-loaded on connect by every MCP-aware editor — Claude Code, Cursor, Windsurf, Cline, Continue, Roo, Zed, Goose, Gemini CLI, Antigravity, Cody), this means you never have to remind the agent to "use symbols-mcp" — the workflow is bootstrapped on first interaction.

### Claude Code: enforcement hooks (installed by default)

Project-level rule files (CLAUDE.md, AGENTS.md, etc.) are best-effort — long contexts dilute them and the agent can drift. For Claude Code, `init-rules` also installs a hooks layer that the harness enforces directly:

| Hook | Trigger | What it does |
|---|---|---|
| `symbols-mcp-require.sh`  | PreToolUse `Edit\|Write\|MultiEdit`  | **BLOCKS** Edit/Write on `*.js`/`*.ts`/`*.tsx` inside any directory tree containing `symbols.json`, until the session has called `mcp__symbols-mcp__get_project_rules` (or `get_project_context`/`generate_component`/`audit_component`). |
| `symbols-mcp-reminder.sh` | UserPromptSubmit                     | Injects the MUST-DO sequence + frankability FA-rule cheatsheet on every turn when cwd is inside a Symbols project. Per-turn injection isn't diluted by long contexts the way CLAUDE.md is. |
| `symbols-mcp-audit.sh`    | PostToolUse `Edit\|Write\|MultiEdit` | After every JS edit inside a Symbols project, runs `frank-audit` plus an inline FA-rule pattern check (FA101/102/103/105/106/206/207/513/514) and surfaces violations back to Claude. |

Files installed:

```
.claude/settings.json                       # wires the three hooks
.claude/hooks/symbols-mcp-require.sh        # PreToolUse  — block edit until rules loaded
.claude/hooks/symbols-mcp-reminder.sh       # UserPromptSubmit — inject directive
.claude/hooks/symbols-mcp-audit.sh          # PostToolUse — frank-audit + FA-rule check
```

Skip hooks: `npx -y @symbo.ls/mcp init-rules --no-hooks`.
Disable a single hook at runtime: `SYMBOLS_MCP_REQUIRE_RULES=0`, `SYMBOLS_MCP_REMINDER=0`, `SYMBOLS_MCP_POST_AUDIT=0`.

Hooks require `bash` and `jq` on `PATH` (already standard on macOS / most Linux distros). `frank-audit` is invoked via `npx -y --no-install @symbo.ls/frank-audit` — if not installed, the inline pattern check still runs.

See [SETUP.md → Bootstrapping](SETUP.md#bootstrapping-a-new-symbols-project--auto-load-rules-in-every-editor) for the layered model and verification steps.

---

## What about `/symbols-audit`?

The `/symbols-audit` slash command is **Claude Code-only**, but the underlying capability works in **every MCP-aware editor** — Cursor, Windsurf, Cline, Continue, Roo, Zed, Goose, Gemini CLI, Antigravity (Google), Cody, Claude.ai web, and any custom MCP client.

Three patterns:

1. **Natural language** (zero setup) — just say _"Run a full Symbols audit on this project using symbols-mcp."_ The agent calls `get_project_context` → `audit_project` (playbook) → `bin/symbols-audit` CLI → iterates fixes with `audit_component`.
2. **Custom command** — register a Cursor rule, Continue customCommand, Windsurf workflow, etc. for one-keystroke parity. Templates in [SETUP.md](SETUP.md#using-symbols-audit-and-other-tools-in-any-editor).
3. **Pure shell** — `npx -y @symbo.ls/mcp symbols-audit ./symbols` works from any terminal, no editor needed. Strict by default, exit 1 on findings.

---

## Full setup guide

**See [SETUP.md](SETUP.md)** for:

- **Per-editor configs:** Claude Code · Claude Desktop · Claude.ai (web) · Cursor · Windsurf · Zed · Cline · Continue · Roo · Cody · Gemini CLI · Goose · Antigravity · generic clients
- **Local development:** clone the repo, run from source, `.mcp.json` template
- **Using `/symbols-audit` & other tools in non-Claude-Code editors:** natural language, custom commands per editor, shell fallback, sourcing the bundled venv directly
- **Transport modes:** stdio (default) and SSE (for claude.ai web / remote clients)
- **Audit CLI:** standalone `bin/symbols-audit` for CI / pre-commit
- **Updating** and **Troubleshooting** (PATH issues, stale versions, missing tools)
