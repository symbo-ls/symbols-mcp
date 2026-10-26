---
description: Symbols.app project — required workflow and hard rules
alwaysApply: true
---

# Symbols.app project — agent rules

This is a Symbols.app / Symbols project (smbls 3.14.0). The `symbols-mcp` MCP server is the source of truth for framework rules, syntax, design system, audit playbook, and platform tools.

## Required workflow

1. **Call `mcp__symbols-mcp__get_project_context` FIRST.** Resolves owner / key / env / token from cwd's `symbols.json`. Treat its `next_step` as authoritative. NEVER hardcode owner / key / creds.
2. **Before generating ANY component or page**, call `mcp__symbols-mcp__get_project_rules` once per session.
3. **For new code**, use `mcp__symbols-mcp__generate_component` / `generate_page`.
4. **Validate every component** with `mcp__symbols-mcp__audit_component(code, file_path)` after writing.
5. **For full audits**, run `mcp__symbols-mcp__audit_project()` (playbook) + `npx -y -p @symbo.ls/mcp symbols-audit ./symbols` (CLI).

## Hard rules

- **Flat element API.** `el.X` not `el.props.X`. `el.onClick` not `on: { click }`. Reactive functions are `(el, s)`.
- **Lowercase child keys NEVER render.** PascalCase only.
- **Auto-extend by key.** A key that names a registered component IS that component when it has no `extends` (`Navbar: {}`, not `Navbar: { extends: 'Navbar' }`). Multi-instance → `Navbar_1`, `Navbar_2`. A key WITH `extends` is a role name (`SidebarNav: { extends: 'Navbar' }`) — right unless it names a different registered component or is a tag name, a generic word or a placeholder (`Header`, `Row`, `Foo`): name it for its role, never rename it to the base. Other forms: multi-base composition (`extends: ['Hgroup', 'Form']`), nested-child chains (`extends: 'AppShell > Sidebar'`).
- **ALL values use design-system tokens.** NO raw px/hex/rgb/hsl/ms.
  - Sequence families (typography, spacing, timing) share the letter alphabet but each generates its own values from `{ base, ratio }` — `fontSize: 'B'` ≠ `padding: 'B'` ≠ `transition: 'B'`.
  - NO custom-named spacing tokens — sequence + sub-tokens (`A1`, `A2`, …) only.
- **Polyglot for all user-facing strings.** `'{{ key | polyglot }}'` template. **NO `t` or `tr`** — only `polyglot`.
- **Declarative `fetch:` prop** (@symbo.ls/fetch). NEVER `window.fetch` / `axios`.
- **Helmet for metadata.** `metadata: {…}`. NEVER `document.title = …`.
- **Router** via `el.router(path, el.getRoot())`. NEVER `window.location.*`.
- **Theme** via `changeGlobalTheme()` from `smbls`. NEVER `setAttribute('data-theme')`.
- **Icons** via `Icon` component + `designSystem.icons`. `html: '<svg ...>'` is BANNED (Rule 62).
- **NO imports between project files.** PascalCase key auto-extends. Call functions via `el.call('fn', …)`.
- **NO direct DOM manipulation.** No `document.*`, `addEventListener`, `classList`, `innerHTML`, `setAttribute`, `el.node.style.X = …`, `parentNode` traversal.
- **HTML attrs are flat props** — NOT inside `attr: {}`.
- **`extends` / `childExtends` are quoted strings.** Never inline objects.

## When in doubt

Use `symbols-mcp` tools. Do not write Symbols code from memory.
