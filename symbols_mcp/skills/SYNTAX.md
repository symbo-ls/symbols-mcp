# DOMQL v3 Syntax — Complete Language Reference

Every pattern here is derived from real working code. Use this as the authoritative reference for writing correct DOMQL v3.

---

## 1. Element Anatomy

A DOMQL element is a plain JS object. Every key has a specific meaning:

```js
export const MyCard = {
  // ── Composition ────────────────────────────────────────────────────
  extends: 'Flex',            // extend from registered component(s)

  // ── DOM ────────────────────────────────────────────────────────────
  tag: 'section',             // HTML tag (default: div)

  // ── CSS props (top-level → promoted to props via propertizeElement) ─
  padding: 'B C',             // design-token value
  gap: 'A',
  flow: 'column',
  theme: 'dialog',
  round: 'C',

  // ── HTML attributes ────────────────────────────────────────────────
  attr: {
    role: 'region',
    'aria-label': ({ props }) => props.label
  },

  // ── State ──────────────────────────────────────────────────────────
  state: { open: false },

  // ── Events (v3 style) ──────────────────────────────────────────────
  onClick: (event, el, state) => { state.update({ open: !state.open }) },
  onRender: (el, state) => { console.log('rendered') },

  // ── Child elements ─────────────────────────────────────────────────
  Header: {
    extends: 'Flex',
    text: ({ props }) => props.title
  },
  Body: {
    html: ({ props }) => props.content
  }
}
```

---

## 2. Element Lifecycle (internal flow)

```
create(props, parent, key, options)
  ├── createElement()          creates bare element
  ├── applyExtends()           merges extends stack (element wins over extends)
  ├── propertizeElement()      routes onXxx events, promotes CSS props
  ├── addMethods()             attaches el.lookup / el.update / etc.
  ├── initProps()              builds props from propsStack
  └── createNode()
        ├── throughInitialExec()     executes function props
        ├── applyEventsOnNode()      binds element.on.* → DOM addEventListener
        └── iterates children → create() recursively
```

**Critical ordering**: `propertizeElement` runs BEFORE `addMethods`. Do not rely on prototype methods in `propertizeElement`.

---

## 3. REGISTRY Keys (handled by DOMQL, NOT promoted to CSS props)

```
attr, style, text, html, data, classlist, state, scope, deps,
extends, children, content, childExtends, childExtendsRecursive,
props, if, define, __name, __ref, __hash, __text,
key, tag, query, parent, node, variables, on, component, context
```

Any key NOT in this list and not a component name (uppercase first) → promoted to `element.props` as a CSS prop.

---

## 4. Extending & Composing

### Single extend
```js
export const PrimaryButton = { extends: 'Button' }
```

### Multiple extends — order matters (first = highest priority)
```js
export const RouteLink = { extends: [Link, RouterLink] }
export const Button    = { extends: ['IconText', 'FocusableComponent'] }
```

### String reference (resolved from `context.components`)
```js
export const MyItem = { extends: 'Hoverable' }
```

### Merge semantics
- Element's own properties **always win** over extends properties
- Objects are deep-merged (both sides preserved)
- Functions are NOT merged — element's function replaces extend's
- Arrays are concatenated

---

## 5. CSS Props — Top-Level Promotion

Top-level non-registry, non-component keys become `element.props`:

```js
export const Card = {
  padding: 'B C',        // → props.padding
  gap: 'Z',              // → props.gap
  flow: 'column',        // → props.flow (shorthand for flexDirection)
  align: 'center',       // → props.align (NOT flexAlign — see RULES.md)
  fontSize: 'A',         // → props.fontSize
  fontWeight: '500',     // → props.fontWeight
  color: 'currentColor', // → props.color
  background: 'codGray', // → props.background
  round: 'C',            // → props.round (border-radius token)
  opacity: '0.85',
  overflow: 'hidden',
  transition: 'B defaultBezier',
  transitionProperty: 'opacity, transform',
  zIndex: 10,
  tag: 'section',        // stays at root (in REGISTRY)
  attr: { href: ... }    // stays at root (in REGISTRY)
}
```

### Pseudo-classes and pseudo-elements

```js
export const Hoverable = {
  opacity: 0.85,
  ':hover':  { opacity: 0.9, transform: 'scale(1.015)' },
  ':active': { opacity: 1,   transform: 'scale(1.015)' },
  ':focus-visible': { outline: 'solid X blue.3' },
  ':not(:first-child)': {
    '@dark':  { borderWidth: '1px 0 0' },
    '@light': { borderWidth: '1px 0 0' }
  }
}
```

### CSS class state modifiers (Emotion `.className`)

```js
export const Item = {
  opacity: 0.6,
  '.active':   { opacity: 1, fontWeight: '600' },
  '.disabled': { opacity: 0.3, pointerEvents: 'none' },
  '.hidden':   { transform: 'translate3d(0,10%,0)', opacity: 0, visibility: 'hidden' }
}
```

### Raw style object (escape hatch)

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

### Media queries (responsive)

```js
export const Grid = {
  columns: 'repeat(4, 1fr)',
  '@tabletSm': { columns: 'repeat(2, 1fr)' },
  '@mobileL': { columns: '1fr' },
  '@dark': { background: 'codGray' },
  '@light': { background: 'concrete' }
}
```

---

## 6. Events

### v3 syntax — top-level `onXxx` (preferred)

```js
export const MyForm = {
  // DOM events — signature: (event, el, state)
  onClick:    (event, el, state) => { /* ... */ },
  onChange:   (event, el, state) => { /* ... */ },
  onInput:    (event, el, state) => { state.update({ value: event.target.value }) },
  onSubmit:   (event, el, state) => { event.preventDefault(); /* ... */ },
  onKeydown:  (event, el, state) => { if (event.key === 'Enter') /* ... */ },
  onMouseover:(event, el, state) => { /* ... */ },
  onBlur:     (event, el, state) => { /* ... */ },
  onFocus:    (event, el, state) => { /* ... */ },

  // DOMQL lifecycle events — signature: (el, state)
  onRender:       (el, state) => { /* after element renders */ },
  onInit:         (el, state) => { /* before render */ },
  onUpdate:       (el, state) => { /* after state/props update */ },
  onStateUpdate:  (el, state) => { /* specifically after state update */ },
  onCreate:       (el, state) => { /* after full creation */ }
}
```

### DOMQL lifecycle events (never bound to DOM)

```
init, beforeClassAssign, render, renderRouter, attachNode,
stateInit, stateCreated, beforeStateUpdate, stateUpdate,
beforeUpdate, done, create, complete, frame, update
```

### Event detection rule (v3)

```js
// A key is a v3 event handler if:
key.length > 2 &&
key.startsWith('on') &&
key[2] === key[2].toUpperCase() &&  // onClick, onRender — NOT "one", "only"
isFunction(value)
```

### Async events

```js
onRender: async (el, state) => {
  try {
    const result = await el.call('fetchData', el.props.id)
    state.update({ data: result })
  } catch (e) {
    state.update({ error: e.message })
  }
}
```

---

## 7. State

### Defining state

```js
export const Counter = {
  state: { count: 0, open: false, selected: null },
}
```

### Reading state in element definitions

```js
export const Item = {
  text:    ({ state }) => state.label,
  opacity: ({ state }) => state.loading ? 0.5 : 1,
  isActive: ({ key, state }) => state.active === key
}
```

### Updating state from events

```js
onClick: (event, el, state) => {
  state.update({ on: !state.on })    // partial update
  state.set({ on: false })           // replace
  state.reset()                      // reset to initial
  state.toggle('open')               // toggle boolean
}
```

### Accessing root state

```js
onClick: (event, el) => {
  const rootState = el.getRootState()
  const user = el.getRootState('user')
}

// In definitions
text: (el) => el.getRootState('currentPage')
```

### Targeted state updates (performance)

```js
state.root.update({
  activeModal: true
}, {
  onlyUpdate: 'ModalCard'   // only ModalCard subtree re-renders
})
```

---

## 8. `attr` — HTML Attributes

```js
export const Input = {
  tag: 'input',
  attr: {
    type: 'text',
    autocomplete: 'off',
    placeholder: ({ props }) => props.placeholder,
    name:        ({ props }) => props.name,
    disabled:    ({ props }) => props.disabled || null,  // null removes the attr
    value: (el) => el.call('exec', el.props.value, el),
    required: ({ props }) => props.required,
    role:       'button',
    'aria-label': ({ props }) => props.aria?.label || props.text,
    tabIndex:   ({ props }) => props.tabIndex
  }
}
```

**Rule**: Returning `null` or `undefined` from an attr function removes the attribute.

---

## 9. `text` and `html`

```js
// Plain text content
export const Label  = { text: ({ props }) => props.label }
export const Badge  = { text: 'New' }
export const Price  = { text: ({ state }) => `$${state.amount.toFixed(2)}` }

// Raw HTML (XSS risk — use sparingly)
export const RichText = { html: ({ props }) => props.html }
```

---

## 10. Children

### Named children (most common)

```js
export const Card = {
  extends: 'Flex',
  Header: {
    extends: 'Flex',
    Title: { text: ({ props }) => props.title },
  },
  Body: { html: ({ props }) => props.content },
  Footer: {
    CloseButton: { extends: 'SquareButton', icon: 'x' }
  }
}
```

**Rule**: Child keys that start with uppercase or are numeric → child elements. All others → CSS props or builtins.

### `childExtends` — extend all direct children

Must be a named component string (see RULES.md Rule 10):

```js
export const NavList = {
  childExtends: 'NavLink'   // ✅ named string only
}
```

### `childExtendRecursive` — apply to ALL descendants

```js
export const Tree = {
  childExtendRecursive: { fontSize: 'A' }
}
```

### `children` — dynamic child list from data

```js
export const DropdownList = {
  children: ({ props }) => props.options || [],
  childExtends: 'OptionItem'
}
```

### `content` — single dynamic child

```js
export const Page = {
  content: ({ props }) => props.page
}
```

---

## 11. Props

### Passing props (consumer side)

```js
const instance = {
  extends: 'Button',
  props: {
    text: 'Submit',
    href: '/dashboard',
    disabled: false
  }
}
```

### Accessing props inside definitions

```js
export const Input = {
  attr: {
    placeholder: ({ props }) => props.placeholder,
    value: (el) => el.props.value,
    disabled: ({ props }) => props.disabled || null
  },
  text: ({ props }) => props.label
}
```

### Boolean / computed props

```js
export const MyComponent = {
  isActive: ({ key, state }) => state.active === key,   // computed boolean
  hasIcon:  ({ props }) => Boolean(props.icon),
  useCache: true
}
```

`is*`, `has*`, `use*` prefixed props are treated as boolean flags.

### `childProps` — inject props into named children

```js
export const Layout = {
  childProps: {
    onClick: (ev) => { ev.stopPropagation() }  // all children get this
  }
}
```

---

## 12. `define` — Custom Property Transformers

```js
define: {
  isActive: (param, el, state, context) => {
    if (param) el.classList.add('active')
    else el.classList.remove('active')
  },
  $collection: async (param, el, state) => {
    const items = await exec(param, el)
    // render dynamic list
  }
}
```

---

## 13. `if` — Conditional Rendering

```js
export const AuthView = {
  if: (el, state) => state.isAuthenticated,
  Dashboard: { /* only renders if condition is true */ }
}

export const ErrorMsg = {
  if: ({ props }) => Boolean(props.error),
  text: ({ props }) => props.error
}
```

---

## 14. `scope`, `data`

```js
// scope: 'state' — element.scope becomes element.state
export const Form = {
  scope: 'state',
  state: { name: '', email: '' }
}

// data — non-reactive storage (doesn't trigger re-renders)
export const Chart = {
  data: { chartInstance: null },
  onRender: (el) => {
    el.data.chartInstance = new Chart(el.node, { /* ... */ })
  }
}
```

---

## 15. Element Methods (on every element)

```js
// Navigation
el.lookup('key')              // find ancestor by key or predicate
el.lookdown('key')            // find first descendant by key
el.lookdownAll('key')         // find all descendants
el.nextElement()              // sibling after
el.previousElement()          // sibling before

// Updates
el.update({ key: value })     // partial update of element properties
el.set({ key: value })        // full replacement
el.setProps({ key: value })   // update props specifically

// Content
el.updateContent(newContent)
el.removeContent()

// State
el.getRootState()             // app-level root state
el.getRootState('key')        // specific key from root state
el.getRoot()                  // root element
el.getContext('key')          // from element's context

// DOM
el.setNodeStyles({ key: value }) // apply inline styles
el.remove()                   // remove element from DOM

// Calling context functions
el.call('fnKey', ...args)     // looks up in context.utils → functions → methods → snippets

// Debug
el.parse()                    // serialize element to plain object
el.keys()                     // list element's own keys
el.verbose()                  // log element in console
```

---

## 16. State Methods

```js
state.update({ key: value })       // partial update, triggers re-render
state.set({ key: value })          // replace, triggers re-render
state.reset()                      // reset to initial value
state.toggle('open')               // toggle boolean property
state.remove()                     // remove state node
state.quietUpdate({ key: value })  // update without re-render
state.add(item)                    // add to collection
state.setByPath('a.b.c', value)    // update nested by path
```

---

## 17. `el.call()` — Context Function Lookup

```js
el.call('router', href, root, {}, options)
el.call('exec', value, el)              // execute a potentially-function prop
el.call('isString', value)
el.call('fetchData', id)
el.call('replaceLiteralsWithObjectFields', template)
```

Lookup order: `context.utils → context.functions → context.methods → context.snippets`

---

## 18. Router (Navigation)

### Declaring pages

```js
// pages/index.js
export default {
  '/':          homePage,
  '/dashboard': dashboardPage,
}
```

### Navigation via Link

```js
export const NavItem = {
  extends: 'Link',
  text: ({ props }) => props.label,
  href: '/dashboard'
}
```

### Programmatic navigation

```js
onClick: (event, el) => {
  event.preventDefault()  // MUST come BEFORE router call
  el.call('router', '/dashboard', el.__ref.root, {}, {
    scrollToTop: true,
    scrollToOptions: { behavior: 'instant' }
  })
}
```

---

## 19. Common Patterns

### Loading state

```js
export const DataList = {
  state: { items: [], loading: true, error: null },

  Loader: { if: ({ state }) => state.loading, extends: 'Spinner' },
  Error:  { if: ({ state }) => Boolean(state.error), text: ({ state }) => state.error },
  Items:  {
    if: ({ state }) => !state.loading && !state.error,
    $collection: ({ state }) => state.items,
    childExtends: 'ListItem'
  },

  onRender: async (el, state) => {
    try {
      const items = await el.call('fetchItems')
      state.update({ items, loading: false })
    } catch (e) {
      state.update({ error: e.message, loading: false })
    }
  }
}
```

### Active list item

```js
export const Menu = {
  state: { active: null },
  childExtends: 'MenuItem',
  childProps: {
    isActive: ({ key, state }) => state.active === key,
    '.active': { fontWeight: '600', color: 'primary' },
    onClick: (ev, el, state) => { state.update({ active: el.key }) }
  }
}
```

### Modal (v3 complete pattern)

```js
export const ModalCard = {
  position: 'absolute', flexAlign: 'center center',
  top: 0, left: 0, boxSize: '100% 100%',
  transition: 'all C defaultBezier',
  opacity: '0', visibility: 'hidden', pointerEvents: 'none', zIndex: '-1',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': { opacity: '1', zIndex: 999999, visibility: 'visible', pointerEvents: 'initial' },

  onClick: (event, element) => { element.call('closeModal') },
  childProps: { onClick: (ev) => { ev.stopPropagation() } },
}
```

---

## 20. Finding DOMQL Elements in the Browser DOM

DOMQL elements use generated Emotion class names (`smbls-xxx`). Access via `node.ref`:

```js
// Every DOMQL-managed DOM node has .ref pointing to its DOMQL element
const domqlElement = someNode.ref
domqlElement.key           // element key name
domqlElement.props         // current props
domqlElement.state         // element state
domqlElement.parent        // parent DOMQL element

// Find by key
for (const node of document.querySelectorAll('*')) {
  if (node.ref?.key === 'ModalCard') { /* ... */ break }
}

// Debug CSS state
ref.__ref.__class        // CSS object input to Emotion
ref.__ref.__classNames   // generated Emotion class names
window.getComputedStyle(ref.node).opacity
```
