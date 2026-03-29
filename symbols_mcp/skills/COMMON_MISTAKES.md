# Common Mistakes — Wrong vs Correct DOMQL v3 Patterns

This is a zero-tolerance reference. Every pattern in the "Wrong" column is FORBIDDEN. The audit tool catches all of them. There is no concept of "known debt" — every violation must be fixed to 100%.

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

## 4. Icons — use Icon component + `designSystem/icons`, never inline HTML

```js
// ❌ WRONG — inline HTML strings
BtnBold: { extends: 'ToolbarBtn', html: '<b>B</b>' }
BtnColorRed: { html: '<span style="color:#d93025;font-weight:bold">A</span>' }

// ✅ CORRECT — Icon component with designSystem/icons
BtnBold: { extends: 'ToolbarBtn', Icon: { extends: 'Icon', icon: 'bold', width: 'A', height: 'A' } }
BtnColorRed: { extends: 'ToolbarBtn', color: 'danger', Icon: { extends: 'Icon', icon: 'colorA', width: 'A', height: 'A' } }

// designSystem/icons.js:
// bold: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="..."/></svg>'
// colorA: '<svg width="24" height="24" viewBox="0 0 24 24"><path d="..."/></svg>'
```

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
