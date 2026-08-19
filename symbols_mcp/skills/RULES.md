# Symbols / DOMQL — Strict Rules for AI Agents

These rules are absolute. Violations cause silent failures (black page, nothing renders, or a working app with a degraded UX you'll later have to rebuild). DO NOT override with general coding instincts.

This is **smbls** (signal-based reactive engine, flat element API). The forbidden patterns below are the canonical anti-patterns to refuse — they are all banned regardless of where they came from.

---

## #1 simplification you'll ship 10× a day: rename the key to match the component

DOMQL auto-extends by key. If the key name matches a registered component, that component IS the extends — no `extends` clause needed.

```js
// ❌ WRONG — wrapper key with redundant extends
Header: { extends: 'Navbar' }

// ✅ RIGHT — just name the key after the component you're extending
Navbar: {}
```

This is the **single most common boilerplate mistake** in Symbols projects. Multiple instances → suffix with `_N` (the part before `_` is what auto-extends):

```js
Navbar_1: { ...overrides },
Navbar_2: { ...overrides }     // both auto-extend Navbar
```

Keep `extends:` only when the wrapper key carries a **genuinely different semantic meaning** (e.g. `SidebarNav: { extends: 'Navbar' }` if your project uses `SidebarNav` as a label and `Navbar` as the base). When the wrapper is just dead-weight aliasing — drop it. Full coverage in Rule 6 below.

---

## CRITICAL: Canonical syntax

| ✅ USE THIS | ❌ NEVER USE |
| -- | -- |
| `extends: 'Component'` | ~~`extend: 'Component'`~~ |
| `childExtends: 'Component'` | ~~`childExtend: 'Component'`~~ |
| `onClick: (e, el, s) => …` flat top-level | ~~`on: { click: (e, el, s) => … }`~~ |
| `onInit: (el, s) => …` flat top-level | ~~`on: { init: (el, s) => … }`~~ |
| `el.text` / `el.value(el, s)` flat access | ~~`el.props.text` / `el.props.value`~~ |
| `el.onClick` runtime read flat | ~~`el.on.click`~~ |
| props flattened directly on element | ~~`props: { ... }` wrapper~~ |
| individual reactive prop functions | ~~`props: ({ state }) => ({ … })`~~ |
| `(el, s) => …` reactive prop signature | ~~`({ props, state }) => …`~~ |
| `align: 'center center'` | ~~`flexAlign: 'center center'`~~ |
| `children` + `childExtends` | ~~`$collection`, `$propsCollection`~~ |
| `children` + `childrenAs: 'state'` | ~~`$stateCollection`~~ |
| No `extends` for Text/Box/Flex; replace `extends: 'Flex'` with `flow:` | ~~`extends: 'Text'`~~, ~~`extends: 'Box'`~~, ~~`extends: 'Flex'`~~ |
| `color: {}`, `theme: {}`, `typography: {}` (lowercase) | ~~`COLOR: {}`, `THEME: {}`, `TYPOGRAPHY: {}`~~ |
| `import { typography } from '@symbo.ls/scratch'` | ~~`import { TYPOGRAPHY } …`~~ |
| `el.call('fn', …args)` for any project function | raw imports across project files |
| `el.fetch` declarative | raw `window.fetch` / `axios` calls in components |
| `'{{ key | polyglot }}'` for translations | hardcoded user-facing strings |

**Flat access — flat is the law:**

- Props live at `el.X` (NOT `el.props.X`)
- Event handlers live at `el.onClick`, `el.onInit`, etc. (NOT `el.on.click`, NOT inside `on: {}`)
- A component declared with `props: { ... }` will have those props **flattened onto the element** at runtime — but the canonical declaration writes them flat too. Do NOT rely on the `props` wrapper at the call site or the read site.

Confirmed by the smbls test suite:
- `smbls/packages/css-in-props/__tests__/cases.test.js:6` — _"props are flat on the element (element.X instead of element.props.X)"_
- `smbls/packages/element/__tests__/create.test.js:779-786` — _"on.init syntax is not supported (use onInit instead)"_

---

## Rule 0 — Design system keys are ALWAYS lowercase

UPPERCASE design system keys (`COLOR`, `THEME`, `TYPOGRAPHY`, `SPACING`, `TIMING`, `FONT`, `FONT_FAMILY`, `ICONS`, `SHADOW`, `MEDIA`, `GRID`, `ANIMATION`, `RESET`, `SVG`, `GRADIENT`, `SEMANTIC_ICONS`, `CASES`) are **deprecated and strictly banned**.

Always lowercase: `color`, `theme`, `typography`, `spacing`, `timing`, `font`, `font_family`, `icons`, `shadow`, `media`, `grid`, `animation`, `reset`, `svg`, `gradient`, `vars`.

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

// ❌ — function returning object
export const Header = (el, state) => ({ padding: 'A' })
```

---

## Rule 2 — NO imports between project files (zero exceptions inside components/, functions/, methods/, designSystem/)

NEVER use `import` between `components/`, `pages/`, `functions/`, `methods/`, `designSystem/`, `state/`, `snippets/`. Reference components by PascalCase key in the object tree. Reference functions via `el.call('fnName', …)`. Reference design tokens by string name (`color: 'primary'`, `padding: 'A'`).

```js
// ❌
import { Navbar } from './Navbar.js'
import { findUser } from '../functions/findUser.js'
import { brandColor } from '../designSystem/color.js'

// ✅
Nav: { extends: 'Navbar' }                       // string lookup
text: (el, s) => el.call('findUser', s).name     // el.call
color: 'brand'                                    // token name
```

**Only exception:** `pages/index.js` is the route registry — imports ARE allowed there.

```js
// pages/index.js — only file where imports are permitted
import { main } from './main.js'
export default { '/': main }
```

---

## Rule 3 — `components/index.js` uses `export *`, NOT `export * as`

`export * as Foo` wraps in a namespace and breaks string-key resolution.

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

## Rule 6 — PascalCase keys = child components (auto-extends). Lowercase keys NEVER render.

**This is the #1 root cause of "missing content".** Lowercase keys (`h1:`, `nav:`, `form:`, `hgroup:`, `group:`, `div:`) are filtered out of the child-creation loop entirely (`packages/element/src/create.js` → `createChildren` gates on `firstChar < 65 || firstChar > 90`), so a lowercase key NEVER renders, regardless of whether it happens to match an HTML tag name.

```js
// ❌ Lowercase — never renders as child elements
h1:     { text: 'Hello' }
nav:    { ... }
form:   { ... }
hgroup: { ... }

// ✅ PascalCase — always renders
H1:     { tag: 'h1', text: 'Hello' }   // explicit tag
Nav:    { ... }                         // tag auto-detected from key (Nav → 'nav')
Form:   { ... }                         // also auto-extends built-in Form atom
Hgroup: { ... }                         // also auto-extends built-in Hgroup atom
```

The framework's tag-from-key auto-detection (`packages/element/src/cache.js → detectTag`) lowercases the PascalCase key and maps it to a valid HTML tag, so `Nav: {}` renders as `<nav>`, `Article: {}` as `<article>`, etc.

**Built-in atoms auto-apply when key matches:** `Box`, `Flex`, `Grid`, `Hgroup`, `Form`, `Text`, `Img`, `Iframe`, `Svg`, `Shape`, `Picture`, `Video`, `Link`, `Button`, `Select`, `Input`, `NumberInput`, `Checkbox`, `Radio`, `Toggle`, `Textarea`, `Icon`. **You don't need `extends: 'Flex'`** — naming the child `Flex: {...}` is enough. Same goes for any registered component: `Button: {...}` inherits Button without an explicit `extends`.

```js
export const MyCard = {
  Hgroup: { gap: '0' },        // auto-extends: 'Hgroup'
  Flex:   { flow: 'y', gap: 'A' }   // auto-applies the Flex atom
}
```

`Key_suffix` (e.g. `Icon_1`, `Icon_2`) also auto-extends `Key` — useful when you need multiple instances:

```js
Toolbar: {
  Icon_1: { icon: 'home' },
  Icon_2: { icon: 'search' }
}
```

### Auto-extend by key — `Header: { extends: 'Navbar' }` should usually be `Navbar: {}`

**The rule:** if a key would do nothing besides aliasing a registered component, drop the wrapper. Rename the key to match the component. DOMQL extends by key automatically.

```js
// ❌                                         // ✅
Header: { extends: 'Navbar' }                  Navbar: {}
Header: { extends: 'Navbar', padding: 'A' }    Navbar: { padding: 'A' }
Hgroup: { extends: 'Hgroup', gap: '0' }        Hgroup: { gap: '0' }
Card:   { extends: 'Card',   padding: 'B' }    Card:   { padding: 'B' }
Foo:    { extends: 'PriceCard', text: 'Pro' }  PriceCard: { text: 'Pro' }
```

**Multiple instances of the same component:** suffix with `_N`. The runtime only looks at the part before the underscore for auto-extend resolution, so `Navbar_1` and `Navbar_2` both auto-extend `Navbar`:

```js
PriceCards: {
  PriceCard_1: { tier: 'starter' },
  PriceCard_2: { tier: 'pro' },
  PriceCard_3: { tier: 'enterprise' }
}
```

**Keep `extends` ONLY when one of these is true:**

- The key carries a **genuinely different semantic meaning** from the component name. `SidebarNav: { extends: 'Navbar' }` is OK if your project distinguishes a `SidebarNav` from the regular `Navbar` somewhere else. If `SidebarNav` only exists because you didn't think to write `Navbar`, drop it.
- **Multi-base composition** — `extends: ['Hgroup', 'Form']` to mix two component shapes.
- **Nested-child reference chain** — `extends: 'AppShell > Sidebar'` to extend a deeply-keyed component.

In every other case, the `extends:` line is dead weight. The audit (`bin/symbols-audit`) flags this aggressively as Rule 6 — see `audit_component(code)` for line-precise hits.

**Audit grep for redundant aliasing:**

```sh
# Find every case where the key name matches a value in extends
grep -nE "^\s+([A-Z][a-zA-Z0-9_]*):\s*\{\s*extends:\s*'\1'" symbols/components/*.js
```

Each match is a candidate for the renaming rule above.

---

## Rule 7 — State updates via `s.update()`, NEVER mutate directly

```js
// ✅
onClick: (e, el, s) => s.update({ count: s.count + 1 })

// ❌ — no re-render
onClick: (e, el, s) => { s.count = s.count + 1 }
```

Root-level global state: `s.root.update({ key: val })` or `s.rootUpdate({ key: val })`.

State methods (all available on every state):
`update`, `replace`, `set`, `clean`, `parse`, `keys`, `values`, `destroy`, `add`, `toggle`, `remove`, `setByPath`, `getByPath`, `removeByPath`, `setPathCollection`, `removePathCollection`, `reset`, `apply`, `applyFunction`, `applyReplace`, `quietUpdate`, `quietReplace`, `rootUpdate`, `parentUpdate`.

---

## Rule 8 — `el.call('fn', arg)` — `this` is the element

Functions live in `functions/` (or `methods/`) and are invoked via `el.call`/`this.call`. NEVER pass `el` as the first argument — it's already bound.

```js
// functions/findMe.js
export const findMe = function findMe(state) {
  const node = this.node  // 'this' is the DOMQL element
  return state.users[state.activeUserId]
}

// ✅
onClick: (e, el, s) => el.call('findMe', s)
text:    (el, s)    => el.call('findMe', s).name

// ❌ — el passed twice
onClick: (e, el) => el.call('findMe', el, s)
```

Lookup order: `context.methods → context.functions → context.utils → element prototype methods`.

Inside lifecycle methods (`onInit`, `onUpdate`) and `this`-bound contexts, use `this.call(...)`.

---

## Rule 9 — Icons: use `Icon` component, store SVGs in `designSystem/icons`

Use the `Icon` component to render icons. `Icon` accepts a `name` or `icon` prop to reference icons from `designSystem.icons`. Auto-converts kebab-case to camelCase. Supports sprite mode via `useIconSprite: true`.

```js
// ✅ — reference icon by name from designSystem.icons
MyBtn: {
  tag: 'button', align: 'center center', cursor: 'pointer',
  Icon: { name: 'arrowRight' }
}

// ❌ — do NOT inline SVGs via Svg for icons
MyBtn: {
  Svg: { viewBox: '0 0 24 24', html: '<path d="..." fill="currentColor"/>' }
}
```

---

## Rule 10 — `extends` and `childExtends` MUST be a quoted string, never a variable or inline object

The string references a component registered in `components/`. Direct variable references require imports (Rule 2) and break after JSON serialization to the platform.

> **Heads-up:** before reaching for `extends`, check whether you can just **rename the key to match the component**. `Header: { extends: 'Navbar' }` should usually be `Navbar: {}` — DOMQL auto-extends by key. See Rule 6 for the full rule. The examples in this rule (Rule 10) intentionally use `extends:` to focus on the string-vs-variable concern, but in real code you'll most often drop `extends` entirely.

```js
// ✅ string references (when `extends` is genuinely needed)
SidebarNav: { extends: 'Navbar' }            // OK — key carries distinct semantic meaning
childExtends: 'NavLink'

// ❌ direct variable reference
import { QuickActionBtn } from './QuickActionBtn.js'
QuickAction: { extends: QuickActionBtn }

// ❌ inline object — dumps prop values as raw text on every child
childExtends: { tag: 'button', background: 'transparent' }
```

Define shared components in `components/`, register via `export *`, reference by string.

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
{ boxShadow: 'black.1 0 A C C' }
{ boxShadow: 'black.1 0 A C C, white.5 0 B D D' }  // multiple → commas
{ boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }          // raw CSS passes through

// ❌ — old comma-separated syntax
{ border: 'solid, gray, 1px' }
```

---

## Rule 13 — CSS override precedence: component level beats props level (and there is no `props` wrapper anyway)

```js
// ✅ — override at component level (where everything lives)
export const MyLink = {
  extends: 'Link',
  color: 'mediumBlue'
}

// ❌ — `props: {}` wrapper is forbidden — flatten onto the element
export const MyLink = {
  extends: 'Link',
  props: { color: 'mediumBlue' }
}
```

---

## Rule 14 — HTML attributes go at root level — `attr: {}` is rarely needed

The `attrs-in-props` module auto-detects 600+ standard HTML attributes per tag. Place them directly at the element root — both static and dynamic (function) values work.

`data-*` and `aria-*` support camelCase (`ariaLabel` → `aria-label`, `dataTestId` → `data-test-id`) and shorthand objects (`aria: { label: 'foo' }`, `data: { testId: 'bar' }`).

Use `attr: {}` ONLY for truly custom attributes not in the attrs-in-props database.

```js
// ✅ — standard attrs at root (auto-detected)
export const Input = {
  tag: 'input',
  type: (el, s) => s.inputType,
  placeholder: 'Enter text...',
  required: true,
  disabled: (el, s) => s.isDisabled
}

// ✅ — aria/data at root (auto-detected, camelCase converted)
export const Widget = {
  role: 'button',
  tabindex: '0',
  ariaLabel: (el, s) => s.label,
  dataTestId: 'widget'
}

// ✅ — shorthand objects
export const Nav = {
  aria: { label: 'Main navigation', expanded: true },
  data: { section: 'header' }
}

// ❌ — don't wrap standard HTML attributes in attr: {}
export const Input = {
  attr: { type: 'text', placeholder: 'Enter...' }
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

Better: prefer `onInit` (fires once before DOM creation, no re-fires), or use signal-based reactive props instead of imperative onRender code.

---

## Rule 16 — Icons use `Icon`, decorative/structural SVGs use `Svg`

Icons → `Icon` component referencing `designSystem.icons` by name.
Decorative/structural SVGs (backgrounds, illustrations) → `Svg` with data stored in `designSystem/svg_data.js`.

```js
// ✅ — icons
Icon: { name: 'arrowRight' }

// ✅ — decorative/structural SVG
Svg: {
  src: (el) => el.context.designSystem.svg_data.folderTopRight,
  aspectRatio: '466 / 48'
}

// ❌
Svg: { viewBox: '0 0 24 24', html: '<path d="..."/>' }   // for an icon — wrong tool
```

---

## Rule 17 — `customRouterElement` for persistent layouts

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

⚠️ **`if:` is DESTRUCTIVE.** Each `if:` toggle false → true destroys the DOM node and re-creates it on the next true. CSS transitions, focus state, scroll position, video playback, IntersectionObserver subscriptions, mounted libraries (chart.js, mapbox, leaflet) — all reset every toggle. For animated show/hide, use `hide:` (a CSS_PROPS_REGISTRY entry that reactively toggles `display`). For modal/dropdown opacity-fade, use the `opacity + pointerEvents` pattern (COMMON_MISTAKES #16).

- **`if:`** removes / re-creates from DOM — reserve for content that genuinely shouldn't exist when the condition is false (404 page, error state, unmounted modal contents).
- **`show:`** / **`hide:`** toggles visibility (keeps in DOM) — for tabs, views, toggles, animated reveals.

```js
// ✅ — show/hide pattern for tabs
HomeView:    { flow: 'y', show: (el, s) => s.root.activeView === 'home' },
ExploreView: { flow: 'y', show: (el, s) => s.root.activeView === 'explore' },
TabHome:     { extends: 'Button', text: 'Home',
               onClick: (e, el, s) => s.root.update({ activeView: 'home' }) }
```

```js
// ✅ — if: for conditional rendering
Modal: { if: (el, s) => s.root.modalOpen, extends: 'Dialog' }
ErrorBanner: { if: (el, s) => s.root.error, text: (el, s) => s.root.error }
```

```js
// ❌ — manual DOM display toggling
const el = document.getElementById('view-home')
if (el) el.style.display = 'none'
```

---

## Rule 19 — Reactive props are functions of `(el, s)` — NOT `({ props, state })`

Every reactive prop function takes the element and state directly (third arg is context if needed):

```js
// ✅
text:        (el, s) => s.user.name
color:       (el, s) => s.active ? 'primary' : 'gray.5'
fontWeight:  (el, s) => s.active ? '600' : '400'
hide:        (el, s) => !s.root.searchOpen
href:        (el, s) => `/user/${s.userId}`
onClick:     (e, el, s) => s.update({ open: !s.open })
onInit:      (el, s, ctx) => el.scope.timer = null

// ❌ — destructured `({ props, state })` signature is forbidden
text: ({ state }) => state.user.name
text: ({ props }) => props.label
```

### What is and isn't reactive

The framework registers reactive effects (via `createEffect`) ONLY for these prop function values:
- `text`, `html`, `value`, `style`, `attr` (function-valued)
- `if`, `show`, `hide`
- Any prop in `CSS_PROPS_REGISTRY` (color, background, padding, margin, gap, fontSize, fontWeight, lineHeight, borderRadius, etc.)
- Any prop in `DEFAULT_CSS_PROPERTIES_LIST`

Custom non-CSS function props — including `isX` conditionals — are NOT wrapped in `createEffect`. They evaluate ONCE during initial render (`applyStaticMixins` → `applyConditionals`) and never re-evaluate when state changes.

### Conditional props (`.isX` / `'!isX'` / `$isX`) — fully reactive

The conditional-cases syntax is the canonical way to express grouped conditional CSS. `isX: (el, s) => …` defines a condition, and the `.isX: {…}` / `'!isX': {…}` block contributes CSS/attrs when the condition resolves truthy/falsy. `$isX` references a global condition from `context.cases`.

The framework wraps `isX` conditions in `createEffect` so the matching `.isX` / `'!isX'` block re-applies whenever any state read by the condition changes. State-driven appearance changes work out of the box.

**STRICTLY enforce this pattern when two or more CSS properties share the same condition.** Repeating the same condition across multiple property functions is redundant and harder to read — collapse them into a single `isX` + `'.isX'` block.

```js
// ✅ CORRECT — single condition drives a whole CSS block (reactive)
export const TabBtn = {
  background: 'transparent',
  color: 'currentColor',
  fontWeight: '400',

  isActive: (el, s) => s.root.activeTab === el.key,
  '.isActive': {
    background: 'primary',
    color: 'white',
    fontWeight: '600'
  }
}

// ✅ CORRECT — '!isX' for the inverse branch
export const Item = {
  opacity: 1,
  isSelected: (el, s) => s.selectedId === el.key,
  '.isSelected': { background: 'primary', color: 'white' },
  '!isSelected': { opacity: 0.6 }
}

// ✅ CORRECT — $isX for global cases from context.cases (browser / device detection)
$isSafari: { paddingTop: 'env(safe-area-inset-top)' }

// ❌ AVOID — same condition repeated across many property functions
export const TabBtn = {
  background: (el, s) => s.root.activeTab === el.key ? 'primary' : 'transparent',
  color:      (el, s) => s.root.activeTab === el.key ? 'white'   : 'currentColor',
  fontWeight: (el, s) => s.root.activeTab === el.key ? '600'     : '400'
}
```

For groups with many CSS props that share one condition — including responsive breakpoints — use the conditional block:

```js
// ✅ One isX drives an entire reactive style group (incl. nested breakpoints)
export const MapPanel = {
  width: '0', height: '0', opacity: '0',
  '@tabletS': { width: '0' },
  '@mobileL': { width: '0' },

  isMapView: (el, s) => s.root.showMapView,
  '.isMapView': {
    width: '50%',
    height: 'calc(100vh - 130px)',
    opacity: '1',
    '@tabletS': { width: '55%' },
    '@mobileL': { width: '100%' }
  }
}
```

For animated show/hide, prefer `hide:` (a CSS_PROPS_REGISTRY entry that reactively toggles `display`) over `if:`. `if:` IS reactive, but each toggle re-creates the DOM node which kills CSS transitions.

---

## Rule 20 — CSS transitions and signal reactivity

The framework uses signal-based reactivity — most prop changes are batched into a single render tick. For CSS transitions that depend on a "before" state being painted before the "after", you must read a layout property to force a flow:

```js
// FadeIn — force browser to paint opacity:0 before flipping to 1
modalNode.style.opacity = '0'
modalNode.style.visibility = 'visible'
s.root.update({ activeModal: true })
modalNode.style.opacity = '0'
void modalNode.offsetHeight   // force reflow
modalNode.style.opacity = ''   // release — CSS transition fires

// FadeOut — wait for CSS transition before removing
modalNode.style.opacity = '0'
setTimeout(() => {
  modalNode.style.opacity = ''
  modalNode.style.visibility = ''
  s.root.update({ activeModal: false })
}, 280)  // match CSS transition duration
```

If you find yourself doing this often, model the modal with CSS classes + `isOpen` toggle and let the framework handle it.

---

## Rule 21 — Semantic-First Architecture

Use semantic components for meaningful content. NEVER use generic divs.

| Intent | Use |
| -- | -- |
| Page header | Header |
| Navigation | Nav |
| Primary content | Main |
| Standalone article/entity | Article |
| Thematic grouping | Section |
| Sidebar | Aside |
| Actions | Button |
| Navigation links | Link |
| User input | Input / Form |

---

## Rule 22 — ARIA and accessibility attributes

Standard HTML attributes (`role`, `tabindex`) at root. Use shorthand objects for `aria` and `data`. Use native elements instead of role overrides whenever possible.

```js
// ✅
role: 'button',
tabindex: '0',
aria: {
  label:    (el, s) => s.label,
  busy:     (el, s) => s.loading,
  live:     'polite',
  expanded: (el, s) => s.open
}
```

---

## Rule 23 — Picture `src` goes on Img child, NEVER on Picture

The `<picture>` tag does NOT support `src`. Place `src` on the inner `Img`:

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

The key `Map` auto-detects as HTML `<map>` (image maps), default `display: inline` with height 0. ALWAYS add `tag: 'div'`.

```js
export const Map = { flow: 'y', tag: 'div', /* ... */ }
```

---

## Rule 25 — `/files/` path resolution

Paths like `/files/logo.png` reference the framework's embedded file system via `context.files`. The `/files/` prefix is stripped automatically — keys are filenames (`"logo.png"`, not `"/files/logo.png"`).

---

## Rule 26 — NEVER extend `'Text'`, `'Box'`, or `'Flex'` — replace with `flow:` / `align:`

`Text`, `Box`, and `Flex` are built-in primitives. Every element is already a Box; any element with `text:` already behaves as Text; any element with `flow:` or `align:` already behaves as Flex. Extending them causes a redundant merge step at runtime.

**CRITICAL: When removing `extends: 'Flex'`, you MUST replace it with `flow: 'x'` or `flow: 'y'`.** An element without `flow:` or `align:` becomes a regular block div and the layout breaks. This is the #1 most common mistake.

```js
// ✅
Row:    { flow: 'x', gap: 'A', align: 'center center' }
Stack:  { flow: 'y', gap: 'B', padding: 'C' }
Header: { flow: 'x', align: 'center space-between', padding: 'A B' }
Tag:    { tag: 'span', text: 'NEW', padding: 'X A', fontSize: 'Y' }
Card:   { padding: 'B', background: 'white' }

// ❌
Row:  { extends: 'Flex', gap: 'A' }
Tag:  { extends: 'Text', text: 'NEW' }
Card: { extends: 'Box', padding: 'B' }

// ❌❌ CATASTROPHIC — removed extends: 'Flex' but forgot flow
Container: { padding: 'C', maxWidth: 'K' }   // BROKEN — block div, not flex
// ✅ FIX
Container: { flow: 'y', padding: 'C', maxWidth: 'K' }
```

---

## Rule 27 — STRICT: ALWAYS use design system tokens — NEVER raw values

ALL spacing, colors, typography, borders, shadows, sizes, durations MUST come from the design system. Hardcoded values are a hard rule violation, not a "nice to have". The design system is the single source of truth — every value flows from it.

```js
// ✅ design system tokens
Header: { padding: 'A B', gap: 'B', fontSize: 'B1', color: 'primary', background: 'surface' }
Card:   { borderRadius: 'Z', boxShadow: '0 A Z gray.2', margin: 'C 0' }

// ❌ hardcoded values
Header: { padding: '16px 26px', gap: '26px', fontSize: '32px', color: '#333', background: '#fff' }
Card:   { borderRadius: '10px', boxShadow: '0 16px 10px rgba(0,0,0,.2)', margin: '42px 0' }
```

**Sequence families share the letter alphabet but NOT values.** Every ratio family — typography, spacing, timing — generates its own sequence from `{ base, ratio }`. Same letter resolves to different absolute values per family:

| Family | Default `base × ratio` | What `'B'` resolves to | Used by |
|---|---|---|---|
| `typography` | `16 × 1.25` (major-third) | `≈ 25 px` | `fontSize`, `lineHeight`, `letterSpacing` |
| `spacing` | `16 × 1.618` (phi / golden) | `≈ 26 px` | `padding`, `margin`, `gap`, `width`, `height`, `boxSize`, `top/right/bottom/left`, `borderRadius` / `round`, `borderWidth`, `outlineWidth`, etc. |
| `timing` | `150 × 1.333` (perfect-fourth) | `≈ 200 ms` | `transition` duration, `animationDuration` |

**Spacing sequence (default):** X(≈3px), Y(≈6px), Z(≈10px), A(16px), B(≈26px), C(≈42px), D(≈68px), E(≈110px), F(≈178px) — plus sub-tokens (Z1, Z2, A1, A2, B1, B2, C1, C2…) for in-between values. Token math: `'A+Z'`, `'B-Y'`.

**Typography sequence (default):** Y(≈10px), Z(≈13px), A(16px), B(≈20px), C(≈25px), D(≈31px), E(≈39px) — plus sub-tokens. `fontSize: 'B'` ≠ `padding: 'B'` (typography ratio is 1.25, spacing is 1.618).

**Timing sequence (default):** A(150ms), B(≈200ms), C(≈266ms), D(≈355ms) — plus sub-tokens. `transition: 'B defaultBezier'` resolves to `200ms cubic-bezier(.29, .67, .51, .97)`.

**No custom-named tokens for these families.** Don't write `spacing: { gutterSm: 12 }` and reference `padding: 'gutterSm'` — the sequence model is closed. Pick the right letter (or sub-letter) or shift the `base`/`ratio`. Custom names ARE supported for `colors`, `themes`, `gradients`, `shadows`, `icons`, `cases`.

**Colors:** Always use theme color tokens (`'primary'`, `'secondary'`, `'surface'`, `'white'`, `'gray.5'`) — never hex, rgb, or hsl.

**Why strict:** Tokens resolve through theme/dark mode/responsive breakpoints automatically. A hardcoded `'#333'` won't switch in dark mode. A hardcoded `'16px'` won't scale on mobile. The whole design system stops working the moment you hardcode.

---

## Rule 28 — NEVER use raw px values

Pixel values are forbidden. Every numeric dimension uses a sequence-generated token from the **right family** (typography for `fontSize`/`lineHeight`/`letterSpacing`; spacing for `padding`/`margin`/`gap`/`width`/`height`/`top`/`right`/`bottom`/`left`/`borderRadius`/`borderWidth`/etc.; timing for `transition` duration). If a value doesn't have a matching letter, pick the nearest one, use a sub-token (e.g. `'A1'`, `'B2'`), or use token math (`'A+Z'`). Don't invent custom names — there are none for these families.

```js
// ✅
{ padding: 'A', width: 'G', gap: 'Z', fontSize: 'B', borderRadius: 'Y' }
{ margin: '-Y 0', letterSpacing: '-X' }

// ❌
{ padding: '16px', width: '500px', gap: '10px', fontSize: '26px' }
```

This applies to ALL CSS dimension properties: padding, margin, gap, width, height, minWidth, maxWidth, minHeight, maxHeight, top, left, right, bottom, borderRadius, fontSize, letterSpacing, lineHeight, borderWidth, outlineWidth, boxShadow offsets, etc.

---

## Rule 29 — ALWAYS use `Icon` for SVG icons; ALL SVGs in `designSystem/icons`

ALL SVGs — including brand logos, custom icons, and complex paths — MUST be stored in `designSystem/icons` and rendered via the `Icon` component. ZERO exceptions. Never `tag: 'svg'`, never nested `<path>` children, never inline SVG markup in components.

```js
// ✅
Logo:        { extends: 'Icon', icon: 'airbnbLogo' }
CloseBtn:    { extends: 'Icon', icon: 'close' }
SearchIcon:  { extends: 'Icon', icon: 'search', width: 'A', height: 'A' }

// designSystem/icons.js — ALL SVGs go here
export default {
  airbnbLogo:    '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M5.47...Z"/></svg>',
  close:         '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>',
  chevronRight:  '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>',
  search:        '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>'
}

// ❌
LogoSvg: { tag: 'svg', attr: { viewBox: '0 0 24 24' }, LogoPath: { tag: 'path' } }
Logo:    { extends: 'Svg', html: '<path d="..."/>' }
Brand:   { tag: 'svg', children: [...] }
```

**Icon prop:** Use `icon: 'iconName'` (or `name: 'iconName'`). Do NOT use `iconName:`, `iconSrc:`, or `props: { name: ... }`.

**Icon SVG dimensions:** All SVGs in `designSystem/icons` MUST have `width="24" height="24"` matching `viewBox="0 0 24 24"`. The `Icon` component scales display via design system tokens (e.g. `width: 'A'`).

`Svg` is ONLY for decorative/structural SVG backgrounds or illustrations that are NOT icons.

---

## Rule 30 — NEVER use direct DOM manipulation — ALWAYS use DOMQL declarative syntax

All DOM structure, events, children, and nesting MUST be expressed through DOMQL's declarative object syntax. Banned APIs (any of these inside a component file or function file is a violation):

| Banned API | Use instead |
| -- | -- |
| `document.createElement(tag)` | Nest a child key: `Child: { tag }` |
| `el.appendChild(child)` | Add as object key, or `children` array |
| `el.removeChild(child)` | `if: (el, s) => condition` |
| `el.classList.add/remove/toggle` | `isX` + `'.isX'` (Rule 19) or `class: { name: bool }` |
| `el.style.X = …` | DOMQL CSS-in-props (`color: …`, etc.) |
| `el.style.display = 'none'` | `show:` / `hide:` (keep in DOM) or `if:` (remove) |
| `el.innerHTML = '...'` | `text:` or `html:` prop |
| `el.setAttribute('href', x)` | `href: x` at root |
| `el.removeAttribute('disabled')` | `disabled: null` (returning null/undefined removes) |
| `el.addEventListener('click', fn)` | `onClick: fn` |
| `document.querySelector('.x')` / `getElementById` / `querySelectorAll` | `el.lookdown('Key')`, `el.lookdownAll('Key')`, `el.lookup('Key')` |
| `document.body.append(...)` | Compose into the DOMQL tree |
| `parent.insertBefore(a, b)` | `children` array ordering |
| `el.parentNode` / `.children` traversal | DOMQL tree: `el.parent`, `el.lookdown`, `el.getRoot()` |
| `el.textContent` / `.innerText` (write) | `text:` prop |
| `el.dataset.X = …` | `data: { x: … }` |
| `el.remove()` (raw DOM API on `el.node`) | `el.remove()` (DOMQL method) — disposes effects too |
| `window.location.href = '/x'` | `el.router('/x', el.getRoot())` |
| `window.location.assign/replace` | `el.router(...)` |
| `window.fetch(url)` in a component file | `el.fetch` declarative or `el.call('fetchX')` (Rule 47) |
| `addEventListener('storage'/'resize'/'scroll')` from a component | `onResize:`/`onScroll:` on the element when the event reaches it; otherwise the flat window/document family — `onWindowResize:` / `onWindowScroll:` / `onWindowStorage:` / `onDocumentClick:` (DOMQL-owned lifecycle, torn down on dispose) |
| `el.node.style.setProperty('--var', …)` / `documentElement.style.setProperty(...)` | `vars: { '--var': value }` prop or design-system token |
| `XMLHttpRequest` / `navigator.sendBeacon` | declarative `fetch:` prop or `el.call` wrapping `el.getDB()` (Rule 47) |
| raw `EventSource` / raw `WebSocket` constructors in components | wrap in a `functions/` file with cleanup (`el.scope.cleanup`); never instantiate at module top level |
| `MutationObserver` / `ResizeObserver` from components | reactive prop functions OR scoped via `el.scope` cleanup hook |
| `IntersectionObserver` from components | scoped via `el.scope` cleanup; preferred: a `functions/observeVisibility.js` helper invoked in `onRender` with a return-cleanup |

**Reading is fine. Writing is not.** `el.node.scrollTop`, `el.node.value`, `el.node.selectionStart`, `el.node.focus()`, `el.node.blur()`, `el.node.select()` are acceptable. Assigning to `el.node.X` is not (Rule 39).

```js
// ✅ declarative — full feature in DOMQL
export const Dropdown = {
  state: { isOpen: false },
  Trigger: {
    extends: 'Button', text: 'Open',
    onClick: (e, el, s) => s.update({ isOpen: !s.isOpen })
  },
  Menu: {
    if: (el, s) => s.isOpen,
    flow: 'y', padding: 'A', background: 'surface',
    children:     (el, s) => s.items,
    childExtends: 'MenuItem',
    childrenAs:   'state'
  }
}

// ❌ imperative — every line below is a violation
export const Dropdown = {
  onRender: (el) => {
    const menu = document.createElement('div')
    menu.className = 'menu'
    el.node.appendChild(menu)
    el.node.querySelector('.trigger').addEventListener('click', () => {
      menu.style.display = menu.style.display === 'none' ? 'block' : 'none'
    })
  }
}
```

---

## Rule 31 — NEVER use `html:` to return markup strings — use DOMQL nesting

`html:` must NEVER be a function that returns HTML template strings. That is imperative HTML masquerading as DOMQL. Use proper children, `text:`, `if:`, and responsive breakpoints.

```js
// ❌
SearchSummary: {
  html: (el, s) => {
    if (window.innerWidth <= 768) {
      return `<span style="color:#222;font-weight:600">${s.root.searchLocation}</span> · <span>anywhere</span>`
    }
    return s.root.searchLocation || 'anywhere'
  }
}

// ✅
SearchSummary: {
  flow: 'x', gap: 'Y',
  Location: {
    text:       (el, s) => s.root.searchLocation || '{{ anywhere | polyglot }}',
    color:      (el, s) => s.root.searchLocation ? 'primary' : 'gray.5',
    fontWeight: (el, s) => s.root.searchLocation ? '600' : '400'
  },
  Dot1: { text: '·' },
  Duration: {
    text: (el, s) => s.root.searchDuration || '{{ anyDuration | polyglot }}',
    show: true,
    '@tabletS': { hide: true }
  }
}
```

---

## Rule 32 — Search/filter UI: state-driven, NEVER DOM traversal

Filtering, searching, and showing/hiding MUST be done through state updates and reactive props. NEVER traverse the DOM with `parentNode`, `children`, `querySelector`, `textContent`, `style.display`, `remove()`, or `createElement`.

```js
// ✅ state-driven
SearchInput: {
  extends: 'Input',
  placeholder: '{{ searchDestinations | polyglot }}',
  onInput: (e, el, s) => s.update({ filterQuery: e.target.value.toLowerCase().trim() })
},
DestGrid: {
  flow: 'x', flexWrap: 'wrap', gap: 'A',
  show:         (el, s) => el.call('filteredCount', 'destinations') > 0,
  children:     (el, s) => s.destinations,
  childExtends: 'DestCard',
  childrenAs:   'state'
},
DestCard: {
  show: (el, s) => !s.root.filterQuery || s.name.toLowerCase().includes(s.root.filterQuery),
  text: (el, s) => s.name
},
NoResults: {
  if: (el, s) => s.root.filterQuery && el.call('totalMatches') === 0,
  text: '{{ noLocations | polyglot }}'
}
```

State drives the UI. Children react automatically — never find DOM nodes, never loop through children, never toggle `style.display`.

---

## Rule 33 — NEVER use module-level variables, helpers, closures — use `functions/` + `el.call`, or `el.scope`

Functions and variables defined outside the component object are NOT available at runtime. The platform serializes components — closures, helpers, and module-level constants are lost.

```js
// ❌ — variables outside scope
const formatPrice = (n) => `$${n.toLocaleString()}`
const TAX_RATE = 0.08
export const PriceCard = {
  text: (el, s) => formatPrice(s.price * (1 + TAX_RATE))
}

// ✅ — functions/ + el.call
// functions/formatPrice.js
export const formatPrice = function formatPrice(amount) {
  return `$${amount.toLocaleString()}`
}
// components/PriceCard.js
export const PriceCard = {
  text: (el, s) => el.call('formatPrice', s.price * 1.08)
}

// ✅ — el.scope for shared local values within a component instance
export const FilterPanel = {
  onInit: (el) => { el.scope.debounceTimer = null },
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

**What's safe:** component object properties, state, `text:`, `if:`, `show:`, `onX:` handler bodies (they're stringified during push to the platform).
**What is lost:** `const`/`let`/`var` outside the export, imported helpers, closures, module-level side effects.

---

## Rule 34 — Spacing tokens are em-based — aligned elements share the same fontSize

Symbols spacing tokens (X, Y, Z, A, B, C, D, E…) resolve relative to the element's computed `fontSize`. Two siblings with the same token but different `fontSize` render at different pixel sizes.

For grids/columns/tables, every element in the same row or column MUST declare the same `fontSize` token. Don't rely on inheritance.

```js
// ✅ shared fontSize → consistent E and C
const ColHeader = { fontSize: 'Z1', width: 'E' }
const DataCell  = { fontSize: 'Z1', width: 'E' }
const RowNum    = { fontSize: 'Z1', width: 'C' }
```

---

## Rule 35 — PascalCase keys — distinctive names to avoid auto-extend collisions

camelCase keys are CSS properties and never render as children. PascalCase auto-extends a registered component of the same name. Generic names (`Header`, `Body`, `Row`, `Cells`, `List`) may silently inherit from default library components.

Use distinctive names for structural wrappers without inherited styling.

```js
// ✅ distinctive PascalCase
HeaderRow: { tag: 'div', display: 'flex' }
ColLabels: { tag: 'div', display: 'flex' }
CellsList: { tag: 'div', display: 'flex' }

// ✅ intentionally extending a registered component
RowNum: { extends: 'RowNumberCell' }

// ❌ camelCase — treated as CSS prop, never renders
headerRow: { tag: 'div' }

// ❌ generic PascalCase — may silently auto-extend a library component
Header: { tag: 'div' }
Cells:  { tag: 'div' }
```

---

## Rule 36 — `childrenAs: 'state'` passes state automatically — never use `el.parent.state`

Each child receives its data slice as state. State is inherited by nested children at any depth. Always use `s.field` directly.

```js
// ✅
const DataCell = {
  background: (el, s) => s.active ? 'accentBg' : 'surface',
  Input: {
    value:  (el, s) => s.value,                // inherits s
    color:  (el, s) => s.fmt?.colorRed ? 'danger' : 'text',
    onBlur: (e, el, s) => el.call('commit', { val: e.target.value, r: s.r, c: s.c })
  }
}

// ❌
Input: { value: (el) => el.parent.state.value }
```

### Prefer `childrenAs: 'state'` over `state: 'key'` for reusability

`state: 'key'` (narrow scope by binding to a parent-state subtree) is **valid** and still works (see SYNTAX.md "Narrow state scope"). For component **reusability**, prefer `childrenAs: 'state'` — the child reads its own `s.field` and doesn't couple to the parent's state shape, so the same child component works for any list whose items match the shape it consumes.

```js
// ✅ Preferred for reusability — child is decoupled from parent state shape
export const TeamList = {
  state: { members: [] },
  childExtends: 'TeamItem',
  children:     (el, s) => s.members,
  childrenAs:   'state'
}
export const TeamItem = {
  Title: { text: (el, s) => s.name }       // works for any list of `{ name, ... }`
}

// ✅ Also valid — narrow scope; pick this when the child should NOT be reused
//   elsewhere and you want the parent's state subtree to be the child's state directly.
export const TeamList = {
  state: 'members',
  children: (el, s) => s,
  childExtends: 'TeamItem'
}
export const TeamItem = {
  state: true,                              // required: opt the child into its own state slot
  Title: { text: (el, s) => s.name }
}
```

---

## Rule 37 — `designSystem.color` is for color values only — never store dimensions there

Don't put px values, font sizes, or dimensions in `color`. They won't resolve for non-color CSS properties.

For in-between sizes, use sub-tokens (Z1, Z2, A1, A2…) or token math. For genuine edge cases, define a CSS custom property.

```js
// ✅
fontSize: 'Z2', width: 'C1', height: 'A1'
'--trackW': 'someValue', width: '--trackW'

// ❌
color: { btnHeight: '28px', cellWidth: '100px' }
```

---

## Rule 38 — `el.context` is for debugging only — never read design system in props

`el.context` exposes runtime internals. Available in prop functions, but for debugging only. Reference token names directly in props — they resolve through the design system automatically.

```js
// ❌
height:   (el) => el.context.designSystem.uiScale.btnHeight
fontSize: (el) => el.context.designSystem.typography.base

// ✅
height:   'B'
fontSize: 'Z2'
```

---

## Rule 39 — `el.node` is fine for reading — forbidden only for DOM manipulation

Reading `el.node` is fine. Writing through it is forbidden.

```js
// ✅ reading
const atStart = el.node.selectionStart === 0
const atEnd   = el.node.selectionEnd === el.node.value.length

// ❌ writing
el.node.value       = 'something'
el.node.textContent = 'something'
el.node.style.color = 'red'
el.node.innerHTML   = '...'

// ✅ native methods with no DOMQL equivalent
el.node.focus()
el.node.blur()
el.node.select()
```

---

## Rule 40 — Never use browser DOM queries — use DOMQL tree methods

`document.getElementById`, `document.querySelector`, `document.querySelectorAll` bypass the DOMQL tree. Forbidden.

| Need | Use |
| -- | -- |
| Find a child by key | `el.lookdown('KeyName')` |
| Find all matching descendants | `el.lookdownAll('KeyName')` |
| Find an ancestor by key | `el.lookup('KeyName')` |
| Find by exact path | `el.spotByPath(['Parent', 'Child', 'Target'])` |
| Get the root element | `el.getRoot()` |
| Get root state | `el.getRootState()` |
| Next sibling | `el.nextElement()` |
| Previous sibling | `el.previousElement()` |

```js
// ❌
const t = document.getElementById(`cell-${r}-${c}`)
if (t) t.focus()

// ✅
const cell = el.lookdown(`cell-${r}-${c}`)
if (cell) cell.node.focus()
```

---

## Rule 41 — STRICTLY use `Link` with `href` at root — NEVER `<a>` tags or href in `attr`

All links MUST use `extends: 'Link'`. The `href` property MUST be at the root level — NOT inside `attr: {}`.

```js
// ✅
Nav: { extends: 'Link', href: '/about', text: 'About' }
ProfileLink: {
  extends: 'Link',
  href: (el, s) => `/user/${s.userId}`,
  text: 'View Profile'
}

// ❌
Nav: { extends: 'Link', attr: { href: '/about' } }
Nav: { tag: 'a', href: '/about' }
```

---

## Rule 42 — NEVER use `window.location` for navigation — use `el.router()`

All SPA navigation MUST go through `el.router(path, el.getRoot())`. Never `window.location.href`, `assign()`, `replace()`.

```js
// ✅
onClick: (e, el)    => el.router('/', el.getRoot())
onClick: (e, el, s) => el.router(`/profile/${s.userId}`, el.getRoot())

// ❌
onClick: () => { window.location.href = '/' }
```

`el.router()` integrates with the router plugin — guards, dynamic params (`/:id`), query parsing, scroll management, and `customRouterElement` all work automatically.

---

## Rule 43 — Use default template styles for new apps — no tiny fonts

Base new apps' design system on the default template at `templates/templates/default/designSystem/` (typography, spacing, colors, shapes, grid, media). The default enforces readable sizing.

---

## Rule 44 — Never chain CSS selectors — nest instead

Media queries (`@dark`, `@mobileL`) and pseudo-classes (`:hover`, `:active`) must be nested as separate objects, never chained into a single key.

```js
// ❌
Button: {
  '@dark :hover':    { background: 'blue' },
  '@mobileL :active': { opacity: '0.5' }
}

// ✅
Button: {
  '@dark':    { ':hover':  { background: 'blue' } },
  '@mobileL': { ':active': { opacity: '0.5' } }
}
```

---

## Rule 45 — Define each color ONCE — use modifier syntax for shades

Never define multiple shade variants of the same color (`blue100`, `blue200`, `blue300`). Define one base value and use modifiers: `.XX` (opacity), `+N` (lighten), `-N` (darken), `=N` (absolute lightness).

```js
// ✅
color: { blue: '#0474f2' }
// → 'blue', 'blue.7', 'blue+20', 'blue-30', 'blue.5+15'

// ❌
color: { blue50: '#eff6ff', blue100: '#dbeafe', blue200: '#bfdbfe' }
```

---

## Rule 46 — Fetched shared libraries are READONLY — override locally instead

When shared libraries are fetched from the platform (`smbls fetch` / `smbls sync`), both `sharedLibraries.js` and `.symbols_local/libs/` are **strictly readonly** — overwritten on every fetch/sync. To override, define in your local project files — the app always wins at runtime.

```js
// ❌ — editing fetched .symbols_local/libs/ files
// These are overwritten on every fetch/sync

// ✅ — override in components/Button.js
export const Button = { theme: 'dialog', padding: 'Z A' }
```

`sharedLibraries.js` can be edited only when custom-linking to local folders (advanced). Fetched libraries — never.

---

## Rule 47 — STRICT: declarative data fetching via `el.fetch` / `state + fetch` — NEVER raw `window.fetch` in components

All data fetching MUST go through the smbls fetch plugin (`@symbo.ls/fetch`). Configure adapter in `config.js`, then use the declarative `fetch` prop on elements. Caching, stale-while-revalidate, retries, deduplication, pagination, optimistic updates, and refetch-on-focus are handled by the framework.

**Setup (`config.js`):**

```js
db: { adapter: 'supabase', url: 'https://xxx.supabase.co', key: 'sb_publishable_…' }
// or: { adapter: 'rest', url: 'https://api.example.com', headers: { Authorization: '…' } }
// or: { adapter: 'local', data: { articles: [] }, persist: true }
```

**Declarative usage (in any element):**

```js
// ✅ — minimal
{ state: 'articles', fetch: true }

// ✅ — with options
{ state: 'articles',
  fetch: { params: { status: 'published' }, cache: '5m', order: { by: 'created_at', asc: false }, limit: 20 } }

// ✅ — RPC + transform
{ state: { items: [], featured: null },
  fetch: {
    method: 'rpc', from: 'get_content_rows',
    params: { p_table: 'videos' },
    transform: (data) => ({ featured: data.find(v => v.is_featured), items: data.filter(v => !v.is_featured) })
  } }

// ✅ — parallel array of fetches
{ state: { articles: [], events: [] },
  fetch: [
    { method: 'rpc', from: 'get_content_rows', params: { p_table: 'articles' }, as: 'articles', cache: '5m' },
    { method: 'rpc', from: 'get_content_rows', params: { p_table: 'events' },   as: 'events',   cache: '5m' }
  ] }

// ✅ — submit on form submit
{ tag: 'form', fetch: { method: 'insert', from: 'contacts', on: 'submit' } }

// ✅ — pagination + keepPreviousData
{ state: { items: [], page: 1 },
  fetch: { from: 'articles', page: (el, s) => s.page, pageSize: 20, keepPreviousData: true } }
```

**❌ NEVER:**

```js
// raw window.fetch / axios in components
onClick: async (e, el, s) => {
  const r = await fetch('/api/articles')
  s.update({ items: await r.json() })
}

// useEffect-style imperative fetch in onRender
onRender: async (el, s) => {
  const r = await fetch(...)
  s.update({ data: r })
}
```

If you genuinely need imperative control (e.g. a multi-step flow), wrap it in a `functions/` file and call via `el.call('loadX')` — but `el.fetch` declarative is the default.

---

## Rule 48 — STRICT: all user-facing strings use polyglot — NEVER hardcoded text

All user-facing strings MUST go through the polyglot plugin (`@symbo.ls/polyglot`). Hardcoded English (or any single-language) strings in components are a violation, no matter how simple the app.

**No exceptions for length.** `'Submit'`, `'OK'`, `'Cancel'`, `'Loading…'`, `'…'`, `'Yes'`, `'No'` — every visible string MUST go through polyglot. ARIA labels (`aria-label`, `aria-description`), `title=` attributes, `placeholder=`, `alt=` text, validation messages, error toasts, and any `console.log` strings shown to the user — all polyglot. Single-language MVPs use `defaultLang: 'en'` with one entry — but every string still routes through polyglot so adding a language is one config change instead of a project-wide refactor.

**⚠️ Forbidden function names — these DO NOT exist and will silently fail:**
- `t` / `_t` / `__` — common i18n library aliases — DO NOT register or call them
- `tr` — DO NOT use; reactivity comes from the `{{ key | polyglot }}` template, not a separate `tr` function
- `i18n` / `__i18n` — DO NOT use

The ONLY registered polyglot exports (verified at `plugins/polyglot/functions.js:5-14`) are: `polyglot`, `getLocalStateLang`, `getActiveLang`, `getLang`, `setLang`, `getLanguages`, `loadTranslations`, `upsertTranslation`. Use `polyglot` for both reactive (in `{{ key | polyglot }}`) and imperative (`el.call('polyglot', 'key')`) lookups.

**Setup (`context`):**

```js
import { polyglotPlugin } from '@symbo.ls/polyglot'
import { polyglotFunctions } from '@symbo.ls/polyglot/functions'

context.polyglot = {
  defaultLang: 'en',
  languages: ['en', 'ka', 'ru'],
  translations: {
    en: { hello: 'Hello', search: 'Search', anyDuration: 'Any time' },
    ka: { hello: 'გამარჯობა', search: 'ძიება' },
    ru: { hello: 'Привет', search: 'Поиск' }
  }
  // OR for server-backed (CMS) translations:
  // fetch: { rpc: 'get_translations_if_changed', table: 'translations' }
}
context.functions = { ...context.functions, ...polyglotFunctions }
context.plugins   = [polyglotPlugin, ...]
```

**Usage:**

```js
// ✅ — mustache template (resolved by replaceLiteralsWithObjectFields, reactive on lang change)
{ text: '{{ hello | polyglot }}' }
{ placeholder: '{{ searchDestinations | polyglot }}' }

// ✅ — el.call('polyglot', key) — direct lookup (NOT reactive — captures the value at evaluation time)
{ text: (el) => el.call('polyglot', 'hello') }

// ✅ — per-language state field (e.g. CMS title_en / title_ka)
{ text: '{{ title_ | getLocalStateLang }}' }

// ✅ — language switcher
TabKa: { extends: 'Button', text: 'KA',
  onClick: (e, el) => el.call('setLang', 'ka') }

// ✅ — current language indicator
LangBadge: { text: (el) => el.call('getLang') }
```

**❌ NEVER:**

```js
// hardcoded user-facing strings
{ text: 'Hello' }
{ placeholder: 'Search destinations' }
{ text: 'Any time' }
```

For dynamic values mixed with translations, compose via state:

```js
{ text: (el, s) => `${el.call('polyglot', 'welcome')}, ${s.user.name}` }
```

Polyglot integrates with the fetch plugin: when `state.root.lang` changes, every fetch request gets an `Accept-Language` header automatically. The header is the only injection — fetch does NOT add a `lang` query parameter or RPC argument. If your backend expects `lang` in `params`, set it explicitly: `fetch: { from: 'articles', params: (el, s) => ({ lang: s.root.lang, status: 'published' }) }`.

---

## Rule 49 — STRICT: SEO/page metadata via helmet — NEVER raw `document.title` or `<head>` injection

All SEO metadata MUST go through `@symbo.ls/helmet`. Define `metadata` on the app or any page/component. Helmet handles runtime AND brender SSR identically.

```js
// ✅ — app-level defaults
// app.js
export default {
  metadata: {
    title:       'My App',
    description: 'Built with Symbols',
    'og:image':  '/social.png'
  }
}

// ✅ — page-level (overrides app-level)
export const about = {
  metadata: {
    title:       'About Us',
    description: 'Learn more about us'
  }
}

// ✅ — dynamic metadata (function-as-object)
export const product = {
  metadata: (el, s) => ({
    title:       s.product.name,
    description: s.product.description,
    'og:image':  s.product.image
  })
}

// ✅ — per-property functions
export const profile = {
  metadata: {
    title:       (el, s) => `${s.user.name} — My App`,
    description: (el, s) => s.user.bio
  }
}
```

**❌ NEVER:**

```js
onRender: (el, s) => { document.title = s.product.name }
onRender: (el)    => { document.head.appendChild(metaTag) }
```

---

## Rule 50 — STRICT: theme handling is owned by the framework — NEVER `data-theme` writes from project code

Theme activation is INTERNAL to the framework. Projects MUST NOT:

- read `matchMedia('(prefers-color-scheme: …)')` to detect dark mode
- write `document.documentElement.setAttribute('data-theme', …)`
- write `document.documentElement.dataset.theme = …`
- write `document.documentElement.style.colorScheme = …`
- write `document.documentElement.style.setProperty('--theme-…', …)`
- mirror the active theme into root state OR page state
- define a `globalTheme` / `theme` / `darkMode` field on any state slice

Theme is resolved at `create(app, options)` and lives on `context.globalTheme` + the scope root attribute. Use `changeGlobalTheme(newTheme, targetConfig?)` from `smbls` to flip themes — it updates `CONFIG.globalTheme`, writes `data-theme` to `CONFIG.themeRoot`, mirrors `style.colorScheme`, and refreshes CSS vars. The optional `targetConfig` enables cross-app theme control (e.g. an editor toolbar switching the embedded project's theme); omit it to operate on the active config from the push stack.

Persistence is the **project's responsibility** — `changeGlobalTheme` does NOT write to localStorage. If you want persistence, write to your `themeStorageKey` after calling it. `themeStorageKey` is read at init only. Set `themeStorageKey: false` in options to opt out of localStorage reads on init.

**Keep `useDocumentTheme: true` in `config.js` (default).** When set to `false`, the design system's `theme.document` `@light`/`@dark` blocks DO NOT apply background/color to `<body>` — pages render against the browser's default white. Symptom: dark-mode flashes white-then-dark on first paint, or never goes dark at all.

```js
// ✅ theme switcher (registered project function — import-safe at module top)
import { changeGlobalTheme } from 'smbls'

export function switchTheme () {
  const next = this.context.globalTheme === 'dark' ? 'light' : 'dark'
  changeGlobalTheme(next, this.context.designSystem)         // 2nd arg = optional targetConfig (cross-app)
  try { (this.context.window || window).localStorage.setItem('my-app-theme', next) } catch (e) {}
}

// component just calls it
ThemeToggle: {
  extends: 'Button', text: 'Toggle',
  onClick: (e, el) => el.call('switchTheme')
}

// ✅ Other valid invocations:
changeGlobalTheme('dark')                                     // forced — targets active config's themeRoot
changeGlobalTheme('auto')                                     // back to OS follow
changeGlobalTheme('ocean')                                    // custom scheme — must exist in designSystem/theme.js
changeGlobalTheme('light', otherApp.context.designSystem)     // cross-app targeting

// ✅ theme-dependent UI — pure CSS toggle (no JS reactivity)
LightLogo: { extends: 'Icon', icon: 'logoLight', '@dark': { display: 'none' } }
DarkLogo:  { extends: 'Icon', icon: 'logoDark',  display: 'none', '@dark': { display: 'inline-flex' } }

// ❌
onRender: (el) => {
  if (matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
}
```

For multi-design-system isolation: pass `options.themeRoot` on each `create()` call so each design system attaches its `data-theme` to its own root.

---

## Rule 51 — Use signal-based reactivity — never manual DOM updates from state changes

smbls is signal-based. When you write `text: (el, s) => s.count`, the framework subscribes that effect to `s.count` automatically. Manual update propagation is forbidden and breaks the model.

```js
// ✅ — declarative reactive prop, framework runs the effect
{ text: (el, s) => `Count: ${s.count}` }

// ❌ — manual DOM update from state change
onStateUpdate: (el, s) => { el.node.textContent = `Count: ${s.count}` }
```

For computed values across multiple state fields, just reference them in one prop function — the framework tracks all reads:

```js
{ text: (el, s) => `${s.user.firstName} ${s.user.lastName} (age ${s.user.age})` }
```

---

## Rule 52 — Use `el.fetch` / polyglot / helmet / router as a coherent modern stack

For any non-trivial project, the modern smbls stack is:

| Plugin | Purpose | Rule |
| -- | -- | -- |
| `@symbo.ls/fetch` | Declarative data fetching, caching, dedup, retry | Rule 47 |
| `@symbo.ls/polyglot` | Translations, language switching, fetch integration | Rule 48 |
| `@symbo.ls/helmet` | SEO metadata, brender SSR parity | Rule 49 |
| `@symbo.ls/router` | SPA routing, guards, dynamic params, query parsing | Rule 42 |
| `@symbo.ls/scratch` | Design system runtime, `changeGlobalTheme` | Rule 50 |
| `@symbo.ls/brender` | SSR / SSG static rendering, prefetch | (Rule 49 / metadata) |
| `@symbo.ls/helmet`, `@symbo.ls/freestyler`, `@symbo.ls/keyflows`, `@symbo.ls/sync`, `@symbo.ls/funcql` | composable plugins layered on top | per-plugin docs |

Wire them in `context.plugins` and `context.functions`. NEVER replace any of these with custom in-app implementations — that's a violation of "no hacks, no workarounds" (CLAUDE.md).

```js
// ✅ — wire the modern stack at app entry
import { polyglotPlugin } from '@symbo.ls/polyglot'
import { polyglotFunctions } from '@symbo.ls/polyglot/functions'
import { fetchPlugin } from '@symbo.ls/fetch'
import { routerPlugin } from '@symbo.ls/router'
import { helmetPlugin } from '@symbo.ls/helmet'

context.plugins   = [routerPlugin, fetchPlugin, polyglotPlugin, helmetPlugin]
context.functions = { ...context.functions, ...polyglotFunctions }
context.polyglot  = { defaultLang: 'en', languages: ['en','ka'], translations: { … } }
context.db        = { adapter: 'supabase', url: 'https://xxx.supabase.co', key: 'sb_publishable_…' }
// add @supabase/supabase-js to dependencies.js — DO NOT pass `createClient` here (mermaid bundle strips it)
```

---

## Rule 53 — Always run frank to recompile JSON when modifying templates

When modifying any project inside `templates/` or `templates-next/`:

- ALWAYS run `smbls frank to-json` after any change — never leave templates in an uncompiled state
- Applies to every edit: components, pages, design system, config, structure
- Verify compiled output before considering the task done

---

## Rule 54 — Clear `.parcel-cache` and restart dev server after framework-level changes

When making framework-level changes (in `smbls/`):

```sh
rm -rf .parcel-cache
# restart only the app's direct Parcel port (NEVER kill :1355 — that's the shared portless proxy)
```

`portless <app> --force sh -c '/…/smbls start --no-cache -p $PORT'`

---

## Rule 55 — Strict no-hacks policy

If something doesn't work: diagnose root cause and fix at the right level. NEVER:

- Use raw CSS values (px, rem, hex, rgba) when tokens exist (Rule 27/28)
- Use `document.querySelector` / `window.location` / raw DOM APIs (Rule 30/40/42)
- Import files directly between project files (Rule 2)
- Write `style` overrides to work around a layout bug — fix the layout
- Add `!important` or selector hacks to force visual output
- Wrap a broken component in a div to hide its broken behavior
- Copy-paste duplicated logic instead of fixing the abstraction
- Hardcode user-facing strings (Rule 48)
- Bypass fetch plugin with raw `window.fetch` in components (Rule 47)

If a bug is in the framework, fix it at the framework level. If a pattern is missing from the design system, add it to the design system. If a rule conflicts with what you need, surface the conflict and resolve properly.

---

## Rule 56 — smbls root app `extends:` does NOT inherit properties

The root element returned by `create(app, context)` (smblsapp) bypasses the key-based auto-extend that children go through. `extends: 'Foo'` at the top level does NOT merge `Foo`'s properties onto the root — only direct properties declared on the root object apply.

To share layout styles across multiple apps' root `app.js` files, export a plain styles object and spread it:

```js
// shared/AppShell.js
export const appShellStyles = {
  display: 'grid',
  gridTemplateRows: 'auto 1fr',
  minHeight: '100dvh'
}

// app.js
import { appShellStyles } from '.../AppShell.js'
export default {
  extends: 'Page',
  ...appShellStyles,
  // app-specific overrides + children
}
```

Lifecycle behaviors should be exported as helper functions and registered in `functions/` so each app's `onCreate` calls them via `el.call('installAppShellSync', s)`. Signature: `function (s) { const el = this; ... }` — `el.call` sets `this` to the element, first arg is the payload.

Component-based `AppShell` with `extends: 'Page'` still works fine for non-root uses (anywhere a child key auto-extends). The gotcha is specifically the smblsapp root.

---

## Rule 61 — STRICT: enforce component reusability — extract to `components/` or use `extends` / `childExtends` / `childProps`

**If a shape, style cluster, or behavior repeats — extract it.** The framework gives you four reuse mechanisms; pick the right one for the situation. Inlining a duplicate is a violation.

### When to extract

- **Same shape appears 2+ times** (even with small variations) → extract to `components/<Name>.js`, reference by string key.
- **Same style cluster used by multiple keys** → extract to a named component, then `extends: 'Name'` or rely on key auto-extend.
- **Same per-child behavior across a list** → use `childExtends: 'Name'` (single child type) or `childProps: { … }` (one-level overrides).
- **A handful of children share styling** with a parent → use `childProps:` so the parent injects them once.

### The four reuse mechanisms

| Mechanism | When to use | Example |
| -- | -- | -- |
| **Extract to `components/`** | Any shape used 2+ times anywhere in the project | `components/PriceCard.js` referenced as `PriceCard: {}` (auto-extend by key) |
| **`extends: 'Name'`** | Component needs a different key but same base | `MyLink: { extends: 'Link', color: 'brand' }` |
| **`extends: ['A', 'B']`** | Multi-base composition | `extends: ['Hgroup', 'Form']` |
| **`extends: 'Parent > Child > Sub'`** | Reference a nested-child shape from another component | `extends: 'AppShell > Sidebar'` |
| **`childExtends: 'Name'`** | All children of a list/group share one base | `NavList: { childExtends: 'NavLink' }` |
| **`childExtends: ['A', 'B']`** | Children compose multiple bases | rare — usually extract instead |
| **`childProps: { … }`** | Inject one-level prop overrides into every named child | `Layout: { childProps: { fontSize: 'A', color: 'caption' } }` |
| **`childProps: (parent, child) => ({ … })`** | Per-child computed overrides | dynamic key/props from parent state |

### ❌ Forbidden — duplicated shapes

```js
// ❌ Two identical-shape blocks — duplicated
export const Pricing = {
  StarterCard: {
    flow: 'y', padding: 'C', borderRadius: 'B', background: 'surface',
    Title: { fontSize: 'B', text: '{{ starter | polyglot }}' },
    Price: { fontSize: 'C', text: '$0' }
  },
  ProCard: {
    flow: 'y', padding: 'C', borderRadius: 'B', background: 'surface',
    Title: { fontSize: 'B', text: '{{ pro | polyglot }}' },
    Price: { fontSize: 'C', text: '$29' }
  }
}

// ❌ Three identical childExtends inline — duplicated
export const Nav = {
  Home: { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600', href: '/' },
  About: { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600', href: '/about' },
  Docs: { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600', href: '/docs' }
}
```

### ✅ Correct — extracted + reused

```js
// components/PricingCard.js
export const PricingCard = {
  flow: 'y', padding: 'C', borderRadius: 'B', background: 'surface',
  Title: { fontSize: 'B', text: (el, s) => s.title },
  Price: { fontSize: 'C', text: (el, s) => s.price }
}

// components/Pricing.js
export const Pricing = {
  flow: 'x', gap: 'B',
  childExtends: 'PricingCard',
  childrenAs: 'state',
  children: (el, s) => s.tiers   // [{ title, price }, ...]
}
```

```js
// components/NavLink.js
export const NavLink = {
  extends: 'Link',
  color: 'primary',
  padding: 'X A',
  fontWeight: '600'
}

// components/Nav.js — childExtends + state-driven children
export const Nav = {
  childExtends: 'NavLink',
  childrenAs:   'state',
  children: () => [
    { key: 'Home',  text: '{{ home | polyglot }}',  href: '/' },
    { key: 'About', text: '{{ about | polyglot }}', href: '/about' },
    { key: 'Docs',  text: '{{ docs | polyglot }}',  href: '/docs' }
  ]
}

// — OR, if you need named children (not a state-driven list) —
export const Nav = {
  childExtends: 'NavLink',                      // every direct child auto-inherits NavLink
  Home:  { href: '/',      text: '{{ home | polyglot }}' },
  About: { href: '/about', text: '{{ about | polyglot }}' },
  Docs:  { href: '/docs',  text: '{{ docs | polyglot }}' }
}
```

### ✅ Correct — `childProps` for per-instance shared overrides

```js
// All buttons inside a footer get the same theme + size, but each has its own key
export const FooterActions = {
  flow: 'x', gap: 'A',
  childProps: { theme: 'subtle', fontSize: 'Z' },
  Cta:    { extends: 'Button', text: '{{ get_started | polyglot }}' },
  Cancel: { extends: 'Button', text: '{{ cancel | polyglot }}' }
}
```

### Reuse decision tree

```
Is this shape / cluster used more than once?
├── No  → keep inline (single use)
└── Yes →
    ├── Same component, multiple call sites? → extract to components/<Name>.js
    │       └── Reference by key (auto-extend by naming `Name: {...}`)
    │       └── Multiple instances at the same level → `Name_1`, `Name_2` (auto-extend `Name`)
    │       └── ❌ NEVER `Wrap: { extends: 'Name' }` if Wrap carries no extra meaning — just rename the key to `Name`
    ├── List of similar children?            → `childExtends: 'Name'`
    │       └── Data-driven? → use `childrenAs: 'state'` (preferred for reusability — child decouples from parent state shape)
    │       └── Single-use, narrow-scope?   → `state: 'key'` is also valid (binds to a parent-state subtree)
    ├── Per-child uniform overrides?         → `childProps: { ... }`
    └── Variation between siblings?          → extract base + extend with overrides per call site
```

> `childrenAs: 'state'` vs `state: 'key'`: both are valid. **Prefer `childrenAs: 'state'` for reusable child components** — the child reads its own `s.field` and isn't coupled to a specific parent-state shape, so the same component works across any list whose items match what it consumes. Use `state: 'key'` only when the child is one-off bound to a specific parent-state subtree (Rule 36).

### Audit checks

- Grep for repeated PascalCase blocks with overlapping property sets → candidates for extraction
- Grep for inline `childExtends: { ... }` (object form) → must be a quoted string referencing a registered component (Rule 10 + FRAMEWORK.md §2)
- Look for any `Foo: { extends: 'Bar', ...sharedProps, X: 1 }` and `Foo2: { extends: 'Bar', ...sharedProps, X: 2 }` → extract `sharedProps` into `Bar` itself, leave only the differing prop at call site
- Look for repeated `padding: 'A B', gap: 'A', borderRadius: 'B'` clusters across files → candidate for a `Card`/`Panel`/`Surface` shared component

### Why strict

- **Frank serialization size** balloons when shapes duplicate; extraction shrinks the published JSON.
- **Update consistency** — fixing a card style means editing one file, not 14.
- **Override predictability** — `extends:` chains compose deterministically (FRAMEWORK.md §2 "extends — string, array, or inline object"). Inline duplication has no inheritance, so global theme tweaks miss the duplicates.
- **Frank serialization breaks** for inline-object `childExtends` (Rule 10) — the only safe form is a quoted string.

---

## Rule 58 — Frank module discovery is fixed; only the standard slots are loadable

Frank discovers project code ONLY via these slots:

```
state.js
dependencies.js
sharedLibraries.js
config.js
designSystem/index.js
components/index.js
pages/index.js
functions/index.js
methods/index.js
snippets/index.js
files/index.js
```

Files outside this list — `lib/`, `helpers/`, `utils/`, `services/`, `models/`, `hooks/`, etc. — are **INVISIBLE to frank** and therefore stripped from any published JSON. Move loadable code into one of the standard slots, OR re-export it through one of the index files (e.g. `functions/index.js` re-exporting from `functions/helpers/foo.js` works because the bundler picks up the import).

```
// ❌ Invisible to frank — stripped on publish
symbols/lib/format.js          // NEVER discovered
symbols/helpers/api.js         // NEVER discovered
symbols/services/auth.js       // NEVER discovered

// ✅ Inside the standard slots
symbols/functions/format.js
symbols/methods/api.js
symbols/functions/index.js → export * from './format.js'
```

---

## Rule 59 — Never ship `db.createClient` in `config.js` / `context.db`

The supabase adapter (`plugins/fetch/adapters/supabase.js:16-19`) dynamic-imports `@supabase/supabase-js` at runtime when no `createClient` is provided. Mermaid's bundle script (`mermaid/src/bundle.js:65-66`) explicitly strips `createClient` from the published JSON because functions don't survive frank serialization.

Result: passing `createClient` does nothing in production — the adapter rebuilds it via dynamic import.

```js
// ❌ Wrong — `createClient` is stripped on publish; works only locally
import { createClient } from '@supabase/supabase-js'
db: { adapter: 'supabase', createClient, url: '…', key: '…' }

// ✅ Correct — let the runtime adapter resolve `@supabase/supabase-js` via importmap
db: { adapter: 'supabase', url: 'https://xxx.supabase.co', key: 'sb_publishable_…' }

// dependencies.js
export default {
  '@supabase/supabase-js': 'latest'   // exact version pinning recommended for production
}
```

---

## Rule 60 — Async boundaries lose the active scratch CONFIG — capture context up front

The framework's `pushConfig`/`popConfig` stack scopes `getActiveConfig()` to the right design system in multi-app pages. The framework wraps event handlers, lifecycle hooks, and `onFrame` ticks. It does NOT wrap project-scheduled work via `setTimeout` / `setInterval` / `queueMicrotask` / `Promise.resolve().then` / web-worker postMessage callbacks — those create fresh call stacks with no active config.

Symptom in multi-app pages: CSS-var resolution returns the primary's tokens instead of the secondary's. Theme reads return `'auto'` instead of the app's actual `globalTheme`. Atomic-class generation uses the wrong prefix.

```js
// ❌ Timer callback loses config scope
onClick: (e, el) => {
  setTimeout(() => {
    el.call('refreshSomething')   // getActiveConfig() returns the global singleton
  }, 100)
}

// ✅ Capture context up front; access the design system, document, window through it
onClick: (e, el) => {
  const ctx = el.context
  setTimeout(() => {
    // ctx.designSystem, ctx.document, ctx.window are stable references across async boundaries
    el.call('refreshSomething', ctx)
  }, 100)
}
```

Also applies to: `MutationObserver` callbacks, `IntersectionObserver` callbacks, `ResizeObserver` callbacks, `WebSocket` `onmessage`, `EventSource` `onmessage`, `BroadcastChannel` listeners — all run in fresh call stacks.

---

## Rule 57 — Shared-package components looked up only via DOMQL string-key need `sideEffects: true`

When a component lives in a shared package and is referenced ONLY by DOMQL string-key lookup at runtime (e.g. `AppAssistant: {}` at the app root), Parcel's tree-shaker can't prove the export is used and strips it. Symptom: an empty `<div data-key="Foo"></div>` with no class names, no children, no merged props.

Put a `package.json` at the root of the shared package directory with `"sideEffects": true`:

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

After adding, do a full Parcel restart on every downstream app (`rm -rf .parcel-cache dist` then respawn portless) so the module graph re-analyzes under the new flag.

**Defense-in-depth for overlays:** even with `sideEffects: true`, a registry-resolution failure leaves an overlay element in the DOM as an empty shell that can fall into normal grid flow. Inline the positioning props at the consumer site (in the app's own `app.js` object literal) so positioning survives even if the shared component fails to merge:

```js
AppAssistant: {
  position: 'fixed',
  top: '0', right: '0',
  height: '100dvh',
  zIndex: '10000'
}
```

---

## Rule 62 — STRICT: `html: '<svg ...>'` for icons is BANNED — ALWAYS use the `Icon` component

This is the strictest, most enforced corollary of Rule 29. **Inline SVG via `html: '<svg ...>'` to render an icon is FORBIDDEN.** Every icon — without exception — must be stored in `designSystem/icons` and rendered through the `Icon` component by name.

**Why this is a critical violation:**

- Inline SVG bypasses the design system — `currentColor` / theme color resolution silently breaks because the SVG is not threaded through `Icon`'s color-prop pipeline.
- Brender SSR cannot hydrate an inline `html:` SVG correctly; the published output will mismatch the local dev render (the #1 publish-time failure on Symbols projects).
- The icon sprite (`useIconSprite: true`) cannot dedupe / reference the symbol — every page ships the full SVG markup.
- Theme-aware swaps (e.g. `@dark` icon variants) fail because the inline html string is static, not selectable per theme.
- Audit tooling, design-direction enforcement, and migration scripts cannot find or rewrite icons stored as inline html.

**Forbidden patterns (every one of these is a Rule 62 critical finding):**

```js
// ❌ html: '<svg ...>'
Logo: { html: '<svg viewBox="0 0 24 24"><path d="M5 5h10"/></svg>' }

// ❌ tag: 'svg' inline component
LogoSvg: { tag: 'svg', attr: { viewBox: '0 0 24 24' }, Path: { tag: 'path', attr: { d: '...' } } }

// ❌ extends: 'Svg' with html: SVG markup
Logo: { extends: 'Svg', html: '<path d="..."/>' }

// ❌ tag: 'path' / 'circle' / 'rect' inline
Path: { tag: 'path', attr: { d: '...' } }
```

**The ONLY correct pattern:**

```js
// designSystem/icons.js
export default {
  brandLogo: '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M5.47...Z"/></svg>',
  close:     '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>'
}

// component
Logo:     { extends: 'Icon', icon: 'brandLogo' }
CloseBtn: { extends: 'Icon', icon: 'close' }
```

**Note on `Svg`:** the `Svg` element is reserved for non-icon decorative/illustration backgrounds. It is NEVER acceptable for icons. If you find yourself reaching for `extends: 'Svg'` to render an icon, stop — register the icon in `designSystem/icons` and use `Icon` instead.

---

## Rule 63 — STRICT: NO DUPLICATES — search all 3 tiers before defining ANY component or function

**This is a P0 rule. Defining a component or function whose name already exists somewhere in scope is a critical violation, even when "the existing one looks slightly different".** DOMQL resolves bare keys through merged context (built-ins → shared libraries → project), and registered functions are looked up the same way. Re-declaring a name that already exists silently shadows the original and breaks every other consumer that expected the canonical version.

### The mandatory pre-write checklist

Before writing `export const <Name> = {…}` for a component, OR `export function <name>` / `export const <name> = …` for a function, you MUST confirm — in this order — that NO entry with that name already exists:

1. **Tier 1 — Framework built-ins** (`@symbo.ls/default-config`).
   - Atoms: `Block`, `Box`, `Flex`, `Grid`, `Hgroup`, `Img`, `Picture`, `Video`, `Iframe`, `Text`, `Form`, `Svg`, `Shape`, `Theme`, `InteractiveComponent`.
   - Components: `Avatar`, `Button`, `Dialog`, `Dropdown`, `Link`, `Notification`, `Range`, `Select`, `Tooltip`, `Icon`, `Input`.
   - If your name collides — STOP. Use the built-in via bare key (`Avatar: { src: '…' }`).

2. **Tier 2 — Shared libraries** declared in `sharedLibraries.js` at the project root.
   - Inspect `sharedLibraries.js` and `symbols.json` (`sharedLibrariesMode`) to know whether libraries resolve into `node_modules/<pkg>/` (`npm` mode) or `.symbols_local/libs/<owner>/<key>/` (`local` mode), or a custom `destDir`.
   - Grep every resolved library path:
     ```sh
     # npm mode
     grep -rEn '^export const [A-Z][A-Za-z0-9_]* ' node_modules/<pkg>/components/ node_modules/<pkg>/snippets/ 2>/dev/null
     grep -rEn '^export (const|function) [a-z]'    node_modules/<pkg>/functions/  node_modules/<pkg>/methods/   2>/dev/null
     # local mode
     grep -rEn '^export const [A-Z][A-Za-z0-9_]* ' .symbols_local/libs/*/*/components/ .symbols_local/libs/*/*/snippets/ 2>/dev/null
     grep -rEn '^export (const|function) [a-z]'    .symbols_local/libs/*/*/functions/  .symbols_local/libs/*/*/methods/   2>/dev/null
     ```
   - If your name collides — STOP. Reuse via bare key, or `extends: 'Name'` in your local file to override specific props (Rule 46 — never edit the library source).

3. **Tier 3 — Current project** — `components/`, `pages/`, `snippets/`, `functions/`, `methods/`.
   ```sh
   grep -rEn '^export const [A-Z][A-Za-z0-9_]* ' components/ pages/ snippets/ 2>/dev/null
   grep -rEn '^export (const|function) [a-z]'    functions/  methods/                 2>/dev/null
   ```
   - If your name collides — STOP. Either reuse the existing definition, or rename the new one to express its distinct purpose.

You may also use `mcp__symbols-mcp__search_symbols_docs(query)` for semantic search across the bundled catalog. **Skipping this checklist is the violation, even if the duplicate ships and "works".**

### The four resolutions when a name collides

| Situation | Action |
| -- | -- |
| The existing entry covers your case | Reuse it via bare key (`Card: { … }`) or `el.call('fn', …)` — do NOT redefine |
| The existing entry covers ~80% but you need different visuals/behavior | `extends: 'Card'` (or wrap the function) in YOUR file with the diff — do NOT copy the source |
| The existing entry is genuinely the wrong shape for your need | **Rename** your new component/function — do NOT shadow |
| You truly intend to override a shared-library entry project-wide | Define the same key in your local project (local always wins on collision) — make this an explicit, documented decision, not an accidental shadow |

### ❌ Forbidden — duplicate names

```js
// ❌ Avatar exists in @symbo.ls/default-config — redefining loses theme/SSR/sprite/a11y wiring
export const Avatar = { tag: 'div', borderRadius: 'A', Img: { /* … */ } }

// ❌ Card exists in shared library `system/default` — accidental shadow shadows every consumer
// (no project-wide decision was made; the author just didn't grep)
export const Card = { padding: 'C', background: 'surface' }

// ❌ formatDate already exists in functions/formatDate.js — duplicate file, divergent logic
// functions/formatTime.js
export const formatDate = (d) => new Date(d).toLocaleString()

// ❌ Two near-duplicates with cosmetic naming differences
export const UserCard    = { /* same shape */ }
export const MemberCard  = { /* same shape */ }
export const ProfileCard = { /* same shape */ }
```

### ✅ Correct — reuse, extend, or rename

```js
// ✅ Reuse the built-in by bare key
Avatar: { src: 'me.jpg' }

// ✅ Extend the shared-library Card to customize for this project (Rule 46)
//    components/Card.js — local override
export const Card = {
  extends: 'Card',          // pulls in the shared-library Card as the base
  borderRadius: 'C',        // your project tweak
  background: 'brand'
}

// ✅ Reuse the registered function via el.call
text: (el, s) => el.call('formatDate', s.createdAt)

// ✅ Extract the shared shape, rename instances per usage
//    components/PersonCard.js
export const PersonCard = { /* canonical shape */ }
//    pages/Team.js
PersonCard_1: { /* member-specific overrides */ }
PersonCard_2: { /* profile-specific overrides */ }
```

### Why strict

- **Silent shadowing.** Built-ins / shared-library entries collide with local re-definitions silently — no error. Bugs surface weeks later as "the avatar lost its theme styling" or "this function returns the wrong shape on prod". Almost always traced back to an undeclared name collision.
- **Frank serialization divergence.** A redefined component drops the canonical version's wiring (theme, sprite, SSR, a11y); the local dev render looks fine, the deployed payload doesn't.
- **Update propagation breaks.** When the shared-library version updates upstream, every consumer benefits — except the one that quietly redefined the name.
- **Cognitive load.** Three near-duplicates (`UserCard`, `MemberCard`, `ProfileCard`) means three drift trajectories; one canonical `PersonCard` means one.

### Audit checks

- Cross-grep tier-3 component/function names against tier-1 catalog and tier-2 library paths — any match that isn't an intentional override is a Rule 63 violation.
- For functions, also check that `el.call('name', …)` resolves to the intended definition (DOMQL's function registry merges across tiers the same way).
- Treat any new file whose `export const X` matches an existing name as a P1 fix, not a "TODO later".

---

## Rule 64 — STRICT: NEVER assign to `window` / `globalThis` / `document` — no globals, period

**Writing anything to `window`, `globalThis`, or `document` from project code is BANNED.** This is a P0 rule with zero exceptions for "convenience", "debugging", "passing data between components", or "exposing for devtools". The framework already gives you four reactive, scoped, garbage-collected channels — use them. Globals are silent bugs disguised as shortcuts.

**Banned patterns — every one of these is a Rule 64 violation:**

```js
// ❌ Stashing app/element references on window
onInit: (el) => { window.smblsApp     = el.getRoot() }
onInit: (el) => { window.__rootEl     = el }
onInit: (el) => { window.app          = el }

// ❌ Cross-component context sharing through window
onClick: (e, el, s) => { window.activeProject = s.project }
onInit:  (el)       => { const p = window.activeProject; … }

// ❌ Assigning helpers / functions to window for "easy access"
onInit: (el) => { window.refreshUser = () => el.call('refreshUser') }
onInit: (el) => { window.openModal   = (id) => el.getRootState().update({ modal: id }) }

// ❌ Module-side-effect bridges (also FA514 — stripped by frank, breaks in prod)
window.__projectInit = initFunction
window.__myBus       = new EventTarget()

// ❌ Document-level writes
document.title                = s.project.name      // use `metadata:` / @symbo.ls/helmet (Rule 49)
document.body.dataset.theme   = 'dark'              // use `changeGlobalTheme()` (Rule 50)
document.documentElement.style.setProperty('--x',v) // use `vars: { '--x': v }` or design-system tokens
document.cookie               = '…'                 // wrap in a `functions/` helper, never inline
document.body.classList.add('open')                 // `class: { open: (el, s) => s.isOpen }`

// ❌ globalThis is just window with extra steps
globalThis.smblsApp = el.getRoot()
```

### Why this is strict — five concrete failure modes

1. **Not reactive.** smbls is signal-based; `window.foo = x` does not trigger a re-render. Components reading `window.foo` will silently render stale data forever.
2. **Cross-app contamination.** Canvas, workspace, and preview all load in the same Chrome tab during dev — `window.foo` written by one app leaks into every other. Production embeds (iframes, multi-tenant pages) hit the same trap.
3. **GC leaks.** A reference held on `window` is alive forever. Mounting and unmounting your app (canvas re-init, hot reload, route swap) keeps every previous element tree alive — memory grows until the tab dies.
4. **Frank-serialization divergence.** `window.__projectInit = …` and similar module-side-effect bridges are STRIPPED at publish (FA513/FA514). Your local dev works; the deployed payload silently does nothing.
5. **Implicit, undocumented contracts.** Any reader of `window.X` creates an invisible contract. Renaming, refactoring, or removing the writer breaks consumers nobody can grep for.

### Use these instead — element tree traversal + the four canonical channels

DOMQL gives you everything `window` would tempt you to use. Pick by scope and reactivity:

| Need | Use |
| -- | -- |
| Walk to a parent / ancestor by key | `el.lookup('KeyName')` (Rule 40) |
| Find a child / descendant by key | `el.lookdown('KeyName')` / `el.lookdownAll('KeyName')` |
| Reach the root element | `el.getRoot()` |
| Read / write app-wide reactive state | `el.getRootState()` + `s.root.X` reads / `el.getRootState().update({ X: … })` writes |
| Component-local reactive state | `state: { … }` + `s.update({ … })` |
| Per-instance NON-reactive storage (timers, library refs, debounce handles) | `el.scope.X = …` in `onInit`, clean up in `onRemove` |
| Boot-time config / registered functions | `context` (passed to `create(app, context)`) — read-only at runtime |
| Call a registered project function | `el.call('fnName', …args)` — never `window.fnName` |
| Navigate | `el.router(path, el.getRoot())` (Rule 42) |
| Set page title / meta | `metadata: { … }` via @symbo.ls/helmet (Rule 49) |
| Switch theme | `changeGlobalTheme()` from `smbls` (Rule 50) |
| Set CSS vars / styles | `vars: { '--x': v }` or design-system tokens (Rule 30) |
| Toggle classes | `class: { open: (el, s) => s.isOpen }` |
| React to scroll / resize / visibility | `onScroll:` / `onResize:` lifecycle props on the element |
| Genuine browser events (`beforeunload`, `hashchange`, `storage`) | flat `onWindowBeforeunload:` / `onWindowHashChange:` / `onWindowStorage:` on the owning component — DOMQL registers once, tears down on dispose (no `el.scope` cleanup, no `onRemove` bookkeeping); document-level (outside-click, foreign portals) → `onDocumentClick:` etc. — read-only listeners only, never assignments |

### ✅ Correct — every banned case rewritten

```js
// ✅ Cross-component data → root state (reactive, scoped to the app)
//    state.js
state: { activeProject: null }
//    setter
onClick: (e, el, s) => el.getRootState().update({ activeProject: s.project })
//    reader
text: (el, s) => s.root.activeProject?.name || '{{ noProject | polyglot }}'

// ✅ Per-instance non-reactive storage → el.scope
onInit:   (el) => { el.scope.timer = null },
onInput:  (e, el, s) => {
  clearTimeout(el.scope.timer)
  el.scope.timer = setTimeout(() => s.update({ q: e.target.value }), 200)
},
onRemove: (el) => { clearTimeout(el.scope.timer) }

// ✅ Calling a project function → el.call (never window.fn)
onClick: (e, el, s) => el.call('refreshUser', s)

// ✅ Reaching another part of the tree → element tree traversal
onClick: (e, el) => el.lookup('AppShell').lookdown('Sidebar').toggle()

// ✅ Page title → metadata: prop
metadata: { title: (el, s) => s.project.name }

// ✅ Theme swap → framework API
import { changeGlobalTheme } from 'smbls'
onClick: () => changeGlobalTheme('dark')
```

### The two narrow read-only exceptions (NOT assignments)

- **`window.location` reads** (`window.location.pathname`, `.hash`, `.search`) are tolerated for inspection — but for navigation, ALWAYS `el.router(path, el.getRoot())` (Rule 42). Never `window.location.href = '/x'`.
- **Window/document-level listeners** for genuine browser events (`resize`, `beforeunload`, `hashchange`, `storage`) and for events that never reach an element you own (foreign portals, outside-click, Escape) — declare the flat `onWindowXxx:` / `onDocumentXxx:` prop on the owning component (framework-owned: registered once, inert while `if:`-hidden, torn down on dispose). Prefer node-level `onResize:` / `onScroll:` when the event reaches the element. Raw `window.addEventListener` / `document.addEventListener` from project code is FA503 — there is no longer a case it is needed for. **Listeners are reads, not writes.**

Anything else — including formal devtools hooks (`__REDUX_DEVTOOLS_EXTENSION__`, `__SMBLS_DEVTOOLS_GLOBAL_HOOK__`) — must be added at the framework level, not from a project. If you need a hook that doesn't exist, open a ticket in `FRAMEWORK_TICKETS.md` (per the no-hacks policy in Rule 55) — never add a project-side `window.__X = …` shim.

### Audit checks

- Grep your project for `window.`, `globalThis.`, `document.title`, `document.body`, `document.documentElement`, `document.cookie`, `document.createElement`, `document.querySelector`, `document.getElementById` — every match outside the two read-only exceptions is a Rule 64 violation.
- For each violation, identify which canonical channel replaces it (state, scope, root state, context, `el.call`, `el.lookup` / `el.lookdown`, `metadata:`, `vars:`, `class:`, `onScroll:` / `onResize:`, `onDocumentXxx:` / `onWindowXxx:`, `el.router`).
- A `window.X = …` write is ALWAYS a P0 fix — not a "TODO later". Silent global writes are the highest-rework class of bug in Symbols projects.

**Auto-fix protocol:** when an audit finds an `html: '<svg...>'` icon, the fix is always:
1. Lift the SVG markup into `designSystem/icons.js` under a clear semantic name
2. Replace the offending component body with `{ extends: 'Icon', icon: '<name>' }`
3. Re-run the audit to confirm zero Rule 62 findings

This rule is enforced by:
- `bin/symbols-audit` (regex sweep, severity `critical`, category `icons`)
- `mcp__symbols-mcp__audit_component` (in-text rule check)
- Generation tools (`generate_component`, `generate_page`) — output prompts forbid inline SVG for icons

---

## Rule 65 — STRICT: interaction states are DECLARED on the primitive, never left to the call site

**Every interactive element MUST declare `:hover`, `:active`, `:focus-visible` and — where applicable — `:disabled`, on the component that defines it.** A control that only has a resting style is a bug, not a minimal design.

Set them ONCE on the primitive (`Button`, or your project's `PrimaryBtn` / `GhostBtn` / row / tile) and let every call site inherit. Re-declaring states per instance is how an app ends up with 40 buttons that each behave differently.

```js
// ✅ Declared once, on the primitive
export const PrimaryBtn = {
  extends: 'Button',
  background: 'brand',
  cursor: 'pointer',
  ':hover': { background: 'brand+10' },
  ':active': { background: 'brand-10' },
  ':focus-visible': { outline: '2px solid currentColor', outlineOffset: '2px' },
  ':disabled': { opacity: '0.35', pointerEvents: 'none' }
}

// ❌ Resting style only — the control never acknowledges the pointer
export const PrimaryBtn = { extends: 'Button', background: 'brand', cursor: 'pointer' }
```

**Hover must change the FILL, not the opacity.** `:hover': { opacity: '0.85' }` fades the label along with the surface, so the control gets *harder* to read exactly when the user is aiming at it. Step the background token instead.

**A hover step must be perceptible.** Two tokens one step apart on a tinted surface can differ by less than the eye resolves. If you cannot see it in the browser, it is not a state — measure the composited luminance delta of the two, and treat anything under ~0.02 as no change at all.

---

## Rule 66 — STRICT: never let chrome change the page's LAYOUT — reserve the box or overlay it

**A control, banner, count, or panel appearing MUST NOT move anything already on screen.** Layout shift is the single most-reported UI defect in review; treat it as a correctness bug, not polish.

Three patterns cause almost all of it:

**1. `if:`-gated chrome inside a flow.** An `if:` gate ADDS and REMOVES the node, so its neighbours move. If the element is chrome (a Clear button, a result count, a status line), keep it mounted and toggle visibility instead — and disable it while hidden so it is neither clickable nor focusable:

```js
// ❌ enters the row on the first keystroke and shoves its neighbours
ClearBtn: { if: (el, s) => !!s.root.query, text: 'Clear' }

// ✅ box reserved; only visibility changes
ClearBtn: {
  text: 'Clear',
  visibility: (el, s) => (s.root.query ? 'visible' : 'hidden'),
  pointerEvents: (el, s) => (s.root.query ? 'auto' : 'none'),
  tabindex: (el, s) => (s.root.query ? '0' : '-1'),
  aria: { hidden: (el, s) => (s.root.query ? null : 'true') }
}
```

This also REPAIRS `role="status"` regions: a live region must exist in the DOM *before* its content changes, so an `if:` gate silently defeats the announcement it was written for.

**2. A label that changes width.** `'Save'` → `'Saving…'` resizes the control mid-action, exactly while the user is looking at it. Give it a `minWidth` floor sized to the LONGER label.

**3. A result panel rendered inline above existing content.** An explanation, preview, or editor that opens *in* the flow pushes everything below it down and yanks it back on close. If it is a read-then-dismiss artifact, it belongs on an overlay (fixed panel + backdrop, dismissable by backdrop click AND Escape) — not in the document flow.

**Verify it, don't assume it.** Snapshot the geometry of the SAME element references before and after the change and count how many moved; a `PerformanceObserver` on `layout-shift` confirms it independently. Comparing positions by ARRAY INDEX is invalid — an inserted node shifts every later index and reports a shift that did not happen.

---

## Rule 67 — STRICT: never use a raw theme-invariant colour for a state — mirror it with `light-dark()`

**A hard-coded `rgba(255,255,255,…)` or `rgba(0,0,0,…)` wash is correct on exactly ONE theme and wrong on the other.** A white wash is a frosted highlight on a dark shell and invisible on a light one — which inverts the meaning of an active state: the selected item ends up reading *fainter* than its unselected siblings.

```js
// ❌ theme-invariant — white-on-white on the light shell
background: (el, s) => (s.active ? 'rgba(255,255,255,0.1)' : 'transparent')

// ✅ mirrored per theme
background: (el, s) =>
  s.active ? 'light-dark(rgba(20,20,22,0.08), rgba(255,255,255,0.1))' : 'transparent'
```

The same trap applies to fixed theme TOKENS used on a coloured surface. `overlay` is a fixed low-alpha wash: on a surface of similar lightness it composites to the surface colour and vanishes — a field with no visible fill, a hover that never appears. On a tinted/branded surface use a tint of `currentColor`, which adapts to whatever ink that surface carries:

```js
style: { background: 'color-mix(in srgb, currentColor 12%, transparent)' }
```

**Bind a state value ONCE** as a named constant (or a token) and reference it everywhere, rather than repeating the literal. Copies drift; a binding cannot.

---

## Rule 68 — STRICT: never override a control's padding at the call site

**The control scale belongs to the primitive.** Overriding `padding` on an instance to make a button "smaller" in a dense row silently breaks its geometry.

Why it fails, specifically: primitives set `minHeight` for the tap target, which means the VERTICAL padding value is inert — the box keeps its height no matter what you pass. Your override therefore only ever shrinks the HORIZONTAL inset. The result is a control with generous room above and below the label and almost none at the ends: visibly lopsided, and the exact complaint that reaches you as "the button looks unbalanced".

```js
// ❌ only the horizontal inset actually changes — the label ends up ~4px from each end
BfGhostBtn: { padding: 'V X', text: 'Save assessment' }

// ✅ inherit the scale
BfGhostBtn: { text: 'Save assessment' }
```

If a genuinely denser control is needed, define a compact VARIANT on the primitive (its own `minHeight` + `padding` pair) and extend that. One named variant beats N ad-hoc overrides — and when the scale changes, every consumer moves together.

Compact SPANS (pills, badges, hint chips) are not controls: they carry no `minHeight` and no tap-target obligation, so a small padding pair on them is the intended scale, not an override.

---

## Rule 69 — CROSS-THEMED projects: prefer a THEME, then a SEMANTIC PAIR; a raw hue is not semantic

**Scope: this rule applies only to projects that render in more than one theme**
(a `globalTheme: 'auto'` config, a theme toggle, or an app embedded in a shell
that pushes `?globalTheme=`). A project pinned to a single theme has no second
ground to fail on — a raw hue is fine there, and this rule does not apply.

**A semantic colour is one that has a `[light, dark]` pairing in the design
system.** That is the whole test, and it is mechanical: if the token is not an
array pair in `designSystem/color.js`, it is not semantic — no matter how
token-ish the name reads.

```js
// ❌ raw HUE token — looks compliant (it IS a token, not a hex) but it is a
//    SINGLE fixed value with no light/dark pair, so it is exactly as broken
//    as '#E98232'. Correct in the theme it was eyeballed in, dead in the other.
{ color: 'orange' }        // 2.42:1 as ink on a light page wash
{ color: 'red' }           // 2.45:1
{ color: 'white' }         // 1.14:1 on a light board — invisible

// ✅ semantic PAIR — one declaration, adapts by itself, no media query
{ color: 'warningInk' }    // ['orangeDeep', 'orangeBright']
{ color: 'dangerInk' }
{ color: 'title' }         // neutral pair — ['gray1', 'gray15']
```

**Reach for the layers in this order:**

1. **A theme** — `theme: 'primary'`, `theme: 'common-card'`, `theme: 'success'`.
   A theme bundles background + ink + hover/focus/active and flips as a unit, so
   it is the least that can drift. Prefer it whenever you need a SURFACE plus
   its ink (buttons, cards, badges, plates).
2. **A semantic pair token** — `warningInk`, `dangerInk`, `successInk`,
   `accentInk`, `magentaInk`, or a neutral (`title`, `caption`, `subtitle`,
   `paragraph`, `line`, `overlay`, `hover`, `selected`). Use when only the INK
   varies and the ground is already handled.
3. **A raw hue** — decoration ONLY, on a ground you control: plates, dots,
   washes, chart series. Never as text.

**Prefer a pair over `@dark` / `@light` blocks.** A pair is one declaration that
adapts; a media-query block is a manual restatement of the same intent in two
places, and the two drift. Reserve `@dark` / `@light` for things a colour pair
cannot express — swapping an icon, hiding an element, changing a border style.

**Hue-as-text is usually the wrong shape anyway.** Prefer **wash + neutral ink**
(a tinted plate carrying the hue, with `title`/`caption` text on it): it reads
at any size and cannot fail contrast when the ground flips. Reach for a hue ink
only when the hue itself IS the signal and there is no plate.

**Verify in BOTH themes before calling it done.** Measured cost of not doing so
(2026-08-09, symbols workspace): 150 raw-hue `color:` declarations across 12
apps; `/warehouse` in light had its `LOW` badges at 1.91:1 and its expired count
at 2.45:1; the `/` home tile glyphs were hardcoded white at 1.14:1. Every one
had been eyeballed in dark and called correct.

---

## Rule 70 — A lowercase custom prop set to a function is AUTO-INVOKED, not stored — use `el.call` (Rule 8) to stash a callback

**Any lowercase (non-PascalCase) prop whose value is a function is a reactive
factory prop** — the exact same mechanism `text:`, `hide:`, `background:`, and
every other built-in factory prop use. The framework replaces it with a
getter that calls `fn(element, element.state, element.context)` on **every
read** and returns whatever that call returns. This is intentional and is
what makes `text: (el, s) => s.count` work — but it also means a lowercase
prop can never be used to stash a callback you intend to invoke later.

```js
// ❌ WRONG — looks like a stored callback, is actually a reactive factory.
// `el.toData` is auto-invoked and OVERWRITTEN with its return value.
export const Widget = {
  toData: (el, root) => [1, 2, 3],
  onRender: (el, s) => {
    console.log(typeof el.toData)   // 'object' — NOT 'function'
    el.toData(el, s.root)           // TypeError: el.toData is not a function
  }
}

// ✅ RIGHT — register it as a project function and invoke via el.call (Rule 8)
// functions/toData.js
export const toData = function toData(root) {
  return [1, 2, 3]
}

// component
export const Widget = {
  onRender: (el, s) => {
    const data = el.call('toData', s.root)
  }
}
```

**The failure is completely silent at the declaration site** — nothing about
the syntax signals that THIS particular prop name is about to be
auto-invoked-and-replaced rather than left as a stored reference. The only
symptom is a `TypeError` at the first call site, which can be arbitrarily far
(in time and in file) from where the prop was declared. In the field this
surfaced as "all three charts render with zero canvases, no visible console
error" — the throw landed in an unguarded position.

**Dev-only advisory warning:** `wrapCustomPropFunctions`
(`smbls/packages/element/src/create.js`) logs a heuristic, advisory-only
`console.warn` (gated by `isLoudDevRuntime()` — never in production) when a
lowercase custom prop is a 2-argument function whose second parameter isn't
named like the state/context convention (`s` / `state` / `ctx` / `context`) —
the shape of a stashed callback rather than a reactive factory. This is a
heuristic (false positives/negatives are expected) and never changes the
resolved value — it exists only to surface the trap at declaration time
instead of at a downstream `TypeError`.

**Files:** `smbls/packages/element/src/create.js` (`wrapCustomPropFunctions`,
`looksLikeStashedCallback`).
