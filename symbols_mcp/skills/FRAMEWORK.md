# Symbols Framework — MCP Reference

Single source of truth for all framework-level guidance: project structure, plugin usage, theming, SSR, JSON ↔ FS compilation, and publishing. Cross-references the deeper docs in `packages/` / `plugins/` and `DESIGN_SYSTEM.md`.

> Audience: Claude (and other agents) working in any Symbols project. Optimize for skim-and-act, not narrative.

---

## 1. Canonical project layout

A Symbols project has this shape:

```
my-project/
  index.html             # entry HTML; loads index.js
  index.js               # `create(app, context)` boot
  package.json
  symbols.json           # publish/runtime metadata (key, owner, brender flag, prefix, etc.)

  symbols/
    app.js               # root element definition (NOT the page content; pages live in pages/)
    context.js           # aggregated context: spreads config + app + state + components + pages + ...
    config.js            # framework flags + plugin config (useReset, globalTheme, themeStorageKey, fetch, polyglot, router, ...)
    state.js             # initial root state (object, not function)
    dependencies.js      # external script CDN deps
    sharedLibraries.js   # array of cross-project context contributors
    globalScope.js       # constants and helpers exposed via `__scope`
    cases.js             # named conditional predicates for `$X` / `.X` / `!X` blocks
    components/index.js  # `export * from './X.js'` for every component
    pages/index.js       # `export default { '/': main, '/about': about, ... }`
    designSystem/index.js
    functions/index.js   # registered fns called via `el.call('fnName', ...)`
    methods/index.js     # methods bound onto every element (`this.X(...)`)
    snippets/index.js
    files/index.js       # static assets / inline file blobs
    workers/<name>.js    # module Web Workers, one file each, no index.js (`self` is the global; since smbls 3.14.859 / cli 3.14.826)
    admin/index.js       # optional lazy route group (context.js `lazy: { admin: () => import('./admin/index.js') }`),
                         # laid out like the project: admin/components/, admin/pages/, admin/functions/, …
```

`index.js` is one line:

```js
import { create } from 'smbls'
import context from './symbols/context.js'
create({ AppModals: {} }, context)
```

The first arg to `create()` is the **root element shape** (not the whole app). Pages are looked up out of `context.pages` by the router.

---

## 2. Component rules (enforced)

### Identity & references

- Components are plain objects — never functions or classes.
- **No imports between project files.** Reference components by their
  PascalCase key name (`extends: 'Header'`). Reference functions via
  `el.call('fnName', ...)` / `this.call('fnName', ...)`.
- `extends` and `childExtends` must be **quoted strings**, never inline
  objects. If you need a reusable child shape, extract it to a named
  component in `components/` and reference it by name. Inline-object
  `childExtends` triggers a css-in-props text-leak bug and breaks frank
  serialization.

### PascalCase children — the #1 root cause of "missing content"

**All child element keys must be PascalCase (A-Z first char). No
exceptions.** Lowercase keys are filtered out of the child-creation loop
entirely (`packages/element/src/create.js:1583` → the `createChildren`
function gates on `firstChar < 65 || firstChar > 90`), so a lowercase
key never renders, regardless of whether it happens to match an HTML
tag name.

```js
// ❌ Lowercase — never render as child elements
h1:     { text: 'Hello' }
nav:    { ... }
form:   { ... }
hgroup: { ... }
group:  { ... }

// ✅ PascalCase — always renders
H1:     { tag: 'h1', text: 'Hello' }
Nav:    { ... }                 // tag auto-detected from key (Nav → 'nav')
Form:   { ... }                 // also auto-extends built-in Form atom
Hgroup: { ... }                 // also auto-extends built-in Hgroup atom
```

The framework's tag-from-key auto-detection
(`packages/element/src/cache.js:53` → `detectTag`) lowercases the key
and maps it to a valid HTML tag, so `Nav: {}` renders as `<nav>`,
`Article: {}` as `<article>`, etc.

Built-in atoms (`Box`, `Flex`, `Grid`, `Hgroup`, `Form`, `Text`, `Img`,
`Iframe`, `Svg`, `Shape`, `Picture`, `Video`, `Link`, `Button`, `Select`,
`Input`, `NumberInput`, `Checkbox`, `Radio`, `Toggle`, `Textarea`, `Icon`)
auto-apply when the key matches their name. **You don't need
`extends: 'Flex'`** — naming the child `Flex: {...}` is enough. Same
goes for any registered component: `Button: {...}` inherits Button
without an explicit `extends` (verified at
`packages/element/src/create.js:1589-1593`).

To mount multiple instances of the same component, use `Icon_1` /
`Icon_2` (the `_<suffix>` is ignored for extend resolution). A key with
an explicit `extends` is a role name (`SidebarNav: { extends: 'Navbar' }`):
never name it after a different registered component (RULES.md Rule 6).

### Flat access

- `el.props.X` → `el.X` (props live directly on the element).
- `el.on.event` → `el.onEvent` (event handlers are top-level).
- Don't write `on: { … }` or `props: { … }` wrappers in component
  definitions. The framework does not read them.
- Exception for `props: …`: only when `props` is a function returning a
  reactive object — that's how reactive props work. Object-form `props: {…}`
  should be flattened to component root.

### HTML attributes & DOM API

- HTML attributes that DOMQL exposes as first-class props (`placeholder`,
  `type`, `name`, `value`, `disabled`, `checked`, `title`, `role`,
  `tabindex`, `src`, `href`, …) go **top-level** — do **not** wrap in
  `attr: { … }`. Reserve `attr: { … }` only for attributes that aren't
  surfaced as first-class props.
- For dynamic HTML attributes that aren't first-class props, use
  `attr: { 'data-foo': (el, s) => … }`. Function values on `attr` keys
  are reactively bound to the attribute; function values on unknown
  top-level keys are not wired to anything.
- Navigation uses `el.router(path, el.getRoot())` or
  `el.router(path)` from inside a method. **Never** `window.location`.
- Links: `extends: 'Link'` with `href: '...'` prop. Never `attr: { href }`.

### Design-system tokens (see `DESIGN_SYSTEM.md` for full conventions)

- Design system token keys are lowercase (`color`, `theme`, `typography`,
  `font`, `spacing`); values are tokens (no raw `px`, `rem`, `hex`,
  `rgb()`).
- `color`, `background`, `boxShadow`, `border`, `textShadow`, etc. follow CSS syntax but are **empowered by the scratch design system** — values can be design-system tokens (named colors, spacing keys, timing keys, CSS vars), and color tokens accept opacity + tone modifiers via the grammar below.
- Color token grammar `<colorName>(.<alphaDigits>)?(<+N|-N|=N>)?` (`COLOR_TOKEN_REGEX` in `packages/scratch/src/utils/color.js`; `colorName` may be hyphenated when every segment starts with a letter, e.g. `line-highlight`):
  - `.N` is **alpha** (`'white.5'` → `rgba(...,0.5)`), NOT a shade index — don't confuse with Tailwind's `blue-700` palette syntax.
  - `+N` / `-N` add / subtract `N` to/from **each of R, G and B** (0–255), clamped — a channel shift, NOT HSL lightness. `'black+51'` → `rgb(51, 51, 51)`; `'gray+100'` with `gray: '#4e4e50'` → `rgb(178, 178, 180)`.
  - `=N` sets HSL lightness to `N%` (absolute; hue and saturation stay).
  - Combinable: `'white.5-10'` (alpha 0.5, each channel −10), `'neutral.3=40'` (alpha 0.3 + lightness 40%).
- Border shorthand `border: '1px solid border'` works
  (`packages/scratch/src/transforms/index.js:37` resolves color tokens,
  spacing keys, CSS vars). The split form (`borderWidth` /
  `borderStyle` / `borderColor`) is the alternative when you want
  field-level reactivity. See DESIGN_SYSTEM.md "Borders" for both forms.
- `flow:` / `align:` are valid shorthands (resolved via the shorthand plugin) — `flow: 'y'` ≡ `flexFlow: 'column'`, `flow: 'x'` ≡ `flexFlow: 'row'`. Both `flow`/`align` and `flexFlow`/`flexAlign` work.
- CSS nesting: `'@dark': { ':hover': {} }`. Never chained selectors like
  `'@dark :hover'`.
- `cases.js` lives at the root of `symbols/`, NOT inside `designSystem/`.

### Collections

- Collections: `children` + `childExtends`. Never `$collection` or
  `$stateCollection`.
- For state-driven children, the canonical patterns are:

  ```js
  // ❌ Forbidden — removed
  $stateCollection: ({ state }) => state.data

  // ❌ Wrong — children doesn't see per-row state
  childExtends: 'Row',
  children: ({ state }) => state.data

  // ✅ Preferred — `childrenAs: 'state'` (decouples Row from parent state shape; reusable)
  state: { data: [] },
  childExtends: 'Row',
  children:     (el, s) => s.data,
  childrenAs:   'state'
  // Inside Row: read with `(el, s) => s.field`

  // ✅ Also valid — narrow scope via `state: 'key'` (binds Row to parent.state.data subtree)
  state: 'data',
  childExtends: 'Row',
  children: (el, s) => s             // each row gets its own state slice
  // Inside Row: declare `state: true` and read `(el, s) => s.field`
  ```

### Module exports

- `components/index.js`: `export *` (one line per file). **Never**
  `export * as` — namespace exports break the component registry.
- No imports between component files (each component file is standalone).
- `pages/index.js`: default export `{ '/': Main, '/about': About, … }`.
- `functions/index.js`, `methods/index.js`, `snippets/index.js`: also
  namespace `export *`.
- Files under non-standard folders (`lib/`, `helpers/`, `utils/`) are
  invisible to frank — move them into `functions/`, `methods/`, or
  `snippets/`, or import them from one of those.

### `extends` — string, array, or inline object

`applyExtends` (`packages/element/src/extends.js:8-26`) accepts:

- **String** — registered component name. Resolved via
  `components[name] || components['smbls.' + name]`. Supports nested
  child access too: `extends: 'Component > Child > SubChild'`.
- **Array** — multi-base composition, resolved left-to-right (later
  entries override earlier on conflicts).
- **Inline object** — raw definition merged in directly.

```js
// Single base
extends: 'Button'

// Multi-base composition
extends: ['Hgroup', 'Form']

// Nested-child reference
extends: 'AppShell > Sidebar'

// Inline object — works at runtime, but inflates JSON when serialized
// by frank. Prefer named components in components/ for anything reused.
extends: { tag: 'div', padding: 'A' }
```

What's NOT supported:

- **Function-valued extends** (`extends: () => ...`) — `resolveExtend`
  has no branch for functions; returns `null`.
- **Unquoted closures** (`extends: MyBase` from a top-of-file import) —
  works at runtime if the import resolves, but breaks frank
  serialization for publish. Use string references for any code that
  ships through frank/mermaid.

### Audit

Run `mcp__symbols-mcp__audit_component` on any component you touch before
declaring done.

---

## 3. Theming — single source of truth

**Full contract: [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md). Read it before changing anything theme-related.** Quick rules:

- The framework owns `data-theme`. **Never** call `setAttribute('data-theme', …)` from project code. The framework writes it via `resolveAndApplyTheme` (early-paint) and `changeGlobalTheme` (runtime) — **`changeGlobalTheme()` is the only supported way to switch theme at runtime.**
- Initial theme resolution (`resolveAndApplyTheme`, runs synchronously before the async init chain) follows a fixed precedence, first match wins: (1) `?globalTheme=<name>` URL param — how embedded iframes push a theme into a child app; (2) `localStorage[options.themeStorageKey]` — the user's last manual toggle (pass `themeStorageKey: false` to opt out); (3) `options.globalTheme` from project config — the configured default, where `'auto'` means "no forced theme, follow the OS live" via `prefers-color-scheme`.
- Theme is **never** in root state. Read from `el.context.globalTheme`, write via `changeGlobalTheme(newTheme[, targetConfig])` exported from `smbls`.
- Theme-conditional UI uses pure-CSS `@dark` / `@light` blocks (icon swap, alt copy, etc.) — no JS reactivity needed. `data-theme` flips atomically.
- Persistence is the **project's** job. `themeStorageKey` is read at init only — write to the same localStorage key after `changeGlobalTheme` if you want persistence across reloads.
- For multi-app pages (canvas + iframe), pass `themeRoot` to each `create()` so themes scope to their own subtree. Secondary apps get a `cssPrefix` (alphanumeric, max 6 chars from key) for atomic-class and CSS-var isolation.

Per-element shapes:

```js
// Pure-CSS theme switch — no JS plumbing
ThemeToggle: {
  SunIcon:  { display: 'none',         '@dark': { display: 'inline-block' } },
  MoonIcon: { display: 'inline-block', '@dark': { display: 'none' } }
}

// Switching at runtime — registered project function
import { changeGlobalTheme } from 'smbls'
export function switchTheme () {
  const next = this.context.globalTheme === 'dark' ? 'light' : 'dark'
  changeGlobalTheme(next, this.context.designSystem)
  try { (this.context.window || window).localStorage.setItem('my-app-theme', next) } catch (e) {}
}
```

---

## 4. Router

**No workaround needed in current framework.** The lifecycle does the right thing:

```
element create:
  triggerLifecycle('Create')
  triggerLifecycle('Complete')
  triggerLifecycle('Render')          ← user's onRender fires here
  triggerLifecycle('RenderRouter')    ← framework's onRouterRenderDefault fires here
                                        → (first render: in the next task — see below)
                                        → defaultRouter(url, element, ...)
                                        → element.set(pageDef, { ...context.domqlOptions, ...mountOptions, contentElementKey: 'content' })
                                        → element.content gets the matched page
```

`initRouter(app, context)` wires `app.onRenderRouter = onRouterRenderDefault` automatically (unless the project defines its own). `app.routes = ctx.pages` is set just before element creation, so `targetEl.routes` is populated when `defaultRouter` reads it.

**The first render runs as short tasks** (`firstRender` in `config.js`, on by default; `false` keeps one task, a number sets the chunk budget in ms, default `10`, `{ budget, progressive: true }` shows the view as it builds). The task the entry script runs in ends when `create()` is called; the design system, the shell (app root) and the first page then each start a task of their own, and the shell and the page are built in chunks. The first view is painted ONCE: the root is built outside the document and inserted when the shell and the first page are complete, so nothing on screen moves (with `progressive: true`, what follows the routed content can move as the page grows). `create()` resolves after the first view is in the document and the first page's `onRender` and `onRouteChanged` have run; no `onMounted` runs before. Every element of the first view, the root too, runs `onInit` / `onCreate` / `onRender` while its node is OUTSIDE the document, and the node stays outside until the commit, some tasks later — so a promise continuation after a hook (`await loader()` in `onCreate`) also sees `el.node.isConnected === false`. Never read that as "removed": a removed element has `el.node === null` and `el.__ref === null`, so `if (el.node && !el.node.isConnected) return` skips the swap forever on the first render and still lets a removed element through. Work that needs the node in the document (`showModal()`, `focus()`, measuring) or a swap that waits for it goes in `el.whenConnected(fn)`: it runs `fn(el)` now when connected, otherwise in the same task as the insertion that connects the node, and never for an element removed first (SYNTAX.md → Element Methods). Lazy page: `const page = await el.scope.loader(); el.whenConnected(() => el.set(page))`. The first page's hooks, `onRouteChanged`, the scroll and the hash target run in the document. An element whose children were built in a later chunk fires `onCreate` → `onRender` after its last child; hooks keep the order of a synchronous build. Code after `create()` in `index.js` runs before the design system is prepared; `DOMContentLoaded` and `load` can fire before the app is in the document. A boot whose document goes away during that wait (an iframe app whose host removes the frame, a test whose window closes) stops: `create()` resolves with the bare definition, nothing mounts, no root `onCreate`, no error (smbls 3.14.841); await `create()` before a teardown when the app must finish. A route guard that awaits keeps `create()` waiting no longer than before (the shell goes in, the page later — built outside the document in chunks and inserted whole). The page is created with the app's `domqlOptions` (a `domqlOptions.mountYield` now reaches routed pages too), and after the first render reconciles, `if:` and navigations build in one go again. A server render keeps one task.

**Rows go in whole** (`@symbo.ls/element` `mountWhole`, set by smbls for the first render and for the adoption of a pre-rendered page, never after). An element whose children are still being built waits outside its parent and goes in with one insertion when its last chunk is in, before its `onCreate`. So a row that reaches the live document while the first render still yields (a fetched list a state update builds as the root goes in) is never on screen with only its first children. A first render with `progressive: true` does not hold rows; a project's own `domqlOptions.mountWhole` wins. `@symbo.ls/element` exports `mountIdle()` (`true` when no deferred mount work is queued now) beside `whenMountIdle()`: a promise that settles as the queue drains can queue more work before the `whenMountIdle()` caller resumes, so re-check with `while (!mountIdle()) await whenMountIdle()`.

**A pre-rendered page is adopted in the same short tasks** (§8 → Hydration). The adoption starts a task of its own; the shell and then the first page are built over the server markup in chunks of the budget (about 10 ms). The server's nodes stay on screen while each element takes its own, so nothing visible changes between tasks. A click on a server node whose element is not built yet is held (no default action, no handler) and dispatched again, once, on the same node when the adoption is done; an element already adopted handles its own events at once. `firstRender: false` adopts in one task, as before. A page the client REPLACES (no registry: `hydrate: false`, a platform pre-render) builds in the same short tasks (since smbls 3.14.859): the app is built outside the document while the server's page stays on screen with its styles, and the server's markup and styles go in the task that inserts the app — never both pages, never neither. `progressive: true` does not apply to a replace; `firstRender: false` replaces in one task.

`onpopstateRouter` registers a `popstate` listener (removed by `destroy(app)`) so back/forward navigation re-runs the router — inside `customRouterElement` when one is configured, with the app-wide `router.guards`.

**Anti-patterns to delete on sight:**

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

// ❌ window.location for nav
window.location.href = '/about'

// ✅ Use the router method
el.router('/about', el.getRoot())
```

Customizing the router target element (e.g. routing inside a layout instead of at root):

```js
context.router = { customRouterElement: 'AppShell.Main' }   // dot path
// or
context.router = { initRouter: false }                       // disable auto-init
```

Default `routerOptions` (from `@symbo.ls/router` README): `pushState`, `replace`, `popState`, `scrollToTop`, `injectRouterInLinkComponent`, `useParamsMatching`, `removeOldElement`, `level`, `contentElementKey: 'content'`, `exitTimeout: 300` (the longest wait for an `onRouteExit` exit before the page swaps; see SYNTAX.md → Router → Route events). Create-time options in `config.js` `router`: `customRouterElement`, `guards` (app-wide; they also run on Back / Forward, where a refusal puts the address back and a redirect replaces the entry; a guard that answers directly, not with a promise, is not awaited; a newer navigation wins over one still waiting on an async guard), `keepSamePage` (only another page swaps; also per call), `scrollRestoration: 'restore' | 'manual' | 'auto'` with `scrollRestoreTimeout` (default `1000` ms) (SYNTAX.md → Router). `scrollNode` defaults to the viewport of the document the app renders into, so an iframe app scrolls its own frame.

**Replace, do not push, for a redirect.** `el.router(path, el.getRoot(), {}, { replace: true })` (or `app.navigate(path, { replace: true })`) rewrites the current history entry with `history.replaceState` — a legacy-URL forward, a canonical rewrite, or a filter/query change then adds no Back-button entry. `replace` only picks how the entry is written; `pushState: false` still writes none, so a `{ pushState: false }` "redirect" renders the new route but leaves the OLD URL in the address bar. Never hand-write `history.replaceState` next to a router call. Available after `@symbo.ls/router` 3.14.601 (smbls repo commit `9f498831e`); up to smbls 3.14.805 the option is ignored and the call pushes. Full example: SYNTAX.md → Router → "Replace instead of push".

**A router that shows a base path — `routerHref`** (since attrs-in-props 3.14.697 / default-config 3.14.794). An app whose own `router` function shows an address its routes do not carry (for the route `/notes` it shows `/w/<org>/<workspace>/notes`) registers `routerHref(href, el)` beside it, found as `Link` finds `router`: `functions`, then `snippets`, then `utils` (`this` is `el` too). The rendered `href` of a `Link`, and of any `<a>` / `<area>`, goes through it, so a Cmd / Ctrl / Shift / middle click, "Copy link address" and the status bar name the address a plain click shows, not a bare path that boots another app state. A plain click still routes the `href` as written. Only an in-app path reaches the hook (`/…`, never `//…` or `/\…`); a fragment, a query, a relative path, every scheme and a `<link>` / `<base>` / SVG `href` stay as written. No hook: the same `href` as before. A hook that returns no string keeps the `href`; one that throws keeps it and logs one `console.warn`. On a `Link` the `href` is a tracked effect: a hook that reads root state (read it first, before any early return) runs again when that state changes. A plain anchor's static `href` is mapped when it is written (mount, `el.update({ href })`); give it a function `href` to follow state.

```js
// functions/routerHref.js — the address a plain click on an in-app link shows
export const routerHref = function routerHref (href, el) {
  const base = el.getRoot().state.base   // read first: a Link's href follows it
  return base ? base + href : href
}
```

Param routes: `{ '/blog/:id': BlogPost }`. Wildcard fallback: `{ '/*': NotFound }`. Param routes are skipped by `smbls brender` since they need runtime data.

### Three router patterns (legacy projects)

Older projects ship with one of three router setups. Always prefer
**Pattern A** for new work — Patterns B/C exist only for compat with
legacy projects.

**Pattern A — Empty `app.js` + framework routing (preferred).** Routes
defined in `pages/index.js`, framework wires everything:

```js
// app.js
export default {}                                  // or { Modals: {} }, root-level chrome only

// pages/index.js
import { home }  from './home.js'
import { about } from './about.js'
export default { '/': home, '/about': about }
```

**Pattern B — Layout + `Folder` nesting (legacy).** Uses inline `define`
block, custom `router` function, sets `Top/Cnt/Bottom` slots:

```js
export default {
  extends: 'Layout',
  define: { routes: (param) => param },
  routes: { '/': {}, '/section-a': SectionA },
  Folder: { if: (el, s) => s.root.active !== '/' },
  on: {
    render: (el) => {
      router.call(el, window.location.pathname, {}, 1)
      window.onpopstate = () => router.call(el, window.location.pathname, {}, 0)
    }
  }
}
```

**Pattern C — Layout + simple `Content` slot (legacy).** Uses
`el.call('router', ...)` from `onRender`:

```js
export default {
  extends: 'Layout',
  define: { routes: (param) => param },
  onRender: (el) => {
    if (el.__initialized) return
    el.__initialized = true
    el.call('router', window.location.pathname, {}, true)
    window.onpopstate = () => el.call('router', window.location.pathname, {}, false)
  }
}
```

**Why Pattern A wins:** Pattern C crashes on every route change with
`Cannot read properties of undefined (reading 'node')` because
`el.set()` returns `undefined` rather than the new element.
Pattern B's `Folder.set({ [route]: {...} })` plumbing is brittle for
the same reason. **Always prefer Pattern A unless you have a documented
reason for custom routing.**

### SPA routing rules

- `<a>` tags with `onClick` handlers MUST call `e.preventDefault()`,
  otherwise the browser does a full page reload.
- Don't add capturing click listeners on `document` — they intercept link
  clicks before the router gets them and break SPA routing.
- Don't roll your own `pushState`/`popstate` plumbing. The framework
  already wires `onpopstate` via `onpopstateRouter(element, context)`.
- For programmatic nav: `el.router(path, el.getRoot())`. For declarative
  links: `extends: 'Link', href: '/path'` (the framework injects router
  click handling into the `Link` component). `Link` routes only a plain
  primary-button click on a same-tab link: modified clicks (Ctrl/Cmd/Shift/
  Alt), a middle click, `target` other than `_self`, `download` and an
  already-prevented click stay the browser's.

---

## 5. `@symbo.ls/fetch` — declarative data

Full reference: `plugins/fetch/README.md`. Auto-registered when `config.js` sets `fetch` (the adapter config, resolved onto `context.fetch`). `db` is not a config key — it is the usual name of the adapter `getDB()` returns.

### Configure once in `config.js`

```js
fetch: {
  adapter: 'rest',                        // 'rest' | 'local' | a registered adapter name
  url: 'https://xxx.supabase.co/rest/v1', // e.g. Supabase's PostgREST endpoint
  headers: { apikey: 'sb_publishable_...' },
  fetchOptions: { credentials: 'include' },
  auth: { baseUrl: '…', sessionUrl: '/me', signInUrl: '/login', signOutUrl: '/logout' }
}
```

### Custom adapters — `registerAdapter`

```js
import { registerAdapter } from '@symbo.ls/fetch'

// the loader resolves to a module that exports `setup(options) => adapter`
registerAdapter('api', () => import('./adapters/api.js'))

// config.js
fetch: { adapter: 'api', /* options passed to setup() */ }
```

A registration shadows a built-in of the same name (`rest`, `local`). An element made before its adapter registers waits for it up to about 5 s, then fails with `Unknown db adapter`.

**An adapter that cannot open fails only its queries** (since `@symbo.ls/fetch` 3.14.676 / smbls 3.14.864). When `setup()` throws, every run that needs the adapter fails as a failed request does: the element gets its error status, and `onFetchError` runs on the element and on the query (the `fetch:` item). The next run tries the adapter again. A `smbls build` pre-render no longer ends on such a throw. So an adapter may throw in `setup()` when its client is missing (no SDK client in a server render): that query errors, and the page still builds. Show the element's empty or error state for it; the client fetches again after the takeover.

### Declarative fetch on an element / app

```js
fetch: [
  { from: 'venues', as: '~/venues', cache: '5m', order: { by: 'rating', asc: false } },
  {
    from: 'transactions', schema: 'core',
    as: '~/adminTransactions',
    select: '*,users(display_name,email)',
    cache: '2m',
    onFetchComplete: (data, el) => el.state.root.update({ transactionsLoading: false }, { preventFetch: true })
  }
]

// Single fetch shorthand
{ state: 'articles', fetch: true }                 // table name = state key
{ state: 'data', fetch: 'blog_posts' }              // string shorthand
{ state: 'item', fetch: { method: 'rpc', from: 'get_item', params: { id: 1 } } }

// Mutations
{ tag: 'form', fetch: { method: 'insert', from: 'contacts', on: 'submit', fields: true } }

// Binary / streamed response (REST) — a Blob / ArrayBuffer / stream / Response lands in state only under `as`
{ state: { answerAudio: null }, fetch: { from: '/voice/answer', responseType: 'blob', as: 'answerAudio' } }
```

### Cache, retry, dedupe, focus refetch — all default-on

Defaults: `cache: { stale: '1m', gc: '5m' }`, `retry: 3` (exp backoff) for reads and none for writes (`insert` / `update` / `upsert` / `delete` / rpc actions — a timed-out write may have been applied), `refetchOnWindowFocus: true`, `refetchOnReconnect: true` (in the browser: a server render binds no focus, reconnect or `refetchInterval` refetch). A forced refetch (`el.__ref.refetch()`, each `refetchInterval` tick; a reconnect up to smbls 3.14.860, see below) reaches the network even while the entry is fresh. A shared in-flight request that fails gives every element on it the error. Override per-fetch:

```js
{ fetch: { from: 'X', cache: false, retry: false, refetchOnWindowFocus: false } }
```

**A refused request is not sent again** (fetch after 3.14.678 / smbls after 3.14.870). The answer's status decides the retry: the result's `status` (the REST adapter's), else the error's `status` / `statusCode` (the SDK's errors), returned or thrown. A 4xx is sent once and reaches `onFetchError` at once, also under an explicit `retry` count (a count is for transient failures). A 408, a 5xx, a network failure and an error with no status keep the retries (1 s / 2 s / 4 s apart by default). A 429 is sent again once, after the server's `Retry-After` (seconds or an HTTP date; the `delay` when there is none; no retry when it asks for more than the backoff's 30 s cap). The REST adapter carries a failed answer's `Retry-After` header as `retryAfter` on its result when the server sends one. A custom adapter gives a refused result (or the error it throws) a `status`, so a refused read costs one request — a page that reads a rate-limited public endpoint no longer spends four requests on one refusal.

**Reconnect, one answer per element, a language switch** (since smbls 3.14.862 / fetch 3.14.675). A reconnect asks once per key: the window `online` event marks the page's store, then each mounted declaration runs as a refresh (the cache skipped, a request on its key that started after the mark shared), so N declarations of one key send one request. A request out from before the reconnect is never shared: it may have been sent offline. `refetchInterval`, `el.__ref.refetch()` and `fetchNextPage` stay forced. An element takes each answer once per declaration: a focus refetch that joins the element's own create-time request does not run `onFetchComplete` again, and an older reply never replaces a newer answer's rows or turns them into an error. A language switch (polyglot `setLang`, or a host writing root `lang`) runs the create-time queries on screen again in the new language: a fresh entry on the new key answers from the cache, a request in flight on it is shared, else one request goes out; an answer for a language the element no longer asks for is not delivered. A page that switches its language in the root `onRender` (a browser that lists `ka`) gets the new language's rows after the switch, not the start language's.

### State path syntax

- `~/key` — root state (e.g. `as: '~/venues'`)
- `../key` — parent state
- `dashboard/stats` — nested path
- omit `from` and let it derive from `state` key

### Triggers

`on: 'create'` (default) | `'click'` | `'submit'` | `'stateChange'` — or a list of them. For `'stateChange'`, `params: (el, s) => ({ q: s.query })` re-fetches when what `params` / `enabled` / `skip` / `page` resolve to changes — not on create, not when its own rows land. Removing the element releases its timers, listeners, watcher and subscription.

**A list of triggers** (fetch after 3.14.671): `on: ['create', 'stateChange']` is one config, one `params`, that loads on create and runs again when its inputs change — a list page that follows its filter needs no second config. Each trigger in the list does what it does alone; with `'create'` in it the config keeps everything a create-time query has (cache entry, focus / reconnect / interval refetch, invalidation, seeded and early answers). `'submit'` / `'click'` in a list make an `rpc` an action. A list of one is that trigger, an empty list is `'create'`, a repeated trigger counts once.

```js
export const ArticleList = {
  state: { kind: 'texts', rows: [] },
  fetch: { from: 'articles', params: (el, s) => ({ kind: s.kind }), on: ['create', 'stateChange'], as: 'rows', cache: '5m' },
  text: (el, s) => s.rows.map((row) => row.title).join(', ')
}
```

### Optimistic updates + cache invalidation

```js
{
  fetch: {
    method: 'update', from: 'posts',
    params: (el) => ({ id: el.state.postId }),
    on: 'click',
    optimistic: (data, current) => ({ ...current, likes: current.likes + 1 }),
    invalidates: ['posts']     // every key CONTAINING "posts"; true or '*' = the write's own `from`
  }
}
```

After a successful write the matching entries go stale and the queries MOUNTED on them refetch at once (others on their next mount). A match is a substring, a RegExp or `(key) => boolean`. An `rpc` is an ACTION — sent on every trigger, never cached or shared, runs its `invalidates` — when a click / submit fires it, when it declares `invalidates`, or with `mutation: true` (`mutation: false` keeps a clicked read cached).

### Infinite queries

```js
fetch: {
  from: 'messages',
  limit: 20,
  infinite: true,
  getNextPageParam: (lastPage) => lastPage.length < 20 ? null : lastPage.at(-1).id,
  getPreviousPageParam: (firstPage) => firstPage[0]?.id  // bidirectional
}
// el.__ref.fetchNextPage(), .fetchPreviousPage(), .__hasNextPage, .__pages
```

### Imperative

```js
const db = await this.getDB()
const { data, error } = await db.select({ from: 'articles' })
// also: db.insert / .update / .upsert / .delete / .rpc; auth where the adapter keeps sessions: .getSession / .signIn / .signOut / .setToken (REST)

// REST adapter — every call takes responseType: 'auto' (default) | 'json' | 'text' | 'blob' | 'arrayBuffer' | 'stream' | 'response'
const { data: blob } = await db.select({ from: '/reports/q3.xlsx', responseType: 'blob' })              // a Blob
const { data: stream } = await db.insert({ from: '/ask', data: { question }, responseType: 'stream' })  // a ReadableStream (SSE)
await db.insert({ from: '/voice', data: formData })                                                     // FormData / Blob / ArrayBuffer bodies are sent as they are
await db.select({ from: '/me', headers: { Authorization: `Bearer ${userToken}` } })                     // per-call headers win over the configured ones

// the query cache from project code — registered as functions whenever `fetch` is configured.
// Project code cannot import `queryClient` from '@symbo.ls/fetch' (frank serializes that import to a stub).
await this.call('invalidateQueries', 'articles')                // mounted queries refetch; resolves when they settle
this.call('removeQueries', /^articles:select:/)                  // next mount loads without stale rows
this.call('getQueryData', { from: 'articles' })                  // a key, or a config keyed like this element would key it
this.call('setQueryData', 'articles:select:', (old) => [...old, newOne])
```

`responseType` and per-call `headers` also work in a declarative `fetch:`. Worked examples (SSE read, Blob download, FormData upload): SYNTAX → Data Fetching.

### Early requests — `fetch.early` (REST adapter, opt-in)

The first view's GETs can start while the HTML is still parsing; the REST adapter then ADOPTS each answer for the first call that asks for exactly that request instead of sending it again:

```js
// config.js
fetch: {
  adapter: 'rest', url: 'https://<project>.supabase.co/rest/v1', headers: { apikey: '<publishable key>' },
  early: {
    query: { apikey: 'apikey' },          // configured headers sent as query parameters (no CORS preflight)
    rpc: 'get',                           // read-only RPCs go early as GETs (PostgREST); else only `select`
    always: (params, ctx) => [{ from: 'site_settings', select: 'key,value', lang: false }],
    routes: {                             // route pattern (as in pages) → that page's first-view requests
      '/': [{ method: 'rpc', from: 'get_content_rows', params: { p_table: 'articles', p_limit: 20 } }],
      '/blog/:id': ({ id }, ctx) => [{ method: 'rpc', from: 'get_content_rows', params: { p_slug: id, p_limit: 1 } }]
    },
    maxAge: 30000                         // ms; an older answer is not adopted
  }
}
```

- A request is the adapter call it stands for (`method` `'select'` / `'rpc'`, `from`, `params`, `select`, `limit`, `offset`, `order`, `single`). A function form runs before the app: no imports, no project functions — only its arguments (`ctx = { path, query, lang, storage(key), meta(name), prerendered }`) and browser globals.
- The script asks in the language the app starts in (§6 → The start language): the address's (`/en/…`), else the stored choice, else `state.lang`, else `polyglot.defaultLang`. It embeds the same rule polyglot uses, so its `Accept-Language` is the app's.
- Adopted only when it is the same request: same address, same `Accept-Language` (set `lang: false` for a call that sends none), no other headers — a signed-in call never takes the anonymous answer. Each answer is taken once; a failed one, an expired one, or one still waiting after an invalidation is not.
- `early.query` and `early.rpc` default to `fetch.reads` (SYNTAX → Anonymous reads), which makes the call itself send the same anonymous GET; declare them once in `reads`.
- `smbls build` (and `smbls deploy`) writes the script as `early.<hash>.js`, referenced right after the page's `<meta charset>` (the charset declaration stays first; since cli 3.14.826, also on a page without a `<head>` tag), else first in `<head>` (a file, so a CSP without `'unsafe-inline'` allows it) — the optimized page included (unquoted attributes, no `<head>` tag). With `fetch.early` set and nothing added (no app script on the page, no request the script can make), the build prints `Early data requests not added: <reason>`. `smbls start` does not emit it. Without `fetch.early` nothing changes.
- **Request lists given as data are made at build time** (since fetch 3.14.677 / cli 3.14.830). When every request list is data (no function in it, no request chained with `after`), the build makes each request's address and identity with the adapter's own code, and the script only sends them: one list of settings is under 0.3 KB Brotli. A request list that is a function is decided in the browser, by the script's own code. A request with a key the declaration's text never names (a computed `order`, `limit`, `offset` or `single`) is not sent early; the app sends it as usual.
- **Inline — `inline: true`** (since cli 3.14.830). As a file the script shares the line with the app's script, its preloads, the fonts and the first photo: on slow 4G it can arrive long after the page, and its requests start only then. `fetch.early.inline: true` writes the script into the page at the same place, `<script data-symbols-early>…</script>`, so its requests start as the parser reaches it. A CSP without `'unsafe-inline'` allows it by its hash: the build logs it (`Allow the inline early script with 'sha256-…' in script-src`) and writes it in the page report (`early: { mode: 'inline', hash, bytes }`); `smbls csp` lists it with no build (since cli 3.14.831; CLI.md → `smbls csp`). Every page built from the shell carries the same script, so one hash allows it everywhere; the hash changes when the declaration or the CLI changes. The page grows by the script's bytes, and a returning visitor gets them with each page instead of from the cache. A script whose text holds `<!--` or `</script` stays a file, and the build says why.
- **When the script decides, and on which pages** (fetch 3.14.670). The script comes right after the page's `<meta charset>` (else it is the head's first child), so at once it sees nothing after itself. Without the options below it decides at once, as before.
  - `wait: 'head'` — the requests are decided once the head is parsed (`DOMContentLoaded` at the latest). A request function can then read a later head tag: `ctx.meta(name)` is the `content` of `<meta name="…">` (`null` when absent), so an edge's `<meta name="hero" content="spring">` asks for that entry in the same round trip as the page.
  - `prerendered: 'skip'` — send nothing on a page built ahead (its head has `<meta name="brender">`; it carries its own answers, `fetch.seed`). Implies `wait: 'head'`. The app shell (`200.html`) still gets its requests.
  - `prerendered: 'omit'` (since fetch 3.14.678 / cli 3.14.832) — `smbls build` leaves the script out of every page brender builds ahead (the inline script, or the file's tag), and the app shell (`200.html`, the client-rendered routes) keeps it. With `'skip'` the browser still parses and runs the script on a built page (measured: ~25 ms of blocking time per page), and its hooks and the project's own `script` module run there too; with `'omit'` nothing of it runs there. For built pages that carry their language and their answers. A built page is the same page less exactly the tag and the line it was on; `brender.beforeWrite` gets it without the script. The build log says how many pages went without it, the page report marks `early.builtPages: 'omit'`, and `smbls csp` keeps the inline script's hash (the shell needs it), marked "the app shell only". A built page that carries the script anyway (one the build did not make) stands it down as `'skip'` does.
  - `<meta name="smbls-early" content="off">` in one page's head — that page sends nothing (read with `wait: 'head'` or `prerendered`).
  - `ctx.prerendered` — `true` on a page built ahead, for a request function that chooses per request.
- **A smaller page of a list — `slice: true`.** A select with a `limit` (no `offset`, not `single`) and `slice: true` also answers a call that asks the same with a SMALLER limit: the call takes the first rows, once, and sends nothing. A call for more rows, another offset, filter or order asks the network.
- **`firstPaint(ctx)`** runs once, at the page's first paint (long before the app takes over a page built ahead, where `afterFirstView` runs): below-the-fold work, a beacon. It must stand alone, as a request function; it runs on every page the script is on.

```js
// config.js — fetch.early
early: {
  wait: 'head',
  prerendered: 'skip',
  routes: {
    '/:lang': ({ lang }, ctx) => [
      { from: 'entries', select: 'id,title', order: 'published_at.desc', limit: 24, slice: true },   // a list asking limit 6 takes the first 6
      ctx.meta('hero') && { from: 'entries', params: { slug: 'eq.' + ctx.meta('hero') }, single: true }
    ]
  },
  firstPaint: (ctx) => { /* self-contained: no imports, no project functions */ }
}
```

**fetch 3.14.671 / smbls 3.14.857 / cli 3.14.823 additions (all opt-in):**

- **`slice: '<limit argument>'` for an rpc** — `slice: 'p_limit'` makes an rpc answer stand in for the same rpc with a smaller `p_limit`, as `slice: true` does for a select (the call takes the first rows, once).
- **`adopt: 'init'`** — the script reads each answer as it comes in, and an element whose create-time query (`select`, or a read `rpc`, with a `cache`) asks for exactly an answer that is in takes it AT ITS INIT: it renders with its data from its first render, no loading look, one `onFetchComplete`. Only on the app shell (on a page built ahead the adoption stays as it is). Implies `wait: 'head'`. With `adopt: 'init'`, an early answer with FEWER rows than the call asks for is the call's **first part**: the element shows it at its init and asks for all rows at once; their answer replaces the first part.
- **A first part's status is for the view, not for `transform`.** While the full answer is on its way the element is fetching (`el.__ref.__fetchStatus.isFetching`). `transform` runs for the first part AND for the full answer and cannot tell them apart. Keep "more rows" logic (a "Show more", a filter bar) in the view, behind `isFetching`, never in `transform`.
- **`startLang(ctx)`** — names the language the first view is in, for a project whose languages are data or whose addresses decide the language its own way. The requests ask in it, `ctx.lang` is it, and the script stores it as polyglot's choice (`polyglot.storageLangKey`) before the app starts, so the app starts in it too. Runs at once on every page the script is on. The app starts in its answer in every `polyglot.addressLang` mode, `'strict'` included (the script records it — utils `polyglotEarlyStartLang` — so the start does not depend on the stored copy, which `'strict'` never reads). `null` / `''` keeps the built-in rule and stores nothing. A request's `lang: '<code>'` asks in a language of its own (`lang: false`: none).
- **`firstView(ctx)`** — runs once the first view is in, for work that must not compete with it (a beacon, page views): after smbls reports its first view (on a page built ahead: after the takeover), the page has loaded and painted its first content, at the next idle moment (2 s at most). A background tab counts paint 5 s after load; an app that never reports is not waited for past 20 s after load.
- **`script: './early.js'`** — bundles the project's own pre-boot module (relative to the project's source directory; it may import what it likes) into the same `early.<hash>.js`: one request instead of two. The module runs first, on every page, before the requests. Its exported hooks `startLang`, `firstPaint`, `firstView`, `afterFirstView` are the script's, with the module's closure. A hook declared in `fetch.early` AND exported stops the script's build (`Early data requests skipped: … declared twice`). Remove the module's own `<script>` from the page. The module is pre-boot code, not app code: it runs before DOMQL exists, so browser globals are fine there, and it never ships through frank. frank-audit (after 3.14.782) reads `fetch.early.script` from `config.js` and audits the module and every file it imports as pre-boot code (slot `preBoot`): the app-only rules (DOM APIs, `addEventListener`, `window.fetch`, window assignments, FA006 orphan) do not report there; FA905 (hardcoded deploy values) still does. A file in a canonical folder that the module imports (`functions/x.js`) ships in the app too and keeps every rule.

```js
// config.js
fetch: { adapter: 'rest', url: '…', early: { script: './early.js', adopt: 'init', routes: { '/': [/* … */] } } }

// symbols/early.js
let views = 0
export const startLang = (ctx) => /^\/en(\/|$)/.test(ctx.path) ? 'en' : 'ka'
export const firstView = (ctx) => { views++ /* the beacon */ }
```

### A pre-built page shows the data of its build — `fetch.seed`

A page `smbls build` pre-rendered carries the answers its render got (§8), and the calls that take them never reach the server: its visitor sees the **build time's** data until the next build. `fetch.seed` tells a page its data is stale (`isStale`, `maxAge`, or `<html data-smbls-stale>` from the host); it then shows the build's data at once and, after the adoption, asks again for exactly what took a recorded answer. `fetch.seed: false` adopts no recorded answer. Config, example and the refresh contract: SYNTAX.md → Data Fetching → A pre-built page's data. When to use it: PATTERNS.md → Pre-built pages and fresh data.

### Auth guard

`{ fetch: { from: 'profile', auth: true } }` — fetch only fires when `db.getSession()` returns a session.

### Status surfaces

`el.__ref.__fetchStatus = { isFetching, isLoading, isStale, isSuccess, error, status, fetchStatus }` (`plugins/fetch/index.js`). Also `__fetching` (mirrors `isFetching`), `__fetchError` (mirrors `error`). Callbacks: `onFetchStart`, `onFetchComplete`, `onFetchError`.

Note: there is no `isError` boolean field — derive from `!!__fetchStatus.error` if needed.

A first part shown at init (`fetch.early` `adopt: 'init'`, a smaller early answer) keeps the element fetching until the full answer is in: read `isFetching` in the view (hide a "Show more" meanwhile), never in `transform` (it runs for both answers).

### Anti-patterns

- Don't bypass adapter — `await fetch(...)` from inside DOMQL skips cache, retry, dedupe, optimistic, and the `Accept-Language` header injection. Streaming (SSE), binary downloads and multipart uploads are no exception: the REST adapter reads them through `responseType` and sends `FormData` / `Blob` bodies as they are (see Imperative).
- Don't ship a client or a function in the `config.js` `fetch` config (RULES.md Rule 59): only plain options survive publish — the served runtime deletes `fetch.createClient`. The exceptions are self-contained functions that use only their arguments: `fetch.early` request lists and `fetch.seed.isStale` / `onRefresh`. Don't configure under `db:` (never read) or `adapter: 'supabase'` (the Supabase adapter was removed; use the REST adapter on the PostgREST endpoint, or a registered adapter).
- Don't write to state inside a fetch's own `transform` and a parent's `onFetchComplete` for the same key — race on cache resolution. Pick one.

---

## 6. `@symbo.ls/polyglot` — i18n

Full reference: `plugins/polyglot/README.md`. Auto-registered when `context.polyglot` is set; auto-merges `polyglotFunctions` into `context.functions`.

⛔ **Never import `@symbo.ls/polyglot` / `@symbo.ls/polyglot/functions` in
project code** (`plugins: [polyglotPlugin]`, `functions: { ...polyglotFunctions }`).
The runtime does both itself from `context.polyglot`. Under `smbls push` the
package is not a declared library, so frank STUBS the import: the payload
ships `plugins: [""]` and, when the spread enumerates, `functions.polyglot: ""`
— a stub phantom that sat on the built-in's key and made
`el.call('polyglot', key)` return `undefined` on every published page.
The runtime now drops non-plugin entries and lets a real function win over a
phantom, but the import is still dead weight that only exists to be stubbed —
delete it.

### Static translations

```js
context.polyglot = {
  defaultLang: 'en',
  languages: ['en', 'ka', 'ru'],
  storageLangKey: 'myapp_lang',     // localStorage key for active lang
  storagePrefix: 'myapp_t_',        // localStorage prefix for translations
  fontWait: 3000,                   // ms setLang waits for the new labels' font faces (default); false = no wait
  prefetch: true,                   // warm the other languages' labels + faces at idle (default false)
  translations: {
    en: { hello: 'Hello' },
    ka: { hello: 'გამარჯობა' },
    ru: { hello: 'Привет' }
  }
}
```

**One copy in the payload — `translationsFrom`** (frank after 3.14.810; utils after 3.14.859, smbls after 3.14.870, brender after 3.14.680, mermaid after 3.14.850, sync after 3.14.708). When an app's `translations` ARE its design system's lang map (`translations: lang`, `lang` imported from `designSystem/lang.js`), `frank.toJSON` — so `smbls push` — writes the polyglot config with `translationsFrom: 'designSystem.lang'` in the place of `translations`. JSON writes a shared object at each place it occurs, so the payload used to carry the map twice. `translationsFrom` is a dotted path from the project's root. Every framework reader puts the map back before it reads the config: the runtime's context (before shared libraries merge in), a server render (brender), mermaid's head and start-up script, each shared library merge, a livesync snapshot. With `translations` as well, the named map is the base and `translations` adds to it, per language. Code of your own that reads a payload's `polyglot.translations` (a script over the stored JSON, a server of your own) resolves the pointer first, with `@symbo.ls/utils`: `polyglotTranslations(project, polyglot)` returns the map, `resolvePolyglotTranslations(project)` writes it back in place, `withPolyglotTranslations(project)` returns a view and leaves the payload as it is. A reader older than these releases (a self-hosted server on an older brender or smbls) finds no static strings in such a payload, and the keys show: update it together with the CLI. A root-level `lang.js` (PATTERNS.md → Polyglot) is not the design system's map, so frank writes its `translations` as they are.

### Server translations (CMS-backed, stale-while-revalidate)

```js
context.polyglot = {
  defaultLang: 'ka',
  languages: ['ka', 'en'],
  fetch: {
    rpc: 'get_translations_if_changed',  // RPC: (p_lang, p_cached_version) → { changed, version, translations }
    table: 'translations'                // for upsert (CMS edit)
  }
}
```

Mixed mode: ship `translations` in the bundle (UI strings) and add `fetch` (content strings) — server overrides static when loaded.

### Warming the other languages — `prefetch`

`polyglot.prefetch: true` (or `'idle'`; polyglot after 3.14.611) makes a first `setLang` to another language instant: once per app, after the active language's labels, when the page has loaded and the browser is idle (`requestIdleCallback`, 2 s at most; a task later where there is none), each other language in `languages` loads through `loadTranslations` — the project's own, when it has one — one at a time, into the root state and storage (so the switch applies the stored copy at once), and then the font faces its letters need load in the body's font (`document.fonts`). Static labels warm their faces only. Skipped when the browser asks to save data (`navigator.connection.saveData`) and in a realm without a window; a server render (brender) switches it off for its renders. Replaces a project's own "load every other language on `load`" function.

### The start language

The app starts in ONE language, chosen before the first render (smbls `prepareState`, polyglot's `initPolyglot` and the `fetch.early` script share the rule):

1. the address's language — `/en/about` with `languages: ['ka', 'en']` starts in `en` (the first path segment, when it is one of `languages`, else of the `translations` keys; case does not matter);
2. the stored choice (`storageLangKey`);
3. the state's `lang`, else `defaultLang`, else `'en'`.

`polyglot.addressLang` sets step 1: `true` (default) — the address wins over a stored choice; `'fallback'` — a stored choice wins, the address only replaces the default; `'strict'` — the address alone decides (an unprefixed address is the default language's page, whatever is stored); `false` — the address is never read. `{ mode: 'strict', except: ['/admin'] }` (polyglot 3.14.610) uses `mode` everywhere except under the `except` paths, which take `true`: public pages strict, the admin in its staff's last language. A path matches the address's first segments (`/admin` matches `/admin/x`; `:param` matches one segment). The first render, its declarative fetches (`Accept-Language`), the labels and a router's language guard all see the start language, so a first visit to `/en/…` asks for and shows only English. The address's language is never stored (it is not a choice); `setLang` stores one. Ahead of all steps: the language the pre-boot `fetch.early.startLang(ctx)` hook chose for this page load wins in every mode (a hook returning `null`, an admin's, chooses none). `polyglot.defaultLang` may be a function `(polyglot) => code` (a default that is data), called each time the default is asked; the pre-boot script carries its source and calls it there with `{ languages }`. A server page asks it too: `smbls start` (the runner), brender and mermaid write its answer in `<html lang>`, also when the payload holds the function as its source text (frank JSON), which they compile as the browser does. A runtime that compiles no code from text (a Worker; mermaid's `evalAvailable: false`) keeps the fallback `'en'` there and never throws; the browser applies the answer at boot. Example: SYNTAX.md → Polyglot → The start language.

### Using translations in components

The functions registered by `polyglotFunctions` (verified at
`plugins/polyglot/functions.js:5-15`) are:

```
polyglot          → translate(key, lang?)
getLocalStateLang → reads `state.<key>_<lang>` for per-language state fields
getActiveLang     → reads state.root.lang or context.polyglot.defaultLang
getLang           → alias for getActiveLang
setLang           → switch (async): persist first, wait for labels + their font faces (polyglot.fontWait,
                    default 3000 ms; false/0 = no wait), then text, state.root.lang and <html lang> in ONE frame;
                    the last call wins; setLang(lang, { persist: false }) stores nothing
getPendingLang    → the language a switch is waiting for, or null (reactive — a busy state; no state key)
getLanguages      → array of available language codes
loadTranslations  → load a lang's labels — one load per lang PER APP: a second call while one is in flight gets
                    its promise; loadTranslations(lang, { inFlight: true }) starts nothing and answers the
                    app's load in flight, or undefined
upsertTranslation → CMS write (optimistic + persists)
```

There is **no** `t` or `tr` function — use `polyglot` for both reactive
and non-reactive lookups. Reactivity for text comes from the
template-literal mechanism in
`packages/utils/string.js:48-62` (`{{ key | filterName }}`), which
re-evaluates inside text-effect createEffect on state change:

```js
// Reactive — text-template effect re-evaluates `polyglot('hello')` on
// every state.root.lang change.
{ text: '{{ hello | polyglot }}' }

// Imperative call (non-reactive — captures the value at evaluation time):
{ text: (el) => el.call('polyglot', 'hello') }

// Per-language state field (e.g. CMS title_en / title_ka):
{ text: '{{ title_ | getLocalStateLang }}' }

// Switch language (the person's choice: persisted to localStorage)
{ onClick: (e, el) => el.call('setLang', 'ka') }

// A switch that is NOT the person's choice (a language the host resolved,
// the echo of a choice another tab stored): the screen switches, storage is
// untouched, so no `storage` event reaches other tabs
{ onRender: (el) => el.call('setLang', 'ka', { persist: false }) }

// Read current language
{ text: (el) => el.call('getLang') }
```

### Auto integration with fetch

When polyglot sets `state.root.lang`, every declarative `fetch` request
(queries and writes) gets an `Accept-Language` header automatically, and a
query's cache key ends in `:<lang>`; a `getDB()` call sends no language unless
you pass the header (`plugins/fetch/index.js`). The header is the only injection;
fetch does NOT add a `lang` query parameter or RPC argument. If your
backend expects `lang` in `params`, set it explicitly:

```js
fetch: { from: 'articles', params: (el, s) => ({ lang: s.root.lang, status: 'published' }) }
```

### Labels on an adopted page

On a page built ahead (§8), the takeover keeps each adopted label's built text while the active language's labels still load (`polyglot.fetch`): a missing label no longer writes its key, or an empty string, over the built text. The text updates when the labels arrive. A key that the loaded labels do not have stays a key, as in the build. A failed load keeps the built text. A client-rendered page is unchanged: it shows the key until the labels load (utils 3.14.850 / element 3.14.815 / polyglot 3.14.611 / smbls 3.14.853).

Any text reader can use the same channel, from `@symbo.ls/utils`:

```js
import { evaluateText, markTextNotReady } from '@symbo.ls/utils'
evaluateText(() => 'Log in')                                   // { value: 'Log in', ready: true }
evaluateText(() => { markTextNotReady(); return 'ui.nav.login' }) // { value: 'ui.nav.login', ready: false }
```

A reader calls `markTextNotReady()` while its value is a stand-in for data on the way. The text writer keeps the adopted node's built text for a value that is not ready, and writes again when the data arrives. A call outside `evaluateText` does nothing.

### CMS upsert

```js
el.call('upsertTranslation', 'ui.nav.home', 'en', 'Home')   // optimistic + persists
```

### Anti-patterns

- Don't mirror `lang` into a separate state field. `state.root.lang` is the source of truth — polyglot reads/writes it directly.
- Don't rebuild your own language switcher; `setLang` already handles localStorage + remote refetch + fonts + state, switching text, `state.root.lang` and `<html lang>` together. For a busy indicator read `el.call('getPendingLang')`, not a state flag of your own.
- Don't read UI text from root state (`s.root.hello`), and never name a state flag after a text key. At boot polyglot copies each translation key that NOTHING in state declares into `state.root`; a language switch re-translates only those seeded keys, and only while each still holds the text polyglot wrote. A key the app has set since, and a key that was never seeded (a module's text keys join after boot), is left alone — a switch never fills an empty key by name. Read text through `'{{ key | polyglot }}'`, a bare `'{{ key }}'` (it falls back to the active translation map) or `el.call('polyglot', 'key')`, and declare every flag in `state.js`: an undeclared flag that shares a text key's name boots holding that text.
- Don't put the language switch UI's `show:` logic on JS — flag the UI with `data-lang="ka"` and use CSS `[data-lang="ka"] &` selectors in design tokens if you want pure-CSS reactivity.

---

## 7. `@symbo.ls/helmet` — SEO metadata

Full reference: `plugins/helmet/README.md`. Auto-registered always (no config required). Reads `metadata: {...}` from app and pages, writes `<title>` / `<meta>` / `<link>` tags. Brender uses the same metadata for SSR `<head>`.

### App-level defaults + page overrides

```js
// app.js
metadata: {
  title: 'My App',
  description: 'Built with Symbols',
  'og:image': '/social.png',
  'og:type': 'website',
  'twitter:card': 'summary_large_image'
}

// pages/about.js
export const about = {
  metadata: { title: 'About', description: 'Learn more' }
}
```

### Dynamic metadata (function form)

```js
export const product = {
  metadata: (el, s) => ({
    title: s.product.name,
    description: s.product.description,
    'og:image': s.product.image
  })
}

// per-key functions also work
metadata: {
  title: (el, s) => `${s.user.name} — My App`,
  'og:image': '/default-avatar.png'
}
```

To REPLACE an element's metadata at runtime, pass a factory or `null`: `el.update({ metadata: (el, s) => ({ title: 'Checkout', robots: 'noindex' }) })`, `el.update({ metadata: null })`. An object patch (`el.update({ metadata: { title: 'Checkout' } })`) changes nothing — `update()` does not assign an object to a lowercase prop.

### A route entry's head

Since smbls 3.14.860 (@symbo.ls/utils 3.14.854, router 3.14.615, helmet 3.14.673, mermaid 3.14.848). A route entry names its page's component and may carry that route's own head — several routes, one page component, a head each:

```js
// pages/index.js
export default {
  '/ask': 'AiPage',
  '/blueprint': { extends: 'AiPage', metadata: { title: '{{ ai.blueprint.title | polyglot }}', robots: 'noindex' } },
  '/make': { extends: 'AiPage', metadata: { title: '{{ ai.make.title | polyglot }}' } }
}
```

- A string entry's head is its component's static `metadata`. An object entry's head is its own `metadata` (or `helmet`) over the component's: the entry's keys win, the component's other keys stay. A whole-function `metadata` replaces the component's (a server head cannot read it); per-key functions work as usual.
- The component is found as `extends` resolves: the project's components, then the linked libraries, along its string `extends` chain (at most 8 components; a cycle ends).
- The served head (mermaid, `@symbo.ls/utils` `getPageMetadata`), the SSR head (`extractMetadata`) and the browser read it by this one rule (`routeEntryMetadata`), so the served `<title>` and robots are the route's own. Before, a string entry served the app's head, and an object entry lost its component's keys.
- Two entries that name the same component and carry nothing but a head (`extends` with `metadata` / `helmet`, or a string) are the SAME page for `keepSamePage` (SYNTAX.md → Router → Keep the page): the page stays mounted (a canvas keeps its state) and the head changes to the new entry's, what a fresh visit to that address shows. An entry with any other key is a page of its own.

### Runtime — the head is the merge of mounted layers

Every element with `metadata` adds a LAYER to the document head: opened when the element is created, kept current by a signal effect (a language switch re-resolves it), closed when the element is disposed (the router swaps the page, a list row leaves, `destroy(app)`).

1. Each layer resolves its metadata: function values run, `{{ }}` templates resolve, files-map keys become file URLs.
2. Order: an element sits above its ancestors (the app is the lowest layer); of two unrelated elements the later-mounted sits above.
3. Each key takes the value of the highest layer that sets it (`null` / `undefined` sets nothing).
4. A key no layer sets any more (its element left, or its metadata dropped the key) falls back to the next layer that sets it (e.g. the app's value); else to the value the served document had before helmet first wrote that tag — only while the document still shows the path it was served for, and only if no layer wrote that same value; else the tag is removed.
5. `title` / `description` cascade into `og:title` / `og:description` (unless a non-empty one comes from the title's layer or a layer above it) and `twitter:title` / `twitter:description` (unless any layer sets one) — as the server head does.

Helmet never touches a tag no layer set. Put route-independent defaults in the app's `metadata`; a page sets only what it changes — no need to restate every key to clear the previous page's tags.

Array keys:

| Key | Tags | When the layer that set it leaves |
|---|---|---|
| `jsonLd` | `<script type="application/ld+json" data-smbls-jsonld>` | removed, or the next layer's list |
| `styles` | `<style data-smbls-style>` | removed, or the next layer's list |
| `alternate` | `<link rel="alternate" data-smbls-alternate>` | removed, or the next layer's list |
| `favicons` | `<link rel="icon" data-smbls-favicon>` | removed, or the next layer's list |
| `icon` / `favicon` | `<link rel="icon" data-smbls-single-icon>` | removed, or the next layer's icon |
| `scripts` | `<script src data-smbls-script>` | stays — load-once: added once, never removed |

The highest layer's list replaces the lists below it. The served head (brender, and the static head of the mermaid server and the runner) writes `alternate`, `favicons` and `icon` with the same `data-smbls-*` keys, so a client that boots on a server-rendered page takes those tags over instead of adding a second copy.

#### Labels still loading, and a head the build wrote

Since smbls 3.14.859. The live head keeps what the document shows until a real value is there:

- A value that is a label's stand-in (a `polyglot` key whose language is still loading; `translate` marks it through `@symbo.ls/utils` `evaluateText`) is never written. The tag keeps the served value, or the last real one, and the label is written when it lands. So a title never flips to a raw `ui.meta.*` key.
- On a page the build wrote (`<meta name="brender">` / `<meta name="brender-stamp">` in the served head), on the path it was served for, the app root's metadata does not replace a tag the document carries. The page's own metadata is written as soon as it is ready. A navigation, or a change of the app's values (a language switch), ends this.
- A head the HOST wrote (an edge Worker that writes each route's own title and description into an app shell) is kept the same way when it carries `<meta name="smbls-head" content="served">` (since helmet 3.14.673; opt-in). Without the marker the app's defaults fill every tag the page does not set.

So the app's defaults name labels (`title: '{{ ui.meta.site_name | polyglot }}'`), and the static text that shows before the labels load is written once, in `index.html`. `app.js` need not repeat the `index.html` literals (FRANKABILITY_CATALOG.md → FA701 → Head metadata defaults).

#### The first head write, and a noindex the host forced

Since helmet 3.14.673:

- An app that routes renders its head once its first page is in: the app's metadata and the first route's page metadata, merged in ONE write (at the first `routeChanged`, or when the first navigation settles without one). The served title changes at most once at boot, to the first page's; the app's title alone is never written first. An app without routes (or with `router: false`) writes at once.
- A Symbols-managed host (`*.symbo.ls`, every slot; a custom domain is the indexed one) serves the forced `<meta name="robots" content="noindex" data-smbls-host="forced">` (`generateMetaTags`, @symbo.ls/utils 3.14.854). Into a marked tag helmet writes only a robots value that keeps the page out of the index (it contains `noindex` or `none`, e.g. `noindex, nofollow`) and never removes it, so a project's `robots: 'index, follow'` does not reach a development or staging copy. A custom domain's head has no mark: the project's `robots` applies. `applyMetadata` keeps the same rule.

### Supported keys

Two surfaces with **different supported-key sets**.

**Runtime (browser)** — the `META_TAGS` table in `plugins/helmet/index.js`, plus the array keys above. Unknown keys are silently skipped:

```
title, description, keywords, robots, author, canonical,
image, url, siteName, type, locale, theme-color,
og:title, og:description, og:image, og:url, og:type, og:site_name, og:locale,
twitter:card, twitter:title, twitter:description, twitter:image, twitter:site,
jsonLd, styles, scripts, alternate, favicons, icon / favicon
```

**SSR / brender HTML** — `generateHeadHtml()`. Broader prefix-rule set:

- All runtime keys above PLUS:
- `viewport` (auto-emits a default if not set)
- `og:*`, `article:*`, `product:*`, `fb:*`, `profile:*`, `book:*`,
  `business:*`, `music:*`, `video:*` → `<meta property="X">`
- `twitter:*`, `DC:*`, `DCTERMS:*` → `<meta name="X">`
- `http-equiv:X` → `<meta http-equiv="X">`
- `itemprop:X` → `<meta itemprop="X">`
- Any other string-valued key → `<meta name="X">` fallback

If you set e.g. `article:author` and rely on it client-side, the
runtime won't emit it (it's not in META_TAGS). It WILL appear in the
SSR HTML brender produces.

**`source` is a declaration, never a tag.** A `:param` page may declare where its record lives — `metadata: { source: { collection, type, param, lang }, … }` — for a renderer that reads the record and resolves the address's head from it, then hands that head to `renderProjectHtml` as `metadata` (§8). No surface prints `source`: the server head (`generateMetaTags`) skips it, helmet's SSR head skips object values, and the browser runtime applies only the keys above.

### SSR priority order (brender)

`extractMetadata(data, route)` in `plugins/helmet/index.js`:

1. `data.integrations.seo` — lowest priority (defaults)
2. `data.app.metadata` — medium
3. the route entry's head — highest: an object entry's `metadata` (or `helmet`) over its component's static `metadata`; a string entry, the component's (A route entry's head, above)
4. Falls back to `page.state.title` / `page.state.description`
5. Final default: `data.name || 'Symbols'` for `title`
6. Cascades `title` / `description` into `og:title` / `og:description` (unless the page sets them) and `twitter:title` / `twitter:description` (unless set anywhere)
7. `og:url` is route-aware only as a BASE: an `og:url` (or `url`) from `integrations.seo` or the app gets the route appended (`baseUrl + route`); a page's own `og:url` (or `url`) is that page's address and stays as written. The runtime never appends a route.
8. Files-map keys become file URLs (own keys and bare names; `src` → `content.src` → `content.storageUrl`)

### Anti-patterns

- Don't write to `document.title` or insert `<meta>` tags from project code. Helmet owns them; manual writes drift on route change.
- Don't manually duplicate `title` into `og:title` / `twitter:title` — the cascade does it, at runtime and on the server. Set them only when you need a *different* social-only string.
- Don't fill every key on every page to clear what the previous page set — an omitted key falls back to the app's layer or the served value.
- Don't `el.update({ metadata: { … } })` with an object — pass a factory or `null`.

---

## 8. `@symbo.ls/brender` — SSR + hydration

Full reference: `plugins/brender/README.md`. Renders DOMQL trees to HTML on the server; in the browser the app either ADOPTS that HTML (each element takes the server's node at its path) or replaces it with a fresh render.

### When brender runs

- **`smbls brender`** CLI — pre-renders every static route to `dist-brender/`, route `/x` → `x/index.html`. Its pages carry no registry: with its client bundle (ISR, on by default) the app boots over the markup and replaces it.
- **`smbls build`** — pre-renders into the build output, route `/x` → `x.html`. Both write `/*` to `404.html`; `:param` routes and nested `*` routes have no single URL, so they are skipped and listed unless `brender.paths` lists addresses for them. Both run one route loop: the `symbols.json` `brender` settings (`context`, `exclude`, `paths`, `strict`, `eagerImages`, `timeout`, `stamp`), `file:` URLs mapped into the output, and the same diagnostics — `--strict` fails on a page made without its data or labels. Both exit 1 when no route renders (opt out with `--no-brender`). Every built page is made for adoption (hydration, below) unless `symbols.json` says `"brender": { "hydrate": false }`. `smbls build` also writes the prepared design system (below), `200.html` for routes without their own page and the `_redirects` rules that serve it (CLI.md → Dev / build / deploy → Routes without their own page). `smbls build` also takes `brender.lazyGroups` (a lazy route built as its group's real page, SYNTAX.md → Router → Lazy routes) and the opt-in built-page options `module`, `onProblem`, `report`, `paint`, `faces`, `app`, `pageScript`, `preloadImage`, `beforePaint` (since cli 3.14.832), `beforeWrite`, and `paths` as a function (since cli 3.14.826 / brender 3.14.676; CLI.md → Dev / build / deploy → Built-page options).
- **`smbls publish --ssr`** (or `"prerender": true`) — pre-renders the static routes at publish time and stores them on the platform, one row per route outside the project content, served by the platform renderer; each route keeps its own icons after its content (CLI.md → Publish flow). A project whose `config.js` declares `agentView` (since cli 3.14.832) also gets each stored route rendered at its agent view's query and stored under `<route>?view=agent` — what the platform renderer serves AI crawlers, which read only the served HTML — from size budgets of its own (CLI.md → Publish flow → Agent view).
- **mermaid** runtime — calls `renderRoute(...)` per request when `channel === 'production'` or `'staging'`. Falls back to client-side render if brender throws or `BRENDER=false` env var is set. `renderProjectHtml({ adoptDom, ssrWithoutEval, evalAvailable })`: without `eval` (Cloudflare Workers) there is no live server render, so the platform serves the client render or a stored `__ssr` pre-render. `renderProjectHtml(data, { metadata })` takes a head the CALLER resolved for this address (for example from a CMS record it read): with keys it is the page's head, over a server render's and the page's own; an empty object, an array, `null` or a string keeps the usual head. It reaches the `<head>` tags only — the boot payload, and so the client, never carries it. (Head keys and `metadata.source`: §7.) `renderProjectHtml(data, { search })` (since mermaid 3.14.850) makes a live render at that query — an explicit view of the page, such as its agent view; never pass the visitor's own query. `@symbo.ls/mermaid/render` exports `renderVariants(data)`: the views a publish renders beside each page, `[{ name: 'agent', search: '?view=agent' }]` from config.js `agentView`, else `[]` (it reads config where the render reads `polyglot`: `data.config` or `data.settings` when the payload keeps config nested, else the payload's top level, where a served payload has it). The served page names its language on `<html lang>` (mermaid 3.14.848, client and server render alike): the language a server render rendered in, else the page's start language (the address's when the project uses one, else `defaultLang`), escaped; no attribute without polyglot; a project `index.html` that sets `lang` on `<html>` keeps its own.

### The page and the client boot

A pre-rendered page carries NO inline script, so a strict Content-Security-Policy (`script-src 'self'`, no `'unsafe-inline'`) cannot break it — a policy blocks inline scripts, never `<meta>` tags or JSON data blocks:

| Part | Where | Meaning |
|------|-------|---------|
| `<meta name="brender" content="hydrate\|replace">` | `<head>` | the page is pre-rendered |
| `data-br="br-N"` | each server element node | its key |
| `<script type="application/json" data-brender="registry">` | after the markup | element path → key; only on a page made for adoption |
| `<script type="application/json" data-brender="registry-tree">` | after the markup | the same registry as a tree, `{ "f": "tree", "e": [...] }` — what `smbls build` writes when the page's smbls reads it (brender 3.14.672; `brender.registryFormat: 'paths'` keeps the old tag) |
| `<style data-smbls-faces>` | `<head>`, before `<style data-brender>` | the page's `@font-face` rules (brender 3.14.672); the takeover keeps it, so faces stay loaded. Two marks (brender 3.14.678): `data-smbls-faces-version` — a content hash of its rules, the same for the same rules — and `data-smbls-faces-files` — each rule's file address (its first `src` `url()`), in rule order, `-` for none (CLI.md → Font faces in their own sheet) |
| `<script type="application/json" data-fetch-seed>` | after the markup | the anonymous GET answers the render got (`@symbo.ls/fetch`) |
| `<meta name="brender-stamp" content="<stamp>" data-time="<ms>">` | `<head>` | the build the page comes from (`brender.stamp`, else the render time) — `el.context.prerender` |
| `<link rel="preload" as="fetch" data-smbls="design-system">` | `<head>` | `smbls build` only: the design system the build prepared (below) |
| `<meta name="smbls-design-system" content="…" data-smbls="design-system">` | `<head>` | `smbls build`, client-rendered pages only (`200.html`, a no-pre-render `index.html`): names the prepared design system without preloading it (below) |
| `<meta name="brender-lazy" content="<groups>">` | `<head>` | the `context.lazy` groups whose page the page shows (since smbls 3.14.859 / brender 3.14.676): the boot reads it into `context.lazyFirstView`, so the first navigation loads them and the takeover adopts the built page; `smbls build` adds one `<link rel="modulepreload">` per group chunk |
| `<link rel="expect" href="#smbls-whole" blocking="render">` + `<template id="smbls-whole">` | after the charset declaration / after the markup | `brender.paint: { whole: true }`: the first paint waits until the markup is in (cli 3.14.826) |
| `<script type="application/json" data-smbls-paint>` + `smbls-built.<hash>.js` (or the same script inline) | `<head>`, after the faces sheet | the settings and the small script of `brender.faces` / `brender.app` (`brender.pageScript`; cli 3.14.826). Since cli 3.14.827 it also sets `window.__smblsFacesReady` (a promise of the page's loaded faces; it never rejects) and takes a failed AVIF `<source>` out of its `<picture>` once (CLI.md → Built-page options). Since cli 3.14.828 / brender 3.14.679: each page's script holds only the parts that page uses (one file, or one CSP hash, per set of parts), and the promise only when something names it; `faces.inline: true` and the promise take only the faces the page's elements draw (`@symbo.ls/brender` `drawnFaces`). Since cli 3.14.831: a page held by `faces.wait` also has `window.__smblsPaintReady` (a promise of the hold's end, resolved in the task that shows the page, so a title fit that waits on it runs before the first visible frame; it never rejects) and `<html data-smbls-paint-wait>` from its first byte until that task; `smbls csp` lists the inline scripts' hashes with no build |
| `<script data-smbls-before-paint src="/smbls-built.<hash>.js">` (or the same script inline) | right after the markup | `brender.beforePaint` (since cli 3.14.832): the project's script that must run before the first paint (a title fit). The file blocks the parser there, so it runs at that point; on a page held by `faces.wait` the hold ends only after it has run and the faces are in (or at the cap). The build's one line on its first line meets the page's script in `window.__smblsBeforePaint` (CLI.md → Built-page options) |
| `<link rel="preload" as="image" fetchpriority="high">` | `<head>`, after `<meta name="viewport">` (else after the charset declaration) | `brender.preloadImage: true` (since cli 3.14.831): the first view's image — the first `<img fetchpriority="high">`, else the first eager image that is not `fetchpriority="low"`; from a `<picture>`, its first `<source>` with a `srcset` (CLI.md → Built-page options) |
| `<template data-smbls-app>` | before `</body>` | `brender.app: 'afterFirstView'`: the app's scripts and preloads wait here until the first view is in, the first input, or `wait` ms (cli 3.14.826); with `app.after` (cli 3.14.827) also until the faces (`'faces'`) or the project's named `window` promises settle |

**Hydration (adoption).** On by default when the page carries the registry; `hydrate: false` in the project config refuses it (fresh render). The client runs its normal `create()`, but each element takes the server's node at its path: attributes and text are written again by the client, so the result is the client's own render without a second paint. A node of another tag is not adopted (that element gets a fresh one); a throw falls back to the fresh render, in one task (the adoption has taken back the server nodes it had claimed). The adoption stays open until the first view has settled — the first route rendered (also behind a guard that waits) and no `@symbo.ls/fetch` request in flight — so the routed page and every list that renders with its first data adopt their server nodes; until then the server nodes still waiting stay on screen, in place. It closes at the latest after 3 s (`hydrate: { timeout: ms }`), or at the visitor's first click or key press, counted from the end of the adoption; whatever no element adopted then goes. The adoption itself runs in short tasks, and a click during it is held and dispatched again once (§4). An adopted image that had already loaded fires its `load` again, once, so `onLoad` runs. The build's `aria-*` / `data-*` attributes stay on an adopted node until its element writes that attribute (set or removal, by the framework or project code) or the adoption window closes; then the ones no element wrote go (element 3.14.810). So `aria-busy` and the styles that reserve a part's height hold between adoption chunks. `class`, `style`, `id` and other attributes are written again at adoption, as before. On `<img>` and a `<picture>`'s `<source>`, the attributes that choose the image and its fetch (`src`, `srcset`, `sizes`, `loading`, `fetchpriority`, `decoding`, `crossorigin`, `referrerpolicy`, `width`, `height`, `media`, `type`) are never removed: the element writes its own values over them, so a built photo loads once (element 3.14.811). An app that declares `content: {}` keeps the built page on screen: while the window is open, the router's first `set()` hands the old content's node back and the new content adopts it in place (element 3.14.814; before, the page was off screen for a frame). An adopted label keeps its built text until polyglot's labels for the active language load (`polyglot.fetch`), then the real label is written (smbls 3.14.853, §6 → Labels on an adopted page). `window.__BRENDER_HYDRATION__` reports `{ adopted, misses, removed }`. The smbls embed never adopts (RUNNING_APPS.md → Embed Bundle).

**Replace.** A page without the registry (`"brender": { "hydrate": false }`, `renderPage` without `adoptDom`, a platform pre-render): the server's markup and styles go and the app renders fresh. The app builds in short tasks while the server's page stays on screen, and the server's markup and styles go in the task that inserts it (§4 → the first render); `window.__BRENDER_HYDRATION__` is `{ replaced: true }` from that task on. A body-level `<svg id>` (the icon sprite) stays, and the client adds every icon to it. The recorded data answers are still adopted by the requests that ask for them.

**The visitor's input survives the replace** (since smbls 3.14.861). The server's page takes input while the app builds. Just before the server's nodes go, the replace reads every field the visitor changed (a value typed, an option picked, a box ticked, a radio picked), the focused field with its selection, and the scroll position of every scroller they moved and of the viewport (`document.scrollingElement`). In the task that inserts the app it puts them on the app's matching nodes — matched by the `data-key` chain, the tag and the rank among equal chains (the app's own root key may differ from the server's) — and focuses with `preventScroll`. Once the first view is in, each restored field fires `input`, and `change` where the visitor had committed it (a pick, a tick, a text field they had left; the field they are still typing in gets `input` only), so the app's own handlers write its state. A focus or a scroll those handlers make in reply (a pick that opens its section with a smooth `scrollIntoView`) goes back to where the visitor is before a frame shows it. A field at its server default, an element at scroll 0 and a page with nothing focused cost nothing and fire nothing; an untouched field keeps the app's own default; a field the app renders `disabled` is left alone. The one-task replace (`firstRender: false`) does the same. What the app owes it: the field's `data-key` chain is the same on the server's page and in the app (keyed children give that), and its handlers treat these events as a visitor's. The code that does this loads only for a replace (since smbls 3.14.867): a code-splitting build (`smbls/core`) keeps it in a file of its own, which a page that adopts never requests; a page built to be replaced starts its load at the boot's first step.

**The data the server used.** The page's `data-fetch-seed` answers are taken by the client call that sends exactly the recorded request (URL with its query, `Accept-Language`, no other header): no second request, and the data lands in the task the app booted in. A create-time `fetch:` (a cached `select` / `rpc` read that runs on create, not infinite) takes its recorded answer when its element is created, before its children are built (fetch 3.14.670): the adopted element starts from the page's data, with no loading status, no `aria-busy` and no empty state between chunks, and `onFetchComplete` runs once. Only anonymous GETs are recorded — a keyed backend's reads count when `fetch.reads` moves the key into the query (`reads: { query: { apikey: 'apikey' }, rpc: 'get' }`, read-only RPCs as GETs with `read: true`). Code that reads the seed block itself (`script[type="application/json"][data-fetch-seed]`): since brender 3.14.675 the list ends with one more item, `{"r":{…}}` (which of its queries each element ran in the render), after the query items (`{"k":…,"b":…}`). Skip an item you do not know (one without `k`), as `@symbo.ls/fetch` does.

Pages from older servers still work: the inline `window.__BRENDER__` flag, `window.__BR_REGISTRY__` and `window.__BRENDER_HYDRATE__` are read (that registry adopts only with `hydrate: true` or the flag); when a policy blocked such a page's flag, its `data-br` markup in the mount node is taken for the mark — one app root, never two. An smbls older than this format does not know the `<meta>`: keep `smbls` and `@symbo.ls/brender` at the same release.

**The data is the build's.** A `smbls build` page shows the answers of the build time until the next build. A page flagged stale gets them at once and then, after the adoption, asks again (§5 → `fetch.seed`); on an adopted page `window.__BRENDER_HYDRATION__.refreshed` reports that refresh (`{ queries, reads, changed }`).

**When the first view is in — `afterFirstView`** (since smbls 3.14.859). The create option `afterFirstView: (app, state, context) => {}` (config.js, context.js or `create(App, { afterFirstView })`) runs once per app, a task after the first view is in: after `create()` rendered it or adopted the pre-rendered page, after the first navigation settled — the moment `fetch.early`'s `afterFirstView` hook runs. Use it for work that must wait for the takeover (a page view, a beacon, revealing a below-the-fold part); never poll `window.__BRENDER_HYDRATION__` or loop on `requestAnimationFrame` for it. A hook that throws or rejects is reported, never rethrown. brender never runs it in a server render.

**In app code:** `el.context.prerendered` is `true` in an app that booted over a pre-rendered page, and `el.context.prerender` is the build the page comes from, `{ stamp, time }` (the `brender-stamp` meta; `undefined` on a page without one). A gate that hides the app until its data is in (`opacity: 0` until labels, settings and fonts load) also hides the adopted page until then — let a pre-rendered first view count as ready: `isReady: (el, s) => el.context.prerendered || …`.

**In the server render:** `el.context.ssr` is `true` while brender renders the page — in every render: `smbls build`, `smbls brender`, a publish's pre-render, a live server render (since brender 3.14.676). No payload key and no `context` override turns it off. A browser has no `ssr` key, so compare strictly: `el.context.ssr === true`. The server document lays nothing out and observes nothing: no `getComputedStyle`, no `ResizeObserver` or `IntersectionObserver` (`onInView` never fires), no scroll. What the render ends with is stored in the page, and the visitor sees it until the client takes over — seconds on a slow phone. So code that measures, observes or plays an entrance renders the FINAL state there. An entrance that starts at `opacity: 0` and waits for the view stores a blank block. Start in the final state on the server (`data: { rise: (el) => el.context.ssr === true ? 'in' : 'wait' }`, SYNTAX.md → View events), and return early from a function that measures: `if (this.context.ssr === true) return`. A timer callback of the server window (`el.context.window.setTimeout`, `setInterval`, `requestAnimationFrame`) that throws is reported once per message, as a browser reports it, and the render goes on; it no longer ends the process that renders (since brender 3.14.678). A bare `setTimeout` or a promise the code never handles still reaches the process: `smbls publish` reports it during its pre-render, other hosts keep their own policy.

| Key | Set in | Meaning |
|---|---|---|
| `el.context.ssr` | the server render | `true`: this code runs inside brender |
| `el.context.prerendered` | the browser | `true`: this app booted over a pre-rendered page (adopted or replaced) |
| `el.context.prerender` | the browser | `{ stamp, time }`: the build that page comes from |
| `el.getAdoption()` | the browser, per element | `'adopted'`, `'replaced'` or `null` (below) |

**Per element — `el.getAdoption()`** (since smbls 3.14.862 / element 3.14.819). `el.context.prerendered` answers for the whole page, also for the parts the build never had. `el.getAdoption()` answers for one element: `'adopted'` when its node is the built page's (a hydration boot); `'replaced'` when a replace boot built it in the first view over the built page and the built page had its counterpart (the same `data-key` chain, tag and rank); `null` for everything else — a fresh client render, a part the built page did not have, and every element made after the boot's first view (a navigation, a list's next data, an `if` that opens later). It is known from the element's first hook: `onInit` and a create-time `fetch:` `transform` run before the node is made and read the answer the node will get (since smbls 3.14.867; before, they read `null`), `onRender` and `onInView` read the one it got (in a replace, before the swap). It stays for the element's life. A replace answers `'replaced'`, never `'adopted'`: a gate that waits for data reads a fresh build, and an entrance can skip a part the visitor saw already:

```js
onInView: (el) => { if (!el.getAdoption()) el.call('rise') }
```

On a client boot over a pre-rendered page (`el.context.prerendered`), the server's first view is already on screen: an entrance that hides it again makes it blink.

**The design system prepared at build time.** Every server render of `smbls build` also prepares the app's design system (the processed config and the global CSS). The build writes it once as `smbls-ds.<sha>.json` next to the bundles and puts `<link rel="preload" as="fetch" data-smbls="design-system">` into every page it pre-renders (their boot waits for it). The app's first document requests the file before its first yield and ADOPTS it (the config revived, the global rules replayed) instead of processing the design system again. `context.designSystemSource` says which ran: `'prepared'` or `'processed'`. It adopts only a file prepared from the same input — a fingerprint of the design system without its `font` family, and of the options that shape processing, with the theme the page boots in. **A page the client renders** (the app shell `200.html`, the `index.html` of a build without a pre-render) gets no preload, only a reference: `<meta name="smbls-design-system" content="smbls-ds.<sha>.json" data-smbls="design-system">` (smbls 3.14.845). The boot requests the file at low priority when it runs (after the app script is in) and never waits for the download: the app adopts the file when its answer is in by the time the design system is prepared, else processes the design system itself. Both give the same CSS, so nothing repaints; a later visit finds the file in the HTTP cache. `symbols.json` `build.prepareDesignSystem: false` (= `{ shell: false }`) leaves the reference out of the client-rendered pages (pre-rendered pages keep their preload). `build.prepareDesignSystem: { pages: false }` (opt-in, cli 3.14.814) leaves the preload out of the pre-rendered pages too; their client processes the design system itself. The page processes as before when:

- there is no file — `smbls start`, an older build, a fetch that fails or a CSP that blocks it;
- the fingerprint differs — a shared library fetched over the network that changed since the build, a theme the visitor stored, `?globalTheme=`;
- the design system holds something data cannot carry — a function, a class instance, a host object: the build prepares nothing (DESIGN_SYSTEM.md → Prepared at build time);
- the project reads a local design-system file, or the app is not the first app of its document (a second app, an iframe tile).

The `font` family is never prepared: its file URLs are the build machine's, so the page resolves fonts and font faces itself. A host that writes the page itself can hand the prepared design system in as `context.preparedDesignSystem`, or inline it as a data block (`designSystemBlock(prepared)` from `@symbo.ls/utils`, selector `script[type="application/json"][data-smbls="design-system"]`; the link's selector is `link[rel="preload"][data-smbls="design-system"]`, the client-rendered page's reference `meta[name="smbls-design-system"][data-smbls="design-system"]`, `DESIGN_SYSTEM_DEFERRED` in `@symbo.ls/utils`).

Programmatic use:

```js
import { renderPage, renderRoute, composeIntoShell, prerenderParts } from '@symbo.ls/brender'   // needs smbls installed (peer)
const { html, route, brKeyCount, shell } = await renderPage(data, '/about', { shell: builtIndexHtml, depth: 1, adoptDom: true })
// shell: a built app document to render INTO (the result then has shell: true); depth: the output file's
// directory depth, used to rebase the shell's relative asset URLs; adoptDom: ship the registry (adoption);
// nonce: the CSP nonce for the inline scripts an `isr` document still has
import { createDomqlElement, prepareContext } from 'smbls/ssr'   // the same module instance as 'smbls'
```

- `render()`, `renderRoute()` and `renderPage()` take `search` (since brender 3.14.680): the query of the address the page is rendered at (`'?view=agent'`). The render's `location.search` and `location.href` carry it, so a page that reads its query at init renders that view; the head stays the page's own. `''`, `'?'`, `null` or none render as before, byte for byte, and the next render never inherits a query. A value that is not a string, or that holds a `#`, throws a TypeError that names the option. The views a project declares: `import { agentViewOf, renderVariantsOf } from '@symbo.ls/utils/server'` (since utils 3.14.859) — `agentViewOf(data)` is `{ param, on, off }` from config.js `agentView` (`true` or `{}`: `view` / `agent` / `human`) or `null`, and throws a TypeError naming the shape for a declaration outside the platform renderer's rules; `renderVariantsOf(data)` is `[{ name, search }]`.
- `renderRoute(data, { route, prefetch })` returns `html`, `globalCSS` (`rootRule`, `resetRules`, `keyframeRules`), `css` / `classRules` (class rules only), `fetchSeed` (the server's fetch answers) and the registries. The page's `fetch` runs during the render either way; `prefetch: false` fetches no table/RPC labels first and waits only a 50 ms quiet period for the page's requests (default: up to 2 s).
- `prerenderParts({ brRegistry, fetchSeed, adoptDom })` returns `{ meta, blocks }`: the page's `<meta name="brender">` and its data blocks. `adoptionScripts` (inline scripts) remains for older callers — a page under a strict policy needs `prerenderParts`.
- Server style tags carry `data-brender` (global CSS) or `data-emotion="smbls"` (class rules). The client boot removes only `style[data-emotion="smbls"]` and `style[data-brender]`: a host page's own styles stay. `renderPage` writes the page's `@font-face` rules in `<style data-smbls-faces>` ahead of them (brender 3.14.672); the boot keeps that sheet. smbls `applyFontFaces` does not insert a face that names no file (smbls 3.14.850).
- Registry writers are server-only (utils 3.14.849): `import { brenderRegistryBlock, encodeBrenderRegistry, brenderRegistryTreeBlock } from '@symbo.ls/utils/server'` (ESM and CJS). They are not in the `@symbo.ls/utils` index, `smbls` does not export them, and `el.call('brenderRegistryBlock', …)` / `context.utils` no longer reach them. The client half stays in the index: `BRENDER_REGISTRY_BLOCK`, `BRENDER_REGISTRY_TREE_BLOCK`, `decodeBrenderRegistry`, `readJsonDataBlock`, `jsonForScript`.
- The same entry has `revivePolyglotDefaultLang(polyglot, { evaluate })` for a server that reads a project as frank JSON, where a `defaultLang` function is its source text. It returns the config with that text revived (as the browser revives it), or the same object when there is nothing to revive, when `evaluate: false`, or where nothing compiles from text (a Worker). brender's render and mermaid's page call it; the runner revives with the index's `deepDestringifyFunctions`. The index helpers (`polyglotDefaultLang`, `polyglotFallbackLang`, `polyglotStartupScript`) compile no text: they ride in every browser bundle, so unrevived text counts as no language there.

**Page weight** (brender 3.14.671). A page built ahead carries only what it paints before boot; the client adds the rest of the sprite, the atomic rules and the variables when it boots. `renderPage` options (each default `'all'` / `'paths'` when called directly): `spriteIcons: 'page'` (only the page's icons in the sprite), `cssClasses: 'page'` (only rules of classes in the markup), `cssVariables: 'page'` (only the variables the page reads), `registryFormat: 'tree' | 'auto' | 'paths'`. `smbls build` turns on `spriteIcons: 'page'`, `cssClasses: 'page'` and `registryFormat: 'auto'` by default (`symbols.json` `brender.spriteIcons: 'all'`, `brender.cssClasses: 'all'`, `brender.registryFormat: 'paths'` switch each off). `brender.cssVariables: 'page'` is opt-in: a stylesheet the page links (public CSS, a CDN) is not seen, so do not use it when such a stylesheet reads design-system variables before boot. Text between the sprite's symbols (an icon whose value is not an `<svg>` leaves it there, for example a stray `<>`) and comments never stop the sprite trim; an element other than a symbol in the sprite still leaves the sprite whole (since brender 3.14.676; an older brender leaves the whole sprite on such text too). The four trims are exported from `@symbo.ls/brender` (since brender 3.14.676) for a tool that weighs a page of its own: `trimSpriteToPage(html, context?)` → `{ html, kept, dropped }`, `markupClasses(...texts)` → a `Set` of class names, `classRulesForPage(rules, classes)` → the rules, `trimVariablesToPage(rootCss, ...readers)` → `{ css, kept, dropped }` (the publish pre-render uses them). With them, `stylesheetRules(css)` (since brender 3.14.676) reads a stylesheet text back into its rules, the array `classRulesForPage` takes, whatever the layout (one rule per line, as a stored pre-render keeps them, or several per line); it returns `null` for a text it cannot read whole, so keep that text as it is. Never pass a string to `classRulesForPage`: it reads it one character at a time.

`symbols.json` `brender`: `true` (the default for `smbls build`), `false` (no pre-render), or an object, which turns it on with settings (CLI.md → Dev / build / deploy):

```json
{ "brender": true, "brenderDistDir": "dist-brender" }
```

### Theme during SSR

Brender defaults to `globalTheme: 'auto'` and emits both:

- `[data-theme="<scheme>"]` selectors (forced themes, including custom)
- `@media (prefers-color-scheme: dark|light) :root:not([data-theme])` (OS preference fallback)

So themes work without JavaScript on the rendered HTML. `resolveAndApplyTheme` in the client bundle then writes the concrete `data-theme` attribute on first paint.

A project whose `globalTheme` is a fixed theme (`light`, `dark` or a named scheme) gets `<html data-theme="<theme>">` on every built page (brender 3.14.670; `renderRoute` returns it as `theme`). First paint then uses the project theme, not the OS scheme, and the boot keeps the attribute. `auto`, `system` or unset (or a config with its own `themeRoot`) write no attribute: the `prefers-color-scheme` fallback applies until boot.

### Hydration contract (`data-br`)

1. **Sequential** — `br-0`, `br-1`, … assigned in DOM tree order via depth-first traversal.
2. **Deterministic** — same DOMQL input always produces the same key assignment. The client still needs the page's registry (element path → key) to find each element's node: an element with no node in the DOM (a false `if`, a text node) has no key.
3. **Element nodes only** — no text/comment nodes get keys.
4. **Bidirectional** — after hydration, `element.node === domNode` and `domNode.ref === element`.

This means SSR HTML and client bundle must run **identical** DOMQL source. Any divergence (different shared libraries, stale extends chain, conditional branches that diverge) breaks hydration.

### What to avoid in code that may run during SSR

- `window` / `document` / `localStorage` access without `typeof window !== 'undefined'` guards. Brender stubs many browser APIs but not all.
- Async work in `onCreate`/`onRender` that mutates the DOM — SSR captures the synchronous output. Async mutations show up only after hydration. Declarative `fetch:` data is the exception: it loads during the render, through the fetch plugin, and the render waits for its requests (below).
- Imports of browser-only packages (e.g. `mapbox-gl`, `leaflet`) at the module top level. Lazy-load via `el.call('requireOnDemand', 'mapbox-gl')` inside an event handler.
- Random / time-of-day output without a deterministic seed. Two renders must produce the same HTML.
- Reading from outside the project context (e.g. global `import.meta`, `process.env` at module top level — these resolve at bundle time). The exception is `new URL('<relative path>', import.meta.url)` naming a project file: frank publishes the file and rewrites the call to its URL (§9 → Asset URLs).

Custom properties keep their name in a server render from brender 3.14.677: `el.node.style.setProperty('--coverBoxLeft', v)` (and `removeProperty` / `getPropertyValue`) writes `--coverBoxLeft` into the server HTML, as the browser does. brender 3.14.676 and older wrote it as `--cover-box-left` — another property (custom property names are case-sensitive) — so a `var(--coverBoxLeft, …)` read its fallback until the browser's own write, and the content moved when the page adopted. Other style names are unchanged.

### SSR data — the page's `fetch` runs during the render

A page's declarative `fetch` runs during the render, through the fetch plugin with the real element (`transform(data, el, state)`, `children` re-run on the answer), and the render waits for its requests (up to 2 s with `prefetch`, the default). It uses the project's own `config.fetch` (e.g. `{ adapter: 'rest', url, headers }`). The platform's `'sdk'` adapter cannot run on the server (`hasAdapter(name)` in `@symbo.ls/fetch` says whether an adapter is registered); its data loads in the browser. `renderPage(...).diagnostics` names failed requests and raw label keys. A render waits for the labels its own page is loading (polyglot `loadTranslations(lang, { inFlight: true })`), within the render's time limit; label loads are per app, so a page never gets the previous page's load.

Each render has a query cache of its own. Renders in one process — one after another or at once, of one project or of several — never share cached rows, requests in flight or invalidations, and `el.call('invalidateQueries' | 'removeQueries' | 'getQueryData' | 'setQueryData', …)` acts on the cache of the render that calls it. A server render binds no window-focus, reconnect or `refetchInterval` refetch: once its markup is taken, a page's queries leave no listener, no timer and no request behind, and its `data-fetch-seed` carries only the requests the page itself made.

`prefetchPageData(data, route)` (deprecated, like `injectPrefetchedState`) fetches a page's `fetch` data OUTSIDE a render; `render()` does not use it. It takes the configs that run on create: no `on`, `on: 'create'`, or a list that names `'create'` (or is empty), as the fetch plugin reads `on`.

### Diagnose a broken hydration

In the browser, `window.__BRENDER_HYDRATION__` after the boot: `misses` counts elements whose server node did not match (a fresh node instead), `removed` the server nodes no element adopted. Non-zero means the client rendered something else than the server.

brender's own `hydrate.js` (the `liquidate` example) logs unlinked elements:

```
Linked:   129 elements
Unlinked: 0 elements        ← any non-zero number = SSR/client divergence
```

Common causes: dynamic imports in different order, conditional branches that depend on `Date.now()` or `Math.random()`, plugins registered in one but not the other.

---

## 9. `@symbo.ls/frank` — JSON ↔ FS

Full reference: `plugins/frank/README.md`. Bidirectional bridge between a `symbols/` directory and a JSON object.

### `toJSON(projectDir, options?)` — FS → JSON

Bundles all project modules with esbuild, loads the result, returns a plain JSON-serializable object with functions stringified. This is what `smbls push` / `smbls publish` ship to the server, and what mermaid hydrates back into a runtime context.

```js
import { toJSON } from '@symbo.ls/frank'
const project = await toJSON('/path/to/symbols')
// { components, pages, designSystem, state, functions, methods, snippets, files, config, ..., workers }  (workers: publish data, since cli 3.14.826)
```

Options:
- `entry` — defaults to `context.js`; auto-generates one if missing
- `stringify: false` — keep functions as functions (only useful when bundling locally)
- `tmpDir` — custom temp dir for bundled output (default `.frank_tmp/`)
- `external` — additional packages to externalize
- `resolveAssetUrl` — `(asset) => url` or `'dataurl'`: the URL for a project file referenced as `new URL('<path>', import.meta.url)` (`smbls push` uploads the file; `smbls frank to-json` inlines a `data:` URL)
- `importMetaUrls` — `'load'` (default) or `'all'`; also `"frank": { "importMetaUrls": "all" }` in `symbols.json`

**Asset URLs — `new URL('<relative path>', import.meta.url)`.** frank bundles to CommonJS, where `import.meta` is empty, so such a call used to throw `Invalid URL` and fail the push. Now a call whose first argument is a relative path literal naming an existing file becomes `new URL("<url>")` with the URL `resolveAssetUrl` gives (push: the uploaded or reused platform asset). Scope `'load'` resolves only calls that run while the project loads (outside every function and `try`; the ones that used to crash); `'all'` also resolves calls inside function bodies, helpers frank lifts into globalScope, lazily imported modules and `app.js` — and with a resolver, a call it cannot resolve (a non-literal path, a missing file, a query string) fails the build. A load-time failure that is still this case throws `FRANK_IMPORT_META_URL`, naming the project file, line and reason. Parcel never runs this (local dev keeps its hashed assets); asset `import` statements keep esbuild's dataurl loader.

**Declared runtime packages need not be installed.** A bare import of a package `dependencies.js` declares that esbuild cannot resolve is stubbed like the fixed external list: `await import('<pkg>')` publishes as `import('<pkg>')`, a static import used inside functions loads at runtime. An installed package still bundles inline; an undeclared one still fails (`package.json` dependencies do not count); a value computed from the stub while the project loads fails with `FRANK_UNINSTALLED_DEPENDENCY_VALUE`.

**Host-registered packages (`@symbo.ls/sdk`).** A static import publishes as a synchronous registry read with a named error on a miss. A literal `import('@symbo.ls/sdk')` in code publishes as the on-demand marker (`@symbo.ls/utils` `lazyHostImportExpr`; since cli 3.14.826, before that the `import()` as written, which a browser rejects). A comment, a string, a member call `x.import(…)`, import attributes, a template specifier and a subpath stay as written (§10 → Host packages on demand).

### `toFS(data, distDir, options?)` — JSON → FS

Writes a `symbols/` directory from a JSON object (auto-generates `index.js`, `context.js`, sub-indexes). Used by editors that import a server-side project into a workspace.

### Always run `frank` after editing FS-bundled projects

When editing any project whose published artifact is a frank-bundled JSON (`app.json` or the referenced data inside `symbols.json`), the compiled JSON becomes stale on every source edit. **Always run `frank` to recompile** after any edit (component, page, design system, config, file). Verify the compiled output before declaring done.

### Function stringification gotchas

- `stringifyFunctions` skips `__fn`, `__fnMeta`, `__handler`, `__meta` (internal markers). Don't name your own keys this.
- The runtime revives a payload (`deepDestringifyFunctions`, `destringifyGlobalScope`, the server renderer's reviver) without any key named `__proto__`, `constructor` or `prototype`, at any depth — `state` and `globalScope` included. Such a key never reaches a prototype and never lands in the app. Don't name your own data keys this.
- WeakMap-backed circular handling means circular refs become `'[Circular]'` strings in the output; if your function captures the parent element via closure, the closure isn't preserved — the function body is, evaluated against the runtime context.
- `(el) => el.call('myFn', el.state.x)` round-trips fine. `() => MY_CONSTANT` publishes only because frank hoists `MY_CONSTANT` into the project's shared `globalScope` under its own name — a same-name declaration elsewhere or an element `scope` key collides with it. Put it in `scope: { MY_CONSTANT }` or `globalScope.js` (RULES.md Rule 33).

### Module discovery

Frank finds these files under `symbols/`:

| Path | Export style |
|------|--------------|
| `state.js` | `default` |
| `dependencies.js` | `default` |
| `sharedLibraries.js` | `default` (array) |
| `components/index.js` | namespace (`export *`) |
| `snippets/index.js` | namespace |
| `pages/index.js` | `default` |
| `functions/index.js` | namespace |
| `methods/index.js` | namespace |
| `designSystem/index.js` | `default` |
| `files/index.js` | `default` |
| `config.js` | `default` |
| `workers/<name>.js` | one module Web Worker per file (no `index.js`); published in the `workers` section, not the context (since smbls 3.14.859 / cli 3.14.826; below) |

Anything outside this list is invisible to frank. Don't put loadable code in `lib/`, `helpers/`, or other ad-hoc folders — either move it into one of the standard slots or import it from one of them.

**Lazy route groups** (SYNTAX.md → Router → Lazy routes) are the one more place: a folder that `context.js` (or `config.js`) names in `lazy: { admin: () => import('./admin/index.js') }`. Its entry module and its `components/`, `pages/`, `functions/`, `methods/` and `snippets/` are discovered; any other file in it is an orphan of the group. `toJSON` publishes the COMPLETE project: it merges every group into the canonical sections, replaces each route placeholder (`{ lazy: 'admin', … }`) by the group's page of the same route and drops `lazy` — the output equals the project declared eagerly. It refuses with a coded error a malformed `lazy` or a group exporting another section (`FRANK_LAZY_GROUP_INVALID`), a placeholder naming an undeclared group (`FRANK_LAZY_GROUP_UNDECLARED`), a loader that throws (`FRANK_LAZY_GROUP_LOAD_FAILED`), and a name or route the app already defines differently (`FRANK_LAZY_GROUP_COLLISION`). `toFS` (and so `smbls fetch`) writes the merged project eagerly — the split lives in your source tree.

#### Web Worker files — `workers/<name>.js`

Since smbls 3.14.859 / cli 3.14.826. Each file (`.js` or `.mjs`) is one MODULE worker: its global is the worker's own scope (`self.onmessage = …`, `self.postMessage(…)`), not the app's window, and it may import packages (they ship inside the worker). Start it from app code with the form every bundler resolves: `new Worker(new URL('../workers/<name>.js', import.meta.url), { type: 'module' })` (the path is relative to the calling file). Parcel (`smbls build`) and Vite emit each worker as its own hashed bundle, loaded only when it starts; `smbls build` never runs frank. `toJSON` ships each worker bundled (esbuild, one ES module, every import inlined) in a `workers` section, `{ <name>: { type: 'module', file: 'workers/<name>.js', code } }`; a `new URL('<file>', import.meta.url)` inside the worker graph (a `.wasm` beside its glue) resolves through `resolveAssetUrl` (`smbls push` uploads it). In the published code every caller's `new URL('…/workers/<name>.js', import.meta.url)` becomes `new URL('/__smbls/workers/<name>.js', globalThis.location.href)` (`@symbo.ls/utils` `workerScriptPath`), and the platform serves the worker's code there, same-origin, so `new Worker` accepts it. `workers` is publish data: nothing in the app reads it. `toFS` writes a worker back only where the tree lacks that file. frank-audit treats `workers/` as a frank slot (no FA006); in a worker file FA409 allows `self.X` / `globalThis.X` writes, and `window` stays banned.

---

## 10. Publishing — workflow + pitfalls

### One-shot: `smbls publish`

The full pipeline. Equivalent to `push` → `versions publish <id>` → `environments publish <env>` for each enabled environment.

```bash
smbls publish                   # default: push current project, mark new version as published, publish all envs
smbls publish --version <id>    # the LATEST version only (skip push); an older one is refused before any write
smbls publish --version <old> --mode version --env <env> # pin <env> to an older version; the published version stays
smbls publish --no-push         # use latest version on the server (skip push)
smbls publish --env staging     # publish only staging
smbls publish --env development,staging # CSV form (also: --env development --env staging)
smbls publish --mode latest     # set one mode on every target, pinned envs included
```

Without `--mode`, each environment keeps the mode it is configured with (no stored mode: prod-like envs = `published`, others = `latest`). An environment pinned to a version, or a branch-mode environment on another branch, is skipped and the output says so (`staging pinned to 1.5.1 — skipped; pass --env staging to move it`). Name it with `--env`, or pass `--mode`, to move it. See CLI.md "Publish flow".

**`--version` publishes the latest version only.** A `--version` (id or value) that is not the branch's latest is refused before any write, and the error prints the pin command. `--dry-run` gives the same refusal. To serve an older version, pin environments: `smbls publish --version <old> --mode version --env <env>` pins each target env to that version's value (an id is resolved to its value) and leaves the project's published version unchanged. The platform publishes the branch head as the next minor (`1.6.0` → `1.7.0`), and the CLI prints the version the server answered, never the one passed. If the version mark fails, each `mode: published` env is reported failed (it keeps serving the previous published version) and the command exits 1; `latest` / `version` / `branch` envs still publish. To bring old content back, use `smbls project restore`, not a publish. An older CLI publishes the latest version under any `--version` and prints the requested one.

### Granular commands

```bash
smbls push                      # frank → JSON → upload, no environment publish
smbls versions list             # versions on server
smbls versions publish <id>     # mark a version as the project's "published" one
smbls environments list         # enabled environments
smbls environments publish <env># republish env to pick up the new version
```

### `smbls build`

Runs the bundler (symbols-runner by default; parcel/vite only when set via the `bundler` field in `symbols.json`) and optionally pre-renders pages with brender:

```bash
smbls build                     # build SPA + brender pre-render
smbls build --no-brender        # SPA only
```

**Dev diagnostics.** The framework's dev-only warnings (`el.call` to a missing function, reserved-key notes, …) print in a dev runtime: `NODE_ENV` not `production`, or a `localhost` / `*.localhost` host. A parcel `smbls build` (production mode) strips them from the app bundle, so the built page is silent even on localhost (about 12 kB raw / 3.6 kB brotli less, smbls 3.14.845 / cli 3.14.811). `smbls start` (parcel serve) keeps them. Real errors stay in both. Debug a dev warning under `smbls start`, never on a built page. Since smbls 3.14.847 / cli 3.14.813 the parcel build also drops 62 more author-mistake warnings (an unknown design-system token, …), all behind `globalThis.__SMBLS_DEV_DIAGNOSTICS_OFF__`. A Vite build keeps every warning.

**Smaller production builds (opt-in).** `symbols.json` `build` has size options for a parcel `smbls build`, all off by default (CLI.md → `symbols.json` `build` — size options): `treeShakeComponents` / `treeShakeIcons` (`true` or `{ keep: [...] }`), `treeShakeLibraries: true`, `lazyServerUtils: true`, `treeShakeFeatures` (`true` or `{ keep: [...], drop: [...] }`). What app code must know:

- A default component, icon or feature the build left out logs one `console.error` naming the key and the option when the app asks for it (in production too); a left-out component renders as an empty element. The scan sees only source: put keys that only data carries (DB records, fetched payloads) in `keep`.
- With `lazyServerUtils`, `generateMetaTags`, `getPageMetadata`, `getImportMapScript`, `polyglotStartupScript`, `objectToString` and `deepStringifyFunctions` return a Promise in the browser: `await el.call('getPageMetadata', …)`.
- `treeShakeFeatures` feature names (for `keep` and `drop`): `autoGrow`, `inertOutside`, `bridge`, `viewEvents`, `lazyRoutes`, `viewTransition`, `liveSync`, `prerender` (kept when the build pre-renders), `safeInk`, `containerVw` (trigger `breakpointsFrom`), `capsize` (triggers `useCapsize` / `metrics`, or a `fontFamily` set to a font of capsize's metrics table; since smbls 3.14.858 / cli 3.14.825), `routeHead` (since smbls 3.14.862 / cli 3.14.828: a route entry's own head and the router's one page across such entries; the build reads the routes, not the source words — CLI.md), `themeColorList` (since smbls 3.14.862 / cli 3.14.828: the `'theme-color'` list; kept for a list, a name or a call, not a plain colour), `faceWait` (since smbls 3.14.865: the `faceWait` prop, `designSystem.faceWait` and `el.facesReady()`; triggers `faceWait`, `facesReady` — DESIGN_SYSTEM.md → fonts), `faceWaitLinks` (since smbls 3.14.869 / cli 3.14.832: faceWait's wait for a Google Fonts family stylesheet still on its way; left out when the configuration names no Google Fonts address in the design system's `font` table — CLI.md → `symbols.json` `build` — size options).
- **`smbls/core` kits** (since smbls 3.14.858 / cli 3.14.825). With `treeShakeFeatures` and `"smblsEntry": "core"` the build also leaves out each kit the `create()` configuration never switches on: `windows`, `dropdown`, `tooltip`, `shorthand`, `analyze`, `inspect`, `fetchOnCreate`, and the fetch `local` adapter. The kit names work in `keep` / `drop`; a left-out kit that the app asks for logs one `console.error` and resolves to nothing. `treeShakeLibraries` also keeps `@symbo.ls/channels` out of the boot, and the default-icon option drops a default icon that the project's own `designSystem.icons` replaces under the same name (CLI.md → `symbols.json` `build` — size options).
- **Lazy group parts** (since smbls 3.14.859 / cli 3.14.826). With `treeShakeFeatures`, `"smblsEntry": "core"` and `context.lazy` groups with plain `() => import('./file.js')` loaders, the framework parts that only group code uses (`inertOutside`, the bridge hooks, `TooltipLayer`) move into one file, `smbls.core.lazyParts-*.js`, which loads with the first group load. A part that the main code names, or `keep` names, stays in the main bundle (CLI.md → Lazy group parts); since smbls 3.14.862 / cli 3.14.828 only a group whose own code uses a part loads it, and a page built with that group preloads the file.
- A feature stays only for the setting that switches it on (smbls 3.14.849). `liveSync`: `socketUrl`, `notifications: true`, `verbose: true` or the runner. A member named `editor` or a bare `livesync` does not keep it. `lazyRoutes`: `lazy` as an object key or an assigned non-literal member (`lazy: { … }`, `ctx.lazy = groups`) or `loadLazy`. `React.lazy(`, `lazy: true`, `lazy: 'admin'`, `loading: 'lazy'` and a read of `ctx.lazy` do not keep it.
- `drop: [...]` forces a feature out when the app spells a trigger for something else. The build refuses it, with a warning, when the framework itself uses the feature or `keep` lists it, and (cli 3.14.818) when a build option or the config needs it: `prerender` while brender is on, `lazyRoutes` when `context.lazy` is an object, `viewTransition` when `designSystem.viewTransition` is set, `liveSync` when `socketUrl`, the runner, `notifications: true` or `verbose: true` is set. A scan hit alone still gives way to `drop`. Unknown names warn.

**Lean app bundles — `smbls/core`.** The `smbls` entry is the full runtime: it registers every bundled package on `globalThis.__SMBLS_PKGS__`, which published or fetched project code (frank-serialized functions, libraries fetched with `smbls fetch --scope libs`, raw JSON handed to `create()`) reads synchronously — and that registry keeps every export alive, so a bundler can drop nothing. `smbls/core` is the same API without the registry (no `registerHostPackages`, no `HOST_REGISTERED_PACKAGES`, no `importHostPackage` and no on-demand host-package loader), without the Simone client and socket.io, code-split so each kit and platform plugin is a file loaded only when switched on. For a parcel build, set `"smblsEntry": "core"` in `symbols.json` (CLI.md → Dev / build / deploy): every bare `smbls` import then resolves to `smbls/core`. Never import both entries in one app (two copies of the runtime), and never use `core` for an app that runs published or fetched code — its registry reads get `{}`.

On both entries the kits and platform plugins load only when the configuration switches them on; `create()` starts every load at once and awaits each before the first render: `windows` / `dropdown` / `tooltip` (on by default, `false` keeps each out), `analyze`, `shorthand`, `inspect`, `fetch` (the plugin and its REST adapter, one file), and live sync. `@symbo.ls/sync` loads only when `wantsLiveSync(ctx)` (`@symbo.ls/sync/applier`) finds a transport the page may use — a collab `socketUrl` (`editor.socketUrl` or `settings.socketUrl`) or `editor.runtime: 'runner'` — and no `sync: false`, or for its toasts (`notifications: true`). A page the platform published uses its `socketUrl` only inside an editor session (framed, or opened with `?liveSync`), so a published page outside an editor session loads no sync file. In `smbls/core` each kit is its own lazy file: an app that keeps a kit on pays one module request at boot (the kits it keeps load in parallel, after the entry has evaluated); the single-file builds carry them inline. Turn off the kits an app does not use. `symbols.json` `"build": { "modulePreload": true }` (opt-in) makes `smbls build` preload the lazy modules the config switches on, beside the entry (CLI.md → Dev / build / deploy).

#### Host packages on demand — `@symbo.ls/sdk`

Since smbls 3.14.859 / cli 3.14.826. `@symbo.ls/sdk` is a host-registered package: `smbls` never bundles it and no public CDN serves it; the page that runs the code supplies it. Project code reads it in one of two ways:

- **Static** — `import { SDK } from '@symbo.ls/sdk'` at the top of a file. The SDK ships inline in the first document, registered before boot (`Smbls.registerHostPackages`).
- **On demand** — a literal `import('@symbo.ls/sdk')` inside the function that needs it. frank rewrites the call into a fixed marker (`@symbo.ls/utils` `lazyHostImportExpr`): the registry first, then the page's loader, else a named rejection. When EVERY mention of the SDK in the page is a marker, and the page's smbls installs the loader, the first document carries no SDK bytes, only a declaration of a same-origin, content-hashed, immutable file: `window.__SMBLS_HOST_SOURCES__ = { '@symbo.ls/sdk': { src: '/__smbls/host/sdk.<sha256-16hex>.js', integrity: 'sha384-…', global: 'SymbolsSDK' } }`. The first call loads it: one classic `<script>` with SRI, one shared load for concurrent calls, one SDK instance per page (registry first, the first registration wins), the same SDK build the page would have inlined. `smbls start` / `smbls build` serve and write that file (CLI.md → Dev / build / deploy); the platform serves it for a published page.

```js
// functions/openAccount.js — the SDK loads on the first call
export const openAccount = async function (form) {
  const { SDK } = await import('@symbo.ls/sdk')
  // …
}
```

The loader is `importHostPackage(spec, { timeoutMs })` (the load deadline, default 30 s; hand-written code: `Smbls.importHostPackage('@symbo.ls/sdk')`), in the full `smbls` entry only; the full entry installs it as `globalThis[Symbol.for('smbls.importHostPackage')]`. `smbls/core` installs nothing. A failure rejects with an `Error` that has `code`, `specifier` and `retryable`; catch it and offer a retry (PATTERNS.md → Load the SDK on demand):

| `code` | When | `retryable` |
|---|---|---|
| `SMBLS_HOST_PACKAGE_LOAD_FAILED` | the file did not load (the script is removed; a retry inserts a new one) | yes |
| `SMBLS_HOST_PACKAGE_TIMEOUT` | the file did not load in 30 s | yes |
| `SMBLS_HOST_PACKAGE_NO_GLOBAL` | the file loaded but defined no global | yes |
| `SMBLS_HOST_PACKAGE_NO_SOURCE` | the page declares no file and registered nothing (every server render) | no |
| `SMBLS_HOST_PACKAGE_NO_DOM` | no document to load into | no |
| `SMBLS_HOST_PACKAGE_UNKNOWN` | the specifier is not host-registered | no |
| `SMBLS_HOST_PACKAGE_NO_LOADER` | no smbls runtime on the page provides the loader | no |

Rules for a page that should stay lazy (else it inlines the SDK as before, and still works):

- Write only the on-demand form. No static `import … from '@symbo.ls/sdk'` anywhere in the page's parts (app, shared libraries, kits).
- Name the specifier nowhere else inside a function body: frank publishes function text as written, so a comment or a string that names `@symbo.ls/sdk` is a mention. The function that imports on demand is published as bundle text, so the comments inside THAT function are not served.
- Never list `@symbo.ls/sdk` in `dependencies.js`.
- Push with a CLI whose frank has the marker (cli 3.14.826 or later). An older frank publishes the `import()` as written, and a browser cannot resolve that bare private specifier.
- A server render declares no file, so there the call rejects with `SMBLS_HOST_PACKAGE_NO_SOURCE`: call the SDK from a handler or after the first view, never while the page renders.

### `smbls deploy`

Targets a static host:

- `symbols` — push to Symbols platform
- `cloudflare` — Cloudflare Pages, or Workers static assets with `--target workers` (auto-creates `wrangler.jsonc` with `assets.directory: './dist'`; on a pre-rendered build it never falls back to `index.html`, which is the home page)
- `vercel` — auto-creates `vercel.json` (`cleanUrls`, a rewrite of every address without a file to `/200`)
- `netlify` — auto-creates `netlify.toml`
- `github-pages` — pushes to `gh-pages` branch (no rewrites there: the workflow copies `200.html` to `404.html` when the project has no not-found page)

A route without its own page (a `:param` route `brender.paths` does not list, `prerender: false`, an excluded or failed one) must get `200.html`, never another page: the rule per host is in CLI.md → Dev / build / deploy → Routes without their own page.

### Pre-publish checklist

1. **Run frank** — recompile JSON if the project's published artifact is a frank-bundled JSON.
2. **Audit components** — `mcp__symbols-mcp__audit_component` on changed components.
3. **Verify the design system tokens are present** — every color/spacing/typography token used in components must be defined in `designSystem/`. Missing tokens cause silent visual fallbacks in production.
4. **Check `dependencies.js`** — any package referenced from project code must be in `dependencies.js` so mermaid can resolve it via importmap. Missing entries fail at runtime in deployed channels.
5. **`config.js` flags** — `useReset`, `useVariable`, `useFontImport`, `useIconSprite`, `useSvgSprite`, `useDefaultConfig`, `useDocumentTheme` should all be `true` for normal projects. Mermaid's bundle script defaults them to `true` if missing, but explicit beats implicit.
6. **The `fetch` config is plain data** — no `createClient` or other function in `config.js` `fetch` (the served runtime deletes `fetch.createClient`; a self-contained `seed.isStale` / `seed.onRefresh` / `early` request function is the exception), no `db:` key, no `adapter: 'supabase'` (RULES.md Rule 59).
7. **No browser-only top-level code in modules** — see §8 SSR rules above. If you import a leaflet/mapbox/etc. package at the top of a component file, brender will crash and fall back to client-render. Lazy-load instead.
8. **Test with `channel=production`** — `smbls deploy --channel production` (or `mermaid` with `BRENDER=true`) catches SSR regressions early.

### Common publish-time failures

| Symptom | Cause | Fix |
|---|---|---|
| Page renders blank in deployed env | Brender failed silently → client render path expected hydration markers | Run `smbls build` locally with `BRENDER=true`; check console for the brender warning |
| Theme flashes wrong color on first paint | Project-side `setAttribute('data-theme', …)` racing `resolveAndApplyTheme`, OR `useDocumentTheme: false` skipping the design-system's document background/color application | Remove any project-side theme setAttribute (framework owns it via `resolveAndApplyTheme`). Keep `useDocumentTheme: true` so the design system's `document` block applies on `<body>` |
| Declarative `fetch:` loads nothing; `getDB()` returns `null` | The adapter config sits under `db:`, which the runtime never reads | Rename it to `fetch:` in `config.js` (RULES.md Rule 59) |
| `Unknown db adapter: "supabase"` after about 5 s | `@symbo.ls/fetch` has no Supabase adapter | `fetch: { adapter: 'rest', url: 'https://<project>.supabase.co/rest/v1', headers: { apikey } }`, or a registered adapter; drop `createClient` and `@supabase/supabase-js` |
| Routes 404 in deployed env | `pages/index.js` default export not in expected `{ '/': X, '/about': Y }` shape | Frank only picks up the default export of `pages/index.js`. Named exports must be re-exported there |
| Font flicker / FOUT | `useFontImport: false` or design system `font` block missing `fontFace` | Set `useFontImport: true` and define `fontFace` for every font family. Text that must not show in a fallback face: `faceWait: true` (DESIGN_SYSTEM.md → fonts; since smbls 3.14.865) |
| CSS vars missing in iframe | Multi-app secondary not getting its own document on `config.document` | Use the framework's `prepareDesignSystem` flow — pass `context.document` (and `themeRoot`) to the iframe app's `create()` call. Don't manually inject CSS into the iframe |
| `[smbls/router] no content matched for path /` warning | Router fired before pages were registered | Verify `context.pages` exists (frank picks it up from `pages/index.js`'s default export). Check `context.router !== false` |
| Parcel dev server crash: `ENOENT: no such file or directory, open '.../.parcel-cache/<hash>'` | Race in Parcel's dev cache write/read after a fresh build | Clear `.parcel-cache` AND `dist` for the project, restart. Not a code bug. For framework-level changes, run the monorepo-wide nuke: `find <your-monorepo-root> -name ".parcel-cache" -type d -exec rm -rf {} +` |
| Text leaking into the page from an inline `childExtends` object | css-in-props edge case with inline-object `childExtends` | Extract the inline `childExtends` to a named component referenced by string |
| `backdropFilter` value bleeds into text content | css-in-props bug on this specific property | Wrap in a `style: { backdropFilter: '...' }` block instead of a top-level prop |
| External package `Cannot find module` at runtime | Listed in `package.json` but not in `symbols/dependencies.js` (or vice-versa) | Both lists are required. `package.json` is for `npm install`; `symbols/dependencies.js` is what the Symbols runtime resolves via importmap |
| Atomic class resolves to empty body in production (`._c-neutral900 { }`) but works locally | The design-system token is missing from the published bundle (color/spacing/font defined in `designSystem/` but not present in the version that mermaid serves). The atomic-class generator runs against whatever tokens are present and silently emits an empty rule for missing ones | Re-run `frank` to recompile the published JSON, then republish. Diagnose via Chrome devtools: walk `document.styleSheets`, grep for the class name, inspect the rule body. Empty body confirms the token is missing on the server side, not a CSS-in-props bug |
| Branded base color (`color.black: '#10241A'`) bleeds into dark-mode page background | `theme.document` falls back to bare `'black'` / `'white'` / `'neutral'` tokens, which resolve to the brand's tinted versions instead of stepped neutrals | Always pair branded core tokens with explicit `theme.document.@dark` / `@light` blocks in `designSystem/theme.js`. Use the modifier system (`neutral+45`, `neutral-45`, `neutral=50`) to step away from the tinted base; reserve bare `black` / `white` / `neutral` for places where the brand tint is intentional. See `DESIGN_SYSTEM.md` "Branded core tokens" |
| A fix that works in the dev shell / a Parcel build does NOT show on `*.at.symbo.ls` (e.g. `hide:` true-at-birth on a Button/IconButton stays visible) | The worker-injected runtime is the LAST PUBLISHED `smbls` npm package (`smbls/iife-string`, pinned to an exact version by the hosting worker), NOT the latest smbls source. A framework fix reaches published sites only after npm publish → pin bump → worker deploy | Check before diagnosing: download `smbls@<pinned>` and byte-compare its `dist/smbls.iife-string.js` with the `var Smbls=` script in the served page (they match exactly when the pin is live); grep the served IIFE for a marker the fix introduced (e.g. `__explicitDisplay` for the `hide:` fix). Same code, different build = "stale published runtime", not a second bug |
| "`@mobileL` / `@media` props emit no CSS on the published page" | A grep of `<style>` textContent or the HTML is BLIND — css-in-props inserts rules via CSSOM (`insertRule`), so the sheets have no text. The rules ARE emitted (verified under smbls 3.14.785: `@media screen and (max-width: 768px)` rules for `@mobileL` blocks, `display:none` included) | Read `document.styleSheets[*].cssRules` (recurse into `CSSMediaRule.cssRules`) and match the element's generated class. If the element still shows, look for an INLINE `style="display: …"` writer (explicit-display enforcement) outranking the media rule — a different defect with a different owner |
| `el.call('polyglot', key)` returns `undefined` on the published page while `{{ key \| polyglot }}` pipes work | The project imported `@symbo.ls/polyglot` (see §6): frank stubbed it and the payload carries `functions.polyglot: ""` / `plugins: [""]` — the phantom blocked the runtime's own registration | Remove the project-side polyglot imports; the runtime registers from `context.polyglot`. (A current runtime also ignores the phantom.) |
| `s.add('history', item)` "drops entries" — after the first add the array is gone | `s.add(key, value)` ASSIGNED the key in older runtimes: `history` became the item object, the next iteration threw inside a factory and DOMQL swallowed it. Same in a Parcel build — not a published-runtime divergence | A current runtime: `add` appends to an array key / merges into an object key / sets otherwise (SYNTAX.md). Until the worker carries it, write `s.update({ history: [...s.history, item] })` on published sites |

---

## 11. What never to do

- Edit `node_modules/`, framework `dist/` files, or shared-library source from a consumer project. Surface the issue to the user before touching shared code.
- Use `document.querySelector` / `window.location` / direct DOM mutation from project code. Use `el.lookup(...)` / `el.lookdown(...)` / `el.router(...)` / `el.set(...)` / `el.update(...)`.
- Add `style: { ... }` overrides or `!important` to work around layout bugs — fix the layout (or extend the design-system token).
- Wrap a broken component in a div to hide its broken behavior.
- Copy-paste duplicated logic instead of extracting into a snippet, function, or component.
- Skip `frank` when editing template projects. The published JSON drifts silently.
- Hand-roll a router, theme switcher, fetch wrapper, i18n helper, or metadata system. The framework already has one — extend it instead of replacing it.
- Use raw CSS (px, rem, hex, rgba) when design system tokens exist.
- Mutate `window.Smbls.CONFIG.*` (or any other framework runtime
  singleton) from project code. The framework owns its own state —
  changing it from `app.onRender` or anywhere else creates race
  conditions with the framework's own writes and silently breaks
  multi-app config isolation. If you need to influence config, do it
  through the legitimate API (`config.js` flags, `changeGlobalTheme`,
  `setLang`, options passed to `create()`).
- Use `<style>` tags in `index.html` or inject `<style>` blocks at
  runtime to patch atomic-class colors, theme variables, or fonts.
  The right fix is in `designSystem/` — add the missing token or
  theme variant.
- Use the browser-MCP tool to mutate live page state during testing.
  It's a read-only inspection surface (`getComputedStyle`,
  `document.styleSheets`, `document.documentElement.getAttribute`,
  `getPropertyValue`). Mutating from MCP masks real bugs and is not
  reproducible without the MCP harness.

---

## 12. Migrating legacy projects (v2 → v3+)

Use this checklist when pulling a v2 DOMQL project into the modern
framework.

### Syntax renames

| v2 | v3+ |
|---|---|
| `extend` | `extends` |
| `childExtend` | `childExtends` |
| `childExtendRecursive` | `childExtendsRecursive` |
| `on: { click: fn }` | `onClick: fn` |
| `on: { init: fn }` | `onInit: fn` |
| `on: { render: fn }` | `onRender: fn` |
| `on: { initStateUpdate: fn }` | `onInitStateUpdate: fn` |
| `on: { initUpdate: fn }` | `onInitUpdate: fn` |
| `align: 'center space-between'` (in `props`) | `flexAlign: 'center space-between'` (root level) |
| `flow: 'y'` | `flexFlow: 'column'` |
| `props: { X: Y }` (object) | flatten X to component root |
| `$collection` | `children: ({ context }) => [...]` |
| `$stateCollection` | `state: 'data'` + `childExtends: 'Row'` + `children: ({ state }) => state` |
| `DOM.create()` / `createSync()` | `create()` from `smbls` |
| `DOM.define()` | use built-in atoms (`Collection`, etc.) or inline `define` block on parent |

### Architectural changes

- **Routing:** swap any `Pattern B` / `Pattern C` (custom `router.js`,
  `Folder` nesting, `el.call('router', ...)` chains) for **Pattern A**
  (empty `app.js` + `pages/index.js` route map) unless there's a documented
  reason. See §4 above.
- **Cross-file imports:** v2 projects often imported components/functions
  from each other directly. v3+ resolves components by string name
  (`extends: 'ComponentName'`) and functions via `el.call('fnName', ...)`.
  Remove every cross-file import.
- **Inline `childExtends` extraction:** `childExtends: { extends: 'X', ... }`
  inline objects should be extracted to a named component in `components/`
  for any pattern that's reused. Inline objects work at runtime but
  inflate frank-serialized JSON.
- **`define` blocks at app root:** Custom defines (e.g. `$query`,
  `$setCollection`, `$stateCollection`) are inherited by all children.
  Keep them on the app root rather than scattering.

### Removable legacy deps

Common v2 deps that can be dropped during migration:

| Package | Reason | Replacement |
|---|---|---|
| `fastclick` | Modern mobile browsers don't have the 300ms tap delay; click synthesis causes ghost-click bugs | Delete it. If you want the pressed-state / tap-highlight polish it used to provide, use `@symbo.ls/tap` instead (`plugins: [tapPlugin]`) — declarative, no synthesis. See `MODERN_STACK.md` → `@symbo.ls/tap` |
| `@domql/cookie` | Bundled into smbls utils | `el.call('setCookie' / 'getCookie')` via context |
| `axios` | Native `fetch` in every modern runtime | `fetch(...)` (or the `@symbo.ls/fetch` declarative API) |

Remove from BOTH `package.json` and `symbols/dependencies.js`.

### Color & shadow normalization

Hand-written rgba and comma-separated shadows from v2 should become named
tokens in `designSystem/color.js` and space-separated values:

```js
// designSystem/color.js
whiteLight:  'rgba(255,255,255,0.1)',     // was 'white .1'
whiteBorder: 'rgba(255,255,255,0.35)',    // was 'white .35'
blackMuted:  'rgba(0,0,0,0.35)',          // was 'black .35'

// In components — boxShadow space-separated, named color
boxShadow: '0 0 C3 blackMuted'             // was '0, 0, C3, black .35'
```

Border shorthand becomes three props (see DESIGN_SYSTEM.md "Borders"):

```js
// v2
border: '1px, solid, border'

// v3+
borderWidth: '1px',
borderStyle: 'solid',
borderColor: 'border'
```

### Theme handling

v2 projects often stored `globalTheme` in root state and called
`document.documentElement.setAttribute('data-theme', …)` from a
`switchTheme` function. **Replace both** with the framework's
`changeGlobalTheme(...)` API. See `DESIGN_SYSTEM.md` for the contract.

### Project config

Every migrated project needs:

```json
// package.json (root, not symbols/)
{
  "scripts": { "start": "smbls start", "build": "smbls build" },
  "dependencies": { "smbls": "*" }
}
```

```json
// symbols.json (root) — omit `bundler` to use symbols-runner (default).
// Only set "bundler": "parcel" (or "vite") for projects that genuinely need it.
{ "key": "<project-name>.symbo.ls", "dir": "symbols" }
```

```html
<!-- symbols/index.html -->
<html>
  <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
  <body><script type="module" src="./index.js"></script></body>
</html>
```

**No `<style>` tags in `index.html`.** All styling goes through CSS-in-props.

### Parcel cache after framework changes

When smbls itself changes (new packages/element behavior, new define
handlers, etc.) every dependent project's `.parcel-cache` is stale. Nuke
them all before restarting dev servers:

```bash
find <your-monorepo-root> -name ".parcel-cache" -type d -exec rm -rf {} +
```

Then restart any active dev server. Don't kill the portless proxy on
`:1355` — that tears down every other app. Find the actual app's parcel
PID via `ps aux | grep 'portless <app-name>'` and restart by direct port.

---

## 13. App teardown — destroy / dispose / context.key

### `destroy(app)` — named app teardown

`destroy` is a named export from `'smbls'`. It is also available as `app.destroy()` on the object returned by `create()`.

```js
import { create, destroy } from 'smbls'
import context from './symbols/context.js'

const app = await create({ … }, context)

// Swap apps cleanly — tear down the old one first
destroy(app)                // returns true on first call; false if already destroyed (idempotent)
```

Teardown order inside `destroy(app)`:

1. Runs every function registered in `context.__teardowns` (popstate listener, custom consumer hooks) — these fire BEFORE the element tree is walked so they can still read context state.
2. Calls `dispose(app)` — recursive element teardown (see below).
3. Clears memoized `fetch.__resolved` / `fetch.__resolving` / `db.__resolved` / `db.__resolving` caches so a re-`create()` starts fresh.

`destroy` does NOT strip CSS rules from the shared `<style data-smbls>` sheet. Those sheets are realm-wide by design (atomic CSS dedup, scoped IDs). Orphan rules are inert — their selectors target content-hashed class names that no new element will ever share.

### `dispose(element)` — recursive element teardown

`dispose` is a named export from `'smbls'` (re-exported from `@symbo.ls/element`). Unlike `destroy`, it walks only the element subtree — it does NOT run `context.__teardowns`.

```js
import { dispose } from 'smbls'
dispose(someChildElement)
```

Teardown order inside `dispose(element)`:

1. `onBeforeRemove(el, state, context)` — user hook fires FIRST, before anything is torn down. Handler can still read state and cancel sockets / in-flight requests.
2. Reactive effects (`ref.__effects`) disposed.
3. Delegated event listeners (`ref.__eventCleanup`) removed.
4. Children recursively disposed.
5. DOM node removed from parent.
6. Owned state (`state.destroy()`) called if this element owns it.
7. Element removed from parent's `__children` tracking.
8. `onRemove(el)` — user hook fires AFTER DOM detach + `state.destroy()`, BEFORE refs cleared. Safe for logging `el.key` / `el.parent`.
9. Refs cleared (`el.node = null`, `el.parent = null`, `el.__ref = null`).

Both `onBeforeRemove` and `onRemove` are wrapped in try/catch — a misbehaving handler does not block sibling cleanup.

### `context.key` derivation

Every app instance has a stable identifier at `context.key`. Derivation order (first truthy value wins):

1. Explicit `context.key` supplied by the caller.
2. `symbolsConfig.owner` + `symbolsConfig.key` combined → `"owner--key"` (e.g. `"system--canvas"`, `"system--workspace"`). Used when both fields are present in `symbols.json`.
3. Bare `symbolsConfig.key` (when no owner).
4. The `app` argument if it is a string.
5. `'smblsapp'` — the default fallback.

Source: `smbls/packages/smbls/src/createDomql.js:40-46`.

Apps in the same browser realm (e.g. canvas editor + preview iframe mounted on the same page) get unique stable identifiers from this derivation, which drives atomic-CSS prefix isolation and design-system config lookup.

### Live sync — collab socket identity needs an owner (`@symbo.ls/sync`)

**Since smbls 3.14.865 (sync 3.14.708, utils 3.14.856, freestyler 3.14.658).** This section describes the owner + key identity: the collab socket, the `editor.remote` project fetch (`X-AppKey: owner/key`, no fetch without an owner), the shared-library API fallback (searched by owner) and freestyler's `projectKey`. A project is named by owner + key: the server answers a bare key that several owners share with 409 `ambiguous_key`, and never picks one. Set `owner` in `symbols.json`; older releases ignore it.

The collab live-sync transport (`SyncComponent`, attached via `syncPlugin` when a page wants live sync) opens a socket only when it can name the project. The collab server resolves a handshake by `projectId` first (unique, wins outright — `owner` is then optional, carried along if known), then by `owner` + `projectKey` — a bare key alone is the legacy 1-seg route and is not unique across owners (`acme/web` and `globex/web` share the key `web`).

`editor.projectId` (mermaid injects the served record's `_id`) is read straight off. With no `projectId`, `owner` is required and comes from, first match wins (`plugins/sync/identity.js`):

1. `editor.projectKey` — paired ONLY with `editor.owner` (never with `ctx.owner` / `symbolsConfig.owner`, even when those are set).
2. `ctx.key` + `ctx.owner` — the served project data: mermaid fills `owner` from the appkey, the runner fills it from `symbols.json`.
3. `symbolsConfig.key` + `symbolsConfig.owner`, when that key is the one in use — `prepareContext`'s `<owner>--<key>` composite (see "context.key derivation" above) maps back to this pair.

**No `projectId` and no owner anywhere → fails closed.** No service-token request, no socket — one `console.error` naming the fix: set `owner` in `symbols.json` (or `context.owner` / `editor.owner`), or pass `editor.projectId`.

**A key shared by more than one owner → the server answers `ambiguous_key`.** The client logs one `console.error` naming every candidate as `owner/key`, then disconnects — it never retries the same ambiguous join.

**Every (re)connect takes a fresh service token.** The socket's token expires; a reconnect after that fetches a new one instead of replaying the old one. A refresh that fails logs one warning and closes the socket. A join the server refuses (a private project the token may not see) logs one warning naming `owner/key` and does not reconnect. A session the server ends after a join gets one fresh handshake, not a loop.

Set the owner once, in `symbols.json`:

```json
{ "owner": "acme", "key": "web" }
```

### `import * as` getter-only namespaces — Parcel fallback

`prepareContext` in `createDomql.js` rehydrates function-strings back to real functions after frank serializes a project. When the bucket (`functions`, `methods`, `snippets`) is an ESM-namespace-shaped object with getter-only own properties, `Object.assign(value, destringified)` throws a `TypeError`. The framework now catches that error and assigns the destringified clone to the key instead:

```js
try { Object.assign(value, destringified) } catch (e) { if (key) target[key] = destringified }
```

This means `import * as functions from './functions/index.js'` in `context.js` no longer breaks published Parcel-compiled projects. The old warning to avoid `import * as` for functions/methods/snippets context keys is no longer applicable — Parcel getter-only namespaces are handled by the rehydrate fallback.

---

## 14. Where to read more

| Topic | Doc |
|---|---|
| Design system + theme contract | [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) |
| Modern plugin stack (fetch / polyglot / helmet / router / scratch / **analyze**) | [`MODERN_STACK.md`](./MODERN_STACK.md) |
| Shared libraries (link vs destDir, drift, smbls libs CLI) | [`SHARED_LIBRARIES.md`](./SHARED_LIBRARIES.md) |
| Fetch | `plugins/fetch/README.md` |
| Polyglot (i18n) | `plugins/polyglot/README.md` |
| Helmet (SEO) | `plugins/helmet/README.md` |
| Brender (SSR) | `plugins/brender/README.md` |
| Frank (JSON ↔ FS) | `plugins/frank/README.md` |
| Analyze (runtime audit logger) | `plugins/analyze/README.md` |
| Router | `plugins/router/README.md` + `packages/smbls/src/router.js` |
| CLI | `packages/cli/bin/*.js` (top-level `smbls libs`: `bin/libs/README.md`) |
| Element create flow | `packages/element/src/create.js` |
| Scratch (design system) | `packages/scratch/src/` |
| Design system tokens | each project's `symbols/designSystem/` + `packages/default-config/` |

When you can't find what you need above, the source is:

```
packages/
  smbls/         # entry point, create(), prepareContext, prepareDesignSystem, router init
  element/       # @symbo.ls/element — DOMQL element creation, lifecycle, reactivity
  state/         # state proxy + store methods
  signal/        # createSignal / createEffect / batch (the reactivity primitive)
  scratch/       # design-system token resolver, theme system
  css-in-props/  # CSS prop transforms (color, spacing, layout, …)
  attrs-in-props/# HTML attr handling
  utils/         # shared utilities
  default-config/# default DOMQL components + design system
  domql/         # DOMQL spec + bundled distributions
  cli/           # smbls CLI
  css/           # atomic CSS engine

plugins/
  router/        # @symbo.ls/router — defaultRouter, parseRoute, matchRoute
  fetch/         # @symbo.ls/fetch — declarative data + adapters
  polyglot/      # @symbo.ls/polyglot — i18n
  helmet/        # @symbo.ls/helmet — metadata / SEO
  brender/       # @symbo.ls/brender — SSR + hydration
  frank/         # @symbo.ls/frank — JSON ↔ FS
  mermaid/       # deployed runtime (Express + CF Worker handler)
  capsize/ shorthand/ funcql/ qsql/ tunnel/ sync/ ...
```

Use `mcp__symbols-mcp__*` tools (`get_project_rules`, `get_sdk_reference`, `search_symbols_docs`, `audit_component`) before writing or modifying any Symbols code.
