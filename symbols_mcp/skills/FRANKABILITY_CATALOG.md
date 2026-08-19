# Frankability Catalog — every `@symbo.ls/frank-audit` rule

**Auto-generated** by `bin/sync-frankability-catalog` from `frank-audit explain`.
Do not edit by hand — re-run the script after upgrading `@symbo.ls/frank-audit`.

For deeper conceptual context on the most-used rules, see `FRANKABILITY.md`.
This file is the exhaustive reference: brief explainer + bad/good examples per
rule, lifted verbatim from the CLI source-of-truth.


---

## FA0xx — Project structure & imports

# FA001 — sibling-import

## Safety

The fix only drops the import if the symbol is resolvable elsewhere
(re-exported from `functions/index.js`, `methods/index.js`, declared
in `globalScope.js`, or registered as a PascalCase component key).
Otherwise the finding is left for the human to resolve — dropping
a sibling import without a fallback would leave a dangling
`ReferenceError` at module-load time.

Root-level config files (`config.js`, `state.js`, `lang.js`, `vars.js`,
`cases.js`, `globalScope.js`, `envs.js`, `schema.js`) are exempt — they
legitimately import sibling root files for configuration composition.


Symbols projects rely on the framework to compose components and resolve
functions at runtime. Importing one project file from another:

  - couples the source layout to the runtime resolution
  - prevents frank from serializing the project (the bundler inlines
    the imported file into the importing one)
  - leaks framework-private state across file boundaries

## Fix

  - For component references: drop the import and use `extends: 'Name'`
    or just name the child key after the registered component.
  - For functions: drop the import and call via `el.call('fnName', ...)`
    (or `this.call(...)` inside lifecycle methods).
  - For shared helpers/constants: move them to `globalScope.js`
    and reference them as bare identifiers — frank wires the resolution.

Files where sibling imports remain legal:
  index.js, context.js, app.js, dependencies.js, sharedLibraries.js,
  config.js, state.js, lang.js, cases.js, vars.js, globalScope.js,
  envs.js, schema.js

# FA006 — orphan-file

frank.toJSON walks only the canonical project slots:

  components/  pages/  functions/  methods/  snippets/
  designSystem/  files/  assets/

Files in any other folder (utils/, lib/, helpers/, services/, ...) are
silently dropped from the published JSON. The local dev server still
sees them via normal JS imports — local works, prod is missing the code.

## Fix

Sub-folder orphans are auto-moved to `functions/`. If the exports are
method-style (require `this`-binding), pass `--rule FA006` and move the
file manually into `methods/` instead.

Root-level orphans (a misnamed file at symbols/ root) are surfaced but
not auto-moved — they need a rename decision a human should make.

# FA007 — namespaced-component-reexport

`components/index.js` is the component registry. The framework merges
every NAMED export from the index into the global component map. When
you wrap a re-export with `as`:

  export * as Button from './Button.js'

the registry sees a single name `Button` whose value is a namespace
object — components inside the namespace are unreachable.

## Fix

  export * from './Button.js'

so each named export inside `Button.js` lands in the registry directly.

# FA008 — incomplete-index

## Safety

Sibling files that have parse errors OR declare no named exports are
NOT auto-added to the index. Including a parse-broken file in the
bundle would propagate the error to every consumer; including an
empty file pollutes the registry with undefined bindings. Use
`FRANK_AUDIT_VERBOSE=1` to see which siblings were skipped and why.


Each canonical sub-folder (components, snippets, functions, methods)
must have an `index.js` that re-exports every sibling .js file. Files
not re-exported are invisible to frank.toJSON and dropped from the
published payload.

## Fix

frank-audit regenerates the index by appending

  export * from './<filename>'

for every missing sibling. The fix preserves any existing entries and
comments above them.

For a brand-new folder with no `index.js` at all, the file is created
with re-exports for every sibling.

# FA009 — name-mismatch

Component / snippet files should export a single value whose name
matches the filename. Mismatches break the auto-registry — the file
system suggests one name; the registry binding sees another.

Examples:

  Header.js   →   export const Header = { ... }   ✓
  Header.js   →   export const HeaderBar = { ... } ✗

The audit reports these but does not auto-fix because rename direction
(rename the file vs rename the export) is a design call, not a
mechanical one.

# FA010 — missing-context

Every Symbols project should ship a hand-written `context.js` at the
project root that aggregates its modules into the bundle entry frank
reads during publish. When the file is missing, frank falls back to a
synthetic entry built from a hard-coded module list — fragile by nature,
and the source of several "works on parcel CSR but breaks on mermaid SSR"
incidents.

## Fix

The autofix scaffolds a baseline `context.js` that re-exports whichever
slots are present on disk. Hand-edit afterwards if the project layout
is non-standard (custom slot names, deferred imports, etc.).

Template:

```js
import * as components from './components/index.js'
import * as functions from './functions/index.js'
import * as globalScope from './globalScope.js'
import designSystem from './designSystem/index.js'
import pages from './pages/index.js'
import state from './state.js'
import config from './config.js'

export default {
  ...config, state, components, pages, functions, globalScope, designSystem
}
```


---

## FA1xx — Flat element API

# FA101 — flat-element-access

There is no `.props` wrapper on the element. Every prop a component
declares is flat on the element itself.

Bad:    `el.props.value`     `el.props.text`     `el.props.src`
Good:   `el.value`           `el.text`           `el.src`

This applies to runtime ACCESS (reading the prop off the element).
For declaration-side flattening (the `props: { ... }` wrapper key in
a component literal), see FA103.

# FA102 — flat-event-access

Every event handler is a flat `onX` prop on the element. There is no
`.on` namespace.

Bad:    `el.on.click()`         `el.on.init`
Good:   `el.onClick()`          `el.onInit`

See FA104 for declaration-side flattening of `on: { event: fn }` keys.

# FA103 — props-wrapper

Every prop a component declares lives directly on the component
object — there is no `props: { ... }` envelope.

Bad:
  Card: {
    props: {
      padding: 'A',
      color: 'blue'
    },
    Title: {}
  }

Good:
  Card: {
    padding: 'A',
    color: 'blue',
    Title: {}
  }

See FA101 for runtime-access flattening (`el.props.X` → `el.X`).

# FA104 — on-wrapper

Event handlers are flat top-level keys named `onEvent`. There is no
`on: { ... }` envelope.

Bad:
  Button: {
    on: {
      click: (e, el) => { ... },
      init: (el, s) => { ... }
    }
  }

Good:
  Button: {
    onClick: (e, el) => { ... },
    onInit: (el, s) => { ... }
  }

Strings like `on: 'click'` are the FA107 case (handler-name reference).

# FA105 — attr-wrapping-flat

DOMQL surfaces most HTML attributes as flat top-level props. Wrapping
them in `attr: { ... }` adds noise without changing behavior.

Bad:
  Input: {
    attr: {
      placeholder: 'Search...',
      type: 'search',
      value: ''
    }
  }

Good:
  Input: {
    placeholder: 'Search...',
    type: 'search',
    value: ''
  }

The `attr: { ... }` wrapper is reserved for attributes that are NOT
exposed as flat props — rare edge cases. The audit only flattens known
flat attrs and leaves anything else inside `attr:` untouched.

# FA106 — handler-destructure-signature

Reactive prop functions and event handlers receive `(el, s)`. Legacy
code destructures an envelope:

Bad:    `text: ({ state }) => state.title`
        `onClick: ({ key, state }) => state.update({ active: key })`
Good:   `text: (el, s) => s.title`
        `onClick: (e, el, s) => s.update({ active: el.key })`

The audit rewrites the signature and patches every destructured field
access in the body. If a body uses fields the audit does not recognize
(e.g. `({ unusual })`), the function is left untouched and surfaced as
advisory.

# FA107 — stringy-event-registration

A component literal that declares `on: 'click'` or
`on: ['init', 'render']` is using the legacy event-binding shape:
name the events as strings, attach handlers elsewhere.

Handlers are bound in one place:

  Button: {
    onClick: (e, el) => { ... }
  }

The audit reports these but does not auto-fix because synthesizing the
handler body requires intent. Open the file, find the legacy-style
handler attached to this component, and inline it as `onEvent: fn`.

# FA108 — style-wrapping-flat

DOMQL handles every standard CSS property as a flat top-level prop
with design-token resolution and theme-aware shorthand expansion.
Putting CSS inside `style: { ... }` short-circuits all of that —
`style:` is a raw HTML attribute pass-through, not a DOMQL prop.

Two failure modes when CSS is wrapped in `style:`:

  1. Design tokens stop resolving:
       Bad:    style: { width: 'B1', height: 'B1' }
       Result: <img style="width:B1; height:B1"> (invalid CSS,
               element falls back to intrinsic size)
       Good:   width: 'B1', height: 'B1'
       Result: width and height resolve through the spacing scale

  2. Theme-aware colors stop resolving:
       Bad:    style: { color: 'caption', background: 'card' }
       Good:   color: 'caption', background: 'card'

## When `style:` IS appropriate

  - Vendor-prefixed CSS that DOMQL doesn't expose:
      style: { WebkitTapHighlightColor: 'transparent' }
  - Custom CSS variables (`--my-var`):
      style: { '--card-accent': 'red' }
  - Per-instance literal CSS where you explicitly want to bypass
    DOMQL's transformer (rare).

The audit only hoists keys it knows DOMQL handles flat — anything
unknown stays inside `style:` untouched.

# FA109 — no-param-state-factory

Smbls invokes state factories as `stateDef(element, parent?.state)`.
A state factory with NO parameters cannot receive `element`, and
arrow functions IGNORE `this` from `.call()` (lexically bound).

Bad (works in dev, breaks under mermaid/brender SSR):

  const docPage = (providerKey) => ({
    scope: { providerKey },
    Header: {
      extends: "DashHeader",
      state: () => ({
        title: 'Connect ' + providerKey
      })
    }
  })

Good (static — resolved at factory call time):

  const docPage = (providerKey) => ({
    Header: {
      extends: "DashHeader",
      state: {
        title: 'Connect ' + providerKey
      }
    }
  })

Good (reactive — rewrite signature to receive element):

  Header: {
    extends: "DashHeader",
    state: (el) => ({
      title: 'Connect ' + el.scope.providerKey
    })
  }

The audit auto-fixes static bodies (no closure dependencies) by
unwrapping the arrow. Bodies that read identifiers (factory params,
module-scope vars) are surface-only — the right fix depends on
whether you want per-call-time static resolution or runtime
reactivity. Pick:

  • Static (call-time):  state: { ... } — value is baked in
  • Reactive (runtime):  state: (el) => ({...el.scope.X...})

See also FA205 (factory-closure) which adds scope:{} declarations
to factory return objects so the inner factories can resolve at
runtime — both rules together cover the full closure-loss surface.


---

## FA2xx — DOMQL syntax & scope movers

# FA201 — mutable-module-state

A `let`/`var` declared at module scope of a component file and read or
written inside a handler captures the binding. After frank serializes
the handler, the captured binding is gone — handler reads return
undefined, writes silently disappear.

frank ships with a runtime workaround (`Smut`) that wraps mutable
globalScope entries in an object reference so writes survive the
serialize/destringify roundtrip. That workaround only triggers for
values that live in `globalScope.js`.

## Fix

The audit moves the `let`/`var` to `globalScope.js` and removes it from
the source file. The handler keeps its bare identifier reference; frank
rewrites it to `__scope.Smut.<name>` at toJSON time.

Example:

  // before — components/GameCanvas.js
  let containerEl = null
  export const GameCanvas = {
    onRender: (el) => { containerEl = el }
  }

  // after — globalScope.js gains:
  export default { containerEl: null }

  // after — components/GameCanvas.js
  export const GameCanvas = {
    onRender: (el) => { containerEl = el }
  }

# FA202 — multifile-helper

A function declared with `const fn = (...) => ...` (or `function fn`)
at the module scope of one file but referenced from 2+ files is shared
infrastructure. Two costs of leaving it inline:

  - Other files must `import` it, which FA001 forbids.
  - frank inlines it once per importing file at bundle time, bloating
    the JSON payload and breaking identity equality across consumers.

## Fix

Move the function to `globalScope.js`. Every consumer references it
as a bare identifier; frank wires the resolution at toJSON time.

For helpers used in only ONE file, see FA204 (inline as `el.scope`).

# FA203 — multifile-constant

Constants shared across files (game tuning values, color hex tables,
route paths, copy strings, etc.) belong in `globalScope.js`. Inlining
them in one file forces every other consumer to either import the
sibling (forbidden — FA001) or duplicate the value.

## Fix

The audit moves the `const X = …` to `globalScope.js` and removes it
from the source. Every reference stays a bare identifier; frank
rewrites them at toJSON time.

For constants used in only ONE component, see FA204 (inline as
`el.scope` so the value travels with the element).

# FA204 — single-component-const

A constant used by exactly one component is best inlined as a
`scope: { name: value }` block on that component. Two reasons:

  - The value serializes with the element naturally (no globalScope
    indirection, no Smut wrapping, no scope-rewriter step).
  - The component's source becomes self-contained — readers can see
    the constant next to where it is used.

## Fix

The audit moves

  const MAX_SLIDES = 24
  export const Lightbox = { text: (el) => MAX_SLIDES + " slides" }

into

  export const Lightbox = {
    scope: { MAX_SLIDES: 24 },
    text: (el) => el.scope.MAX_SLIDES + " slides"
  }

Bare references inside handlers stay bare; frank rewrites them to
`el.scope.MAX_SLIDES` at toJSON time.

# FA205 — factory-closure

A factory function that returns a component object literal whose
handlers reference factory parameters silently breaks under frank:

  const navTab = (path) => ({
    color: () => path === currentPath ? 'blue' : 'gray'
  })

frank stringifies `color: () => …`, the closure over `path` is gone,
and `path` is undefined when the handler runs — wrong color, silently.

## Fix

The audit emits `scope: { path }` on the returned object so the value
travels with the element through serialization:

  const navTab = (path) => ({
    scope: { path },
    color: () => path === currentPath ? 'blue' : 'gray'
  })

Bare `path` references inside the handler stay bare; frank rewrites
them to `el.scope.path` at toJSON time.

# FA206 — npm-import-in-handler

frank externalizes runtime packages (React, Supabase, lodash, ...) at
bundle time so the JSON payload stays small. Static top-of-file
imports of external packages used inside handler bodies trigger
frank's runtime async-import workaround — works, but the rewrite
happens silently and adds an `await import(...)` round-trip on every
handler call.

Doing the dynamic-import explicitly in source keeps local-dev and
production execution paths identical:

  // before
  import { Chart } from 'chart.js'
  export const ChartView = {
    onRender: async (el) => { new Chart(el.node, ...) }
  }

  // after
  export const ChartView = {
    onRender: async (el) => {
      const { Chart } = await import('chart.js')
      new Chart(el.node, ...)
    }
  }

The audit reports these but does not auto-fix because rewriting an
import that's destructured into multiple bindings or used in
module-top-level code requires a call-graph trace.


---

## FA3xx — Design-system tokens

# FA301 — hex-color

Color props must reference design-system tokens, never raw hex.

Bad:    color: '#3a86ff'
Good:   color: 'primary'   color: 'blue.7'   color: 'gray+50'

The audit cannot pick the right token automatically — open
designSystem/color.js, find the token whose value matches the hex
(or define a new token), and reference it by name.

# FA302 — rgb-color

rgb() / rgba() literals belong in designSystem/color.js, not in
component prop values. Reference the token by name.

Bad:    background: 'rgba(0, 0, 0, 0.5)'
Good:   background: 'overlay'   background: 'black+50'

# FA303 — hsl-color

hsl() / hsla() literals belong in designSystem/color.js, not in
component prop values. Reference the token by name.

# FA304 — raw-px-rem

Spacing, sizing, typography, and timing props use design-system tokens.
Raw px/rem literals bypass the token scale and break responsive scaling.

Bad:    padding: '16px'      fontSize: '14px'      borderRadius: '4px'
Good:   padding: 'B'         fontSize: 'A'         borderRadius: 'A'

For fixed-dimension UI primitives (avatars, icons, hairline borders, thumbnails)
a raw px value may have no close equivalent in the spacing scale. When a project
has designSystem/sizes.js, FA304 will suggest the matching sizes token instead
of a spacing letter:

Bad:    width: '48px'       height: '1px'        boxSize: '24px'
Good:   width: 'avatarMd'   borderWidth: 'hairline'   boxSize: 'iconLg'

Resolution priority:
1. If the project has designSystem/sizes.js and there is an exact pixel match,
   use that token (e.g. 'avatarMd' for 48px).
2. Otherwise find the closest spacing-scale letter (e.g. 'C' for ~42px).
3. If no token is within 10% and no sizes token matches, add the needed token to
   designSystem/sizes.js (for fixed UI primitives) or adjust the spacing
   base/ratio (for layout tokens).

See DESIGN_SYSTEM.md § sizes for the full default token catalog.


---

## FA4xx — Fix-time rules

# FA401 — window-location

Navigation routes through the framework's router. Setting
`window.location.href`, calling `window.location.assign` or
`window.location.replace` bypasses the router and tears down state
incorrectly.

Bad:    window.location.href = '/dashboard'
        window.location.assign('/login')
Good:   el.router('/dashboard', el.getRoot())
        el.router('/login', el.getRoot())

For programmatic redirects from a non-element scope, plumb `el` through
a function and call `el.router(...)` from there.

# FA402 — window-fetch

Network access is owned by the framework. Direct `window.fetch` calls
bypass cancellation, error capture, SSR hydration, and the data layer.

Bad:    onClick: (e, el) => window.fetch('/api/save', { ... })
Good:   onClick: (e, el) => el.call('saveCard', el.value)
        // and saveCard lives in functions/ doing the fetch

For data-bound components prefer the declarative `fetch:` prop
from @symbo.ls/fetch.

# FA403 — axios-call

Same problem as FA402 (window.fetch) — direct HTTP from handlers
bypasses the framework data layer.

See FA402 for the declarative `fetch:` prop pattern.

# FA404 — xhr

XMLHttpRequest and jQuery $.ajax are legacy network APIs that bypass
the framework's data layer. See FA402 for the declarative `fetch:`
prop pattern.

# FA405 — document-title

Page-level metadata is owned by @symbo.ls/helmet. Setting
`document.title` directly or appending into `document.head` bypasses
helmet, breaks SSR hydration, and confuses tab/history state.

Bad:    document.title = 'Dashboard'
Good:   metadata: { title: 'Dashboard' }     // on the page component

# FA406 — data-theme-write

Theme activation is a framework concern — only the framework writes
`data-theme` on the scope root, and only via `changeGlobalTheme()`.

Bad:    document.documentElement.setAttribute('data-theme', 'dark')
Good:   import { changeGlobalTheme } from 'smbls'
        changeGlobalTheme('dark')

Direct attribute writes diverge from CONFIG.globalTheme, skip the
cssVars regeneration, and break the preview-editor sync.

# FA407 — prefers-color-scheme

OS-theme resolution is owned by the framework. Project code does NOT
read `prefers-color-scheme` directly — instead, declare CSS-in-props
`@dark` / `@light` blocks and the framework will:

  - emit `[data-theme="dark"] &` for forced themes
  - emit `@media (prefers-color-scheme: dark) :root:not([data-theme]) &`
    for the OS-following auto mode

Bad:
  if (matchMedia('(prefers-color-scheme: dark)').matches) { ... }
Good:
  Card: { background: 'white', '@dark': { background: 'gray.9' } }

# FA408 — invalid-polyglot-fn

The only registered translation function is `polyglot`. The audit sees
calls to `t`, `tr`, `i18n`, `__t`, `_t` — typically carry-overs from
i18next / lingui / formatjs / gettext.

Bad:    el.call('t', 'login.button')
Good:   el.call('polyglot', 'login.button')
        text: '{{ login.button | polyglot }}'    // template form

These calls fail silently — `el.call` looks up the function in the
project's `functions/` registry and returns undefined when the name
isn't registered.

# FA409 — window-assignment

Symbols projects must not expose state on the global object. Writes
like `window.smblsApp = ...` or `window.platformState = ...` couple
framework internals to `window`, break SSR, and let any other script
silently mutate or observe the value.

Use the framework element tree:

  Bad:    window.smblsApp = { state: context.state }
  Bad:    window.platformState = state
  Bad:    globalThis.config = { ... }

  Good:   const root = el.getRootState()                 // what 'state' was
  Good:   const ctx  = el.context                        // assembled context
  Good:   el.context.globalScope.myThing = ...           // long-lived shared data

For boot-time bridges that need to run before any element exists,
declare a function in `functions/` and accept `el` as the first arg —
the framework calls it during create() and you receive the element
graph naturally.


---

## FA5xx — Banned runtime APIs & frank-serialization

# FA501 — query-selector

DOM queries are replaced by DOMQL's tree-walking helpers:

Bad:    document.querySelector('.modal')
        document.querySelectorAll('button')
Good:   el.lookdown('Modal')
        el.lookdownAll('Button')

Use `el.lookup('Key')` to walk up the tree, `el.lookdown('Key')` for
descendants. Both reference component keys, not CSS selectors.

# FA502 — get-element-by-id

Bad:    document.getElementById('modal-root')
Good:   el.lookdown('ModalRoot')

# FA503 — add-event-listener

Bad:    el.node.addEventListener('click', handler)
Good:   onClick: (e, el) => handler(e, el)    // on the component itself

Bad:    document.addEventListener('click', handler)   // foreign portal / outside-click
Good:   onDocumentClick: (e, el, s) => handler(e, el) // document-level, DOMQL-owned lifecycle
        onDocumentKeydown: 'closeOnEscape'              // string shortcut → el.call
        onDocumentPointerdown: { capture: true, handler } // options: capture / passive / once
Bad:    window.addEventListener('resize', handler)
Good:   onWindowResize: (e, el, s) => handler(e, el)   // window-level sibling, same shapes

Flat `onEvent` handlers are tracked by DOMQL's lifecycle and are
cleaned up automatically when the element unmounts. `onDocumentXxx` /
`onWindowXxx` (PORTAL-EVENTS-PRIMITIVE-1) extend that to events that never
reach an element the project owns — third-party widgets portaled into
document.body, outside-click / Escape for layers, window resize/scroll:
registered once when the element gets its node, inert while `if:`-hidden,
torn down in dispose(). Raw addEventListener stays banned everywhere —
every receiver now has a sanctioned flat prop.

# FA504 — classlist-mutation

Class state is data-driven, not imperative.

Bad:    el.node.classList.add('active')
Good:   isActive: (el, s) => s.activeId === el.key
        // matching `.isActive: { ... }` style block on the component

For classes that do not follow the `isX` convention:
        class: { highlighted: (el, s) => s.flag }

# FA505 — inner-html-write

Bad:    el.node.innerHTML = '<b>Hi</b>'
Good:   text: 'Hi'                             // auto-escaped, preferred
        html: '<b>Hi</b>'                      // raw, when truly needed

Both `text:` and `html:` re-render correctly when their value
changes — direct innerHTML mutation does not.

# FA506 — set-attribute

Attributes are flat top-level props on the component (placeholder,
type, name, value, disabled, ...). Setting them imperatively bypasses
DOMQL's diffing and breaks reactive updates.

Bad:    el.node.setAttribute('aria-expanded', 'true')
Good:   'aria-expanded': (el, s) => String(s.open)

# FA507 — remove-attribute

Bad:    el.node.removeAttribute('disabled')
Good:   disabled: (el, s) => s.locked || null    // null removes the attr

# FA508 — append-child

Bad:    parentEl.node.appendChild(childEl.node)
Good:   declare the child as a key on the parent component, or use
        children: [...] + childExtends: when the list is dynamic

# FA509 — remove-child

Bad:    parentEl.node.removeChild(child.node)
Good:   Child: { if: (el, s) => s.show }

When the predicate flips false the framework unmounts the child. When
it flips back true the child re-mounts cleanly.

# FA510 — insert-before

Bad:    parent.node.insertBefore(newEl.node, anchor.node)
Good:   children: [...] on the parent — DOMQL renders in array order

# FA511 — el-node-write

Reading `el.node` (for measurement, focus, scroll, observers, ...) is
fine. Writing to it bypasses DOMQL diffing — the next render
overwrites the imperatively-set value.

Bad:    el.node.value = ""
        el.node.style.color = 'red'
        el.node.textContent = 'updated'
        el.node.innerHTML = '...'
Good:   value: ""                         // resets via the prop
        color: 'red'                      // CSS-in-props
        text: 'updated'                   // text prop, reactive
        html: '...'                       // raw markup prop

# FA512 — dom-traversal

DOM traversal lives on the DOMQL element, not on the raw node.

Bad:    el.node.parentNode
        el.node.childNodes
        el.node.nextSibling
Good:   el.parent
        el.lookdown('Key')
        el.nextElement()
        el.previousElement()

# FA513 — window/document update misuse

`.update({...})` is a DOMQL element method. It does NOT exist on the
native `window` or `document` globals — no smbls package adds it.
Calling these throws `TypeError: <target>.update is not a function`
at runtime, breaking the surrounding component.

Common origins:
  - v2/v3 migration where the author guessed at an API that never
    existed (the only similar v3 helper was `el.update`).
  - Copy-paste from documentation that meant `el.update` but the
    code substituted `window` because the handler runs at
    document/window scope.

Fixes by context:

  1. Window-level events (scroll, resize, popstate, beforeunload):

       Bad:    window.update({ onScroll: onScroll })
       Good:   declare onScroll on the page/root component, OR
               window.addEventListener("scroll", onScroll, { passive: true })
               from a functions/ helper invoked via el.call("setup")

  2. DOM ref (querySelector result, el.node, sibling ref):

       Bad:    minInput.update({ value: '' })
       Good:   minInput is the wrong reference — call `.update` on
               the OWNING DOMQL element instead: el.update({ value: '' })

Frank-audit doesn't auto-fix this — the right replacement depends on
whether you want the framework event-delegation path or an
imperative listener.


---

## FA6xx — Lifecycle & events

# FA601 — svg-tag

Icons live in `designSystem/icons` and are rendered via the `Icon`
component. Inline `<svg>` markup bypasses the design system, breaks
theme-aware color resolution, breaks SSR, and breaks brender hydration.

Bad:    Logo: { tag: 'svg', html: '<path .../>' }
Good:   Logo: { extends: 'Icon', name: 'logo' }
        // matching `logo: { svg: '<path .../>' }` in designSystem/icons.js

# FA602 — path-tag

Same problem as FA601 — see that rule for the migration pattern.

# FA603 — inline-svg-html

Inline SVG via `html:` for icons bypasses designSystem.icons, breaks
theme color resolution, breaks SSR, and breaks brender hydration.

Bad:    Logo: { html: '<svg ...><path .../></svg>' }
Good:   Logo: { extends: 'Icon', name: 'logo' }
        // and `logo: { svg: '<path .../>' }` in designSystem/icons.js

# FA604 — svg-extends-with-html

extends: 'Svg' is for decorative or structural SVG (background shapes,
patterns, illustrations). For ICONS use the Icon component, which
reads designSystem.icons by name and resolves theme colors correctly.

Bad:    Logo: { extends: 'Svg', html: '<path .../>' }
Good:   Logo: { extends: 'Icon', name: 'logo' }


---

## FA7xx — State

# FA701 — hardcoded-english-text

Strings displayed to the user typically need to flow through the
polyglot pipeline so other locales render correctly.

Bad:    placeholder: 'Search across everything'
        text: 'Welcome back to your dashboard'
Good:   placeholder: '{{ search.placeholder | polyglot }}'
        text: el.call('polyglot', 'dashboard.welcome')

Heuristic only — single-word labels and intentionally untranslated
product names should be left as-is (allow with `// @symbols allow polyglot`).


---

## FA8xx — Pages & routing

# FA801 — page-must-extend-page

Every file under pages/ must extend 'Page', either directly:

  Dashboard: { extends: 'Page', ... }

in array form combined with another base:

  Dashboard: { extends: ['Page', 'AppLayout'], ... }

or through a layout that itself extends Page:

  // components/AppLayout.js: { extends: 'Page', ... }
  // pages/Dashboard.js: { extends: 'AppLayout', ... }   ✓

Without this chain the page misses Page-only behavior (route mounting,
metadata pickup, default body class) and fails to register with the
router as a navigable surface.

# FA802 — lowercase-child-keys

Lowercase HTML-like keys (h1, nav, form, header, ...) silently DO
NOT render — they end up as plain JS property names on the parent
object and the framework discards them.

The framework auto-detects the HTML tag from a PascalCase key:

  Bad:    h1: { text: 'Welcome' }    // never renders
  Good:   H1: { text: 'Welcome' }    // renders an <h1>

Same applies to Nav/Form/Header/Section/Article/Main/Aside/Span/P/
Button/Input/Select/etc.

Scope: this rule only fires inside DOMQL components. Lowercase keys
in state.js, config.js, design-system files, or inside style/attr/
state/scope/props/cases/data containers are NOT renamed — those are
data, not children.

# FA803 — redundant-flex-extends

Bad:    Row: { extends: 'Flex', flow: 'x' }
Good:   Row: { flow: 'x' }                 // flow alone is enough
        Flex: { flow: 'x' }                // or rename — the key auto-extends Flex

The key name `Flex` (or `Flex_1`, `Flex_2` for multiple instances)
auto-extends the Flex atom.

# FA804 — redundant-box-extends

Bad:    Card: { extends: 'Box', padding: 'B' }
Good:   Card: { padding: 'B' }

Every element is already a Box, so `extends: 'Box'` is a no-op.

# FA805 — redundant-text-extends

Bad:    Heading: { extends: 'Text', text: 'Hi' }
Good:   Heading: { text: 'Hi' }

Any element with a `text:` prop is already a Text component.

# FA806 — auto-extend-wrapper

DOMQL auto-extends by key name. A wrapper that just re-exports another
component under a different name (`Header: { extends: 'Navbar' }`) is
usually noise — rename the key to match.

Bad:    Header: { extends: 'Navbar', logo: '...' }
Good:   Navbar: { logo: '...' }

Multi-instance:
  Bad:    Icon1: { extends: 'Icon', name: 'home' }
          Icon2: { extends: 'Icon', name: 'search' }
  Good:   Icon_1: { name: 'home' }
          Icon_2: { name: 'search' }

Keep the explicit extends only when the wrapper carries distinct
semantic meaning (e.g. `Sidebar: { extends: 'Drawer' }` where Sidebar
has a real role beyond just "another Drawer instance").

# FA807 — extends-variable

`extends` must be a quoted string. The framework resolves it through
the registered component map (PascalCase keys). A JS identifier value
creates a hard coupling that breaks frank serialization and the
registry lookup.

Bad:    Card: { extends: BaseCard, ... }       // BaseCard is imported
Good:   Card: { extends: 'BaseCard', ... }     // BaseCard is registered in components/

# FA808 — inline-childextends-object

Inline `childExtends: { ... }` creates an anonymous component that
cannot be reused, registered, or serialized by frank. Register the
inline shape under a name in components/ and reference by string.

Bad:    List: {
          childExtends: { padding: 'A', color: 'gray.5' },
          children: items
        }
Good:   // components/ListItem.js
        export const ListItem = { padding: 'A', color: 'gray.5' }
        // List.js
        List: { childExtends: 'ListItem', children: items }


---

## FA9xx — Reference resolution

# FA901 — unresolvable-free-var

A handler body references an identifier that:

  - is not declared at the module scope of the file
  - is not imported
  - is not a key in globalScope.js
  - is not a known JS / DOM / smbls global

frank cannot resolve this at bundle time. At runtime the handler
throws `ReferenceError: <name> is not defined` the first time it runs.

## What to check

  - Did you mean a different name? (Typos are common — `state` vs `s`)
  - Should this value live in `globalScope.js`?
  - Should it be passed via `scope: { name: value }` on the element?

The audit never auto-fixes these — the right fix depends on what the
identifier was supposed to mean.

# FA902 — side-effect-import

A `const X = factory(...)` at module scope runs the factory at import
time. If frank-audit moved the declaration to `globalScope.js`, the
factory would run at a different point in the framework lifecycle —
typically deferred until first read, sometimes inside an async
handler. For factories with side effects (network connections, auth
token fetches, observers, registrations), that timing change can
silently break the app.

## What to do

  - If the factory is pure (just constructs a value), it's safe to
    inline the construction inside `globalScope.js` itself or wrap
    in a getter.
  - If the factory has side effects, leave the declaration where it
    is and treat the cross-file usage as deliberate (consider an
    `el.call('X')` interface that hides the binding).

# FA903 — component-as-function

Symbols components are plain objects:

  export const Card = { padding: 'A', text: 'hi' }

Function-style components

  export const Card = (props) => ({ ... })

are not serializable by frank — the function call would have to run at
JSON-export time, which it does not. The deployed JSON contains the
function source as a string, never the object the function returns.

## What to do

  - If the function takes props and returns a static-ish object,
    convert to a plain object and use the `props:` declaration shape
    (or `scope:` for instance-bound values).
  - If the function is genuinely dynamic, register it under
    `functions/` and have a real component (a plain object) call it
    via `el.call('makeCard', ...)`.

No auto-fix because the conversion depends on what the function
actually does.

# FA904 — circular-globalscope

Two component files both reach across the boundary via globalScope
helpers, each one consuming a value declared in the other. Example:

  A.js declares  helperA   — used by B.js
  B.js declares  helperB   — used by A.js

frank still serializes both correctly, but the call graph zigzags
across the project — debugging gets harder, refactors get fragile.

## What to do

  - Pick a single owner for the shared concern and put both helpers
    in globalScope.js, removing the file-to-file pingpong.
  - Or extract the shared concern into its own functions/ entry and
    have both files call it via `el.call('shared', ...)`.

No auto-fix — the right consolidation depends on which side carries
the dominant logic.

