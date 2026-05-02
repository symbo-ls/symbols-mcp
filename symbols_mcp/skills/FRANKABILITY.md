# Frankability — patterns that survive frank.toJSON

Frank (`@symbo.ls/frank`) serializes a Symbols project into a JSON payload that the deployed runtime hydrates. Code that "looks fine locally" can silently break under serialization — closures vanish, module-level mutations are dropped, sibling imports get inlined and lose identity. This document is the contract for code that frank can serialize without surprises.

> Run `smbls frank-audit` to see findings, `smbls frank-audit --fix` to apply safe auto-fixes (verify-or-rollback semantics — every applied fix is verified against `frank.toJSON`; regressions roll back). Frank itself ships a bundle-time fixer that recovers many patterns at publish time; frank-audit is for cleaning the source so what you commit matches what frank ships. See `@symbo.ls/frank-audit` for the full rule reference.

---

## Why this matters

The deployed app runs from a JSON payload, not from your `.js` source. Frank stringifies handler bodies, walks the project tree, and assembles a portable representation. Two costs of writing non-frankable code:

1. **local ≠ prod**. Your local dev server resolves identifiers via JS module closures. The serialized payload doesn't have those closures. Code that compiles and runs locally can throw `ReferenceError` or silently render wrong values in production.
2. **Frank's bundle-time fixer only catches some cases.** Frank ships a runtime workaround (it scans bundled output and rewrites references to `__scope.X`), but the workaround can't recover every closure or module-scope binding. The cases it misses produce silent data corruption — a button shows the wrong active state, a counter shows undefined, etc.

The fix is to write source code that doesn't rely on the patterns frank's workaround has to repair.

---

## The frankability rules (mirrors `@symbo.ls/frank-audit`)

### Discovery + structure (FA0xx)

#### FA001 — Never import between sibling project files

```js
// ❌ Bad
import { fmtMoney, escapeHtml } from '../functions/utils.js'
export const Card = { text: () => fmtMoney(amount) }

// ✅ Good
export const Card = { text: (el) => el.call('fmtMoney', amount) }
```

Files where sibling imports ARE allowed: `index.js`, `context.js`, `app.js`, `dependencies.js`, `sharedLibraries.js`. Everything else references siblings by string key (`extends: 'Name'`) or via `el.call('fnName', ...)`.

#### FA006 — Never put loadable code in non-discovered folders

Frank only walks: `components/`, `snippets/`, `pages/`, `functions/`, `methods/`, `designSystem/`, `files/`, `assets/`. Anything in `utils/`, `lib/`, `helpers/`, `services/`, etc. is **silently dropped from the published JSON**. Local dev still sees it via JS imports — local works, prod is missing the code.

If a file is generic-utility-shaped, put it in `functions/` (default) or `methods/` (if it needs `this`-binding).

#### FA007 — `components/index.js` uses `export *`, never `export * as`

```js
// ❌ Bad — namespacing breaks the registry
export * as Card from './Card.js'

// ✅ Good
export * from './Card.js'
```

#### FA008 — Every sub-folder index.js re-exports every sibling

```js
// components/index.js — every component file in this folder MUST appear here
export * from './Header.js'
export * from './Footer.js'
export * from './Card.js'
// (missing one = invisible to frank)
```

---

### Flat-syntax (FA1xx) — always required

#### FA101 — `el.props.X` does not exist; use `el.X`

```js
// ❌ Bad
text: (el) => el.props.title

// ✅ Good
text: (el) => el.title
```

#### FA102 — `el.on.event` does not exist; use `el.onEvent`

```js
// ❌ Bad
onClick: (e, el) => el.on.init()

// ✅ Good
onClick: (e, el) => el.onInit()
```

#### FA103 — No `props: { ... }` wrapper inside component literals

```js
// ❌ Bad
Card: {
  props: { padding: 'A', color: 'blue' },
  Title: { text: 'hi' }
}

// ✅ Good
Card: {
  padding: 'A',
  color: 'blue',
  Title: { text: 'hi' }
}
```

#### FA104 — No `on: { event: fn }` wrapper; use flat `onEvent: fn` keys

```js
// ❌ Bad
Button: {
  on: {
    click: (e, el) => { ... },
    init:  (el)    => { ... }
  }
}

// ✅ Good
Button: {
  onClick: (e, el) => { ... },
  onInit:  (el)    => { ... }
}
```

#### FA105 — Don't wrap flat HTML attributes in `attr: { ... }`

DOMQL surfaces these as flat top-level props: `placeholder`, `type`, `name`, `value`, `disabled`, `checked`, `title`, `role`, `tabindex`, `href`, `src`, `alt`, `id`, `min`, `max`, `step`, `pattern`, `required`, `readonly`, `multiple`, `accept`, `autocomplete`, `autofocus`, `rows`, `cols`, `maxlength`, `minlength`, `spellcheck`, `lang`, `dir`, `draggable`, `contenteditable`, `hidden`, `target`, `rel`, `download`, `for`, `colspan`, `rowspan`, `scope`, `headers`, `span`.

```js
// ❌ Bad
Input: {
  attr: { placeholder: 'Search…', type: 'search', value: '' }
}

// ✅ Good
Input: {
  placeholder: 'Search…',
  type: 'search',
  value: ''
}
```

`attr: { ... }` is reserved for attributes NOT exposed as flat props (rare).

#### FA106 — Handlers receive `(el, s)` (or `(e, el, s)`); never destructure an envelope

```js
// ❌ Bad
text: ({ state }) => state.title
onClick: ({ key, state }) => state.update({ active: key })

// ✅ Good
text: (el, s) => s.title
onClick: (e, el, s) => s.update({ active: el.key })
```

#### FA107 — Never declare events as `on: 'event'` strings

```js
// ❌ Bad
Button: { on: 'click' }
Form:   { on: ['init', 'render'] }

// ✅ Good — bind the handler in one place
Button: { onClick: (e, el) => { ... } }
Form:   { onInit: (el) => { ... }, onRender: (el) => { ... } }
```

---

### Scope movers (FA2xx) — the headline frankability work

These are the patterns that make local pass but prod silently fail.

#### FA201 — Mutable module-scope state (`let` / `var`) goes in `globalScope.js`

```js
// ❌ Bad — components/GameCanvas.js
let containerEl = null
export const GameCanvas = {
  onRender: (el) => { containerEl = el }
}

// ✅ Good — globalScope.js
export default {
  containerEl: null
}

// ✅ Good — components/GameCanvas.js (reference stays bare; frank wires it)
export const GameCanvas = {
  onRender: (el) => { containerEl = el }
}
```

Frank wraps mutable globalScope entries in a `Smut` object so writes survive serialization. That only triggers for values that already live in `globalScope.js`.

#### FA202 — Helper functions used in 2+ files go in `globalScope.js`

```js
// ❌ Bad — components/GameCanvas.js
const createGameEl = (el, key, name, extra) => { ... }
const removeGameEl = (key) => { ... }
// ...used by Bird.js, Block.js, Pig.js as well via sibling imports

// ✅ Good — globalScope.js
export default {
  createGameEl: (el, key, name, extra) => { ... },
  removeGameEl: (key) => { ... }
}
```

#### FA203 — Constants used in 2+ files go in `globalScope.js`

```js
// ❌ Bad
const GROUND_Y = 520
const GRAVITY = 0.6
// referenced by GameCanvas.js + physics.js + levels.js

// ✅ Good — globalScope.js
export default { GROUND_Y: 520, GRAVITY: 0.6 }
```

#### FA204 — Constants used in only one component → inline as `scope: { X }`

```js
// ❌ Bad — components/Lightbox.js
const MAX_SLIDES = 12
export const Lightbox = {
  text: (el) => MAX_SLIDES + ' slides'
}

// ✅ Good — value travels with the element
export const Lightbox = {
  scope: { MAX_SLIDES: 12 },
  text: (el) => el.scope.MAX_SLIDES + ' slides'
}
```

(Bare references inside handlers stay bare; frank rewrites to `el.scope.X` at toJSON time.)

#### FA205 — Factory closures must export captures via `scope: { ... }`

```js
// ❌ Bad — silent corruption in prod
const navTab = (path) => ({
  color: () => path === currentPath ? 'blue' : 'gray'
})

// ✅ Good — `path` travels with the element
const navTab = (path) => ({
  scope: { path },
  color: () => path === currentPath ? 'blue' : 'gray'
})
```

When frank stringifies the `color: () => ...` function, the closure over `path` is gone. Without `scope: { path }`, `path` is undefined at runtime — wrong color, no error.

#### FA206 — NPM packages used inside handlers should be dynamic-imported

```js
// ❌ Risky — frank rewrites this silently at bundle time
import { Chart } from 'chart.js'
export const ChartView = {
  onRender: async (el) => { new Chart(el.node, ...) }
}

// ✅ Explicit — local-dev and prod execute the same path
export const ChartView = {
  onRender: async (el) => {
    const { Chart } = await import('chart.js')
    new Chart(el.node, ...)
  }
}
```

Defensive destructure for ESM/CJS-shaped packages (some packages expose the
named export under `default`; both forms occur in the wild):

```js
const mod = await import('motion')
const animate = mod.animate || mod.default?.animate
```

Never use `require('pkg')` synchronously inside a handler — sync require
emits a bundle-internal `require_X()` call that frank's rewriter handles
case-by-case but cannot recover universally. Always async `import()`.

#### FA207 — Nested `function name () {}` declarations get hoisted out of handlers

esbuild hoists nested function declarations to module scope, then frank's
classifyFreeVars promotes them to `globalScope.X`. The promotion strips the
closure — captured locals become undefined at runtime.

```js
// ❌ Bad — nested function decl, captured `topBar` lost at runtime
onRender: (el) => {
  const topBar = el.TopBar.node
  function readBaseHeight () {
    return topBar.offsetHeight
  }
  function onScroll () { /* ... */ }
}

// ✅ Good — const arrow form (cannot be hoisted)
onRender: (el) => {
  const topBar = el.TopBar.node
  const readBaseHeight = () => topBar.offsetHeight
  const onScroll = () => { /* ... */ }
}
```

Rule of thumb: inside any `onRender` / `onClick` / `onInit` handler, every
nested helper MUST be `const X = () => { ... }`. Never `function X () {}`.

#### FA208 — `globalScope.js` helpers MUST NOT cross-import from peer modules

When `globalScope.js` imports from `./config.js` AND a sibling like
`functions/fetch.js` ALSO imports the same name from `./config.js`, esbuild
de-duplicates with a rename (`getApiUrl` → `getApiUrl2`), which then can't be
resolved by frank's classifyFreeVars and surfaces as
`__scope.getApiUrl2 is not a function` at runtime.

```js
// ❌ Bad — globalScope.js shares config imports with peer modules
import { getApiUrl, GOOGLE_CLIENT_ID } from './config.js'
export const initGoogleOneTap = async () => { /* uses getApiUrl */ }

// ✅ Good — globalScope.js inlines its own private copies
const _GOOGLE_CLIENT_ID = '...'
const _resolveApiUrl = () => { /* inlined logic */ }
export const initGoogleOneTap = async () => { /* uses _resolveApiUrl */ }
```

When a page imports a globalScope export AND uses it as a bare reference,
prefer the import form so esbuild keeps the canonical name:

```js
// pages/main.js
import { initGoogleOneTap } from '../globalScope.js'
export const main = {
  onRender: async (el, s) => { initGoogleOneTap() }
}
```

#### FA209 — `dependencies.js` is the runtime importmap, NOT a build-time manifest

Mermaid generates a `<script type="importmap">` from `dependencies.js`. Only
declare packages you `await import('X')` at runtime. Build-time-only tools
(`@symbo.ls/freestyler`, build plugins, etc.) listed here will 404 from
esm.sh and surface as runtime CDN errors.

```js
// ❌ Bad — build-time tool in deps
export default {
  '@symbo.ls/freestyler': '4.0.0',
  'motion': 'latest'
}

// ✅ Good — only runtime dynamic-import targets
export default {
  'motion': 'latest',
  'ninja-keys': '1.2.2'
}
```

#### FA210 — Bypass-mode / mock-auth handlers must guard `el.node` and `s.parent` / `s.root`

If the project has any local-dev auth bypass (`?bypass=true`, mock auth,
etc.), any handler that touches `el.node` or reads `s.parent` / `s.root`
must guard. Mock data paths frequently render before the real shadow DOM
attaches.

```js
// ❌ Bad — assumes el.node + shadowRoot + s.parent are populated
onRender: async (el, s) => {
  const fleet = window.fleet || s.parent.fleet || s.root.fleet || []
  el.node.shadowRoot.innerHTML = ''
}

// ✅ Good — defensive at every step
onRender: async (el, s) => {
  const fleet = window.fleet || s.parent?.fleet || s.root?.fleet || []
  if (!el.node) return
  if (!el.node.shadowRoot) return
  el.node.shadowRoot.innerHTML = ''
}
```

---

### Banned runtime APIs (FA5xx — extends DOM-traversal family)

#### FA513 — Never call `window.update(...)` / `document.update(...)`

`update()` is a DOMQL element method, not a `window`/`document` method.
Calling it on the global object throws at runtime.

```js
// ❌ Never
window.update({ onScroll })

// ✅ Declarative (preferred) — declare on the page/root
export const main = {
  onScroll: (e, el, s) => { /* ... */ }
}

// ✅ Imperative — addEventListener
window.addEventListener('scroll', fn, { passive: true })
```

#### FA514 — Never use module-side-effect bridges

```js
// ❌ Never — frank strips top-level side effects
window.__myProjectInit = initFunction
// later in handler:
window.__myProjectInit?.()

// ✅ Use a bare reference; frank will rewrite to __scope.initFunction
//   and resolve via globalScope
initFunction()
```

---

## Frank's automatic rewrites (informational — you can rely on these)

Phase 2 framework patches recover several patterns AT JSON-GENERATION time.
You don't need to anticipate them, but understanding them helps explain
audit warnings and bundle output:

- `Promise.resolve().then(() => __toESM(require_X(), [n]))` → `import('<pkg>')`
- `Promise.resolve().then(() => (init_X(), Y_exports))` → `import('<pkg>')`
  (init/exports identifiers vary — multi-entry ESM packages)
- Bundle-comment / inline-tag scan maps esbuild identifiers to package
  names from `// node_modules/<pkg>/...` comments AND inline tags
  `__esm({"node_modules/<pkg>/..."() {...}})` and
  `__esm({"stub-external:<pkg>"() {...}})`.
- `scopeRewriter` rewrites bare references to `__scope.X` and chains
  `el.scope` → `context.globalScope` via prototype.
- No-param arrow → `el` injection at rewrite time (so `el.scope` is
  reachable even when source declares `() => ...`).
- `async` modifier preserved when arrow→function conversion happens for
  globalScope helpers calling peer keys.
- `setTimeout` / `queueMicrotask` stubs in the serialization scanner now
  swallow async user-code rejections (won't crash frank).

These cover *many* of the historical FA206-class violations automatically,
but generating dynamic imports up front (FA206) avoids the round-trip and
keeps local-dev parity with prod.

---

## Quick reference — placement decision

| Pattern | Where it goes |
|---|---|
| Mutable state (`let`/`var`) referenced by handlers | `globalScope.js` |
| Function helper used by 2+ files | `globalScope.js` (or `functions/` if invoked via `el.call`) |
| Constant used by 2+ files | `globalScope.js` |
| Constant used by 1 component | `scope: { X }` on that component |
| Factory closure variable | `scope: { X }` on the returned object |
| Single-use helper inside one component | inline as a method on the component, or `scope: { fn }` |
| Nested helper inside `onRender`/`onClick`/etc. | `const X = () => {}` — never `function X () {}` (FA207) |
| NPM package used inside a handler | dynamic `await import('pkg')` inside the handler (FA206) |
| Helpers in `globalScope.js` that need shared config | inline private copies with `_` prefix (FA208) |
| Runtime importmap entry | `dependencies.js` — runtime-only (FA209) |
| Build-time tool (e.g. freestyler) | NEVER `dependencies.js` (FA209) |

---

## Generation checklist — verify before emitting code

When `generate_component` / `generate_page` produces code, OR when
hand-writing a Symbols project file, verify ALL of:

1. ✅ **No top-level `import { X } from 'npmpkg'`** for runtime-only deps —
   must be dynamic `await import('npmpkg')` inside the handler. (FA206)
2. ✅ **No sync `require('X')`** anywhere — always async `import()`. (FA206)
3. ✅ **No module-scope `const`/`let`** captured by exported handlers (other
   than environment-independent constants like `const SCALE = 1.25`). Use
   `scope: { X }` or `globalScope.js`. (FA201–204)
4. ✅ **Nested helper functions inside lifecycle methods use `const X = () => {}`** —
   never `function X () {}`. (FA207)
5. ✅ **HTML attributes are flat props** (`placeholder`, `type`, etc.), NOT
   in `attr: {}`. (FA105)
6. ✅ **Reactive prop functions take `(el, s)`** — never destructured
   `({state})`. (FA106)
7. ✅ **Function access via `el.call('fn')` / `this.call('fn')`** — no
   inter-file imports outside the allow-list. (FA001)
8. ✅ **`extends:` only when key name differs** from the extended component
   (use key-name match + `_N` suffix for multi-instance).
9. ✅ **All values use DS tokens** — no raw px/hex/rgba. (FA301–304)
10. ✅ **No `window.update(...)`, no `document.update(...)`, no
    `window.__projectInit = ...`** module-side-effect bridges. (FA513, FA514)
11. ✅ **`dependencies.js` lists only runtime dynamic-import targets** —
    never build-time tools. (FA209)
12. ✅ **`globalScope.js` helpers do NOT cross-import from peer module
    files** — inline private helpers with `_` prefix. (FA208)
13. ✅ **Bypass-mode / mock-auth handlers guard `el.node` and
    `s.parent`/`s.root`**. (FA210)

---

## Checklist before committing

1. **No imports between sibling project files** outside the allow-list (`index.js`, `context.js`, `app.js`, `dependencies.js`, `sharedLibraries.js`).
2. **No `let` / `var` at module scope** in component / page / snippet files. (Mutable state lives in `globalScope.js`.)
3. **No module-scope `const` referenced by handlers** unless it's a closure scoped via `scope: { X }`.
4. **No `el.props.X`, `el.on.event`, `props: {}`, `on: {}`, `attr: { placeholder }`, or `({ props, state })` signatures.** All flattened.
5. **Every sub-folder `index.js` re-exports every sibling file.**
6. **`components/index.js` uses `export *`, never `export * as`.**
7. **No nested `function name () {}` inside handlers** — use `const x = () => {}` (FA207).
8. **No `window.update(...)`, `document.update(...)`, or `window.__projectInit = ...` bridges** (FA513, FA514).
9. **`dependencies.js` contains only runtime dynamic-import targets** (FA209).
10. **`globalScope.js` does not cross-import from peer modules** (FA208).
11. **Run `smbls frank-audit`** to see findings. Run `smbls frank-audit --fix` to apply safe auto-fixes; the fixer verifies against `frank.toJSON` after every risky change and rolls back regressions. Run with `--strict` if you want CI to fail on high-confidence critical findings.

If your project ships and a handler renders the wrong value in prod but the right value locally, the cause is almost always a frankability rule violation in this list. Frank's bundle-time fixer recovers many of these automatically — frank-audit is the source-level pass that prevents the bug from being committed in the first place.
