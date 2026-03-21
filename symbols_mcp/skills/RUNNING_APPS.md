# Running Symbols Apps — 4 Modes

## Overview

| Mode | Package/Tool | Best For | Build Step |
|---|---|---|---|
| **Local Project** | `@symbo.ls/cli` | Production apps, team collaboration | Optional |
| **CDN** | `smbls` via ESM CDN | Prototypes, demos, learning | None |
| **JSON Runtime** | `@symbo.ls/frank` | Data-driven apps, platform sync | None |
| **Remote Server** | Mermaid | Managed hosting on `*.symbo.ls` | Server-side |

---

## 1. Local Project (Full Development Setup)

Standard way to build Symbols apps. Uses `smbls` CLI with structured `symbols/` directory. No build step for development — components are plain objects resolved at runtime.

### When to Use
- Full applications with routing, state, design systems
- Team collaboration via `smbls sync` / `smbls collab`
- Production deployments (Cloudflare, Vercel, Netlify, GitHub Pages, Symbols Platform)
- SSR with Brender

### Setup

```bash
npm i -g @symbo.ls/cli
smbls create my-app
cd my-app
npm start
```

Or link to the Symbols platform:

```bash
smbls project create my-app --create-new
cd my-app
npm start
```

### Project Structure

```
my-app/
├── symbols.json              # Project config (key, dir, bundler, brender)
├── package.json
└── symbols/
    ├── index.js              # Root entry: re-exports everything
    ├── state.js              # export default { key: value, ... }
    ├── dependencies.js       # export default { 'pkg': 'version' }
    ├── config.js             # export default { useReset: true, ... }
    ├── components/
    │   ├── index.js          # export * from './Navbar.js'
    │   └── Navbar.js         # export const Navbar = { ... }
    ├── pages/
    │   ├── index.js          # import-based route map (only file with imports)
    │   └── main.js           # export const main = { extends: 'Page', ... }
    ├── cases.js              # export default { isSafari: () => {}, ... }
    ├── functions/
    │   ├── index.js          # export * from './myFn.js'
    │   └── myFn.js           # export const myFn = function() {}
    ├── methods/
    │   └── index.js
    └── designSystem/
        ├── index.js          # export default { color, theme, font, ... }
        ├── color.js
        └── theme.js
```

### Key Rules
- **No imports between project files** (except `pages/index.js`)
- Components are plain objects, never functions
- Reference components by PascalCase key name in the tree
- `components/index.js` uses `export *` (never `export * as`)

### Deployment

```bash
smbls deploy --provider symbols       # Symbols Platform (native)
smbls deploy --provider cloudflare    # Cloudflare Pages
smbls deploy --provider vercel        # Vercel
smbls deploy --provider netlify       # Netlify
smbls deploy --provider github-pages  # GitHub Pages
```

All providers run `smbls build` first, outputting to `dist/`.

### SSR with Brender

Enable in `symbols.json`:

```json
{ "brender": true, "brenderDistDir": "dist-brender" }
```

```bash
smbls brender                # pre-render all static routes
smbls brender --watch         # watch mode
```

Generates static HTML with `data-br` hydration keys. Client-side DOMQL reconnects to pre-rendered DOM for full interactivity.

### Sync & Collaboration

```bash
smbls push                   # upload local -> platform
smbls fetch --update          # download platform -> local
smbls sync                   # two-way sync
smbls collab                 # real-time collaboration (watch mode)
```

---

## 2. CDN (Browser-Only, Zero Build)

Run Symbols directly in the browser with a single HTML file. No npm, no bundler, no CLI.

### When to Use
- Quick prototypes and demos
- Learning Symbols / DOMQL syntax
- Embedding Symbols in existing websites
- Single-file interactive examples
- Environments where npm/Node.js is unavailable

### Quick Start

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1" />
  <title>My Symbols App</title>
</head>
<body>
  <script type="module">
    import { create } from 'https://esm.sh/smbls'

    create({
      flow: 'column',
      padding: 'C',
      text: 'Hello from Symbols!'
    })
  </script>
</body>
</html>
```

### CDN Providers

| Provider | ESM Import | Recommended |
|---|---|---|
| **esm.sh** | `import { create } from 'https://esm.sh/smbls'` | Yes (best) |
| **jsDelivr** | `import { create } from 'https://cdn.jsdelivr.net/npm/smbls/+esm'` | Yes |
| **Skypack** | `import { create } from 'https://cdn.skypack.dev/smbls'` | Yes |
| **unpkg** | `import { create } from 'https://unpkg.com/smbls?module'` | OK |

Pin a version: `https://esm.sh/smbls@3.6.8`

### IIFE (Classic Script Tag)

For non-module usage, the IIFE build exposes `window.Smbls`:

```html
<script src="https://cdn.jsdelivr.net/npm/smbls"></script>
<script>
  Smbls.create({
    flow: 'y',
    text: 'Hello!'
  })
</script>
```

### Full CDN App Pattern

```html
<script type="module">
  import { create } from 'https://esm.sh/smbls'

  // Define reusable components as variables
  const Card = {
    flow: 'column',
    padding: 'B',
    round: 'A',
    background: 'white.95',
    border: '1px solid gray.1',

    Title: { tag: 'h3', fontSize: 'B', fontWeight: '600' },
    Description: { tag: 'p', fontSize: 'A', color: 'gray+20' }
  }

  const App = {
    flow: 'column',
    gap: 'B',
    padding: 'C',

    state: { count: 0 },

    Counter: {
      gap: 'A',
      Label: { text: ({ state }) => `Count: ${state.count}` },
      Inc: {
        extends: 'Button',
        text: '+',
        onClick: (e, el, s) => s.update({ count: s.count + 1 })
      }
    }
  }

  // Mount with optional config
  create(App, {
    designSystem: { color: { primary: '#0066cc' } },
    components: { Card },
    functions: { /* callable via el.call('fnName') */ },
    state: { /* global state */ }
  })
</script>
```

### Available Builds

The `smbls` package ships four formats:

| Format | Path | Usage |
|---|---|---|
| ESM | `dist/esm/index.js` | `import` with bundler (unbundled files) |
| CJS | `dist/cjs/index.js` | `require('smbls')` (Node) |
| Browser | `dist/browser/index.js` | Bundled ESM for direct browser/CDN use |
| IIFE | `dist/iife/index.js` | `<script>` tag → `window.Smbls` global |

### Available Exports

Everything exported from `smbls` is available via CDN:

```js
import { create, Flex, Button, Icon, Link } from 'https://esm.sh/smbls'
```

Includes: `create()`, all UIKit components (`Flex`, `Button`, `Input`, `Link`, `Icon`, etc.), design tokens, state management, events, CSS-in-props.

### CDN Limitations

- **No component registry** — cannot use `childExtends: 'MyComponent'` without `components/index.js`. Repeat shared styles inline or define JS variables.
- **No file-based routing** — no `pages/` folder, no `$router`. Use tab/view switching with DOM IDs.
- **No SSR** — client-side only.
- **Load time** — first load fetches dependencies from CDN (cached after).

### CDN vs Local Project

| Feature | Local Project | CDN |
|---|---|---|
| Component registry | `components/` folder | `components` option in `create()` |
| File-based routing | `pages/` folder | Not available (use tab switching) |
| `childExtends: 'Name'` | Works (registered components) | Works if passed in `components` |
| Design system | `designSystem/` folder | `designSystem` option in `create()` |
| SSR | Yes (Brender) | No (client-side only) |
| Build step | Optional (for production) | None |

---

## 3. JSON Runtime (`@symbo.ls/frank`)

Bidirectional transformation between Symbols project directories and JSON. Run Symbols apps from pure data — no filesystem, no imports.

### When to Use
- Storing/transporting Symbols apps as data (databases, APIs)
- Platform-to-local and local-to-platform synchronization
- Server-side rendering from stored project data
- Dynamic app loading without filesystem access
- Headless CMS or visual editor backends

### How It Works

**Project -> JSON** (`toJSON`):
```js
import { toJSON } from '@symbo.ls/frank'

const projectData = await toJSON({
  entry: './symbols',           // project directory
  stringify: true,              // serialize functions to strings
})
// Returns: { components, pages, designSystem, state, functions, methods, config, dependencies, ... }
```

**JSON -> Project** (`toFS`):
```js
import { toFS } from '@symbo.ls/frank'

await toFS(projectData, './output-dir', { overwrite: true })
// Generates full symbols/ directory structure from JSON
```

### JSON Output Structure

```json
{
  "components": {
    "Navbar": "{ flow: 'x', ... }",
    "Card": "{ flow: 'y', ... }"
  },
  "pages": {
    "/": "{ extends: 'Page', ... }",
    "/about": "{ extends: 'Page', ... }"
  },
  "designSystem": {
    "color": { "primary": "#0066cc" },
    "theme": { "dialog": { "round": "A" } }
  },
  "state": { "user": {}, "activeModal": false },
  "functions": { "switchView": "function switchView() { ... }" },
  "methods": {},
  "config": { "useReset": true, "useVariable": true },
  "dependencies": { "chart.js": "4.4.9" },
  "files": {}
}
```

### CLI Usage

```bash
# Project directory -> JSON file
smbls frank to-json ./symbols -o project.json

# JSON file -> project directory
smbls frank to-fs project.json -o ./output
```

### Integration with Mermaid Server

The Mermaid server (see section 4) loads apps from frank-generated JSON:

```bash
JSON_PATH=./project.json node mermaid/index.js
```

This is how the Symbols platform stores and serves projects — frank serializes for storage, mermaid deserializes for rendering.

---

## 4. Remote Symbols Server (Mermaid)

Rendering server that hosts Symbols apps on dynamic subdomains (`*.symbo.ls`, `*.preview.symbols.app`) and custom domains. Fetches project data and renders full HTML pages.

### When to Use
- Hosting apps on `*.symbo.ls` or `*.preview.symbols.app` subdomains
- Custom domain hosting for Symbols apps
- Managed deployment via `smbls push` / `smbls deploy`
- Multi-environment support (dev, staging, production)
- SEO-optimized server-rendered pages

### How It Works

1. Deploy via `smbls push` -> project data stored on Symbols platform
2. Request hits `myapp.nikoloza.preview.symbols.app`
3. Mermaid resolves appkey from subdomain
4. Fetches project data (from DB, gateway, or local JSON)
5. Generates JavaScript bundle from project data
6. In production: pre-renders HTML via Brender (SSR)
7. Returns complete HTML page with SEO metadata

### URL Patterns

```
# Production
https://myapp.nikoloza.preview.symbols.app/

# Development
https://myapp.nikoloza.preview.dev.symbols.app/

# Staging
https://myapp.nikoloza.preview.staging.symbols.app/

# Legacy format
https://myapp.symbo.ls/

# Custom domain
https://yourdomain.com/
```

### Deployment

```bash
# Push to Symbols platform
smbls push

# The app is live at:
# https://<project>.<username>.preview.symbols.app/
```

### Channels

| Channel | URL Pattern | SEO | Use Case |
|---|---|---|---|
| **production** | `*.preview.symbols.app` | Indexed | Live site |
| **staging** | `*.preview.staging.symbols.app` | noindex | QA/review |
| **development** | `*.preview.dev.symbols.app` | noindex | Active dev |

### Custom Domains

Attach custom domains through the Symbols platform. Mermaid resolves custom domains to the correct project data.

### Self-Hosting Mermaid

Run as:

1. **Node.js server**: `node mermaid/index.js` (port 3333)
2. **Cloudflare Worker**: `npx wrangler deploy` (edge deployment)
3. **With local JSON**: `JSON_PATH=./project.json node mermaid/index.js`

Environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `PORT` | HTTP port | 3333 |
| `APPKEY` | Lock to specific project | (from Host header) |
| `MONGODB_URI` | Direct DB connection | — |
| `GATEWAY_URL` | Gateway endpoint | — |
| `JSON_PATH` | Local JSON file | — |
| `NODE_ENV` | development/staging/production | development |

### Data Flow

```
Local Project ──(frank toJSON)──> JSON Data ──(store)──> Database
                                                            │
Browser Request ──> Mermaid Server ──(fetch)────────────────┘
                         │
                    Render HTML ──> Response
```

---

## Comparison

| Feature | Local Project | CDN | JSON Runtime | Remote Server |
|---|---|---|---|---|
| Setup complexity | Medium | None | Low | Low (managed) |
| Build step | Optional | None | None | Server-side |
| Routing | Full (`pages/`) | Manual | Full | Full |
| Component registry | Yes | Limited | Yes | Yes |
| SSR | Yes (Brender) | No | Yes (via Mermaid) | Yes |
| State management | Full | Full | Full | Full |
| Design system | File-based | Inline | JSON | JSON |
| Collaboration | `smbls collab` | No | Platform | Platform |
| Custom domains | Via deploy | No | No | Yes |
| SEO | With Brender | No | With Mermaid | Yes |
| Offline | Yes | No (first load) | Yes | No |
| Best for | Production apps | Prototypes | Data-driven apps | Managed hosting |

---

## Detection Guide

### Local Project
- Has `symbols.json` in root
- Has `symbols/` directory with `components/`, `pages/`, etc.
- Has `package.json` with `smbls` dependency
- Uses `smbls start` / `smbls build` commands

### CDN
- Single `index.html` file (or few HTML files)
- Contains `import ... from 'https://esm.sh/smbls'` or similar CDN URL
- Or uses `<script src="https://cdn.jsdelivr.net/npm/smbls"></script>` (IIFE)
- No `package.json` or `symbols.json`
- No `symbols/` directory

### JSON Runtime
- Has `.json` files containing serialized Symbols project data
- Uses `@symbo.ls/frank` for conversion
- May have `JSON_PATH` environment variable
- Project data stored in database or API

### Remote Server
- Deployed to `*.symbo.ls` or `*.preview.symbols.app`
- Uses `smbls push` for deployment
- May have custom domain configured
- Mermaid server handles rendering
