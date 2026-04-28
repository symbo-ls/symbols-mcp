# Modern smbls Stack — `fetch` / `polyglot` / `helmet` / `router` / `scratch` / `analyze`

Every non-trivial Symbols app uses this coherent set of plugins. Each plugin replaces an entire class of imperative one-offs with a declarative prop or function call. **NEVER reimplement what these plugins already do** — that's a "no hacks, no workarounds" violation.

---

## The Stack at a Glance

| Plugin | Responsibility | Key surface | Strict rule |
| -- | -- | -- | -- |
| `@symbo.ls/fetch` | Declarative data fetching, caching, dedup, retry, refetch-on-focus, pagination | `db: { adapter, ... }` config + `fetch:` prop on elements | Rule 47 |
| `@symbo.ls/polyglot` | Translations, language switching, fetch integration | `'{{ key | polyglot }}'` template + `el.call('polyglot', 'key')` + `el.call('setLang', 'ka')` | Rule 48 |
| `@symbo.ls/helmet` | SEO metadata at runtime AND in brender SSR | `metadata: {…}` on app/page/component | Rule 49 |
| `@symbo.ls/router` | SPA routing, guards, dynamic params, query parsing, scroll mgmt | `el.router(path, el.getRoot())` + `routes:` map | Rule 42 |
| `@symbo.ls/scratch` (theme runtime) | Design system runtime, `changeGlobalTheme()` | `changeGlobalTheme(name, targetConfig?)` (import from `smbls`) + `context.globalTheme` | Rule 50 |
| `@symbo.ls/brender` | SSR / SSG static rendering with prefetch and hydration | `smbls brender` CLI + `renderPage(data, route, opts)` | (helmet + fetch are prefetched here) |
| `@symbo.ls/analyze` | Runtime audit logger — errors, warnings, browser events, network, session replay | `analyze: true|{...}` on `create()` + `context.analyze.query()` | (errors/warnings on by default; browser/network opt-in) |

---

## Wiring the stack

```js
// dependencies.js
import { fetchPlugin } from '@symbo.ls/fetch'
import { polyglotPlugin } from '@symbo.ls/polyglot'
import { polyglotFunctions } from '@symbo.ls/polyglot/functions'
import { routerPlugin } from '@symbo.ls/router'
import { helmetPlugin } from '@symbo.ls/helmet'

// app.js
import deps from './dependencies.js'
import context from './context.js'
import create from 'smbls'

create(app, {
  ...context,
  plugins:   [routerPlugin, fetchPlugin, polyglotPlugin, helmetPlugin],
  functions: { ...context.functions, ...polyglotFunctions },
  polyglot:  {
    defaultLang: 'en',
    languages:   ['en', 'ka'],
    translations: { en: { … }, ka: { … } }
  },
  db: { adapter: 'supabase', url: 'https://xxx.supabase.co', key: 'sb_publishable_…' }
})
```

---

## `@symbo.ls/fetch` — declarative data

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

### Use

```js
// minimal — fetch & store in state.articles on element create
{ state: 'articles', fetch: true }

// with options
{ state: 'articles',
  fetch: { params: { status: 'published' }, cache: '5m', limit: 20,
           order: { by: 'created_at', asc: false } } }

// RPC + transform
{ state: { items: [], featured: null },
  fetch: { method: 'rpc', from: 'get_content_rows', params: { p_table: 'videos' },
           transform: (data) => ({ featured: data.find(v => v.is_featured),
                                   items: data.filter(v => !v.is_featured) }) } }

// parallel
{ state: { articles: [], events: [] },
  fetch: [
    { from: 'articles', as: 'articles', cache: '5m' },
    { from: 'events',   as: 'events',   cache: '5m' }
  ] }

// triggered by user action
{ tag: 'form', fetch: { method: 'insert', from: 'contacts', on: 'submit' } }
{ fetch: { method: 'delete', from: 'items',
          params: (el) => ({ id: el.state.itemId }), on: 'click' } }

// pagination
{ state: { items: [], page: 1 },
  fetch: { from: 'articles', page: (el, s) => s.page,
           pageSize: 20, keepPreviousData: true } }

// polling
{ fetch: { from: 'notifications', refetchInterval: '30s' } }

// dynamic enabled
{ fetch: { from: 'profile', enabled: (el, s) => !!s.userId } }

// optimistic
{ fetch: { method: 'update', from: 'todos', on: 'click', optimistic: (curr, params) => ({ ...curr, done: true }) } }

// initial / placeholder
{ fetch: { from: 'settings', initialData: { theme: 'auto' } } }
{ fetch: { from: 'articles', placeholderData: [] } }
```

### Cache semantics

```js
cache: true                                    // staleTime 1m, gcTime 5m (default)
cache: false                                   // no caching
cache: '5m'                                    // 5min stale
cache: { stale: '1m', gc: '10m' }
cache: { staleTime: '30s', gcTime: '1h', key: 'custom-key' }
```

- Stale-while-revalidate: stale data served immediately, background refetch swaps it.
- Garbage collection: unused entries cleaned after `gcTime`.
- Deduplication: identical concurrent queries share one network request.
- Refetch on window focus: enabled by default. Disable with `refetchOnWindowFocus: false`.

### ❌ Forbidden alternatives

```js
// raw window.fetch in a component
onRender: async (el, s) => {
  const r = await fetch('/api/articles')
  s.update({ items: await r.json() })
}

// axios / SWR / TanStack Query / fetch wrappers in a component
import axios from 'axios'
onClick: async (e, el, s) => {
  const r = await axios.get('/api/articles')
  s.update({ items: r.data })
}
```

If you genuinely need imperative control (a multi-step flow with conditionals), wrap it in a `functions/` file and call via `el.call('loadX')` — but the declarative `fetch:` prop is the default.

---

## `@symbo.ls/polyglot` — translations

### Setup

```js
// context.js
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
```

### Use

```js
// mustache template — resolved by replaceLiteralsWithObjectFields, reactive on lang change
{ text: '{{ hello | polyglot }}' }
{ placeholder: '{{ searchDestinations | polyglot }}' }

// el.call('polyglot', key) — imperative lookup (NOT reactive — captures value at evaluation time)
{ text: (el) => el.call('polyglot', 'hello') }

// per-language state field (CMS title_en / title_ka)
{ text: '{{ title_ | getLocalStateLang }}' }

// composed string with state (reactive on s.user.name; the polyglot call inside is captured)
{ text: (el, s) => `${el.call('polyglot', 'welcome')}, ${s.user.name}` }

// NOTE: there is NO `t` or `tr` function — use `polyglot` for both reactive and non-reactive.
// Reactivity comes from the `{{ key | polyglot }}` template-literal mechanism inside the text-effect createEffect.

// language switcher
{ extends: 'Button', text: 'KA',
  onClick: (e, el) => el.call('setLang', 'ka') }

// current lang
{ text: (el) => el.call('getLang') }

// upsert from CMS admin
upsertTranslation: (e, el) => el.call('upsertTranslation', 'ui.nav.home', 'en', 'Home')
```

### Fetch integration

When `state.root.lang` changes (via `setLang`), `@symbo.ls/fetch` automatically adds an `Accept-Language` header to every request. The header is the **only** injection — fetch does NOT add a `lang` query parameter or RPC argument (verified at `plugins/fetch/index.js:537-540`). If your backend expects `lang` in `params`, set it explicitly:

```js
fetch: { from: 'articles', params: (el, s) => ({ lang: s.root.lang, status: 'published' }) }
```

### ❌ Forbidden alternatives

```js
// hardcoded English
{ text: 'Hello' }
{ placeholder: 'Search destinations' }

// manual ternary on lang
{ text: (el, s) => s.root.lang === 'ka' ? 'გამარჯობა' : 'Hello' }

// react-i18next / formatjs / i18next imports in a component
import { t } from 'react-i18next'
```

---

## `@symbo.ls/helmet` — SEO metadata

Define a declarative `metadata` object on any app, page, or component. Works at runtime (updates DOM `<head>`) and during SSR (generates HTML via `@symbo.ls/brender`).

> **Strict (Rule 49):** all metadata MUST go through `@symbo.ls/helmet`. NEVER write `document.title = …` or inject `<head>` tags directly from project code. NEVER mutate `<title>` from `onRender`. The framework owns `<head>`.

### Supported metadata types

| Prefix / Type | Generates | Example Key |
|---|---|---|
| _(none)_ | `<title>`, `<meta name>`, `<link rel>` | `title`, `description`, `canonical` |
| `og:` | `<meta property="og:...">` | `og:title`, `og:image` |
| `twitter:` | `<meta name="twitter:...">` | `twitter:card`, `twitter:site` |
| `article:` | `<meta property="article:...">` | `article:published_time` |
| `product:` | `<meta property="product:...">` | `product:price:amount` |
| `DC:` | `<meta name="DC....">` | `DC:title`, `DC:creator` |
| `itemprop:` | `<meta itemprop="...">` | `itemprop:name` |
| `http-equiv:` | `<meta http-equiv="...">` | `http-equiv:cache-control` |
| `apple:` | `<meta name="apple:...">` | `apple:mobile-web-app-capable` |
| `msapplication:` | `<meta name="msapplication:...">` | `msapplication:TileColor` |
| `alternate` | `<link rel="alternate" ...>` | `alternate: [{ hreflang, href }]` |
| `customMeta` | `<meta ...attrs>` | `customMeta: { name, content }` |

**Behaviors:**
- Array values expand into multiple tags
- Function values receive `(el, s)` for dynamic metadata
- Merges metadata from global, app-level, and page-level (page wins)

### App-level defaults

```js
// app.js
export default {
  metadata: {
    title:       'My App',
    description: 'Built with Symbols',
    'og:image':  '/social.png',
    'twitter:card': 'summary_large_image'
  }
}
```

### Page-level (overrides app-level)

```js
// pages/about.js
export const about = {
  metadata: {
    title:       'About Us',
    description: 'Learn more about us'
  }
}
```

### Dynamic — function-as-object

```js
export const product = {
  metadata: (el, s) => ({
    title:       s.product.name,
    description: s.product.description,
    'og:image':  s.product.image
  })
}
```

### Dynamic — per-property functions

```js
export const profile = {
  metadata: {
    title:       (el, s) => `${s.user.name} — My App`,
    description: (el, s) => s.user.bio,
    'og:image':  '/default-avatar.png'
  }
}
```

### Complete example (all metadata families)

```js
export default {
  metadata: {
    // Basic
    title: 'My Awesome Website',
    description: 'This is an awesome website with great content',
    keywords: 'awesome, website, content',
    author: 'John Doe',
    robots: 'index, follow',
    canonical: 'https://example.com/page',

    // Open Graph
    'og:title': 'My Awesome Website',
    'og:description': 'This is an awesome website with great content',
    'og:type': 'website',
    'og:url': 'https://example.com',
    'og:image': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg'],
    'og:site_name': 'Example Site',
    'og:locale': 'en_US',

    // Twitter Cards
    'twitter:card': 'summary_large_image',
    'twitter:site': '@example',
    'twitter:creator': '@johndoe',
    'twitter:title': 'My Awesome Website',
    'twitter:description': 'This is an awesome website with great content',
    'twitter:image': 'https://example.com/twitter-image.jpg',

    // Article metadata
    'article:published_time': '2023-01-01T00:00:00Z',
    'article:modified_time': '2023-01-02T00:00:00Z',
    'article:author': ['John Doe', 'Jane Smith'],
    'article:section': 'Technology',
    'article:tag': ['web', 'development', 'javascript'],

    // Product metadata
    'product:price:amount': '29.99',
    'product:price:currency': 'USD',
    'product:availability': 'in stock',
    'product:condition': 'new',
    'product:brand': 'Example Brand',
    'product:category': 'Electronics',

    // Dublin Core
    'DC:title': 'My Awesome Website',
    'DC:creator': ['John Doe', 'Jane Smith'],
    'DC:subject': ['web development', 'javascript'],
    'DC:description': 'This is an awesome website with great content',
    'DC:publisher': 'Example Publisher',
    'DC:date': '2023-01-01',
    'DC:type': 'Text',
    'DC:language': 'en',

    // Mobile app metadata
    'apple:mobile-web-app-capable': 'yes',
    'apple:mobile-web-app-status-bar-style': 'black-translucent',
    'apple:mobile-web-app-title': 'My App',
    'msapplication:TileColor': '#ffffff',
    'msapplication:TileImage': '/mstile-144x144.png',
    'msapplication:task': [
      'name=Task 1;action-uri=/task1;icon-uri=/task1.ico',
      'name=Task 2;action-uri=/task2;icon-uri=/task2.ico'
    ],

    // HTTP-Equiv directives
    'http-equiv:cache-control': 'no-cache',
    'http-equiv:expires': 'Tue, 01 Jan 1980 1:00:00 GMT',

    // Structured data & verification
    'itemprop:name': 'My Awesome Website',
    'itemprop:description': 'This is an awesome website with great content',
    'google-site-verification': 'abc123def456',
    'fb:app_id': '123456789',
    'geo.region': 'US-NY',
    'geo.placename': 'New York City',
    'geo.position': '40.7128;-74.0060',

    // Alternate language links
    alternate: [
      { hreflang: 'es', href: 'https://example.com/es/' },
      { hreflang: 'fr', href: 'https://example.com/fr/' }
    ],

    // Custom metadata
    customMeta: {
      name: 'custom-property',
      content: 'custom-value',
      'data-custom': 'additional-data'
    }
  }
}
```

### Merge priority

Higher priority wins. Later levels override earlier ones.

| Priority | Source | Scope |
|---|---|---|
| 1 (lowest) | `data.integrations.seo` | Global SEO settings |
| 2 | `data.app.metadata` | App-level defaults |
| 3 (highest) | `page.metadata` | Page-level overrides |

**Fallback chain for `title`:** `page.metadata.title` → `page.state.title` → `data.name`

Helmet works identically at runtime AND in `smbls brender` SSR.

### ❌ Forbidden alternatives

```js
// document.title writes
onRender: (el, s) => { document.title = s.product.name }

// manual <head> injection
onInit: (el) => {
  const meta = document.createElement('meta')
  meta.setAttribute('name', 'description')
  meta.setAttribute('content', 'Search results')
  document.head.appendChild(meta)
}

// next/head, react-helmet imports
import Head from 'next/head'
```

---

## `@symbo.ls/router` — SPA routing

### Routes map

```js
// pages/index.js — only file allowed to import siblings
import { home }      from './home.js'
import { about }     from './about.js'
import { userPage }  from './user-page.js'
import { notFound }  from './not-found.js'

export default {
  '/':           home,
  '/about':      about,
  '/users/:id':  userPage,
  '/*':          notFound
}
```

Dynamic params (`:id`) populate `state.params`. Query strings populate `state.query`.

### Programmatic navigation

`event.preventDefault()` BEFORE `el.router(...)`:

```js
onClick: (e, el, s) => {
  e.preventDefault()
  el.router(`/users/${s.userId}`, el.getRoot(), {}, {
    scrollToTop: true,
    scrollToOptions: { behavior: 'instant' }
  })
}
```

### Link component

```js
NavItem: {
  extends: 'Link',
  text: '{{ about | polyglot }}',
  href: '/about'
}

ProfileLink: {
  extends: 'Link',
  href: (el, s) => `/users/${s.id}`,
  text: '{{ viewProfile | polyglot }}'
}
```

### Guards / middleware

```js
const authGuard = ({ element }) =>
  element.state.root.isLoggedIn ? true : '/login'

const adminGuard = ({ params }) =>
  params.section === 'admin' ? false : true

el.router('/dashboard', el.getRoot(), {}, { guards: [authGuard, adminGuard] })
```

Guards return: `true` to allow, `false` to block, or a string to redirect.

### Custom router element (persistent layouts)

```js
// config.js
export default {
  router: { customRouterElement: 'Folder.Content' }
}
```

The `/` page defines the persistent layout shell. Sub-pages render inside the target element without destroying the shell.

### ❌ Forbidden alternatives

```js
window.location.href = '/x'
window.location.assign('/x')
window.location.replace('/x')
history.pushState({}, '', '/x')
```

---

## `@symbo.ls/scratch` theme runtime — `changeGlobalTheme(theme, targetConfig?)`

Theme is a context-level concern. The framework owns `data-theme`, OS preference detection, and CSS var refresh. Import `changeGlobalTheme` from `smbls` (re-exported from scratch).

`changeGlobalTheme(theme, targetConfig?)`:
- Operates on `targetConfig` if provided, otherwise the active CONFIG (from the push stack or singleton).
- Forced theme: writes `data-theme="<value>"` to `CONFIG.themeRoot` and mirrors to `root.style.colorScheme`.
- `'auto'`: reads current `prefers-color-scheme`, writes the resolved `'dark'`/`'light'` to `data-theme`, registers a one-time OS-preference listener so future toggles flip the attribute live.
- Clears every theme-prefixed CSS-var entry and re-applies under the new theme.
- Does **NOT** persist to localStorage — that's the project's responsibility.

### Switching themes (registered project function — import-safe)

```js
// functions/switchTheme.js
import { changeGlobalTheme } from 'smbls'

export function switchTheme () {
  const next = this.context.globalTheme === 'dark' ? 'light' : 'dark'
  changeGlobalTheme(next, this.context.designSystem)            // 2nd arg = targetConfig (cross-app)
  try { (this.context.window || window).localStorage.setItem('my-app-theme', next) } catch (e) {}
}

// components/ThemeToggle.js
ThemeToggle: {
  extends: 'Button',
  text: '{{ toggleTheme | polyglot }}',
  onClick: (e, el) => el.call('switchTheme')
}

// follow OS
ThemeAuto: {
  extends: 'Button',
  text: 'Auto',
  onClick: (e, el) => el.call('switchTheme', 'auto')   // adapt switchTheme to accept an explicit value
}

// cross-app (editor toolbar switches embedded project's theme)
import { changeGlobalTheme } from 'smbls'
changeGlobalTheme('dark', projectApp.context.designSystem)
```

### Theme-dependent UI — pure CSS

For elements that depend on the active theme, prefer pure-CSS toggles via `@dark` / `@light` blocks. CSS updates atomically when `data-theme` flips — no JS plumbing.

```js
LightLogo: { extends: 'Icon', icon: 'logoLight', '@dark': { display: 'none' } }
DarkLogo:  { extends: 'Icon', icon: 'logoDark',
             display: 'none', '@dark': { display: 'inline-flex' } }
```

### Multi-DS isolation

For multiple design systems on one page (canvas editor + iframe project), pass `options.themeRoot` per `create()`:

```js
create(canvasApp, { themeRoot: canvasShellNode, designSystem: canvasDS })
create(projectApp, { themeRoot: previewIframeRoot, designSystem: projectDS })
```

Each design system attaches its `data-theme` to its own root.

### ❌ Forbidden alternatives

```js
// project code writing data-theme
document.documentElement.setAttribute('data-theme', 'dark')

// project code reading prefers-color-scheme
if (matchMedia('(prefers-color-scheme: dark)').matches) { ... }

// storing globalTheme in root state
state: { globalTheme: 'dark' }

// manual CSS var writes
document.documentElement.style.setProperty('--bg', '#000')
```

---

## `@symbo.ls/brender` — SSR / SSG

Pre-render Symbols apps to static HTML. Brender uses linkedom (a virtual DOM) to run the same DOMQL component tree server-side, producing HTML with `data-br` hydration keys for client-side reconnection without re-rendering.

> Brender pairs with the rest of the modern smbls stack. `@symbo.ls/helmet` metadata is rendered into `<head>`, `@symbo.ls/fetch` declarative `fetch:` is prefetched server-side, and `@symbo.ls/polyglot` translations are resolved per route at render time.

### CLI

```bash
smbls brender                  # render all static routes
smbls brender --out-dir build  # custom output directory
smbls brender --no-prefetch    # skip SSR data prefetching
smbls brender --no-isr         # skip client SPA bundle
smbls brender --watch          # watch & re-render
```

Output goes to `dist-brender/` by default (configurable via `brenderDistDir` in `symbols.json`), separate from the SPA's `dist/` folder.

### Programmatic

```js
import { renderPage, loadProject } from '@symbo.ls/brender'

const data = await loadProject('/path/to/project')
const result = await renderPage(data, '/about', { prefetch: true })

// result.html       -> complete <!DOCTYPE html> page
// result.route      -> '/about'
// result.brKeyCount -> number of hydration keys
```

### How it works

**Render phase (server):**
1. Create virtual DOM with linkedom
2. Run DOMQL `create()` against it — the full component tree resolves
3. Stamp `data-br="br-N"` on every element node (sequential, deterministic)
4. Return HTML string, registry, and element tree

**Hydrate phase (browser):**
1. Pre-rendered HTML already in DOM — instant page display
2. DOMQL re-creates element tree from source definitions
3. `hydrate()` matches `data-br` keys between DOMQL tree and real DOM
4. Bidirectional links: `element.node = domNode` and `domNode.ref = element`
5. Reactive updates, event handlers, and state changes work as if client-rendered

### Key APIs

| Function | Purpose |
|---|---|
| `renderElement(def, opts?)` | Render a single component to HTML |
| `render(data, opts?)` | Render a full project (routing, state, designSystem) |
| `renderPage(data, route, opts?)` | Complete HTML page with metadata, CSS, fonts |
| `prefetchPageData(data, route)` | SSR data prefetching via DB adapter |
| `hydrate(element, opts?)` | Client-side: reconnect DOMQL tree to DOM |
| `loadProject(path)` | Import a `symbols/` directory structure |
| `generateSitemap(data)` | Generate sitemap.xml from routes |

### Features

| Feature | Details |
|---|---|
| Metadata | Title, description, Open Graph, Twitter cards from declarative `metadata` objects |
| Emotion CSS | Full CSS extraction including emotion-generated rules, CSS variables, reset, font imports |
| Theme support | Generates `prefers-color-scheme` media queries and `[data-theme]` selectors (no JS needed) |
| Data prefetching | Executes declarative `fetch` definitions during SSR via DB adapter (Supabase) |
| ISR | Optional client bundle for hydration + SPA navigation after initial static load |
| Sitemap | Auto-generated `sitemap.xml` from route definitions |

### Configuration

In `symbols.json`:

```json
{
  "brender": true,
  "brenderDistDir": "dist-brender"
}
```

### What brender prefetches

When `--prefetch` is enabled (default), brender executes declarative `fetch:` definitions during SSR via the configured DB adapter. The HTML ships with data already in state — no client-side waterfall.

Helmet metadata is rendered into `<head>` server-side.

Param routes (`/blog/:id`) are skipped during static generation — they require runtime data.

---

## `@symbo.ls/analyze` — runtime audit logger

Errors, warnings, lifecycle traces, browser events, network calls, and session replay. Designed for smbls's declarative model so the runtime is the source of truth.

Auto-registered when `analyze: true|{...}` is passed to `create()`. **Errors and warnings are on by default**; everything else is opt-in.

```js
import { create } from 'smbls'

create(App, {
  analyze: true   // → errors + warnings, redact → enrich → summarize → [console, memory]
})
```

### What gets captured

| Category | Default | Notes |
|---|---|---|
| `errors` | **on** | `window.onerror`, `unhandledrejection`, lifecycle handler throws, `el.error()` |
| `warnings` | **on** | `el.warn()` and framework warnings |
| `pointer` | off | clicks, throttled pointermove, contextmenu |
| `keyboard` | off | key codes + modifiers, never values |
| `forms` | off | input/change/submit; values masked by default |
| `scroll` | off | throttled |
| `viewport` | off | resize, orientationchange, visibilitychange + initial snapshot |
| `network` | off | fetch + XHR + chained smbls fetch events (cache key, mode, durationMs) |
| `performance` | off | LCP, CLS, INP, longtasks, paint |
| `navigation` | off | route changes via `renderRouter` |
| `console` | off | `console.{log,warn,error,debug}` proxy |
| `lifecycle` / `state` / `updates` | debug only | smbls internals — high volume |

### Hydration gate

The plugin sits in `context.plugins` from creation but is **dormant** until `app.onCreate` fires (`packages/smbls/src/index.js`). At that point `context.analyze.activate(context)` runs:

1. Drains the pre-ready buffer (only error events are buffered before activation)
2. Attaches browser-event listeners (per the enabled categories)
3. Wraps `window.fetch` and XHR (when network capture is on)

Pre-hydration errors still surface. Pre-hydration `info`/`debug` events are dropped.

### Network capture chains with `@symbo.ls/fetch`

`runFetch` and `runMutation` in `plugins/fetch/index.js` call `context.analyze.emitNetwork({ phase, mode, from, method, cacheKey, durationMs, ... })` at start/success/error. The call is a no-op when analyze isn't installed, so projects without analyze pay nothing.

When analyze is installed AND `network: true` is set, the events are smbls-aware (they include the cache key, mode, and lang suffix). `window.fetch` and XHR are also wrapped to catch non-smbls traffic.

### Session replay (smbls-native)

Conventional session replay (rrweb, FullStory) records DOM mutations. Because smbls owns the rendering pipeline, replay only needs:

```
replay payload  =  initial state snapshot
                +  input event log (clicks, keys, forms, viewport)
                +  state mutations  (the stateUpdate hook)
```

Restart the app with the snapshot, replay events in order, DOM regenerates itself. Tiny payload, perfect fidelity.

```js
analyze: {
  level: 'info',
  capture: { replay: true },
  sinks: [{ type: 'memory', max: 5000 }]
}
// later: context.analyze.replay() → { initialSnapshot, events }
```

### Transformer pipeline + sinks

```
hook fires → build event → transformers[] → sinks[]
```

Built-in transformers (string names):
- `redact` — always-first PII scrubber. Disable with `redact: false`.
- `enrich` — adds session, route, viewport, app id (default).
- `summarize` — replaces raw element refs and Error instances with safe slices (default).
- `dedupe`, `sample` — opt-in.

Built-in sinks:
- `console` — pretty + color. Saves originals so console proxy doesn't recurse.
- `memory` — ring buffer queryable via `context.analyze.query({ level, type, sinceMs })`.
- `beacon` — batched POST + `sendBeacon` fallback on `pagehide`.

### Debug mode

```js
analyze: { debug: true }                 // config
// or URL param:
//   ?analyze=debug   → enables lifecycle + state + updates + console capture
//   ?analyze=off     → disables analyze entirely
// or runtime:
context.analyze.setLevel('debug')
context.analyze.setCapture('updates', true)
```

### Element-core integration (load-bearing)

Two small framework changes:

1. `packages/element/src/create.js` — lifecycle handler throws now go through `triggerLifecycle('error', element, { hook, error })` instead of bare `console.error`. The framework still falls back to `console.error` when no plugin handled the hook.
2. `packages/element/src/methods.js` — `el.warn()` and `el.error()` emit through `context.analyze` first, then fall through to the original env-gated console.warn / throw.

`packages/utils/function.js` — `runPluginHook` now returns `true` when at least one plugin handled the hook.

### Element targeting via `data-key`

Click/key/form events reference the DOMQL key path (e.g. `App > Sidebar > MenuItem_3`) by walking up `data-key` DOM attributes (set by element/create.js for every keyed element). Stable across renders. Falls back to a CSS selector when the node isn't owned by a DOMQL tree.

### Privacy defaults

- `redact` always runs first; cannot be reordered.
- `<input type="password">`, `<input type="hidden">`, and fields matching `/email|token|secret|ssn|card|cvv|pin|otp/i` are never recorded.
- Form values masked by default. Opt in per-field with `data-analyze="track"`. Never track with `data-analyze="skip"`.
- Mask strategies: `'mask'` (`***`), `'hash'` (`#<hex>`), `'redact'` (drop the field entirely).

---

## Strict no-hacks rule

If a framework feature already exists for a problem, you MUST use it:

- Need to fetch data? → declarative `fetch:` (NOT `window.fetch`)
- Need to translate text? → polyglot (NOT hardcoded strings)
- Need to set page title? → helmet (NOT `document.title`)
- Need to navigate? → `el.router()` (NOT `window.location`)
- Need to switch theme? → `changeGlobalTheme()` (NOT `setAttribute('data-theme')`)
- Need to render server-side? → brender (NOT custom SSR)
- Need observability? → analyze (NOT `try/catch` + `console.error` everywhere)

If the framework feature has a gap, **fix the framework** — don't paper over it in the project (per CLAUDE.md "no hacks, no workarounds").
