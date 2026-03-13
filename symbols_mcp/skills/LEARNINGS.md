# Framework Learnings — Technical Internals & Gotchas

Deep technical findings about the DOMQL/Symbols runtime. Understanding these
internals helps you write correct code and avoid subtle bugs.

---

## CSS-in-Props Resolution Order

When DOMQL processes CSS properties on an element, it follows this order:

1. `element.classlist[key]` — component-level class definitions (highest priority)
2. `CSS_PROPS_REGISTRY[key]` — theme-aware processors (color, border, shadow, hide, etc.)
3. `DEFAULT_CSS_PROPERTIES_LIST.includes(key)` — raw pass-through (no theme resolution)
4. Everything else → `rest` (returned as non-CSS props)

**Implication**: If you want theme colors to resolve, the property must go through
`CSS_PROPS_REGISTRY`. Shorthand properties like `borderColor` resolve themes, but
directional variants (`borderTopColor`) need explicit registry entries.

---

## CSS Override Precedence

`props` block CSS **cannot** override base component-level CSS. Override must match
the declaration level:

```js
// WRONG — props can't override component-level color
export const MyLink = {
  extends: 'Link',
  props: { color: 'primary' },  // Won't override Link's component-level color
}

// CORRECT — override at the same level
export const MyLink = {
  extends: 'Link',
  color: 'primary',  // Overrides at component level
}
```

Same rule applies to sub-component overrides in nested children.

---

## Event Handler Signatures

There are two different signatures depending on event type:

**Lifecycle events** — `(element, state)`:
```js
onInit: (el, s) => {}
onRender: (el, s) => {}
onUpdate: (el, s) => {}
```

**DOM events** — `(event, element, state)`:
```js
onClick: (event, el, s) => {}
onInput: (event, el, s) => {}
onKeydown: (event, el, s) => {}
```

**Common mistake**: Using DOM event signature `(event, el, s)` in lifecycle events,
which shifts all parameters and causes `state` to be `undefined`.

---

## Dynamic HTML Attributes Must Use `attr` Block

Functions at component level get **stringified** as HTML attributes. For dynamic
HTML attribute values, always use the `attr: {}` block:

```js
// WRONG — renders type="({ props }) => props.type" literally
export const MyButton = {
  tag: 'button',
  type: ({ props }) => props.type,
}

// CORRECT — attr block properly executes functions
export const MyButton = {
  tag: 'button',
  attr: {
    type: ({ props }) => props.type || 'button',
  },
}
```

---

## Component Key Auto-Extending

A child key matching a registered component name **automatically extends** that component:

```js
export const MyPage = {
  // "Hgroup" auto-extends the registered Hgroup component
  Hgroup: { gap: '0' },

  // "Avatar" auto-extends the registered Avatar component
  Avatar: { boxSize: 'C' },

  // "Button" auto-extends the registered Button component
  Button: { text: 'Click' },
}
```

Use explicit `extends` only when the key casing differs from the component name,
or when you want to extend a different component than the key name suggests.

---

## Conditional Props Pattern (isActive)

Use `isActive` boolean + `.isActive` / `!isActive` blocks instead of spreading props:

```js
// CORRECT — conditional style blocks
export const NavItem = {
  isActive: (el, s) => s.root.currentPath === s.path,
  padding: 'Z A',
  opacity: '.6',

  '.isActive': {
    opacity: '1',
    fontWeight: '700',
    borderBottom: '2px solid',
    borderBottomColor: 'primary',
  },

  '!isActive': {
    ':hover': { opacity: '.8' },
  },
}

// WRONG — dynamic props spread
export const NavItem = {
  props: (el, s) => ({
    opacity: s.root.currentPath === s.path ? '1' : '.6',
    fontWeight: s.root.currentPath === s.path ? '700' : '400',
  }),
}
```

Default state goes at component level; active overrides go in the `.isActive` block.

---

## state.root.update() with onlyUpdate

For performance, limit re-rendering to specific component subtrees:

```js
onClick: (e, el, s) => {
  s.root.update(
    { activeModal: 'settings' },
    { onlyUpdate: 'ModalCard' }  // Only re-render ModalCard subtree
  )
}
```

---

## SPA Navigation — preventDefault Required

When using `tag: 'a'` with `attr: { href: '/' }` AND an `onClick` handler, both the
handler and the browser's default navigation fire. Always call `e.preventDefault()`:

```js
export const NavLink = {
  extends: 'Link',
  onClick: (e, el) => {
    e.preventDefault()
    el.router('/', el.getRoot())
  },
}
```

---

## Emotion CSS Class Cleanup

When toggling CSS-in-props values (like `hide`, `opacity`), stale Emotion class names
can persist on the DOM. The framework handles cleanup, but be aware:

- `hide: true` generates a class with `display: none !important`
- When `hide` becomes falsy, no class is generated — the old one must be removed
- Class names are content-hashed: `smbls-{hash}-{label}`

---

## Forced Reflow for Transitions

`state.root.update()` applies all Emotion classes in one JS execution block — the
browser never paints the intermediate state. Use `node.offsetHeight` to force reflow:

```js
// Force reflow between states for CSS transition to work
el.node.style.opacity = '0'
el.node.offsetHeight  // Trigger reflow
el.node.style.opacity = ''  // Let Emotion class transition take over
```

Don't use `requestAnimationFrame` (unreliable) or `transitionend` (may not fire if
element starts hidden).

---

## Update Cascade Path

Understanding the render cycle helps debug state issues:

```
state.update()
  → applyElementUpdate
    → element.update({}, { updateByState: true })
      → for (param in element): update children recursively
      → update content element explicitly (bypasses REGISTRY skip)
        → triggerEventOn('beforeClassAssign')
          → Box.onBeforeClassAssign
            → useCssInProps(props, element) → ref.__class
              → transformEmotionClass → ref.__classNames
                → clean stale classNames
                  → applyClassListOnNode → node.setAttribute('class', ...)
```

---

## state.replace() vs state.update()

- `state.update()` — merges new values into existing state, triggers re-render
- `state.replace()` — replaces the entire state object, useful for arrays

```js
// For arrays, use replace to ensure proper re-render
onClick: (e, el, s) => s.replace({
  items: [...s.items, 'New Item']
})

// For simple value updates, use update
onClick: (e, el, s) => s.update({
  count: s.count + 1
})
```

---

## scope for Local Instance Data

Use `scope` for data that doesn't need to trigger re-renders:

```js
export const Timer = {
  state: { seconds: 0 },
  scope: {},
  onRender: (el, s) => {
    el.scope.interval = setInterval(() => {
      s.update({ seconds: s.seconds + 1 })
    }, 1000)
  },
  // Access scope from anywhere in the component tree
  Button: {
    text: 'Stop',
    onClick: (e, el) => clearInterval(el.scope.interval),
  },
}
```

---

## Template Strings ({{ }})

Use `{{ key }}` syntax for simple state-to-text binding without a function:

```js
export const Greeting = {
  state: { name: 'World' },
  P: { text: 'Hello, {{ name }}!' },          // Simple binding
  P_2: { text: (el, s) => `Score: ${s.score}` },  // Complex binding
}
```

`{{ key }}` resolves from the element's local state. Use function syntax for
computed values, parent state access, or complex expressions.

---

## External Dependencies

External libraries go in both `package.json` AND `symbols/dependencies.js`:

```js
// dependencies.js
import lottie from 'lottie-web'
import Prism from 'prismjs'

export default { lottie, Prism }
```

Access in components via `el.context.dependencies.lottie`.
