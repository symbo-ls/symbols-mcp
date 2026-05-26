# Workspace — Multi-App Monorepos with Shared Libraries

**A workspace is a Symbols monorepo where multiple sibling apps share components, designSystem tokens, functions, and files** via the framework's `sharedLibraries` mechanism — without drift, duplication, or breaking the CLI's tooling guarantees.

This file documents the **workspace concept** (layout, project shapes, the two-file contract, transitive-resolution rules, onboarding checklist). The runtime mechanics of how libraries merge into a consuming app's context — input shapes, lockfile, `link` vs `destDir`, `sideEffects: true`, drift detection — live in [SHARED_LIBRARIES.md](./SHARED_LIBRARIES.md). Read both: workspace = the topology, shared-libraries = the merge engine that powers it.

---

## Layout

```
<workspace>/
  <shared-lib>/                 # flat library — pure shared code, no app entry
    context.js                  # entry (at root because dir is ".")
    components/
    designSystem/
    functions/
    files/
    package.json                # name: @<org>/<lib>, sideEffects: true, main: ./context.js
    symbols.json                # owner: <org>, key: <lib>, dir: "."

  <app-a>/                      # full app — runs standalone, can also be a shared library
    symbols/
      context.js                # entry (under symbols/ because dir is "./symbols")
      sharedLibraries.js        # runtime imports
      components/ pages/ functions/ designSystem/ ...
    package.json                # if consumed as a library: sideEffects: true, main: ./symbols/context.js
    symbols.json                # owner, key, dir: "./symbols", sharedLibraries declarations

  <app-b>/                      # …another full app
  <app-c>/
```

---

## Two project shapes (this drives every other rule)

A workspace mixes two project shapes — and the `dir` field in `symbols.json` is what distinguishes them. **Get this wrong and import paths break.**

| Shape | `symbols.json` `dir` | `context.js` location | Has `pages/` | Runs standalone | Can also be consumed as a library |
|---|---|---|---|---|---|
| **Flat library** | `"."` | project root | No | No | Yes — its sole purpose |
| **Full app** | `"./symbols"` | `<app>/symbols/context.js` | Yes | Yes | Yes (if exposed via `package.json`) |

**Why this matters at the workspace level:**

- `sharedLibraries.js` imports the target's `context.js`. The path differs by shape:
  - Flat library target → `import lib from '../<lib>/context.js'`
  - Full-app target → `import lib from '../<app>/symbols/context.js'`
- `smbls libs link` reads the target's `symbols.json` to compute the right import path. Pre-3.14.35 CLI ignored `dir` and hardcoded `<targetRoot>/context.js`, which broke full-app-as-library consumers and caused false drift in `smbls libs status`. **Upgrade `@symbo.ls/cli` to 3.14.35+ if you see drift on full-app library consumers.**

---

## The two-file contract — both files must agree

Every consuming app keeps shared-library config in **two files**. They have different jobs and `smbls libs status` enforces they don't drift.

### 1. `<app>/symbols.json` — declarative manifest

What the project depends on, plus how to source it. Read by the CLI, the lockfile, the publish pipeline.

```json
{
  "owner": "<org>",
  "key": "<app>",
  "dir": "./symbols",
  "version": "1.0.0",
  "packageManager": "esm.sh",
  "sharedLibraries": {
    "system/default":        { "link": "../<shared-lib>" },
    "<other-org>/<lib-key>": { "link": "../../<other-shared-lib>" }
  }
}
```

- **No `bundler` field by default** — Symbols projects run via symbols-runner, which resolves the bundler automatically. Only add `"bundler": "parcel"` (or `"vite"`) for an app that genuinely needs that pipeline (e.g. the `workspace/` shell). Do not re-add it to a `symbols.json` if a tool drops it.
- Keys use `owner/key` format. Default owner is `system` (so `default` and `system/default` are equivalent).
- `link:` paths are relative to **the consuming app's project root**. They point at the **target's project root**, not its `symbols/` subdir. (The CLI reads the target's `symbols.json` to figure out the actual `context.js` path inside.)
- Four supported input shapes — see SHARED_LIBRARIES.md "Configuration" for the full normalization table.

### 2. `<app>/symbols/sharedLibraries.js` — runtime wiring

What gets imported at app boot and merged into the app's context. The runtime authority — DOMQL only sees what this file exports.

```js
import defaultLib from '../../<shared-lib>/context.js'
import otherLib   from '../../../<other-shared-lib>/symbols/context.js'

export default [defaultLib, otherLib]
```

- Imports the target's `context.js` directly. Path shape depends on whether the target is a flat library or a full app (see the table above).
- Order matters at merge time — earlier entries win on conflicting keys (after the app's own keys, which always win — see SHARED_LIBRARIES.md "Runtime Merge").
- **Canonical shape only** — `import` lines + one `export default [...]`. Anything else makes the CLI refuse to regenerate the file without `--force` (a safety guard against losing hand edits).

### Why both?

Runtime only needs the JS file. CLI tooling needs the JSON declaration to manage versions, lockfile state, drift detection, and cloud sync. Keep them in lockstep — `smbls libs status` will tell you when they drift.

---

## No transitive resolution — each consumer declares every dep directly

The shared-library merger does **not** recurse. If `<lib-A>` lists `system/default` in its own `sharedLibraries.js`, but `<consumer>` (which uses `<lib-A>`) doesn't list `system/default` directly, then `<consumer>` won't get `system/default`'s components through `<lib-A>`.

**Always declare every dep directly in each consumer.** This is verbose but keeps merge order explicit and avoids hidden coupling. If three apps in a workspace all depend on `system/default` + `acme/brand`, all three must list both.

---

## Adding a new shared dep — the canonical CLI flow

Don't hand-edit. Use the CLI — it writes both files in lockstep, updates the lockfile, and runs cloud sync if applicable.

```bash
# Link a sibling project as a shared library
cd <consumer>
smbls libs link ../<sibling>
# → updates symbols.json sharedLibraries entry with mode "linked"
# → adds canonical import to symbols/sharedLibraries.js (resolving target's dir field)
# → records mode: "linked" in .symbols_local/lock.json

# Add a cloud-sourced library
smbls libs add system/landing@1.2.0
# → declares it in symbols.json
# → fetches into .symbols_local/libs/system--landing/
# → adds import to symbols/sharedLibraries.js

# Inspect current state + drift
smbls libs status

# Remove
smbls libs remove <owner>/<key>   # works for both linked and cloud
smbls libs unlink <owner>/<key>   # explicit unlink (linked entries)
```

When in doubt, run `smbls libs status` — it's the source of truth on whether the two files agree.

---

## Runtime resolution — 3-tier search order (within a workspace)

DOMQL's bare-key resolver walks (highest priority first):

1. **App-local** — `<app>/symbols/components/`, `snippets/`, `functions/`, `methods/`, etc. **Always wins on collision.**
2. **Shared libraries** — entries in `sharedLibraries.js`, in declaration order (first entry wins among libraries).
3. **Framework built-ins** — `@symbo.ls/default-config` (Atoms: `Block`, `Box`, `Flex`, `Grid`, `Hgroup`, `Img`, `Picture`, `Video`, `Iframe`, `Text`, `Form`, `Svg`, `Shape`, `Theme`, `InteractiveComponent`. Components: `Avatar`, `Button`, `Dialog`, `Dropdown`, `Link`, `Notification`, `Range`, `Select`, `Tooltip`, `Icon`, `Input`). Always present, never need to be declared.

So `Card: { src: '...' }` works whether `Card` is defined in the app, in a shared lib, or as a built-in. The merger fills `undefined` slots only — never overwrites an app-defined key. `designSystem` uses `deepDefaults` (recursive fill of nested gaps). See SHARED_LIBRARIES.md "Runtime Merge" for the full algorithm.

**Before defining ANY new component, snippet, or function** (Rule 63 — REUSE BEFORE CREATING):

```bash
# Tier 1 — framework built-ins
# (See COMPONENTS.md + DEFAULT_COMPONENTS.md catalog)

# Tier 2 — shared libraries (use this workspace's actual paths)
ls ../<shared-lib>/components/
ls ../<other-app>/symbols/components/

# Tier 3 — current project
grep -rE '^export const [A-Z]' components/ snippets/
grep -rE '^export (const|function) ' functions/ methods/
```

If a built-in or shared-lib component covers ~80% of your case, **reference it by bare key and override differing props locally**. Don't redefine the name — that silently shadows the canonical version and breaks every other consumer (the most-violated rule in any Symbols codebase).

---

## Override pattern — never edit shared source

Shared library files are **read-only from the consumer's perspective**:

- **Cloud-fetched libraries** — `.symbols_local/libs/` is overwritten on every `smbls fetch`. Edits are lost.
- **Linked sibling libraries** — owned by their own project. Editing them from the consumer breaks separation of concerns and silently changes behavior for every other app linking the same library.

To customize a shared component for one app, define it locally — the merger picks the local version:

```js
// <consumer>/symbols/components/Card.js
export const Card = {
  extends: 'Card',                  // pulls in the shared-library Card as base
  borderRadius: 'A2',               // override just the props you need
  '@dark': { background: 'gray.9' }
}
```

The local `Card` now wins for this app only. Other apps in the workspace still get the shared-library `Card` untouched.

---

## Apps consumed as shared libraries — `sideEffects: true` is required

When a full-app project is consumed as a shared library AND its components are referenced only by bare-key DOMQL lookup at runtime (e.g. `Foo: {}` somewhere in the consumer's tree), Parcel's tree-shaker may strip the export because static analysis can't prove it's used. Symptom: an empty `<div data-key="Foo">` with no class, no children, no merged props.

Fix: every shared-library project root needs:

```json
{
  "name": "@<org>/<lib>",
  "type": "module",
  "main": "./symbols/context.js",   // or "./context.js" for flat libraries
  "sideEffects": true,
  ...
}
```

After adding, do a full Parcel restart on every consumer:

```bash
rm -rf .parcel-cache dist
# restart dev server
```

See SHARED_LIBRARIES.md "Parcel tree-shaking" for the deeper explanation.

---

## Known gotchas (workspace-specific)

- **`destDir` is a footgun in a workspace** — never point `destDir` at a real source folder (e.g. a sibling app). `smbls fetch` overwrites with `overwrite: true`. Use `link:` for sibling sources, plain cloud entries (no `destDir`) for everything else.

- **`sharedLibraries.js` deviating from canonical shape** — if you hand-edit imports beyond `import name from 'spec'` + `export default [...]`, the CLI refuses to regenerate without `--force`. This is a safety guard against losing hand-maintained custom wiring. To go back to canonical, simplify the file or pass `--force` once.

- **No transitive resolution** — every consumer must declare every dep directly. See section above.

- **Built-ins beat nothing, app beats everything** — local definitions silently shadow built-ins and shared-library entries. If a built-in or library `Avatar` works almost right, `extends: 'Avatar'` to customize. Don't redefine the bare key with a fresh implementation — that breaks every other consumer that expected the canonical behavior.

- **Pre-3.14.35 CLI ignored target's `dir` field** — hardcoded `<targetRoot>/context.js` for import-spec generation. For full-app shared libraries (`dir: "./symbols"`), this caused false `smbls libs status` drift and broken `smbls libs link`. Fixed in `@symbo.ls/cli@3.14.35`. Upgrade if you see drift on full-app library consumers.

---

## Summary checklist — adding a new app to a workspace

1. Scaffold the project (`smbls create <app>` or hand-create with the right `symbols.json`).
2. Link each shared library you need:
   ```
   cd <app>
   smbls libs link ../<shared-lib-1>
   smbls libs link ../<shared-lib-2>
   ```
3. `smbls libs status` → verify `✓ in sync`.
4. Confirm `package.json` has `"type": "module"`. Add `"sideEffects": true` and `"main": "./symbols/context.js"` only if this app will itself be consumed as a shared library by another app in the workspace.
5. Use bare-key references in components — don't redefine built-ins or shared-library exports.
6. `smbls start` to develop.

---

## Cross-references

- [SHARED_LIBRARIES.md](./SHARED_LIBRARIES.md) — the merge engine: input shapes, lockfile, runtime merge algorithm, `link` vs `destDir` semantics, `sideEffects: true` mechanics, `smbls libs` command reference, drift detection internals.
- [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) — single-project layout (frank-discovered folders, file conventions).
- [CLI.md](./CLI.md) — full CLI reference including `smbls libs` subcommands.
- [COMPONENTS.md](./COMPONENTS.md) + [DEFAULT_COMPONENTS.md](./DEFAULT_COMPONENTS.md) — Tier 1 catalog (framework built-ins to reuse before defining anything).
