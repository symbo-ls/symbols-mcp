# sharedLibraries

sharedLibraries is a mechanism in the Symbols framework that allows projects to inherit components, functions, methods, state, designSystem, pages, files, snippets, and dependencies from external library projects. Libraries are merged into the consuming app's context at runtime — no manual re-exports needed.

---

## Configuration

### symbols.json

Three supported formats:

```json
// Array of strings (library keys)
"sharedLibraries": ["brand", "shared"]

// Object with key:version
"sharedLibraries": { "brand": "1.0.0", "shared": "latest" }

// Object with key:config (used in editor)
"sharedLibraries": {
  "brand": { "version": "1.0.0", "destDir": "../brand" },
  "shared": { "destDir": "../shared" }
}
```

All formats are normalized by the CLI (`cli/helpers/symbolsConfig.js:246-268`) to: `[{ key, version, destDir }]`

### sharedLibraries.js

Each package has a `sharedLibraries.js` that imports other packages' `context.js` and exports them as an array:

```js
import brand from '../brand/context.js'
import shared from '../shared/context.js'

export default [brand, shared]
```

For remote libraries fetched from the platform:

```js
import platformSymboLs from '../.symbols_local/libs/platform.symbo.ls/context.js'
import docsSymboLs from '../.symbols_local/libs/docs.symbo.ls/context.js'

export default [platformSymboLs, docsSymboLs]
```

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

`smbls/src/prepare.js:240-251`:

```js
export const prepareSharedLibs = (context) => {
  const sharedLibraries = context.sharedLibraries
  for (let i = 0; i < sharedLibraries.length; i++) {
    const sharedLib = sharedLibraries[i]
    if (context.type === 'template') {
      overwriteShallow(context.designSystem, sharedLib.designSystem)
      deepMerge(context, sharedLib, ['designSystem'], 1)
    } else {
      deepMerge(context, sharedLib, [], 1)
    }
  }
}
```

**Two strategies:**

| App Type | designSystem | Everything Else |
|----------|-------------|-----------------|
| **template** | `overwriteShallow` — library completely replaces template's designSystem | `deepMerge` with designSystem excluded |
| **regular** | `deepMerge` (app wins) | `deepMerge` (app wins) |

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

### Scaffolding (`cli/bin/fs.js:231-345`)

`scaffoldSharedLibraries()`:
1. Reads `sharedLibraries` from project JSON
2. Creates each library as a full project folder via frank's `toFS()`
3. Default location: `.symbols_local/libs/`
4. Generates `sharedLibraries.js` with import statements

### Fetch (`cli/bin/fetch.js`)

When fetching from the platform:
- Pulls full project data including `sharedLibraries` array
- Each library is a complete Symbols project object
- Extracts version info and stores in lock file

### toJSON (`frank/toJSON.js:170-183`)

Context modules list includes sharedLibraries:

```js
const CONTEXT_MODULES = [
  { name: 'state', path: './state.js', style: 'default' },
  { name: 'dependencies', path: './dependencies.js', style: 'default' },
  { name: 'sharedLibraries', path: './sharedLibraries.js', style: 'default' },
  { name: 'components', path: './components/index.js', style: 'namespace' },
  { name: 'snippets', path: './snippets/index.js', style: 'namespace' },
  { name: 'pages', path: './pages/index.js', style: 'default' },
  { name: 'functions', path: './functions/index.js', style: 'namespace' },
  { name: 'methods', path: './methods/index.js', style: 'namespace' },
  { name: 'designSystem', path: './designSystem/index.js', style: 'default' },
  { name: 'files', path: './files/index.js', style: 'default' },
  { name: 'config', path: './config.js', style: 'default' }
]
```

### Validation (`cli/bin/validate-domql-runner.js:323-342`)

`mergeSharedLibraries()` merges all library exports for DOMQL validation:

```js
function mergeSharedLibraries(sharedLibraries) {
  const merged = { pages: {}, components: {}, functions: {}, methods: {}, snippets: {} }
  for (const lib of libs) {
    if (isPlainObject(lib?.pages)) Object.assign(merged.pages, lib.pages)
    if (isPlainObject(lib?.components)) Object.assign(merged.components, lib.components)
    // ...
  }
  return merged
}
```

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

1. **No re-exports needed** — components/functions from a shared library are automatically available in the consuming app's context
2. **App always wins** — app's own definitions take precedence over shared libraries
3. **Order matters** — first library in the array has priority over later ones for filling undefined slots
4. **Templates are special** — designSystem is fully overwritten (shallow) rather than deep-merged
5. **Methods are protected** — METHODS_EXL prevents shared libraries from overwriting element methods and internal references
6. **No circular detection** — JavaScript's ESM module system prevents infinite loops naturally; circular deps resolve as undefined values

---

## Source Files

| Purpose | File | Lines |
|---------|------|-------|
| Runtime merge entry | `smbls/packages/smbls/src/createDomql.js` | 42-44 |
| prepareSharedLibs | `smbls/packages/smbls/src/prepare.js` | 240-251 |
| deepMerge | `smbls/packages/utils/object.js` | 61-76 |
| overwriteShallow | `smbls/packages/utils/object.js` | 431-439 |
| METHODS_EXL | `smbls/packages/utils/keys.js` | 147-152 |
| Config normalization | `smbls/packages/cli/helpers/symbolsConfig.js` | 246-268 |
| FS scaffolding | `smbls/packages/cli/bin/fs.js` | 231-345 |
| Context modules | `smbls/packages/frank/toJSON.js` | 170-183 |
| Validation merge | `smbls/packages/cli/bin/validate-domql-runner.js` | 323-342 |
