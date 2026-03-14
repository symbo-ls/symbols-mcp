# Symbols / DOMQL v3 — Strict Rules for AI Agents

These rules are absolute. Violations cause silent failures (black page, nothing renders). DO NOT override with general coding instincts.

---

## CRITICAL: v3 Syntax Only

| ✅ v3 — USE THIS              | ❌ v2 — NEVER USE                        |
| ------------------------------ | ---------------------------------------- |
| `extends: 'Component'`        | ~~`extend: 'Component'`~~               |
| `childExtends: 'Component'`   | ~~`childExtend: 'Component'`~~          |
| `onClick: fn`                  | ~~`on: { click: fn }`~~                 |
| `onRender: fn`                 | ~~`on: { render: fn }`~~                |
| props flattened at root        | ~~`props: { ... }` wrapper~~            |
| individual prop functions      | ~~`props: ({ state }) => ({})` function~~ |
| `align: 'center center'`      | ~~`flexAlign: 'center center'`~~        |
| `children` + `childExtends`   | ~~`$collection`, `$propsCollection`~~   |
| `children` + `childrenAs: 'state'` | ~~`$stateCollection`~~              |
| No `extends` needed for Text/Box/Flex; replace `extends: 'Flex'` with `flow: 'x'` or `flow: 'y'` | ~~`extends: 'Text'`~~, ~~`extends: 'Box'`~~, ~~`extends: 'Flex'`~~ |

---

## Rule 1 — Components are OBJECTS, never functions

```js
// ✅
export const Header = { flow: 'x', padding: 'A' }

// ❌
export const Header = (el, state) => ({ padding: 'A' })
```

---

## Rule 2 — NO imports between project files

NEVER use `import` between `components/`, `pages/`, `functions/`, etc. Reference components by PascalCase key in the object tree.

```js
// ❌
import { Navbar } from './Navbar.js'

// ✅
Nav: { extends: 'Navbar' }
```

**Only exception:** `pages/index.js` is the route registry — imports ARE allowed there.

```js
// pages/index.js — only file where imports are permitted
import { main } from './main.js'
export default { '/': main }
```

---

## Rule 3 — `components/index.js` uses `export *`, NOT `export * as`

`export * as Foo` wraps in a namespace object and breaks component resolution.

```js
// ✅
export * from './Navbar.js'
export * from './PostCard.js'

// ❌
export * as Navbar from './Navbar.js'
```

---

## Rule 4 — Pages extend `'Page'`

NEVER extend `'Flex'` or `'Box'` for page components.

```js
// ✅
export const main = { extends: 'Page', ... }

// ❌
export const main = { extends: 'Flex', ... }
```

---

## Rule 5 — All folders are flat — no subfolders

```
✅ components/Navbar.js
❌ components/nav/Navbar.js
```

---

## Rule 6 — PascalCase keys = child components (auto-extends)

A PascalCase key auto-extends the registered component matching that name.

```js
export const MyCard = {
  Hgroup: {          // auto-extends: 'Hgroup'
    gap: '0',        // merges with base Hgroup
  }
}
```

SET `extends` explicitly only when the base differs from the key name.

---

## Rule 7 — State updates via `s.update()`, NEVER mutate directly

```js
// ✅
onClick: (e, el, s) => s.update({ count: s.count + 1 })

// ❌ — no re-render
onClick: (e, el, s) => { s.count = s.count + 1 }
```

Root-level global state: `s.root.update({ key: val })`

---

## Rule 8 — `el.call('fn', arg)` — `this` is the element

```js
// functions/myFn.js
export const myFn = function myFn(arg1) {
  const node = this.node  // 'this' is the DOMQL element
}

// ✅
onClick: (e, el) => el.call('myFn', someArg)

// ❌ — el passed twice
onClick: (e, el) => el.call('myFn', el, someArg)
```

---

## Rule 9 — Icons: use `Icon` component, store SVGs in design system

Use the `Icon` component to render icons. `Icon` extends `Svg` internally, accepts a `name` or `icon` prop to reference icons from `designSystem.icons`, and auto-converts kebab-case to camelCase. Supports sprite mode via `useIconSprite: true` in the design system.

```js
// ✅ — reference icon by name from designSystem.icons
MyBtn: {
  tag: 'button', align: 'center center', cursor: 'pointer',
  Icon: { name: 'arrowRight' }
}

// ❌ — do NOT inline SVGs via Svg component for icons
MyBtn: {
  tag: 'button', align: 'center center', cursor: 'pointer',
  Svg: { viewBox: '0 0 24 24', width: '22', height: '22',
    html: '<path d="..." fill="currentColor"/>' }
}
```

---

## Rule 10 — `childExtends` MUST be a named string, never an inline object

Inline objects cause ALL property values to render as visible text on every child.

```js
// ✅
childExtends: 'NavLink'

// ❌ — dumps prop values as raw text
childExtends: {
  tag: 'button',
  background: 'transparent',
  border: '2px solid transparent'
}
```

Define shared styles as a named component in `components/`, register in `components/index.js`, then reference by name.

---

## Rule 11 — Color token syntax (dot-notation)

Use dot-notation for opacity. Use `+`/`-`/`=` for tone modifiers.

```js
// ✅
{ color: 'white.7' }
{ background: 'black.5' }
{ background: 'gray.92+8' }      // opacity 0.92, tone +8
{ color: 'gray+16' }             // full opacity, tone +16
{ color: 'gray=90' }             // absolute lightness 90%

// ❌ — old space-separated syntax
{ color: 'white .7' }
{ color: 'gray 1 +16' }
```

For rarely-used colors, define named tokens in `designSystem/color.js`.

---

## Rule 12 — Border, boxShadow, textShadow — space-separated (CSS-like)

```js
// ✅
{ border: '1px solid gray.1' }
{ border: 'solid mediumGrey' }
{ boxShadow: 'black.1 0 A C C' }
{ textShadow: 'gray1 6px 6px' }
{ boxShadow: 'black.1 0 A C C, white.5 0 B D D' }  // multiple: use commas
{ boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }          // raw CSS passes through

// ❌ — old comma-separated syntax
{ border: 'solid, gray, 1px' }
{ boxShadow: 'black .1, 0, A, C, C' }
```

---

## Rule 13 — CSS override precedence: component level beats props level

```js
// ✅ — override at component level
export const MyLink = {
  extends: 'Link',
  color: 'mediumBlue',     // WINS — same declaration level
}

// ❌ — props block CANNOT override component-level CSS
export const MyLink = {
  extends: 'Link',
  props: { color: 'mediumBlue' }  // LOSES to Link's component-level color
}
```

---

## Rule 14 — Standard HTML attributes go at root, `attr: {}` is for non-standard only

The `attrs-in-props` module auto-detects 600+ standard HTML attributes per tag. Place them directly at the element root — both static and dynamic values work.

Use `attr: {}` ONLY for: `data-*`, `aria-*`, and custom non-standard attributes.

```js
// ✅ — standard attrs at root (auto-detected)
export const Input = {
  tag: 'input',
  type: ({ props }) => props.type,
  placeholder: ({ props }) => props.placeholder,
  required: ({ props }) => props.required,
  disabled: ({ props }) => props.disabled || null,
}

// ✅ — non-standard / ARIA in attr: {}
export const Widget = {
  role: 'button',
  tabindex: '0',
  attr: {
    'aria-label': ({ props }) => props.label,
    'data-testid': 'widget',
  }
}

// ❌ — don't use attr: {} for standard HTML attributes
export const Input = {
  attr: {
    type: 'text',
    placeholder: 'Enter...',
  }
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

## Rule 16 — Icons use `Icon`, decorative/structural SVGs use `Svg`

For **icons**, always use the `Icon` component referencing `designSystem.icons` by name. For **decorative or structural SVGs** (backgrounds, illustrations, shapes) that are not icons, use `Svg` and store the SVG data in `designSystem/svg_data.js`.

```js
// ✅ — icons: use Icon component
Icon: { name: 'arrowRight' }

// ✅ — decorative/structural SVG: reference from designSystem
Svg: {
  src: ({ context }) => context.designSystem.svg_data && context.designSystem.svg_data.folderTopRight,
  aspectRatio: '466 / 48',
}

// ❌ — do NOT use Svg for icons
Svg: { viewBox: '0 0 24 24', html: '<path d="..." fill="currentColor"/>' }

// ❌ — do NOT inline SVG strings in components
Svg: {
  src: '<svg fill="none" viewBox="0 0 466 48">...</svg>',
}
```

---

## Rule 17 — `customRouterElement` for persistent layouts

Use `customRouterElement` in config to render pages inside a specific element instead of root.

```js
// config.js
export default {
  router: {
    customRouterElement: 'Folder.Content'  // dot-separated path from root
  }
}
```

The `/` (main) page defines the persistent layout. Sub-pages render inside the target element without re-creating the layout.

---

## Rule 18 — Tab/view switching: use DOM IDs, NOT reactive `display`

Reactive `display: (el, s) => ...` on multiple full-page trees causes rendering failures.

```js
// ✅ — DOM ID pattern
HomeView: { id: 'view-home', flow: 'column', ... },
ExploreView: { id: 'view-explore', flow: 'column', display: 'none', ... },

// functions/switchView.js
export const switchView = function switchView(view) {
  ['home', 'explore'].forEach(v => {
    const el = document.getElementById('view-' + v)
    if (el) el.style.display = v === view ? 'flex' : 'none'
  })
}
```

---

## Rule 19 — Conditional props: use `isX` + `'.isX'`

```js
// ✅ — v3 conditional props
export const ModalCard = {
  opacity: '0',
  visibility: 'hidden',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': {
    opacity: '1',
    visibility: 'visible',
  },
}

// ❌ — deprecated props function with conditional spread
export const ModalCard = {
  props: (el, s) => ({
    ...(s.root.activeModal ? { opacity: '1' } : { opacity: '0' })
  }),
}
```

---

## Rule 20 — CSS transitions require forced reflow

DOMQL + Emotion apply all CSS changes in one JS tick. The browser skips the "before" state. Force reflow to fix.

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

## Rule 21 — Semantic-First Architecture

Use semantic components for meaningful content. NEVER use generic divs.

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

## Rule 22 — ARIA and accessibility attributes

Standard HTML attributes (`role`, `tabindex`) go at root. Place `aria-*` attributes in `attr: {}`. Use native elements instead of role overrides wherever possible.

```js
// Standard attrs at root
role: 'button',
tabindex: '0',
// ARIA in attr: {}
attr: {
  'aria-label': ({ props }) => props.label,
  'aria-busy': ({ state }) => state.loading,
  'aria-live': 'polite'
}
```

---

## Rule 23 — Picture `src` goes on Img child, NEVER on Picture

The `<picture>` tag does NOT support `src`. In v3, lowercase props move to `element.props`, so `element.parent.src` returns `undefined`.

```js
// ✅
Picture: {
  Img: { src: '/files/photo.jpg' },
  width: '100%',
  aspectRatio: '16/9'
}

// ❌
Picture: { src: '/files/photo.jpg', width: '100%' }
```

---

## Rule 24 — `Map` component key needs `tag: 'div'`

The key `Map` auto-detects as HTML `<map>` (image maps), which defaults to `display: inline` with height 0. ALWAYS add `tag: 'div'`.

```js
export const Map = {
  flow: 'y',
  tag: 'div',   // prevents <map> auto-detection
  // ...
}
```

---

## Rule 25 — `/files/` path resolution

Paths like `/files/logo.png` reference the framework's embedded file system via `context.files`. The `/files/` prefix is stripped automatically — keys are just filenames (e.g., `"logo.png"`, not `"/files/logo.png"`).

---

## Rule 26 — NEVER extend `'Text'`, `'Box'`, or `'Flex'` — they are implicit defaults

`Text`, `Box`, and `Flex` are built-in base primitives. Every element is already a Box; any element with `text:` already behaves as Text; any element with `flow:` or `align:` already behaves as Flex. Extending them explicitly causes an unnecessary merge step at runtime.

**When removing `extends: 'Flex'`:** if the element has no `flow:` or `align:` property, you MUST add `flow: 'x'` (or `flow: 'y'` for vertical layout) to preserve flex behavior. Without these, the element becomes a regular block div.

```js
// ✅ CORRECT — use flow/align instead of extends
Row: { flow: 'x', gap: 'A', align: 'center center' }
Stack: { flow: 'y', gap: 'B', padding: 'C' }
Tag: { tag: 'span', text: 'NEW', padding: 'X A', fontSize: 'Y' }
Card: { tag: 'div', padding: 'B', background: 'white' }

// ❌ WRONG — unnecessary extends
Tag: { extends: 'Text', text: 'NEW', padding: 'X A' }
Card: { extends: 'Box', padding: 'B', background: 'white' }
Row: { extends: 'Flex', gap: 'A', align: 'center' }

// ❌ WRONG — removed extends: 'Flex' but forgot to add flow
Container: { padding: 'C', maxWidth: 'K' }  // now block, not flex!
// ✅ FIX
Container: { flow: 'y', padding: 'C', maxWidth: 'K' }
```

Use a semantic or functional component instead: `Link`, `Button`, `Header`, `Section`, etc. For flex layout, use `flow:` or `align:` props directly.

---

## Project Structure Quick Reference

```
smbls/
├── index.js                  # export * as components, export default pages, etc.
├── state.js                  # export default { ... }
├── dependencies.js           # export default { 'pkg': 'version' }
├── components/
│   ├── index.js              # export * from './Foo.js'  — flat re-exports ONLY
│   └── Navbar.js             # export const Navbar = { ... }
├── pages/
│   ├── index.js              # import + export default { '/': main }
│   └── main.js               # export const main = { extends: 'Page', ... }
├── functions/
│   ├── index.js              # export * from './switchView.js'
│   └── switchView.js         # export const switchView = function(...) {}
└── designSystem/
    └── index.js              # export default { color, theme, ... }
```

---

## Output Verification Checklist

Before finalizing generated code, verify ALL of the following:

- [ ] Components are objects, not functions (Rule 1)
- [ ] No cross-file imports except `pages/index.js` (Rule 2)
- [ ] `components/index.js` uses `export *`, not `export * as` (Rule 3)
- [ ] Pages extend `'Page'` (Rule 4)
- [ ] All folders are flat — no subfolders (Rule 5)
- [ ] v3 event syntax: `onClick`, `onRender`, not `on: { click: ... }` (CRITICAL table)
- [ ] `align` not `flexAlign` for flex alignment shorthand (CRITICAL table)
- [ ] State updated via `s.update()`, never direct mutation (Rule 7)
- [ ] `childExtends` references named component strings only (Rule 10)
- [ ] Color uses dot-notation: `'white.7'` not `'white .7'` (Rule 11)
- [ ] Standard HTML attributes at root; only `data-*`/`aria-*`/custom in `attr: {}` (Rule 14)
- [ ] `onRender` guards against double-init (Rule 15)
- [ ] Conditional props use `isX` / `'.isX'` pattern (Rule 19)
- [ ] One H1 per page; logical heading hierarchy H1 > H2 > H3
- [ ] Buttons for actions, Links for navigation (Rule 21)
- [ ] Forms have labeled inputs with `name` and `type` attributes
- [ ] Picture `src` is on the Img child (Rule 23)
- [ ] `Map` component key has `tag: 'div'` (Rule 24)
- [ ] `$propsCollection` / `$stateCollection` replaced with `children` pattern (CRITICAL table)
- [ ] No `extends: 'Text'`, `extends: 'Box'`, or `extends: 'Flex'` — use `flow:`/`align:`/`gap:` instead (Rule 26)
