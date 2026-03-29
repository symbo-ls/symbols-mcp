# Symbols / DOMQL Runtime — Internal Rules & Gotchas

These are mandatory technical rules for the DOMQL/Symbols runtime. Violating any of them causes silent bugs, missed renders, or incorrect DOM output.

---

## CSS-in-Props Resolution Order

Every property on an element is resolved top-down through this pipeline. The first match wins:

| Priority | Source | Behavior |
|----------|--------|----------|
| 1 (highest) | `element.classlist[key]` | Component-level class definitions |
| 2 | `CSS_PROPS_REGISTRY[key]` | Theme-aware processors (color, border, shadow, hide, etc.) — resolves design tokens |
| 3 | `DEFAULT_CSS_PROPERTIES_LIST.includes(key)` | Raw CSS pass-through — no theme resolution |
| 4 (lowest) | Everything else | Returned as non-CSS props (`rest`) |

**Why this matters:** Only properties routed through `CSS_PROPS_REGISTRY` (priority 2) resolve theme tokens. Shorthand properties like `borderColor` resolve themes, but directional variants (`borderTopColor`) require explicit registry entries or they pass through raw.

---

## CSS Override Precedence

`props` block CSS CANNOT override base component-level CSS. You must override at the same declaration level.

```js
// WRONG — props can't override component-level color
export const MyLink = {
  extends: 'Link',
  props: { color: 'primary' },  // Ignored — Link's component-level color wins
}

// CORRECT — override at the same level
export const MyLink = {
  extends: 'Link',
  color: 'primary',  // Overrides at component level
}
```

This same rule applies to sub-component overrides in nested children.

---

## Event Handler Signatures

There are exactly two signatures. Using the wrong one shifts all parameters silently.

| Event type | Signature | Examples |
|------------|-----------|----------|
| Lifecycle events | `(element, state)` | `onInit`, `onRender`, `onUpdate` |
| DOM events | `(event, element, state)` | `onClick`, `onInput`, `onKeydown` |

**Common bug:** Writing `(event, el, s)` in a lifecycle handler. The first arg is actually the element, so `s` becomes `undefined`.

```js
// CORRECT
onInit: (el, s) => {}
onClick: (event, el, s) => {}
```

---

## HTML Attributes Are Automatic

Do NOT use `attr: {}` for standard HTML attributes. DOMQL's `attrs-in-props` module auto-detects valid attributes for each tag using a database of 600+ attributes.

During element creation, `applyPropsAsAttrs()` calls `filterAttributesByTagName(tag, props, cssPropsRegistry)`. If a property is a valid HTML attribute for that tag AND is not in the CSS properties registry, it automatically becomes `setAttribute()`.

```js
// CORRECT — type, disabled, placeholder all auto-detected
export const MyButton = { tag: 'button', type: 'submit', disabled: true }
export const MyInput = { tag: 'input', type: 'email', placeholder: 'Enter email' }
```

**Use `attr: {}` ONLY for:**
- Custom/non-standard attributes not in the HTML spec
- `data-*` attributes
- ARIA attributes beyond auto-detected ones
- Forcing a property to be an attribute when it would otherwise be interpreted as CSS

```js
export const MyElement = {
  attr: {
    'data-testid': 'my-element',
    'aria-describedby': 'tooltip-1',
  },
}
```

---

## Property Classification (Three Paths)

Every property on a DOMQL element takes exactly one of three paths:

| Path | What matches | Handling |
|------|-------------|----------|
| 1. REGISTRY | `attr`, `style`, `text`, `html`, `data`, `classlist`, `state`, `scope`, `fetch`, `deps`, `extends`, `children`, `content`, `childExtends`, `childExtendsRecursive`, `props`, `if`, `define`, `tag`, `on`, `component`, `context`, `query`, `variables` | Built-in DOMQL properties handled by mixins |
| 2. CSS | 300+ registered CSS properties (`display`, `flexDirection`, `margin`, `padding`, `color`, `background`, `border`, `opacity`, `transform`, `transition`, etc.) | Processed by `css-in-props` via Emotion; theme-aware processors handle tokens |
| 3. HTML attribute | Valid HTML attribute for the element's tag AND not a CSS property | Auto-applied as DOM attribute via `setAttribute()` |

Anything matching none of the three paths stays as a component-level property in DOMQL's internal element tree.

---

## state.root.update() with onlyUpdate

To limit re-rendering to a specific component subtree, pass `onlyUpdate` as the second argument:

```js
onClick: (e, el, s) => {
  s.root.update(
    { activeModal: 'settings' },
    { onlyUpdate: 'ModalCard' }  // Only re-render ModalCard subtree
  )
}
```

**Why:** Without `onlyUpdate`, the entire component tree re-renders on root state change. Use this for performance.

---

## Emotion CSS Class Cleanup

When toggling CSS-in-props values (like `hide`, `opacity`), stale Emotion class names can persist on the DOM. Key facts:

| Scenario | What happens |
|----------|-------------|
| `hide: true` | Generates a class with `display: none !important` |
| `hide` becomes falsy | No class is generated — the old class must be removed |
| Class name format | `smbls-{hash}-{label}` (content-hashed) |

The framework handles cleanup internally, but be aware of this when debugging class-related issues.

---

## Forced Reflow for Transitions

`state.root.update()` applies all Emotion classes in one JS execution block — the browser never paints the intermediate state. To make CSS transitions work, force a reflow with `node.offsetHeight`:

```js
el.node.style.opacity = '0'
el.node.offsetHeight          // Force reflow — browser paints the 0 state
el.node.style.opacity = ''    // Let Emotion class transition take over
```

Do NOT use `requestAnimationFrame` (unreliable timing) or `transitionend` (may not fire if element starts hidden).

---

## Update Cascade Path

This is the exact render cycle triggered by `state.update()`. Use it to debug state/render issues:

```
state.update()
  -> applyElementUpdate
    -> element.update({}, { updateByState: true })
      -> for (param in element): update children recursively
      -> update content element explicitly (bypasses REGISTRY skip)
        -> triggerEventOn('beforeClassAssign')
          -> Box.onBeforeClassAssign
            -> useCssInProps(props, element) -> ref.__class
              -> transformEmotionClass -> ref.__classNames
                -> clean stale classNames
                  -> applyClassListOnNode -> node.setAttribute('class', ...)
```

---

## preventFetch Option in state.update()

When a `fetch` plugin is configured on the root state, **every** `state.root.update()` call re-triggers the fetch unless you opt out. For UI-only state changes (opening modals, toggling menus, changing language, etc.) always pass `{ preventFetch: true }`:

```js
// ❌ Re-triggers data fetch — wrong for UI-only changes
onClick: (e, el, s) => s.root.update({ activeModal: true })

// ✅ UI-only — fetch plugin skipped
onClick: (e, el, s) => s.root.update({ activeModal: true }, { preventFetch: true })
```

**When to omit `preventFetch`:** Only when the state change should re-fetch data (e.g., changing a filter, page number, or search query).

---

## Animated Show/Hide — opacity vs show

`show: false` sets `display: none`, which **prevents CSS transitions**. For any element that needs to animate in or out, use `opacity + pointerEvents + transition + transform` instead:

```js
// ❌ Instant — no transition possible
Dropdown: {
  show: (el, s) => s.root.dropdownOpen,
  ...
}

// ✅ Smooth fade + slide
Dropdown: {
  opacity: (el, s) => s.root.dropdownOpen ? '1' : '0',
  pointerEvents: (el, s) => s.root.dropdownOpen ? 'auto' : 'none',
  transition: 'opacity 0.2s ease, transform 0.2s ease',
  transform: (el, s) => s.root.dropdownOpen ? 'translateY(0)' : 'translateY(-6px)',
}
```

Use `show` only for elements that should be completely removed from layout (no animation needed). For modals, dropdowns, tooltips, and any element with a visible open/close state — use the opacity pattern.

---

## state.replace() vs state.update()

| Method | Behavior | Use when |
|--------|----------|----------|
| `state.update()` | Merges new values into existing state, triggers re-render | Updating individual properties |
| `state.replace()` | Replaces the entire state object | Replacing arrays or resetting state entirely |

```js
// Arrays: use replace to ensure proper re-render
onClick: (e, el, s) => s.replace({
  items: [...s.items, 'New Item']
})

// Simple values: use update
onClick: (e, el, s) => s.update({
  count: s.count + 1
})
```

---

## scope for Local Instance Data

`scope` holds data that does NOT trigger re-renders. Use it for timers, refs, caches, and any mutable data that should not cause UI updates.

```js
export const Timer = {
  state: { seconds: 0 },
  scope: {},
  onRender: (el, s) => {
    el.scope.interval = setInterval(() => {
      s.update({ seconds: s.seconds + 1 })
    }, 1000)
  },
  Button: {
    text: 'Stop',
    onClick: (e, el) => clearInterval(el.scope.interval),
  },
}
```

`scope` is accessible from anywhere in the component tree via `el.scope`.

---

## Template Strings

Use `{{ key }}` syntax for simple state-to-text binding without a function. It resolves from the element's local state.

```js
export const Greeting = {
  state: { name: 'World' },
  P: { text: 'Hello, {{ name }}!' },              // Simple binding
  P_2: { text: (el, s) => `Score: ${s.score}` },  // Complex binding
}
```

Use function syntax instead when you need: computed values, parent/root state access, or complex expressions.

---

## External Dependencies

External libraries must be declared in BOTH `package.json` AND `symbols/dependencies.js`:

```js
// symbols/dependencies.js
import lottie from 'lottie-web'
import Prism from 'prismjs'

export default { lottie, Prism }
```

Access in components via `el.context.dependencies.lottie`. Missing the `dependencies.js` export means the library is installed but invisible to components.

---

## Symbols Module Architecture

### Core Runtime

| Package | Purpose |
|---------|---------|
| `@domql/element` | Core element system — create, update, render, destroy, and all mixins (attr, style, text, html, data, classList, state, scope) |
| `@domql/state` | Reactive state management — update, replace, toggle, parent/root state access |
| `@domql/utils` | Shared utilities — propertizeElement, object manipulation, element creation helpers |
| `domql` | Main DOMQL library entry point (bundles element, state, utils) |

### Styling & Attributes

| Package | Purpose |
|---------|---------|
| `css-in-props` | CSS-in-props system with 300+ CSS property registry and Emotion-based styling. Handles theme-aware processors for colors, spacing, borders, shadows |
| `attrs-in-props` | HTML attribute validation and filtering by tag name. Database of 600+ valid HTML attributes per tag — ensures only valid attrs become DOM attributes |
| `scratch` | CSS framework and methodology (Phi-notation spacing system) |

### UI Components

| Package | Purpose |
|---------|---------|
| `@symbo.ls/uikit` | Pre-built UI components: Button, Input, Select, Dialog, Avatar, Icon, Range, Dropdown, Notification, Link, Tooltip — all built on DOMQL atoms |

### Build & Tooling

| Package | Purpose |
|---------|---------|
| `smbls` | Main Symbols package — runtime entry point |
| `cli` | CLI for project management (`smbls start`, `smbls build`, `smbls create`) |
| `runner` | Build runner and toolchain (Parcel integration) |
| `create` / `create-smbls` | Project scaffolding and creation |
| `frank` | Bidirectional transformation between Symbols project JSON and filesystem formats |
| `preview` | Development preview server |

### Data & Sync

| Package | Purpose |
|---------|---------|
| `state` | State management package |
| `sync` | Real-time bidirectional sync with Express/Socket.io |
| `icons` | Icon system and icon set management |
| `default-config` | Default configuration for new projects |

### Element REGISTRY — All Built-in Properties

These properties are handled internally by DOMQL. They are NOT passed to DOM or CSS:

```
attr, style, text, html, data, classlist, state, scope, fetch, deps,
extends, children, content, childExtends, childExtendsRecursive,
props, if, define, tag, query, on, component, context, variables,
__name, __ref, __hash, __text, key, parent, node
```

Any property NOT in this registry, NOT a CSS property, and NOT a valid HTML attribute for the tag stays as a component-level property in DOMQL's internal element tree.

---

## Dynamic HTML Attributes — Three Equivalent Paths

Dynamic (function) attribute values work at root level, inside `props:`, and inside `attr: {}`. All three paths call `exec()` on function values — they are executed, not stringified:

```js
// All three are equivalent — all work correctly:
Input: { type: (el, s) => s.inputType }                    // root level
Input: { props: { type: (el, s) => s.inputType } }         // inside props
Input: { attr: { type: (el, s) => s.inputType } }          // inside attr

// Flow: root/props → filterAttributesByTagName → element.attr → exec() → setAttribute
```

`data-*` and `aria-*` are also auto-detected at root/props level via attrs-in-props:
- camelCase conversion: `ariaLabel` → `aria-label`, `dataTestId` → `data-test-id`
- Shorthand objects: `aria: { label: 'foo', expanded: true }`, `data: { testId: 'bar' }`

Use `attr: {}` only for truly custom attributes not recognized by the attrs-in-props database.

---

## Polyglot Translation Patterns

Use `{{ key | polyglot }}` template syntax for static text. When template strings don't work (inside children state data or function returns), use `el.call('polyglot', key)`:

```js
// ✅ Template syntax (static text)
Button: { text: '{{ submit | polyglot }}' }

// ✅ Dynamic context (children, functions)
text: (el, s) => el.call('polyglot', 'itemCount') + ': ' + s.items.length
```

---

## hide vs display: 'none'

Use `hide:` to conditionally hide elements, never `display: 'none'`. The `display` property gets overridden by CSS classes from component extends (e.g. Flex sets `display: flex`). The `hide` property generates `display: none !important` which takes priority:

```js
// ❌ Gets overridden by extends CSS
Sidebar: { display: (el, s) => s.open ? 'flex' : 'none' }

// ✅ Correct — hide generates display:none !important
Sidebar: { hide: (el, s) => !s.open }
```

Use `hide` for toggling visibility. Use `if` for removing from DOM entirely. For animated show/hide, use the opacity pattern (see COMMON_MISTAKES #16).
