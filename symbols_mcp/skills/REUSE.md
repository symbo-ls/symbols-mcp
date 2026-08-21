# 🧱 BUILT-IN COMPONENTS — REUSE, DO NOT REDEFINE (READ THIS BEFORE GENERATING)

Every Symbols project automatically inherits the catalog from `@symbo.ls/default-config` (see COMPONENTS.md + DEFAULT_COMPONENTS.md below). The catalog includes:

  • **Atoms**: `Block`, `Box`, `Flex`, `Grid`, `Hgroup`, `Img`, `Picture`, `Video`, `Iframe`, `Text`, `Form`, `Svg`, `Shape`, `Theme`, `InteractiveComponent`
  • **Components**: `Avatar`, `Button`, `Dialog`, `Dropdown`, `Link`, `Notification`, `Range`, `Select`, `Tooltip`, `Icon`, `Input`

## The auto-extend rule

DOMQL automatically extends a component when the key name matches a registered component. **`Avatar: {}` renders the built-in Avatar.** No `extends:` needed. Same for every other built-in.

```js
// ❌ WRONG — redefining a built-in from scratch
Avatar: {
  tag: 'div',
  borderRadius: 'A',
  Img: { src: '...' }
}

// ❌ WRONG — redundant `extends`
Avatar: { extends: 'Avatar', src: '...' }

// ✅ RIGHT — just use the bare key, override only what changes
Avatar: { src: '...' }

// ✅ Multi-instance — _N suffix
Avatar_1: { src: 'a.jpg' }
Avatar_2: { src: 'b.jpg' }
```

## The boundary — what IS overridable

**Components** = reuse, do NOT redefine. Override per-instance via props on the bare key.
**Design system** = MUST be customized for each brand — colors, typography (fonts, base, ratio), spacing (base, ratio), timing, themes (`@dark` / `@light` / custom). That's the entire point of a design system; per-project branding flows through `designSystem/` token files. See DESIGN_SYSTEM.md.

## When IS it OK to write a new component definition?

1. **The component genuinely doesn't exist in the catalog.** Search COMPONENTS.md / DEFAULT_COMPONENTS.md first. Use `mcp__symbols-mcp__search_symbols_docs` if unsure.
2. **The catalog component has the wrong primitive shape for your use case.** (Rare — most of the time you compose, override props, or use `childExtends`.)
3. **You need a project-specific composition** (e.g. `MemberCard` made of `Avatar` + `Text` + `Button`). Define the new component, but **its children should still be bare-key references to built-ins**: `MemberCard: { Avatar: {...}, Heading: {...}, Button: {...} }`.

If you redefine a built-in (e.g. write `Avatar: { tag: 'div', borderRadius: ..., ... }` from scratch), you (a) lose theme/SSR/sprite/a11y wiring already baked into the canonical version, (b) bypass the design-system contract, (c) duplicate code that updates centrally when the built-in is improved upstream. Don't do this unless you can articulate exactly why the catalog version is wrong for your case.

---

# 🔁 REUSE — 3-TIER SEARCH ORDER (SEARCH BEFORE CREATING)

Reuse is mandatory across THREE concentric tiers. Search in this order before defining anything new:

1. **Framework built-ins** (`@symbo.ls/default-config`) — every Symbols project automatically inherits the Atoms + Components catalog. See COMPONENTS.md / DEFAULT_COMPONENTS.md (bundled above).
2. **Shared libraries** linked via `sharedLibraries.js` at the project root. Most projects depend on `system/default` (the canonical default library, ~127 components covering common patterns) plus any org-specific library. Library files merge into `context.components` / `context.functions` at runtime. **READ-ONLY** — overwritten on every `smbls fetch` / `smbls sync`. Override by defining the same key in your local project (local always wins on collision).
3. **Current project** — `components/`, `snippets/`, `functions/`, `methods/`.

DOMQL's bare-key resolver walks all three tiers automatically — `Card: { ... }` works whether `Card` is a built-in, a shared-library export, or a local component. Reuse is free; the cost is in remembering to look first.

## Where shared libraries land on disk

Resolution depends on the project's `sharedLibrariesMode` field in `symbols.json`:

| Mode | Triggered by | Location |
|---|---|---|
| `npm` | Default for npm/bun/yarn/pnpm projects, or explicit `sharedLibrariesMode: 'npm'` | `node_modules/<package-name>/` (resolved via standard package resolution; `package-name` is whatever the entry in `sharedLibraries.js` imports as) |
| `local` | Browser/CDN setups, or explicit `sharedLibrariesMode: 'local'` | `.symbols_local/libs/<owner>/<key>/` (gitignored) |
| custom `destDir` | Per-entry override in `sharedLibraries.js` | Whatever path the entry's `destDir` points at (e.g. `../shared/brand`) |

Always start by reading `sharedLibraries.js` and `symbols.json` to see what's linked and where.

## The discovery loop (run BEFORE writing new code)

```bash
# 0. See what tier-2 libraries are linked + their resolution mode
cat sharedLibraries.js
grep -E 'sharedLibrariesMode|packageManager' symbols.json 2>/dev/null

# 1. Built-ins — see catalog (already in get_project_rules output above)

# 2a. Shared libraries — `local` mode
ls .symbols_local/libs/*/*/components/ 2>/dev/null
grep -rE '^export const [A-Z]' .symbols_local/libs/*/*/components/ 2>/dev/null | head -40

# 2b. Shared libraries — `npm` mode (resolve each sharedLibraries.js entry against node_modules)
# For each library `<pkg>` listed in sharedLibraries.js:
#   ls node_modules/<pkg>/components/  &&  grep -rE '^export const [A-Z]' node_modules/<pkg>/components/

# 3. Current project
grep -rE '^export const [A-Z]' components/ snippets/ | head -40
grep -rE '^export (const|function) ' functions/ methods/ | head -40

# 4. Semantic search across ALL tiers (built-ins via MCP docs + project + libs)
# Prefer mcp__symbols-mcp__search_symbols_docs(query) — searches all bundled skill docs.
```

## The reuse-vs-extract decision

| Situation | Action |
|---|---|
| Built-in or shared-library component covers your case | Reference by bare key: `Avatar: { ... }` — DOMQL auto-resolves |
| A library component covers ~80% but needs different visuals | Override the divergent props on the bare key — never copy the source |
| A library component is semantically close but not identical | `extends: 'LibComponent'` + add what's new in the local file |
| Existing local component covers your case | Reference by bare key |
| You're writing the SECOND near-duplicate (local) | Acceptable — but flag for refactor |
| You're writing the THIRD near-duplicate (local) | **STOP**. Extract the shared shape. |
| A pattern recurs across MULTIPLE projects in the org | Promote it to a shared library (separate concern; ask first) |

## When you find duplication, fix it inline

If you discover `UserCard.js`, `MemberCard.js`, `ProfileCard.js` with the same structure:

1. Check each tier first — does a built-in or shared-library component already cover this?
   If yes, the duplicates were the bug; replace all three with bare-key references to the
   library version.
2. Otherwise, lift the shared shape into ONE canonical component at `components/<Name>.js`.
3. Replace the duplicates with bare-key references + per-instance prop overrides.
4. Page wrappers call the canonical: `Card: { user: ... }` or `Card_1: {...}, Card_2: {...}`.
5. Delete the redundant files; their `index.js` re-exports auto-propagate the deletion.

## Functions — same 3-tier rule

Project functions register on `context.functions`. Shared libraries also contribute (e.g. `polyglot`, `currency`, common formatters from `system/default`). Before writing a new helper, check the same locations as for components — substitute `functions/` and `methods/` for `components/` in the discovery commands above. Resolution mode (`npm` vs `local` vs `destDir`) is identical to the component case.

If two pages compute the same thing inline, extract to `functions/<name>.js` and invoke via `el.call('name', …)`. NEVER copy logic between files; NEVER `import` between project files (FA001).

## Shared-library override pattern

When a shared-library component is *almost* right but needs a project-level tweak, override at the consumer level — local always wins on key collision:

```js
// <library-resolved-path>/components/Card.js  (READ-ONLY — never edit)
// → defines Card with default styling

// components/Card.js  (your project — overrides the library version)
export const Card = {
  extends: 'Card',                      // pull in the library's Card as the base
  borderRadius: 'C',                    // add your override
  background: 'brand'
}
```

Both consumers in the project still write `Card: {...}`; DOMQL resolves your local override
rather than the library version.

## Folder placement (frank-discovered slots)

- `components/` — reusable DOMQL components (the default for a new shared shape)
- `snippets/` — composable element fragments smaller than a full component
- `functions/` — pure / project-state helpers, called via `el.call('fn', …)`
- `methods/` — `this`-binding helpers (lifecycle utilities)

Anything outside the frank-discovered slots (`utils/`, `lib/`, `helpers/`) is silently dropped at publish time — see FA006. So 'extracting to a helper' MUST land in `functions/` or `methods/`, never `utils/`.

---
