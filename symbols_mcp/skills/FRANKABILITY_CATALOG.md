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
  envs.js, schema.js, and the entry module of each lazy group
  (context.js `lazy: { admin: () => import('./admin/index.js') }`)

# FA006 — orphan-file

frank.toJSON walks only the canonical project slots:

  components/  pages/  functions/  methods/  snippets/
  designSystem/  files/  assets/

Files in any other folder (utils/, lib/, helpers/, services/, ...) are
silently dropped from the published JSON. The local dev server still
sees them via normal JS imports — local works, prod is missing the code.

A lazy group's folder (context.js `lazy: { admin: () => import('./admin/index.js') }`)
is discovered: its entry module and its components/, pages/, functions/,
methods/ and snippets/ ship — frank merges them into the canonical
sections. Any other file in it is an orphan of that group.

## Fix

Sub-folder orphans are auto-moved to `functions/` (a lazy group's own
`functions/` for an orphan inside the group). If the exports are
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

Every attribute an element's tag has is a flat prop (attrs-in-props:
the per-tag tables, the global attributes, aria-* and data-*, both
spellings of multi-word names). Wrapping one in `attr: { ... }` is the
legacy nested syntax.

Bad:
  Img: {
    attr: { srcset: (el, s) => s.srcset, sizes: '100vw', fetchpriority: 'high' }
  },
  Field: {
    tag: 'input',
    attr: { inputmode: 'numeric', 'aria-label': 'Amount' }
  }

Good:
  Img: { srcset: (el, s) => s.srcset, sizes: '100vw', fetchpriority: 'high' },
  Field: { tag: 'input', inputmode: 'numeric', ariaLabel: 'Amount' }

## Decided per tag, by the runtime's own rules

An entry is flagged only when, written flat on the element's tag, it
reaches the DOM as that attribute — attrs-in-props
`checkAttributeByTagName`, after the element's own routing:

  - a CSS key is CSS when flat: `width` / `height` on an <img>, `color`,
    `translate` stay in `attr: {}` (except `rows` / `cols` / `wrap` on a
    <textarea> and `fill` / `stroke` on an <svg>, which stay attributes);
  - a framework key means something else flat: `content` (<meta>),
    `scope` (<th>), `class`, `style` stay in `attr: {}` (`value` is the
    exception: flat, it sets the node's value);
  - a name the tag's table does not list stays: `href` on a <div>, `d`
    or `cx` on an SVG child (no table).

The tag comes from `tag:`, else the extends ladder (the key-derived
base first, then `extends` with its last entry dominant), else the key
(`Img: {}` is an <img>). Where source cannot tell — an exported component
without `tag:`, a base from a linked shared library, childProps or
childExtends on the parent — only the attributes that are flat on every
tag (globals, aria-*, data-*) are flagged.

`attr: { ... }` stays for names no table lists (custom attributes), for
`translate`, and for the cases above. The fix hoists the flagged entries
verbatim and keeps the rest in `attr:`. When the element already sets
the same attribute flat, the finding is low-confidence (a human picks
the value) and the fix refuses it.

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

CARVE-OUT — a `fetch` config trigger is NOT this rule:

  { tag: 'form', fetch: { method: 'insert', from: 'contacts', on: 'submit' } }

`on` is a documented key of the fetch plugin ('create' | 'click' |
'submit' | 'stateChange'); the plugin binds the listener itself. An
`onSubmit: fn` there does NOT run the declarative mutation, so an `on`
string that sits directly on a fetch config is skipped — in the object
form, in the `fetch: [ ... ]` array form, and in the function form
`fetch: (el, s) => ({ ... })`. Any other `on` string still reports.

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

## CSS custom properties: `vars` or a top-level `--x` key

Custom properties have their own channel, not `style:`:

      vars: { cardAccent: 'red' }                     // --cardAccent
      vars: { '--card-accent': (el, s) => s.accent }
      '--card-accent': (el, s) => s.accent           // top-level, same path
      vars: (el, s) => ({ '--x': s.x + 'px' })        // the whole bag

A static entry compiles into the element's atomic class, so a `:hover`,
`@media` or `.isX` block overrides it; a factory is written inline and
re-runs when what it reads changes (`null` removes the property). Names
and values are verbatim — no design-token lookup.

## When `style:` IS appropriate

  - Vendor-prefixed CSS that DOMQL doesn't expose:
      style: { WebkitTapHighlightColor: 'transparent' }
  - Per-instance literal CSS where you explicitly want to bypass
    DOMQL's transformer (rare).

The audit only hoists keys it knows DOMQL handles flat — anything
unknown stays inside `style:` untouched. Custom properties stay too:
the message lists them when the flagged block holds any; move them to
`vars` by hand (a `style:` block of custom properties alone is not a
finding).

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

For a helper only ONE file uses, see FA211 (keep module scope empty:
`functions/X.js` + `el.call('X', …)`).

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

Not flagged inside a bridge's own code (`onBridgeMount` /
`onBridgeUpdate` / `onBridgeDestroy` and the host's `onXxx` handlers):
the option objects a library takes (toolbar handlers, key bindings,
paste matchers) are built there at runtime, inside one serialized
function, so their closures survive. A factory that RETURNS a bridge
host is still flagged.

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

# FA211 — module-scope-binding

Keep module scope EMPTY in `components/`, `pages/`, `snippets/` and
`functions/` files (RULES.md Rule 33). frank does not drop a
module-level binding a function reads: it evaluates the module at
publish and hoists the value into the project's ONE shared
`globalScope`, rewriting each read to `__scope.<name>`. It keeps a pure
value working, at three costs — one flat namespace per project (two
files' `DEFAULT` publish as `DEFAULT` and `DEFAULT2`, or the publish is
refused), shadowing by any element whose own `scope` has that key, and
evaluation where frank runs instead of in the browser.

Bad:
  const rise = (delay) => ({ animationName: 'coverRise', animationDelay: delay })
  const formatPrice = (n) => '$' + n.toFixed(2)
  export const PriceCard = {
    ...rise('0s'),
    Price: { text: (el, s) => formatPrice(s.price) }
  }

  // functions/listQuerySet.js
  const DEFAULT = ['home', 'about']
  export const listQuerySet = function listQuerySet (patch) { … return DEFAULT }

Good:
  // components/Rise.js — a shared style cluster is a component
  export const Rise = { animationName: 'coverRise', animationDelay: '0s' }
  // functions/formatPrice.js — a callable helper is a function
  export const formatPrice = function formatPrice (n) { return '$' + n.toFixed(2) }
  export const PriceCard = {
    extends: 'Rise',
    Price: { text: (el, s) => el.call('formatPrice', s.price) }
  }
  // functions/listQuerySet.js — the constant lives inside the function
  export const listQuerySet = function listQuerySet (patch) {
    const DEFAULT = ['home', 'about']
    …
  }

| What | Where |
| -- | -- |
| A callable helper | `functions/X.js` + `el.call('X', …)` |
| A style cluster spread into components | a component + `extends` / `childProps` (Rule 61) |
| A constant a `functions/` export needs | inside the function |
| A value one component uses | `scope: { X }` on that component (FA204 moves the simple case) |
| A value several files use | `globalScope.js`, under a distinctive name (FA202 / FA203) |
| Mutable state | `globalScope.js` (FA201), or `el.scope` per instance |

Not flagged: exports, imports, unused bindings, a name another file
uses too (FA202 / FA203), what FA201 / FA204 / FA205 report, test
files, and files outside those folders. Detect-only — each finding
becomes a prescription.

## Opt-in

FA211 is not in the default rule set: a default run reports no FA211
finding, count or prescription (on 24 measured projects it would add
3 582, 1 336 in one of them). Name it to run it:

  frank-audit audit <dir> --rule FA211
  smbls frank-audit --rule FA211
  audit(dir, { ruleIds: new Set(['FA211']) })   // HTTP: { ruleIds: ['FA211'] }
  eslint: rules: { 'frank/FA211': 'warn' }

Not FA207: that id names the nested-helper check in symbols-mcp docs and
installed hooks (FA208–FA210 are documented ids too). frank-audit has no
rule FA207; `--rule FA207` runs nothing and says the id was ignored.


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

See designSystem/spacing.js (or sizing.js, typography.js) for the available
tokens. The audit cannot pick the right one — open the design system and
choose the token whose declared value matches the literal.


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

## Cross-origin redirects (OAuth, payment, …)

External URLs aren't routable by `el.router` — the in-app router
only knows about same-origin routes. FA401 already auto-suppresses
when the call argument is a string literal starting with `https://`,
`http://`, `mailto:`, `tel:`, or `sms:`. For URLs built at runtime
(`new URL(SUPABASE_URL + …).toString()`), the literal detection misses
them — use the inline pragma:

    window.location.assign(authUrl) // frank-allow FA401

Or above the line:

    // frank-allow FA401 — OAuth provider redirect
    window.location.assign(authUrl)

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

# FA410 — history-write

The router owns the address. A raw History API write moves the URL
while the page, `state.route` / `state.query`, the guards and the
Back / Forward bookkeeping stay where they were (RULES.md Rule 42).

Bad:    history.pushState({}, '', `/user/${slug}`)
        window.history.replaceState(null, '', '/login')
        win.history.replaceState(win.history.state, '', path + '?' + qs)
Good:   el.router(`/user/${slug}`, el.getRoot())
        el.router('/login', el.getRoot(), {}, { replace: true })
        el.router(path + '?' + qs, el.getRoot(), {}, { replace: true, scrollToTop: false })

`{ replace: true }` rewrites the current entry instead of adding one —
a redirect, a canonical URL, a filter or query sync that must not stack
Back entries. A query-only navigation keeps the mounted page (no
re-render) and updates `state.query`; pass `scrollToTop: false` when the
view must stay where it is. From outside an element (boot code, a
function called before render) use the app's `app.navigate(path,
{ replace })`, or accept `el` and call `el.router`.

Not flagged: `history.back()` / `go()` / `forward()` (the router follows
popstate), reads of `history.state`, test files. A deliberate raw write
(for example stripping an OAuth code from the address before the app
renders) keeps `// frank-allow FA410` on or above the call.


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

Bad:    window.visualViewport.addEventListener('resize', apply)
Good:   onVisualViewportResize: (e, el, s) => apply(el) // visualViewport target
Bad:    window.matchMedia('(max-width: 768px)').addEventListener('change', fn)
Good:   onMediaQueryChange: { query: '(max-width: 768px)', handler: fn }
        onMediaQueryChange: { query: 'mobileL', handler: fn }  // or '@mobileL'
        // the query MINTS the target, so it travels in the options form;
        // a designSystem.media key (stock or the project's own) reads the
        // query `@mobileL` blocks use, so a moved breakpoint moves it too;
        // an array of { query, handler } watches several queries at once

A custom event name that is not identifier-shaped is still a key — it
just has to be QUOTED, because everything after the prefix is taken
verbatim and lowercased:

Bad:    window.addEventListener('symbols:auth-callback', onAuth)
Good:   'onWindowSymbols:auth-callback': (e, el) => onAuth(e, el)

Flat `onEvent` handlers are tracked by DOMQL's lifecycle and are
cleaned up automatically when the element unmounts. `onDocumentXxx` /
`onWindowXxx` / `onVisualViewportXxx` / `onMediaQueryChange` extend
that to events that never reach an element the project owns —
third-party widgets portaled into
document.body, outside-click / Escape for layers, window resize/scroll,
the soft-keyboard viewport and a media-query flip: registered once when
the element gets its node, inert while `if:`-hidden,
torn down in dispose(). Raw addEventListener stays banned outside a
bridge host — every receiver now has a sanctioned flat prop.

An element hears its own subtree through the node-level options form:

Bad:    node.addEventListener('scroll', fn, { capture: true, passive: true })
Good:   onScroll: { capture: true, passive: true, selector: '.inner', handler: fn }
        // capture hears what never bubbles to the element (a scroll inside
        // it) and runs before an inner node's own listener; selector
        // narrows the target; once / passive as declared

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA504 — classlist-mutation

Class state is data-driven, not imperative.

Bad:    el.node.classList.add('active')
Good:   isActive: (el, s) => s.activeId === el.key
        // matching `.isActive: { ... }` style block on the component

For classes that do not follow the `isX` convention:
        class: { highlighted: (el, s) => s.flag }

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA505 — inner-html-write

Bad:    el.node.innerHTML = '<b>Hi</b>'
Good:   text: 'Hi'                             // auto-escaped, preferred
        html: '<b>Hi</b>'                      // raw, when truly needed

Both `text:` and `html:` re-render correctly when their value
changes — direct innerHTML mutation does not.

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA506 — set-attribute

Attributes are flat top-level props on the component (placeholder,
type, name, value, disabled, ...). Setting them imperatively bypasses
DOMQL's diffing and breaks reactive updates.

Bad:    el.node.setAttribute('aria-expanded', 'true')
Good:   'aria-expanded': (el, s) => String(s.open)

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA507 — remove-attribute

Bad:    el.node.removeAttribute('disabled')
Good:   disabled: (el, s) => s.locked || null    // null removes the attr

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA508 — append-child

Bad:    parentEl.node.appendChild(childEl.node)
Good:   declare the child as a key on the parent component, or use
        children: [...] + childExtends: when the list is dynamic

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA509 — remove-child

Bad:    parentEl.node.removeChild(child.node)
Good:   Child: { if: (el, s) => s.show }

When the predicate flips false the framework unmounts the child. When
it flips back true the child re-mounts cleanly.

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

# FA510 — insert-before

Bad:    parent.node.insertBefore(newEl.node, anchor.node)
Good:   children: [...] on the parent — DOMQL renders in array order

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

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

Not flagged inside a bridge host (default-config `Bridge`, or any
element that declares `onBridgeMount`): the library owns the DOM in it,
so the bridge's own code — `onBridgeMount` / `onBridgeUpdate` /
`onBridgeDestroy` and the host's other `onXxx` handlers — works on it
directly. The same code anywhere else is still flagged.

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
               onWindowScroll: (e, el, s) => onScroll(e, el, s) on the
               owning component (a window-level listener DOMQL owns;
               raw addEventListener stays FA503)

  2. DOM ref (querySelector result, el.node, sibling ref):

       Bad:    minInput.update({ value: '' })
       Good:   minInput is the wrong reference — call `.update` on
               the OWNING DOMQL element instead: el.update({ value: '' })

Frank-audit doesn't auto-fix this — the right replacement depends on
whether you want the framework event-delegation path or an
imperative listener.

# FA515 — conditional `s.root.X` read in a reactive factory

A prop factory runs inside a `createEffect`. Its dependency set is what
it ACTUALLY READS on a given run — not what it might read. So a
short-circuit silently drops a dependency:

    hide: (el, s) => !el.call('ready', s.root) || s.root.rows.length > 0

On the first run `ready` is false, `||` short-circuits, `rows` is never
read — and therefore never subscribed to. When `rows` lands, this
factory does not re-fire. Ever.

Why it escapes review: on a fast network the fetch usually resolves
before first render, the factory takes the ready branch, and tracking is
armed by luck. It breaks on slow connections — real users, not your
machine. This is the 2026-07-29 warehouse-widget incident: a `children:`
factory showed 3 fetched rows while its `text:`/`hide:` siblings, reading
the SAME signal, stayed frozen — `children:` read the collection
unconditionally, the siblings did not.

Fixes, best first:

  1. Declare the dependency (smbls 044742dbc):

         hideDeps: ['rows'],
         hide: (el, s) => !el.call('ready', s.root) || s.root.rows.length > 0

  2. Add the key to `subscribeTo: [...]` on the same element — note a
     parent's subscribeTo does NOT cascade to descendants; each element
     needs its own.

  3. Hoist the read so it is unconditional (the older `void s.root.X`
     prelude, ~1,054 of which exist in the monorepo). Works, but needs
     one statement per key and is easy to forget when the condition
     changes later.

Not auto-fixed: choosing between declaring, hoisting, and restructuring
the condition is a judgement call about what the factory should depend on.

# FA516 — lookup-predicate-arity

`lookup`/`lookdown` (and `lookupAll`/`lookdownAll`) call the predicate
with exactly ONE argument: the candidate element. The DOMQL prop-factory
signature `(el, s)` does NOT apply here.

Bad:    el.lookup((el, s) => s.key === key)
        el.lookdown((el, s) => el.Rename && s.key === key)
Good:   el.lookup((n) => n.state?.key === key)
        el.lookdown((n) => n.Rename && n.state?.key === key)

A `&&` in front of the state read only hides the bug: it throws as soon
as a candidate satisfies the left-hand side, which can be months later.

Note `lookup` starts at `this.parent` — it is NOT self-inclusive. If the
element itself can satisfy the predicate, write
`pred(el) ? el : el.lookup(pred)`. If the thing you want is always on an
ancestor (the usual case), do NOT add that guard — it changes behaviour.


---

## FA6xx — Lifecycle & events

# FA601 — svg-tag

Icons live in `designSystem/icons` and are rendered via the `Icon`
component. Inline `<svg>` markup bypasses the design system, breaks
theme-aware color resolution, breaks SSR, and breaks brender hydration.

Bad:    Logo: { tag: 'svg', html: '<path .../>' }
Good:   Logo: { extends: 'Icon', name: 'logo' }
        // matching `logo: { svg: '<path .../>' }` in designSystem/icons.js

## Data-viz / sparklines

FA601 auto-suppresses when the SVG has a non-icon-grid `viewBox`
(anything outside the 16/20/24/32/48/64 square set) OR contains a
child with a computed `d` / `points` / path attribute. Charts and
sparklines look like that; they aren't icons.

For other edge cases (procedural illustrations with icon-grid
viewBox), use the inline pragma:

    // frank-allow FA601 — generated decoration, not an icon
    Burst: { tag: 'svg', viewBox: '0 0 24 24', ... }

# FA602 — path-tag

Same problem as FA601 — see that rule for the migration pattern.
FA602 auto-suppresses for `<path>` entries whose `d` value is a
function (sparklines, data-driven viz). Inline `// frank-allow FA602`
works the same way as on FA601.

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

Strings displayed to the user must flow through the polyglot pipeline so
other locales render correctly (RULES.md Rule 48).

## The rewrite form depends on the PROP, not on the string

There are two forms, and only one of them is correct for any given prop.
Choosing wrong is SILENT: the label renders as an empty string, in every
language including English, with no error anywhere.

  TEMPLATE   text: '{{ nav.openInEditor | polyglot }}'
  FUNCTION   placeholder: (el) => el.call('polyglot', 'nav.searchHint')

| prop | template | function | use |
|---|---|---|---|
| `text` | works | works | TEMPLATE |
| `placeholder`, `alt`, `aria-*`, other HTML attributes | works | works | FUNCTION |
| `href`, `src` (also `action`, `poster`, `data`) | resolves once, never switches | works | FUNCTION |
| `label`, `caption`, `helperText` (custom props) | works | works | FUNCTION |
| `title` | works | renders "" as content | TEMPLATE |

Why: since smbls 2026-09-24 an attribute prop holding a `{{ }}`
template gets its own reactive effect, resolved against the element
STATE with the polyglot
filter, and the prop KEEPS its template. Before that fix the static
attribute pass resolved the template once, without the element binding
(so a filtered template rendered ""), and wrote the empty answer back
OVER the prop, which destroyed it. The function form always worked: a
function-valued flat attribute registers its own effect, `polyglot`
reads `root.lang`, and the effect re-fires on a switch. Both forms are
correct now — except on the ATTR_TRANSFORMS props (`src`, `href`,
`action`, `poster`, `data`): those resolve a template ONCE, at mount,
through their transform, so it renders the mount language and never
switches. FUNCTION stays the default because it is also correct when
the consumer reads the prop as content, and a custom prop can become an
HTML attribute the day someone renames it.

## `title` takes the TEMPLATE form

`title` is a global HTML attribute on EVERY tag, and it is also a common
custom prop meaning "the heading string", read by a child as
`text: (el) => el.parent.title`.

  - as a TOOLTIP: both forms work.
  - as CONTENT:   only the TEMPLATE form works. The prop keeps its
    template, so the child text effect resolves it. A FUNCTION is never
    auto-invoked (`title` is a valid attribute on every tag), so the
    prop stays a function and the child's text effect drops it on its
    `typeof val !== 'function'` guard — an empty label.

A `title` a child reads as content is still better RENAMED to a prop
that is not an HTML attribute (`heading`, `label`): the attribute also
paints a native tooltip nobody asked for.

Measured on the smbls element runtime; the runtime test that pins this
table and this rule change together.

## The key comes from the LOCATION, never from the copy

  <namespace>.<area>.<element>      e.g. preview.navbar.editorLink

namespace = the surface; area = the enclosing export; element = the
innermost PascalCase child key the string sits under (in DOMQL that key
IS the element's role), or the prop name when the string sits directly
on the export.

A key derived from the English copy changes when the copy changes, so
every translation silently reverts to the base language on a wording
tweak; and two surfaces that happen to use the same words collide across
the whole project. `preview.navbar.editorLink` survives "Open in editor"
becoming "Edit this project". A key spelled `openInEditor` does not
survive a second surface wanting those words for a different action.

Override the namespace with the `polyglotNamespace` option; it defaults
to the audit root's directory name.

## What counts as copy

Props: `text`, `placeholder`, `label`, `title`, `caption`, `helperText`,
`alt`, and the ARIA strings in every spelling — `'aria-label'`,
`ariaLabel`, `aria: { label }`, and the same for `description`. Rule 48
makes no exception for length or language: `'Save'`, `'New'`,
`'Monthly subscription'` and `'ხმა'` are all flagged.

Not copy, never flagged:
  - a `{{ … }}` template; a function value;
  - no letter, or one: numbers, symbols, a glyph or an initial
    (`'01'`, `'→'`, `'λ'`, `'A'`);
  - one ALL-CAPS token: an acronym or a key name (`API`, `ESC`, `GET`);
  - one name-shaped token: an inner capital or a digit (`GitHub`,
    `OpenAI`, `Auth0`), a file, URL, handle or address (`NavHeader.js`,
    `@kekela`, `mcp.symbols.app`);
  - outside the ARIA props, a string whose first letter is lowercase:
    an identifier, unit, icon name or polyglot key (`'shell.app.studio'`).
    An ARIA label is read aloud, so there a lowercase word counts.
Any letter of a non-Latin script makes a string copy whatever its case.
Test files (`*.test.js`, `__tests__/`) and files outside every frank
slot are not audited for copy.

## Escape hatch

Heuristic only — a brand mark spelled as one plain word (`Figma`), a
person's name, and intentionally untranslated internal tool copy are
allowed with `// frank-allow FA701` on or above the offending property.

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

# FA809 — key-detected-styled-tag

Bad:    Badge: { Sup: { text: 'Soon' } }        // renders <sup>: shifted, smaller
Good:   Badge: { Sup: { tag: 'span', text: 'Soon' } }
        Note: { Mark: { tag: 'mark', text: 'hit' } }   // a highlight you MEAN

A child key that names an HTML tag becomes that tag when no `tag:` is set
(smbls detectTag). For tags the browser styles, that is almost always an
accident of naming: `Mark: {}` paints a yellow `<mark>`, `Sub`/`Sup` shift
and shrink their text, `Dialog` brings a border and a white sheet, `Menu`
list padding. Flagged tags: mark, sub, sup, small, s, u, ins, del, b, i, q,
cite, dfn, var, abbr, kbd, samp, dialog, menu, details, summary, legend,
fieldset. Set the tag you mean.

Message: this key renders a `<x>`; add `tag: 'x'` if you mean it, else `tag: 'div'`

Not flagged: an own `tag:`, an `extends:` (the base decides), lowercase keys,
tags without a visible UA style (`Strong`, `Em`, `Header`, `P`, …). Keep a
meant one with `// frank-allow FA809` on or above the key.

Census 2026-10-02: 286 such keys took their tag from the name, 113 more
already undid it with an explicit `tag:`. The first 19 tags are planned to
leave key detection in smbls.


# FA810 — condition-case-block

Bad:    Card: {
          background: (el, s) => s.open ? 'surface' : 'transparent',
          color: (el, s) => s.open ? 'title' : 'caption',
          padding: (el, s) => s.open ? 'B' : 'A'
        }
Good:   Card: {
          isOpen: (el, s) => s.open,
          background: 'transparent', color: 'caption', padding: 'A',
          '.isOpen': { background: 'surface', color: 'title', padding: 'B' }
        }

One condition declared once as `isX` drives a `'.isX'` (or `'!isX'`) block:
one reactive class instead of N reactive props. Flagged when 3 or more
CSS props of one element use the same condition (parameters compared by
position, whitespace ignored).

## Opt-in

FA810 is not in the default rule set: a default run reports no FA810
finding, count or prescription. Name it to run it:

  frank-audit audit <dir> --rule FA810
  smbls frank-audit --rule FA810
  audit(dir, { ruleIds: new Set(['FA810']) })   // HTTP: { ruleIds: ['FA810'] }
  eslint: rules: { 'frank/FA810': 'warn' }

symbols-mcp's audit_component runs the same check; the two agree.

# FA811 — interactive-states

Bad:    Save: { extends: 'Button', ':hover': { background: 'accent' } }
Good:   Save: { extends: 'Button',
          ':hover': { background: 'accent' },
          ':active': { background: 'accent.-1' },
          ':focus-visible': { outline: 'solid, Z, accent' } }

An interactive element with a hover state and no pressed state gives no
feedback on touch and on click. Interactive here: the Link / Button
family by extends or key, tag 'a' / 'button', or href / onClick on an
exported definition or a lowercase-keyed element. An element extending
only project components is skipped — its primitive owns the states.

## Opt-in

FA811 is not in the default rule set: a default run reports no FA811
finding, count or prescription. Name it to run it:

  frank-audit audit <dir> --rule FA811
  smbls frank-audit --rule FA811
  audit(dir, { ruleIds: new Set(['FA811']) })   // HTTP: { ruleIds: ['FA811'] }
  eslint: rules: { 'frank/FA811': 'warn' }

symbols-mcp's audit_component runs the same check; the two agree.

# FA812 — button-call-site-override

Bad:    Toolbar: { Button_save: { text: 'Save', padding: 'Z A', height: 'B' } }
Good:   // components/CompactButton.js — a variant owns the scale
        export const CompactButton = { extends: 'Button', padding: 'Z A', minHeight: 'B' }
        Toolbar: { CompactButton: { text: 'Save' } }

Buttons keep one scale across the product. A call site that changes a
Button's padding or height breaks that; a variant (an exported
component extending Button) or a design-system token keeps it.

## Opt-in

FA812 is not in the default rule set: a default run reports no FA812
finding, count or prescription. Name it to run it:

  frank-audit audit <dir> --rule FA812
  smbls frank-audit --rule FA812
  audit(dir, { ruleIds: new Set(['FA812']) })   // HTTP: { ruleIds: ['FA812'] }
  eslint: rules: { 'frank/FA812': 'warn' }

symbols-mcp's audit_component runs the same check; the two agree.

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

# FA905 — hardcoded-deploy-value

Project source contains deployment identity:

  - absolute platform hosts — `api.symbols.app` (any `dev.`/`staging.`
    prefix), `preview.symbols.app`, `*.symbo.ls` tenant hostnames,
    `localhost:<port>`
  - 24-hex Mongo ObjectId literals

Deployment identity belongs to the deployer: `__SYMBOLS_ENV__` → the
injected identity tag → `/resolve`. Tenant code that hardcodes a host
is pinned to one environment; a hardcoded ObjectId is invisible
env-coupling — the record it names exists in exactly one database, so
the same source silently breaks (or worse, reads the wrong tenant)
anywhere else.

## Severity

Advisory (`info`) — a debt register, not a build blocker. Real
projects carry hundreds of asset/content URLs that work today; the
point is to make the coupling visible, not to fail the build.
Findings aggregate per file per family (count + per-value breakdown +
sample lines) so the register stays readable.

## Not this rule’s business

`w3.org` xmlns, `images.unsplash.com`, CDNs, and every other
non-platform host. npm-scope strings (`@symbo.ls/pkg`) are package
names, not hostnames. The `assets/` and `files/` slots are skipped
entirely — those manifests are the platform’s own serialization of
uploaded media, deployer-owned by construction. Comment-only matches
still surface, at low confidence.

## What to do

  - hosts → resolve through the environment (`__SYMBOLS_ENV__` /
    `/resolve`, `workspaceApiBase()`), never a literal
  - ObjectIds → look the record up by a stable key (slug, name) or
    receive the id from state/config seeded by the deployer
  - a genuinely intentional literal → `// frank-allow FA905`

Never auto-fixed — replacing an id or host needs the deployer-side
counterpart to exist first.

