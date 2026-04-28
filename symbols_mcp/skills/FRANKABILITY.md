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
| NPM package used inside a handler | dynamic `await import('pkg')` inside the handler |

---

## Checklist before committing

1. **No imports between sibling project files** outside the allow-list (`index.js`, `context.js`, `app.js`, `dependencies.js`, `sharedLibraries.js`).
2. **No `let` / `var` at module scope** in component / page / snippet files. (Mutable state lives in `globalScope.js`.)
3. **No module-scope `const` referenced by handlers** unless it's a closure scoped via `scope: { X }`.
4. **No `el.props.X`, `el.on.event`, `props: {}`, `on: {}`, `attr: { placeholder }`, or `({ props, state })` signatures.** All flattened.
5. **Every sub-folder `index.js` re-exports every sibling file.**
6. **`components/index.js` uses `export *`, never `export * as`.**
7. **Run `smbls frank-audit`** to see findings. Run `smbls frank-audit --fix` to apply safe auto-fixes; the fixer verifies against `frank.toJSON` after every risky change and rolls back regressions. Run with `--strict` if you want CI to fail on high-confidence critical findings.

If your project ships and a handler renders the wrong value in prod but the right value locally, the cause is almost always a frankability rule violation in this list. Frank's bundle-time fixer recovers many of these automatically — frank-audit is the source-level pass that prevents the bug from being committed in the first place.
