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

---

## REGISTRY Keys

These are handled by DOMQL internally and are NOT promoted to CSS props:

```
attr, style, text, html, data, classlist, state, scope, deps,
extends, children, content, childExtends, childExtendsRecursive, childProps, childrenAs,
props, if, show, hide, value, define, key, tag, query, parent, node,
variables, component, context, fetch, routes, metadata,
onInit, onCreate, onComplete, onRender, onRenderRouter, onUpdate, onBeforeUpdate,
onStateInit, onStateCreated, onStateUpdate, onBeforeStateUpdate,
onAttachNode, onFrame, onError,
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
| Multiple (first = highest priority) | `extends: ['Link', 'RouterLink']` |
| String reference (from `context.components`) | `extends: 'Hoverable'` |
| Auto-extend by key | `Icon: {...}` auto-extends 'Icon'; `Icon_1: {...}` also auto-extends 'Icon' |

### Merge Semantics

| Type | Rule |
| -- | -- |
| Own properties | Always win over extends |
| Plain objects | Deep-merged (PascalCase children deep-merge child overrides) |
| Special keys (`childProps`, `attr`, `style`, `scope`, `data`) | Shallow merge {...base, ...override} |
| Functions | NOT merged; element's function replaces extend's |
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

### Conditional Props (Cases)

Three prefix types for conditional CSS and attributes:

| Prefix | Resolution | Example |
| -- | -- | -- |
| `$` | Global case from `context.cases` | `$isSafari: { padding: 'B' }` |
| `.` | Element/state first, then `context.cases` | `'.isActive': { opacity: 1 }` |
| `!` | Inverted — applies when falsy | `'!isActive': { opacity: 0 }` |

Cases are defined in `cases.js` at the project root and added to `context.cases`. CSS props AND HTML attributes inside conditional blocks are applied.

`.isX` / `'!isX'` / `$isX` blocks are fully reactive — the framework wraps `isX` conditions in `createEffect`, so the matching block re-applies whenever the state read by the condition changes. Use the pattern when two or more CSS props share a single condition; it's cleaner than repeating the same condition across many prop functions.

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

// ✅ $isX for global cases (browser detection from context.cases)
$isSafari: { paddingTop: 'env(safe-area-inset-top)' }
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
onUpdate:      (el, s, ctx)    => { /* after el.update() */ },
onBeforeUpdate:(changes, el, s, ctx) => { /* return false to cancel */ },
onStateUpdate: (changes, el, s, ctx) => { /* after state change */ },
onBeforeStateUpdate: (changes, el, s, ctx) => { /* return false to cancel */ },
onFrame:       (el, s, ctx)    => { /* every requestAnimationFrame */ },
onError:       (el, s, ctx)    => { /* lifecycle error caught inside the element */ },
onBeforeRemove:(el, s, ctx)    => { /* fires BEFORE refs/state are torn down — can still read state and cancel sockets/requests */ },
onRemove:      (el)            => { /* fires AFTER DOM detach + state.destroy(); refs are still present for logging */ }
```

`onBeforeUpdate` / `onStateUpdate` / `onBeforeStateUpdate` receive `changes` as their FIRST parameter.

`onBeforeRemove` fires inside `dispose(element)` BEFORE effects, event listeners, and state are destroyed — the handler can still access `el.state`, `el.context`, and call methods. `onRemove` fires AFTER DOM detach and `state.destroy()` but BEFORE refs are cleared — safe for logging `el.key` / `el.parent`. Both hooks are wrapped in try/catch so a misbehaving handler does not block sibling cleanup.

### Event Detection Rule

A key is an event handler when:

```js
key.length > 2 && key[0] === 'o' && key[1] === 'n' &&
  key[2] >= 'A' && key[2] <= 'Z' &&     // onClick, onRender — NOT "one", "only"
  isFunction(value)
```

Detection is structural (pattern of `onUpper...`), not registry-based — any custom event name like `onCustomThing` works as long as it's a function.

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
  s.update({ open: !s.open })   // partial update (deep merge)
  s.replace({ open: false })    // shallow replace (removes other keys)
  s.set({ open: false })        // alias for replace
  s.reset()                     // restore to initial parsed state
  s.toggle('open')              // flip boolean
  s.add('items', { id: 1 })     // push to array or merge into object
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
| `s.update(value, opts?)` | Deep merge, triggers reactivity |
| `s.replace(value, opts?)` | Replace entire state (drops missing keys) |
| `s.set(value, opts?)` | Alias for replace |
| `s.clean(opts?)` | Remove all keys |
| `s.parse()` | Snapshot as plain object |
| `s.keys()` | Property names |
| `s.values()` | Property values |
| `s.destroy(opts?)` | Destroy underlying signal store |
| `s.add(key, val, opts?)` | Add to array or object |
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
| `s.quietUpdate(value)` | Update without triggering listeners |
| `s.quietReplace(value)` | Replace without triggering listeners |
| `s.rootUpdate(obj, opts?)` | Update root state from anywhere |
| `s.parentUpdate(obj, opts?)` | Update parent state |
| `s.root` | Root state reference |
| `s.parent` | Parent state reference |

```js
// apply vs applyFunction
s.apply((cur) => ({ ...cur, count: cur.count + 1 }))   // returns new value
s.applyFunction((cur) => { cur.count++ })              // mutates in place
```

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

`is*`, `has*`, `use*` prefixes are treated as boolean conditions when followed by a function. Pair with `'.isX'` blocks (Rule 19):

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
| **Updates** | `el.update(value, opts?)` | Deep merge update |
| | `el.setProps(value, opts?)` | Alias for update |
| | `el.set(content, opts?)` | Replace element's `content` child |
| | `el.reset(opts?)` | Dispose + recreate from parsed definition |
| **Content** | `el.removeContent()` | Dispose & remove `content` child |
| **DOM** | `el.setNodeStyles({})` | Apply inline styles directly (escape hatch) |
| | `el.remove()` / `el.dispose()` | Remove from tree, dispose effects, dispose state |
| **Functions** | `el.call('fnName', ...args)` | Lookup: `methods → functions → utils → prototype` |
| **Routing** | `el.router(path, root, state?, options?)` | SPA navigation (root = `el.getRoot()`) |
| **Debug** | `el.parse(exclude)` | Plain object snapshot |
| | `el.parseDeep(exclude)` | Deep parse including children |
| | `el.keys()` | Element's own keys |
| | `el.log(...keys)` | Console.log element or specific keys |
| | `el.verbose()` | Verbose log |
| | `el.warn(...)` / `el.error(...)` | Logging helpers |
| | `el.variables()` | Resolved variables |
| | `el.getRef()` | Internal `__ref` tracking |

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

### Custom Router Element (Persistent Layouts)

```js
// config.js
export default {
  router: { customRouterElement: 'Folder.Content' }
}
```

The `/` page defines the persistent layout shell. Sub-pages render inside the target without destroying the shell.

### Guards

```js
const authGuard = ({ element }) =>
  element.state.root.isLoggedIn ? true : '/login'

el.router('/dashboard', el.getRoot(), {}, { guards: [authGuard] })
```

---

## Data Fetching (`@symbo.ls/fetch`)

Declarative fetch on any element. Caching, dedup, retry, refetch-on-focus, pagination — all built in.

### Setup (`config.js`)

```js
db: { adapter: 'supabase', url: 'https://xxx.supabase.co', key: 'sb_publishable_…' }
// or REST:
db: { adapter: 'rest', url: 'https://api.example.com',
      headers: { Authorization: 'Bearer token' },
      auth: { baseUrl: '…', signInUrl: '/login', sessionUrl: '/me' } }
// or local:
db: { adapter: 'local', data: { articles: [] }, persist: true }
```

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
Deduplication: identical concurrent queries share one network request.

### Retry / Optimistic / Initial / Placeholder

```js
{ fetch: { from: 'articles', retry: 5 } }
{ fetch: { from: 'articles', retry: { count: 3, delay: (n) => 1000 * 2 ** n } } }
{ fetch: { from: 'articles', placeholderData: [] } }
{ fetch: { from: 'settings', initialData: { theme: 'dark' } } }
```

> NEVER call `window.fetch` / `axios` from a component. Use `fetch:` declaratively, or a `functions/loadX.js` for imperative flows. (Rule 47.)

---

## Polyglot (`@symbo.ls/polyglot`)

### Setup

```js
import { polyglotPlugin } from '@symbo.ls/polyglot'
import { polyglotFunctions } from '@symbo.ls/polyglot/functions'

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
context.functions = { ...context.functions, ...polyglotFunctions }
context.plugins   = [polyglotPlugin, …]
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

When `state.root.lang` changes, every fetch request gets an `Accept-Language` header automatically. The header is the **only** injection — fetch does NOT add a `lang` query parameter or RPC argument. If your backend expects `lang` in `params`, set it explicitly: `fetch: { from: 'articles', params: (el, s) => ({ lang: s.root.lang, status: 'published' }) }`.

**Available polyglot functions** (registered automatically when `context.polyglot` is set; do NOT use `t` or `tr` — those don't exist):

| Function | Purpose |
| -- | -- |
| `polyglot(key, lang?)` | Translate (used in template literals AND imperative calls) |
| `getLocalStateLang(prefix)` | Read per-language state field (`state.<prefix>_<activeLang>`) |
| `getActiveLang()` | Active language code |
| `getLang()` | Alias for getActiveLang |
| `setLang(lang)` | Switch language + persist + load remote (async) |
| `getLanguages()` | Available language codes |
| `loadTranslations(lang)` | Manually trigger remote load |
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

Helmet works identically at runtime AND in `smbls brender` SSR.

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

```js
export const DataList = {
  state: { items: [] },
  fetch: { from: 'items', cache: '5m', placeholderData: [] },
  Loader: { if: (el, s) => s.__loading, extends: 'Spinner' },
  Error:  { if: (el, s) => Boolean(s.__error), text: (el, s) => s.__error.message },
  Items:  {
    if: (el, s) => !s.__loading && !s.__error,
    children:     (el, s) => s.items,
    childExtends: 'ListItem',
    childrenAs:   'state'
  }
}
```

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
onStateUpdate, onBeforeStateUpdate, onAttachNode, onFrame,
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
