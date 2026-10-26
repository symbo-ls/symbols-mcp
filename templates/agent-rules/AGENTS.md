# Symbols.app project — universal agent rules

A vendor-neutral version of the rules for any agent that reads `AGENTS.md` (Codex/Aider/Sourcegraph Cody/Goose/etc.). Identical content to CLAUDE.md / .cursor/rules / .windsurfrules — drop in projects where you don't know which agent will pick it up.

## Required workflow

1. Call `mcp__symbols-mcp__get_project_context` FIRST. Resolves owner / key / env / token from cwd's `symbols.json`. NEVER hardcode.
2. Call `mcp__symbols-mcp__get_project_rules` before generating any component or page.
3. Use `mcp__symbols-mcp__generate_component` / `generate_page` for new code.
4. Validate with `mcp__symbols-mcp__audit_component(code, file_path)` after each component.
5. Full audit: `audit_project()` playbook + `npx -y -p @symbo.ls/mcp symbols-audit ./symbols` CLI.

## Hard rules

- Flat element API: `el.X` (NOT `el.props.X`); `el.onClick` (NOT `on: {}`); `(el, s)` reactive sigs.
- Lowercase child keys NEVER render — PascalCase only.
- Auto-extend by key: a key that names a registered component IS that component when it has no `extends` (`Navbar: {}`). Multi-instance → suffix with `_N` (`Navbar_1`, `Navbar_2`). A key WITH `extends` is a role name (`SidebarNav: { extends: 'Navbar' }`) — right unless it names a different registered component or is a tag name, a generic word or a placeholder (`Header`, `Row`, `Foo`): name it for its role, never rename it to the base.
- Design-system tokens for ALL values. NO raw px / hex / rgb / hsl / ms.
- Three sequence families (typography, spacing, timing) — same letter, different values per family. NO custom-named spacing tokens.
- Polyglot only for user-facing strings — `'{{ key | polyglot }}'`. No `t` / `tr` function exists.
- Declarative `fetch:` prop. No `window.fetch` / `axios` in components.
- Helmet `metadata: {…}` for SEO. No `document.title = …`.
- `el.router(path, el.getRoot())` for navigation. No `window.location.*`.
- `changeGlobalTheme()` from `smbls` for theme. No `setAttribute('data-theme')`.
- Icons via `Icon` component + `designSystem.icons`. `html: '<svg ...>'` is BANNED (Rule 62).
- No imports between project files. PascalCase keys auto-extend. `el.call('fn', …)` for functions.
- No direct DOM manipulation.

Do not write Symbols code from memory. Use `symbols-mcp` tools or read the bundled skill files via the MCP resource URIs (`symbols://skills/*`).
