# Symbols Project Structure

Follow this environment-agnostic folder structure for the Symbols platform. Generate independent files without JS module preloading. Files must render seamlessly across VSCode, file structure, Symbols platform, server rendering (`@symbo.ls/brender`), and browsers.

> Conventions: flat element API, `(el, s)` reactive prop functions, declarative `fetch:` (`@symbo.ls/fetch`), polyglot, helmet metadata, signal-based state.

---

## Core Principle

Do NOT use JavaScript imports/exports for component usage. Register components once in their folders and reuse them through a declarative object tree. No build step is required.

---

## Full Project Layout

```
project-root/
├── supabase/                     # Supabase backend (server-side)
│   ├── config.toml               # Supabase local dev config
│   ├── seed.sql                  # Database seeding
│   ├── migrations/               # SQL migration files
│   │   └── 001_create_tables.sql
│   └── functions/                # Supabase Edge Functions (Deno, server-side)
│       └── send-email/
│           └── index.ts
│
└── symbols/                      # Symbols frontend (client-side)
    ├── index.js                  # Root entry: exports components, pages, state, designSystem, functions
    ├── state.js                  # export default { key: initialValue, ... }
    ├── cases.js                  # export default { isSafari: () => {}, ... } — conditional cases
    ├── lang.js                   # Translations — root level, NOT in designSystem
    ├── dependencies.js           # export default { 'pkg': 'exact-version' }
    ├── config.js                 # export default { useReset: true, db: { adapter: 'supabase', url, key, auth, db, global }, polyglot: {...}, router: {...} }
    ├── vars.js                   # export default { APP_VERSION: '1.0.0', ... }
    │
    ├── components/
    │   ├── index.js              # export * from './Foo.js'  — FLAT re-exports only
    │   └── Navbar.js             # export const Navbar = { ... }
    │
    ├── pages/
    │   ├── index.js              # Import-based registry — ONLY file with imports allowed
    │   └── main.js               # export const main = { extends: 'Page', ... }
    │
    ├── functions/                # Frontend functions ONLY (called via el.call())
    │   ├── index.js              # export * from './switchView.js'
    │   └── switchView.js         # export const switchView = function(...) {}
    │
    ├── methods/
    │   ├── index.js              # export * from './formatDate.js'
    │   └── formatDate.js         # export const formatDate = function(date) { ... }
    │
    ├── designSystem/             # Visual tokens ONLY — NO translations, NO logic
    │   ├── index.js              # export default { color, theme, font, ... }
    │   ├── color.js              # export default { blue: '#0474f2', ... }
    │   ├── theme.js              # export default { dialog: { ... }, ... }
    │   └── typography.js         # export default { base: 16, ratio: 1.25, ... }
    │
    └── state/                    # (alternative to state.js)
        ├── index.js              # export default { user: {}, metrics: [], ... }
        └── metrics.js            # export default [{ title: 'Status', ... }]
```

Each folder is described below. Follow these rules strictly when creating or modifying files.

---

## Components (`components/`)

Create one named export per file, PascalCase, matching the filename exactly.

```js
// components/Header.js
export const Header = {
  flow: 'x',
  minWidth: 'G2',
  padding: 'A',

  Search: { extends: 'Input', flex: 1 },     // Search is the key, Input is the atom
  Avatar: { boxSize: 'B' },                    // Avatar key auto-extends the Avatar default-library component (no Image atom — it's `Img`)
}
```

**Rules:**
- Use a named export matching the filename (PascalCase).
- Never import from other project files — reference by key name in the tree.
- Use design system tokens for props (`minWidth: 'G2'`, `padding: 'A'`).

Use `export *` only in `components/index.js`. Never use `export * as`.

```js
// components/index.js
export * from './Header.js'
export * from './Navbar.js'
// NEVER: export * as Header from './Header.js'
```

---

## Pages (`pages/`)

Create files as shown. Use dash-case filenames and camelCase exports. Always extend from `'Page'`.

```js
// pages/dashboard.js
export const dashboard = {
  extends: 'Page',
  width: '100%',
  padding: 'A',

  onRender: async (el, state) => {
    await el.call('auth')
  },

  Form: {
    Input: { extends: 'Input', placeholder: 'Search...' }
  }
}
```

**Rules:**
- Filenames: dash-case (`add-network.js`, `edit-node.js`).
- Exports: camelCase (`export const addNetwork`).
- Always extend from `'Page'`.

Register routes in `pages/index.js` — the only file where imports are allowed:

```js
// pages/index.js
import { main } from './main.js'
import { dashboard } from './dashboard.js'

export default {
  '/':          main,
  '/dashboard': dashboard,
}
```

---

## Functions (`symbols/functions/`) — Frontend Only

`symbols/functions/` contains **client-side frontend functions** that run in the browser. They are called via `el.call()` from components, and `this` is bound to the DOMQL element.

**Do NOT place server-side/backend functions here.** Supabase Edge Functions (Deno) go in `supabase/functions/`.

```js
// symbols/functions/parseNetworkRow.js
export const parseNetworkRow = function parseNetworkRow(data) {
  return processedData
}
```

Frontend functions may call external APIs (including Supabase) via the client SDK:

```js
// symbols/functions/fetchItems.js
export const fetchItems = async function fetchItems(category) {
  const el = this
  const s = el.getRootState()
  // Use the framework's getDB() to obtain the configured adapter (supabase/rest/local)
  const db = await this.getDB()
  const { data } = await db.select({ from: 'items' })
  s.update({ items: data || [] })
}
```

Call functions from event handlers via `el.call()`:

```js
// In a component
Button: { onClick: (e, el) => el.call('parseNetworkRow', data) }
```

`el.call()` binds the DOMQL element as `this` inside the function.

---

## Supabase Backend (`supabase/`)

Server-side resources live outside the `symbols/` directory:

- `supabase/migrations/` — SQL migration files for schema changes
- `supabase/functions/` — Supabase Edge Functions (Deno, server-side)
- `supabase/config.toml` — Local dev configuration
- `supabase/seed.sql` — Database seeding

```ts
// supabase/functions/send-email/index.ts — server-side Edge Function
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

serve(async (req) => {
  const { to, subject, body } = await req.json()
  // server-side email logic
  return new Response(JSON.stringify({ success: true }))
})
```

---

## Methods (`methods/`)

Create utility methods that extend element behavior. Register once; they become reusable across all components.

```js
// methods/formatDate.js
export const formatDate = function(date) {
  return new Intl.DateTimeFormat().format(date)
}
```

---

## Design System (`designSystem/`) — Visual Tokens Only

Define **visual design tokens only** — colors, typography, spacing, icons, themes. Do NOT store translations, application logic, or data here.

```js
// designSystem/color.js
export default {
  black: '#000',
  white: '#fff',
  primary: '#0066cc',
}

// designSystem/spacing.js
export default { base: 16, ratio: 1.618 }

// designSystem/index.js
import color from './color.js'
import theme from './theme.js'
export default { color, theme }
```

**What belongs here:** color, gradient, theme, font, typography, spacing, timing, grid, icons, shape, reset, animation, media, vars.

**What does NOT belong here:** translations/lang (use root-level `lang.js`), cases (use root-level `cases.js`), application state, API config, business logic.

See `DESIGN_SYSTEM.md` for the full token reference.

---

## Translations (`lang.js`) — Root Level

Translations live at root level (`symbols/lang.js`), NOT inside `designSystem/`. Export them in `context.js` at root level alongside other top-level modules.

```js
// symbols/lang.js
export default {
  en: { welcome: 'Welcome', search: 'Search' },
  ka: { welcome: 'მოგესალმებით', search: 'ძებნა' },
}

// symbols/context.js
import lang from './lang.js'
export default { lang, cases, state, components, designSystem, ...config }
```

For Supabase-backed translations, configure the `polyglot` key in `config.js`:

```js
// config.js
export default {
  polyglot: {
    defaultLang: 'en',
    languages: ['en', 'ka', 'ru'],
    storageLangKey: 'app_lang',
    storagePrefix: 'app_t_',
    fetch: {
      rpc: 'get_translations_if_changed',
      table: 'translations'
    }
  }
}
```

---

## State (`state.js` or `state/index.js`)

Declare pure data structures only. Do not include logic or methods. Keep all initial state in a single file with no cross-imports.

```js
// state.js
export default {
  user: {},
  activeModal: false,
  currentPage: '/',
  metrics: [],
}
```

Access and update state via `state.propertyName` or `state.update({})`.

---

## Dependencies (`dependencies.js`)

Map npm package names to exact version numbers. Do not use `^` or `~`. Do not preload modules — import on demand via dynamic `import()`.

```js
export default {
  'chart.js': '4.4.9',
  'fuse.js': '7.1.0',
  'lit': '3.1.0',
}
```

Dynamic import pattern:

```js
onClick: async (e, el) => {
  const { Chart } = await import('chart.js')
  const chart = new Chart(el.node, { /* config */ })
}
```

---

## Config (`config.js`)

Control runtime behavior, rendering flags, and backend integration:

```js
import { createClient } from '@supabase/supabase-js'

export default {
  useReset: true,
  useVariable: true,
  useFontImport: true,
  useIconSprite: true,
  useSvgSprite: true,
  useDefaultConfig: true,
  useDocumentTheme: true,
  verbose: false,

  // Supabase fetch adapter — declarative data fetching
  fetch: {
    adapter: 'supabase',
    createClient,
    url: 'https://your-project.supabase.co',
    key: 'your-anon-key',
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  },

  // Polyglot i18n configuration
  polyglot: {
    defaultLang: 'en',
    languages: ['en', 'ka'],
    storageLangKey: 'app_lang',
    storagePrefix: 'app_t_'
  }
}
```

---

## Root `index.js`

Wire everything together in the root entry file:

```js
export * as components from './components/index.js'
export { default as designSystem } from './designSystem/index.js'
export { default as state } from './state.js'
export { default as pages } from './pages/index.js'
export * as functions from './functions/index.js'
```

---

## Monorepo Package Layout

```
next/
├── smbls/                     # monorepo submodule
│   ├── packages/
│   │   ├── element/           # @domql/element  — core renderer
│   │   ├── utils/             # @domql/utils    — shared utilities
│   │   ├── state/             # @domql/state
│   │   └── uikit/            # @symbo.ls/uikit
│   └── plugins/
│       └── router/            # @domql/router
├── platform/                  # internal platform app
└── rita/, bazaar/, ...        # consumer apps
```

All packages are version-locked at the same version across the monorepo. Consumer apps depend on `"smbls"` (workspace-resolved).

---

## CLI Setup

### Install

```bash
npm i -g @symbo.ls/cli
```

### Create a Project

| Goal | Command |
|------|---------|
| Default (with `system/default` library) | `smbls create <project-name> && cd <project-name> && npm start` |
| Blank (no shared libraries) | `smbls create <project-name> --blank-shared-libraries && cd <project-name> && npm start` |
| Platform-linked (collaboration + remote preview) | `smbls project create <project-name> --create-new && cd <project-name> && npm start` |

### Authentication

| Command | Action |
|---------|--------|
| `smbls login --check` | Check login status |
| `smbls login` | Sign in |
| `smbls servers` | List servers |
| `smbls servers --select` | Switch server |

### Sync & Collaboration

| Command | Action |
|---------|--------|
| `smbls push` | Upload local to platform |
| `smbls fetch --update` | Download platform to local |
| `smbls sync` | Two-way sync (interactive conflict handling) |
| `smbls collab` | Live collaboration watch mode (run in separate terminal) |

### File Management

| Command | Action |
|---------|--------|
| `smbls files list` | List files |
| `smbls files upload` | Upload files |
| `smbls files download` | Download files |
| `smbls files rm` | Remove files |

### Linking an Existing Platform Project

| Command | Action |
|---------|--------|
| `smbls project link .` | Interactive picker |
| `smbls project link . --key <key>.symbo.ls` | Non-interactive, by key |
| `smbls project link . --id <projectId>` | Non-interactive, by ID |

### Shell Auto-completion

| Command | Action |
|---------|--------|
| `smbls completion zsh --install` | Install zsh completions |
| `smbls completion bash --install` | Install bash completions |

---

## Remote Preview URLs

After linking and pushing a project, access previews at these URLs:

| Type | URL Pattern |
|------|-------------|
| Preview | `https://<app>.<user>.preview.symbo.ls/` |
| Dev environment | `https://dev.<app>.<user>.preview.symbo.ls/` |
| With subpath | `https://<app>.<user>.preview.symbo.ls/<subpath>` |

- `<user>` — Symbols username or org
- `<app>` — project identifier

Example for user `<owner>`, project `my-app`:
```
https://my-app.<owner>.preview.symbo.ls/
https://dev.my-app.<owner>.preview.symbo.ls/
```

---

## AI Integration

Instruct an AI coding assistant to follow project conventions with:

```
Use instructions from all .md files in the /docs folder
```

Recommended tools for Symbols development: Claude Code > Cursor > Copilot.

Workflows that work best with AI assistance:
- Extending existing Symbols apps
- Migrating existing projects to Symbols
- Scaffolding new projects from screenshots or Figma

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Auth required / access denied | Run `smbls login` |
| Missing project key | Check `symbols.json` or run `smbls project link .` |
| Need verbose output | Add `--verbose` to any command |
| CLI not found | Run `npm i -g @symbo.ls/cli` |
| Build fails on new pkg method | Add method to `METHODS` in `keys.js` AND `set.js` |

---

## Build Order

When changing smbls source, rebuild in dependency order:

```bash
cd smbls/packages/utils && npm run build:esm   # utils first
cd smbls/packages/element && npm run build:esm  # then element
# consumer apps pick up via parcel --watch-dir=../smbls/packages
```
