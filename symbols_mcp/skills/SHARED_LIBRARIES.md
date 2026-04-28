# sharedLibraries

sharedLibraries allows projects to inherit components, functions, methods, state, designSystem, pages, files, snippets, and dependencies from external library projects. Libraries are merged into the consuming app's context at runtime — no manual re-exports needed.

**CRITICAL: When shared libraries are fetched from the platform, both `sharedLibraries.js` and `.symbols_local/libs/` folders are strictly READONLY — they are overwritten on every `smbls fetch`/`smbls sync`.** To override shared library components, define them in your local project files (app always wins).

`sharedLibraries.js` can be manually edited for custom linking to local folders (advanced use case), but fetched content must never be modified.

---

## Parcel tree-shaking — shared components need `sideEffects: true`

When a shared-package component is referenced ONLY by DOMQL string-key lookup at runtime (e.g. `AppAssistant: {}` at the app root), Parcel's tree-shaker may strip the component because the static analysis can't prove the export is used. Symptom: an empty `<div data-key="Foo"></div>` with no class, no children, no merged props.

Fix: put a `package.json` at the root of any shared-package directory with `"sideEffects": true`.

```json
{
  "name": "@symbo.ls/editor-shared",
  "version": "3.14.0",
  "private": true,
  "type": "module",
  "main": "./context.js",
  "sideEffects": true
}
```

After adding, do a full Parcel restart on every downstream app: `rm -rf .parcel-cache dist`, then respawn the dev server so the module graph re-analyzes under the new flag. See RULES.md Rule 57 for defense-in-depth (inlining positioning props at the consumer site).

---

## Key Format: `owner/key`

All shared library identifiers use the `owner/key` format. Default owner is `system`.

| Input | Normalized |
|---|---|
| `system/default` | `system/default` |
| `default` | `system/default` |
| `default.symbo.ls` | `system/default` (deprecated) |
| `myorg/mylib` | `myorg/mylib` |

The `.symbo.ls` suffix is deprecated and stripped automatically.

---

## Configuration

### symbols.json

Four supported input shapes (all normalize to a canonical entry shape):

```json
// 1. Array of strings (owner/key or bare key) — cloud, latest
"sharedLibraries": ["system/default", "system/landing"]

// 2. Object key:version — cloud, pinned
"sharedLibraries": { "system/default": "1.0.0" }

// 3. Object key:config (cloud) — version + optional destDir for scaffold relocation
"sharedLibraries": { "system/default": { "version": "1.0.0", "destDir": "./custom" } }

// 4. Object key:config (linked) — point at a sibling source-of-truth folder
"sharedLibraries": { "acme/brand": { "link": "../brand" } }
```

All formats normalize keys to `owner/key` via `normalizeLibraryKey()`.

`normalizeSharedLibrariesConfig` returns entries shaped:

```js
{ key, version, link, destDir, mode }
// mode = 'linked'  when `link` is set
// mode = 'cloud'   otherwise
```

### `link` vs `destDir` (load-bearing distinction)

| Field | Semantic | Behavior in `scaffoldSharedLibraries` |
|---|---|---|
| `link: "../brand"` | "Use this folder as the source. Never scaffold over it." | **Skipped** — `toFS` is never called for this entry. The runtime imports from the link target. |
| `destDir: "../brand"` | "Scaffold the cloud payload to this folder instead of the default." | Scaffolds with `overwrite: true` — **clobbers contents on every fetch**. |

`destDir` was the only option historically. It has a real footgun: pointing it at a real source folder will overwrite that folder. **Use `link` for sibling-project workflows.** `destDir` remains supported for relocating the scaffold target to a custom local path.

### Lockfile (`.symbols_local/lock.json`)

| Field | Set by | Purpose |
|---|---|---|
| `sharedLibraryVersions: { "<key>": "<version>" }` | `smbls fetch` | Skip re-scaffold when version unchanged |
| `sharedLibraryModes: { "<key>": "linked" \| "cloud" }` | `smbls libs link/add/remove` | Tell `fetch` which entries are user-owned and must be left alone |
| `pulledAt`, `etag`, `projectId`, `version`, `branch` | `smbls fetch` | Snapshot metadata |

### sharedLibraries.js (auto-generated on fetch/sync)

The CLI generates this file automatically after `smbls fetch`/`smbls sync`:

```js
import systemDefault from '../.symbols_local/libs/system--default/context.js'

export default [systemDefault]
```

This file is overwritten on every fetch/sync. To customize behavior, override components/state/designSystem in your local project files instead.

### File Structure After Fetch

Directory names use `owner--key` format (double dash separator):

```
.symbols_local/libs/
  system--default/        # owner--key directory convention
    context.js
    components/
    designSystem/
    ...
```

The `owner--key` directory convention matches mermaid hosting URLs (`key--owner.preview.symbols.app`).

### context.js

The `sharedLibraries` array is included in the context export:

```js
import sharedLibraries from './sharedLibraries.js'
import * as components from './components/index.js'
import * as functions from './functions/index.js'
// ...

export default {
  sharedLibraries,
  components,
  functions,
  // ...
}
```

---

## Runtime Merge

### Entry Point

`smbls/src/createDomql.js:42-44`:

```js
if (context.sharedLibraries && context.sharedLibraries.length) {
  prepareSharedLibs(context)
}
```

This runs early in context initialization, **before** designSystem, state, components, and pages are prepared.

### Merge Logic

`smbls/src/prepare.js`:

```js
export const prepareSharedLibs = (context) => {
  const sharedLibraries = context.sharedLibraries
  for (let i = 0; i < sharedLibraries.length; i++) {
    const sharedLib = sharedLibraries[i]
    for (const key in sharedLib) {
      if (isObject(sharedLib[key]) && isObject(context[key])) {
        if (key === 'designSystem') {
          deepDefaults(context[key], sharedLib[key])
        } else {
          for (const k in sharedLib[key]) {
            if (!(k in context[key])) context[key][k] = sharedLib[key][k]
          }
        }
      } else if (!(key in context)) {
        context[key] = sharedLib[key]
      }
    }
  }
}
```

**The app ALWAYS wins.** Shared libraries only fill in missing keys (`!(k in context[key])`). designSystem uses `deepDefaults` which fills nested gaps while preserving all local values.

### deepMerge Behavior

`smbls/packages/utils/object.js:61-76`:

```js
export const deepMerge = (element, extend, excludeFrom = METHODS_EXL) => {
  for (const e in extend) {
    if (_startsWithDunder(e)) continue       // skip __private
    if (excludeFrom.includes(e)) continue    // skip excluded keys
    const elementProp = element[e]
    const extendProp = extend[e]
    if (isObjectLike(elementProp) && isObjectLike(extendProp)) {
      deepMerge(elementProp, extendProp, excludeFrom)  // recursive
    } else if (elementProp === undefined) {
      element[e] = extendProp  // only fill undefined slots
    }
  }
  return element
}
```

Key rules:
- **App always wins** — only merges when the app property is `undefined`
- Skips `__` prefixed properties
- Recursively merges nested objects
- Skips METHODS_EXL keys: `node`, `context`, `extends`, `__element`, `__ref`, and all element/state/props methods

---

## Order of Precedence

Libraries are processed sequentially. First library fills undefined slots, second fills remaining, etc.

```
App's own context  (highest priority — never overwritten)
  ↑
sharedLibraries[0]  (fills undefined slots)
  ↑
sharedLibraries[1]  (fills remaining undefined slots)
  ↑
UIKit atoms         (lowest priority, applied in prepareComponents)
```

After all merges, `prepareComponents` applies:

```js
// smbls/src/prepare.js:51-55
export const prepareComponents = (context) => {
  return context.components
    ? { ...UIkitWithPrefix(), ...context.components }
    : UIkitWithPrefix()
}
```

So the final component resolution is: **App > Shared Libraries > UIKit**

---

## What Gets Merged

| Merged | Not Merged (METHODS_EXL) |
|--------|--------------------------|
| components | node |
| functions | context |
| methods | extends |
| snippets | __element, __ref |
| pages / routes | Element methods (set, reset, update, remove, lookup...) |
| state | State methods (parse, create, destroy, toggle...) |
| designSystem | Props methods |
| files | Properties starting with `__` |
| dependencies | |
| dependenciesOnDemand | |
| utils, cases, plugins | |

---

## CLI Integration

### Project Creation

```bash
smbls create my-app                           # Default: adds system/default + fetches
smbls create my-app --blank-shared-libraries  # Blank: no shared libraries, skips fetch
```

When creating with default libraries:
1. Project is created on the platform
2. `system/default` library is attached via API
3. Local files are scaffolded
4. `smbls fetch` runs to pull library data into `.symbols_local/libs/`

### Library Management

Two command groups:

**`smbls libs ...`** (top-level, prefer this for new flows) — edits BOTH `symbols.json` AND `sharedLibraries.js` in lockstep, plus best-effort cloud project record sync when authed:

```bash
smbls libs status                       # Show declared libs, JS imports, drift
smbls libs link ../brand                # Link a sibling project as a shared library
smbls libs unlink acme/brand            # Remove a linked entry
smbls libs add system/default           # Add cloud lib + run fetch + cloud sync
smbls libs add system/default@1.2.0     # Pinned version
smbls libs remove default               # Remove (cloud or linked)
smbls libs list                         # Mode-aware (linked/cloud)
```

**`smbls project libs ...`** (legacy, cloud-only) — manipulates the cloud project record only; relies on a follow-up `smbls fetch` to update local files:

```bash
smbls project libs available          # List all available libraries (shows owner/key)
smbls project libs list               # List libraries linked to current project
smbls project libs add system/default # Add by owner/key (cloud project record)
smbls project libs add default        # Bare key → system/default
smbls project libs remove default     # Remove library (cloud project record)
```

The new top-level commands are a strict superset.

### Drift detection

`smbls libs status` compares `symbols.json.sharedLibraries` against `sharedLibraries.js` by **library slug** (the last segment of `owner/key`, or the leaf directory of an import path before `/context.js`). This survives the historical inconsistency where `destDir` paths and JS import paths don't always resolve identically (especially when `dir: "."` rather than a `symbols/` subfolder).

Reports:
- Declared libs that aren't imported (`missingFromJs`)
- Imports that aren't declared, when they look like local relative paths (`missingFromJson`) — cloud paths under `.symbols_local/libs/` are excluded
- Whether the JS file is in canonical shape

### sharedLibraries.js — canonical shape

```js
import brand from '../brand/context.js'
import shared from '../shared/context.js'

export default [brand, shared]
```

Anything else (extra exports, side-effect statements, atypical comment placement) is "non-canonical" and the CLI parser refuses to regenerate without `--force`. A non-canonical file is a strong signal that someone hand-edited it intentionally — overwriting silently would lose work.

The `marketplace` and `canvas` packages in the editor workspace currently have non-canonical, hand-managed `sharedLibraries.js` files because the cloud `symbols.json.sharedLibraries` declarations don't match the actual local relative imports. Use `smbls libs link` to migrate to the safe pattern when convenient.

### Scaffolding

`scaffoldSharedLibraries()` in `cli/bin/fs.js`:
1. Reads `sharedLibraries` from project JSON
2. Creates each library as a full project folder via frank's `toFS()`
3. Default location: `.symbols_local/libs/`
4. Auto-generates `sharedLibraries.js` with import statements (overwritten every time)

---

## Context Preparation Sequence

```
prepareContext() {
  1. Set key, define, cssPropsRegistry, window

  2. prepareSharedLibs(context)
     → deepMerge each library into context

  3. prepareDesignSystem(context)
     → uses context.designSystem (now includes shared lib data)

  4. prepareState(app, context)
     → merges context.state + app.state

  5. preparePages(app, context)
     → merges app.routes + context.pages

  6. prepareComponents(context)
     → { ...UIkit, ...context.components }

  7. prepareUtils(context)
     → spreads utils, router, snippets, functions

  8. prepareDependencies()

  9. prepareMethods(context)
     → spreads context.methods + require/router
}
```

---

## Editor Workspace Map

| Package | sharedLibraries | Role |
|---------|----------------|------|
| **brand** | `[]` | Provider — colors, typography, design system |
| **shared** | none | Provider — common components, functions |
| **preview** | `[brand, shared]` | Consumer — standalone preview app |
| **convert** | `[brand, shared]` | Consumer — code converter app |
| **inspect** | `[brand, cms, shared]` | Consumer — inspector editor |
| **cms** | `[brand, shared]` | Consumer — CMS editor |
| **docs** | `[shared]` | Consumer — documentation |
| **assistant** | `[platform, docs, brand, shared]` | Consumer — AI assistant (remote + local libs) |
| **no-code** | `[brand, cms]` | Consumer — no-code editor |
| **canvas** | `[]` | Consumer — canvas editor (no shared libs) |

---

## Key Takeaways

1. **Fetched shared libraries are readonly** — `sharedLibraries.js` and `.symbols_local/libs/` are overwritten on `smbls fetch`/`smbls sync` for cloud entries. Use `link:` (or `smbls libs link <path>`) for sibling-project linking — those are the only entries safe to edit locally.
2. **`link:` ≠ `destDir:`** — `link` means "use this folder as source, never scaffold over it." `destDir` means "scaffold cloud payload INTO this folder" (and will clobber it on every fetch). Always use `link` for local sibling sources.
3. **App always wins** — local project definitions take precedence over shared libraries.
4. **Override by defining locally** — to change a shared library component, define it in your local `components/` with the same name.
5. **Order matters** — first library in the array has priority over later ones for filling undefined slots.
6. **Key format is `owner/key`** — bare keys default to `system/` owner.
7. **`smbls create` defaults to `system/default`** — use `--blank-shared-libraries` for no libraries.
8. **Methods are protected** — METHODS_EXL prevents shared libraries from overwriting element methods and internal references.
9. **`smbls libs status` is the drift detector** — run it whenever you suspect the JS file and JSON declarations are out of sync (especially after manual edits or merging branches). Reports drift by library *slug*, not exact path, so it survives the `dir: "."` path-resolution edge case.
10. **`sharedLibraries.js` has a canonical shape** — the CLI refuses to regenerate a non-canonical (hand-edited) file without `--force`.

---

## Source Files

| Purpose | File | Lines |
|---------|------|-------|
| Runtime merge entry | `smbls/packages/smbls/src/createDomql.js` | 42-44 |
| prepareSharedLibs | `smbls/packages/smbls/src/prepare.js` | 240-251 |
| deepMerge | `smbls/packages/utils/object.js` | 61-76 |
| overwriteShallow | `smbls/packages/utils/object.js` | 431-439 |
| METHODS_EXL | `smbls/packages/utils/keys.js` | 147-152 |
| Key normalization | `smbls/packages/cli/helpers/libraryKeyUtils.js` | — |
| Config normalization (with `link`/`mode`) | `smbls/packages/cli/helpers/symbolsConfig.js` | `normalizeSharedLibrariesConfig` |
| FS scaffolding (skips `mode:linked`) | `smbls/packages/cli/bin/fs.js` | `scaffoldSharedLibraries` |
| Local-edit helpers | `smbls/packages/cli/helpers/symbolsConfigEdit.js` | — |
| sharedLibraries.js parser/writer + drift | `smbls/packages/cli/helpers/sharedLibrariesFile.js` | — |
| `smbls libs` commands | `smbls/packages/cli/bin/libs/commands/` | — |
| `smbls project libs` commands (legacy) | `smbls/packages/cli/bin/project/commands/libs/` | — |
| Context modules | `smbls/packages/frank/toJSON.js` | 170-183 |
| Validation merge | `smbls/packages/cli/bin/validate-domql-runner.js` | 323-342 |
