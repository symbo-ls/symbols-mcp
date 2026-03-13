# Server-Side Rendering with Brender

Pre-render Symbols apps to static HTML using `@symbo.ls/brender`. Uses linkedom (virtual DOM) to run the same DOMQL component tree server-side, producing HTML with `data-br` hydration keys for client-side reconnection without re-rendering.

---

## Quick Start — CLI

```bash
# Render all static routes
smbls brender

# Custom output directory
smbls brender --out-dir build

# Without prefetch or ISR client bundle
smbls brender --no-prefetch --no-isr

# Watch mode
smbls brender --watch
```

Output goes to `dist-brender/` by default (configurable via `brenderDistDir` in `symbols.json`), separate from the SPA's `dist/` folder.

---

## Quick Start — Programmatic

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

1. Create virtual DOM with linkedom
2. Run DOMQL `create()` against it — full component tree resolves
3. Stamp `data-br="br-N"` on every element node (sequential, deterministic)
4. Return HTML string, registry, and element tree

### Hydrate Phase (Browser)

1. Pre-rendered HTML already in DOM — instant page display
2. DOMQL re-creates element tree from source definitions
3. `hydrate()` matches `data-br` keys between DOMQL tree and real DOM
4. Bidirectional links: `element.node = domNode` and `domNode.ref = element`
5. Reactive updates, event handlers, and state changes work as if client-rendered

---

## Key APIs

| Function | Purpose |
|---|---|
| `renderElement(def, opts?)` | Render a single component to HTML |
| `render(data, opts?)` | Render a full project (routing, state, designSystem) |
| `renderPage(data, route, opts?)` | Complete HTML page with metadata, CSS, fonts |
| `prefetchPageData(data, route)` | SSR data prefetching via DB adapter |
| `hydrate(element, opts?)` | Client-side: reconnect DOMQL tree to DOM |
| `loadProject(path)` | Import a `symbols/` directory structure |
| `generateSitemap(data)` | Generate sitemap.xml from routes |

---

## Features

| Feature | Details |
|---|---|
| Metadata | Title, description, Open Graph, Twitter cards from declarative `metadata` objects |
| Emotion CSS | Full CSS extraction including emotion-generated rules, CSS variables, reset, font imports |
| Theme support | Generates `prefers-color-scheme` media queries and `[data-theme]` selectors (no JS needed) |
| Data prefetching | Executes declarative `fetch` definitions during SSR via DB adapter (Supabase) |
| ISR | Optional client bundle for hydration + SPA navigation after initial static load |
| Sitemap | Auto-generated `sitemap.xml` from route definitions |

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
