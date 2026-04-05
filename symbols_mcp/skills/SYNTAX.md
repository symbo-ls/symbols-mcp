# DOMQL v3 Syntax Reference

Authoritative reference for generating correct DOMQL v3 code. Every pattern is derived from real working code.

---

## Element Anatomy

Produce DOMQL elements as plain JS objects. Every key has a specific role:

```js
export const MyCard = {
  tag: 'section', // HTML tag (default: div)

  // CSS props (top-level, promoted via propertizeElement)
  padding: 'B C',
  gap: 'A',
  flow: 'column',
  theme: 'dialog',
  round: 'C',

  // HTML attributes (auto-detected by attrs-in-props)
  role: 'region',
  ariaLabel: 'My card', // camelCase → aria-label
  aria: { describedby: 'desc' }, // object shorthand → aria-describedby
  attr: { 'aria-label': ({ props }) => props.label }, // explicit attr block

  // State
  state: { open: false },

  // Events (v3 top-level)
  onClick: (event, el, state) => {
    state.update({ open: !state.open })
  },
  onRender: (el, state) => {
    console.log('rendered')
  },

  // Children (PascalCase keys)
  Header: { text: ({ props }) => props.title },
  Body: { html: ({ props }) => props.content }
}
```

---

## Element Lifecycle

```
create(props, parent, key, options)
  |- createElement()          creates bare element
  |- applyExtends()           merges extends stack (element wins)
  |- propertizeElement()      routes onXxx events, promotes CSS props
  |- addMethods()             attaches el.lookup / el.update / etc.
  |- initProps()              builds props from propsStack
  +- createNode()
       |- throughInitialExec()     executes function props
       |- applyEventsOnNode()      binds element.on.* to DOM
       +- iterates children -> create() recursively
```

`propertizeElement` runs BEFORE `addMethods`. Do not rely on prototype methods during propertization.

### Propertization and Define System

`propertizeElement()` classifies keys between root and `props`. Keys starting with `$` overlap between css-in-props conditionals (`$isActive`) and define handlers (`$router`, deprecated v2 handlers like `$propsCollection`, `$collection`).

Define handlers (`element.define[key]` or `context.define[key]`) must stay at the element root so `throughInitialDefine` can process them. Propertization checks for define handlers BEFORE applying `CSS_SELECTOR_PREFIXES`:

```js
const defineValue = this.define?.[key]
const globalDefineValue = this.context?.define?.[key]
if (isFunction(defineValue) || isFunction(globalDefineValue)) continue
if (CSS_SELECTOR_PREFIXES.has(firstChar)) {
  obj.props[key] = value  // move to props for css-in-props
}
```

---

## REGISTRY Keys

These keys are handled by DOMQL internally and are NOT promoted to CSS props:

```
attr, style, text, html, data, classlist, state, scope, deps,
extends, children, content,
childExtend (deprecated), childExtends, childExtendRecursive (deprecated), childExtendsRecursive,
props, if, define, __name, __ref, __hash, __text,
key, tag, query, parent, node, variables, on, component, context
```

Any key NOT in this list and not PascalCase (component) is promoted to `element.props` as a CSS prop.

Always use `childExtends` (plural). The singular `childExtend` is deprecated v2 syntax kept for backwards compatibility.

---

## Extending and Composing

| Pattern                                      | Syntax                                        |
| -------------------------------------------- | --------------------------------------------- |
| Single extend                                | `extends: 'Button'`                           |
| Multiple (first = highest priority)          | `extends: [Link, RouterLink]`                 |
| String reference (from `context.components`) | `extends: 'Hoverable'`                        |
| Multiple strings                             | `extends: ['IconText', 'FocusableComponent']` |

### Merge Semantics

| Type           | Rule                                             |
| -------------- | ------------------------------------------------ |
| Own properties | Always win over extends                          |
| Objects        | Deep-merged (both sides preserved)               |
| Functions      | NOT merged; element's function replaces extend's |
| Arrays         | Concatenated                                     |

---

## CSS Props (Top-Level Promotion)

Place CSS props at the element root. Non-registry, non-PascalCase keys become `element.props`:

```js
export const Card = {
  padding: 'B C', // -> props.padding
  gap: 'Z', // -> props.gap
  flow: 'column', // shorthand for flexDirection
  align: 'center', // NOT flexAlign
  fontSize: 'A',
  fontWeight: '500',
  color: 'currentColor',
  background: 'codGray',
  round: 'C', // border-radius token
  opacity: '0.85',
  overflow: 'hidden',
  transition: 'B defaultBezier',
  transitionProperty: 'opacity, transform',
  zIndex: 10,
  tag: 'section', // stays at root (REGISTRY)
  href: '...' // auto-detected as HTML attribute
}
```

### Pseudo-Classes and Pseudo-Elements

```js
export const Hoverable = {
  opacity: 0.85,
  ':hover': { opacity: 0.9, transform: 'scale(1.015)' },
  ':active': { opacity: 1, transform: 'scale(1.015)' },
  ':focus-visible': { outline: 'solid X blue.3' },
  ':not(:first-child)': {
    '@dark': { borderWidth: '1px 0 0' },
    '@light': { borderWidth: '1px 0 0' }
  }
}
```

### Conditional Props (Cases)

Three prefix types for conditional CSS and attributes:

| Prefix | Resolution                              | Example                       |
| ------ | --------------------------------------- | ----------------------------- |
| `$`    | Global case from `context.cases`        | `$isSafari: { padding: 'B' }` |
| `.`    | Props/state first, then `context.cases` | `.isActive: { opacity: 1 }`   |
| `!`    | Inverted — applies when falsy           | `!isActive: { opacity: 0 }`   |

Cases are defined in `symbols/cases.js` and added to `context.cases`. Both CSS props and HTML attributes inside conditional blocks are applied.

```js
export const Item = {
  opacity: 0.6,
  '.active': { opacity: 1, fontWeight: '600', aria: { selected: true } },
  '.disabled': { opacity: 0.3, pointerEvents: 'none', disabled: true },
  '!active': { ariaHidden: true },
  $isSafari: { padding: 'B' }
}
```

### Raw Style Object (Escape Hatch)

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

### Media Queries

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

## Events

### v3 Syntax (Top-Level `onXxx`)

Use top-level `onXxx` handlers. Two signatures exist:

**DOM events** -- signature: `(event, el, state)`:

```js
onClick:     (event, el, state) => { /* ... */ }
onChange:    (event, el, state) => { /* ... */ }
onInput:     (event, el, state) => { state.update({ value: event.target.value }) }
onSubmit:    (event, el, state) => { event.preventDefault() }
onKeydown:   (event, el, state) => { if (event.key === 'Enter') /* ... */ }
onMouseover: (event, el, state) => { /* ... */ }
onBlur:      (event, el, state) => { /* ... */ }
onFocus:     (event, el, state) => { /* ... */ }
```

**Lifecycle events** -- signature: `(el, state)`:

```js
onInit: (el, state) => {
  /* before render */
}
onRender: (el, state) => {
  /* after render */
}
onCreate: (el, state) => {
  /* after full creation */
}
onUpdate: (el, state) => {
  /* after state/props update */
}
onStateUpdate: (el, state) => {
  /* after state update */
}
```

### Element Lifecycle Events (Full Signatures)

| Event            | Signature                                           | When                    | Notes                    |
| ---------------- | --------------------------------------------------- | ----------------------- | ------------------------ |
| `onInit`         | `(element, state, context, updateOptions)`          | Before init             | Return `false` to break  |
| `onAttachNode`   | `(element, state, context, updateOptions)`          | After DOM node attached |                          |
| `onRender`       | `(element, state, context, updateOptions)`          | After render            |                          |
| `onComplete`     | `(element, state, context, updateOptions)`          | After full creation     |                          |
| `onBeforeUpdate` | `(changes, element, state, context, updateOptions)` | Before update           | `changes` is first param |
| `onUpdate`       | `(element, state, context, updateOptions)`          | After update            |                          |

### State Events

| Event                 | Signature                                           | When                | Notes                                      |
| --------------------- | --------------------------------------------------- | ------------------- | ------------------------------------------ |
| `onStateInit`         | `(element, state, context, updateOptions)`          | Before state init   | Return `false` to break                    |
| `onStateCreated`      | `(element, state, context, updateOptions)`          | After state created |                                            |
| `onBeforeStateUpdate` | `(changes, element, state, context, updateOptions)` | Before state update | Return `false` to prevent; `changes` first |
| `onStateUpdate`       | `(changes, element, state, context, updateOptions)` | After state update  | `changes` is first param                   |

`onBeforeStateUpdate` and `onStateUpdate` receive `changes` as their FIRST parameter.

### DOMQL Lifecycle Names (Never Bound to DOM)

```
init, beforeClassAssign, render, renderRouter, attachNode,
stateInit, stateCreated, beforeStateUpdate, stateUpdate,
beforeUpdate, done, create, complete, frame, update
```

### Event Detection Rule

A key is a v3 event handler when:

```js
key.length > 2 &&
  key.startsWith('on') &&
  key[2] === key[2].toUpperCase() && // onClick, onRender -- NOT "one", "only"
  isFunction(value)
```

### Async Events

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

## State

### Define, Read, Update

```js
// Define
state: { count: 0, open: false, selected: null }

// Read in definitions
text:     ({ state }) => state.label
opacity:  ({ state }) => state.loading ? 0.5 : 1
isActive: ({ key, state }) => state.active === key

// Update from events
onClick: (event, el, state) => {
  state.update({ on: !state.on })    // partial update
  state.set({ on: false })           // replace
  state.reset()                      // reset to initial
  state.toggle('open')               // toggle boolean
}
```

### Root State Access

```js
// From events
const rootState = el.getRootState()
const user = el.getRootState('user')

// In definitions
text: (el) => el.getRootState('currentPage')
```

### Targeted Updates (Performance)

```js
state.root.update(
  { activeModal: true },
  {
    onlyUpdate: 'ModalCard' // only ModalCard subtree re-renders
  }
)
```

---

## State Methods

| Method                              | Description                                 |
| ----------------------------------- | ------------------------------------------- |
| `state.update(value, options?)`     | Deep overwrite, triggers re-render          |
| `state.set(value, options?)`        | Replace state entirely (removes old values) |
| `state.reset(options?)`             | Reset to initial values                     |
| `state.add(value, options?)`        | Add item to array state                     |
| `state.toggle(key, options?)`       | Toggle boolean property                     |
| `state.remove(key, options?)`       | Remove property                             |
| `state.apply(fn, options?)`         | Apply fn that RETURNS new value             |
| `state.applyFunction(fn, options?)` | Apply fn that MUTATES state directly        |
| `state.replace(value, options?)`    | SHALLOW replace (nested keys disappear)     |
| `state.clean(options?)`             | Empty the state                             |
| `state.parse()`                     | Get purified plain object                   |
| `state.quietUpdate(value)`          | Update without triggering re-render         |
| `state.quietReplace(value)`         | Replace without triggering re-render        |
| `state.destroy(options?)`           | Completely remove state                     |
| `state.setByPath('a.b.c', value)`   | Update nested by dot-path                   |

`apply()` expects the function to RETURN a new value. `applyFunction()` expects direct MUTATION:

```js
state.apply((s) => ({ ...s, count: s.count + 1 })) // return
state.applyFunction((s) => {
  s.count++
}) // mutate
```

### State Update Options

| Option                      | Description                           |
| --------------------------- | ------------------------------------- |
| `isHoisted`                 | Mark update as hoisted                |
| `preventHoistElementUpdate` | Prevent hoisted element from updating |

### State Navigation

```js
state.parent // parent element's state
state.root // application-level root state
```

State as string inherits from parent:

```js
// Parent has state: { userProfile: { name: 'John' } }
state: 'userProfile' // child inherits parent's userProfile key
```

---

## `attr` (HTML Attributes)

Standard HTML attributes (600+ recognized per tag) are auto-detected by the `attrs-in-props` module and can be placed directly at the element root or in props. Use `attr: {}` ONLY for `data-*`, `aria-*`, and custom non-standard attributes.

```js
export const Input = {
  tag: 'input',
  // Standard HTML attributes — placed directly (auto-detected)
  type: 'text',
  autocomplete: 'off',
  placeholder: ({ props }) => props.placeholder,
  name: ({ props }) => props.name,
  disabled: ({ props }) => props.disabled || null, // null removes attr
  value: (el) => el.call('exec', el.props.value, el),
  required: ({ props }) => props.required,
  role: 'button',
  tabIndex: ({ props }) => props.tabIndex,
  // Non-standard / ARIA — use attr: {}
  attr: {
    'aria-label': ({ props }) => props.aria?.label || props.text
  }
}
```

Return `null` or `undefined` from a prop function to remove the attribute.

---

## `text` and `html`

```js
export const Label = { text: ({ props }) => props.label }
export const Badge = { text: 'New' }
export const Price = { text: ({ state }) => `$${state.amount.toFixed(2)}` }
export const RichText = { html: ({ props }) => props.html } // XSS risk
```

---

## Children

### Named Children

PascalCase or numeric keys become child elements:

```js
export const Card = {
  flow: 'y',
  Header: {
    flow: 'x',
    Title: { text: ({ props }) => props.title }
  },
  Body: { html: ({ props }) => props.content },
  Footer: {
    CloseButton: { extends: 'SquareButton', icon: 'x' }
  }
}
```

### `childExtends`

Extend all direct children. Use a named component string:

```js
export const NavList = { childExtends: 'NavLink' }
```

### `childExtendsRecursive`

Apply to ALL descendants:

```js
export const Tree = { childExtendsRecursive: { fontSize: 'A' } }
```

### `children` (Dynamic Child List)

```js
export const DropdownList = {
  children: ({ props }) => props.options || [],
  childExtends: 'OptionItem'
}
```

### `childrenAs`

Control how children data maps to elements:

| Value               | Behavior                                         |
| ------------------- | ------------------------------------------------ |
| `'props'` (default) | Each item becomes child's `props`                |
| `'state'`           | Each item becomes child's `state`                |
| `'element'`         | Each item is used directly as element definition |

```js
{ children: [{ text: 'Hello' }] }                              // -> { props: { text: 'Hello' } }
{ children: [{ count: 5 }], childrenAs: 'state' }              // -> { state: { count: 5 } }
{ children: [{ tag: 'span', text: 'Hi' }], childrenAs: 'element' }  // -> { tag: 'span', text: 'Hi' }
```

### `state: 'key'` (Narrow State Scope)

Narrow parent state for children:

```js
export const TeamList = {
  state: 'members',
  childExtends: 'TeamItem',
  children: ({ state }) => state
}

export const TeamItem = {
  state: true, // REQUIRED for children to receive individual state
  Title: { text: ({ state }) => state.name }
}
```

`state: true` is required on child components reading `({ state }) => state.field` when used with `childExtends`.

### `content` (Single Dynamic Child)

```js
export const Page = { content: ({ props }) => props.page }
```

### Children as Async

```js
{
  children: async (element, state, context) => await window.fetch('...endpoint'),
  childrenAs: 'state',
}
```

---

## Props

### Pass and Access

```js
// Pass (consumer side)
{ extends: 'Button', props: { text: 'Submit', href: '/dashboard', disabled: false } }

// Access (definition side) — standard attrs auto-detected
placeholder: ({ props }) => props.placeholder,
value: (el) => el.props.value,
disabled: ({ props }) => props.disabled || null,
text: ({ props }) => props.label
```

### Boolean/Computed Props

`is*`, `has*`, `use*` prefixes are treated as boolean flags:

```js
isActive: ({ key, state }) => state.active === key
hasIcon: ({ props }) => Boolean(props.icon)
useCache: true
```

### `childProps`

Inject props into all named children:

```js
export const Layout = {
  childProps: {
    onClick: (ev) => {
      ev.stopPropagation()
    }
  }
}
```

---

## `define` (Custom Property Transformers)

```js
define: {
  isActive: (param, el, state, context) => {
    if (param) el.classList.add('active')
    else el.classList.remove('active')
  }
}
```

### Built-In Defines

| Define     | Purpose                               |
| ---------- | ------------------------------------- |
| `metadata` | SEO metadata (see SEO-METADATA.md)    |
| `routes`   | Route definitions for the router      |
| `$router`  | Render route content into the element |

```js
export const aboutPage = {
  metadata: {
    title: 'About Us',
    description: (el, s) => s.aboutText,
    'og:image': '/about.png'
  }
}
```

---

## `if` (Conditional Rendering)

```js
export const AuthView = {
  if: (el, state) => state.isAuthenticated,
  Dashboard: {
    /* renders only when true */
  }
}

export const ErrorMsg = {
  if: ({ props }) => Boolean(props.error),
  text: ({ props }) => props.error
}
```

---

## `scope` and `data`

```js
// scope: 'state' -- element.scope becomes element.state
export const Form = {
  scope: 'state',
  state: { name: '', email: '' }
}

// data -- non-reactive storage (no re-renders)
export const Chart = {
  data: { chartInstance: null },
  onRender: (el) => {
    el.data.chartInstance = new Chart(el.node, {
      /* ... */
    })
  }
}
```

---

## Element Methods

| Category       | Method                                     | Description                                                                  |
| -------------- | ------------------------------------------ | ---------------------------------------------------------------------------- |
| **Navigation** | `el.lookup('key')`                         | Find ancestor by key or predicate                                            |
|                | `el.lookdown('key')`                       | Find first descendant by key                                                 |
|                | `el.lookdownAll('key')`                    | Find all descendants by key                                                  |
|                | `el.spotByPath(['Header', 'Nav', 'Logo'])` | Find by array path                                                           |
|                | `el.nextElement()`                         | Next sibling                                                                 |
|                | `el.previousElement()`                     | Previous sibling                                                             |
|                | `el.getRoot()`                             | Root element                                                                 |
| **Updates**    | `el.update({ key: value })`                | Deep overwrite element properties                                            |
|                | `el.set({ key: value })`                   | Set content element                                                          |
|                | `el.update({ key: value })`                | Update props specifically                                                    |
| **Content**    | `el.updateContent(newContent)`             | Update content                                                               |
|                | `el.removeContent()`                       | Remove content                                                               |
| **State**      | `el.getRootState()`                        | App-level root state                                                         |
|                | `el.getRootState('key')`                   | Specific key from root state                                                 |
|                | `el.getContext('key')`                     | Value from element's context                                                 |
| **DOM**        | `el.setNodeStyles({ key: value })`         | Apply inline styles                                                          |
|                | `el.remove()`                              | Remove from tree and DOM                                                     |
| **Context**    | `el.call('fnKey', ...args)`                | Lookup: `context.utils -> functions -> methods -> snippets`                  |
| **Router**     | `el.router(path, root)`                    | SPA navigation — `root` must be the element with routes (use `el.getRoot()`) |
| **Debug**      | `el.parse(exclude)`                        | One-level purified plain object                                              |
|                | `el.parseDeep(exclude)`                    | Deep purified plain object                                                   |
|                | `el.keys()`                                | List element's own keys                                                      |
|                | `el.verbose()`                             | Log element in console                                                       |

### Element Update Options

Pass as second argument to `el.update(value, options)`:

| Option                  | Description                         |
| ----------------------- | ----------------------------------- |
| `onlyUpdate`            | Only update specific subtree by key |
| `preventUpdate`         | Prevent element update              |
| `preventStateUpdate`    | Prevent state update                |
| `preventUpdateListener` | Skip update event listeners         |
| `preventUpdateAfter`    | Skip post-update hooks              |
| `lazyLoad`              | Enable lazy loading for the update  |

---

## `el.call()` (Context Function Lookup)

Lookup order: `context.utils -> context.functions -> context.methods -> context.snippets`

```js
el.router(href, el.getRoot(), {}, options) // router is also available as el.router()
el.call('exec', value, el)
el.call('isString', value)
el.call('fetchData', id)
el.call('replaceLiteralsWithObjectFields', template)
```

---

## Router

### Declare Pages

```js
// pages/index.js
export default {
  '/': homePage,
  '/dashboard': dashboardPage
}
```

### Link Navigation

```js
export const NavItem = {
  extends: 'Link',
  text: ({ props }) => props.label,
  href: '/dashboard'
}
```

### Programmatic Navigation

Call `event.preventDefault()` BEFORE the router call:

```js
onClick: (event, el) => {
  event.preventDefault()
  el.router(
    '/dashboard',
    el.getRoot(),
    {},
    {
      scrollToTop: true,
      scrollToOptions: { behavior: 'instant' }
    }
  )
}
```

### Custom Router Element (Persistent Layouts)

Configure in `config.js` to render pages inside a specific element:

```js
// config.js
export default {
  router: {
    customRouterElement: 'Folder.Content' // dot-separated path from root
  }
}
```

The `/` page defines the persistent layout shell. Sub-pages render inside the target element without destroying the layout.

---

## `element.require()` (Cross-Environment Dependency Loading)

```js
{
  tag: 'canvas',
  onRender: async (element, state) => {
    const Chart = element.require('chartjs')
    const ctx = element.node.getContext('2d')
    new Chart(ctx, { type: 'bar', data: { /* ... */ } })
  }
}
```

---

## Common Patterns

### Loading State

```js
export const DataList = {
  state: { items: [], loading: true, error: null },
  Loader: { if: ({ state }) => state.loading, extends: 'Spinner' },
  Error: {
    if: ({ state }) => Boolean(state.error),
    text: ({ state }) => state.error
  },
  Items: {
    if: ({ state }) => !state.loading && !state.error,
    children: ({ state }) => state.items,
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

### Active List Item

```js
export const Menu = {
  state: { active: null },
  childExtends: 'MenuItem',
  childProps: {
    isActive: ({ key, state }) => state.active === key,
    '.active': { fontWeight: '600', color: 'primary' },
    onClick: (ev, el, state) => {
      state.update({ active: el.key })
    }
  }
}
```

### Modal

```js
export const ModalCard = {
  position: 'absolute',
  align: 'center center',
  top: 0,
  left: 0,
  boxSize: '100% 100%',
  transition: 'all C defaultBezier',
  opacity: '0',
  visibility: 'hidden',
  pointerEvents: 'none',
  zIndex: '-1',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': {
    opacity: '1',
    zIndex: 999999,
    visibility: 'visible',
    pointerEvents: 'initial'
  },

  onClick: (event, element) => {
    element.call('closeModal')
  },
  childProps: {
    onClick: (ev) => {
      ev.stopPropagation()
    }
  }
}
```

---

## Naming Conventions

| Category       | Convention          | Examples                                            |
| -------------- | ------------------- | --------------------------------------------------- |
| Components     | PascalCase          | `CustomComponent`, `NavBar`, `UserProfile`          |
| Properties     | camelCase           | `paddingInlineStart`, `fontSize`, `backgroundColor` |
| Repeating keys | Snake_Case suffixes | `Li_1`, `Li_2`, `Li_One`                            |

---

## Reserved Keywords

These keys are handled by the DOMQL engine and are NOT CSS props or child components:

```
key, extends, extend, childExtends, childExtend, childExtendsRecursive,
childProps, props, state, tag, query, data, scope, children, childrenAs,
context, attr, style, text, html, content, classlist, root, deps,
if, define, on, fetch, component, routes, $router, variables,
__name, __ref, __hash, __text, parent, node
```

All other keys: lowercase/camelCase = CSS props, PascalCase = child components.

---

## Finding DOMQL Elements in Browser DOM

Every DOMQL-managed DOM node has `.ref` pointing to its DOMQL element:

```js
const domqlElement = someNode.ref
domqlElement.key // element key name
domqlElement.props // current props
domqlElement.state // element state
domqlElement.parent // parent DOMQL element

// Find by key
for (const node of document.querySelectorAll('*')) {
  if (node.ref?.key === 'ModalCard') {
    /* ... */ break
  }
}

// Debug CSS state
ref.__ref.__class // CSS object input to Emotion
ref.__ref.__classNames // generated Emotion class names
window.getComputedStyle(ref.node).opacity
```
