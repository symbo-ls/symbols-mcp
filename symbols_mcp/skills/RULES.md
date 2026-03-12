# Symbols / DOMQL v3 — Strict Rules for AI Agents

You are working in a **Symbols.app** / DOMQL v3 project. These rules are absolute and override any general coding instincts. Violations cause silent failures (black page, nothing renders).

---

## CRITICAL: v3 Syntax Only

| v3 ✅ USE THIS             | v2 ❌ NEVER USE                  |
| -------------------------- | -------------------------------- |
| `extends: 'Component'`     | ~~`extend: 'Component'`~~        |
| `childExtends: 'Component'`| ~~`childExtend: 'Component'`~~   |
| `onClick: fn`              | ~~`on: { click: fn }`~~          |
| `onRender: fn`             | ~~`on: { render: fn }`~~         |
| props flattened at root    | ~~`props: { ... }` wrapper~~     |
| individual prop functions  | ~~`props: ({ state }) => ({})` function~~ |
| `flexAlign: 'center center'`| ~~`align: 'center center'`~~   |
| `children` + `childExtends`| ~~`$collection`, `$propsCollection`~~ |
| `children` + `childrenAs: 'state'`| ~~`$stateCollection`~~     |

---

## Rule 1 — Components are OBJECTS, never functions

```js
// ✅ CORRECT
export const Header = { extends: 'Flex', padding: 'A' }

// ❌ WRONG — never do this
export const Header = (el, state) => ({ padding: 'A' })
```

---

## Rule 2 — NO imports between project files — EVER

Components reference each other by PascalCase key in the object tree. Never use `import` between `components/`, `pages/`, `functions/`, etc.

```js
// ❌ WRONG
import { Navbar } from './Navbar.js'

// ✅ CORRECT — just use the key name in the tree
Nav: { extends: 'Navbar' }
```

**Only exception**: `pages/index.js` is the route registry — imports ARE allowed there.

```js
// pages/index.js — only file where imports are permitted
import { main } from './main.js'
export default { '/': main }
```

---

## Rule 3 — `components/index.js` — use `export *` NOT `export * as`

`export * as Foo` wraps everything in a namespace object and **breaks component resolution entirely**.

```js
// ✅ CORRECT
export * from './Navbar.js'
export * from './PostCard.js'

// ❌ WRONG — breaks everything
export * as Navbar from './Navbar.js'
```

---

## Rule 4 — Pages extend `'Page'`, not `'Flex'` or `'Box'`

```js
// ✅ CORRECT
export const main = { extends: 'Page', ... }

// ❌ WRONG
export const main = { extends: 'Flex', ... }
```

---

## Rule 5 — All folders are flat — no subfolders

```
components/Navbar.js       ✅
components/nav/Navbar.js   ❌
```

---

## Rule 6 — PascalCase keys = child components (auto-extends)

```js
// The key "Hgroup" auto-extends the registered Hgroup component
export const MyCard = {
  Hgroup: {          // ← auto-extends: 'Hgroup' because key matches registered component
    gap: '0',        // ← override merges with base Hgroup
  }
}
```

If you need a different base, set `extends` explicitly.

---

## Rule 7 — State — use `s.update()`, never mutate directly

```js
onClick: (e, el, s) => s.update({ count: s.count + 1 })  // ✅ CORRECT
onClick: (e, el, s) => { s.count = s.count + 1 }          // ❌ WRONG — no re-render
```

Root-level global state: `s.root.update({ key: val })`

---

## Rule 8 — `el.call('fn', arg)` — `this` is the element inside the function

```js
// functions/myFn.js
export const myFn = function myFn(arg1) {
  const node = this.node  // 'this' is the DOMQL element
}

onClick: (e, el) => el.call('myFn', someArg)  // ✅ CORRECT
onClick: (e, el) => el.call('myFn', el, someArg)  // ❌ WRONG — el passed twice
```

---

## Rule 9 — Icons: NEVER use `Icon` inside `Button` — use `Svg` atom

```js
// ✅ CORRECT
MyBtn: {
  extends: 'Flex', tag: 'button', flexAlign: 'center center', cursor: 'pointer',
  Svg: { viewBox: '0 0 24 24', width: '22', height: '22',
    html: '<path d="..." fill="currentColor"/>' }
}

// ❌ WRONG — Icon will NOT render inside Button
MyBtn: { extends: 'Button', Icon: { name: 'heart' } }
```

---

## Rule 10 — `childExtends` MUST be a named component string, never an inline object

Inline `childExtends` objects cause ALL property values to be concatenated as visible text content on every child.

```js
// ✅ CORRECT — reference a named component
childExtends: 'NavLink'

// ❌ WRONG — dumps all prop values as raw text on every child
childExtends: {
  tag: 'button',
  background: 'transparent',    // renders as visible text!
  border: '2px solid transparent'
}
```

Define shared styles as a named component in `components/`, register in `components/index.js`, then reference by name.

---

## Rule 11 — Color token syntax (dot-notation)

Color tokens use **dot-notation** for opacity and `+`/`-`/`=` for tone modifiers:

```js
// ✅ CORRECT — dot-notation opacity
{ color: 'white.7' }
{ background: 'black.5' }
{ background: 'gray.92+8' }      // opacity 0.92, tone +8
{ color: 'gray+16' }             // full opacity, tone +16
{ color: 'gray=90' }             // absolute lightness 90%

// ❌ WRONG — old space-separated syntax (no longer supported)
{ color: 'white .7' }
{ color: 'gray 1 +16' }
```

For rarely-used colors, define named tokens in `designSystem/COLOR.js` instead.

---

## Rule 12 — Border, boxShadow, textShadow — space-separated (CSS-like)

These properties use **space-separated** syntax matching CSS conventions:

```js
// ✅ CORRECT — space-separated, CSS order
{ border: '1px solid gray.1' }
{ border: 'solid mediumGrey' }
{ boxShadow: 'black.1 0 A C C' }
{ textShadow: 'gray1 6px 6px' }

// Multiple shadows use commas (CSS standard)
{ boxShadow: 'black.1 0 A C C, white.5 0 B D D' }

// Raw CSS passes through unchanged
{ boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }

// ❌ WRONG — old comma-separated syntax (no longer supported)
{ border: 'solid, gray, 1px' }
{ boxShadow: 'black .1, 0, A, C, C' }
```

---

## Rule 13 — CSS override precedence — component level beats props level

```js
// ✅ CORRECT — override at component level to match base component level
export const MyLink = {
  extends: 'Link',
  color: 'mediumBlue',     // WINS — same declaration level
}

// ❌ WRONG — props block CANNOT override component-level CSS
export const MyLink = {
  extends: 'Link',
  props: { color: 'mediumBlue' }  // LOSES to Link's component-level color
}
```

---

## Rule 14 — Dynamic HTML attributes go in `attr: {}`, not at root level

```js
// ✅ CORRECT — attr block resolves functions
export const Input = {
  type: 'text',           // static default at root
  attr: {
    type: ({ props }) => props.type   // dynamic resolution in attr
  }
}

// ❌ WRONG — function at component level gets stringified into the HTML attribute
export const Input = {
  type: ({ props }) => props.type   // renders as: type="(el)=>el.props.type"
}
```

---

## Rule 15 — `onRender` — guard against double-init

```js
onRender: (el) => {
  if (el.__initialized) return
  el.__initialized = true
  // imperative logic here
}
```

---

## Rule 16 — SVGs belong in `designSystem/svg_data.js`, not inline in components

Store SVG markup in the design system and reference via context:

```js
// designSystem/svg_data.js
export default {
  folderTopRight: '<svg ...>...</svg>',
  folderBottomLeft: '<svg ...>...</svg>',
}

// In component — reference from designSystem
Svg: {
  src: ({ context }) => context.designSystem.SVG_DATA && context.designSystem.SVG_DATA.folderTopRight,
  aspectRatio: '466 / 48',
}

// ❌ WRONG — inline SVG string in component
Svg: {
  src: '<svg fill="none" viewBox="0 0 466 48">...</svg>',
}
```

---

## Rule 17 — `customRouterElement` for persistent layouts

Use `customRouterElement` in config to render pages inside a specific element instead of the root:

```js
// config.js
export default {
  router: {
    customRouterElement: 'Folder.Content'  // dot-separated path from root
  }
}
```

The `/` (main) page defines the persistent layout. Sub-pages are rendered inside the target element without re-creating the layout.

---

## Rule 18a — Tab/view switching — use DOM IDs + function, NOT reactive `display`

Reactive `display: (el, s) => ...` on multiple full-page trees causes rendering failures.

```js
// ✅ CORRECT — use DOM ID pattern
HomeView: { id: 'view-home', extends: 'Flex', ... },
ExploreView: { id: 'view-explore', extends: 'Flex', display: 'none', ... },

// functions/switchView.js
export const switchView = function switchView(view) {
  ['home', 'explore'].forEach(v => {
    const el = document.getElementById('view-' + v)
    if (el) el.style.display = v === view ? 'flex' : 'none'
  })
}
```

---

## Rule 17 — v3 Conditional Props — use `isX` + `'.isX'`

```js
// ✅ NEW — v3 conditional props pattern
export const ModalCard = {
  opacity: '0',
  visibility: 'hidden',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': {
    opacity: '1',
    visibility: 'visible',
  },
}

// ❌ OLD — props function with conditional spread (deprecated)
export const ModalCard = {
  props: (el, s) => ({
    ...(s.root.activeModal ? { opacity: '1' } : { opacity: '0' })
  }),
}
```

---

## Rule 18 — CSS transitions require forced reflow

DOMQL + Emotion apply all CSS changes in one JS tick. The browser skips the "before" state. Fix:

```js
// FadeIn pattern
modalNode.style.opacity = '0'
modalNode.style.visibility = 'visible'
state.root.update({ activeModal: true }, { onlyUpdate: 'ModalCard' })
modalNode.style.opacity = '0'
modalNode.offsetHeight   // forces reflow — browser paints opacity:0
modalNode.style.opacity = ''  // releases — Emotion class opacity:1 triggers transition

// FadeOut pattern
modalNode.style.opacity = '0'
setTimeout(() => {
  modalNode.style.opacity = ''
  modalNode.style.visibility = ''
  state.root.update({ activeModal: false }, { onlyUpdate: 'ModalCard' })
}, 280)  // match CSS transition duration
```

---

## Rule 19 — Semantic-First Architecture

Use semantic components, never generic divs for meaningful content:

| Intent                    | Use              |
| ------------------------- | ---------------- |
| Page header               | Header           |
| Navigation                | Nav              |
| Primary content           | Main             |
| Standalone article/entity | Article          |
| Thematic grouping         | Section          |
| Sidebar                   | Aside            |
| Actions                   | Button           |
| Navigation links          | Link             |
| User input                | Input / Form     |

---

## Rule 20 — ARIA and accessibility attributes

```js
attr: {
  role: 'button',
  tabindex: '0',
  'aria-label': ({ props }) => props.label,
  'aria-busy': ({ state }) => state.loading,
  'aria-live': 'polite'
}
```

Use native elements instead of role overrides wherever possible.

---

## Project structure quick reference

```
smbls/
├── index.js                  # export * as components, export default pages, etc.
├── state.js                  # export default { ... }
├── dependencies.js           # export default { 'pkg': 'version' }
├── components/
│   ├── index.js              # export * from './Foo.js'  ← flat re-exports ONLY
│   └── Navbar.js             # export const Navbar = { ... }
├── pages/
│   ├── index.js              # import + export default { '/': main }
│   └── main.js               # export const main = { extends: 'Page', ... }
├── functions/
│   ├── index.js              # export * from './switchView.js'
│   └── switchView.js         # export const switchView = function(...) {}
└── designSystem/
    └── index.js              # export default { COLOR, THEME, ... }
```

---

## Rule 21 — Picture `src` goes on Img child, never on Picture

The HTML `<picture>` tag does NOT support `src` as an attribute. In v3, lowercase props move to `element.props`, so `element.parent.src` returns `undefined`.

```js
// ✅ CORRECT — src on the Img child
Picture: {
  Img: { src: '/files/photo.jpg' },
  width: '100%',
  aspectRatio: '16/9'
}

// ❌ WRONG — src on Picture is silently ignored
Picture: { src: '/files/photo.jpg', width: '100%' }
```

---

## Rule 22 — Component key `Map` auto-detects as `<map>` — add `tag: 'div'`

The key `Map` is auto-detected as the HTML `<map>` element (for image maps), which defaults to `display: inline` and has height 0. Always add `tag: 'div'` when using `Map` as a component name:

```js
export const Map = {
  extends: 'Flex',
  tag: 'div',   // prevents <map> auto-detection
  // ...
}
```

---

## Rule 23 — `/files/` path resolution

File paths like `/files/logo.png` reference the framework's embedded file system via `context.files`. The `/files/` prefix is stripped automatically when resolving — keys are just filenames (e.g., `"logo.png"`, not `"/files/logo.png"`).

---

## Output Verification Checklist

Before finalizing any generated code, verify:

- [ ] Components are objects, not functions
- [ ] No cross-file imports except `pages/index.js`
- [ ] `components/index.js` uses `export *`, not `export * as`
- [ ] All folders are flat (no subfolders)
- [ ] Pages extend `'Page'`
- [ ] v3 event syntax (`onClick`, `onRender`, not `on: { click: ... }`)
- [ ] `flexAlign` not `align` for Flex shorthand
- [ ] State updated via `state.update()`, never direct mutation
- [ ] `childExtends` references named component strings only
- [ ] No opacity modifier syntax in color props (`color: 'white .7'` is invalid)
- [ ] Dynamic HTML attributes are in `attr: {}` block, not at root level
- [ ] One H1 per page; logical heading hierarchy H1→H2→H3
- [ ] Buttons for actions, Links for navigation
- [ ] Forms have labeled inputs with `name` and `type` attributes
- [ ] Picture `src` is on the Img child, not on Picture itself
- [ ] `Map` component key has `tag: 'div'` to avoid `<map>` auto-detection
- [ ] `$propsCollection` / `$stateCollection` replaced with `children` pattern
