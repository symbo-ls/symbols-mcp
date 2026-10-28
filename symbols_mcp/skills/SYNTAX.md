# DOMQL Syntax Reference

Authoritative reference for generating correct DOMQL code. Every pattern is derived from real working code in `smbls`.

> smbls is signal-based. Props are flat on the element (`el.X`, NOT `el.props.X`). Event handlers are flat top-level (`onClick`, NOT `on: { click }`). Reactive prop functions take `(el, s)` — never destructured `({ props, state })`.

---

## Element Anatomy

DOMQL elements are plain JS objects. Every key has a specific role:

```js
export const MyCard = {
  tag: 'section',                // HTML tag (default: div)

  // CSS props (top-level)
  padding: 'B C',
  gap: 'A',
  flow: 'y',
  theme: 'dialog',
  round: 'C',

  // HTML attributes (auto-detected by attrs-in-props)
  role: 'region',
  ariaLabel: 'My card',          // camelCase → aria-label
  aria: { describedby: 'desc' }, // shorthand object → aria-describedby

  // State (signal-backed reactive store)
  state: { open: false },

  // Reactive props — function signature is (el, s) or (el, s, ctx)
  text:    (el, s)    => s.label,
  hide:    (el, s)    => !s.open,
  color:   (el, s)    => s.active ? 'primary' : 'gray.5',

  // Events (flat top-level — DOM events: (e, el, s); lifecycle: (el, s, ctx))
  onClick:    (e, el, s) => s.update({ open: !s.open }),
  onKeydown:  (e, el, s) => { if (e.key === 'Escape') s.update({ open: false }) },
  onInit:     (el, s, ctx) => { el.scope.timer = null },
  onRender:   (el, s, ctx) => {},

  // Children (PascalCase keys auto-extend matching components)
  Header: { text: (el, s) => s.title },
  Body:   { html: (el, s) => s.content }
}
```

---

## Element Lifecycle

```
create(definition, parent, key, options)
  ├─ normalize definition (string/number → { text }, null/false → null)
  ├─ applyExtends()           merges extends chain (definition wins)
  ├─ flatten props onto el    (definition.props → flat on element)
  ├─ addMethods()             attaches el.update / el.lookdown / el.call / etc.
  ├─ createElementState()     wraps state in createStore() signal proxy
  ├─ evaluate `if`            mark __if true/false; bail early if false
  ├─ detectTag + cacheNode    create DOM node
  ├─ triggerLifecycle 'Init'  → fires onInit
  ├─ registerEffects()        wire reactive effects for function props
  ├─ applyStaticMixins()      apply text/html/style/attr/data/classlist
  ├─ registerEvents()         bind onXxx handlers via delegation
  ├─ createChildren()         recurse for each PascalCase / children
  ├─ assignNode()             attach to parent in DOM
  └─ triggerLifecycle 'Create' → 'Complete' → 'Render' → 'RenderRouter'
```

The `if` effect re-enters the full creation steps the first time it flips false → true.

**When the app's first view is in — `afterFirstView`** (since smbls 3.14.859). A create option (`config.js`, `context.js`, or `create(App, { afterFirstView })`), called once per app as the root's `onCreate` is, `(app, state, context)`: a task after the first view is in — after `create()` rendered it (on a pre-rendered page: after the adoption) and after the first navigation settled (a route behind an awaited guard renders later). Work that must not compete with the first view goes there: a page view, a beacon, warming the next route. Never poll `window.__BRENDER_HYDRATION__` or loop on `requestAnimationFrame` to learn that a built page was taken over. A hook that throws or rejects is reported, never rethrown; a server render (brender) never runs it. It runs at the moment `fetch.early`'s own `afterFirstView` hook runs (FRAMEWORK.md §5 → Early requests).

```js
// config.js
export default {
  afterFirstView: (app, state, context) => { app.call('pageView') }
}
```

**Yielding mounts.** During an app's first render (`firstRender` in `config.js`, on by default) — or with `domqlOptions.mountYield` / `yieldChildren` — `createChildren()` can stop at a time budget and continue in a later task. Such an element is attached at once (during the first render and the adoption of a pre-rendered page, smbls sets `mountWhole`: it waits outside its parent and goes in with one insertion when its last chunk is in, so a row is never on screen half built), but `Create` → `Complete` → `Render` → `RenderRouter` (and the `onMounted` queueing) run after its last deferred child, and a parent in the same mount waits for its incomplete children: `onRender` always sees every child. The rest is built depth-first, so every hook fires in the same order as a synchronous build — only spread over several tasks. The smbls embed never yields: every children loop builds in one go.

---

## REGISTRY Keys

These are handled by DOMQL internally and are NOT promoted to CSS props:

```
attr, style, text, html, data, classlist, state, scope, deps,
extends, children, content, childExtends, childExtendsRecursive, childProps, childrenAs,
props, if, show, hide, value, define, key, tag, query, parent, node,
variables, component, context, fetch, routes, metadata,
onInit, onCreate, onComplete, onRender, onRenderRouter, onUpdate, onBeforeUpdate,
onStateInit, onStateCreated, onStateUpdate, stateDeps, onBeforeStateUpdate,
onAttachNode, onFrame, onError, onInView, onLeaveView,
onBeforeRemove, onRemove, onDestroy, onDispose,
onClick, onInput, onChange, onSubmit, onKeydown, onKeyup, onMouseover,
onBlur, onFocus, onScroll, onResize, … any other onXxx
```

Any key NOT in this list and not PascalCase is promoted as a CSS prop.

> Forbidden keys: `extend`, `childExtend`, `childExtendRecursive`, `props: {}` wrapper, `on: {}` wrapper.

---

## Extending and Composing

| Pattern | Syntax |
| -- | -- |
| Single extend | `extends: 'Button'` |
| Multiple (**LAST = highest priority**) | `extends: ['Link', 'RouterLink']` — `RouterLink` wins every conflicting key |
| String reference (from `context.components`) | `extends: 'Hoverable'` |
| Auto-extend by key | `Icon: {...}` auto-extends 'Icon'; `Icon_1: {...}` also auto-extends 'Icon' |

### Merge Semantics

| Type | Rule |
| -- | -- |
| Own properties | Always win over extends |
| `extends: [A, B]` array | **LAST wins** — later entries override earlier ones on every conflicting key, like later CSS declarations. Keys only one entry declares are all kept. A component still beats what it extends. |
| Plain objects | Deep-merged (PascalCase children deep-merge child overrides) |
| Special keys (`childProps`, `attr`, `style`, `scope`, `data`) | Shallow merge {...base, ...override} |
| Functions | NOT merged; element's function replaces extend's — except a lifecycle handler the base marks `{ always: true, handler }`, which runs BEFORE the one that replaces it (Lifecycle events → `always`) |
| Arrays | Concatenated where applicable; otherwise replaced |

---

## CSS Props (Top-Level)

Place CSS props at the element root. Non-registry, non-PascalCase, lowercase keys become CSS props:

```js
export const Card = {
  padding: 'B C',         // spacing token
  gap: 'Z',
  flow: 'y',              // shorthand for flexDirection
  align: 'center',        // alignment shorthand (NOT flexAlign)
  fontSize: 'A',
  fontWeight: '500',
  color: 'currentColor',
  background: 'codGray',
  round: 'C',             // border-radius token
  opacity: '0.85',
  overflow: 'hidden',
  transition: 'B defaultBezier',
  zIndex: 10,
  tag: 'section',         // stays at root (REGISTRY)
  href: '/about'          // auto-detected as HTML attribute on <a>
}
```

### `null` Is a Tombstone — Removes the Declaration

A CSS prop set to `null` emits **nothing**: no declaration, no atomic class. This holds for a raw value and for a prop written as a function that RETURNS `null`. It covers every registered CSS prop, including `show` — `show: null` no longer forces `display: none`.

```js
export const Decision = {
  extends: 'ThemedCard',
  border: null    // removes the inherited border declaration entirely — nothing is emitted
}

// Same tombstone when a function returns null
border: (el, s) => s.hasCustomBorder ? undefined : null
```

`null` is how a project, or a platform merge, REMOVES an inherited declaration. It is not a way to author `none` / `0` / `unset` — write those values explicitly when you mean them.

**`undefined` is deliberately NOT a tombstone.** Several props read `undefined` as "fall back to my alias":

```js
borderRadius: (val, el) => transformBorderRadius(val ?? el.round, …)   // undefined → falls back to el.round
```

Use `null` to remove a declaration outright; use `undefined`, or omit the prop, when a fallback should still apply.

> Scope: this is the CSS-prop contract (`usePropsAsCSS` / `CSS_PROPS_REGISTRY`), fixed in smbls `e1ada1387`. `attr:` / HTML attributes are a separate mechanism (below) where BOTH `null` and `undefined` remove the attribute.

### Pseudo-Classes and Pseudo-Elements

```js
export const Hoverable = {
  opacity: 0.85,
  ':hover':         { opacity: 0.9, transform: 'scale(1.015)' },
  ':active':        { opacity: 1,   transform: 'scale(1.015)' },
  ':focus-visible': { outline: 'solid X blue.3' },
  ':not(:first-child)': {
    '@dark':  { borderWidth: '1px 0 0' },
    '@light': { borderWidth: '1px 0 0' }
  }
}
```

**A PascalCase key nested inside a pseudo-class / media / theme block is never a valid selector fragment — never nest a child-component key there.** A bare capitalized identifier (`Add`, `Icon`, …) can't syntactically be a pseudo-class (`:`), theme/media block (`@`), or combinator (`&`) — it's the shape of a DOMQL child-component key. The engine refuses to emit that rule at all (a dead selector that can never match is worse than a silently-wrong one) and logs a dev-only warning naming the offending key and element:

```js
// ❌ `Add` inside `:hover` is a child-component key, not a selector — dropped, dev warning logged
Toolbar: {
  ':hover': {
    Add: { opacity: 1 }   // never emitted; Add's own opacity stays whatever it was
  }
}

// ✅ Style the child directly — it already has its own class
Toolbar: {
  Add: {
    opacity: 0,
    transition: 'opacity B',
    ':hover &': { opacity: 1 }   // hoist via an explicit combinator if you need parent-hover-affects-child
  }
}
```

`backdropFilter` and `userSelect` automatically get a paired `-webkit-` declaration in every generated rule (atomic classes, compound `css()` bodies, `injectGlobal`, keyframes) — WebKit-based engines historically ignored the unprefixed form for these two properties. You do not need to hand-write the `-webkit-` variant or reach for a `style: {}` escape hatch just to get vendor coverage; write the plain prop and both declarations are emitted for you.

### Attribute Selectors

A key that starts with a bare attribute selector — `[attr="value"]` — compounds onto the element's OWN class, exactly like a leading `:pseudo`. It is never a descendant search for some other element carrying that attribute:

```js
export const Disclosure = {
  aria: { expanded: (el, s) => (s.open ? 'true' : 'false') },
  '[aria-expanded="true"]':    { background: 'primary' },  // .cls[aria-expanded="true"]     — attribute on THIS element
  '[aria-expanded="true"] .x': { opacity: 1 },              // .cls[aria-expanded="true"] .x  — compound head, then a real descendant
  '&[aria-expanded="true"]':   { background: 'primary' }    // identical result — the `&` form, useful when mixed with other `&`-anchored keys
}
```

`'[attr] .x'` and `'&[attr] .x'` compile to the same head (`.cls[attr]`); the space before `.x` is a genuine descendant combinator, not an extra ancestor hop. There is no bare-`[attr]`-searches-descendants form — to match the attribute on a descendant instead of this element, name the descendant explicitly: `'& [data-key="Target"][attr]'`.

### Conditional Props (Cases)

Three prefix types for conditional CSS and attributes:

| Prefix | Resolution | Example |
| -- | -- | -- |
| `$` | Global case from `context.cases` — **currently does not apply at all, see below** | `$isSafari: { padding: 'B' }` |
| `.` | Element/state first, then `context.cases` | `'.isActive': { opacity: 1 }` |
| `!` | Inverted — applies when falsy | `'!isActive': { opacity: 0 }` |

Cases are defined in `cases.js` at the project root and added to `context.cases`. CSS props AND HTML attributes inside `.`/`!` conditional blocks are applied while the block matches: `aria: { selected: true }`, `'aria-pressed': 'true'`, `title`, `data: { state: 'on' }`. An attribute value may be a factory (`(el, s, ctx)`) or a `{{ }}` template and follows what it reads while the block matches; when the block stops matching, each attribute goes back to the value it had before the block took it (removed when it had none). The block's CSS keys keep their turn-on value. Not read inside a block: `attr: {}` holders, event handlers, and `style` / `class` / `value`; keys that are attributes on the tag itself (`fill` on an `<svg>`, `rows` on a `<textarea>`) stay CSS inside a block.

`.isX` / `'!isX'` blocks are fully reactive — the framework wraps the `isX` condition in its own `createEffect` (both directions: applying AND reverting), so the matching block re-applies every time the state read by the condition changes, for a flag on the element's own state or on root state, whether the state key is declared up front or arrives later. Use the pattern when two or more CSS props share a single condition; it's cleaner than repeating the same condition across many prop functions.

A condition that reads only the element's own props (`isQuiet: (el) => !!el.quiet`, directly or through `el.call('fn')`) re-runs on `el.update()` and never warns. In dev, a condition whose FIRST run read state WITHOUT subscribing — the `in` operator, `Object.keys` / spread / JSON, a `__` key, `s.parse()` / `keys()` / `values()` — and so tracked nothing logs ``[smbls] conditional `.isX` on X subscribed to nothing`` once: no state write will ever re-run it. The decision is made at run time (the source is never read). Declare the dependency — `isXDeps: ['key', (el, s) => s.root.openId]` is read first, unconditionally, so the subscription exists while the key is undeclared — or `isXDeps: []` to mark the condition static on purpose (no warning).

**`$isX` (global cases) does not currently apply at all — do not use it.** Unlike `.isX`/`!isX`, nothing in the runtime reads a `$`-prefixed key: it is neither compiled once at create nor wired into a reactive effect, so a `$isSafari: {...}` block silently emits no CSS, ever. Express a global-case condition as an ordinary reactive prop function instead (`padding: (el, s) => isSafari(s) ? 'B' : undefined`).

```js
// ✅ Reactive grouped CSS via .isX
export const Item = {
  opacity: 0.6,
  isActive: (el, s) => s.root.active === el.key,
  '.isActive': { opacity: 1, fontWeight: '600', aria: { selected: true } }
}

// ✅ '!isX' for the inverse branch
export const Item = {
  isSelected: (el, s) => s.selectedId === el.key,
  '.isSelected': { background: 'primary', color: 'white' },
  '!isSelected': { opacity: 0.6 }
}
```

### Raw Style Object (Escape Hatch)

Use `style: {...}` only when you need raw CSS-in-JS rules (`& [...]`, descendant selectors, animation keyframes). Prefer top-level CSS props.

```js
export const DropdownParent = {
  style: {
    '&:hover': {
      zIndex: 1000,
      '& [dropdown]': { transform: 'translate3d(0,0,0)', opacity: 1 }
    }
  }
}
```

Design-system tokens resolve in a `style` block and its `&` blocks like the same key at the top level: `style: { padding: 'A', '& > span': { marginLeft: '-Z' } }` gets the spacing variables. This happens only for a real CSS property that has a transformer, only for a spacing / typography / timing letter (`A`, `-Z`, `B2`) or a `sizes` name, and only when the browser rejects the raw value. Other values pass through verbatim: `gridArea: 'A'` stays `A`, and smbls aliases (`round`, `flow`, `boxSize`) are not CSS there.

### CSS Custom Properties — `vars` and `'--x'`

Set a custom property as a top-level `'--x'` key or in the `vars` prop. Both spellings take one path:

```js
export const Gauge = {
  vars: {
    trackOpacity: 0.4,                                   // a bare name → --trackOpacity; static → the element's class
    '--fill': (el, s) => Math.round((s.done / s.total) * 100) + '%'   // factory → inline, reactive
  },
  '--tilt': (el, s) => (s.flipped ? '180deg' : null),    // a top-level factory is reactive too; null removes it
  isDone: (el, s) => s.done === s.total,
  '.isDone': { vars: { trackOpacity: 1 } },              // in a block: overrides by the cascade
  Rail: { opacity: 'var(--trackOpacity)' },
  Bar: { width: 'var(--fill)', transform: 'rotate(var(--tilt, 0deg))' }
}
// or the whole bag from state: vars: (el, s) => ({ '--x': s.x + 'px', '--y': s.y + 'px' })
```

- A STATIC value compiles into the element's atomic class, so a `:hover` / `@media` / `.isX` block overrides it. A FACTORY (`'--x': fn`, a `vars` entry, a whole `vars: (el, s) => ({…})`) is written inline and re-runs when what it reads changes.
- `null`, `undefined`, `false` or `''` removes the property (only what that factory wrote).
- Names are verbatim and case-sensitive: `--rteTop` and `--rte-top` are two properties. Values are verbatim too: no design-token lookup (`'C'` stays `C`).
- `vars` inside a pseudo / media / theme / `.isX` block declares custom properties there. `el.update({ vars })` re-applies the static entries.
- Prefer `vars` / `'--x'` over `style: { '--x': … }` and over `node.style.setProperty` (Rule 30).

**`fill` and `stroke`** are CSS props on every tag except `<svg>`, where the element's own flat `fill` / `stroke` stay the presentation attributes they always were. Inside a CSS block (`:hover`, `.isActive`, `@dark`) they are CSS on every tag, which outranks the attribute, so a block still repaints an `<svg>`. Their values are written as given (no colour-token lookup): `fill: 'currentColor'` with a `color` token.

### Media Queries

```js
export const Grid = {
  columns: 'repeat(4, 1fr)',
  '@tabletS': { columns: 'repeat(2, 1fr)' },
  '@mobileL': { columns: '1fr' },
  '@dark':    { background: 'codGray' },
  '@light':   { background: 'concrete' }
}
```

#### Breakpoints that follow a container — `breakpointsFrom`

Breakpoint keys (`@mobileL`, `@tabletS`, …) are window media queries. A subtree drawn narrower than the window (a page editor's canvas, a device preview, a side panel) can measure its own box instead:

```js
export const Canvas = {
  breakpointsFrom: 'container',              // or a container name: 'canvas' | 'window'
  width: (el, s) => s.root.previewWidth,     // a device width the editor chose
  Page: {
    padding: 'D',
    '@mobileL': { padding: 'C B' },          // → @container breakpoints (max-width: 768px)
    '@print':   { padding: '0' }             // not width-only → stays @media
  }
}
```

- The element that declares it becomes the size container (`container-type: inline-size`, `container-name: breakpoints`, or the name you give, or the first name of its own `containerName`). Its OWN breakpoint keys stay window queries: a container query never measures the element it is declared on. Inline-size containment means its width must not come from its content: give it a width, or let it stretch.
- Every DESCENDANT's width-only breakpoint (`(max-width: N)`, `(min-width: N)`, `(width < N)`, joined with `and` / `or`, optionally behind `screen and`) compiles to `@container <name> (…)`. Height, orientation, aspect-ratio, print, colour-scheme and hover breakpoints, and raw `'@media …'` keys, stay media queries.
- `breakpointsFrom: 'window'` on a nested element sends its descendants back to the window (a fixed toolbar inside the canvas). The nearest ancestor that declares it decides. A function value `(el, s, ctx) => …` works too.
- **`vw` follows the container** (smbls 3.14.857 / element 3.14.817). Inside a `breakpointsFrom` container, `vw` lengths measure the container, not the window: write `vw` as you would for a full-window page (no `cqw` needed). The container's class gives its children `--smbls-cvw: 1cqi` (a registered `<length>` custom property, initial value `1vw`, so it inherits as px and a nested card container does not re-measure it) and re-declares every design-system token with a `vw` length (and each token that refers to one) in `--smbls-cvw`. A descendant's own `vw` / `svw` / `lvw` / `dvw` values (static and reactive props, case blocks, `style` blocks, inline writes) are written as `calc(N * var(--smbls-cvw))`. `breakpointsFrom: 'window'` inside a container gives its subtree the window's `vw` again. Apps without a container emit the same CSS as before.
- `vh` still measures the window, and `onMediaQueryChange` still listens to the window (`matchMedia`).
- **`containerVw` is an optional element feature.** The lean engine (the smbls embed) leaves it out. `build.treeShakeFeatures` drops it from a production build whose source never names `breakpointsFrom` (feature `containerVw`, trigger `breakpointsFrom`).

#### CSS system colours and forced-colours blocks

A CSS system colour (`CanvasText`, `Canvas`, `Highlight`, `HighlightText`, `ButtonText`, `ButtonFace`, …) is a valid colour value, with these rules (scratch 3.14.793):

- Inside `'@media (forced-colors: active)'`, or a media key of your design system that maps to it (`media: { forcedColors: '(forced-colors: active)' }` → `'@forcedColors'`), every spelling passes (`'Highlight'` and `'highlight'`).
- Outside such a block the spec spelling passes (`color: 'CanvasText'`, for example beside `forcedColorAdjust: 'none'`). A lowercase word that only shares the name (`'highlight'`, `'canvastext'`) is a missing palette token: it is dropped with a dev warning.
- The same holds for a CSS named colour (`red`, `navy`): a name the project's palette does not define is dropped with a dev warning, never emitted as the browser's colour. A hyphenated unknown word (`highlight-reversed`) passes through as before. A render with no palette at all passes every name through. So define every colour token you use (`highlight`, `red`) in `designSystem/color.js`, and give a test that mounts components the project's design-system colours.
- A palette token of the same name always wins. A system colour inside a `border` / `outline` / `boxShadow` shorthand (`'1px solid ButtonText'`) stays as written.

```js
export const FilterChip = {
  extends: 'Button',
  background: 'surface',
  '@media (forced-colors: active)': {
    color: 'ButtonText',
    border: '1px solid ButtonText'      // the shorthand keeps the system colour as written
  }
}
```

---

## Events — Flat `onXxx` Top-Level

### Event Signatures

DOM events: `(event, el, state)`

```js
onClick:     (e, el, s) => {},
onChange:    (e, el, s) => {},
onInput:     (e, el, s) => s.update({ value: e.target.value }),
onSubmit:    (e, el, s) => { e.preventDefault() },
onKeydown:   (e, el, s) => { if (e.key === 'Enter') {} },
onMouseover: (e, el, s) => {},
onBlur:      (e, el, s) => {},
onFocus:     (e, el, s) => {}
```

Lifecycle events: `(el, state, context, options?)`

```js
onInit:        (el, s, ctx)    => { /* before DOM creation */ },
onAttachNode:  (el, s, ctx)    => { /* DOM node created, not attached */ },
onCreate:      (el, s, ctx)    => { /* full setup done */ },
onComplete:    (el, s, ctx)    => { /* alias of onCreate */ },
onRender:      (el, s, ctx)    => { /* effects + children + DOM ready */ },
onRenderRouter:(el, s, ctx)    => { /* router-specific post-render */ },
onUpdate:      (el, s, ctx, opts) => { /* after el.update() on THIS element — see the table below */ },
onBeforeUpdate:(el, s, ctx, options) => { /* return false to cancel this update */ },
onStateInit:   (el, data, ctx, options) => { /* the element builds its OWN state — see below */ },
onStateCreated:(el, s, ctx, options)    => { /* the element's state exists, methods included */ },
onBeforeStateUpdate: (el, s, ctx, { changes, options }) => { /* return false to cancel the write */ },
onStateUpdate: (el, s, ctx, { prev, next }) => { /* a stateDeps value changed — see below */ },
onFrame:       (el, s, ctx)    => { /* every requestAnimationFrame */ },
onError:       (el, s, ctx)    => { /* lifecycle error caught inside the element */ },
onBeforeRemove:(el, s, ctx)    => { /* fires BEFORE refs/state are torn down — can still read state and cancel sockets/requests */ },
onRemove:      (el)            => { /* fires AFTER DOM detach + state.destroy(); refs are still present for logging */ }
```

Every lifecycle handler takes the element FIRST.

#### A base that owns a lifecycle step — `{ always: true, handler }`

A merge gives every key ONE value: an element's own `onRender` replaces its base's. That default never changes. A base marks a handler `always` when every component that extends it must run it:

```js
export const Tracked = {
  onRender: { always: true, handler: (el) => el.call('trackImpression', el.key) }
}
export const Card = {
  extends: 'Tracked',
  onRender: (el, s) => { /* runs AFTER Tracked's handler, never instead of it */ }
}
```

- An `always` handler survives every merge that would replace it: an `extends` chain or array, `childExtends`, the key auto-extend, a nested child override, `childProps`. It runs before the handler that replaced it.
- `always` handlers accumulate down a chain (deepest base first, an `extends` array in order); ONE plain handler — the last merged — runs after them. A plain handler between them is still replaced: `Rise { always r }` → `Card { extends: 'Rise', onRender: c }` → `{ extends: 'Card', onRender: o }` runs `r, o`.
- `el.onRender` stays one function: calling it runs them all with the same `this` and arguments. A throwing handler does not stop the rest (the error is reported); `false` from any of them is returned (an `onBeforeUpdate` veto); an async one keeps the hook pending until it settles.
- Composes: the lifecycle hooks (`onInit` … `onRemove`, `onUpdate`, `onStateUpdate`, `onMounted`, `onFrame`, …) and `onInView` / `onLeaveView`, each entry with its own options. Does NOT compose: DOM events (`onClick` …), the bridge hooks (`onBridgeMount` returns the one library instance). `always` there warns in dev and the plain merge applies.

#### View events — `onInView` / `onLeaveView`

```js
export const Rise = {
  // a server render starts in the final state (no view there, nothing fires)
  data: { rise: (el) => el.context.ssr === true ? 'in' : 'wait' },
  '[data-rise="wait"]': { opacity: '0' },
  '[data-rise="in"]': { animationName: 'riseIn', animationDuration: 'E' },
  onInView: {
    always: true,       // every component that extends Rise keeps this step
    once: true,         // first time only, then the element is no longer watched
    threshold: 0.1,     // share of the element that must be visible, 0–1 (default 0)
    rootMargin: '0px',  // grows/shrinks the viewport, as IntersectionObserver's
    handler: (entry, el, s, ctx) => el.update({ data: { rise: 'in' } })
  },
  onLeaveView: (entry, el, s, ctx) => el.call('pausePreview', el)
}
```

- `onInView` runs when the element crosses INTO its threshold; `onLeaveView` on the way out, never for an element that starts out of view. `entry` is the `IntersectionObserverEntry`; `this` is the element. `onInView: 'reveal'` → `el.call('reveal', entry)`.
- ONE shared IntersectionObserver per document + threshold + `rootMargin`, created by the first element that declares one of the events, disconnected with the last. No element declares them → no observer, no cost.
- Observed when the element gets its node; unobserved on removal and once its `once` handlers ran. An `if:`-hidden element leaves the view.
- Entries delivered together run in delivery order and share `entry.time` (count them for a stagger).
- No IntersectionObserver (SSR / brender, jsdom) → nothing observed, nothing runs. Never hand-roll an IntersectionObserver in `onRender` for this.
- So a start state that hides the element stays hidden in a server render, and the page is stored with a blank block until the client takes over. Start in the final state when `el.context.ssr === true` (the example's `data.rise`; FRAMEWORK.md §8 → In the server render).

The smbls embed (`SymbolsEmbed`) has neither feature: `onInView` / `onLeaveView` never fire there, and `{ always: true, handler }` is not a handler (RUNNING_APPS.md → Embed Bundle).

State hooks:

- `onStateInit(el, data, ctx, options)` runs in create(), before `onInit`, while the element builds its OWN state from plain data (an object or function `state:`, or the app root from context state). `data` is a new plain object with the initial values (never the shared definition); what the handler writes into it is in the state. It does not run for a string-path state, a ready-made store, a function that returns a store, or an element that only shares its parent's state. The return value is ignored.
- `onStateCreated(el, s, ctx, options)` runs in create(), before `onInit`, after the state exists with its methods: for every element that declares `state` (object, function, string path, store) and for the app root from context state; not for an element that only shares its parent's state.
- `onBeforeStateUpdate(el, s, ctx, { changes, options })` runs on the element that OWNS the state, before `s.update()`, `s.replace()`, `s.set()` or `s.quietUpdate()` writes. Return `false` to cancel: nothing is written, `onUpdate` does not run, the call still returns the state. `changes` is the object that will be applied, so the handler may adjust it. `{ preventBeforeStateUpdateListener: true }` skips it. A direct write (`s.key = v`), `s.toggle()` and a descendant's state change do not run it.

#### Which hook runs on which state change

| Hook | Runs when | Arguments |
| -- | -- | -- |
| `onUpdate` | `el.update(…)` on that element; and on the element that OWNS a state store when that store's `update()` is called | `(el, s, ctx, opts)`; from a store update `(el, s, ctx)`, no opts, before the DOM updates |
| — | a direct write (`s.key = v`), `s.replace`, `s.toggle` | no `onUpdate` runs |
| — | a parent's or the root's state changes | a descendant's `onUpdate` never runs |
| `subscribeTo: ['key', 'a.b']` (or a function, resolved once) | those ROOT-state keys change | `onBeforeUpdate(el, s, ctx, { updateBySubscription: true })`, the reactive props re-run, then `onUpdate(el, s, ctx)` |
| `stateDeps: [selector \| 'key']` + `onStateUpdate` | a selected value changes (`!==`); never on first render, never without `stateDeps` | `(el, s, ctx, { prev, next })` |

To react to a state value from ANY element (root state included), use `stateDeps` + `onStateUpdate` or a reactive prop — not `onUpdate`. This includes state-driven attributes such as `aria-invalid`: `'aria-invalid': (el, s) => Boolean(s.error) || null`. A selector is a function `(el, s, ctx) => value` or a string key of the element's own state.

```js
export const MessageList = {
  stateDeps: [(el, s) => s.root.activeChannelId],
  onStateUpdate: (el, s, ctx, { prev, next }) => {
    el.call('markRead', prev[0])     // leaving a channel marks it read
  }
}
```

- The framework reads every selector inside its own effect, so each one is subscribed even when the handler reads it only on some branches.
- The handler runs only when a selector value changed (`!==`), never on the first render. `prev` and `next` are the selector values, in `stateDeps` order.
- Without `stateDeps`, `onStateUpdate` never runs.
- For a value you only display, a reactive prop (`text: (el, s) => …`) is still the answer (Rule 51). Use `onStateUpdate` for side effects: calls, scroll, focus, a third-party API.

`onBeforeRemove` fires inside `dispose(element)` BEFORE effects, event listeners, and state are destroyed — the handler can still access `el.state`, `el.context`, and call methods. `onRemove` fires AFTER DOM detach and `state.destroy()` but BEFORE refs are cleared — safe for logging `el.key` / `el.parent`. Both hooks are wrapped in try/catch so a misbehaving handler does not block sibling cleanup.

### Event Detection Rule

A key is an event handler when:

```js
key.length > 2 && key[0] === 'o' && key[1] === 'n' &&
  key[2] >= 'A' && key[2] <= 'Z' &&     // onClick, onRender — NOT "one", "only"
  isFunction(value)
```

Detection is structural (pattern of `onUpper...`), not registry-based — any custom event name like `onCustomThing` works as long as it's a function. A DOM event handler may also be a string naming a project function (`onClick: 'toggleMenu'` → `el.call('toggleMenu', e)`) or the options form below.

### Options Form — `{ capture, passive, once, selector, handler }`

Every DOM `onXxx` also takes an options object, the shape the document / window family below takes:

```js
onScroll:  { capture: true, passive: true, selector: '.ql-editor', handler: (e, el, s) => {} }  // a scroll INSIDE the element
onPaste:   { capture: true, handler: (e, el, s) => {} }        // runs before an inner node's own listener
onWheel:   { passive: false, handler: (e, el, s) => {} }       // may call e.preventDefault()
onClick:   { selector: 'figure', handler: (e, el, s) => {} }   // only targets inside a <figure> of this element
onKeydown: { once: true, handler: 'closeOnEscape' }             // string → el.call('closeOnEscape', e)
```

- A plain handler hears an event only on its way UP: a `scroll` inside the element never bubbles to it, and a `paste` / `keydown` reaches it after an inner node's own listener. `capture: true` hears both, first.
- `capture`, an explicit `passive` or `once` bind the listener on the element's own node with exactly those options (a plain handler shares one delegated listener). Touch and wheel stay passive unless `passive` is declared.
- `selector`: the handler runs only when the event target's closest match lies inside the element's node; an invalid selector matches nothing.
- Same `(e, el, s, ctx)` signature; removed on dispose like every handler. This is the declared way to listen on nodes a library owns (see `Bridge` in COMPONENTS.md) — never `addEventListener` (FA503).

### Global-Target Events — `onDocumentXxx` / `onWindowXxx` / `onVisualViewportXxx` / `onMediaQueryChange`

Some events never reach an element you own: a third-party widget portaled into
`document.body` (docsearch modal, date pickers), "outside click" / Escape for a
layer, window `resize` / `scroll` / `hashchange`. Raw `document.addEventListener`
is banned (FA503 — it skips DOMQL's lifecycle and leaks on unmount). Declare the
listener flat on the component instead; DOMQL owns its lifecycle:

```js
onDocumentClick:       (e, el, s, ctx) => {},              // document, bubble phase
onDocumentKeydown:     'closeOnEscape',                     // string shortcut → el.call('closeOnEscape', e)
onDocumentPointerdown: { capture: true, handler: (e, el, s) => {} }, // options form
onWindowResize:        (e, el, s) => {},                    // window family, same shapes
onWindowScroll:        { passive: true, handler: (e, el, s) => {} }
```

Two more TARGETS, identical shapes and identical lifecycle — neither is the
element's document or its window, so neither has any other declarative form:

```js
onVisualViewportResize: (e, el, s) => {},                   // window.visualViewport
onVisualViewportScroll: (e, el, s) => {},                   //   soft keyboard, pinch-zoom
onMediaQueryChange:     { query: '(max-width: 768px)', handler: (e, el, s) => {} },
onMediaQueryChange:     { query: 'mobileL', handler: (e, el, s) => {} },   // a designSystem.media key
onMediaQueryChange:     [ { query: '@tabletS<', handler: a },              // '@' form, any key of the table
                          { query: '(pointer: coarse)', handler: b } ]
```

`query` may name a key of the design system's media table — the query `'@mobileL'` blocks use, so a moved breakpoint moves the listener too: `'@name'` (an unknown key registers nothing and logs one dev warning), a bare `'name'` (when the table has that key; any other string is a raw media query, as before), or `'@media <query>'`. A table value that is not a media query (`@supports`, `@container`, a theme selector) registers nothing.

`matchMedia(query)` MINTS its target, so the query is the target's identity and
travels in the options form — a CSS media query cannot be spelled in a prop
name. That is also why `onMediaQueryChange` alone accepts an ARRAY: each entry
is a different target, not a second handler on one target. `e.matches` carries
the new answer. A `MediaQueryList` with only `addListener`/`removeListener`
(Safari < 14) is watched and unwatched through those; no `visualViewport` /
no `matchMedia` on the window → no listener and no throw, like a missing
document.

**A custom event name that is not identifier-shaped** (a namespaced
`CustomEvent`) is still a key — it just has to be QUOTED, because everything
after the prefix is taken verbatim and lowercased:

```js
'onWindowSymbols:auth-callback': (e, el) => el.call('onAuth', e.detail)
'onDocumentApp-ready':           'handleReady'
```

Two limits follow from the convention: the name is lowercased (declare the
event lowercase, which is the DOM convention anyway — `symbols:authCallback`
is NOT reachable), and the character right after the prefix must be `A-Z` —
the rule that keeps `onWindows` / `onDocuments` ordinary props instead of
events.

Contract: registered ONCE when the element gets its node; torn down in
`dispose()` (no `onRemove` bookkeeping); the handler runs only while the
element is CONNECTED (an `if:`-hidden element is inert and re-arms when shown);
the target is the element's OWN document / window (iframe apps listen in the
frame); no document → no listener (SSR-safe). `capture` / `passive` / `once`
come from the options form; touch and wheel default to passive. Name = the
DOM event lowercased after the prefix (`onDocumentVisibilityChange` →
`visibilitychange`, `onWindowHashChange` → `hashchange`).

The element's OWN document is the only document a component can name. A host
element cannot declare a listener INSIDE an iframe it renders: an iframe that
hosts its own DOMQL app is the supported shape, and every component in that
inner app already gets the frame's document from plain `onDocumentXxx`.

`onWindowLoad` runs once when the page loads. When the page loaded before the element existed (smbls renders asynchronously, so an app root often mounts after `load`), it runs once right after the element is created, with the same `(e, el, s, ctx)` arguments. It does not run during server-side rendering.

### Async Events

```js
onRender: async (el, s) => {
  try {
    const result = await el.call('fetchData', s.id)
    s.update({ data: result })
  } catch (e) {
    s.update({ error: e.message })
  }
}
```

> Modern apps prefer the declarative `fetch:` prop over imperative `onRender + window.fetch`. See SYNTAX → Data Fetching.

---

## State

### Define, Read, Update

```js
// Define
state: { count: 0, open: false, selected: null }

// Read in reactive props — flat (el, s) signature
text:        (el, s) => s.label,
opacity:     (el, s) => s.loading ? 0.5 : 1,
isActive:    (el, s) => s.active === el.key

// Update from events
onClick: (e, el, s) => {
  s.update({ open: !s.open })   // partial update: assigns each TOP-LEVEL key given, keeps the rest
  s.auth.update({ step: 2 })    // partial update of a nested object: its own store keeps auth's other keys
  s.replace({ open: false })    // shallow replace (removes other keys)
  s.set({ open: false })        // alias for replace
  s.reset()                     // restore to initial parsed state
  s.toggle('open')              // flip boolean
  s.add('items', { id: 1 })     // APPENDS to an array key, MERGES a plain object into an object key, SETS a new/scalar key
  s.remove('selected')          // delete key
  s.setByPath('user.name', 'X') // dotted path
}
```

### Root and Parent State

```js
// Read
const root   = el.getRootState()
const ctx    = el.getContext()
const value  = el.getRootState('user')   // root.user

// Update from anywhere
s.rootUpdate({ activeModal: true })
s.parentUpdate({ open: false })

// Or via path
s.root.update({ x: 1 })
s.parent.update({ y: 2 })
```

**A key an element's state does not hold falls back to the ROOT state.** An element's own state (`state: { … }`, each `childrenAs: 'state'` child) reads a key it does not hold — absent, or holding `undefined` — from the root state (the app's `state.js`), never from its parent:

```js
// state.js → export default { lang: 'ka', active: true }
Row: { state: { id: 1 }, text: (el, s) => s.lang }    // 'ka': the row holds no `lang`
// childrenAs: 'state' rows that carry no `active` key all read the ROOT's `active`:
isActive: (el, s) => s.active                          // true on EVERY row
```

- The fallback read is reactive (a later root write re-runs it), but it is not the child's data: `s.parse()`, `s.keys()`, `Object.keys(s)` and `'key' in s` leave it out.
- A write through the child (`s.update({ active: false })`) creates the child's own key, which shadows the root's from then on. A nested object inside a state (`s.auth`) has no fallback.
- So give list items every key they read (an explicit `active: false`), or pick names the root does not use; read app state on purpose through `s.root.key`.

### Targeted Updates (Performance)

```js
s.root.update(
  { activeModal: true },
  { onlyUpdate: 'ModalCard' }    // only ModalCard subtree re-renders
)
```

---

## State Methods — Full Reference

| Method | Purpose |
| -- | -- |
| `s.update(value, opts?)` | Returns the state at once (the DOM updates in a later microtask). Assigns each top-level key of `value`, keeps the keys it does not name, triggers reactivity. A nested plain object is REPLACED as a whole, not merged: `s.update({ auth: { modal: 'x' } })` drops `auth`'s other keys. For a partial nested write use the nested store's own `update` (`s.auth.update({ modal: 'x' })`) or `s.setByPath('auth.modal', 'x')`; to reset a nested object, write the whole object (`s.update({ form: { values: {}, dirty: false } })` sets all of `form`) |
| `s.replace(value, opts?)` | Replace entire state (drops missing keys) |
| `s.set(value, opts?)` | Alias for replace |
| `s.clean(opts?)` | Remove all keys |
| `s.parse()` | Snapshot as plain object — the keys the state HOLDS. A key a reactive prop only READ (and nothing wrote) is not in it, nor in `s.keys()`, `Object.keys(s)` or `'key' in s`; the read still subscribes, so the prop re-runs when the key arrives |
| `s.keys()` | Property names (held keys only, as above) |
| `s.values()` | Property values (held keys only) |
| `s.destroy(opts?)` | Destroy underlying signal store |
| `s.add(key, val, opts?)` | Append `val` to an array-valued key; merge a plain-object `val` into an object-valued key; set when the key is new or scalar. NOT the v3 `state.add(value)` form — that one no longer exists (`s.items.add(x)` is not a function). |
| `s.toggle(key, opts?)` | Flip boolean |
| `s.remove(key, opts?)` | Delete property |
| `s.setByPath(path, val, opts?)` | Set via dotted path |
| `s.getByPath(path)` | Read via dotted path |
| `s.removeByPath(path, opts?)` | Delete via dotted path |
| `s.setPathCollection(paths, val, opts?)` | Multi-path set |
| `s.removePathCollection(paths, opts?)` | Multi-path remove |
| `s.reset(opts?)` | Restore to parsed snapshot |
| `s.apply(fn, opts?)` | `fn(s)` returns new merged value |
| `s.applyFunction(fn, opts?)` | `fn(s)` mutates in place, then update |
| `s.applyReplace(fn, opts?)` | `fn(s)` returns full replacement |
| `s.$settled()` | Promise that resolves with the state once the DOM of the pending writes is applied (see below) |
| `s.quietUpdate(value)` | Update without triggering listeners |
| `s.quietReplace(value)` | Replace without triggering listeners |
| `s.rootUpdate(obj, opts?)` | Update root state from anywhere |
| `s.parentUpdate(obj, opts?)` | Update parent state |
| `s.root` | Root state reference |
| `s.parent` | Parent state reference |

### Reserved store-method names — data wins, `$`-prefixed form always reaches the method

`update`, `parse`, `clean`, `keys`, `values`, `replace`, `add`, `remove`, `destroy`, `quietUpdate` are both store methods AND legal data-key names (e.g. `state: { add: {...}, keys: [...] }` is valid — a shopping-cart `add` field, a document's `keys` list). Reading one of these keys off a store follows this order:

1. **A data key with that name wins.** If the store holds a signal for `add`, `s.add` returns the DATA, not the method — a colliding key is never silently unreadable.
2. **The `$`-prefixed form is always the method**, regardless of collisions: `s.$update(...)`, `s.$add(...)`, `s.$keys()`, `s.$values()`, `s.$replace(...)`, `s.$remove(...)`, `s.$destroy()`, `s.$quietUpdate(...)`, `s.$parse()`, `s.$clean()`. Framework internals use these forms exclusively so they never break on a colliding data shape.
3. **A one-time console warning** fires the moment a reserved name is written as data, naming the key, its state path, and the `$` escape hatch.

```js
// state.cart has a data field legitimately named `add`
state: { cart: { add: { qty: 2 }, items: ['sku-1'] } }

text: (el, s) => s.cart.add.qty          // ✅ reads the DATA — 2 (not the store method)
onClick: (e, el, s) => s.cart.$add('items', 'sku-2')   // ✅ calls the store's `add` METHOD via $ prefix
```

Prefer renaming the field (`cart.items` instead of `cart.add`) when practical — the `$` escape hatch exists for cases where the collision is unavoidable (e.g. CMS-defined field names), not as the default pattern.

**The ROOT state follows the same rule** (smbls 3.14.845). The boot merge of `state.js` / `context.state` keeps every data key:

- A root key named like an ELEMENT method (`log`, `call`, `warn`, `error`, `verbose`, `lookup`, `variables`, `if`, `getRoot`, …) is plain data: `state: { log: [] }` boots as `[]` and `s.log.length` works. Element methods live on the element (`el.call`, `el.log`), never on the state.
- A root key named like a STORE method (`keys`, `values`, `update`, `rootUpdate`, `add`, …) is data too, as in a nested store: `s.keys` reads the data, `s.$keys()` / `s.$values()` / `s.$update({…})` call the method, and the store warns once per path.
- Only the store's own links `parent` and `root` (and `__*` keys) are never data: the merge skips them with a dev warning.

```js
// symbols/state.js
export default { log: [], keys: ['a', 'b'], count: 0 }

// symbols/components/Summary.js
export const Summary = {
  Count: { text: (el, s) => `${s.root.log.length} events, ${s.root.keys.length} keys` },          // data
  Button: { text: '{{ add | polyglot }}', onClick: (e, el, s) => s.root.$update({ count: s.root.count + 1 }) }  // method
}
```

```js
// apply vs applyFunction
s.apply((cur) => ({ ...cur, count: cur.count + 1 }))   // returns new value
s.applyFunction((cur) => { cur.count++ })              // mutates in place
```

### Awaiting the DOM after a write — `$settled()`

`s.update(value, opts?)` returns the state at once; the DOM updates in a later microtask (a large cascade can take longer). To continue once the DOM is applied, await `$settled()`:

```js
onClick: async (e, el, s) => {
  await s.update({ open: true }).$settled()   // resolves with the state once the DOM is applied
  el.Panel.node.focus()
}
// after any write (s.key = v, s.toggle, …): await s.$settled()
// with no store at hand: import { settled } from 'smbls' (or '@symbo.ls/signal'); await settled()
```

It does not cover opt-in deferred children (`yieldChildren` / `mountYield`) or `onMounted`. Never write `await s.update(…)` alone to wait for the DOM.

### State Update Options

| Option | Purpose |
| -- | -- |
| `onlyUpdate` | Limit re-render to a specific subtree by key |
| `preventUpdate` | Skip element update |
| `preventStateUpdate` | Skip state update step |
| `preventUpdateListener` | Skip update event listeners |
| `preventUpdateAfter` | Skip post-update hooks |
| `lazyLoad` | Lazy-load updates |
| `quiet` | Update store without firing subscribers |

### State String References (Path Syntax)

```js
state: '.'                 // current element's state (parent if no local)
state: '../path/to/field'  // dotted path from parent
state: '~/lang'            // dotted path from root
state: 'fieldName'         // direct lookup in parent state, polyglot fallback
```

```js
// Parent has state: { userProfile: { name: 'John' } }
// Child:
state: 'userProfile'   // child inherits the userProfile slice
```

If the path doesn't resolve, polyglot translations for the active language are checked.

---

## Reactive Props — Function Signatures

Every reactive prop is `(el, state, context?) => value`:

```js
// Text content
text:  (el, s) => s.user.name
text:  (el, s) => `${s.first} ${s.last}`        // composed
text:  '{{ hello | polyglot }}'                  // template string (reactive on lang change)

// HTML (use sparingly, NEVER for component composition — use children instead)
html:  (el, s) => sanitize(s.markdown)

// CSS values
color:    (el, s) => s.active ? 'primary' : 'gray.5'
fontSize: (el, s) => s.compact ? 'Y' : 'Z'
hide:     (el, s) => !s.root.searchOpen

// HTML attributes
href:        (el, s) => `/user/${s.id}`
disabled:    (el, s) => s.loading
placeholder: '{{ search | polyglot }}'

// Conditional rendering
if:   (el, s) => s.root.modalOpen
show: (el, s) => s.root.activeView === 'home'

// Value (input/textarea/select — preserves cursor on re-render)
value: (el, s) => s.formField

// Style object
style: (el, s) => ({ transform: `translateX(${s.x}px)` })
```

**Always `(el, s)`. NEVER `({ state })` or `({ props, state })` — those destructured signatures are forbidden.**

### Reactive CSS Props Write Inline — a Declared Longhand Still Wins

A STATIC CSS prop compiles to an atomic **class**. A REACTIVE one (a function) is written **inline** on the node, because its value changes. Inline beats a class in the cascade whatever order you wrote the two keys in.

That split used to lose a shorthand/longhand pair: `transition` (reactive, inline) reset `transition-property` (static, class), so the element animated `all` and every layout property with it.

```js
export const NkButton = {
  transitionProperty: 'background, color',              // class
  transition: (el, s) => s.pressed ? 'A' : 'B defaultBezier'   // inline
}
// -> transition-property: background, color   (the declared longhand wins)
```

The framework re-asserts the element's OWN declared longhands inline, after the reactive shorthand, so the longhand wins — which is what a longhand written beside a shorthand asks for. It holds for every shorthand family: `margin`/`marginTop`, `padding`/`paddingBlock`, `background`/`backgroundColor`, `border`/`borderTopWidth`, `borderRadius`/`borderTopLeftRadius`, `outline`/`outlineColor`, `gap`/`rowGap`, `flex`/`flexBasis`, `inset`/`top`, `overflow`/`overflowX`, `font`/`lineHeight`, `grid`/`gridTemplateRows`, `transition`/`transitionProperty`, plus `mask`, `listStyle`, `textDecoration`, `columns` and the `place-*` group.

Three things the rule deliberately does NOT do:

- **A reactive longhand still beats a static shorthand.** `transition: 'B defaultBezier'` plus `transitionProperty: (el, s) => …` is unchanged — the reactive value is the one that moves, so it stays on top.
- **A longhand that resolves to a theme PAIR stays in its class.** `backgroundColor: 'primary'` under `@dark`/`@light` has no single inline value, so a reactive `background` still wins over it. Write the reactive half as a longhand too when you need both.
- **`style: (el, s) => ({ … })` is untouched.** The raw-style escape hatch is inline by contract and beats every class, longhand included.

A CSS block that sets the SAME property as a reactive prop — `:hover`, `:active`, `:focus-visible`, `@dark`, a media block — is emitted with `!important`, so the block still wins while it applies: `background: (el, s) => …` plus `':hover': { background: 'gray1' }` repaints on hover.

Where a preset and a prop disagree the ladder is unchanged: `theme` < design-system `class` fragment < the element's own prop. A reactive prop is the element's own prop, so it beats both.


### Shorthand vs longhand — which one wins

- Inside one component a longhand always beats its shorthand, whatever the key order: `{ paddingTop: 'B', padding: 'A' }` keeps `padding-top: B`.
- Across the merge (base → the `extends` array in order → the component → `childProps` / the instance) a later layer's shorthand overrides an earlier layer's longhand when its value states that longhand.
- One-value-type shorthands state every longhand: `borderWidth`, `borderStyle`, `borderColor`, `padding`, `margin`, `inset`, `gap`, `overflow`, `borderRadius`, `place*`, `scrollMargin` / `scrollPadding`. An instance's `padding: 'A'` replaces the base's `paddingTop`.
- A line shorthand (`border`, `borderTop`…, `outline`, `columnRule`) states width, style and colour when it has three words. With fewer words it states only a style keyword: `border: 'none'` resets only the style.
- Positional shorthands (`background`, `transition`, `animation`, `font`, `flex`, `grid`, …) never remove a base longhand. To override one, write the longhand.
- A `theme:` preset sits below every layer. A shorthand the element declares (or a `class` fragment sets) overrides each theme longhand it states, in every colour scheme: `{ extends: 'Input', border: '1px solid grayMid' }` paints grayMid, not the `field` theme's `borderColor`. Over a theme a shorter value also states what its words name: `0` or `none` alone states width and style (`border: '0'` turns off a theme's `borderWidth`/`borderStyle` line), a length states the width, one colour (`background: 'white'`) states `background-color`. A colour is never read out of fewer than three words, so `border: '1px solid'` keeps the theme's border colour, and `background: 'white'` keeps a theme's `backgroundImage`. Between layers the rule above stays as it is.
- A pseudo or selector block key gets `!important` when the element writes the same property, or any member of its shorthand family, inline. So `':focus-visible': { outlineColor: 'accent' }` recolours a `Link` / `Focusable` ring.

### Static CSS props — a longhand class beats its shorthand class

Two STATIC props of one family compile to two atomic classes of equal specificity. The engine places every longhand class AFTER every shorthand class of its family (one base sheet per shorthand depth: `border` < `borderTop` < `borderTopColor`), so the longhand always wins — whatever order you wrote the keys in, and whichever element on the page used either class first. Before the release that carries this change, the winner depended on which class the page created first.

```js
export const KitField = {
  transition: 'A defaultBezier',
  transitionProperty: 'background-color, border-color'   // always wins: only these animate
}
```

The families cover every standard CSS shorthand, nested ones included: `font` > `fontVariant` > `fontVariantNumeric`, `background` > `backgroundPosition` > `backgroundPositionX`, `border` > `borderBlock` > `borderBlockStart` > `borderBlockStartColor`, `animation` > `animationRange` > `animationRangeStart`, `cornerShape` > `cornerTopShape` > `cornerTopLeftShape`, `scrollMargin` > `scrollMarginBlock` > `scrollMarginBlockStart`, `whiteSpace`/`textWrap` > `textWrapMode`, and the rest of the list above. Only one-property atomic classes move; a global rule (`injectGlobal`) keeps its place. Conditional rules (`:hover`, `@media`, `@dark`, `.isX`) still beat every flat rule, shorthand or longhand.

Across `extends` layers the merge rule above decides, not the class order: a consumer's three-word `border: '1px solid red'` replaces a base's `borderStyle: 'none'`. A consumer that wants to change one part of a base shorthand writes that longhand (`borderColor: 'red'`).

### Textarea `autoGrow` — rows Floor, max-height Cap

```js
Composer: { tag: 'textarea', rows: 3, autoGrow: true }                 // never below 3 lines
Note:     { tag: 'textarea', rows: 2, autoGrow: { max: '40dvh' } }     // 2 lines .. 40dvh, then scroll
Draft:    { tag: 'textarea', rows: 1, autoGrow: (el, s) => !s.full && { max: '35dvh' } }
```

- **Floor:** an explicit `rows` is the minimum height (rows x line height + padding). With `lineHeight: 'normal'` (the default) the framework measures one line of the textarea's font. Without `rows` the floor is the content (one line); a `minHeight` prop still floors it through the cascade.
- **Cap:** `autoGrow.max` or a `maxHeight` prop. The height stops at the cap, rounded DOWN to whole lines, and the box scrolls (`overflow-y: auto`, removed again when the content fits).
- **Exact height:** the written `height` shows exactly the content for either `boxSizing` (border-box adds the borders, content-box drops the padding) — no 2px inner scroll.
- **autoGrow owns `height`:** a transition that covers `height` (`transition: 'all …'` or `'height …'`) is cancelled on every measure, so the box never animates its height and always shrinks after text is deleted. Other transitions on the node (a border-color focus fade) keep running; the inline `transition` is never touched.
- It re-measures on input, on a programmatic `value` change, on a width change, and when web fonts load. Never write `el.node.style.height` yourself.
---

## `attr` (HTML Attributes)

`attrs-in-props` auto-detects 600+ standard HTML attributes per tag — place them at root. Use `attr: {}` ONLY for non-standard or rare attributes.

```js
export const Input = {
  tag: 'input',
  // standard attrs at root (auto-detected)
  type:        (el, s) => s.inputType,
  autocomplete:'off',
  placeholder: (el, s) => s.placeholder,
  name:        (el, s) => s.name,
  disabled:    (el, s) => s.isDisabled || null,    // null removes attr
  required:    (el, s) => s.required,
  role:        'textbox',
  tabindex:    (el, s) => s.tabIndex,
  // aria/data shorthand
  aria: {
    label:    (el, s) => s.aria?.label || s.text,
    invalid:  (el, s) => Boolean(s.error)
  },
  data: { testId: 'main-input' }
}
```

Return `null` or `undefined` from a prop function to remove the attribute.

### Which names are attributes — both spellings

- The per-tag tables follow the WHATWG HTML attribute index: every attribute an element has is a flat prop on it — `srcset`, `sizes`, `fetchpriority` on `<img>`; `inputmode`, `enterkeyhint`, `popover`, `nonce` on any tag; `commandfor` on `<button>`; `blocking` on `<link>` / `<script>` / `<style>`.
- Every multi-word attribute works in its HTML spelling and in camelCase: `fetchpriority` / `fetchPriority`, `inputmode` / `inputMode`, `httpEquiv` → `http-equiv`, `acceptCharset` → `accept-charset`.
- An element-specific camelCase spelling applies only on a tag that has the attribute: `fetchPriority` on a `<div>` stays a custom prop, exactly like `fetchpriority`. The camelCase spellings of global attributes (`tabIndex`, `inputMode`, `enterKeyHint`, `contentEditable`, `spellCheck`, `autoCapitalize`, `autoCorrect`, `accessKey`, …) apply on every tag.
- Microdata is lowercase only (`itemid`, `itemtype`, `itemprop`, …): `itemId` / `itemType` stay custom props.
- A boolean on an enumerated attribute is written as the keyword it expects: `draggable`, `contenteditable`, `spellcheck`, `writingsuggestions` and `aria-*` → `"true"` / `"false"`; `autocorrect` → `"on"` / `"off"`; `translate` → `"yes"` / `"no"` (through `attr: {}` only — a flat `translate` is the CSS property).
- `attr: {}` is left for names no table lists (non-standard attributes) and for an attribute whose flat key means something else on that tag: `translate` and `width` / `height` on an `<img>` are CSS, `content` and `scope` are framework keys (frank-audit FA105 checks this per tag).

### Updating an attribute prop after mount

`el.update({ … })` and `el.setProps({ … })` write an attribute prop to the node after mount — `disabled`, `checked`, `readonly`, `required`, `hidden`, ARIA props (`ariaPressed`) and any other attribute valid for the tag, in either spelling (`readOnly` / `readonly`, `tabIndex` / `tabindex`, `srcSet` / `srcset` on the built-in `Input`, `Button` and `Img` too). `false`, `null` and `undefined` remove a presence attribute; an ARIA attribute keeps the literal `'false'`. If the element declares a function for that attribute (the built-in `Button`'s `disabled`, `Input`'s `attr.disabled`), that function runs again and its result wins — a factory that reads state keeps following state. CSS props and non-attribute props are never written as attributes. (smbls `217e7c7eb`)

```js
el.update({ disabled: true })      // node.disabled === true — not focusable, not clickable
el.update({ disabled: false })     // the attribute is removed
el.update({ ariaPressed: false })  // aria-pressed="false" — literal, never removed
```

---

## `text` and `html`

```js
export const Label = { text: (el, s) => s.label }
export const Badge = { text: 'New' }
export const Price = { text: (el, s) => `$${s.amount.toFixed(2)}` }
export const Welcome = { text: '{{ welcome | polyglot }}' }   // template literal — polyglot

// html — XSS risk; ONLY for trusted, sanitized markup. Prefer children.
export const RichText = { html: (el, s) => s.sanitizedHtml }
```

NEVER use `html:` to compose components — use children + `text:` (Rule 31).

---

## Children

### Named Children (Auto-Extend by PascalCase)

```js
export const Card = {
  flow: 'y',
  Header: {
    flow: 'x',
    Title: { text: (el, s) => s.title }
  },
  Body: { html: (el, s) => s.content },
  Footer: {
    CloseButton: { extends: 'SquareButton', icon: 'x' }
  }
}
```

`Header`, `Body`, `Footer` auto-extend if a registered component matches. `Header` is a default-library component — use a distinctive name like `CardHeader` if you want a clean wrapper without inherited styling.

### `childExtends` (One Type for All Children)

```js
export const NavList = { childExtends: 'NavLink' }
```

### `childExtendsRecursive`

Apply to ALL descendants:

```js
export const Tree = { childExtendsRecursive: { fontSize: 'A' } }
```

### `children` — Static Array

```js
{ children: [{ text: 'Item 1' }, { text: 'Item 2' }] }
```

### `children` — Reactive Function

```js
export const DropdownList = {
  children: (el, s) => s.options || [],
  childExtends: 'OptionItem'
}
```

### `childrenAs`

Control how data items map to children:

| Value | Behavior |
| -- | -- |
| `'props'` (default) | Each item flattened onto the child as props |
| `'state'` | Each item becomes the child's state |
| `'element'` | Each item used directly as element definition |

```js
{ children: [{ text: 'Hello' }] }                                       // → flat props
{ children: [{ count: 5 }], childrenAs: 'state' }                       // → state
{ children: [{ tag: 'span', text: 'Hi' }], childrenAs: 'element' }      // → definition
```

### Reconciliation Keys

When `children` is a function, the framework reconciles by `child.key || childProps?.key || index`. Provide stable keys for collections that re-order:

```js
children: (el, s) => s.items.map(it => ({ key: it.id, ...it }))
```

An element key is a string. A NUMBER key (a numeric id, a row index) is normalized to its string form where it enters the engine, so `key: 7` and `key: '7'` are the same row, and `key: 0` is the key `'0'` (smbls `e3a9bcc3e`). Runtimes up to smbls 3.14.805 did NOT normalize: a row keyed by a number with its own nested children and no `childExtends` threw `key.indexOf is not a function` (minified: `g.indexOf is not a function`) and was dropped, and a `key: 0` row lost its `data-key`. On those runtimes write `key: String(it.id)`.

Keyed reconcile preserves both **identity and order**: kept nodes are diffed against the new key order and repositioned in the DOM (`insertBefore`) rather than left wherever they were first inserted — so a pure reorder, or a new item landing mid-array, moves existing nodes instead of destroying and recreating them. Moving a node this way preserves its listeners, focus, and any in-progress CSS transition on it. No key-rotation workaround is needed to force a reorder to "take" — a plain re-sort of the array with stable keys is sufficient.

What happens to a row whose key is still there depends on `childrenAs`:

| | Row kept | Row re-created |
| -- | -- | -- |
| `childrenAs: 'state'` | always — its state is patched in place (`state.replace(item)`); keys the item gains or loses reach the row's factories | never |
| plain rows (no `childrenAs: 'state'`) | when its definition is **equal** to the one it was built from | when its definition changed — that row alone |

A plain row's definition is compared to a snapshot taken when the row was built: plain objects and arrays by value, everything else — a function, a store, an element, a class instance, and the component an `extends` names — by identity. A kept row keeps its element, node, local state and DOM state (typed input values, focus, scroll) and fires no lifecycle hook; a re-created row fires `onRemove` for the old one and `onInit` … `onRender` for the new one, removals first. `content` and named siblings declared next to the array are not rows and are never touched by a re-run.

```js
// ✅ Rows survive a re-run unless their own data changed
children: (el, s) => s.items.map(it => ({ key: it.id, tag: 'li', text: it.label }))

// ⚠️ A fresh closure per row is a new function every run: every row is re-created
children: (el, s) => s.items.map(it => ({ key: it.id, text: it.label, onClick: () => open(it.id) }))
// ✅ Read the row from the element instead — one shared function, rows survive
const openRow = (e, el) => el.call('open', el.key)
children: (el, s) => s.items.map(it => ({ key: it.id, text: it.label, onClick: openRow }))
```

For rows whose data changes often (labels, counts, flags), prefer `childrenAs: 'state'` + `childExtends`: the row is patched in place and only the props that read the changed keys re-render. The smbls embed has no plain-row diff: there a plain `children` factory rebuilds its rows on every re-run (RUNNING_APPS.md → Embed Bundle).

A `children` function runs **once** at mount (its reactive effect's first run builds the list), and a new row is inserted into the DOM once, at its final place — a `MutationObserver` sees one `+row` per new row.

Runtimes up to smbls 3.14.837 differ: a plain `children` function was rebuilt from scratch on every re-run (every row removed and created again, named siblings and `content` dropped), every `children` function ran twice at mount, every new row was inserted twice (`+row −row +row`), and a `childrenAs: 'state'` row that GAINED a key on a later update (after an update that still lacked it) never rendered it — give every item the same keys, empty ones included, on those runtimes.

### A key that equals an HTML tag name BECOMES that tag

With no explicit `tag:`, the tag comes from the element's KEY (`detectTag`, `packages/element/src/cache.js`): the key is lowercased, a `_suffix` / `.suffix` is stripped, and if the rest is a known HTML tag name, that is the tag. This is what makes `Nav: {}` a `<nav>` — and it applies to DATA keys too. A row keyed by data is rendered as whatever element its data id happens to name:

| Data key (measured on dev.my.symbols.app, smbls 3.14.805) | Rendered as | Effect |
| -- | -- | -- |
| a service row keyed `canvas` | `<canvas>` | invisible — a canvas never paints its child nodes |
| a row keyed `search` | `<search>` | a landmark element, not a plain row |
| a row keyed `data` | `<data>` | an inline element, not a block row |

The same holds for `input` (a void `<input>` — its children never render), `dialog` (hidden until opened), `button`, `a`, `form`, `select`, `option`, `label`, `img`, `video`, `menu`, `main`, `nav`, `time`, `mark`, `code`, … — every key that is a tag name. `fragment` and `string` are special tags too (a DocumentFragment, a text node). Only document-structure and table-internal names (`html`, `head`, `body`, `script`, `style`, `title`, `template`, `th`, `tr`, `td`, `thead`, `tbody`, …) are never inferred.

**Rule: a row keyed by DATA declares its tag.** Put `tag: 'div'` on the row — on the `childExtends` component, or through `childProps` — or give the key a prefix that is not a tag name:

```js
// ❌ Row tag comes from the data id — 'canvas' becomes an invisible <canvas>
ServiceList: {
  childrenAs: 'state',
  childExtends: 'ServiceRow',          // ServiceRow declares no tag
  children: (el, s) => s.services       // [{ key: 'canvas', … }, { key: 'search', … }]
}

// ✅ The row declares its tag — every row is a <div> whatever its key
ServiceList: {
  childrenAs: 'state',
  childExtends: 'ServiceRow',
  childProps: { tag: 'div' },
  children: (el, s) => s.services
}

// ✅ Or a key prefix that no tag name matches
children: (el, s) => s.services.map(it => ({ ...it, key: 'svc-' + it.key }))
```

An explicit `tag:` always wins over the key. A declared PascalCase key that is a tag name (`Canvas: {}`, `Data: {}`) follows the same rule unless the component it auto-extends declares its own `tag` — name the key after what it is, or set `tag:`.

### `state: 'key'` (Narrow state scope) vs `childrenAs: 'state'`

Both forms are valid. **For reusability, prefer `childrenAs: 'state'`** — the child component (`TeamItem`) reads `s.field` directly without coupling to the parent's state shape, so the same `TeamItem` works for any list whose items match the shape it consumes.

```js
// ✅ Preferred — childrenAs: 'state'. Child is reusable across any list with `{ name, ... }` items.
export const TeamList = {
  state: { members: [] },
  childExtends: 'TeamItem',
  children:     (el, s) => s.members,
  childrenAs:   'state'
}
export const TeamItem = {
  Title: { text: (el, s) => s.name }
}

// ✅ Also valid — `state: 'key'` narrows scope by binding the child to a parent-state subtree.
//   Use when the parent state already has the right shape and you don't need the child to be reusable across other lists.
export const TeamList = {
  state: 'members',
  children:     (el, s) => s,
  childExtends: 'TeamItem'
}
export const TeamItem = {
  state: true,                            // required: the child opts into receiving its own state
  Title: { text: (el, s) => s.name }
}
```

### `content` (Single Dynamic Child)

```js
export const Page = { content: (el, s) => s.page }
```

### `childProps` (Inject Props Into All Named Children)

```js
export const Layout = {
  childProps: {
    onClick: (e) => e.stopPropagation()
  }
}
```

---

## Boolean / Computed Conditional Props

`is*`, `has*`, `use*` prefixes are treated as boolean conditions when followed by a function. Pair with `'.isX'` blocks (RULES Rule 19 → Conditional props):

```js
export const TabBtn = {
  isActive: (el, s) => s.activeTab === el.key,
  '.isActive': { fontWeight: '600', color: 'primary' },
  text: (el, s) => s.label
}
```

---

## `define` (Custom Property Transformers)

```js
define: {
  highlight: (param, el, state, context) => {
    if (param) el.update({ background: 'highlight' })
  }
}
```

### Built-In Defines

| Define | Purpose |
| -- | -- |
| `metadata` | SEO metadata (helmet plugin) |
| `routes` | Route definitions for the router plugin |
| `fetch` | Declarative data fetching (fetch plugin) |
| `polyglot` (context) | Polyglot translations and language switching |

```js
export const aboutPage = {
  metadata: {
    title: 'About Us',
    description: (el, s) => s.aboutText,
    'og:image': '/about.png'
  },
  fetch: { from: 'about_page', cache: '1h' }
}
```

---

## `if` (Conditional Rendering)

```js
export const AuthView = {
  if: (el, s) => s.isAuthenticated,
  Dashboard: { /* renders only when true */ }
}

export const ErrorMsg = {
  if: (el, s) => Boolean(s.error),
  text: (el, s) => s.error
}
```

`if` removes from DOM. For tabs/views, use `show:` / `hide:` (Rule 18).

---

## `scope` and `data`

```js
// scope — non-reactive per-instance storage (debounce timers, refs to libraries, etc.)
export const Form = {
  onInit: (el) => { el.scope.lastSubmitTime = 0 }
}

// data — non-reactive shared storage (no re-renders)
export const Chart = {
  data: { chartInstance: null },
  onRender: (el, s) => {
    if (el.data.chartInstance) return
    const lib = el.context.require('chartjs')
    el.data.chartInstance = new lib(el.node, { /* ... */ })
  }
}
```

> **For inter-component sharing, see PATTERNS.md § Sharing State Across Components.** Use `state` (reactive local), `el.scope` (non-reactive instance), root state via `s.root.*` / `el.getRootState()` (reactive app-wide), or `context` (boot-time config). **Never `window.*`.** Writing to `window` is not reactive, leaks across apps sharing the same browser tab, and prevents garbage collection on unmount.

---

## Element Methods

| Category | Method | Description |
| -- | -- | -- |
| **Navigation** | `el.lookup('Key')` | Find ancestor by key or predicate |
| | `el.lookdown('Key')` | First descendant by key |
| | `el.lookdownAll('Key')` | All descendants by key |
| | `el.spotByPath(['A', 'B'])` | Find by path |
| | `el.nextElement()` | Next sibling |
| | `el.previousElement()` | Previous sibling |
| | `el.getRoot()` | Root element |
| | `el.getRootState()` / `el.getRootState('key')` | App-level state |
| | `el.getRootContext()` | Root context |
| | `el.getContext()` / `el.getContext('key')` | Context (or specific key) |
| | `el.getDB()` | Alias for root state |
| | `el.getQuery(path?)` | Read root state by dotted path |
| | `el.getChildren()` | Direct children array |
| | `el.getPath()` | Ancestor key chain |
| | `el.getAdoption()` | `'adopted'` / `'replaced'` / `null`: how this element's first view came over a pre-rendered page, from its first hook (`onInit` too, since smbls 3.14.867; FRAMEWORK.md → In app code) |
| **Updates** | `el.update(value, opts?)` | Deep merge update |
| | `el.setProps(value, opts?)` | Alias for update |
| | `el.set(content, opts?)` | Replace element's `content` child |
| | `el.reset(opts?)` | Dispose + recreate from parsed definition |
| **Content** | `el.removeContent()` | Dispose & remove `content` child |
| **DOM** | `el.setNodeStyles({})` | Apply inline styles directly (escape hatch) |
| | `el.whenConnected(fn)` | Run `fn(el)` once the node is in a document — now if it is (below) |
| | `el.facesReady()` | `Promise<FontFace[]>`: the faces that draw this element's text, once they are in (3 s cap; `[]` when none applies; never rejects). Await it before you measure text; `.late` is a promise of the faces that came after the cap, or `null` (DESIGN_SYSTEM.md → `faceWait`; since smbls 3.14.865, `late` since 3.14.867) |
| | `el.checkFaces()` | check this element's face wait, and every one inside it, again: after a font change no `class` / `style` / `lang` write shows (since smbls 3.14.867) |
| | `el.remove()` / `el.dispose()` | Remove from tree, dispose effects, dispose state |
| **Functions** | `el.call('fnName', ...args)` | Lookup: `methods → functions → utils → prototype` (a protected built-in name resolves the element's own method; `log`/`warn`/`error`/`verbose` are override points) |
| **Routing** | `el.router(path, root, state?, options?)` | SPA navigation (root = `el.getRoot()`) |
| **Debug** | `el.parse(exclude)` | Plain object snapshot |
| | `el.parseDeep(exclude)` | Deep parse including children |
| | `el.keys()` | Element's own keys |
| | `el.log(...keys)` | Console.log element or specific keys |
| | `el.verbose()` | Verbose log |
| | `el.warn(...)` / `el.error(...)` | Logging helpers |
| | `el.variables()` | Resolved variables |
| | `el.getRef()` | Internal `__ref` tracking |

`el.whenConnected(fn)` runs `fn(el)` now when the element's node is in a document, else in the task of the insertion that connects it: the first render builds the app root outside the document and inserts it in one step, and an `if:` re-attach connects a node later. Use it for work that needs a connected node before the first paint — `dialog.showModal()` throws on a detached one, `focus()` does nothing there — where `onMounted` (next frame, after layout) is a frame late. It never runs for an element disposed first; a callback that throws is logged and the others still run. The built-in `Dialog` opens its `modal` this way.

```js
export const SearchField = {
  extends: 'Input',
  // onRender runs before the node is attached: a bare el.node.focus() here does nothing
  onRender: (el) => el.whenConnected(() => el.node.focus())
}
```

### Element Update Options

| Option | Purpose |
| -- | -- |
| `onlyUpdate` | Limit re-render scope to a key |
| `preventUpdate` | Skip update |
| `preventStateUpdate` | Skip state update |
| `preventUpdateListener` | Skip update listeners |
| `preventUpdateAfter` | Skip post-update hooks |
| `lazyLoad` | Lazy-load |

---

## `el.call()` — Function Lookup

Lookup order: `context.methods → context.functions → context.utils → element prototype`.

Exception — protected built-in element method names (`getRoot`, `getRootState`, `update`, `set`, `lookup`, …): `el.call(name)` resolves the element's own method, exactly like `el[name]()` — the built-in, or the app's own override declared in its `methods/`. A shared library's `methods` never replace a protected built-in. The logging hooks `log` / `warn` / `error` / `verbose` are override points: they keep the normal lookup order, and a library's version may win (see SHARED_LIBRARIES.md, "Methods named like built-in element methods").

```js
// functions/findUser.js
export const findUser = function findUser(s) {
  return s.users.find(u => u.id === s.activeUserId)
}

// component
text:    (el, s) => el.call('findUser', s).name
onClick: (e, el, s) => el.call('save', s.parse())
```

Inside lifecycle methods or `this`-bound contexts:

```js
methods/saveDraft.js:
export const saveDraft = function saveDraft(payload) {
  return this.context.sdk.draft.save(payload)
}
```

---

## Router

### Declare Pages

```js
// pages/index.js
export default {
  '/': homePage,
  '/dashboard': dashboardPage,
  '/users/:id': userPage,
  '/*': notFoundPage
}
```

Dynamic params (`:id`) populate `state.params`. Query strings populate `state.query`.

A route value is a page definition or a component's name (`'/ask': 'AiPage'`). An entry that adds only a head to a component, `'/blueprint': { extends: 'AiPage', metadata: { title: '…', robots: 'noindex' } }`, gives that route its own served and live head over the component's `metadata` (since smbls 3.14.860; FRAMEWORK.md → helmet → A route entry's head).

### Link Navigation

```js
export const NavItem = {
  extends: 'Link',
  text: (el, s) => s.label,
  href: (el, s) => `/${s.slug}`
}
```

### Programmatic Navigation

`event.preventDefault()` BEFORE `el.router(...)`:

```js
onClick: (e, el, s) => {
  e.preventDefault()
  el.router(`/profile/${s.userId}`, el.getRoot(), {}, {
    scrollToTop: true,
    scrollToOptions: { behavior: 'instant' }
  })
}
```

### Replace instead of push — `replace: true`

`replace: true` rewrites the CURRENT history entry (`history.replaceState`) instead of adding one. Use it for a redirect, a canonical-URL rewrite, or a filter / query change that must not stack Back-button entries:

```js
// A legacy URL forwards to its new home — Back does not return to the old URL
onRender: (el) => el.router('/admin/flags', el.getRoot(), {}, { replace: true })

// A filter change rewrites the query without stacking Back entries
onInput: (e, el) => el.router('/search?q=' + encodeURIComponent(e.target.value), el.getRoot(), {}, { replace: true })

// Same through the app handle returned by create()
app.navigate('/login', { replace: true })
```

`replace` only chooses HOW the entry is written: `pushState: false` still writes no history at all (the popstate handler and the initial render use it), so `{ pushState: false }` renders the route but leaves the OLD URL in the address bar. `replace` ships in `@symbo.ls/router` after 3.14.601 (smbls repo commit `9f498831e`); a runtime up to smbls 3.14.805 ignores it and pushes.

### Keep the page — `keepSamePage` and `render: false`

By default a new pathname swaps the page, also when it matches the SAME page (a page mapped again under a language prefix: `'/texts': texts` and `'/:lang/texts': texts`). Two opt-in options change only the address and the route state:

```js
// keepSamePage: only ANOTHER page (another route value) swaps; the same page stays mounted
el.router('/en/texts', el.getRoot(), {}, { replace: true, keepSamePage: true, scrollToTop: false })
// app-wide (config.js); a call turns it off with keepSamePage: false, force: true still swaps
export default { router: { keepSamePage: true } }

// render: false: write the address + route state, keep the page as it is (per call only)
el.router('/en/texts', el.getRoot(), {}, { replace: true, render: false })
```

- `keepSamePage`: the same page object under another pathname, route key or params stays mounted (its elements, their state, focus and whatever is open). Two entries that name the same component and carry nothing but a head (`'/ask': 'AiPage'`, `'/make': { extends: 'AiPage', metadata }`) are the same page too (since smbls 3.14.860): the page stays and its head changes to the new entry's. The history entry, `route` / `params` / `query` and `onRouteChanged` happen as for a query-only navigation; the scroll follows the usual options. The page is not built again, so it reads what changes from the route state (`s.root.params`). No `onRouteExit`, no view transition.
- `render: false`: the navigation mounts, scrolls, exits, transitions and loads nothing (`force` included) and fires `onRouteChanged` with `options.render === false`. Use it when the page on screen already is the page of the new address — a language switch that changed the words in place, or a one-time token (an OAuth code, an auth e-mail link) taken out of the address before the first render (the first render then renders the page as usual). Guards run: a refusal writes nothing, a redirect renders its target. The app-wide `router` options cannot set it.
- Either way never hand-write `history.replaceState` for this (FA410).

### Custom Router Element (Persistent Layouts)

```js
// config.js
export default {
  router: { customRouterElement: 'Folder.Content' }
}
```

The `/` page defines the persistent layout shell. Sub-pages render inside the target without destroying the shell. Every navigation resolves the target: the first render, Back / Forward, `app.navigate`, `Link`, and `el.router(path, el.getRoot())`. A call that passes another element renders into that element; while the target is not rendered yet, the root renders the page.

### Guards

```js
const authGuard = ({ element }) =>
  element.state.root.isLoggedIn ? true : '/login'

// per call
el.router('/dashboard', el.getRoot(), {}, { guards: [authGuard] })

// app-wide (config.js): every navigation, the first render and Back / Forward included
export default { router: { guards: [authGuard] } }
```

A guard returns `true` (go), `false` (stay) or a path (redirect), directly or as a promise. The guards run in order; the first `false` or path ends the run. A guard that answers directly is not awaited: with only such guards the page renders in the same run as the navigation, as without guards (so the first route renders inside `create()` and brender hydration adopts the page, not only the shell). A guard that returns a promise is awaited, and the guards after it run when it settles. The newest navigation wins: a navigation of the same element that starts while an older one still waits on a guard takes over, and when that guard settles the older navigation ends — it renders nothing, writes no history entry and follows no redirect (a Back / Forward waiting on its guard too: the History stays with the newer navigation). A lazy group's loaded render completes its placeholder's navigation; it is not a newer one. On Back / Forward the browser has already moved when the guards run, so the router puts the address back: `false` keeps the page and moves the History back by the same number of entries (no entry added or lost; an entry the router did not write is rewritten with the page on screen instead); a path REPLACES the entry that was reached and renders there. A first render that a guard redirects shows the target URL, not the refused one. To tell entries apart the router adds `history.state.__smblsRouter` to the entries it writes (a copy of your state; your keys stay) — only in apps with guards or `scrollRestoration: 'restore'`.

**A redirect runs its target's guards** (router 3.14.611): the redirected navigation passes through the guards again for the target address. A redirect back to an address the chain already passed, or a chain of 10, renders its target without guards and warns `[smbls/router] redirect loop`.

#### Choosing a route from data — `{ route }` / `{ route, path }`

The router matches an address by its shape: `/:lang` matches `/en` and `/volunteer` alike. A guard can name the route key to show:

```js
// pages: { '/:lang': home, '/:page': editorPage }
const languageOrPage = ({ route, params, element }) => {
  if (route !== '/:lang') return true
  const languages = element.context.polyglot.languages || []
  return languages.includes(params.lang) ? true : { route: '/:page' }
}

// config.js
export default { router: { guards: [languageOrPage] } }
```

- `{ route: '<key>' }` — the address stays; the chosen route renders as if the address had matched it: `state.route` is the chosen key, and `params` are read from the address with the chosen pattern (`/volunteer` with `/:page` → `{ page: 'volunteer' }`). A promise of `{ route }` is awaited, as any guard answer.
- `{ route, path }` — redirect to `path` AND render `route` there (`{ route: '/:page', path: '/team' }` for an old `/old/team` link). A `path` equal to the current address is a plain route choice. A string redirect matches its target by address again.
- A key the routes do not have renders nothing, as an unrouted address (`onNotFound` runs when set). A lazy route chosen this way renders the same chosen route when its group loads.
- Per call: `el.router('/volunteer', el.getRoot(), {}, { route: '/:page' })`. Only the call's own options count: `route` in the app's `router` options is ignored.
- The router reads `element.routes` on each navigation, so a route added at run time matches from the next navigation on.

### Scroll restoration — `scrollRestoration`

```js
// config.js
export default { router: { scrollRestoration: 'restore', scrollRestoreTimeout: 1000 } }
```

- `'restore'`: the router keeps each history entry's scroll offset (in memory and `sessionStorage`, so a reload or a return from another site works too) and puts the page back there on Back / Forward, after the route has rendered. While the page is not tall enough yet (its data is loading) it shows its top, then moves in one step; after `scrollRestoreTimeout` ms (default `1000`) it goes as far as the page reaches. The visitor's own scroll or a newer navigation ends the wait. New navigations still scroll to the top (`scrollToTop`).
- `'manual'` / `'auto'`: set the browser's own `history.scrollRestoration`. Unset: the browser default, untouched.
- The router scrolls the viewport of the document the app renders into (`scrollNode` default), so an app inside an iframe scrolls its own frame.

### URLs no route matches

With a `'/*'` page the not-found page renders; with `onNotFound` that callback decides. Without either, the router renders nothing for an unrouted URL: an in-app navigation to it writes no history, and Back / Forward to it (an entry other code wrote, a route a new deploy removed) rewrites that entry to the page on screen, so Back never gets stuck there.

### Lazy routes — `context.lazy` (opt-in)

Code visitors rarely need (an admin, an editor) can live in a LAZY GROUP: its own chunk (a bundler that splits dynamic imports — parcel under `smbls start` / `smbls build`), downloaded on the group's first route. Declare it in `context.js`:

```js
// symbols/context.js
export default {
  components, functions, pages,
  lazy: { admin: () => import('./admin/index.js') }
}

// symbols/admin/index.js — the group is a folder laid out like the project, with its own index.js barrels
import * as components from './components/index.js'
import * as functions from './functions/index.js'
import pages from './pages/index.js'
export default { components, functions, pages }        // and/or methods, snippets

// symbols/pages/index.js — a PLACEHOLDER renders while the group loads (it is the route's loading page)
'/admin/*': adminLoading

// symbols/pages/adminLoading.js
export const adminLoading = {
  lazy: 'admin',
  extends: 'Page',
  minHeight: '100dvh',
  LoadError: { if: (el, s) => s.lazyStatus === 'error', role: 'alert', text: '{{ admin.loadError | polyglot }}' },
  ReloadNote: { if: (el, s) => s.lazyStatus === 'reload', role: 'alert', text: '{{ admin.reloadToLoad | polyglot }}' },
  WaitNote: { if: (el, s) => s.lazyStatus === 'waiting', text: '{{ admin.signInFirst | polyglot }}' }
}
```

- A navigation runs the guards first (a refused one never downloads the group), writes the history entry and renders the placeholder; its own state carries `lazyStatus`: `'loading'`, then `'error'` if the load fails (the failure is logged, the message is yours), `'waiting'` while the group's `when` says false (below), or `'reload'` when only a page reload can load the group.
- **A failed load loads again in the same page** (cli 3.14.811). The next navigation to a route of the group (the same URL too) or the next `loadLazy` calls the loader again, and the placeholder flips back to `'loading'`. Under smbls's parcel (`smbls start`, a parcel `smbls build`) the retried `import()` requests the chunk again under a fresh address, `<chunk>.js?smbls-retry=<n>`, only when something asks. A project `.parcelrc` that sets its own `runtimes` keeps them and loses this. The loader gets the attempt number (`admin: (attempt) => …`, `0`, `1`, …) for another bundler (vite) that must ask for a fresh address itself.
- `'reload'`: the loader handed back the import that already failed (the same promise, or the same error object), so the router does not pretend to retry: the console says a reload is needed and `loadLazy` rejects with that error. Show a reload action for it, not a retry. A later attempt whose loader hands back a new import still loads.
- **Wait for the app — `{ load, when }`.** A group can load only once the app is ready (a Worker that serves the chunk only with a key the app gets first):

  ```js
  lazy: {
    admin: { load: () => import('./admin/index.js'), when: (el) => el.call('staffReady') }
  }
  ```

  The router asks `when(el)` before each load. A promise holds the load until it resolves (`'loading'`). `false` requests nothing: the placeholder shows `lazyStatus: 'waiting'`, `loadLazy` rejects with an error whose `code` is `'LAZY_WAITING'`, and the next navigation to the group or the next `loadLazy` asks `when` again. A `when` that throws or rejects is a failure (`'error'`). `smbls push` (frank) calls `load` only; `when` is a browser gate.
- Once loaded, the group's pages, components, functions, methods and snippets are registered, each placeholder of the group is replaced in place by the group's page of the same route, and the route renders again in the SAME history entry (no new entry, no scroll, no guards). A name the app already has keeps the app's value (a dev warning; `smbls push` refuses the collision — rename it).
- `onRouteChanged` fires twice: `options.lazy` is `{ group: 'admin', status: 'loading' }`, then `{ …, status: 'loaded' }`.
- `await el.call('loadLazy', 'admin')` preloads (e.g. on hover of the admin link) and resolves once the group is registered; it rejects when the load fails (`code: 'LAZY_WAITING'` while `when` says false). `el.router()` / `app.navigate()` resolve once the placeholder is on screen — call `loadLazy` first to land on the page itself.
- An element built before its group loaded never takes the group's component later: render group components after `loadLazy` resolves (the route's page always does).
- Without `context.lazy`, a `lazy` key is an ordinary prop. `smbls push` publishes the COMPLETE project (frank merges every group into the canonical sections; no `lazy`, no placeholders), so the platform and served pages work as before; frank-audit treats the group folder as discovered.
- **Built pages of a lazy route** (since smbls 3.14.859 / cli 3.14.826 / brender 3.14.676). `smbls build` builds a lazy route as what its render shows at the end. Without `brender.lazyGroups` the render does not wait: the route is the group's page when the group loaded during the render (the context the build loads declares `lazy`, for example through `brender.context`), else its placeholder. `symbols.json` `brender.lazyGroups` makes the render load the group first, so the route is always built as the group's REAL page: `'load'` for every group, or the group names.

  ```json
  { "brender": { "context": "symbols/context.js", "lazyGroups": ["texts"] } }
  ```

  The build reads `lazy` from the module `brender.context` names (or `symbols/context.js`): declare the group there. Its `when` runs in the build too: false (or a failed load) builds the placeholder, so a staff-only group stays out of the built pages. A built page that shows a group's page (either way) names the group, `<meta name="brender-lazy" content="texts">`, and preloads the group's chunk (`<link rel="modulepreload">`; CLI.md → Lazy groups built ahead). Use it for PUBLIC groups: their pages leave the main bundle and still arrive built.
- **The first view — `context.lazyFirstView`** (since smbls 3.14.859). `true`, or an array of group names, makes the app's FIRST navigation onto a route of such a group load the group and render its page, instead of the placeholder while the group loads. Guards, URL and history are the navigation's own; the content stays empty until the group is in. A failed load, or a `when` that says false, shows the placeholder with that `lazyStatus`, and the same navigation does not try again. Later navigations work as above. A built page sets it for the groups whose page it shows (the `brender-lazy` tag), so the takeover adopts the built page instead of mounting the placeholder over it; the group's `when` still gates that load.
- **Framework parts that only a group uses** (since smbls 3.14.859 / cli 3.14.826). With `build.treeShakeFeatures` and `"smblsEntry": "core"`, and loaders that are plain `() => import('./file.js')`, `inertOutside`, the bridge hooks and `TooltipLayer` move into one file that loads with the first group load when only group code uses them (CLI.md → Lazy group parts).

---

### Route events — `onRouteChanged` and exit motion with `onRouteExit`

Both events fire on the routed element (the app root for `el.router(path, el.getRoot())`). `onRouteChanged(el, state, context, options)` runs AFTER the new page is mounted — use it for an entrance. `onRouteExit(el, state, context, exit)` runs BEFORE the router swaps the page, with the page that is leaving; return a promise and the router waits for it before it writes history, updates the route state and mounts the new page:

```js
// app.js
export const app = {
  onRouteExit: (el, s, ctx, exit) => {
    // exit = { page, from, to, pathname, params, query, hash, signal, timeout }
    const anim = exit.page.node.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150 })
    exit.signal?.addEventListener('abort', () => anim.cancel())
    return anim.finished.catch(() => {}) // a cancelled exit is a finished exit
  },
  onRouteChanged: (el) => { /* animate el.content.node in */ }
}
```

- The wait is bounded by the router option `exitTimeout` (default `300` ms): on the timeout `exit.signal` aborts and the swap goes ahead; a rejected promise is a finished exit. A slow exit never blocks navigation.
- No exit runs (and nothing is awaited) for the first route of an element, for a navigation that keeps the page (query-only, same-path hash), under `prefers-reduced-motion: reduce`, or in a tab that is not visible. Without the handler the swap happens in the same synchronous run as before.
- A navigation that starts during an exit takes over: the older one never mounts its page and writes no history entry; a newer one that leaves the same page joins the running exit.
- Ships in `@symbo.ls/router` after smbls 3.14.810 (smbls repo commit `07c4b483b`); an older runtime never calls `onRouteExit`.

---

## Data Fetching (`@symbo.ls/fetch`)

Declarative fetch on any element. Caching, dedup, retry, refetch-on-focus, pagination — all built in.

### Setup (`config.js`)

```js
fetch: { adapter: 'rest', url: 'https://xxx.supabase.co/rest/v1',      // Supabase (PostgREST) through the REST adapter
         headers: { apikey: 'sb_publishable_…' } }
// or another REST API:
fetch: { adapter: 'rest', url: 'https://api.example.com',
         headers: { Authorization: 'Bearer token' },
         auth: { baseUrl: '…', signInUrl: '/login', sessionUrl: '/me' } }
// or local:
fetch: { adapter: 'local', data: { articles: [] }, persist: true }
```

The connection config is the `fetch` key of `config.js` (the runtime resolves it onto `context.fetch`; it is distinct from an element's `fetch:` query). `db` is not a config key — it is the usual name of the adapter `await el.getDB()` returns.

### Declarative Fetch

```js
// minimal
{ state: 'articles', fetch: true }

// options
{ state: 'articles',
  fetch: { params: { status: 'published' }, cache: '5m', limit: 20,
           order: { by: 'created_at', asc: false } } }

// shorthand
{ state: 'data', fetch: 'blog_posts' }

// transform
{ state: { featured: null, items: [] },
  fetch: { from: 'videos',
           transform: (data) => ({ featured: data.find(v => v.is_featured), items: data.filter(v => !v.is_featured) }) } }

// select (TanStack-style)
{ state: { titles: [] },
  fetch: { from: 'articles', select: (data) => data.map(a => a.title) } }

// dynamic params
{ state: { item: null },
  fetch: { method: 'rpc', from: 'get_content_rows',
           params: (el) => ({ p_id: window.location.pathname.split('/').pop() }) } }

// parallel array of fetches
{ state: { articles: [], events: [] },
  fetch: [
    { from: 'articles', as: 'articles', cache: '5m' },
    { from: 'events',   as: 'events',   cache: '5m' }
  ] }

// triggers
{ fetch: { from: 'articles' } }                                            // on: 'create' (default)
{ tag: 'form', fetch: { method: 'insert', from: 'contacts', on: 'submit' } }
{ fetch: { method: 'delete', from: 'items',
          params: (el) => ({ id: el.state.itemId }), on: 'click' } }
{ fetch: { from: 'articles',
          params: (el, s) => ({ title: { ilike: '%' + s.query + '%' } }),
          on: 'stateChange' } }
{ fetch: { from: 'articles', as: 'rows',                                  // a list of triggers: load on create,
          params: (el, s) => ({ kind: s.kind }),                          // then again when s.kind changes —
          on: ['create', 'stateChange'] } }                               // one config, one params

// enabled
{ fetch: { from: 'profile', enabled: (el, s) => !!s.userId } }

// pagination + keepPreviousData
{ state: { items: [], page: 1 },
  fetch: { from: 'articles', page: (el, s) => s.page, pageSize: 20, keepPreviousData: true } }

// polling
{ fetch: { from: 'notifications', refetchInterval: '30s' } }
```

### Cache

```js
cache: true                // staleTime 1m, gcTime 5m (default)
cache: false               // no caching
cache: '5m'                // 5min stale
cache: { stale: '1m', gc: '10m' }
cache: { staleTime: '30s', gcTime: '1h', key: 'custom-key' }
```

Stale-while-revalidate: stale data served immediately, background refetch swaps it.
Garbage collection: unused entries cleaned after `gcTime`.
Deduplication: identical concurrent queries share one network request — and, if it fails, every element on it gets the error (`onFetchError`), not empty rows.
A forced refetch reaches the network even while the entry is fresh: `el.__ref.refetch()`, each `refetchInterval` tick, the browser coming back online. Each page of a paginated / infinite query has its own key (the cursor is part of it).
`on: 'stateChange'` runs the query when the values its `params`, `enabled`, `skip` and `page` resolve to change — not on create, and not when its own rows land in state.
**`on` as a list** (fetch after 3.14.671): `on: ['create', 'stateChange']` is ONE config that loads on create and runs again when its inputs change — write it instead of two configs with the same `params` (one `'create'`, one `'stateChange'`). Each trigger in the list does what it does alone. With `'create'` in the list the config is a create-time query: it mounts its cache entry, refetches on focus / reconnect / `refetchInterval`, is refetched by an invalidation, and takes a seeded or early answer. `'stateChange'` then compares against the values the create run asked with. `'submit'` or `'click'` in the list make an `rpc` an action. A list of one is that trigger; an empty list is `'create'`; a trigger named twice counts once. (Before this release a list named no trigger and the config never ran.)
Removing an element releases what fetch bound for it: interval timers, focus / online / submit / click listeners, the `stateChange` watcher, a realtime subscription.
A server render (brender) binds no interval timer and no focus / online listener, and each render has a query cache of its own.

### Retry / Optimistic / Initial / Placeholder

```js
{ fetch: { from: 'articles', retry: 5 } }
{ fetch: { from: 'articles', retry: { count: 3, delay: (n) => 1000 * 2 ** n } } }
{ fetch: { from: 'articles', placeholderData: [] } }
{ fetch: { from: 'settings', initialData: { theme: 'dark' } } }
```

Reads retry 3 times by default. A write — `insert`, `update`, `upsert`, `delete` or an rpc action (below) — is sent once unless `retry` asks for more: a write that timed out may have been applied.

### Invalidation, actions, and the cache from project code

```js
// after a successful write, matching keys go stale and the queries MOUNTED on them refetch now
{ tag: 'form', fetch: { method: 'insert', from: 'articles', on: 'submit', fields: true, invalidates: true } }   // true / '*': the write's own `from`
{ fetch: { method: 'delete', from: 'items', on: 'click', invalidates: ['items:select:', 'item_counts'] } }    // a string matches every key that CONTAINS it

// an rpc is an ACTION (never cached, never shared, runs `invalidates`) when a click / submit fires it,
// when it declares `invalidates`, or with `mutation: true`; `mutation: false` keeps a clicked read cached
{ extends: 'Button', fetch: { method: 'rpc', from: 'save_article', params: (el, s) => ({ p_id: s.id }), on: 'click', invalidates: ['get_content_rows'] } }

// a functions/ file — project code cannot import the query client; it calls the same controls:
export const saveArticle = async function saveArticle (form) {
  const db = await this.getDB()
  const res = await db.rpc({ from: 'save_article', params: form })
  if (res.error) throw new Error(res.error)
  await this.call('invalidateQueries', 'get_content_rows')   // resolves when the mounted lists have refetched
  this.router('/blog/' + res.data.slug, this.getRoot())
}
```

- `el.call('invalidateQueries', match)`, `el.call('removeQueries', match)`, `el.call('getQueryData', keyOrConfig)`, `el.call('setQueryData', keyOrConfig, valueOrUpdater)` — registered whenever fetch is configured (a project function of the same name wins). `match`: a string contained in the key, a RegExp, a `(key) => boolean`, or an array (`['articles', 'select']` → keys containing `articles:select`); nothing matches every key. `keyOrConfig`: a key, or `{ from, method, params }` built the way the calling element would build it.
- Invalidation marks entries stale: mounted queries refetch at once (one request per key), others on their next mount showing the stale rows meanwhile — use `removeQueries` when they must load without them. A reply already on its way never replaces the refetched rows.
- A key is `from:method:` + the params as JSON, then `:infinite` / `:p<page>` / `:c<cursor>` when set, then `:<lang>` when a language is active; `cache: { key }` replaces it. A write through `getDB()` knows no keys: invalidate after it, as above.

### Early requests — `fetch.early` (REST adapter, opt-in)

`config.js` `fetch.early` lists the first view's GETs per route (`always`, `routes: { '/blog/:id': (params, ctx) => [...] }`); `smbls build` / `smbls deploy` emit `early.<hash>.js` (with `inline: true`, since cli 3.14.830: the same script in the page, allowed by its CSP hash — `smbls csp` lists it), which sends them while the HTML parses, and the REST adapter ADOPTS each answer for the first call that asks for exactly that request (same address, language and headers; once; not failed, expired or invalidated). `smbls start` does not emit it. Options to stand down on a page built ahead (`prerendered: 'skip'`, `<meta name="smbls-early" content="off">`), to wait for the head (`wait: 'head'`, `ctx.meta(name)`), to answer a smaller list (`slice: true`, an rpc's `slice: 'p_limit'`), to show an answer at an element's init (`adopt: 'init'`; a smaller answer is a first part — read `isFetching` in the view, not in `transform`), to name the start language (`startLang(ctx)`), to run at first paint (`firstPaint(ctx)`) and once the first view is in (`firstView(ctx)`), and to bundle the project's own pre-boot module into the same file (`script: './early.js'`). Config and rules: FRAMEWORK.md §5 → Early requests.

### Anonymous reads — `fetch.reads` (REST adapter, opt-in)

Every RPC is a POST with a JSON body and the configured headers, so a cross-origin read waits for a CORS preflight. With `reads`, an anonymous read goes as a simple GET:

```js
// config.js
fetch: {
  adapter: 'rest',
  url: 'https://<project>.supabase.co/rest/v1',
  headers: { apikey: '<publishable key>' },
  reads: {
    query: { apikey: 'apikey' },   // header → query parameter on anonymous reads. A PUBLIC key only: URLs land in logs and history
    rpc: 'get'                     // read-only RPCs go as GET <url>/rpc/<from>?<params> (PostgREST: STABLE/IMMUTABLE functions)
  }
}
```

- A read RPC is a declarative `fetch` with `method: 'rpc'` that is a query (no `on: 'submit'` / `'click'`, no `invalidates`, no `mutation: true`), a prefetch of one, or `db.rpc({ …, read: true })`. `read: false` keeps a declarative rpc a POST; `db.rpc()` without `read: true` stays a POST. Actions stay POSTs.
- Only scalar arguments (strings, finite numbers, booleans) go in a GET; a `null`, an object or an array keeps the call a POST.
- Only anonymous calls: with a token (`setToken`, `auth.token`) or a per-call `Authorization` header the call is unchanged. A session token never goes into a URL.
- A GET answered `405` is sent again as the POST. A relative `url` (same origin) keeps RPCs as POSTs. Without `reads` nothing changes.
- `fetch.early` takes `query` and `rpc` from `reads` when it does not set its own, so the pre-boot GET and the call's GET match.

### A pre-built page's data — `fetch.seed`

A page `smbls build` pre-rendered carries the data answers its render got (`data-fetch-seed`). A call that sends exactly a recorded request takes the recorded answer and never reaches the server, so the page shows the data of the **build time** until the next build. Each page names its build: `<meta name="brender-stamp" content="<stamp>" data-time="<ms>">` (`brender.stamp`, else the build time — CLI.md), read in app code as `el.context.prerender` (`{ stamp, time }`; `time` in ms or `null`). A page is **stale** when:

- the host marks it: `<html data-smbls-stale>` (an edge Worker that compares the stamp with its data's last change);
- `fetch.seed.isStale(stamp, { time })` returns true, or a promise of true. It runs once, when the REST adapter reads the page's seed;
- its build is older than `fetch.seed.maxAge` (ms, or `'30m'`, `'6h'`).

```js
// config.js
export default {
  fetch: {
    adapter: 'rest',
    url: 'https://api.example.com',
    seed: {
      maxAge: '6h',                                               // a build older than 6 h is stale
      isStale: (stamp, { time }) => stamp !== 'catalog-v2',      // or compare the build's own stamp
      onRefresh: (changes, root) => {                            // imperative reads whose answer changed
        for (const { from, data } of changes) {
          if (from === 'settings') root.state.update({ settings: data })
        }
      }
    }
  }
}
```

A stale page is adopted from the build's answers at once, as any page is. When the adoption is done (the hydration window closed; on a replaced page, when its first view settled), at idle, it asks again for exactly what took a recorded answer:

- a declarative query that took one: its key is invalidated, so every mounted query on it refetches and writes its rows into state (a keyed list keeps the nodes of unchanged rows);
- an imperative read (`getDB()` → `db.select` / `db.rpc`) that took one: its request is sent again, and the ones whose answer changed go to `onRefresh(changes, root)` — `changes` is `[{ method, from, params, data, previous }]`, `root` the app's root element;
- recorded answers no call took are dropped.

On an adopted page `window.__BRENDER_HYDRATION__.refreshed` reports it: `{ queries, reads, changed }` (a replaced page has no such report). A page that is not stale records nothing and sends nothing extra. `fetch.seed: false` adopts no recorded answer (the client asks for everything) and brender writes no seed into the page. `isStale` and `onRefresh` are published with the config: write them self-contained — only their arguments, no closure, no import (RULES.md Rule 59). When to flag a page: PATTERNS.md → Pre-built pages and fresh data.

**Parts whose query runs later** (fetch 3.14.671 / smbls 3.14.857). A render also records which of its queries each element ran, also one that ran after the element's create (on a state change, once its `enabled` turned true): `fetchRunsOf(context)` from `@symbo.ls/fetch` → `{ [element path]: [index in its fetch list, …] }`. The page carries that record as the seed block's last item, `{"r":{…}}`. In the browser such an element takes those queries' recorded answers at its init, whatever its trigger and `enabled` say then: a part that asks for its data later (`on: 'stateChange'`, `enabled: (el, s) => s.below`) is taken over as the page shows it, with no loading look and no request. An element that never ran a query in the render never takes another element's answer. A page without the record (an older build) works as before. Code that reads the seed block itself must skip an item it does not know (one without `k`), as `@symbo.ls/fetch` does: the `{"r"}` item exists since brender 3.14.675. Build side: `createEarlySeedBlock(entries, runs)`. The element path is `elementPath(el)`, now exported by `@symbo.ls/utils` (still by `@symbo.ls/element`).

### Response types and request bodies (REST adapter)

`responseType` sets how the REST adapter reads the response body. It works on `db.select / rpc / insert / update / upsert / delete` and in a declarative `fetch:`.

| `responseType` | `data` on success |
|---|---|
| `'auto'` (default) | JSON when the `content-type` says json, else text |
| `'json'` / `'text'` | parsed JSON, whatever the `content-type` says / the body string |
| `'blob'` / `'arrayBuffer'` | a `Blob` (bytes and content type kept — audio, xlsx, csv) / an `ArrayBuffer` |
| `'stream'` | the body `ReadableStream`, returned before the body is read |
| `'response'` | the raw `Response`, unread (use it to read response headers) |

A failed response keeps `{ data, error, status }` for every type. An unknown `responseType` throws before the request is sent.

```js
// In a handler (in a functions/ file use `this.getDB()`)
const db = await el.getDB()

// SSE / streamed answer — read it chunk by chunk
const { data: stream, error } = await db.insert({ from: '/ask', data: { question }, responseType: 'stream' })
if (!error) {
  const reader = stream.pipeThrough(new TextDecoderStream()).getReader()
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    onChunk(value)  // 'data: …\n\n' lines, as the server sends them
  }
}

// Blob download
const { data: blob } = await db.select({ from: '/reports/q3.xlsx', responseType: 'blob' })
el.state.update({ reportUrl: URL.createObjectURL(blob) })

// FormData upload — the adapter sets no Content-Type, fetch writes the multipart boundary
const form = new FormData()
form.append('audio', recording, 'voice.webm')
await db.insert({ from: '/voice', data: form })

// Per-call headers win over the configured headers and the token; null removes one
await db.select({ from: '/me', headers: { Authorization: `Bearer ${userToken}` } })
await db.select({ from: '/public/feed', headers: { Authorization: null } })
```

Declarative — a `Blob`, `ArrayBuffer`, stream or `Response` lands in state only under `as`:

```js
{ state: { answerAudio: null }, fetch: { from: '/voice/answer', responseType: 'blob', as: 'answerAudio' } }
{ tag: 'form', fetch: { method: 'insert', from: '/upload', on: 'submit', transform: (data, el) => new FormData(el.node) } }
```

- Sent as they are, with no adapter `Content-Type`: `FormData`, `Blob` / `File`, `ArrayBuffer`, typed arrays / `DataView`, `URLSearchParams`, `ReadableStream`. Any other `data` / `params` value is JSON, as before.
- A `'stream'` or `'response'` body can be read once, so those queries are never cached or deduplicated. They refetch on window focus / reconnect only when `refetchOnWindowFocus` / `refetchOnReconnect` is `true`.

> NEVER call `window.fetch` / `axios` from a component — streaming, binary and multipart calls included: use the options above. Use `fetch:` declaratively, or a `functions/loadX.js` for imperative flows. (Rule 47.)

---

## Polyglot (`@symbo.ls/polyglot`)

### Setup

```js
// No import: the runtime registers the plugin and its functions from
// context.polyglot (FRAMEWORK.md §6). An import is stubbed under `smbls push`.
context.polyglot = {
  defaultLang: 'en',
  languages: ['en', 'ka', 'ru'],
  translations: {
    en: { hello: 'Hello', search: 'Search', anyTime: 'Any time' },
    ka: { hello: 'გამარჯობა', search: 'ძიება' },
    ru: { hello: 'Привет', search: 'Поиск' }
  }
  // OR server-backed CMS:
  // fetch: { rpc: 'get_translations_if_changed', table: 'translations' }
}
```

### The start language

The app starts in one language, chosen before the first render: the language a `fetch.early.startLang(ctx)` pre-boot hook chose for this page load (in every mode, `'strict'` too), else the address's (its first path segment, when it is one of `languages`), else the stored choice (`storageLangKey`), else `state.lang`, else `defaultLang` — a code, or a function `(polyglot) => code` called each time it is asked. Server pages (`smbls start`, brender, mermaid) ask it too and write its answer in `<html lang>`; a runtime that compiles no code from text (a Worker) keeps `'en'` there, and the browser applies the answer at boot. `addressLang` sets the first step: `true` (default, the address wins over a stored choice), `'fallback'` (a stored choice wins), `'strict'` (the address alone decides: an unprefixed address is the default language's page, whatever is stored), `false` (the address is never read). `{ mode, except: [...] }` applies `mode` everywhere except under the `except` paths, which take the default `true`. A path matches the address's first segments (`'/admin'` matches `/admin` and `/admin/x`; `:param` matches any one segment). The address's language is not stored; `setLang` stores a choice.

```js
// context.js — /en/about starts in English, even over a stored 'ka'; / with nothing stored starts in Georgian
export const polyglot = {
  defaultLang: 'ka',
  languages: ['ka', 'en'],
  addressLang: true,            // the default; 'fallback' | false
  // addressLang: { mode: 'strict', except: ['/admin'] }  — public pages follow the address, the admin keeps the stored choice
  translations: { ka: { hello: 'გამარჯობა' }, en: { hello: 'Hello' } }
}
```

The first render, its declarative fetches (`Accept-Language`), the labels and a router's language guard all see it, so `/en/…` never renders in `ka` first. More: FRAMEWORK.md §6 → The start language.

### Warming the other languages — `prefetch`

A first switch to a language with no copy waits for its labels and the font faces they need. `polyglot.prefetch: true` (or `'idle'`; polyglot after 3.14.611 — FRAMEWORK.md §6) gets both ahead, once per app: after the active language's labels, once the page has loaded and the browser is idle (2 s at most), each other language in `languages` loads through `loadTranslations` (a project's own `loadTranslations` included) into the root state and storage, one at a time, and the faces its letters need in the body's font load. Static labels warm their faces only. Nothing for a reader whose browser asks to save data (`navigator.connection.saveData`); a server render never prefetches. Do not hand-write a loop over the languages on the window's `load` for this.

```js
// context.js — the other languages' labels and faces load at idle, so a first switch is instant
export const polyglot = {
  defaultLang: 'ka',
  languages: ['ka', 'en'],
  fetch: { rpc: 'get_translations_if_changed' },
  prefetch: true
}
```

### Use in components

```js
// mustache template (resolved by replaceLiteralsWithObjectFields, reactive)
{ text: '{{ hello | polyglot }}' }
{ placeholder: '{{ searchDestinations | polyglot }}' }

// el.call('polyglot', key) — direct lookup (NOT reactive — captures value at evaluation time)
{ text: (el) => el.call('polyglot', 'hello') }

// per-language state field (e.g. CMS title_en / title_ka)
{ text: '{{ title_ | getLocalStateLang }}' }

// language switcher
{ extends: 'Button', text: 'KA',
  onClick: (e, el) => el.call('setLang', 'ka') }

// current lang
{ text: (el) => el.call('getLang') }
```

When `state.root.lang` changes, every declarative `fetch` request (queries and writes) gets an `Accept-Language` header automatically (a `getDB()` call sends none unless you pass it). The header is the **only** injection — fetch does NOT add a `lang` query parameter or RPC argument. If your backend expects `lang` in `params`, set it explicitly: `fetch: { from: 'articles', params: (el, s) => ({ lang: s.root.lang, status: 'published' }) }`.

**Available polyglot functions** (registered automatically when `context.polyglot` is set; do NOT use `t` or `tr` — those don't exist):

| Function | Purpose |
| -- | -- |
| `polyglot(key, lang?)` | Translate (used in template literals AND imperative calls) |
| `getLocalStateLang(prefix)` | Read per-language state field (`state.<prefix>_<activeLang>`) |
| `getActiveLang()` | Active language code |
| `getLang()` | Alias for getActiveLang |
| `setLang(lang, { persist? })` | Switch language (async): stores the choice at once (`persist: false` writes nothing to storage), waits while the old language stays on screen for the new labels (when not cached) and their font faces (up to `polyglot.fontWait` ms, default 3000; `false` / `0` = no wait), then switches text, `state.root.lang` and `<html lang>` (last) in one frame. The last call wins; a failed load keeps the current language |
| `getPendingLang()` | The language a switch is waiting for, or `null` — reactive, for a busy state: `aria: { busy: (el) => (el.call('getPendingLang') ? 'true' : null) }` |
| `getLanguages()` | Available language codes |
| `loadTranslations(lang, { inFlight? })` | Load a language's labels — one load per language per app (a second call gets the load in flight); `{ inFlight: true }` starts nothing and answers the app's load in flight, or `undefined` |
| `upsertTranslation(key, lang, value)` | CMS write (optimistic + persists) |

---

## Helmet — SEO Metadata

```js
// app.js — global defaults
export default {
  metadata: {
    title: 'My App',
    description: 'Built with Symbols',
    'og:image': '/social.png'
  }
}

// per page — overrides
export const about = {
  metadata: {
    title: 'About Us',
    description: 'Learn more about us'
  }
}

// dynamic
export const product = {
  metadata: (el, s) => ({
    title: s.product.name,
    description: s.product.description,
    'og:image': s.product.image
  })
}
```

Helmet renders at runtime AND in `smbls brender` SSR. In the browser the head is the merge of the mounted elements' `metadata` layers (an element above its ancestors, the later-mounted above an unrelated one): a key a page omits falls back to the app's value — or the served value — never the previous page's; `title` / `description` cascade into `og:` / `twitter:`. To replace an element's metadata at runtime pass a factory or `null` to `el.update` (an object patch changes nothing). Since smbls 3.14.859 the runtime never writes a label's stand-in (a polyglot key whose language is still loading), and on a head the build wrote it keeps the served tags over the app's defaults until a navigation or a language switch: name labels in the app's defaults (`title: '{{ ui.meta.site_name | polyglot }}'`) and write the pre-label text once, in `index.html`. The runtime knows fewer keys than the server head — FRAMEWORK.md §7.

---

## `el.require()` — Cross-Environment Dependency Loading

```js
{
  tag: 'canvas',
  onRender: (el, s) => {
    const Chart = el.require('chartjs')
    el.data.chart = new Chart(el.node.getContext('2d'), { /* ... */ })
  }
}
```

`el.require()` resolves the dep through whichever runtime is active (Node / browser / brender) without needing imports.

---

## Common Patterns

### Loading State via `fetch:`

Keep the flags in the element's own state and set them from the fetch callbacks:

```js
export const DataList = {
  state: { items: [], loading: false, error: null },
  fetch: { from: 'items', as: 'items', cache: '5m' },
  onFetchStart:    (el, s) => s.update({ loading: true, error: null }),
  onFetchComplete: (data, el, s) => s.update({ loading: false }),
  onFetchError:    (error, el, s) => s.update({ loading: false, error: error?.message || String(error) }),
  Loader:  { if: (el, s) => s.loading, text: 'Loading…' },
  Failure: { if: (el, s) => Boolean(s.error), text: (el, s) => s.error },
  Items: {
    if: (el, s) => !s.loading && !s.error,
    children: (el, s) => s.items,
    childrenAs: 'state',
    childProps: { text: (el, s) => s.title }
  }
}
```

- The fetch plugin writes no loading or error key into state: there is no `s.__loading` or `s.__error`. A `__`-prefixed state key never re-renders anything.
- Start with `loading: false`: a fresh cache hit sends no request, so neither `onFetchStart` nor `onFetchComplete` runs.
- The REST adapter's `error` is a string; other adapters may give an object with `message`.
- `el.__ref.__fetchStatus` (`isFetching`, `isLoading`, `isStale`, `isSuccess`, `isError`, `error`, `status`, `fetchStatus`) is final before the rows reach state, so a render the rows trigger reads the final status. It is not reactive: writing it re-renders nothing, so do not drive `if:` / `text:` from it alone.
- The three callbacks also work inside the `fetch` object (`fetch: { …, onFetchStart }`), with the same arguments.

### Active List Item

```js
export const Menu = {
  state: { active: null },
  childExtends: 'MenuItem',
  childProps: {
    isActive: (el, s) => s.active === el.key,
    '.isActive': { fontWeight: '600', color: 'primary' },
    onClick: (e, el, s) => s.update({ active: el.key })
  }
}
```

### Modal (using `if:` + transition pattern)

```js
export const ModalCard = {
  position: 'absolute',
  align: 'center center',
  top: 0, left: 0, boxSize: '100% 100%',
  transition: 'all C defaultBezier',
  opacity: '0', visibility: 'hidden', pointerEvents: 'none', zIndex: '-1',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': {
    opacity: '1', zIndex: 999999, visibility: 'visible', pointerEvents: 'initial'
  },

  onClick: (e, el) => el.call('closeModal'),
  childProps: { onClick: (e) => e.stopPropagation() }
}
```

### In-place modal layer — `inertOutside`

`inertOutside` makes an element a modal layer WITHOUT moving it: while the prop is truthy and the element is in the document, everything outside it gets the `inert` attribute (as behind `<dialog>.showModal()`), so a field that expands in place keeps its editor's text, selection and undo history.

```js
export const NoteField = {
  state: { expanded: false },
  inertOutside: (el, s) => s.expanded,
  role: (el, s) => (s.expanded ? 'dialog' : null),
  aria: { modal: (el, s) => (s.expanded ? 'true' : null) },
  Button: { text: '{{ notes.expand | polyglot }}', onClick: (e, el, s) => s.update({ expanded: !s.expanded }) },
  Editor: { tag: 'textarea' }
}
// An `if:`-gated layer can declare it statically: { if: (el, s) => s.root.sheetOpen, inertOutside: true }
```

- Inert while open: the siblings of the element and of each ancestor up to `<body>`, plus whatever lands there while it is open (a toast, a portal appended to `<body>`). Closing (the prop turns false, the element is removed or `if:`-hidden) takes off exactly the `inert` it added; an element that was inert already, or sets its own `inert` meanwhile, keeps it.
- Layers stack: the newest open layer defines what is interactive; closing it hands the page back to the one below. A dialog that opens over a layer must be a layer itself, or live inside it.
- Opening moves focus into the layer when focus is outside it (an `[autofocus]` element first); closing returns focus to the element that had it.
- It follows the prop, not visibility: gate it on what shows the layer. `role`, `aria-modal`, Escape and scroll locking stay the component's own. An iframe app's layer inerts its own frame. A server render (brender) writes no `inert`.

### Search + Filter (state-driven, no DOM traversal)

See Rule 32 in RULES.md.

---

## Naming Conventions

| Category | Convention | Examples |
| -- | -- | -- |
| Components | PascalCase | `CustomComponent`, `NavBar`, `UserProfile` |
| Properties | camelCase | `paddingInlineStart`, `fontSize`, `backgroundColor` |
| Repeating keys | `_suffix` | `Li_1`, `Li_2`, `Li_One` (auto-extend by base name) |

---

## Reserved Keywords (Not CSS, Not Children)

```
key, extends, childExtends, childExtendsRecursive, childProps, childrenAs,
state, scope, data, attr, style, text, html, content, classlist, class,
tag, query, parent, node, context, define, props, deps,
if, show, hide, value, fetch, routes, metadata, variables, component,
__name, __ref, __hash, __text,
onInit, onCreate, onComplete, onRender, onRenderRouter,
onUpdate, onBeforeUpdate, onStateInit, onStateCreated,
onStateUpdate, stateDeps, onBeforeStateUpdate, onAttachNode, onFrame,
onInView, onLeaveView,
onError, onBeforeRemove, onRemove, onDestroy, onDispose,
onClick, onInput, onChange, onSubmit, onKeydown, onKeyup,
onMouseover, onMouseout, onBlur, onFocus, onScroll, onResize, …
```

All other keys: lowercase / camelCase = CSS prop, PascalCase = child component.

---

## Finding DOMQL Elements in the DOM (Debug Only)

DOMQL DOM nodes carry `.ref` pointing to the DOMQL element:

```js
const domqlElement = someNode.ref
domqlElement.key      // element key name
domqlElement.text     // current text (flat)
domqlElement.state    // state proxy
domqlElement.parent   // parent element
```

Debug CSS:

```js
domqlElement.__ref.__class       // CSS object input
domqlElement.__ref.__classNames  // generated class names
window.getComputedStyle(domqlElement.node).opacity
```

> Production code uses `el.lookdown('Key')` / `el.lookup('Key')` — never `document.querySelector`.
