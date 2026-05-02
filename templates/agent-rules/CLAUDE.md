# Symbols.app project — agent rules

This is a Symbols.app / Symbols project (smbls 3.14.0). The `symbols-mcp` MCP server is the source of truth for framework rules, syntax, design system, audit playbook, generation prompts, and platform tools.

> **Claude Code: this project ships hooks** at `.claude/settings.json` that BLOCK Edit/Write on any `*.js` until you call `mcp__symbols-mcp__get_project_rules` (or `get_project_context`). The block is enforced by the harness — there is no way to skip it from inside the conversation. Just call the tool first.

## MUST-DO sequence (numbered — follow in order)

1. **Call `mcp__symbols-mcp__get_project_context` FIRST.** Walks up from cwd looking for `symbols.json`, returns owner/key/env_type/token_present and a `next_step` hint. Treat the next_step as authoritative. If owner / key / token is missing, surface a `🟢 ASK USER` block — NEVER hardcode.

2. **Before generating ANY component or page**, call `mcp__symbols-mcp__get_project_rules` once per session. Bundles FRAMEWORK + DESIGN_SYSTEM + RULES + DEFAULT_PROJECT (~180K chars) into one read.

3. **For new components/pages**, use `mcp__symbols-mcp__generate_component` / `mcp__symbols-mcp__generate_page` — these return a structured prompt + the right context.

4. **After each component**, run `mcp__symbols-mcp__audit_component(code)` to validate inline. Compact response (~1K) with violations.

5. **For full project audits**, run `mcp__symbols-mcp__audit_project()` to get the multi-phase playbook, pair with `npx -y @symbo.ls/mcp symbols-audit ./symbols` (the CLI), iterate until convergence per the playbook's strict-mode contract.

6. **Before committing**, run `mcp__symbols-mcp__audit_and_fix_frankability(symbols_dir, mode='safe-fix')` — this catches FA0xx–FA5xx violations that break frank.toJSON serialization (silent prod-only bugs). The PostToolUse hook also runs an inline FA-rule check on every `*.js` you edit; fix flagged items before continuing.

## Frankability — code that survives `frank.toJSON`

Local dev resolves identifiers via JS module closures; the deployed payload doesn't. A handler that compiles and renders right locally can silently render wrong values in prod. The full ruleset is in `mcp__symbols-mcp__get_project_rules` (FRANKABILITY section). Most-violated:

- **FA001** — no sibling-imports between project files; use `el.call('fnName', …)` or PascalCase key refs
- **FA206** — npm packages used in handlers must be `await import('pkg')` inside the handler, NEVER top-level `import`
- **FA207** — nested helpers inside handlers must be `const x = () => {}`, NEVER `function x () {}` (esbuild hoists + frank promotes, stripping the closure)
- **FA208** — `globalScope.js` must NOT cross-import from peer modules (esbuild dedup-rename → `__scope.X2 is not a function` at runtime)
- **FA209** — `dependencies.js` is the runtime importmap, NOT a build-time manifest (build-time tools 404 from esm.sh)
- **FA210** — bypass-mode / mock-auth handlers MUST guard `el.node` and optional-chain `s.parent?.x` / `s.root?.x`
- **FA513** — `window.update(...)` / `document.update(...)` is banned (declare `onScroll` on the element instead)
- **FA514** — module-side-effect bridges (`window.__projectInit = …`) are stripped by frank; use bare references

Run `mcp__symbols-mcp__explain_frankability_rule('FA207')` for any FA-id when unsure.

## 🧱 Built-in components — REUSE, do NOT redefine

Every Symbols project automatically inherits the catalog from `@symbo.ls/default-config`. DOMQL auto-extends by key name, so just writing the bare key renders the built-in:

```js
// ✅ Renders the canonical Avatar from @symbo.ls/default-config
Avatar: { src: 'me.jpg' }

// ✅ Multi-instance — _N suffix
Avatar_1: { src: 'a.jpg' }
Avatar_2: { src: 'b.jpg' }

// ❌ Redefining from scratch — loses theme/SSR/sprite/a11y wiring
Avatar: { tag: 'div', borderRadius: 'A', Img: { src: '...' } }

// ❌ Redundant `extends`
Avatar: { extends: 'Avatar', src: 'me.jpg' }
```

**The built-in catalog:**
- **Atoms:** `Block`, `Box`, `Flex`, `Grid`, `Hgroup`, `Img`, `Picture`, `Video`, `Iframe`, `Text`, `Form`, `Svg`, `Shape`, `Theme`, `InteractiveComponent`
- **Components:** `Avatar`, `Button`, `Dialog`, `Dropdown`, `Link`, `Notification`, `Range`, `Select`, `Tooltip`, `Icon`, `Input`

Read `mcp__symbols-mcp__get_project_rules` — it bundles `COMPONENTS.md` (catalog + when to override) and `DEFAULT_COMPONENTS.md` (full source/structure of every built-in). When you need an unfamiliar built-in's prop surface, that's where to look.

**The boundary:**
- **Components → reuse, never redefine.** Override per-instance via props on the bare key.
- **Design system → MUST be branded per project.** Colors, typography (fonts, base, ratio), spacing (base, ratio), timing, themes (`@dark` / `@light` / custom) all flow through `designSystem/` token files. Built-ins consume those tokens automatically. Editing the design system to match the brand is the normal flow.

**When IS it OK to write a new component definition?**
1. The component genuinely doesn't exist in the catalog (search first via `mcp__symbols-mcp__search_symbols_docs`).
2. You need a project-specific composition (e.g. `MemberCard` = `Avatar` + `Heading` + `Button`). Define the wrapper, but its children must still be bare-key references to built-ins.

If you redefine a built-in (write `Avatar: { tag: 'div', ... }`), you (a) lose theme/SSR/sprite/a11y wiring, (b) bypass the design-system contract, (c) duplicate code that updates centrally upstream. Don't.

---

## 🔁 Reuse — 3-tier search order

Reuse is mandatory across THREE concentric tiers. Search in this order before defining anything new:

1. **Framework built-ins** (`@symbo.ls/default-config`) — Atoms + Components catalog (covered above; full reference in COMPONENTS.md / DEFAULT_COMPONENTS.md).
2. **Shared libraries** linked via `sharedLibraries.js` at the project root. Most projects depend on `system/default` (the canonical default library, ~127 components covering common patterns) plus any org-specific library. Library files merge into `context.components` / `context.functions` at runtime. **READ-ONLY** — overwritten on every `smbls fetch` / `smbls sync`. To override, define the same key in your local project (local always wins on collision).
3. **Current project** — `components/`, `snippets/`, `functions/`, `methods/`.

DOMQL's bare-key resolver walks all three tiers automatically — `Card: { ... }` works whether `Card` is a built-in, a shared-library export, or a local component.

### Where shared libraries land on disk

Resolution depends on the project's `sharedLibrariesMode` field in `symbols.json`:

| Mode | Triggered by | Location |
|---|---|---|
| `npm` | Default for npm/bun/yarn/pnpm setups, or explicit `sharedLibrariesMode: 'npm'` | `node_modules/<package-name>/` (resolved via standard package resolution; `package-name` is whatever the entry in `sharedLibraries.js` imports as) |
| `local` | Browser/CDN setups, or explicit `sharedLibrariesMode: 'local'` | `.symbols_local/libs/<owner>/<key>/` (gitignored) |
| custom `destDir` | Per-entry override in `sharedLibraries.js` | Whatever path the entry's `destDir` points at |

Always start by reading `sharedLibraries.js` and `symbols.json` to see what's linked and where.

### Discovery loop (run BEFORE writing new code)

```bash
# 0. What's linked + how is it resolved?
cat sharedLibraries.js
grep -E 'sharedLibrariesMode|packageManager' symbols.json

# 1. Built-ins — see catalog above (no grep needed)

# 2a. Shared libraries — `local` mode
ls .symbols_local/libs/*/*/components/ 2>/dev/null
grep -rE '^export const [A-Z]' .symbols_local/libs/*/*/components/ 2>/dev/null | head -40

# 2b. Shared libraries — `npm` mode (substitute each sharedLibraries.js entry)
# ls node_modules/<pkg>/components/
# grep -rE '^export const [A-Z]' node_modules/<pkg>/components/

# 3. Current project
grep -rE '^export const [A-Z]' components/ snippets/ | head -40
grep -rE '^export (const|function) ' functions/ methods/ | head -40

# 4. Semantic search across all tiers
# Prefer mcp__symbols-mcp__search_symbols_docs(query) — it searches the bundled catalogs.
```

### Reuse-vs-extract decision

| Situation | Action |
|---|---|
| Built-in or shared-library component covers your case | Bare-key reference: `Avatar: { ... }` — DOMQL auto-resolves |
| A library component covers ~80% but needs different visuals | Override the divergent props on the bare key — never copy the source |
| A library component is semantically close but not identical | `extends: 'LibComponent'` in your local file + add what's new |
| Existing local component covers your case | Bare-key reference |
| You're writing the SECOND near-duplicate (local) | Acceptable — but flag for refactor |
| You're writing the THIRD near-duplicate (local) | **STOP. Extract the shared shape.** |
| A pattern recurs across MULTIPLE projects in the org | Promote to a shared library (separate concern; ask first) |

### When you find duplication, fix it inline

If `UserCard.js`, `MemberCard.js`, `ProfileCard.js` have the same structure:

1. Check tiers 1+2 — does a built-in or shared-library component already cover this? If yes, the duplicates were the bug; replace all three with bare-key references to the library version.
2. Otherwise, lift the shared shape into ONE canonical `components/<Name>.js`.
3. Replace the duplicates with bare-key references + per-instance overrides.
4. Pages call the canonical: `Card_1: {...}, Card_2: {...}`.
5. Delete the redundant files (their `index.js` re-exports auto-propagate).

### Shared-library override pattern

When a library component is *almost* right but needs a project tweak, override at the consumer level — never edit the library file:

```js
// <resolved-library-path>/components/Card.js  (READ-ONLY)

// components/Card.js  (your project — overrides the library version)
export const Card = {
  extends: 'Card',         // pull in the library's Card as the base
  borderRadius: 'C',       // add your override
  background: 'brand'
}
```

Both consumers still write `Card: {...}`; DOMQL resolves your local override rather than the library version.

### Functions — same 3-tier rule

If two pages compute the same thing inline, extract to `functions/<name>.js` and invoke via `el.call('name', …)`. NEVER copy logic between files; NEVER `import` between project files (FA001). Library functions also register on `context.functions` — check the library before writing a new helper.

### Folder placement (frank-discovered slots — files outside these are silently dropped at publish)

- `components/` — reusable DOMQL components (default for a new shared shape)
- `snippets/` — composable element fragments smaller than a full component
- `functions/` — pure / project-state helpers, called via `el.call('fn', …)`
- `methods/` — `this`-binding helpers (lifecycle utilities)

Never `utils/`, `lib/`, `helpers/` — those folders aren't in frank's discovery list (FA006), so anything in them is invisible to the published bundle even though it works locally.

---

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
