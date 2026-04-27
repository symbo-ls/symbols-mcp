# Common Mistakes — Wrong vs Correct DOMQL Patterns

This is a zero-tolerance reference. Every pattern in the "Wrong" column is FORBIDDEN. The audit tool catches all of them. There is no concept of "known debt" — every violation must be fixed to 100%.

> DOMQL is signal-based with a flat element API. Nested access patterns (`el.props.X`, `el.on.X`, `props: {}`, `on: {}`, `({ props })` destructuring) are FORBIDDEN. Reactive prop functions are `(el, s)` only.

---

## 0. ⚠️ CRITICAL — Lowercase keys NEVER render (#1 cause of "missing content")

**Lowercase top-level child keys are FILTERED OUT of the child-creation loop entirely** by `packages/element/src/create.js → createChildren` (gates on `firstChar < 65 || firstChar > 90`). So a lowercase key never renders, regardless of whether it happens to match an HTML tag name. This is the #1 root cause of "my content isn't showing up."

```js
// ❌ Lowercase — never renders. Silently invisible.
export const Card = {
  h1:     { text: '{{ heading | polyglot }}' },     // never appears
  nav:    { children: [...] },                       // never appears
  form:   { Input: {...} },                          // never appears
  hgroup: { ... },                                   // never appears
  group:  { ... },                                   // never appears
  div:    { text: '...' }                            // never appears
}

// ✅ PascalCase — always renders. Tag auto-detected from key.
export const Card = {
  H1:     { text: '{{ heading | polyglot }}' },     // <h1>
  Nav:    { children: [...] },                       // <nav>
  Form:   { Input: {...} },                          // <form>
  Hgroup: { ... },                                   // <hgroup>
  // (etc — Article, Section, Aside, Header, Footer, Main all auto-detect)
}
```

**Audit grep:** `grep -nE '^\s+[a-z][a-zA-Z]*:\s*\{' symbols/components/*.js` — every match is a missing-content bug.

---

## 1. Colors — use design system tokens, never hex/rgb

```js
// ❌ WRONG — raw hex values
color: '#202124',  background: '#f1f3f4',  borderColor: '#dadce0'

// ✅ CORRECT — named tokens from designSystem.color
color: 'text',  background: 'headerBg',  borderColor: 'border'
```

---

## 2. CSS — flatten at root level, never use `style: {}` wrapper

```js
// ❌ WRONG — CSS inside style: {} block
FileName: {
  tag: 'input',
  style: { fontSize: '16px', border: 'none', color: '#202124' }
}

// ✅ CORRECT — CSS flat as props
FileName: {
  tag: 'input',
  fontSize: 'A',  border: 'none',  color: 'text'
}
```

---

## 3. Spacing — use design system tokens, never raw px

```js
// ❌ WRONG — raw pixel values
padding: '4px 10px',  height: '30px',  width: '1px',  gap: '4px'

// ✅ CORRECT — spacing tokens
padding: 'X Y',  height: 'B',  borderLeft: '1px solid border',  gap: 'X'
```

---

## 4. Icons — use Icon component + `designSystem/icons`, never inline HTML, never inline SVG (Rule 29 / Rule 62 — CRITICAL)

`html: '<svg ...>'` for icons is **BANNED**. It bypasses the design system, breaks `currentColor` theme resolution, breaks Brender SSR hydration (the #1 publish-time failure), kills sprite deduping, and makes `@dark` icon swaps impossible.

```js
// ❌ BANNED — inline SVG via html: (Rule 62 — critical)
Logo:    { html: '<svg viewBox="0 0 24 24"><path d="M5 5h10"/></svg>' }

// ❌ BANNED — tag: 'svg' inline component
LogoSvg: { tag: 'svg', attr: { viewBox: '0 0 24 24' }, Path: { tag: 'path' } }

// ❌ BANNED — extends: 'Svg' with html: SVG markup (Svg is for backgrounds, NOT icons)
Logo:    { extends: 'Svg', html: '<path d="..."/>' }

// ❌ BANNED — inline HTML strings for "icon-like" content
BtnBold:     { extends: 'ToolbarBtn', html: '<b>B</b>' }
BtnColorRed: { html: '<span style="color:#d93025;font-weight:bold">A</span>' }

// ✅ CORRECT — Icon component referencing designSystem/icons by name
Logo:        { extends: 'Icon', icon: 'brandLogo' }
CloseBtn:    { extends: 'Icon', icon: 'close' }
BtnBold:     { extends: 'ToolbarBtn', Icon: { extends: 'Icon', icon: 'bold', width: 'A', height: 'A' } }
BtnColorRed: { extends: 'ToolbarBtn', color: 'danger', Icon: { extends: 'Icon', icon: 'colorA', width: 'A', height: 'A' } }

// designSystem/icons.js — every SVG, no exceptions, lives here:
export default {
  brandLogo: '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M5.47...Z"/></svg>',
  close:     '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>',
  bold:      '<svg width="24" height="24" viewBox="0 0 24 24"><path d="..."/></svg>',
  colorA:    '<svg width="24" height="24" viewBox="0 0 24 24"><path d="..."/></svg>'
}
```

**Auto-fix when you find an inline SVG:** lift the markup into `designSystem/icons.js` under a semantic name, replace the offending body with `{ extends: 'Icon', icon: '<name>' }`, re-audit.

---

## 5. Select options — use children + childExtends, never raw HTML

```js
// ❌ WRONG — raw html string of option tags
FontSizeSelect: {
  html: '<option value="12">12</option><option value="13" selected>13</option>...'
}

// ✅ CORRECT — declarative children with state
FontSizeSelect: {
  children: [10, 11, 12, 13, 14, 16, 18, 20, 24, 28, 32].map(sz => ({
    label: String(sz), value: String(sz)
  })),
  childrenAs: 'state',
  childExtends: 'FontSizeOption',
}
```

---

## 6. Grids/tables — declarative DOMQL, never `document.createElement`

```js
// ❌ WRONG — imperative DOM building
GridWrapper: {
  onRender: (el) => {
    const table = document.createElement('table')
    const th = document.createElement('th')
    th.textContent = colLabel(c)
    headRow.appendChild(th)
    // ... hundreds of lines of imperative DOM
    document.getElementById(`cell-${r}-${c}`)?.querySelector('input')?.focus()
  }
}

// ✅ CORRECT — fully declarative DOMQL
BodyRows: {
  children: (el) => {
    const rs = el.getRootState()
    return rs.grid.map((row, r) => ({ cells: row.map((v, c) => ({ v, r, c })) }))
  },
  childrenAs: 'state',
  childExtends: 'SpreadsheetRow',
}

SpreadsheetCell: {
  CellInput: {
    value: (el, s) => s.v,
    onFocus: (e, el, s) => el.call('selectCell', { r: s.r, c: s.c }),
  }
}
```

---

## 7. Dynamic text — reactive `text:` prop, never polling with `el.node.textContent`

```js
// ❌ WRONG — setInterval polling with el.node.textContent
CellLabel: {
  onRender: (el) => {
    setInterval(() => {
      el.node.textContent = colLabel(rs.sel.c) + (rs.sel.r + 1)
    }, 50)
  }
}

// ✅ CORRECT — reactive text prop
CellLabel: {
  text: (el) => {
    const rs = el.getRootState()
    return rs ? el.call('colLabel', rs.sel.c) + (rs.sel.r + 1) : 'A1'
  }
}
```

---

## 8. Input value — reactive `value:` prop, never polling with `el.node.value`

```js
// ❌ WRONG — setInterval writing el.node.value
FormulaInput: {
  onRender: (el) => {
    setInterval(() => {
      if (document.activeElement !== el.node) return
      el.node.value = rs.formulaBarValue
    }, 60)
  }
}

// ✅ CORRECT — reactive value prop
FormulaInput: {
  value: (el) => el.getRootState()?.formulaBarValue || '',
}
```

---

## 9. State — use `s` directly with `childrenAs: 'state'`, never `el.parent.state`

```js
// ❌ WRONG — parent state traversal
value: (el) => el.parent.state.v,
onFocus: (e, el) => el.call('selectCell', { r: el.parent.state.r, c: el.parent.state.c })

// ✅ CORRECT — s inherited automatically via childrenAs: 'state'
value: (el, s) => s.v,
onFocus: (e, el, s) => el.call('selectCell', { r: s.r, c: s.c })
```

---

## 9b. Prefer `childrenAs: 'state'` over `state: 'key'` when the child should be reusable

`state: 'key'` (narrow scope by binding to a parent-state subtree) is **valid** — not a violation. But for **reusability**, `childrenAs: 'state'` is the preferred form. The child reads its own `s.field` without coupling to a specific parent-state shape, so the same component works across any list whose items match the shape it consumes.

```js
// ✅ Preferred for reusability — TeamItem is decoupled from parent state shape
export const TeamList = {
  state: { members: [] },
  childExtends: 'TeamItem',
  children:     (el, s) => s.members,
  childrenAs:   'state'
}
export const TeamItem = {
  Title: { text: (el, s) => s.name }       // works for any `{ name, ... }` list
}

// ✅ Also valid — `state: 'key'` narrows scope; pick this when the child won't be reused
//   elsewhere AND you want the parent's state subtree to BE the child's state directly.
export const TeamList = {
  state: 'members',
  children: (el, s) => s,
  childExtends: 'TeamItem'
}
export const TeamItem = {
  state: true,                              // required: opt into receiving the narrowed state
  Title: { text: (el, s) => s.name }
}
```

Rule of thumb: if `TeamItem` could be useful inside `MemberList`, `BoardMembers`, or `ContributorList` too — use `childrenAs: 'state'`. If it's a one-off bound to this exact list's exact shape — either form works; use `state: 'key'` if you prefer narrower scope.

---

## 10. Event handlers — correct signature for root vs local state

```js
// ❌ WRONG — s is local state, not root — breaks for global updates
onInput: (e, el, s) => s.update({ filename: e.target.value })

// ✅ CORRECT — el.getRootState() for global state, s for local inherited state
onInput: (e, el) => el.getRootState().update({ filename: e.target.value })
onBlur: (e, el, s) => el.call('commitEdit', { r: s.r, c: s.c, val: e.target.value })
```

---

## 11. Rich text — DOMQL children with tokens, never inline `style=`

```js
// ❌ WRONG — html string with inline style
PoweredBy: { html: 'Built with <strong style="color:#1a73e8">Symbols</strong>' }

// ✅ CORRECT — DOMQL children with token colors
PoweredBy: {
  flow: 'x',
  gap: 'X',
  Prefix: { text: 'Built with' },
  Sym: { tag: 'strong', color: 'accent', text: 'Symbols' },
  Ver: { tag: 'span', text: ' · smbls@latest' },
}
```

---

## 12. Token alignment — aligned elements must share `fontSize`

Spacing tokens are em-based. Mixed `fontSize` on siblings causes the same token to resolve to different px values.

```js
// ❌ WRONG — mixed fontSize, E resolves differently
ColHeaderCell: { fontSize: 'Z1', width: 'E', ... }
SpreadsheetCell: { fontSize: 'Z2', width: 'E', ... }  // wider than header!

// ✅ CORRECT — all grid elements share the same fontSize
ColHeaderCell:   { fontSize: 'Z1', width: 'E', ... }
SpreadsheetCell: { fontSize: 'Z1', width: 'E', ... }
RowNumberCell:   { fontSize: 'Z1', width: 'C', ... }
CornerCell:      { fontSize: 'Z1', width: 'C', ... }
```

---

## 13. Design system keys — ALWAYS lowercase, never UPPERCASE

```js
// ❌ WRONG — UPPERCASE keys are deprecated and banned
import { TYPOGRAPHY, SPACING } from '@symbo.ls/scratch'
const { COLOR, THEME } = context.designSystem
set({ COLOR: { blue: '#00f' }, TYPOGRAPHY: { base: 16 } })

// ✅ CORRECT — lowercase keys only
import { typography, spacing } from '@symbo.ls/scratch'
const { color, theme } = context.designSystem
set({ color: { blue: '#00f' }, typography: { base: 16 } })
```

---

## 14. Navigation — use `el.router()` with root element, never `window.location`

```js
// ❌ WRONG — bypasses SPA routing
onClick: () => { window.location.href = '/' }
onClick: () => { window.location.assign('/dashboard') }

// ❌ WRONG — el is a leaf/button, has no routes — throws "Cannot read properties of undefined"
onClick: (e, el) => el.router('/')
onClick: (e, el) => el.router('/', el)

// ✅ CORRECT — pass root element that holds route map
onClick: (e, el) => el.router('/', el.getRoot())
onClick: (e, el) => el.router('/dashboard', el.getRoot())
```

`el.getRoot()` returns the DOMQL root element which holds the `routes` map. Passing any other element causes a runtime error.

---

## 15. Links — use `extends: 'Link'` with `href` as prop, never `attr: { href }`

```js
// ❌ WRONG — href in attrs
Nav: { extends: 'Link', attr: { href: '/about' } }

// ❌ WRONG — no Link component
Nav: { tag: 'a', attr: { href: '/about' } }

// ✅ CORRECT — Link component with href as prop
Nav: { extends: 'Link', href: '/about', text: 'About' }
```

---

## 16. Animated elements — use `opacity + pointerEvents`, never `show` for transitions

`show: false` sets `display: none`, which cuts CSS transitions instantly. Elements that animate in/out must stay in the DOM.

```js
// ❌ WRONG — show removes element from layout, transitions never fire
Dropdown: {
  show: (el, s) => s.root.open,
  transition: 'opacity 0.2s ease',  // Ignored — element is display:none when closed
}

// ✅ CORRECT — element stays in DOM, transitions work
Dropdown: {
  opacity: (el, s) => s.root.open ? '1' : '0',
  pointerEvents: (el, s) => s.root.open ? 'auto' : 'none',
  transition: 'opacity 0.2s ease, transform 0.2s ease',
  transform: (el, s) => s.root.open ? 'translateY(0)' : 'translateY(-6px)',
}
```

Use `show` only for elements that should be fully removed from layout with no animation. For modals, dropdowns, tooltips, drawers — always use the opacity pattern.

---

## 17. CSS selectors — nest media and pseudo, never chain into one string

```js
// ❌ WRONG — chained selector string
'@dark :hover': { background: 'blue' }
'@mobileL :focus': { outline: 'none' }

// ✅ CORRECT — nested objects
'@dark': { ':hover': { background: 'blue' } }
'@mobileL': { ':focus': { outline: 'none' } }
```

---

## 18. Colors — define once, shade with modifiers, not Tailwind-style palettes

```js
// ❌ WRONG — multiple shade definitions
color: {
  blue50: '#eff6ff', blue100: '#dbeafe', blue200: '#bfdbfe',
  blue300: '#93c5fd', blue400: '#60a5fa', blue500: '#3b82f6',
}

// ✅ CORRECT — single base, use modifiers in components
color: { blue: '#0474f2' }
// Then: 'blue.7' (opacity), 'blue+20' (lighten), 'blue-30' (darken)
```

---

## 19. Flat access — `el.props.X` and `el.on.X` are FORBIDDEN

```js
// ❌ WRONG — nested access (FORBIDDEN)
text: (el, s) => el.props.label
isActive: (el, s) => el.props.src === s.src
onClick: (e, el) => el.on.click(e)

// ❌ WRONG — destructured signature (FORBIDDEN)
text: ({ props }) => props.label
text: ({ state }) => state.label
isActive: ({ key, state }) => state.active === key

// ✅ CORRECT — flat element API
text: (el, s) => el.label                  // (or directly s.label / via state)
isActive: (el, s) => el.src === s.src
onClick: (e, el, s) => s.update({ open: true })

// ✅ CORRECT — reactive prop signature is (el, s) or (el, s, ctx)
text: (el, s) => s.label
isActive: (el, s) => s.active === el.key   // el.key, not destructured key
```

---

## 20. Event handlers — flat top-level only, NEVER `on: {}`

```js
// ❌ WRONG — on: {} wrapper (FORBIDDEN)
{
  on: {
    click: (e, el, s) => s.update({ x: 1 }),
    init:  (el, s) => {},
    render: (el, s) => {}
  }
}

// ✅ CORRECT — flat top-level
{
  onClick: (e, el, s) => s.update({ x: 1 }),
  onInit:  (el, s) => {},
  onRender: (el, s) => {}
}
```

---

## 21. Props — flat on the element, NEVER `props: {}` wrapper

```js
// ❌ WRONG — props wrapper (FORBIDDEN)
export const Button = {
  extends: 'Link',
  props: { color: 'mediumBlue', text: 'Submit' }
}

// ✅ CORRECT — flat
export const Button = {
  extends: 'Link',
  color: 'mediumBlue',
  text: 'Submit'
}
```

---

## 22. Data fetching — declarative `fetch:` prop, NEVER `window.fetch` in components

```js
// ❌ WRONG — raw fetch in component
ArticlesList: {
  state: { articles: [] },
  onRender: async (el, s) => {
    const r = await fetch('/api/articles')
    s.update({ articles: await r.json() })
  }
}

// ❌ WRONG — useEffect-style imperative loading
ArticlesList: {
  onInit: async (el, s) => {
    s.update({ articles: await axios.get('/api/articles').then(r => r.data) })
  }
}

// ✅ CORRECT — declarative fetch (caching, dedup, retry, refetch-on-focus all built in)
ArticlesList: {
  state: 'articles',
  fetch: { from: 'articles', cache: '5m', limit: 20, order: { by: 'created_at', asc: false } },
  children: (el, s) => s,
  childExtends: 'ArticleCard',
  childrenAs: 'state'
}

// ✅ CORRECT — RPC + transform
ContentPage: {
  state: { featured: null, items: [] },
  fetch: {
    method: 'rpc', from: 'get_content_rows', params: { p_table: 'videos' },
    transform: (data) => ({ featured: data.find(v => v.is_featured), items: data.filter(v => !v.is_featured) })
  }
}
```

Configure the adapter once in `config.js`: `db: { adapter: 'supabase'|'rest'|'local', ... }`.

---

## 23. Translations — polyglot only, NEVER hardcoded user-facing strings

```js
// ❌ WRONG — hardcoded English
SearchInput: { placeholder: 'Search destinations' }
WelcomeBanner: { text: 'Welcome to our app' }
Submit: { text: 'Submit' }

// ❌ WRONG — manual ternary on lang (this is what polyglot does for you)
SearchInput: { placeholder: (el, s) => s.root.lang === 'ka' ? 'ძიება' : 'Search' }

// ✅ CORRECT — polyglot template (resolved by replaceLiteralsWithObjectFields, reactive)
SearchInput: { placeholder: '{{ searchDestinations | polyglot }}' }
WelcomeBanner: { text: '{{ welcome | polyglot }}' }
Submit: { text: '{{ submit | polyglot }}' }

// ✅ CORRECT — el.call('polyglot', key) — imperative lookup (NOT reactive)
{ text: (el) => el.call('polyglot', 'hello') }

// ✅ CORRECT — per-language state field (CMS title_en / title_ka)
{ text: '{{ title_ | getLocalStateLang }}' }

// ✅ CORRECT — composed string
{ text: (el, s) => `${el.call('polyglot', 'welcome')}, ${s.user.name}` }

// ⚠️ NOTE: There is no `t` or `tr` function — use `polyglot`. Reactivity comes from
// the `{{ key | polyglot }}` template-literal mechanism, not a separate function.

// ✅ CORRECT — language switcher
{ extends: 'Button', text: 'KA', onClick: (e, el) => el.call('setLang', 'ka') }
```

Configure once in context: `context.polyglot = { defaultLang, languages, translations }` and `context.functions = { ...context.functions, ...polyglotFunctions }`.

---

## 24. SEO metadata — @symbo.ls/helmet only, NEVER `document.title` writes

```js
// ❌ WRONG — direct document.title manipulation
ProductPage: {
  onRender: (el, s) => { document.title = s.product.name }
}

// ❌ WRONG — manual <head> tag injection
SearchPage: {
  onInit: (el) => {
    const meta = document.createElement('meta')
    meta.setAttribute('name', 'description')
    meta.setAttribute('content', 'Search results')
    document.head.appendChild(meta)
  }
}

// ✅ CORRECT — page-level metadata (also works in brender SSR)
export const product = {
  metadata: (el, s) => ({
    title: s.product.name,
    description: s.product.description,
    'og:image': s.product.image
  })
}

// ✅ CORRECT — per-property functions
export const profile = {
  metadata: {
    title: (el, s) => `${s.user.name} — My App`,
    description: (el, s) => s.user.bio,
    'og:image': '/default-avatar.png'
  }
}
```

---

## 25. Theme — `changeGlobalTheme()`, NEVER `data-theme` writes from project code

```js
// ❌ WRONG — bypasses framework theme machinery
ThemeToggle: {
  onClick: () => {
    document.documentElement.setAttribute('data-theme',
      document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark')
  }
}

// ❌ WRONG — reading prefers-color-scheme manually
onInit: (el) => {
  if (matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
}

// ❌ WRONG — storing globalTheme in root state
state: { globalTheme: 'dark' }

// ✅ CORRECT — changeGlobalTheme handles attribute + CSS vars (NOT persistence — that's the project's job)
// Wrap in a registered project function so it's import-safe across frank serialization.

// functions/switchTheme.js
import { changeGlobalTheme } from 'smbls'
export function switchTheme () {
  const next = this.context.globalTheme === 'dark' ? 'light' : 'dark'
  changeGlobalTheme(next, this.context.designSystem)              // 2nd arg = optional targetConfig
  try { (this.context.window || window).localStorage.setItem('my-app-theme', next) } catch (e) {}
}

// components/ThemeToggle.js
ThemeToggle: {
  extends: 'Button',
  onClick: (e, el) => el.call('switchTheme')
}

// ✅ CORRECT — theme-dependent UI via pure CSS
LightLogo: { extends: 'Icon', icon: 'logoLight', '@dark': { display: 'none' } }
DarkLogo: { extends: 'Icon', icon: 'logoDark', display: 'none', '@dark': { display: 'inline-flex' } }
```

---

## 26. Module-level helpers — banned, use `functions/` + `el.call()` or `el.scope`

```js
// ❌ WRONG — variable / helper outside the export (lost during platform serialization)
const TAX_RATE = 0.08
const formatPrice = (n) => `$${n.toLocaleString()}`

export const PriceCard = {
  text: (el, s) => formatPrice(s.price * (1 + TAX_RATE))
}

// ✅ CORRECT — register in functions/, call via el.call
// functions/formatPrice.js
export const formatPrice = function formatPrice(amount) {
  return `$${amount.toLocaleString()}`
}
export const TAX_RATE = 0.08

// components/PriceCard.js
export const PriceCard = {
  text: (el, s) => el.call('formatPrice', s.price * 1.08)
}

// ✅ CORRECT — el.scope for shared local instance values
export const FilterPanel = {
  onInit: (el) => { el.scope.debounceTimer = null },
  Input: {
    onInput: (e, el, s) => {
      clearTimeout(el.scope.debounceTimer)
      el.scope.debounceTimer = setTimeout(() => s.update({ q: e.target.value }), 200)
    }
  }
}
```

---

## 27. `extends: 'Flex'` removed — replace with `flow:` (catastrophic if forgotten)

```js
// ❌❌ CATASTROPHIC — extends: 'Flex' removed but flow: not added → element collapses to block div
Container: { padding: 'C', maxWidth: 'K' }   // BROKEN! children stack as block

// ✅ CORRECT — always replace with flow:
Container: { flow: 'y', padding: 'C', maxWidth: 'K' }
Row: { flow: 'x', gap: 'A', align: 'center center' }

// ❌ WRONG — extends Flex/Box/Text are redundant and slower (extra merge step)
Card: { extends: 'Box', padding: 'B' }       // Every element is already a Box
Tag:  { extends: 'Text', text: 'NEW' }        // Any element with text: is already Text

// ✅ CORRECT
Card: { padding: 'B', background: 'white' }
Tag:  { tag: 'span', text: 'NEW', padding: 'X A' }
```

---

## 28. Repeating the same condition across many CSS props — collapse into `isX` + `'.isX'`

When two or more properties depend on the same condition, use the conditional-cases pattern (`isX: (el, s) => …` + `'.isX': {…}`). It's fully reactive — the framework wraps `isX` in `createEffect`, so the block re-applies whenever the state read by the condition changes. Repeating the same ternary across many prop functions is redundant and harder to read.

```js
// ❌ Redundant — same condition repeated across multiple props
export const TabBtn = {
  text:       (el, s) => s.label,
  background: (el, s) => s.root.activeTab === el.key ? 'primary' : 'transparent',
  color:      (el, s) => s.root.activeTab === el.key ? 'white' : 'currentColor',
  fontWeight: (el, s) => s.root.activeTab === el.key ? '600' : '400'
}

// ✅ One condition drives a whole reactive CSS block
export const TabBtn = {
  text: (el, s) => s.label,
  background: 'transparent',
  color: 'currentColor',
  fontWeight: '400',

  isActive: (el, s) => s.root.activeTab === el.key,
  '.isActive': { background: 'primary', color: 'white', fontWeight: '600' }
}

// ✅ '!isX' for the inverse branch
export const Item = {
  isSelected: (el, s) => s.selectedId === el.key,
  '.isSelected': { background: 'primary', color: 'white' },
  '!isSelected': { opacity: 0.6 }
}

// ✅ $isX for global cases from context.cases
$isSafari: { paddingTop: 'env(safe-area-inset-top)' }
```

**Same gotcha shape for `if:` and animation:** `if:` IS reactive but each toggle re-creates / destroys the DOM node, killing CSS transitions. For animated show/hide, use `hide:` / `show:` (CSS_PROPS_REGISTRY entries that reactively toggle `display` without destroying the node).

---

## 29. Imports between project files — banned, reference by string + `el.call`

```js
// ❌ WRONG — direct imports between project files
import { Navbar } from './Navbar.js'
import { findUser } from '../functions/findUser.js'
import { brandColor } from '../designSystem/color.js'

export const Header = {
  Nav: { extends: Navbar },
  text: (el, s) => findUser(s).name,
  color: brandColor
}

// ✅ CORRECT — string-based extends + el.call + token name
export const Header = {
  Nav: { extends: 'Navbar' },
  text: (el, s) => el.call('findUser', s).name,
  color: 'brand'
}
```

Only `pages/index.js` is allowed to import siblings — it's the route registry.

---

## 30. `@dark` / `@light` are theme-selector keys, NOT media-query keys

If your `designSystem.media` happens to define `dark` or `light` entries, those entries are **ignored** for `@dark` / `@light` blocks on elements. They always compile to `[data-theme="dark"] &` rules with `!important`, NEVER `@media (prefers-color-scheme: dark)`. (Otherwise the framework would emit invalid `@media [data-theme="…"]` rules.)

To target an actual `prefers-color-scheme` media query, use a different name in `media`:

```js
// designSystem/media.js
export default {
  osDark:  '@media (prefers-color-scheme: dark)',
  osLight: '@media (prefers-color-scheme: light)'
}

// component
Card: {
  background: 'surface',
  '@osDark':  { background: 'surfaceDark' }    // emits a real @media rule
}
```

For runtime theme switching (forced themes / OS-follow), use `@dark` / `@light` — those compile to `[data-theme="dark"] &` and update atomically when `changeGlobalTheme` flips the attribute.

---

## 31. Frank module discovery — files outside the standard slots are INVISIBLE

Frank's bundler discovers code only through these paths (FRAMEWORK.md §9 module-discovery table). Anything else is stripped from the published JSON.

```
state.js, dependencies.js, sharedLibraries.js, config.js,
designSystem/index.js, components/index.js, pages/index.js,
functions/index.js, methods/index.js, snippets/index.js, files/index.js
```

```js
// ❌ Invisible to frank — stripped on publish, ReferenceError at runtime
symbols/lib/format.js
symbols/helpers/api.js
symbols/services/auth.js
symbols/utils/date.js

// ✅ Inside standard slots OR re-exported through them
symbols/functions/format.js
symbols/functions/index.js → export * from './format.js'

// ✅ Files inside subfolders work IF re-exported from the slot index
symbols/functions/helpers/normalize.js
symbols/functions/index.js → export * from './helpers/normalize.js'
```

---

## 32b. `Header: { extends: 'Navbar' }` should usually be `Navbar: {}` — auto-extend by key

DOMQL auto-extends a component when the key name matches a registered component. Almost every `Wrap: { extends: 'X', ... }` you write is dead weight — rename the wrapper key to the component name and drop `extends`.

```js
// ❌                                       // ✅
Header: { extends: 'Navbar' }                Navbar: {}
Header: { extends: 'Navbar', padding: 'A' }  Navbar: { padding: 'A' }
Hgroup: { extends: 'Hgroup', gap: '0' }      Hgroup: { gap: '0' }
Card:   { extends: 'Card', padding: 'B' }    Card:   { padding: 'B' }
Foo:    { extends: 'PriceCard', text: 'Pro' }  PriceCard: { text: 'Pro' }
```

**Multiple instances of the same component → suffix with `_N`** (the part before `_` is what auto-extends):

```js
PriceCard_1: { tier: 'starter' }      // both auto-extend PriceCard
PriceCard_2: { tier: 'pro' }
PriceCard_3: { tier: 'enterprise' }
```

**Keep `extends` only when:**
- The wrapper key carries **genuinely distinct semantic meaning** (`SidebarNav: { extends: 'Navbar' }` if your project really uses both labels for different reasons).
- You need **multi-base composition**: `extends: ['Hgroup', 'Form']`.
- You're chaining a **nested-child reference**: `extends: 'AppShell > Sidebar'`.

If none of those apply, the `extends:` clause is wasted bytes. The audit (`bin/symbols-audit`, `audit_component`) flags this aggressively as Rule 6.

---

## 33. Duplicated shapes — extract to `components/` or use `extends` / `childExtends` / `childProps`

If a shape, style cluster, or behavior repeats — extract it. Inlining a duplicate is a violation. (Rule 61.)

```js
// ❌ Three identical Link clusters
export const Nav = {
  Home:  { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600', href: '/' },
  About: { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600', href: '/about' },
  Docs:  { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600', href: '/docs' }
}

// ✅ Extract NavLink, use childExtends to inject the shared base into every child
// components/NavLink.js
export const NavLink = { extends: 'Link', color: 'primary', padding: 'X A', fontWeight: '600' }

// components/Nav.js
export const Nav = {
  childExtends: 'NavLink',
  Home:  { href: '/',      text: '{{ home | polyglot }}' },
  About: { href: '/about', text: '{{ about | polyglot }}' },
  Docs:  { href: '/docs',  text: '{{ docs | polyglot }}' }
}
```

```js
// ❌ Two identical card shapes
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

// ✅ Extract PricingCard, drive children from state
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
  childrenAs:   'state',
  children: (el, s) => s.tiers
}
```

**Reuse mechanisms:** extract to `components/` + key auto-extend, `extends: 'Name'`, `extends: ['A', 'B']`, `extends: 'Parent > Child'`, `childExtends: 'Name'`, `childProps: { ... }`. Pick the right one — see Rule 61 decision tree.

---

## 34. Never `window.*` for inter-component or cross-cutting context sharing

**`window.*` writes are BANNED in DOMQL components.** smbls is signal-based. Anything written to `window` is not reactive, not scoped, not garbage-collected on unmount, and leaks across every app running in the same tab (canvas, workspace, preview all share one `window` during dev).

### Anti-pattern examples (never write this)

```js
// ❌ WRONG — writing context onto window
onInit: (el, s) => { window.smblsApp = el.getRoot() }
onClick: (e, el, s) => { window.activeProject = s.project }

// ❌ WRONG — reading context from window in another component
onInit: (el) => {
  const p = window.activeProject    // not reactive, leaks across iframes
  el.getRootState().update({ project: p })
}

// ❌ WRONG — raw DOM API instead of DOMQL element traversal
onRender: (el) => {
  const btn = document.querySelector('.submit-btn')    // bypasses DOMQL
  btn.disabled = true
}

// ❌ WRONG — direct document.title write (use metadata: prop)
onRender: (el, s) => { document.title = s.project.name }

// ❌ WRONG — document.createElement (use declarative DOMQL children)
onRender: (el) => {
  const div = document.createElement('div')
  div.textContent = 'hello'
  el.node.appendChild(div)
}
```

### Why `window.*` is wrong

- Not reactive — smbls is signal-based; `window.foo = x` does not trigger re-renders
- Pollutes global namespace — collides with browser extensions, third-party scripts, sibling iframe apps
- Holds GC references forever — prevents teardown cleanup on app unmount
- Implicit/undocumented API — anyone who reads it creates a hidden contract that breaks silently
- Cross-app contamination — canvas, workspace, and preview load in the same Chrome tab during dev; `window.foo` from one leaks into the others

### The 4 canonical channels — pick the right one

| Channel | Scope | Reactive | Use when |
|---|---|---|---|
| **`state`** | Single element + reactive children | Yes (signal-backed store) | Component-local mutable data (`state: { open: false, count: 0 }`) — primary mechanism for component state |
| **`scope`** | Component subtree (parent to descendants) | No (instance storage) | Non-reactive per-instance data: debounce timers, chart instances, refs. `el.scope.timer = null` in `onInit`, clean up in `onRemove` |
| **`globalScope`** / root state | Entire app (every component reads same value) | Yes (signal) | App-wide UI state that is NOT business data (active theme, sidebar open/closed, current modal id) — update via `s.rootUpdate({...})` or `el.getRootState().update({...})` |
| **`context`** | Passed at `create(app, context)` boot | No (config-like) | Project-level config + registered functions (`context.functions`, `context.designSystem`, `context.db`) |

### Correct patterns for each channel

```js
// ✅ state — component-local reactive data
export const Counter = {
  state: { count: 0 },
  text: (el, s) => s.count,
  onClick: (e, el, s) => s.update({ count: s.count + 1 })
}

// ✅ scope — non-reactive per-instance storage (debounce, timers, library refs)
export const SearchInput = {
  onInit: (el) => { el.scope.debounceTimer = null },
  Input: {
    onInput: (e, el, s) => {
      clearTimeout(el.scope.debounceTimer)
      el.scope.debounceTimer = setTimeout(() => {
        el.getRootState().update({ query: e.target.value })
      }, 200)
    }
  },
  onRemove: (el) => { clearTimeout(el.scope.debounceTimer) }
}

// ✅ root state (replaces window.activeProject)
// In context.js / state.js:
state: { activeProject: null }

// In one component — set it:
onClick: (e, el, s) => { el.getRootState().update({ activeProject: s.project }) }

// In another component anywhere in the tree — read it:
text: (el, s) => s.root.activeProject?.name || 'No project'

// ✅ context — boot-time config, accessed read-only at runtime
onInit: (el, s, ctx) => {
  const apiKey = ctx.db.key         // read-only; never write back to ctx
  el.call('initSDK', apiKey)
}
```

### Allowed exceptions (very narrow)

- `window.location` reads (read-only) — but prefer `el.router(path, el.getRoot())` for navigation
- `window.addEventListener` for genuine browser events (`resize`, `beforeunload`, `hashchange`) — bind in `onInit`, clean up in `onRemove`
- Formal devtools hooks following the React pattern (`__REDUX_DEVTOOLS_EXTENSION__`, `__SMBLS_DEVTOOLS_GLOBAL_HOOK__`) — opt-in only, gated by `if (window.__HOOK__)`, never an unconditional write

---

## 32. `db.createClient` MUST NOT be in `config.js` / `context.db` — bundle strips it

The supabase adapter dynamic-imports `@supabase/supabase-js` at runtime. Mermaid's bundle script (`mermaid/src/bundle.js:65-66`) explicitly strips `createClient` from published JSON because functions don't survive frank serialization.

```js
// ❌ Wrong — works locally, fails in published env
import { createClient } from '@supabase/supabase-js'
db: { adapter: 'supabase', createClient, url: '…', key: '…' }

// ✅ Correct — let the runtime adapter resolve `@supabase/supabase-js` via importmap
db: { adapter: 'supabase', url: 'https://xxx.supabase.co', key: 'sb_publishable_…' }

// dependencies.js
export default { '@supabase/supabase-js': 'latest' }
```
