---
name: symbols
description: Symbols platform + DOMQL v3.14 framework skill. Use when working in a Symbols project (a directory tree containing symbols.json), writing or editing DOMQL components/pages/design-system tokens, using the smbls CLI (start, build, push, publish), converting React/HTML to DOMQL, or auditing frankability. Routes all framework knowledge through the symbols-mcp tools instead of memory.
---

# Symbols / DOMQL

Symbols projects are plain-object DOMQL declarations compiled and served by the
platform. **Never write Symbols/DOMQL code from memory** — the framework moves
fast and violations fail silently (blank page, dropped styles). Always verify
against the live rules via the `symbols-mcp` MCP server.

## Must-do sequence (every Symbols task)

1. `mcp__symbols-mcp__get_project_context` — resolves owner/key/env from `symbols.json`. Run FIRST.
2. `mcp__symbols-mcp__get_project_rules` — the full live ruleset (framework, design system, components, frankability). Load BEFORE generating or editing.
3. `mcp__symbols-mcp__generate_component` / `generate_page` — for new code.
4. `mcp__symbols-mcp__audit_component` — after each component you write.
5. `mcp__symbols-mcp__audit_and_fix_frankability` — before committing.

If the symbols-mcp server is not connected, say so and ask to add it
(`uvx --refresh symbols-mcp` in the client's MCP config) rather than guessing.

## Hard rules digest (v3.14)

- Components are **plain objects** — never functions or classes. No imports
  between project files: reference components by PascalCase key, call project
  functions via `el.call('fnName', ...)`.
- **Flat access:** `el.X` never `el.props.X`; `onClick`/`onInit` handlers at the
  top level, never `on: { click }`. HTML attributes (`placeholder`, `type`,
  `value`, `disabled`, …) are top-level props — no `attr: {}` wrapper.
- **Design tokens only** — no raw px/rem/hex when a token exists. Design-system
  keys are lowercase (`color`, `theme`, `typography`). Color shading uses
  modifiers (`'blue.7'`, `'gray+50'`).
- Reuse before creating: framework built-ins (Avatar, Button, Dialog, Icon,
  Input, Flex, Grid, …) and shared libraries resolve by bare key — check all
  three tiers before defining anything new; a duplicate name silently shadows
  the original.
- Navigation via `el.router(path, el.getRoot())` — never `window.location`.
  Collections via `children` + `childExtends` — never `$collection`.
- Frank-discovered folders only: `components/ snippets/ pages/ functions/
  methods/ designSystem/ files/ assets/` — anything else is dropped at publish.
- Signature is `(el, s)` — no destructuring. Handler helpers as `const x = () =>`
  arrow consts. Dynamic `await import('pkg')` inside handlers, never top-level.

## CLI quick reference

- `smbls start` — dev server for the current project
- `smbls build` — static build (IIFE runtime + project JSON)
- `smbls push` / `smbls publish` — save a version / make it live on the platform
- `smbls claude` — start the s1m0ne Bridge (local agent behind Symbols chat surfaces)
- `npx -y @symbo.ls/mcp init-rules` — (re)install these rules + skills for every detected agent

## Where the full docs live

`get_project_rules` returns everything (rules, framework model, design-system
contract, component catalog, frankability FA-rules). For targeted lookups use
`mcp__symbols-mcp__search_symbols_docs`. Human docs: https://docs.symbols.app
