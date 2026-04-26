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
    config.js            # framework flags (useReset, globalTheme, themeStorageKey, db, fetch, polyglot, ...)
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
`Icon_2` (the `_<suffix>` is ignored for extend resolution). Prefer
renaming the key to match the extended component over aliasing.

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
- `color`, `background`, `boxShadow`, `border`, `textShadow`, etc. follow CSS syntax but are **empowered by the scratch design system** — values can be design-system tokens (named colors, spacing keys, timing keys, CSS vars), and color tokens accept opacity + lightness modifiers via the grammar below.
- Color token grammar `<colorName>(.<alphaDigits>)?(<+N|-N|=N>)?` (`packages/scratch/src/utils/color.js:180`):
  - `.N` is **alpha** (`'white.5'` → `rgba(...,0.5)`), NOT a shade index — don't confuse with Tailwind's `blue-700` palette syntax.
  - `+N` lightens by `N` / `-N` darkens by `N` (both operate on lightness).
  - `=N` sets HSL lightness to `N%` (absolute).
  - Combinable: `'white.5+10'` (alpha 0.5 + lighter), `'neutral.3=40'` (alpha 0.3 + lightness 40%).
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

- The framework owns `data-theme`. **Never** call `setAttribute('data-theme', …)` from project code. The framework writes it via `resolveAndApplyTheme` (early-paint) and `changeGlobalTheme` (runtime).
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
                                        → defaultRouter(url, element, ...)
                                        → element.set(pageDef, { contentElementKey: 'content' })
                                        → element.content gets the matched page
```

`initRouter(app, context)` wires `app.onRenderRouter = onRouterRenderDefault` automatically (unless the project defines its own). `app.routes = ctx.pages` is set just before element creation, so `targetEl.routes` is populated when `defaultRouter` reads it.

`onpopstateRouter` registers a `window.onpopstate` handler so back/forward navigation re-runs the router.

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

Default `routerOptions` (from `@symbo.ls/router` README): `pushState`, `popState`, `scrollToTop`, `injectRouterInLinkComponent`, `useParamsMatching`, `removeOldElement`, `level`, `contentElementKey: 'content'`.

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
  click handling into the `Link` component).

---

## 5. `@symbo.ls/fetch` — declarative data

Full reference: `plugins/fetch/README.md`. Auto-registered when `context.fetch` (root or page) or `context.db` is set.

### Configure once in `config.js`

```js
db: {
  adapter: 'supabase',          // 'supabase' | 'rest' | 'local'
  createClient,                  // for supabase — pass createClient from @supabase/supabase-js
  url: 'https://xxx.supabase.co',
  key: 'sb_publishable_...',
  auth: { persistSession: false /* ... */ },
  db:   { schema: 'my_tenant' },
  global: { headers: { 'x-tenant-slug': 'my_tenant' } }
}
```

Use `db: { adapter: 'supabase', state: 'supabase' }` to merge config from `state.root.supabase` instead of inlining keys.

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
```

### Cache, retry, dedupe, focus refetch — all default-on

Defaults: `cache: { stale: '1m', gc: '5m' }`, `retry: 3` (exp backoff), `refetchOnWindowFocus: true`, `refetchOnReconnect: true`. Override per-fetch:

```js
{ fetch: { from: 'X', cache: false, retry: false, refetchOnWindowFocus: false } }
```

### State path syntax

- `~/key` — root state (e.g. `as: '~/venues'`)
- `../key` — parent state
- `dashboard/stats` — nested path
- omit `from` and let it derive from `state` key

### Triggers

`on: 'create'` (default) | `'click'` | `'submit'` | `'stateChange'`. For `'stateChange'`, `params: (el, s) => ({ q: s.query })` re-fetches when reads change.

### Optimistic updates + cache invalidation

```js
{
  fetch: {
    method: 'update', from: 'posts',
    params: (el) => ({ id: el.state.postId }),
    on: 'click',
    optimistic: (data, current) => ({ ...current, likes: current.likes + 1 }),
    invalidates: ['posts']     // or true (all "posts:*"), or ['*'] (everything)
  }
}
```

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
// also: db.insert / .update / .delete / .rpc / .upload / .signIn / .onAuthStateChange ...

import { queryClient } from '@symbo.ls/fetch'
queryClient.invalidateQueries('articles')
queryClient.setQueryData('articles:select:', (old) => [...old, newOne])
queryClient.prefetchQuery({ from: 'profile' }, context)
```

### Auth guard

`{ fetch: { from: 'profile', auth: true } }` — fetch only fires when `db.getSession()` returns a session.

### Status surfaces

`el.__ref.__fetchStatus = { isFetching, isLoading, isStale, isSuccess, error, status, fetchStatus }` (verified at `plugins/fetch/index.js:394-399, 508-514`). Also `__fetching` (mirrors `isFetching`), `__fetchError` (mirrors `error`). Callbacks: `onFetchStart`, `onFetchComplete`, `onFetchError`.

Note: there is no `isError` boolean field — derive from `!!__fetchStatus.error` if needed.

### Anti-patterns

- Don't bypass adapter — `await fetch(...)` from inside DOMQL skips cache, retry, dedupe, optimistic, and the `Accept-Language` header injection.
- Don't ship `db.createClient` (a function) in published JSON. `mermaid/src/bundle.js:65-66` strips it (`delete context.db.createClient`). The Supabase adapter at `plugins/fetch/adapters/supabase.js:16-19` falls back to `await import('@supabase/supabase-js')` when no `createClient` is provided, so put the package in `dependencies.js` and let the runtime import it. Trying to keep the function reference across JSON is futile.
- Don't write to state inside a fetch's own `transform` and a parent's `onFetchComplete` for the same key — race on cache resolution. Pick one.

---

## 6. `@symbo.ls/polyglot` — i18n

Full reference: `plugins/polyglot/README.md`. Auto-registered when `context.polyglot` is set; auto-merges `polyglotFunctions` into `context.functions`.

### Static translations

```js
context.polyglot = {
  defaultLang: 'en',
  languages: ['en', 'ka', 'ru'],
  storageLangKey: 'myapp_lang',     // localStorage key for active lang
  storagePrefix: 'myapp_t_',        // localStorage prefix for translations
  translations: {
    en: { hello: 'Hello' },
    ka: { hello: 'გამარჯობა' },
    ru: { hello: 'Привет' }
  }
}
```

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

### Using translations in components

The functions registered by `polyglotFunctions` (verified at
`plugins/polyglot/functions.js:5-14`) are:

```
polyglot          → translate(key, lang?)
getLocalStateLang → reads `state.<key>_<lang>` for per-language state fields
getActiveLang     → reads state.root.lang or context.polyglot.defaultLang
getLang           → alias for getActiveLang
setLang           → switch + persist + load remote (async)
getLanguages      → array of available language codes
loadTranslations  → manually trigger remote load for a lang
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

// Switch language
{ onClick: (e, el) => el.call('setLang', 'ka') }

// Read current language
{ text: (el) => el.call('getLang') }
```

### Auto integration with fetch

When polyglot sets `state.root.lang`, every fetch request gets an
`Accept-Language` header automatically (verified at
`plugins/fetch/index.js:537-540`). The header is the only injection;
fetch does NOT add a `lang` query parameter or RPC argument. If your
backend expects `lang` in `params`, set it explicitly:

```js
fetch: { from: 'articles', params: (el, s) => ({ lang: s.root.lang, status: 'published' }) }
```

### CMS upsert

```js
el.call('upsertTranslation', 'ui.nav.home', 'en', 'Home')   // optimistic + persists
```

### Anti-patterns

- Don't mirror `lang` into a separate state field. `state.root.lang` is the source of truth — polyglot reads/writes it directly.
- Don't rebuild your own language switcher; `setLang` already handles localStorage + remote refetch + state.
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

### Supported keys

Two surfaces with **different supported-key sets**.

**Runtime (browser)** — `applyMetadata()` in
`plugins/helmet/index.js:173`. Looks up keys in the
`META_TAGS` table at `index.js:7-32`. Unknown keys are silently
skipped. Supported set:

```
title, description, keywords, robots, author, canonical,
image, url, siteName, type, locale, theme-color,
og:title, og:description, og:image, og:url, og:type, og:site_name, og:locale,
twitter:card, twitter:title, twitter:description, twitter:image, twitter:site
```

**SSR / brender HTML** — `generateHeadHtml()` in
`plugins/helmet/index.js:209`. Broader prefix-rule set:

- All runtime keys above PLUS:
- `viewport` (auto-emits a default if not set)
- `icon` / `favicon` — `<link rel="icon">` with type auto-detected
- `favicons` (array) — multiple `<link rel="icon">`
- `alternate` (array) — multiple `<link rel="alternate">`
- `og:*`, `article:*`, `product:*`, `fb:*`, `profile:*`, `book:*`,
  `business:*`, `music:*`, `video:*` → `<meta property="X">`
- `twitter:*`, `DC:*`, `DCTERMS:*` → `<meta name="X">`
- `http-equiv:X` → `<meta http-equiv="X">`
- `itemprop:X` → `<meta itemprop="X">`
- Any other string-valued key → `<meta name="X">` fallback

If you set e.g. `article:author` and rely on it client-side, the
runtime won't emit it (it's not in META_TAGS). It WILL appear in the
SSR HTML brender produces.

### SSR priority order (brender)

Verified at `plugins/helmet/index.js:77-156` (`extractMetadata`):

1. `data.integrations.seo` — lowest priority (defaults), line 83-85
2. `data.app.metadata` — medium, line 87-90
3. `page.metadata` (or `page.helmet`) — highest, line 95-99
4. Falls back to `page.state.title` / `page.state.description`, line 101-108
5. Final default: `data.name || 'Symbols'` for `title`, line 111-113
6. Bare filenames resolved against `data.files[val].src`, line 144-153

### Auto-cascade behavior (verified `helmet/index.js:117-141`)

Helmet automatically derives `og:*` and `twitter:*` from `title` /
`description` when the page sets one but not the other:

- `title` → `og:title` (only if not explicitly set on page)
- `title` → `twitter:title` (always, if no twitter:title)
- `description` → `og:description` (only if not explicitly set)
- `description` → `twitter:description` (always)

Plus: `og:url` (or `url`) is **route-aware** — if you set a base URL and
the current route is non-`/`, helmet appends the route to produce
`og:url = baseUrl + route`. Stops at the first trailing slash.

### Anti-patterns

- Don't write to `document.title` or insert `<meta>` tags from project code. Helmet owns them; manual writes drift on route change.
- Don't manually duplicate `title` into `og:title` / `twitter:title` — the auto-cascade does it. Setting them only when you need a *different* social-only string.

---

## 8. `@symbo.ls/brender` — SSR + hydration

Full reference: `plugins/brender/README.md`. Renders DOMQL trees to HTML on the server, then hydrates them in the browser by remapping `data-br="br-N"` keys back to live elements.

### When brender runs

- **`smbls brender`** CLI — pre-renders every static route to `dist-brender/`. Param routes (`/blog/:id`) are skipped (need runtime data).
- **`smbls build`** — runs brender pre-rendering as part of the bundler build (for the static-export path).
- **mermaid** runtime — calls `renderRoute(...)` per request when `channel === 'production'` or `'staging'`. Falls back to client-side render if brender throws or `BRENDER=false` env var is set.

Brender is opt-in via `symbols.json`:

```json
{ "brender": true, "brenderDistDir": "dist-brender" }
```

### Theme during SSR

Brender defaults to `globalTheme: 'auto'` and emits both:

- `[data-theme="<scheme>"]` selectors (forced themes, including custom)
- `@media (prefers-color-scheme: dark|light) :root:not([data-theme])` (OS preference fallback)

So themes work without JavaScript on the rendered HTML. `resolveAndApplyTheme` in the client bundle then writes the concrete `data-theme` attribute on first paint.

### Hydration contract (`data-br`)

1. **Sequential** — `br-0`, `br-1`, … assigned in DOM tree order via depth-first traversal.
2. **Deterministic** — same DOMQL input always produces the same key assignment; server and client don't need to exchange the registry.
3. **Element nodes only** — no text/comment nodes get keys.
4. **Bidirectional** — after hydration, `element.node === domNode` and `domNode.ref === element`.

This means SSR HTML and client bundle must run **identical** DOMQL source. Any divergence (different shared libraries, stale extends chain, conditional branches that diverge) breaks hydration.

### What to avoid in code that may run during SSR

- `window` / `document` / `localStorage` access without `typeof window !== 'undefined'` guards. Brender stubs many browser APIs but not all.
- Async work in `onCreate`/`onRender` that mutates the DOM — SSR captures the synchronous output. Async mutations show up only after hydration. Use `prefetchPageData` to hydrate state from the DB at render time instead.
- Imports of browser-only packages (e.g. `mapbox-gl`, `leaflet`) at the module top level. Lazy-load via `el.call('requireOnDemand', 'mapbox-gl')` inside an event handler.
- Random / time-of-day output without a deterministic seed. Two renders must produce the same HTML.
- Reading from outside the project context (e.g. global `import.meta`, `process.env` at module top level — these resolve at bundle time).

### `prefetchPageData` for SSR with real data

```js
// In a brender-driven request
const stateUpdates = await prefetchPageData(data, '/blog')
// → walks page.fetch declarations, runs them via the project's db adapter,
//   returns { articles: [...], events: [...], ... } injected into page state
//   before render — components see real content during SSR.
```

Works only with adapters that have a Node-side runtime (Supabase, REST). `local` adapter is bundled with the project so it works in any environment.

### Diagnose a broken hydration

`hydrate.js` logs unlinked elements:

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
// { components, pages, designSystem, state, functions, methods, snippets, files, config, ... }
```

Options:
- `entry` — defaults to `context.js`; auto-generates one if missing
- `stringify: false` — keep functions as functions (only useful when bundling locally)
- `tmpDir` — custom temp dir for bundled output (default `.frank_tmp/`)
- `external` — additional packages to externalize

### `toFS(data, distDir, options?)` — JSON → FS

Writes a `symbols/` directory from a JSON object (auto-generates `index.js`, `context.js`, sub-indexes). Used by editors that import a server-side project into a workspace.

### Always run `frank` after editing FS-bundled projects

When editing any project whose published artifact is a frank-bundled JSON (`app.json` or the referenced data inside `symbols.json`), the compiled JSON becomes stale on every source edit. **Always run `frank` to recompile** after any edit (component, page, design system, config, file). Verify the compiled output before declaring done.

### Function stringification gotchas

- `stringifyFunctions` skips `__fn`, `__fnMeta`, `__handler`, `__meta` (internal markers). Don't name your own keys this.
- WeakMap-backed circular handling means circular refs become `'[Circular]'` strings in the output; if your function captures the parent element via closure, the closure isn't preserved — the function body is, evaluated against the runtime context.
- `(el) => el.call('myFn', el.state.x)` round-trips fine. `() => MY_CONSTANT` does NOT — the constant must live in `globalScope.js` or `dependencies.js` so the runtime can re-bind it.

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

Anything outside this list is invisible to frank. Don't put loadable code in `lib/`, `helpers/`, or other ad-hoc folders — either move it into one of the standard slots or import it from one of them.

---

## 10. Publishing — workflow + pitfalls

### One-shot: `smbls publish`

The full pipeline. Equivalent to `push` → `versions publish <id>` → `environments publish <env>` for each enabled environment.

```bash
smbls publish                   # default: push current project, mark new version as published, publish all envs
smbls publish --version <id>    # mark a specific version as published (skip push)
smbls publish --no-push         # use latest version on the server (skip push)
smbls publish --env staging     # publish only staging
smbls publish --env dev,staging # CSV form (also: --env dev --env staging)
smbls publish --mode latest     # override mode (default: prod-like envs = 'published', others = 'latest')
```

### Granular commands

```bash
smbls push                      # frank → JSON → upload, no environment publish
smbls versions list             # versions on server
smbls versions publish <id>     # mark a version as the project's "published" one
smbls environments list         # enabled environments
smbls environments publish <env># republish env to pick up the new version
```

### `smbls build`

Runs the bundler (parcel by default) and optionally pre-renders pages with brender:

```bash
smbls build                     # build SPA + brender pre-render
smbls build --no-brender        # SPA only
```

### `smbls deploy`

Targets a static host:

- `symbols` — push to Symbols platform
- `cloudflare` — Cloudflare Pages (auto-creates `wrangler.jsonc` with `assets.directory: './dist'` and SPA routing)
- `vercel` — auto-creates `vercel.json`
- `netlify` — auto-creates `netlify.toml`
- `github-pages` — pushes to `gh-pages` branch

### Pre-publish checklist

1. **Run frank** — recompile JSON if the project's published artifact is a frank-bundled JSON.
2. **Audit components** — `mcp__symbols-mcp__audit_component` on changed components.
3. **Verify the design system tokens are present** — every color/spacing/typography token used in components must be defined in `designSystem/`. Missing tokens cause silent visual fallbacks in production.
4. **Check `dependencies.js`** — any package referenced from project code must be in `dependencies.js` so mermaid can resolve it via importmap. Missing entries fail at runtime in deployed channels.
5. **`config.js` flags** — `useReset`, `useVariable`, `useFontImport`, `useIconSprite`, `useSvgSprite`, `useDefaultConfig`, `useDocumentTheme` should all be `true` for normal projects. Mermaid's bundle script defaults them to `true` if missing, but explicit beats implicit.
6. **No `db.createClient` in published JSON** — frank stringification preserves `createClient` as a function reference, but mermaid's bundle script strips it (`delete context.db.createClient`). Re-creation happens runtime-side via the adapter. Don't fight this.
7. **No browser-only top-level code in modules** — see §8 SSR rules above. If you import a leaflet/mapbox/etc. package at the top of a component file, brender will crash and fall back to client-render. Lazy-load instead.
8. **Test with `channel=production`** — `smbls deploy --channel production` (or `mermaid` with `BRENDER=true`) catches SSR regressions early.

### Common publish-time failures

| Symptom | Cause | Fix |
|---|---|---|
| Page renders blank in deployed env | Brender failed silently → client render path expected hydration markers | Run `smbls build` locally with `BRENDER=true`; check console for the brender warning |
| Theme flashes wrong color on first paint | Project-side `setAttribute('data-theme', …)` racing `resolveAndApplyTheme`, OR `useDocumentTheme: false` skipping the design-system's document background/color application | Remove any project-side theme setAttribute (framework owns it via `resolveAndApplyTheme`). Keep `useDocumentTheme: true` so the design system's `document` block applies on `<body>` |
| `db.createClient is not a function` at runtime in deployed env | Project shipped a `createClient` reference in JSON. Bundle strips it (`mermaid/src/bundle.js:65`); supabase adapter's dynamic-import fallback (`adapters/supabase.js:16-19`) needs `@supabase/supabase-js` to be importable | Add `@supabase/supabase-js` to `symbols/dependencies.js` so the runtime importmap can resolve it. Stop passing `createClient` from `config.js`; let the adapter fetch it |
| Routes 404 in deployed env | `pages/index.js` default export not in expected `{ '/': X, '/about': Y }` shape | Frank only picks up the default export of `pages/index.js`. Named exports must be re-exported there |
| Font flicker / FOUT | `useFontImport: false` or design system `font` block missing `fontFace` | Set `useFontImport: true` and define `fontFace` for every font family |
| CSS vars missing in iframe | Multi-app secondary not getting its own document on `config.document` | Use the framework's `prepareDesignSystem` flow — pass `context.document` (and `themeRoot`) to the iframe app's `create()` call. Don't manually inject CSS into the iframe |
| `[smbls/router] no content matched for path /` warning | Router fired before pages were registered | Verify `context.pages` exists (frank picks it up from `pages/index.js`'s default export). Check `context.router !== false` |
| Parcel dev server crash: `ENOENT: no such file or directory, open '.../.parcel-cache/<hash>'` | Race in Parcel's dev cache write/read after a fresh build | Clear `.parcel-cache` AND `dist` for the project, restart. Not a code bug. For framework-level changes, run the monorepo-wide nuke: `find <your-monorepo-root> -name ".parcel-cache" -type d -exec rm -rf {} +` |
| Text leaking into the page from an inline `childExtends` object | css-in-props edge case with inline-object `childExtends` | Extract the inline `childExtends` to a named component referenced by string |
| `backdropFilter` value bleeds into text content | css-in-props bug on this specific property | Wrap in a `style: { backdropFilter: '...' }` block instead of a top-level prop |
| External package `Cannot find module` at runtime | Listed in `package.json` but not in `symbols/dependencies.js` (or vice-versa) | Both lists are required. `package.json` is for `npm install`; `symbols/dependencies.js` is what the Symbols runtime resolves via importmap |
| Atomic class resolves to empty body in production (`._c-neutral900 { }`) but works locally | The design-system token is missing from the published bundle (color/spacing/font defined in `designSystem/` but not present in the version that mermaid serves). The atomic-class generator runs against whatever tokens are present and silently emits an empty rule for missing ones | Re-run `frank` to recompile the published JSON, then republish. Diagnose via Chrome devtools: walk `document.styleSheets`, grep for the class name, inspect the rule body. Empty body confirms the token is missing on the server side, not a CSS-in-props bug |
| Branded base color (`color.black: '#10241A'`) bleeds into dark-mode page background | `theme.document` falls back to bare `'black'` / `'white'` / `'neutral'` tokens, which resolve to the brand's tinted versions instead of stepped neutrals | Always pair branded core tokens with explicit `theme.document.@dark` / `@light` blocks in `designSystem/theme.js`. Use the modifier system (`neutral+45`, `neutral-45`, `neutral=50`) to step away from the tinted base; reserve bare `black` / `white` / `neutral` for places where the brand tint is intentional. See `DESIGN_SYSTEM.md` "Branded core tokens" |

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
| `fastclick` | Modern mobile browsers don't have the 300ms tap delay | Just delete it (or move to `onRender` with `__initialized` guard if you really want to keep it) |
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
// symbols.json (root)
{ "key": "<project-name>.symbo.ls", "dir": "symbols", "bundler": "parcel" }
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
| Fetch | `plugins/fetch/README.md` |
| Polyglot (i18n) | `plugins/polyglot/README.md` |
| Helmet (SEO) | `plugins/helmet/README.md` |
| Brender (SSR) | `plugins/brender/README.md` |
| Frank (JSON ↔ FS) | `plugins/frank/README.md` |
| Router | `plugins/router/README.md` + `packages/smbls/src/router.js` |
| CLI | `packages/cli/bin/*.js` |
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
