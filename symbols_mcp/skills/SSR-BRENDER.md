# Server-Side Rendering with Brender

Symbols apps can be pre-rendered to static HTML using `@symbo.ls/brender`. The same DOMQL component tree that runs in the browser is rendered on the server via a virtual DOM (linkedom), producing HTML with `data-br` keys that enable client-side hydration without re-rendering.

---

## Quick Start

### CLI

```bash
# Render all static routes
smbls brender

# Custom output directory
smbls brender --out-dir build

# With SSR data prefetching
smbls brender

# Without prefetch or ISR client bundle
smbls brender --no-prefetch --no-isr

# Watch mode
smbls brender --watch
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

---

## How It Works

### Render Phase (Server)

1. Creates a virtual DOM with linkedom
2. Runs DOMQL `create()` against the virtual DOM — full component tree resolves
3. Stamps `data-br="br-N"` on every element node (sequential, deterministic)
4. Returns HTML string, registry, and element tree

### Hydrate Phase (Browser)

1. Pre-rendered HTML is already in the DOM — instant page display
2. DOMQL re-creates the element tree from source definitions
3. `hydrate()` matches `data-br` keys between DOMQL tree and real DOM
4. Bidirectional links: `element.node = domNode` and `domNode.ref = element`
5. Reactive updates, event handlers, and state changes work as if client-rendered

---

## Key APIs

| Function | Purpose |
|----------|---------|
| `renderElement(def, opts?)` | Render a single component to HTML |
| `render(data, opts?)` | Render a full project (routing, state, designSystem) |
| `renderPage(data, route, opts?)` | Complete HTML page with metadata, CSS, fonts |
| `prefetchPageData(data, route)` | SSR data prefetching via DB adapter |
| `hydrate(element, opts?)` | Client-side: reconnect DOMQL tree to DOM |
| `loadProject(path)` | Import a `symbols/` directory structure |
| `generateSitemap(data)` | Generate sitemap.xml from routes |

---

## Features

- **Metadata**: Title, description, Open Graph, Twitter cards — generated from declarative `metadata` objects on app/pages
- **Emotion CSS**: Full CSS extraction including emotion-generated rules, CSS variables, reset, and font imports
- **Theme support**: Generates `prefers-color-scheme` media queries and `[data-theme]` selectors for theme switching without JS
- **Data prefetching**: Executes declarative `fetch` definitions during SSR via DB adapter (Supabase)
- **ISR**: Optional client bundle for hydration + SPA navigation after initial static load
- **Sitemap**: Auto-generated `sitemap.xml` from route definitions

---

## Configuration

In `symbols.json`:

```json
{
  "brender": true,
  "brenderDistDir": "dist-brender"
}
```

Param routes (e.g. `/blog/:id`) are automatically skipped during static generation — they require runtime data.
