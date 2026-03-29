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
| `color: {}`, `theme: {}`, `typography: {}` (lowercase) | ~~`COLOR: {}`, `THEME: {}`, `TYPOGRAPHY: {}`~~ (UPPERCASE) |
| `context.designSystem.color` | ~~`context.designSystem.COLOR`~~ |
| `import { typography } from '@symbo.ls/scratch'` | ~~`import { TYPOGRAPHY } from '@symbo.ls/scratch'`~~ |

---

## Rule 0 — Design system keys are ALWAYS lowercase

UPPERCASE design system keys (`COLOR`, `THEME`, `TYPOGRAPHY`, `SPACING`, `TIMING`, `FONT`, `FONT_FAMILY`, `ICONS`, `SHADOW`, `MEDIA`, `GRID`, `ANIMATION`, `RESET`, `SVG`, `GRADIENT`, `SEMANTIC_ICONS`, `CASES`) are **deprecated and strictly banned**.

Always use lowercase: `color`, `theme`, `typography`, `spacing`, `timing`, `font`, `font_family`, `icons`, `shadow`, `media`, `grid`, `animation`, `reset`, `svg`, `gradient`, `vars`.

```js
// ❌ BANNED
import { TYPOGRAPHY } from '@symbo.ls/scratch'
const { COLOR } = context.designSystem

// ✅ CORRECT
import { typography } from '@symbo.ls/scratch'
const { color } = context.designSystem
```

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

## Rule 10 — `extends` and `childExtends` MUST be a quoted string name, never a variable or inline object

**Always use a quoted string** for `extends` and `childExtends`. The string references a component registered in `components/`. Never use a direct JS variable reference — variables require imports (Rule 2) and break after serialization (Rule 33).

```js
// ✅ CORRECT — string references (uses component registry lookup, no imports)
Header: { extends: 'Navbar' }
childExtends: 'NavLink'
QuickAction: { extends: 'QuickActionBtn', text: 'Book' }

// ❌ WRONG — direct variable reference (requires import, breaks after serialization)
import { QuickActionBtn } from './QuickActionBtn.js'
QuickAction: { extends: QuickActionBtn }

// ❌ WRONG — inline object (dumps prop values as raw text on every child)
childExtends: {
  tag: 'button',
  background: 'transparent',
  border: '2px solid transparent'
}
```

Define shared components in `components/`, register in `components/index.js` via `export *`, then reference by string name. This is how DOMQL's component registry works — PascalCase keys auto-resolve to registered components.

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

## Rule 14 — HTML attributes go at root level — `attr: {}` is rarely needed

The `attrs-in-props` module auto-detects 600+ standard HTML attributes per tag AND handles `data-*`/`aria-*` attributes. Place them directly at the element root — both static and dynamic (function) values work.

`data-*` and `aria-*` support camelCase (`ariaLabel` → `aria-label`, `dataTestId` → `data-test-id`) and shorthand objects (`aria: { label: 'foo' }`, `data: { testId: 'bar' }`).

Use `attr: {}` only for truly custom attributes not in the attrs-in-props database.

```js
// ✅ — standard attrs at root (auto-detected)
export const Input = {
  tag: 'input',
  type: (el, s) => s.inputType,
  placeholder: 'Enter text...',
  required: true,
  disabled: (el, s) => s.isDisabled,
}

// ✅ — aria/data also at root (auto-detected, camelCase converted)
export const Widget = {
  role: 'button',
  tabindex: '0',
  ariaLabel: (el, s) => s.label,
  dataTestId: 'widget',
}

// ✅ — shorthand objects for aria/data
export const Nav = {
  aria: { label: 'Main navigation', expanded: true },
  data: { section: 'header' },
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

## Rule 18 — Tab/view switching: use `show:` or `hide:`, NOT `if:` or manual DOM

**`if:`** removes/re-creates the element from the DOM — use for conditional rendering.
**`show:`** / **`hide:`** toggles visibility (keeps element in DOM) — use for tabs, views, toggles.

```js
// ✅ — show/hide pattern for tab switching (keeps DOM, toggles visibility)
HomeView: { flow: 'column', show: (el, s) => s.root.activeView === 'home', ... },
ExploreView: { flow: 'column', show: (el, s) => s.root.activeView === 'explore', ... },

// Switch tab via state
TabHome: { extends: 'Button', text: 'Home', onClick: (e, el, s) => s.root.update({ activeView: 'home' }) },
TabExplore: { extends: 'Button', text: 'Explore', onClick: (e, el, s) => s.root.update({ activeView: 'explore' }) }
```

```js
// ✅ — if: for conditional rendering (adds/removes from DOM)
Modal: { if: (el, s) => s.root.modalOpen, extends: 'Dialog', ... }
ErrorBanner: { if: (el, s) => s.root.error, text: (el, s) => s.root.error }
```

```js
// ❌ WRONG — manual DOM display toggling
export const switchView = function switchView(view) {
  ['home', 'explore'].forEach(v => {
    const el = document.getElementById('view-' + v)
    if (el) el.style.display = v === view ? 'flex' : 'none'
  })
}
```

**When to use which:**
| Pattern | DOM behavior | Use for |
|---|---|---|
| `if: (el, s) => bool` | Removes/creates element | Conditional content, modals, error messages |
| `show: (el, s) => bool` | Hides with display:none (keeps in DOM) | Tabs, views, toggleable panels |
| `hide: (el, s) => bool` | Inverse of show (true = hidden) | Alternative to show when logic is inverted |

---

## Rule 19 — Conditional props: use `isX` + `'.isX'` — STRICTLY enforce when multiple properties share the same condition

**IMPORTANT:** When two or more properties depend on the same condition, you MUST use the `isX` / `'.isX'` pattern. NEVER repeat the same condition across multiple property functions — this is redundant, harder to read, and violates DOMQL v3 conventions.

```js
// ✅ CORRECT — conditional props with isX pattern
export const MapPanel = {
  width: '0',
  height: '0',
  opacity: '0',
  '@tabletS': { width: '0' },
  '@mobileL': { width: '0' },

  isMapView: (el, s) => s.root.showMapView,
  '.isMapView': {
    width: '50%',
    height: 'calc(100vh - 130px)',
    opacity: '1',
    '@tabletS': { width: '55%' },
    '@mobileL': { width: '100%' },
  },
}

// ❌ WRONG — same condition repeated across multiple properties
export const MapPanel = {
  width: (el, s) => s.root.showMapView ? '50%' : '0',
  height: (el, s) => s.root.showMapView ? 'calc(100vh - 130px)' : '0',
  opacity: (el, s) => s.root.showMapView ? '1' : '0',
  '@tabletS': { width: (el, s) => s.root.showMapView ? '55%' : '0' },
  '@mobileL': { width: (el, s) => s.root.showMapView ? '100%' : '0' },
}

// ❌ WRONG — deprecated props function with conditional spread
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

## Rule 26 — NEVER extend `'Text'`, `'Box'`, or `'Flex'` — replace with `flow:` / `align:`

`Text`, `Box`, and `Flex` are built-in base primitives. Every element is already a Box; any element with `text:` already behaves as Text; any element with `flow:` or `align:` already behaves as Flex. Extending them explicitly causes an unnecessary merge step at runtime.

**CRITICAL: When removing `extends: 'Flex'`, you MUST replace it with `flow: 'x'` or `flow: 'y'`.** Do NOT just delete the extends — an element without `flow:` or `align:` becomes a regular block div and the layout breaks. This is the #1 most common mistake.

```js
// ✅ CORRECT — replaced extends: 'Flex' with flow:
Row: { flow: 'x', gap: 'A', align: 'center center' }
Stack: { flow: 'y', gap: 'B', padding: 'C' }
Header: { flow: 'x', align: 'center space-between', padding: 'A B' }
Sidebar: { flow: 'y', gap: 'A', width: 'G' }

// ✅ CORRECT — Text/Box don't need extends either
Tag: { tag: 'span', text: 'NEW', padding: 'X A', fontSize: 'Y' }
Card: { padding: 'B', background: 'white' }

// ❌ WRONG — unnecessary extends
Row: { extends: 'Flex', gap: 'A', align: 'center' }
Tag: { extends: 'Text', text: 'NEW', padding: 'X A' }
Card: { extends: 'Box', padding: 'B', background: 'white' }

// ❌❌ CATASTROPHIC — removed extends: 'Flex' but forgot to add flow
Container: { padding: 'C', maxWidth: 'K' }  // BROKEN! now a block div, not flex!
// ✅ FIX — always add flow when removing extends: 'Flex'
Container: { flow: 'y', padding: 'C', maxWidth: 'K' }
```

**Replacement checklist:**
| Remove | Replace with |
|---|---|
| `extends: 'Flex'` | `flow: 'x'` (horizontal) or `flow: 'y'` (vertical) — MANDATORY |
| `extends: 'Box'` | nothing (every element is already a Box) |
| `extends: 'Text'` | nothing (any element with `text:` is already Text) |

Use a semantic or functional component instead: `Link`, `Button`, `Header`, `Section`, etc. For flex layout, use `flow:` or `align:` props directly.

---

## Rule 27 — ALWAYS use Design System values in props

ALL spacing, colors, typography, borders, and shadows MUST come from the design system. Never hardcode raw values. The design system provides tokens for everything — use them.

```js
// ✅ CORRECT — design system tokens
Header: { padding: 'A B', gap: 'B', fontSize: 'B1', color: 'primary', background: 'surface' }
Card: { borderRadius: 'Z', boxShadow: '0 A Z gray.2', margin: 'C 0' }

// ❌ WRONG — hardcoded values
Header: { padding: '16px 26px', gap: '26px', fontSize: '32px', color: '#333', background: '#fff' }
Card: { borderRadius: '10px', boxShadow: '0 16px 10px rgba(0,0,0,.2)', margin: '42px 0' }
```

**Token reference:** X(3px), Y(6px), Z(10px), A(16px), B(26px), C(42px), D(67px), E(109px), F(177px) — with sub-tokens (Z1, Z2, A1, A2, B1, B2, C1, C2).

**Colors:** Always use theme color tokens (`'primary'`, `'secondary'`, `'surface'`, `'white'`, `'gray.5'`) — never hex, rgb, or hsl.

**Typography:** Use font size tokens (`'Y'`, `'Z'`, `'A'`, `'B'`, `'C'`) — never `'14px'` or `'1.2rem'`.

---

## Rule 28 — NEVER use raw px values

Pixel values are forbidden. Every numeric dimension must use a design system spacing token. If a value doesn't have a matching token, use the closest one or token math (`'A+Z'`).

```js
// ✅ CORRECT
{ padding: 'A', width: 'G', gap: 'Z', fontSize: 'B', borderRadius: 'Y' }
{ margin: '-Y 0', letterSpacing: '-X' }

// ❌ WRONG — raw px values
{ padding: '16px', width: '500px', gap: '10px', fontSize: '26px', borderRadius: '6px' }
{ margin: '-6px 0', letterSpacing: '-3px' }
```

This applies to ALL CSS properties: padding, margin, gap, width, height, minWidth, maxWidth, minHeight, maxHeight, top, left, right, bottom, borderRadius, fontSize, letterSpacing, lineHeight, borderWidth, outlineWidth, boxShadow offsets, etc.

---

## Rule 29 — ALWAYS use `Icon` component for SVG icons, ALWAYS save icons in `designSystem/icons`

**ALL SVGs — including brand logos, custom icons, and complex path data — MUST be stored in `designSystem/icons` and rendered via the `Icon` component.** There are ZERO exceptions. Never use `tag: 'svg'`, never nest `<path>` children, never inline SVG markup of any kind in components.

```js
// ✅ CORRECT — Icon component referencing designSystem/icons
Logo: { extends: 'Icon', icon: 'airbnbLogo' }
CloseBtn: { extends: 'Icon', icon: 'close' }
SearchIcon: { extends: 'Icon', icon: 'search', width: 'A', height: 'A' }

// In designSystem/icons.js — ALL SVGs go here, including complex brand logos:
// Icons ALWAYS use width="24" height="24" to match the viewBox.
// The Icon component controls the display size — not the SVG itself.
export default {
  airbnbLogo: '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M5.47...Z"/></svg>',
  close: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>',
  chevronRight: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>',
  search: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>',
  user: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8z"/></svg>'
}
```

```js
// ❌ WRONG — inline SVG with tag: 'svg' (this is FORBIDDEN even for brand logos)
LogoSvg: {
  tag: 'svg',
  attr: { viewBox: '0 0 24 24' },
  LogoPath: { tag: 'path', attr: { d: 'M5.47...' } }
}

// ❌ WRONG — extending Svg for icons
Logo: { extends: 'Svg', html: '<path d="..."/>' }

// ❌ WRONG — any SVG element nesting in components
BrandLogo: { tag: 'svg', width: 'E1', height: 'C1', children: [...] }
```

**Why:** The `Icon` component auto-handles sprite mode, size tokens, camelCase name lookup, theme colors, and keeps SVG markup out of component logic. Even complex brand logos with long path data belong in `designSystem/icons` — the component just references them by name.

**Icon prop:** Use `icon: 'iconName'` to reference icons from `designSystem/icons`. The value must match a key in the icons object. Do NOT use `iconName:`, `iconSrc:`, or `props: { name: ... }`.

```js
// ✅ CORRECT
{ extends: 'Icon', icon: 'user' }
{ extends: 'Button', icon: 'search', text: 'Search' }

// ❌ WRONG prop names
{ extends: 'Icon', iconName: 'user' }
{ extends: 'Icon', iconSrc: 'user' }
{ extends: 'Icon', props: { name: 'user' } }
```

**Icon SVG dimensions:** All SVGs in `designSystem/icons` MUST have `width="24" height="24"` and a matching `viewBox="0 0 24 24"`. The width/height match the viewBox so the icon renders at its natural size. The `Icon` component then scales the display size via design system tokens (e.g., `width: 'A'` on the component).

```js
// ✅ CORRECT — SVG has 24x24 to match viewBox, Icon component controls display size
// designSystem/icons.js:
{ star: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="..."/></svg>' }
// component:
{ extends: 'Icon', icon: 'star', width: 'B', height: 'B' }  // displays at 26px

// ❌ WRONG — mismatched or missing width/height
{ star: '<svg viewBox="0 0 24 24"><path d="..."/></svg>' }           // missing width/height
{ star: '<svg width="48" height="48" viewBox="0 0 24 24">...</svg>' } // mismatch
{ star: '<svg width="100%" viewBox="0 0 24 24">...</svg>' }           // percentage
```

**`Svg`** is ONLY for decorative/structural SVG backgrounds or illustrations that are NOT icons.

---

## Rule 30 — NEVER use direct JS DOM manipulation — ALWAYS use Symbols/DOMQL syntax

All DOM structure, events, children, and nesting MUST be expressed through DOMQL's declarative object syntax. Never use `document.createElement`, `document.querySelector`, `innerHTML`, `appendChild`, `removeChild`, `classList.add/remove/toggle`, `setAttribute`, `style.xxx = ...`, or any imperative DOM API.

DOMQL handles the DOM — you describe what you want, not how to build it.

```js
// ✅ CORRECT — declarative DOMQL syntax
export const Dropdown = {
  flow: 'y',
  gap: 'Z',
  isOpen: false,

  Trigger: {
    extends: 'Button',
    text: 'Open',
    onClick: (e, el, s) => s.update({ isOpen: !s.isOpen })
  },

  Menu: {
    if: (el, s) => s.isOpen,
    flow: 'y',
    padding: 'A',
    background: 'surface',
    children: (el, s) => s.items,
    childExtends: 'MenuItem',
    childrenAs: 'state'
  }
}
```

```js
// ❌ WRONG — imperative DOM manipulation
export const Dropdown = {
  onRender: (el) => {
    const menu = document.createElement('div')
    menu.className = 'menu'
    el.node.appendChild(menu)

    el.node.querySelector('.trigger').addEventListener('click', () => {
      menu.style.display = menu.style.display === 'none' ? 'block' : 'none'
    })

    items.forEach(item => {
      const li = document.createElement('div')
      li.textContent = item.label
      menu.appendChild(li)
    })
  }
}
```

**Use instead:**
| Imperative (WRONG) | DOMQL (CORRECT) |
|---|---|
| `document.createElement('div')` | Nest a child key: `Child: { tag: 'div' }` |
| `el.appendChild(child)` | Add as object key or use `children` array |
| `el.removeChild(child)` | Use `if: (el, s) => condition` to remove from DOM |
| `el.classList.toggle('x')` | Use `isX` + `'.isX'` pattern (Rule 19) |
| `el.style.display = 'none'` | Use `show:` / `hide:` to toggle visibility, or `if:` to remove from DOM |
| `el.innerHTML = '...'` | Use `text:` or `html:` prop |
| `el.setAttribute('href', x)` | Use `href: x` at root level |
| `el.addEventListener('click', fn)` | Use `onClick: fn` |
| `document.querySelector('.x')` | Reference by key name in object tree |
| `parent.insertBefore(a, b)` | Use `children` array ordering |

---

## Rule 31 — NEVER use `html:` with functions returning markup — use DOMQL nesting and children

The `html:` prop must NEVER be a function that returns HTML template strings. This is imperative HTML generation disguised as DOMQL. Instead, use proper DOMQL children, nesting, `text:`, `if:`, and responsive breakpoints.

```js
// ❌ WRONG — html: function returning template strings with inline styles
SearchSummary: {
  html: (el, s) => {
    if (window.innerWidth <= 768) {
      const loc = s.root.searchLocation
      return `<span style="color:#222;font-weight:600">${loc}</span> · <span>anywhere</span>`
    }
    return s.root.searchLocation || 'anywhere'
  }
}
```

```js
// ✅ CORRECT — DOMQL declarative children with responsive breakpoints
SearchSummary: {
  flow: 'x',
  gap: 'Y',

  Location: {
    text: (el, s) => s.root.searchLocation || '{{ anywhere | polyglot }}',
    color: (el, s) => s.root.searchLocation ? 'primary' : 'gray.5',
    fontWeight: (el, s) => s.root.searchLocation ? '600' : '400'
  },

  Dot1: { text: '·' },

  Duration: {
    text: (el, s) => s.root.searchDuration || '{{ anyDuration | polyglot }}',
    color: (el, s) => s.root.searchDuration ? 'primary' : 'gray.5',
    fontWeight: (el, s) => s.root.searchDuration ? '600' : '400',
    show: true,
    '@tabletS': { hide: true }
  },

  Dot2: { text: '·', show: true, '@tabletS': { hide: true } },

  Type: {
    text: (el, s) => s.root.searchType || '{{ saleOrRent | polyglot }}',
    color: (el, s) => s.root.searchType ? 'primary' : 'gray.5',
    fontWeight: (el, s) => s.root.searchType ? '600' : '400',
    show: true,
    '@tabletS': { hide: true }
  }
}
```

**Key replacements:**
| html: pattern (WRONG) | DOMQL (CORRECT) |
|---|---|
| `` `<span>${text}</span>` `` | Child: `{ text: (el, s) => value }` |
| `` style="color:#222" `` | `color: 'primary'` or `color: (el, s) => condition ? 'primary' : 'gray.5'` |
| `` style="font-weight:600" `` | `fontWeight: (el, s) => condition ? '600' : '400'` |
| `window.innerWidth <= 768` | `@mobileL: { ... }` or `@tabletS: { ... }` breakpoints |
| `if (condition) return html` | `if: (el, s) => condition` on child components |
| String concatenation with `·` | Separate Dot child: `{ text: '·' }` |

---

## Rule 32 — Search/filter UI: use state + reactive props, NEVER DOM traversal

Filtering, searching, and showing/hiding content MUST be done through state updates and reactive DOMQL props. NEVER traverse the DOM with `parentNode`, `children`, `querySelector`, `textContent`, `style.display`, `remove()`, or `createElement`.

```js
// ❌ CATASTROPHICALLY WRONG — manual DOM traversal and mutation
SearchInput: {
  tag: 'input',
  onRender: (el) => {
    el.node.addEventListener('input', function () {
      const val = this.value.toLowerCase()
      const parent = el.node.parentNode
      Array.from(parent.children).forEach(child => {
        child.style.display = child.textContent.includes(val) ? '' : 'none'
      })
      if (!matches) {
        const noRes = document.createElement('div')
        noRes.textContent = 'No results'
        parent.appendChild(noRes)
      }
    })
  }
}
```

```js
// ✅ CORRECT — state-driven filtering with DOMQL reactivity
SearchInput: {
  extends: 'Input',
  placeholder: '{{ searchDestinations | polyglot }}',
  onInput: (e, el, s) => s.update({ filterQuery: e.target.value.toLowerCase().trim() })
},

// Grid items show/hide reactively based on state (show: keeps in DOM, if: removes)
DestGrid: {
  flow: 'x',
  flexWrap: 'wrap',
  gap: 'A',
  show: (el, s) => el.call('filteredCount', 'destinations') > 0,
  children: (el, s) => s.destinations,
  childExtends: 'DestCard',
  childrenAs: 'state'
},

// Each card filters itself — show: toggles visibility
DestCard: {
  show: (el, s) => !s.root.filterQuery || s.name.toLowerCase().includes(s.root.filterQuery),
  text: (el, s) => s.name
},

// Section labels hide when their grid has no matches
SuggestLabel: {
  tag: 'h3',
  text: '{{ suggestedDestinations | polyglot }}',
  show: (el, s) => el.call('filteredCount', 'destinations') > 0
},

// No results message — if: adds/removes from DOM
NoResults: {
  if: (el, s) => s.root.filterQuery && el.call('totalMatches') === 0,
  text: '{{ noLocations | polyglot }}',
  padding: 'C A',
  textAlign: 'center',
  color: 'gray.5',
  fontSize: 'Z'
},

// Helper functions in functions/filteredCount.js:
// export const filteredCount = function filteredCount(section) {
//   const s = this.getState()
//   const items = s[section] || []
//   if (!s.root.filterQuery) return items.length
//   return items.filter(i => i.name.toLowerCase().includes(s.root.filterQuery)).length
// }
//
// export const totalMatches = function totalMatches() {
//   return this.call('filteredCount', 'destinations')
//        + this.call('filteredCount', 'moreCities')
//        + this.call('filteredCount', 'regions')
// }
```

**Key principle:** State drives the UI. When the user types in a search input, update state. All children react to state changes automatically — no need to find DOM nodes, loop through children, or toggle `style.display`.

| DOM traversal (WRONG) | DOMQL reactive (CORRECT) |
|---|---|
| `el.node.parentNode` / `.children` | State + child `show:` or `if:` props |
| `child.style.display = 'none'` | `show: (el, s) => condition` (keeps in DOM) or `if:` (removes) |
| `child.textContent.includes(val)` | `show: (el, s) => s.name.includes(s.root.filterQuery)` |
| `document.createElement('div')` | Declarative child with `if:` (adds/removes from DOM) |
| `parent.appendChild(noRes)` | NoResults child with `if: (el, s) => noMatches` |
| `noRes.remove()` | `if:` returns false → auto-removed from DOM |
| `el.node.addEventListener('input', ...)` | `onInput: (e, el, s) => s.update(...)` |
| `el.node.placeholder = '...'` | `placeholder: '{{ searchDestinations \| polyglot }}'` |

---

## Rule 33 — NEVER use variables outside of scope — use `functions/*` with `el.call()` or `el.scope`

Functions and variables defined outside the component object are NOT available at runtime. The platform serializes components as JSON — any closure variables, helper functions, or module-level constants are lost.

**Use instead:**
- **`el.call('fnName', args)`** — call functions registered in `functions/` directory
- **`el.scope.varName`** — access variables stored in the component's scope

```js
// ❌ WRONG — variable outside of scope (lost after serialization)
const formatPrice = (n) => `$${n.toLocaleString()}`
const TAX_RATE = 0.08

export const PriceCard = {
  text: (el, s) => formatPrice(s.price * (1 + TAX_RATE))
}
```

```js
// ✅ CORRECT — functions in functions/ directory, called via el.call
// functions/formatPrice.js:
export const formatPrice = function formatPrice(amount) {
  return `$${amount.toLocaleString()}`
}

// components/PriceCard.js:
export const PriceCard = {
  text: (el, s) => el.call('formatPrice', s.price * 1.08)
}
```

```js
// ✅ CORRECT — scope for shared local values
export const FilterPanel = {
  onInit: (el) => {
    el.scope.debounceTimer = null
  },
  SearchInput: {
    extends: 'Input',
    onInput: (e, el, s) => {
      clearTimeout(el.scope.debounceTimer)
      el.scope.debounceTimer = setTimeout(() => {
        s.update({ filterQuery: e.target.value })
      }, 200)
    }
  }
}
```

**What gets serialized (safe):** component object properties, state, `text:`, `if:`, `show:`, `onX:` handler strings.
**What is lost:** `const`/`let`/`var` outside the export, imported helpers, closures, module-level side effects.

---

## Rule 34 — Spacing tokens are em-based — aligned elements must share the same fontSize

Symbols spacing tokens (X, Y, Z, A, B, C, D, E…) resolve relative to the element's computed `fontSize`. Two sibling elements using the same token but with different `fontSize` values will render at different pixel sizes.

When building layouts where elements must visually align (grids, columns, tables), every element in the same row or column MUST explicitly declare the same `fontSize` token. Do not rely on inheritance.

```js
// ✅ All siblings share fontSize: 'Z1' — E and C resolve identically across all
const ColHeader  = { fontSize: 'Z1', width: 'E', ... }
const DataCell   = { fontSize: 'Z1', width: 'E', ... }
const RowNum     = { fontSize: 'Z1', width: 'C', ... }
CornerCell: { tag: 'div', fontSize: 'Z1', width: 'C', ... }

// Inner content needing a different size sets it on the inner child only
CellInput: { fontSize: 'Z2', ... }  // does not affect parent token resolution

// ❌ Mixed fontSize — E resolves to different px values, elements misalign
const ColHeader = { fontSize: 'Z1', width: 'E', ... }
const DataCell  = { fontSize: 'Z2', width: 'E', ... }  // wider than ColHeader
```

---

## Rule 35 — PascalCase is required for all child elements — use distinctive names to avoid unintended auto-extend

camelCase keys are treated as CSS properties and will never render as child elements. PascalCase is always required. However, PascalCase keys auto-extend the registered component of the same name — generic structural names (`Header`, `Body`, `Row`, `Cells`, `List`) may match default library components and silently inherit unexpected gap, padding, or flex behaviour.

Use distinctive PascalCase names for structural wrappers that should carry no inherited styling.

```js
// ✅ Distinctive PascalCase — renders as child, no accidental auto-extend
HeaderRow:  { tag: 'div', display: 'flex', ... }
ColLabels:  { tag: 'div', display: 'flex', gap: '0', ... }
CellsList:  { tag: 'div', display: 'flex', gap: '0', ... }
BodyRows:   { tag: 'div', flexDirection: 'column', ... }

// ✅ PascalCase intentionally extending a registered component
RowNum: { extends: 'RowNumberCell' }

// ❌ camelCase — treated as CSS property, element never renders
headerRow: { tag: 'div', display: 'flex' }
cellsList: { tag: 'div', display: 'flex' }

// ❌ Generic PascalCase — may silently auto-extend a default library component
Header: { tag: 'div', display: 'flex' }
Cells:  { tag: 'div', display: 'flex' }
Row:    { tag: 'div', display: 'flex' }
```

---

## Rule 36 — `childrenAs: 'state'` passes state automatically — never use `el.parent.state`

When using `childrenAs: 'state'`, each child automatically receives its data slice as state. State is also inherited by nested children at any depth. Always use `s.field` directly — never traverse via `el.parent.state`.

```js
// ✅
const DataCell = {
  background: (el, s) => s.active ? 'accentBg' : 'surface',
  Input: {
    value:  (el, s) => s.value,       // s inherited automatically
    color:  (el, s) => s.fmt?.colorRed ? 'danger' : 'text',
    onBlur: (e, el, s) => el.call('commit', { val: e.target.value, r: s.r, c: s.c }),
  }
}

// ❌ — el.parent.state traversal is unnecessary and fragile
Input: {
  value: (el) => el.parent.state.value,
}
```

---

## Rule 37 — `designSystem.color` is for color values only — never store dimensions there

`designSystem.color` resolves token names for CSS color properties. It is not a general-purpose token store. Never put px values, font sizes, or dimension values there — they will not resolve correctly for non-color CSS properties.

For sizes that fall between spacing tokens, use sub-tokens (Z1, Z2, A1, A2, B1, B2, C1, C2) or token math. For genuine edge cases with no matching token, define a CSS custom property on the component and reference it as a spacing value.

```js
// ✅ sub-tokens for in-between sizes
fontSize: 'Z2',   // between Z and A
width:    'C1',   // between C and D
height:   'A1',   // between A and B

// ✅ edge-case custom property (only when no token fits)
'--trackW': 'someValue',
width: '--trackW'

// ❌ dimensions stored in designSystem.color — wrong namespace, won't resolve
color: {
  btnHeight:  '28px',
  cellWidth:  '100px',
  uiFontSize: '13px',
}
```

---

## Rule 38 — `el.context` is for debugging only — never read design system values from it in props

`el.context` exposes runtime internals. It is available in prop functions but is intended only for debugging. Never use it to read design system values in production component props — always reference token name strings directly.

```js
// ❌ WRONG — reading from el.context in a prop function
height:   (el) => el.context.designSystem.uiScale.btnHeight
fontSize: (el) => el.context.designSystem.typography.base

// ✅ CORRECT — token name resolves through the design system automatically
height:   'B'
fontSize: 'Z2'
```

---

## Rule 39 — `el.node` is fine for reading — forbidden only for DOM manipulation

`el.node` is a valid reference to the underlying DOM node. Reading properties from it is acceptable. What is forbidden is manipulating the DOM through it — assigning properties, setting styles, or changing content.

```js
// ✅ Reading from el.node — fine
const atStart  = el.node.selectionStart === 0
const atEnd    = el.node.selectionEnd === el.node.value.length
const scrollH  = el.node.scrollHeight

// ❌ Writing to el.node — forbidden
el.node.value       = 'something'
el.node.textContent = 'something'
el.node.style.color = 'red'
el.node.innerHTML   = '...'
```

Native DOM methods that have no DOMQL equivalent (`.focus()`, `.blur()`, `.select()`) are fine to call on `el.node` directly:

```js
// ✅ Calling native methods — fine
el.node.focus()
el.node.blur()
el.node.select()
```

---

## Rule 40 — Never use `document.getElementById` or any browser DOM query — always use DOMQL tree methods

`document.getElementById`, `document.querySelector`, `document.querySelectorAll` and all browser DOM query APIs bypass the DOMQL component tree. They are forbidden. Use DOMQL's own traversal methods to find elements, then access `.node` only to call native methods if needed.

```js
// ❌ Bypassing DOMQL — querying the real DOM directly
const t = document.getElementById(`cell-${r}-${c}`)
if (t) t.focus()

document.querySelector('.toolbar button').click()

// ✅ Use DOMQL tree methods to find the element
const cell = el.lookdown(`cell-${r}-${c}`)
if (cell) cell.node.focus()
```

**DOMQL traversal reference:**

| Need | Use |
|---|---|
| Find a child/descendant by key | `el.lookdown('KeyName')` |
| Find all matching descendants | `el.lookdownAll('KeyName')` |
| Find a parent/ancestor by key | `el.lookup('KeyName')` |
| Find by exact path | `el.spotByPath(['Parent', 'Child', 'Target'])` |
| Get the root element | `el.getRoot()` |
| Get root state | `el.getRootState()` |
| Next sibling | `el.nextElement()` |
| Previous sibling | `el.previousElement()` |

---

## Rule 41 — STRICTLY use `Link` component with `href` as a direct property — NEVER use `<a>` tags or put `href` in `attrs`

**IMPORTANT:** All links MUST use the `Link` component with `extends: 'Link'`. The `href` property MUST be placed at the root level of the component, NOT inside `attrs: {}`. This is critical for proper routing and navigation.

```js
// ✅ CORRECT — Link component with href at root
Nav: {
  extends: 'Link',
  href: '/about',
  text: 'About'
}

// ✅ CORRECT — dynamic href at root
ProfileLink: {
  extends: 'Link',
  href: (el, s) => `/user/${s.userId}`,
  text: 'View Profile'
}

// ❌ WRONG — href inside attrs
Nav: {
  extends: 'Link',
  attrs: { href: '/about' },   // NEVER put href in attrs
  text: 'About'
}

// ❌ WRONG — using tag 'a' instead of Link component
Nav: {
  tag: 'a',
  href: '/about',
  text: 'About'
}

// ❌ WRONG — no extends: 'Link' for navigation
Nav: {
  href: '/about',              // href without Link component won't route properly
  text: 'About'
}
```

---

## Rule 42 — NEVER use `window.location` for navigation — use `el.router()`

All navigation MUST use `el.router()`. Never use `window.location.href`, `window.location.assign()`, `window.location.replace()`, or any `window.location` assignment. These bypass SPA routing and break the framework's navigation model.

```js
// ✅ CORRECT — SPA navigation via el.router
onClick: (e, el) => el.router('/', el.getRoot())
onClick: (e, el, s) => el.router('/profile/' + s.userId, el.getRoot())

// ❌ WRONG — bypasses framework routing
onClick: () => { window.location.href = '/' }
onClick: () => { window.location.assign('/profile') }
```

---

## Rule 43 — Use default template styles for new apps — no tiny fonts

When creating new apps, always base the design system on the default template at `templates/templates/default/designSystem/`. This includes typography, font sizes, spacing, colors, shapes, grid, and media breakpoints.

Never use font sizes smaller than what the default template defines. The default template enforces recommended, readable sizing for all new projects.

---

## Rule 45 — Define each color ONCE — use modifier syntax for shades, not Tailwind-style palettes

Never define multiple shade variants of the same color (`blue100`, `blue200`, `blue300`). Define one base value and use the Symbols shading system: `.XX` (opacity), `+N` (lighten), `-N` (darken), `=N` (absolute lightness).

```js
// ✅ CORRECT — single base, shades via modifiers in components
color: { blue: '#0474f2' }
// → 'blue', 'blue.7', 'blue+20', 'blue-30', 'blue.5+15'

// ❌ WRONG — Tailwind-style shade palette
color: { blue50: '#eff6ff', blue100: '#dbeafe', blue200: '#bfdbfe', blue300: '#93c5fd' }
```

---

## Rule 46 — Fetched shared libraries are READONLY — override locally instead

When shared libraries are fetched from the platform (`smbls fetch`/`smbls sync`), both `sharedLibraries.js` and the `.symbols_local/libs/` folders are strictly **readonly** — they are overwritten on every fetch/sync. Never edit fetched library files. To override shared library components, define them in your local project files — the app always wins at runtime.

`sharedLibraries.js` can be manually edited when custom-linking to local folders (advanced use case). But fetched libraries must never be modified.

```js
// ❌ WRONG — editing fetched .symbols_local/libs/ files
// These are overwritten on every fetch/sync

// ✅ CORRECT — override in local components/
// If shared library has Button with theme: 'primary',
// define your own Button in components/Button.js to override it
export const Button = { theme: 'dialog', padding: 'Z A' }
```

---

## Rule 44 — Never chain CSS selectors — use nesting instead

Media queries (`@dark`, `@mobileL`) and pseudo-classes (`:hover`, `:active`) must be nested as separate objects, never chained into a single key string.

```js
// ❌ WRONG — chained selector string
Button: {
  '@dark :hover': { background: 'blue' },
  '@mobileL :active': { opacity: '0.5' },
}

// ✅ CORRECT — nested objects
Button: {
  '@dark': {
    ':hover': { background: 'blue' },
  },
  '@mobileL': {
    ':active': { opacity: '0.5' },
  },
}
```

