<!-- generated from CLAUDE.md (canonical) 2026-08-20 — edit CLAUDE.md, then re-copy -->

# symbols-mcp — CLAUDE.md

MCP (Model Context Protocol) server for Symbols.app. Ships as a Python
package (`symbols-mcp` on PyPI) and a Node wrapper (`@symbo.ls/mcp` on
npm), exposing the same tools to any MCP client: Claude Code, Claude
Desktop, claude.ai, Cursor, Windsurf, VS Code, Zed, Gemini CLI, and more.
Tools cover project context/rules lookup, DOMQL codegen/conversion,
component/project auditing, and Symbols platform project management
(login, save, publish, push). Canonical rules docs live at
`symbols_mcp/skills/*.md` (framework, design system, components,
frankability). Docs/audit/generation tools need no API key; project
management tools need a Symbols.app account.

## Build / test / run

- Python surface: `uv sync` to install, then `uv run symbols-mcp` or
  `uvx symbols-mcp` to run the server. Requires Python >= 3.10.
- Node surface: `npm install`, `npm run build` (esbuild to `dist/esm` +
  `dist/cjs`), `npm run lint` / `lint:fix` (flat ESLint config).
- Tests: `scripts/test.sh` — resolves `uv` (venv fallback if missing),
  then `uv run pytest -q tests/`. Covers imports, tool registration, and
  the skills bundle. This is the CI gate.
- CLI bins shipped to consumers: `symbols-mcp` (the server itself),
  `symbols-audit <dir>` (static frankability audit, strict, exits 1 on
  findings — wraps `@symbo.ls/frank-audit`), `symbols-mcp-init-rules`.
- Per-editor wiring (Claude Code, Cursor, Windsurf, Zed, ...) is
  documented client-by-client in `SETUP.md`.

## Conventions

- This MCP server is CUSTOMER-FACING. No internal-fleet skills, tools,
  prompts, or docs may be added to it, ever. Everything shipped here
  (skill text, tool descriptions, CLI output) is read by external
  users' AI assistants — orchestration/fleet tooling belongs elsewhere.
- `symbols_mcp/skills/*.md` is the canonical rules source for every
  tool response (FRAMEWORK, RULES, COMPONENTS, DESIGN_SYSTEM,
  FRANKABILITY FA0xx-FA5xx, PATTERNS). Update the skill file, not the
  tool code, when a rule changes.
- Targets the current smbls stack (DOMQL v3.14: flat element API,
  signal-based reactivity, `el.fetch`, `el.router`) — keep skill docs in
  step with the framework version they describe.
- `lib/audit.js` is a backward-compat shim only, delegating to
  `@symbo.ls/frank-audit` — don't add new audit logic here.

## Agent protocol

- DONE = shipped + tested + live-verified: a green `scripts/test.sh`
  run AND a real check that the change works end-to-end (a built dist
  exercised by an actual MCP client, not just a passing unit test).
- Work is tracked on the assigned my.symbols platform ticket — update
  the ticket; don't invent local state tracking.
- Escalate anything outside this scope, or blocking, to Nika.

## Never

- Never `npm publish` / publish to PyPI / hand-bump versions or tags —
  publishing runs through the dedicated release pipeline only.
- Never hardcode content, credentials, or project identity — read them
  from the caller's `symbols.json` / project context, or ask the user.
- Never emit or teach raw `fetch` / axios / socket.io in generated or
  audited DOMQL code — the framework's declarative `el.fetch` / SDK
  path is the only sanctioned one.
- Never edit vendored/shared framework code (`@symbo.ls/frank-audit`,
  smbls packages) from this repo — fix upstream, or override locally.
- Never `git stash` in this checkout — commit or leave changes in
  place instead.
