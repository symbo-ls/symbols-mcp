# Symbols.app project — agent rules

This is a Symbols.app / Symbols project (smbls 3.14.0). The `symbols-mcp` MCP server is the source of truth for framework rules, syntax, design system, audit playbook, generation prompts, and platform tools.

## Required workflow — every Symbols-related task

1. **Call `mcp__symbols-mcp__get_project_context` FIRST.** Walks up from cwd looking for `symbols.json`, returns owner/key/env_type/token_present and a `next_step` hint. Treat the next_step as authoritative. If owner / key / token is missing, surface a `🟢 ASK USER` block — NEVER hardcode.

2. **Before generating ANY component or page**, call `mcp__symbols-mcp__get_project_rules` once per session. Bundles FRAMEWORK + DESIGN_SYSTEM + RULES + DEFAULT_PROJECT (~180K chars) into one read.

3. **For new components/pages**, use `mcp__symbols-mcp__generate_component` / `mcp__symbols-mcp__generate_page` — these return a structured prompt + the right context.

4. **After each component**, run `mcp__symbols-mcp__audit_component(code)` to validate inline. Compact response (~1K) with violations.

5. **For full project audits**, run `mcp__symbols-mcp__audit_project()` to get the multi-phase playbook, pair with `npx -y @symbo.ls/mcp symbols-audit ./symbols` (the CLI), iterate until convergence per the playbook's strict-mode contract.

## Hard rules — every output must respect these

Full list lives in RULES.md (62 rules). Most-violated:

- **Flat element API.** Props at `el.X` (NEVER `el.props.X`). Events at `el.onClick` / `el.onInit` (NEVER `on: {}` wrapper). Reactive functions are `(el, s)` (NEVER `({ props, state })`).
- **Lowercase child keys NEVER render.** PascalCase only (e.g. `Heading`, not `h1`).
- **Auto-extend by key.** `Header: { extends: 'Navbar' }` should usually be `Navbar: {}`. Rename the wrapper key to match the component — DOMQL extends by key automatically. Multi-instance? Suffix with `_N`: `Navbar_1`, `Navbar_2`. Keep `extends:` only when (a) the wrapper carries genuinely distinct semantic meaning, (b) you need multi-base composition (`extends: ['Hgroup', 'Form']`), or (c) you're chaining a nested-child reference (`extends: 'AppShell > Sidebar'`).
- **Design-system tokens for ALL values.** NO raw px / hex / rgb / hsl / ms. The three sequence families — typography, spacing, timing — each generate their own values from `{ base, ratio }`. Same letter, **different values per family**: `fontSize: 'B'` ≠ `padding: 'B'` ≠ `transition: 'B'`. NO custom-named spacing tokens — only the generated sequence + sub-tokens (`A1`, `A2`, …).
- **Polyglot for every user-facing string.** Use `'{{ key | polyglot }}'` template (reactive) or `el.call('polyglot', 'key')` (imperative). **NO `t` or `tr` function exists** — only `polyglot`.
- **Declarative `fetch:` prop** (@symbo.ls/fetch). NEVER `window.fetch` / `axios` / SWR / TanStack Query in a component.
- **Helmet for metadata** (`metadata: { title, description, ... }`). NEVER `document.title = …` or `<head>` injection.
- **Router via `el.router(path, el.getRoot())`.** NEVER `window.location.*`.
- **Theme via `changeGlobalTheme()` from `smbls`.** NEVER `setAttribute('data-theme')` from project code.
- **Icons via `Icon` component referencing `designSystem.icons`.** `html: '<svg ...>'` is BANNED (Rule 62 — breaks theme color resolution, breaks Brender SSR, breaks sprite deduping). NEVER `tag: 'svg'`, NEVER `tag: 'path'`, NEVER `extends: 'Svg'` for an icon.
- **NO imports between project files.** Reference components by PascalCase key (auto-extends). Call functions via `el.call('fnName', …)`.
- **NO direct DOM manipulation.** No `document.querySelector` / `addEventListener` / `classList` / `innerHTML` / `setAttribute` / `el.node.style.X = …` / `parentNode` traversal. All structure goes through DOMQL declarative props.
- **HTML attributes are flat props**, not `attr: {…}` wrappers. `placeholder`, `type`, `name`, `value`, `disabled`, `title` go at the top level.
- **`extends`/`childExtends` are quoted strings.** NEVER inline objects.
- **Auto-extend by key**: if a component is named `Avatar`, just use `Avatar: {…}` — don't write `Avatar: { extends: 'Avatar' }`. Multiple instances → `Avatar_1`, `Avatar_2`.

## Auditing

When asked to audit, run:

```bash
npx -y @symbo.ls/mcp symbols-audit ./symbols
```

Strict + deep-fix + deep-framework-audit are ON by default. The CLI emits two reports:
- `audit/symbols_audit_results.md` — project findings + resolutions
- `audit/framework_audit_results.md` — framework bugs with repro + smbls/ trace

Then follow the `audit_project()` playbook for fix loop, build/publish, UI testing, and convergence iteration. **Strict mode = exhaustive: every finding ends as `resolved`, `framework_bug`, or `🟢 ASK USER`. Never silently skip a step. Never leave items as "Recommended follow-up" in the final report.**

## When in doubt

- **Search docs**: `mcp__symbols-mcp__search_symbols_docs(query)`.
- **Convert from React/HTML**: `mcp__symbols-mcp__convert_react(source)` / `convert_html(source)`.
- **CLI reference**: `mcp__symbols-mcp__get_cli_reference()`.
- **SDK reference**: `mcp__symbols-mcp__get_sdk_reference()`.

> If `symbols-mcp` is not registered in your MCP config, see the project's SETUP.md (or `npx @symbo.ls/mcp` to start the server). Without the MCP, every code suggestion is guesswork.
