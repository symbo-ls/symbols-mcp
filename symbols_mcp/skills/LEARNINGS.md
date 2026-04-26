# Symbols / DOMQL Runtime — Internal Rules & Gotchas

These are mandatory technical rules for the DOMQL/Symbols runtime. Violating any of them causes silent bugs, missed renders, or incorrect DOM output.

---

## Reactivity Map — what gets a `createEffect` wrapper

`registerEffects` and `applyConditionals` in `packages/element/src/create.js` decide which prop functions are reactive:

| Prop | Reactive? | Notes |
|------|-----------|-------|
| `text` (string with `{{}}` template OR function) | ✅ | Re-renders text when state changes |
| `html` (function) | ✅ | Re-renders innerHTML |
| `value` (function) | ✅ | Re-applies to input/textarea/select; preserves cursor |
| `style` (function) | ✅ | Re-applies whole style object |
| `attr.*` (function-valued) | ✅ | Per-attribute reactive effect |
| `if` (function) | ✅ | Re-evaluates; remove / re-attach DOM node (kills CSS transitions on each toggle) |
| Function values for keys in `CSS_PROPS_REGISTRY` (color, background, padding, gap, fontSize, fontWeight, hide, show, etc.) | ✅ | Each property gets a reactive effect |
| Function values for keys in `DEFAULT_CSS_PROPERTIES_LIST` (raw CSS pass-through props) | ✅ | Each property gets a reactive effect |
| Function values for tag-recognized HTML attributes (src, href, etc.) at root | ✅ | Reactive per-attribute |
| `isX` conditional (function) + `'.isX'` / `'!isX'` blocks | ✅ | Block re-applies whenever the state read by `isX` changes |
| `$isX` global cases from `context.cases` | ✅ | Block re-applies whenever the case condition's reads change |
| `extends` chain | ❌ | Resolved once at element creation |
| Other custom non-CSS function props | ❌ | Tracked in `__exec` but never wrapped — only run on explicit `el.update()` |

### Practical implications

- For grouped reactive CSS that shares one condition, use the `isX` + `'.isX'` / `'!isX'` block pattern. It's the canonical way to express a state-driven appearance change without repeating the same condition across many prop functions.
- For animated show/hide use `hide:` (or `show:`) — these reactively toggle `display`. Using `if:` for animation destroys / re-creates the DOM node which kills CSS transitions.
- Lifecycle hooks (`onInit`, `onCreate`, `onComplete`, `onRender`, `onRenderRouter`) fire ONCE per element creation. To respond to subsequent state changes, use `onUpdate(el, s, ctx)` or `onStateUpdate(changes, el, s, ctx)`, OR (preferred) just declare reactive prop functions and let the framework subscribe.

### Pattern comparison

```js
// ✅ Grouped reactive CSS via .isX (preferred when 2+ props share a condition)
export const Item = {
  background: 'transparent',
  color: 'currentColor',
  isActive: (el, s) => s.active === el.key,
  '.isActive': { background: 'primary', color: 'white' }
}

// ✅ Direct reactive CSS prop functions (also reactive)
export const Item = {
  background: (el, s) => s.active === el.key ? 'primary' : 'transparent',
  color:      (el, s) => s.active === el.key ? 'white' : 'currentColor'
}

// ✅ '!isX' for the inverse branch
export const Row = {
  isSelected: (el, s) => s.selectedId === el.key,
  '.isSelected': { background: 'primary' },
  '!isSelected': { opacity: 0.6 }
}
```

---

## Three router patterns (use Pattern A; B+C are legacy)

Older projects ship with one of three router setups. Pattern A is the canonical form for new work — Patterns B/C exist only for back-compat with legacy projects.

### Pattern A — Empty `app.js` + framework routing (PREFERRED)

Routes defined in `pages/index.js`; framework wires everything via `triggerLifecycle('RenderRouter')` → `onRouterRenderDefault`:

```js
// app.js
export default {}                                  // or { Modals: {} }, root-level chrome only

// pages/index.js
import { home }  from './home.js'
import { about } from './about.js'
export default { '/': home, '/about': about }
```

### Pattern B — Layout + `Folder` nesting (LEGACY)

Inline `define` block, custom `router` function, sets `Top/Cnt/Bottom` slots. Brittle — `Folder.set({ [route]: {...} })` plumbing fails since `el.set()` returns `undefined` today.

### Pattern C — Layout + simple `Content` slot (LEGACY)

Uses `el.call('router', ...)` from `onRender`. **Crashes on every route change** with `Cannot read properties of undefined (reading 'node')` because `el.set()` today returns `undefined` rather than the new element.

**Always prefer Pattern A unless you have a documented reason for custom routing.**

### Anti-patterns to delete on sight

```js
// ❌ Legacy "deployed-mermaid" workaround — remove from any template that still has it.
//    The framework auto-fires onRenderRouter via triggerLifecycle('RenderRouter').
//    setTimeout polling for empty content slot is brittle cargo code.
onRender: (el, s) => {
  setTimeout(() => el.onRenderRouter(el, s), 0)
  setTimeout(() => el.onRenderRouter(el, s), 50)
  setTimeout(() => el.onRenderRouter(el, s), 200)
}

// ❌ Manual polyglot fallback through window.Smbls — also legacy.
//    createDomql.js auto-registers polyglotPlugin when context.polyglot is set.
if (window.Smbls?.polyglotPlugin) ctx.plugins.push(window.Smbls.polyglotPlugin)

// ❌ Capturing click listeners on document — intercept SPA links before router gets them.
document.addEventListener('click', handler, true)
```

### SPA routing rules

- `<a>` tags with `onClick` handlers MUST call `e.preventDefault()`, otherwise the browser does a full page reload.
- Don't add capturing click listeners on `document` — they intercept link clicks before the router gets them.
- Don't roll your own `pushState`/`popstate` plumbing. The framework already wires `onpopstate` via `onpopstateRouter(element, context)`.
- For programmatic nav: `el.router(path, el.getRoot())`. For declarative links: `extends: 'Link', href: '/path'`.

---

## Multi-app isolation — primary vs secondary apps

When multiple apps share a page (canvas + iframe project, editor + preview), each gets full design-system isolation:

### Primary vs secondary detection

`prepareDesignSystem` detects secondary apps via the `_designSystemInitialized` flag and creates an isolated scratch config via `createConfig(key, designSystem, { cleanBase: true })`. Each isolated config has:

- Separate `cssVars` / `cssMediaVars`
- Own `themeRoot` (scoped to app's root element)
- Own `varPrefix` for CSS variable namespacing
- `scopeSelector` = `[data-smbls-app="<key>"]`
- Own `document` (for iframes)

`cleanBase: true` prevents the primary's already-processed tokens from bleeding into secondary apps — without it, an editor's brand theme would override the embedded project's design system.

### `pushConfig` / `popConfig` mechanism

The framework's config stack ensures `getActiveConfig()` returns the right config in every code path:

| Code path | Scoping mechanism |
|-----------|-------------------|
| Element creation (`applyCssInProps`) | `pushConfig(context.designSystem)` at function entry |
| Reactive effects (function-valued CSS props) | `pushConfig` inside each `createEffect` |
| Reactive conditionals (`.X` / `!X` blocks) | `pushConfig` inside the conditional effect |
| Event handlers (delegated + non-delegated) | `pushConfig` in `delegate.js → wrappedHandler` |
| Async event handlers | Config stays pushed until the returned Promise settles via `.finally()` |
| Lifecycle hooks (onCreate, onRender, onMount, …) | `pushConfig` in `triggerLifecycle` |
| `onFrame` loop | `pushConfig` in each `requestAnimationFrame` tick |

**What the framework cannot wrap:** project code that schedules work via `setTimeout`, `setInterval`, or `queueMicrotask` — those create new call stacks with no active config. Capture context up-front instead:

```js
// ❌ Timer callback loses config scope
onClick: (ev, el) => {
  setTimeout(() => {
    el.call('someFunction')   // getActiveConfig() returns global singleton
  }, 100)
}

// ✅ Capture context up-front; access design system, document, window through it
onClick: (ev, el) => {
  const ctx = el.context
  setTimeout(() => {
    // ctx.designSystem, ctx.document, ctx.window are stable references
  }, 100)
}
```

### CSS prefix derivation

Secondary apps auto-derive a single `cssPrefix` from the app key:

```
cssPrefix = key.replace(/[^a-zA-Z0-9]/g, '').substring(0, 6)
```

Used for both atomic class names AND CSS custom properties. Examples:

| Key | cssPrefix | Atomic class | CSS var |
|-----|-----------|--------------|---------|
| `<no key>` (primary) | `''` | `._w-100` | `--theme-X-color` |
| `myapp` | `myapp` | `._myapp_w-100` | `--myapp-theme-X-color` |
| `dashboard` | `dashbo` | `._dashbo_w-100` | `--dashbo-theme-X-color` |
| `client-portal` | `client` | `._client_w-100` | `--client-theme-X-color` |

Primary apps use no prefix → identical output to single-app pages, fully backward compatible.

### `themeRoot` per-app

Each app's `themeRoot` points to its own root element:

```
Primary:    CONFIG.themeRoot = document.documentElement
Secondary:  CONFIG.themeRoot = doc.querySelector(`[data-smbls-app="<key>"]`)
```

`changeGlobalTheme(theme)` writes `data-theme` to `CONFIG.themeRoot`, so each app's active theme is independent.

### CSS injection isolation

`getActiveDocument()` resolves the target document from the active scratch config (`config.document`), set per-app in `prepareDesignSystem`. A per-document `WeakMap` cache in `@symbo.ls/css` ensures each document gets its own `<style data-smbls>` element.

`setActiveDocument(doc)` still exists as a backward-compat shim — new code should use `pushConfig` with a config that already carries `document`.

---

## smbls root app `extends:` does NOT inherit properties

The root element returned by `create(app, context)` (smblsapp) bypasses the key-based auto-extend that children go through. `extends: 'Foo'` at the top level does NOT merge `Foo`'s properties onto the root — only direct properties declared on the root object apply.

```js
// ❌ AppShell properties don't land on root
export default {
  extends: 'AppShell',   // parsed but not merged onto root
  // ...
}

// ✅ Spread a styles object instead
import { appShellStyles } from '.../AppShell.js'
export default {
  extends: 'Page',
  ...appShellStyles,
  // ... app overrides
}
```

Lifecycle behaviors (e.g., `onCreate` path-sync) should be exported as helper functions and registered in `functions/` so each app's `onCreate` calls them via `el.call('installAppShellSync', s)`. Signature: `function (s) { const el = this; ... }` — `el.call` sets `this` to the element.

Component-based `AppShell` with `extends: 'Page'` still works fine for non-root uses (anywhere a child key auto-extends).

---

## Parcel tree-shakes runtime-only shared components — set `sideEffects: true`

A shared-package component referenced ONLY by DOMQL string-key lookup at runtime (e.g. `AppAssistant: {}` at the app root) gets tree-shaken by Parcel. Symptom: an empty `<div data-key="Foo"></div>` with no class names, no children, no merged props.

**Why:** Parcel's dev server runs production-style tree-shaking. When a module is reached through `export *` barrels → `import * as` namespaces and is then accessed only by string-key at runtime (through `sharedLibraries` → `context.components`), the tree-shaker can't prove the export is used and strips it.

**Fix:** Put a `package.json` at the root of the shared package directory with `"sideEffects": true`:

```json
{
  "name": "@symbo.ls/editor-shared",
  "version": "4.0.0",
  "private": true,
  "type": "module",
  "main": "./context.js",
  "sideEffects": true
}
```

After adding, do a full Parcel restart on every downstream app (`rm -rf .parcel-cache dist`, respawn portless) so the module graph re-analyzes under the new `sideEffects` flag.

### Defense-in-depth for overlay components

Even with `sideEffects: true`, any registry-resolution failure causes overlays like `AppAssistant` to fall into normal grid flow. If the shell uses `grid-template-rows: auto 1fr`, a failed-merge `AppAssistant` with `position: static` auto-places into row 2, stealing the `1fr` track. Mitigate by inlining positioning props at the consumer site, not just in the shared component:

```js
AppAssistant: {
  position: 'fixed', top: '0', right: '0',
  height: '100dvh', zIndex: '10000'
}
```

These inline props live in the app's own object literal — never tree-shaken, no registry lookup. If the shared component merges, its definition layers on top. If it doesn't, the element still renders fixed-positioned (just empty) instead of collapsing layout.

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

There are exactly two shape categories. Using the wrong one shifts all parameters silently.

| Event type | Signature | Examples |
|------------|-----------|----------|
| Lifecycle events | `(el, state, context, options?)` | `onInit`, `onAttachNode`, `onCreate`, `onComplete`, `onRender`, `onRenderRouter`, `onUpdate`, `onFrame` |
| State events | `(changes, el, state, context, options?)` | `onBeforeUpdate`, `onStateUpdate`, `onBeforeStateUpdate` (changes is FIRST) |
| DOM events | `(event, el, state)` | `onClick`, `onInput`, `onKeydown`, `onSubmit`, `onMouseover`, `onScroll` |

**Common bug:** Writing `(event, el, s)` in a lifecycle handler. The first arg is actually the element, so `s` becomes `undefined`.

```js
// ✅ CORRECT
onInit:   (el, s, ctx) => {}
onUpdate: (el, s, ctx) => {}
onStateUpdate: (changes, el, s, ctx) => {}
onClick:  (e, el, s) => {}
```

> Flat at BOTH declaration and runtime read: declare `onClick: fn` (NEVER `on: { click: fn }`); read `el.onClick` (NEVER `el.on.click`).

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

## Dynamic HTML Attributes — flat is canonical

The flat (root-level) form is the canonical declaration. The framework still tolerates the legacy `props: {}` wrapper for back-compat (it is flattened onto the element at runtime), but **never write it that way in new code**. Reactive attribute functions work at root level and (rarely) inside `attr: {}` for non-standard attrs:

```js
// ✅ canonical — flat at root
Input: { type: (el, s) => s.inputType }

// 🟡 tolerated for legacy code — props: {} is flattened at runtime; never declare this way in new code
Input: { props: { type: (el, s) => s.inputType } }

// ✅ for truly non-standard attrs only
Input: { attr: { 'x-custom': (el, s) => s.flag } }

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
