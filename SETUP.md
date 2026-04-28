# Setup Guide — symbols-mcp

Complete setup for every major MCP-capable editor and AI client. Pick your tool below.

> **TL;DR — fastest path:** install once with `uv`, point your editor at `uvx symbols-mcp`. The server auto-updates with `--refresh` on every launch.

---

## Table of contents

- [Prerequisites](#prerequisites)
- [Install methods (pick one)](#install-methods-pick-one)
- [Editor / client configurations](#editor--client-configurations)
  - [Claude Code (CLI)](#claude-code-cli)
  - [Claude Desktop (Mac / Windows)](#claude-desktop-mac--windows)
  - [Claude.ai (web)](#claudeai-web)
  - [Cursor](#cursor)
  - [Windsurf (Codeium)](#windsurf-codeium)
  - [Zed](#zed)
  - [VS Code (Continue / Cline / Roo)](#vs-code-continue--cline--roo)
  - [Cline (VS Code)](#cline-vs-code)
  - [Gemini CLI](#gemini-cli)
  - [Goose (Block)](#goose-block)
  - [Cody (Sourcegraph)](#cody-sourcegraph)
  - [Generic / custom clients](#generic--custom-clients)
- [Local development setup (cloning the repo)](#local-development-setup-cloning-the-repo)
- [Bootstrapping a new Symbols project — auto-load rules in every editor](#bootstrapping-a-new-symbols-project--auto-load-rules-in-every-editor)
- [Using `/symbols-audit` and other tools in any editor](#using-symbols-audit-and-other-tools-in-any-editor)
- [Transport modes](#transport-modes)
- [Verifying the install](#verifying-the-install)
- [Updating](#updating)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Pick whichever runtime you have already. The server is the same Python package either way.

| Runtime | Install link | Used in commands below |
|---|---|---|
| **uv** (recommended) | https://docs.astral.sh/uv/ | `uvx symbols-mcp` |
| pip / Python ≥ 3.10 | https://www.python.org/downloads/ | `pip install symbols-mcp` |
| Node.js ≥ 18 | https://nodejs.org/ | `npx @symbo.ls/mcp` |

No API keys are required for the documentation/audit/generation tools. Project-management tools (`login`, `save_to_project`, `publish`, `push`) need a free Symbols.app account.

---

## Install methods (pick one)

### A. `uvx` (zero-install, auto-update) — recommended

```bash
uvx symbols-mcp           # one-shot run (cached)
uvx --refresh symbols-mcp # always pull latest from PyPI on each launch
```

`uvx` is part of [`uv`](https://docs.astral.sh/uv/). Nothing to install globally — the package lives in uv's cache.

### B. `pip` (global install, manual update)

```bash
pip install --user symbols-mcp
symbols-mcp           # binary on $PATH
```

### C. `npm` (Node-friendly wrapper)

```bash
npx -y @symbo.ls/mcp
```

The npm package is a thin wrapper that delegates to the Python server. Auto-updates with `npx`.

### D. From source (for contributors — see [Local development](#local-development-setup-cloning-the-repo))

---

## Editor / client configurations

Every config below uses the **`uvx --refresh`** form so you always pull the latest. Replace with `uvx symbols-mcp` (no refresh) or `pip`-based commands if you prefer pinned/offline behavior.

### Claude Code (CLI)

Three scopes, in order of precedence:

1. **Project-scoped** (recommended for teams) — `<repo-root>/.mcp.json`:
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
   Commit this file. Anyone who clones the repo gets the same MCP server.

2. **User-global** — `~/.claude.json` under `mcpServers`:
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

3. **Per-project override** — `~/.claude.json` under `projects.<absolute-path>.mcpServers`:
   ```json
   {
     "projects": {
       "/Users/me/work/my-app": {
         "mcpServers": {
           "symbols-mcp": {
             "type": "stdio",
             "command": "uvx",
             "args": ["--refresh", "symbols-mcp"]
           }
         }
       }
     }
   }
   ```

After saving, run `/mcp` in Claude Code and approve the server.

### Claude Desktop (Mac / Windows)

Edit `claude_desktop_config.json`:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"]
    }
  }
}
```

Quit and re-open Claude Desktop. The server appears under the 🛠️ menu.

### Claude.ai (web)

Claude.ai supports MCP servers via the **Integrations** panel (Pro / Team / Enterprise). Two paths:

1. **Hosted (no setup):** if your org has connected the Symbols integration via the Symbols team, you'll see `Symbols` in the integrations list — toggle on.
2. **Custom server:** Settings → Profile → Integrations → Add custom integration. Provide:
   - **Type:** `MCP`
   - **Transport:** `SSE` (web requires SSE — see [Transport modes](#transport-modes))
   - **URL:** `https://<your-host>:<port>/sse`
   - Run the server somewhere reachable: `MCP_TRANSPORT=sse MCP_HOST=0.0.0.0 MCP_PORT=8080 uvx symbols-mcp`

### Cursor

`~/.cursor/mcp.json` (global) or `<repo>/.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"]
    }
  }
}
```

Open Cursor → Settings → MCP — the server should appear and auto-connect. Toggle on.

### Windsurf (Codeium)

`~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"]
    }
  }
}
```

Restart Windsurf. The server appears in Cascade's MCP tools panel.

### Zed

`~/.config/zed/settings.json` under `context_servers`:

```json
{
  "context_servers": {
    "symbols-mcp": {
      "command": {
        "path": "uvx",
        "args": ["--refresh", "symbols-mcp"]
      },
      "settings": {}
    }
  }
}
```

Open the Assistant panel → tools — `symbols-mcp` appears.

### VS Code (Continue / Cline / Roo)

VS Code itself doesn't have built-in MCP yet. Use one of the extensions below. The configs are JSON; paths differ per extension.

#### Continue.dev

`~/.continue/config.yaml`:

```yaml
experimental:
  modelContextProtocolServers:
    - name: symbols-mcp
      transport:
        type: stdio
        command: uvx
        args: ["--refresh", "symbols-mcp"]
```

#### Cline (VS Code)

VS Code → Cline panel → MCP Servers → `Edit MCP settings`. Adds to `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### Roo Code (VS Code)

Same JSON shape as Cline; Roo's settings file lives at `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`.

### Gemini CLI

Google's Gemini CLI (`gemini`) supports MCP. Edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"],
      "trust": true
    }
  }
}
```

For project-scoped: `<repo>/.gemini/settings.json` with the same shape. Run `gemini mcp list` to verify.

### Goose (Block)

Goose has first-class MCP support. Two ways:

1. **Goose Desktop:** Settings → Extensions → Add custom extension → Type: `STDIO`, Command: `uvx --refresh symbols-mcp`.
2. **Config file** — `~/.config/goose/config.yaml`:
   ```yaml
   extensions:
     symbols-mcp:
       type: stdio
       cmd: uvx
       args: ["--refresh", "symbols-mcp"]
       enabled: true
   ```

### Cody (Sourcegraph)

Cody supports MCP via OpenCtx. In VS Code settings (`settings.json`):

```json
{
  "openctx.providers": {
    "symbols-mcp": {
      "command": "uvx",
      "args": ["--refresh", "symbols-mcp"]
    }
  }
}
```

### Generic / custom clients

Any MCP-compliant client works. The minimum invocation is:

```bash
uvx symbols-mcp           # stdio, default
```

For SSE/HTTP transport see [Transport modes](#transport-modes).

The server implements the MCP spec at https://modelcontextprotocol.io/ — no proprietary extensions.

---

## Local development setup (cloning the repo)

Use this if you're contributing to symbols-mcp or want to run an unreleased version.

```bash
git clone https://github.com/symbo-ls/symbols-mcp.git
cd symbols-mcp
uv sync                    # installs deps + the package in editable mode
uv run symbols-mcp         # smoke-test it starts
```

Then point any editor at the local checkout. **Project-scoped `.mcp.json` for Claude Code** (committed in this repo as a working example):

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "symbols-mcp"]
    }
  }
}
```

`uv run` resolves `pyproject.toml` from the cwd, so it works for anyone who clones the repo. Open Claude Code in the repo dir, run `/mcp`, and approve the project-scoped server.

For other editors during development, use the same shape but point at the local checkout:

```json
{
  "mcpServers": {
    "symbols-mcp-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/symbols-mcp", "symbols-mcp"]
    }
  }
}
```

### Running the deterministic audit CLI

The repo ships a standalone Node-based audit at `bin/symbols-audit`. No MCP needed — it sweeps a Symbols project for rule violations:

```bash
node bin/symbols-audit /path/to/project/symbols
# or
./bin/symbols-audit /path/to/project/symbols
```

Strict by default (exit 1 on findings). Pass `--allow-findings` to exit 0 with findings. See [AUDIT.md](symbols_mcp/skills/AUDIT.md).

---

## Bootstrapping a new Symbols project — auto-load rules in every editor

When you create a Symbols project (or adopt symbols-mcp in an existing one), the agent ideally follows the framework rules without ever being told to "use symbols-mcp." Three layers, in order of leverage:

### Layer 1 — MCP server `instructions` field (zero setup)

Once you've connected `symbols-mcp` to your editor (see [Editor configurations](#editor--client-configurations) above), the server exposes an `instructions` string that every MCP-aware editor surfaces to its agent automatically. The current version includes a **MUST-CALL sequence** (`get_project_context` first, `get_project_rules` before generating, `audit_component` after each component, `audit_project` for full audits) plus the hard-rule list. Set once globally — works for every Symbols project you open.

This is invisible to you (the agent reads it on connect) and works for **every editor that speaks MCP**: Claude Code, Cursor, Windsurf, Cline, Continue, Roo, Zed, Goose, Gemini CLI, Antigravity, Cody.

### Layer 2 — Project-level rule files (auto-loaded by each editor)

Each editor reads its own rule file from the project root on every chat:

| Editor | File path | Auto-loaded? |
|---|---|---|
| Claude Code | `CLAUDE.md` | yes |
| Cursor | `.cursor/rules/symbols.md` (with `alwaysApply: true`) | yes |
| Windsurf | `.windsurfrules` | yes |
| Cline | `.clinerules` | yes |
| Codex / Aider / Goose / Cody / generic | `AGENTS.md` | yes (most) |

**Drop them all at once with the bundled init command** — it copies vendor-specific templates into the project root, idempotently:

```bash
# from any Symbols project root:
npx -y @symbo.ls/mcp init-rules

# preview without writing
npx -y @symbo.ls/mcp init-rules --list

# overwrite existing files
npx -y @symbo.ls/mcp init-rules --force

# only some editors
npx -y @symbo.ls/mcp init-rules --only=claude,cursor
```

Files written:
- `CLAUDE.md` — Claude Code (most detailed)
- `.cursor/rules/symbols.md` — Cursor (with `alwaysApply: true` frontmatter)
- `.windsurfrules` — Windsurf
- `.clinerules` — Cline
- `AGENTS.md` — vendor-neutral fallback for any agent that reads it

After running the command, open the project — every editor that supports MCP + project rules now bootstraps the workflow automatically. **No more "use symbols-mcp" reminders.**

### Layer 3 — Optional: claude-mem-style plugin (advanced)

If you need behavior beyond what MCP + rules can do (e.g. a git pre-commit hook that runs `bin/symbols-audit`, or a slash command that auto-runs the audit playbook), you can write an editor plugin. For Symbols this is overkill — Layers 1+2 already cover the bootstrapping need. Skip unless you have a specific automation requirement.

### Verifying the bootstrap

After running `init-rules`, sanity-check by asking your editor's agent: _"Build me a hero component with a search input."_ Without prompting "use symbols-mcp," the agent should:

1. Call `get_project_context` to resolve the project
2. Call `get_project_rules` (or read CLAUDE.md / AGENTS.md / equivalent)
3. Call `generate_component` for the hero
4. Call `audit_component` on the result before saving

If the agent skips step 1 or 2, the rule files weren't picked up — check the editor's settings. If the agent doesn't have the symbols-mcp tools at all, see [Editor configurations](#editor--client-configurations).

---

## Using `/symbols-audit` and other tools in any editor

`/symbols-audit` is a **Claude Code slash command** — short for "run the multi-phase audit playbook end-to-end." It bundles three things:

1. `mcp__symbols-mcp__get_project_context` (resolve owner/key/env from cwd)
2. `mcp__symbols-mcp__audit_project` (fetch the playbook)
3. `bin/symbols-audit ./symbols` (deterministic regex CLI), then iterate fixes with `audit_component` + chrome-mcp UI tests

The slash-command sugar is Claude Code-only, but **the capability works in every MCP-aware editor**. Three patterns, in order of recommendation:

### Pattern 1 — Natural language (zero setup, works in every MCP editor)

Just ask the AI what you want. It picks the right tools.

| Editor | Prompt |
|---|---|
| Cursor / Windsurf / Cline / Roo / Continue / Zed / Goose | "Run a full Symbols audit on this project. Use symbols-mcp." |
| Antigravity (Google) | Same. Antigravity supports MCP and exposes the symbols-mcp tools to its agents. |
| Gemini CLI | `gemini "Audit this Symbols project end-to-end using symbols-mcp."` |
| Claude.ai (web, with MCP integration) | "Run audit_project for me, then call audit_component on the violations." |
| Cody (Sourcegraph) | "Use symbols-mcp's audit_project tool, then validate components with audit_component." |

The agent reads the playbook, runs the CLI via Bash, iterates fixes. Same outcome as `/symbols-audit`.

### Pattern 2 — Custom command (slash-command parity)

If your editor supports custom commands, register one named `symbols-audit` for one-keystroke invocation.

#### Cursor

`<repo>/.cursor/rules/symbols-audit.md`:

```markdown
---
description: Full Symbols project audit
---

When the user asks for a Symbols project audit:
1. Call mcp__symbols-mcp__get_project_context (no args — uses cwd)
2. Call mcp__symbols-mcp__audit_project (returns the playbook)
3. Run `npx -y @symbo.ls/mcp symbols-audit ./symbols` via the terminal
4. For each violation in audit/findings.json, call mcp__symbols-mcp__audit_component to verify the fix
5. Iterate until findings.json is clean, then write audit/report.md
```

Then say "audit my symbols project" — Cursor follows the rule.

#### Continue.dev

`~/.continue/config.yaml`:

```yaml
customCommands:
  - name: symbols-audit
    description: Full Symbols project audit (multi-phase playbook)
    prompt: |
      Use symbols-mcp end-to-end:
      1. mcp__symbols-mcp__get_project_context — resolve project from cwd
      2. mcp__symbols-mcp__audit_project — fetch playbook
      3. Run bin/symbols-audit ./symbols via shell (strict, exit 1 on findings)
      4. Iterate fixes with mcp__symbols-mcp__audit_component
      5. Write audit/report.md per Phase 5 of the playbook
```

Then `/symbols-audit` works in Continue.

#### Windsurf

Cascade workflow `~/.codeium/windsurf/workflows/symbols-audit.json`:

```json
{
  "name": "symbols-audit",
  "description": "Full Symbols project audit",
  "steps": [
    "Call mcp__symbols-mcp__get_project_context",
    "Call mcp__symbols-mcp__audit_project",
    "Run `npx -y @symbo.ls/mcp symbols-audit ./symbols` in terminal",
    "For each finding, validate the fix with mcp__symbols-mcp__audit_component",
    "Iterate to convergence, then write audit/report.md"
  ]
}
```

#### Cline / Roo / Zed / Goose

These don't have custom slash commands per se — use Pattern 1 (natural language). Or save a snippet/macro at the editor level (e.g. text expander → "audit my symbols project end-to-end with symbols-mcp").

#### Antigravity (Google)

Antigravity supports MCP via its standard config (`~/.antigravity/mcp.json` or in-app settings). With symbols-mcp connected, Pattern 1 works directly. For repeated use, save a custom system prompt: "When I say `audit`, run the symbols-mcp audit_project playbook end-to-end."

#### Gemini CLI

Gemini CLI ships first-class MCP. After registering symbols-mcp in `~/.gemini/settings.json`, use:

```bash
gemini "Run a full Symbols audit on $(pwd) using symbols-mcp."
```

For shorthand, alias it in your shell:

```bash
alias symbols-audit='gemini "Run a full Symbols audit on $(pwd) using symbols-mcp."'
```

### Pattern 3 — Direct shell (no editor needed)

The audit CLI is independent of any editor. Run it from any terminal:

```bash
# via npm wrapper (no install)
npx -y @symbo.ls/mcp symbols-audit ./symbols

# via uv (after `uvx symbols-mcp`'s cache populates)
uvx --from symbols-mcp symbols-audit ./symbols

# via local checkout (contributors)
node /path/to/symbols-mcp/bin/symbols-audit ./symbols
```

Strict by default — exit 1 on findings. Pass `--allow-findings` for soft mode (exit 0 with findings) or `--json` for machine-readable output.

### Pattern 4 — Source the bundled venv (advanced / debugging)

When installed via npm (`npm i @symbo.ls/mcp-server`), the package ships a Python venv at:

```
node_modules/@symbo.ls/mcp-server/node_modules/@symbo.ls/mcp/.venv
```

Source it for direct binary access (useful when an editor's MCP loader fails to spawn the server, or when you want to run the Python module manually):

```bash
source /Users/me/proj/node_modules/@symbo.ls/mcp-server/node_modules/@symbo.ls/mcp/.venv/bin/activate

# Now you have:
symbols-mcp                            # start MCP server (stdio)
python -m symbols_mcp.server           # same thing
mcp                                    # generic MCP CLI
deactivate                             # leave the venv
```

This bypasses any editor-side MCP wiring — useful for diagnosing "tools not loading" issues. If the server starts cleanly here, the problem is in the editor's config, not the package.

### Cheatsheet — capability ↔ MCP tool

| You want to… | MCP tool (works in any MCP editor) | Shell equivalent |
|---|---|---|
| Resolve project owner/key/env | `get_project_context` | (read `symbols.json` manually) |
| Get framework rules | `get_project_rules` | `cat symbols_mcp/skills/RULES.md` |
| Validate a single component | `audit_component(code)` | (n/a — shell can't read source strings) |
| Get the audit playbook | `audit_project()` | `cat symbols_mcp/skills/AUDIT.md` |
| Sweep a project for violations | (n/a — call `audit_component` per file, or run shell) | `bin/symbols-audit ./symbols` |
| Generate a component | `generate_component(description, name)` | (n/a) |
| Convert React/HTML | `convert_react(code)` / `convert_html(code)` | (n/a) |
| Push to platform | `save_to_project` + `publish` + `push` | `smbls publish` |
| Login | `login(email, password)` | `smbls login` |

The MCP tools are universal across editors. The shell column is your fallback when no MCP is available.

---

## Transport modes

The server speaks three transports:

### stdio (default)

Editors spawn the process and talk over stdin/stdout. No network, no port. Used by every editor config above.

### SSE (self-hosted HTTP)

Run as a long-lived server that any HTTP MCP client can hit:

```bash
MCP_TRANSPORT=sse MCP_HOST=0.0.0.0 MCP_PORT=8080 uvx symbols-mcp
```

Then connect from claude.ai / a remote client / a custom integration to `http://<host>:8080/sse`.

| Env var | Default | Purpose |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` | `stdio` or `sse` |
| `MCP_HOST` | `127.0.0.1` | Bind address for SSE |
| `MCP_PORT` | `8080` | Bind port for SSE |

### Streamable HTTP (hosted worker)

The official Symbols-hosted edge worker — no install, no process to keep alive, latency-optimized via Cloudflare's edge network. Speaks the [MCP Streamable HTTP transport](https://modelcontextprotocol.io/) and exposes plain REST helpers alongside.

| Env | URL |
|---|---|
| Production | `https://symbols-mcp.symbols.workers.dev` |
| Dev / next | `https://symbols-mcp-dev.nika-980.workers.dev` |

Configure any MCP-aware editor with the `url` form (no `command` / `args`):

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "url": "https://symbols-mcp.symbols.workers.dev"
    }
  }
}
```

Useful REST endpoints (all return JSON):

| Endpoint | Purpose |
|---|---|
| `GET /` | Discovery — name, version, has_project_context |
| `GET /health` | Liveness check |
| `GET /tools` | List all tools |
| `POST /tools/<name>` | Invoke one tool, body is the tool args |
| `GET /resources` | List skill / reference resources |
| `GET /resources/read?uri=<uri>` | Read a single resource |

#### Project context — `?owner=&key=`

The hosted worker accepts project identity as URL parameters and uses them to fetch the live project context from the Symbols KV cache. Pass them on every MCP request:

```
https://symbols-mcp.symbols.workers.dev/?owner=acme&key=storefront
```

Equivalent legacy form (slash-separated, accepted for backward-compat):

```
https://symbols-mcp.symbols.workers.dev/?project_key=acme/storefront
```

When project context is found, every tool that takes an active-project argument (`generate_component`, `generate_page`, `convert_*`, `get_project_context`, `save_to_project`, `publish`, `push`) automatically scopes to that project — components, pages, design-system tokens, state, and functions are surfaced into the prompt so generations match the project's actual surface area, not generic defaults.

Project identity is canonical `${owner}/${key}` per [§45](../server/CLAUDE.md) — bare keys can collide across owners, the worker resolves through the 2-segment route `/core/projects/key/:owner/:projectSlug`. The legacy compound `owner--slug` shape is normalized for older clients.

---

## Verifying the install

After configuring your editor:

1. **List tools** — your editor's MCP UI should show ~25 tools (`generate_component`, `audit_project`, `get_project_rules`, etc.) and ~25 resources (`symbols://skills/*`).
2. **Smoke-test from a chat:**
   ```
   Use the symbols-mcp tool get_project_rules to fetch the current ruleset.
   ```
   You should see ~150-180 KB of bundled rules + framework + design-system + default-styles content.
3. **Audit a known-bad snippet** — paste this and call `audit_component`:
   ```js
   export const Bad = { html: '<svg viewBox="0 0 24 24"><path d="M12 2L1 21h22L12 2z"/></svg>' }
   ```
   Expected: `Rule 62` violation (banned inline-SVG-for-icon). If you don't see Rule 62, your client is hitting an older PyPI version — see [Updating](#updating).

---

## Updating

```bash
# uvx — clear cache and re-fetch
uv cache clean symbols-mcp && uvx symbols-mcp

# pip
pip install --upgrade symbols-mcp

# npm
npm update -g @symbo.ls/mcp

# from source
cd symbols-mcp && git pull && uv sync
```

The recommended `uvx --refresh symbols-mcp` setup pulls the latest on every launch — no manual update needed.

---

## Troubleshooting

### `Unknown command: /symbols-audit` (Claude Code)

The slash command isn't installed in a path Claude Code scans. Either:
- Place `symbols-audit.md` in `~/.claude/commands/` (user-global), or
- Place it in `<repo>/.claude/commands/` (project-scoped — must be in the cwd Claude Code launched from)

### `audit_project tool isn't exposed`

Your client is hitting a PyPI version older than 1.1.0. Either:
- Switch to `uvx --refresh symbols-mcp`
- Use the local checkout (`uv run symbols-mcp` from a clone)
- `uv cache clean symbols-mcp && uvx symbols-mcp`

### Server fails to start: `command not found: uvx`

Install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Or use the `pip` install path (`pip install symbols-mcp` then point your editor at the `symbols-mcp` binary).

### `ENOENT` / `command not found: uv` from inside an editor

Editors often spawn MCP servers with a minimal `PATH`. Use the full absolute path to the binary:
```json
{
  "command": "/Users/me/.local/bin/uv",
  "args": ["run", "symbols-mcp"]
}
```
Find the path with `which uv`.

### Tools list is empty after connecting

1. Check the editor's MCP log for stderr from the server.
2. Run `uvx symbols-mcp` manually — if it prints an import error, you're missing Python ≥ 3.10.
3. Verify with `uvx symbols-mcp --version` (should print 1.1.x or later).

### Rule 62 not flagged on a clearly bad snippet

You're on an old version. See [Updating](#updating).

### Server is slow on first launch

`uvx --refresh` checks PyPI every launch (~1-2s). For faster startup at the cost of stale risk, drop `--refresh`:
```json
{ "command": "uvx", "args": ["symbols-mcp"] }
```

---

## Quick reference card

| Task | Command |
|---|---|
| One-off run | `uvx symbols-mcp` |
| Always-latest | `uvx --refresh symbols-mcp` |
| Local dev | `uv run symbols-mcp` (from repo) |
| SSE for web clients | `MCP_TRANSPORT=sse uvx symbols-mcp` |
| Run audit CLI | `node bin/symbols-audit ./symbols` |
| Slash command (Claude Code) | `/symbols-audit [path]` |

For framework rules, syntax, and the audit playbook, see the bundled skills:
[FRAMEWORK.md](symbols_mcp/skills/FRAMEWORK.md) ·
[DESIGN_SYSTEM.md](symbols_mcp/skills/DESIGN_SYSTEM.md) ·
[RULES.md](symbols_mcp/skills/RULES.md) ·
[AUDIT.md](symbols_mcp/skills/AUDIT.md)
