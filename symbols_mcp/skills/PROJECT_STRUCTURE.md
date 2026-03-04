# Symbols Project Structure & Setup

Environment-agnostic folder structure for the Symbols platform. Generates independent files without JS module preloading, enabling seamless rendering across VSCode, file structure, Symbols platform, server rendering, and browsers.

---

## Core Principle

**NO JavaScript imports/exports for component usage.** Components are registered once in their folders and reused through a declarative object tree. No build step required.

---

## Full Project Layout

```
smbls/
├── index.js                  # Root entry: exports components, pages, state, designSystem, functions
├── state.js                  # export default { key: initialValue, ... }
├── dependencies.js           # export default { 'pkg': 'exact-version' }
├── config.js                 # export default { useReset: true, useVariable: true, ... }
├── vars.js                   # export default { APP_VERSION: '1.0.0', ... }
│
├── components/
│   ├── index.js              # export * from './Foo.js'  ← FLAT re-exports only
│   └── Navbar.js             # export const Navbar = { ... }
│
├── pages/
│   ├── index.js              # import-based registry — ONLY file with imports allowed
│   └── main.js               # export const main = { extends: 'Page', ... }
│
├── functions/
│   ├── index.js              # export * from './switchView.js'
│   └── switchView.js         # export const switchView = function(...) {}
│
├── methods/
│   ├── index.js              # export * from './formatDate.js'
│   └── formatDate.js         # export const formatDate = function(date) { ... }
│
├── designSystem/
│   ├── index.js              # export default { COLOR, THEME, FONT, ... }
│   ├── COLOR.js              # export default { blue: '#0474f2', ... }
│   ├── THEME.js              # export default { dialog: { ... }, ... }
│   └── TYPOGRAPHY.js         # export default { base: 16, ratio: 1.25, ... }
│
└── state/                    # (alternative to state.js)
    ├── index.js              # export default { user: {}, metrics: [], ... }
    └── metrics.js            # export default [{ title: 'Status', ... }]
```

---

## 1. Components (`components/`)

```js
// components/Header.js
export const Header = {
  extends: 'Flex',
  minWidth: 'G2',
  padding: 'A',

  Search: { extends: 'Input', flex: 1 },
  Avatar: { extends: 'Image', boxSize: 'B' },
}
```

Rules:
- Named export matching filename (PascalCase)
- Component name MUST match filename
- No imports from other project files — reference by key name in tree
- Props use design system tokens (`minWidth: 'G2'`, `padding: 'A'`)

```js
// components/index.js — use export * ONLY, never export * as
export * from './Header.js'
export * from './Navbar.js'
// ❌ NEVER: export * as Header from './Header.js'
```

---

## 2. Pages (`pages/`)

```js
// pages/dashboard.js — dash-case filename, camelCase export
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

Rules:
- Filenames: **dash-case** (`add-network.js`, `edit-node.js`)
- Exports: **camelCase** (`export const addNetwork`)
- Always extend from `'Page'`

```js
// pages/index.js — only file where imports are allowed
import { main } from './main.js'
import { dashboard } from './dashboard.js'

export default {
  '/':          main,
  '/dashboard': dashboard,
}
```

---

## 3. Functions (`functions/`)

```js
// functions/parseNetworkRow.js
export const parseNetworkRow = function parseNetworkRow(data) {
  return processedData
}
```

Rules:
- Named export matching filename (camelCase)
- Pure, standalone utilities — no imports of other project files
- Called via `el.call('functionName', ...args)` from event handlers

```js
// In component
Button: { onClick: (e, el) => el.call('parseNetworkRow', data) }
```

`el.call()` binds the DOMQL element as `this` inside the function.

---

## 4. Methods (`methods/`)

```js
// methods/formatDate.js
export const formatDate = function(date) {
  return new Intl.DateTimeFormat().format(date)
}
```

Rules:
- Utility methods that extend element behavior
- Registered once, reused across all components

---

## 5. Design System (`designSystem/`)

```js
// designSystem/COLOR.js
export default {
  black: '#000',
  white: '#fff',
  primary: '#0066cc',
}

// designSystem/SPACING.js
export default { base: 16, ratio: 1.618 }

// designSystem/index.js
import COLOR from './COLOR.js'
import THEME from './THEME.js'
export default { COLOR, THEME }
```

See `DESIGN_SYSTEM.md` for full token reference.

---

## 6. State (`state.js` or `state/index.js`)

```js
// state.js
export default {
  user: {},
  activeModal: false,
  currentPage: '/',
  metrics: [],
}
```

Rules:
- Pure data structures only — no logic, no methods
- All initial state inline in a single file (no cross-imports)
- Accessed and updated via `state.propertyName` or `state.update({})`

---

## 7. Dependencies (`dependencies.js`)

```js
export default {
  'chart.js': '4.4.9',
  'fuse.js': '7.1.0',
  'lit': '3.1.0',
}
```

Rules:
- Maps npm package names to **exact** version numbers (no `^` or `~`)
- No module preloading — packages imported on-demand via dynamic `import()`
- Keeps structure resolvable without a build step

Dynamic import pattern:
```js
onClick: async (e, el) => {
  const { Chart } = await import('chart.js')
  const chart = new Chart(el.node, { /* config */ })
}
```

---

## 8. Config (`config.js`)

```js
export default {
  useReset: true,
  useVariable: true,
  useFontImport: true,
  useIconSprite: true,
  useSvgSprite: true,
  useDefaultConfig: true,
  useDocumentTheme: true,
  verbose: false,
}
```

Controls runtime behavior and rendering flags.

---

## Root `index.js`

The root entry file wires everything together:

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

All packages version-locked at the same version across the monorepo. Consumer apps depend on `"smbls": "3.x.x"` (workspace-resolved).

---

## CLI Setup

### Installation

```bash
npm i -g @symbo.ls/cli
```

### Create a new project

```bash
# Local-only (fastest)
smbls create <project-name>
cd <project-name>
npm start

# Platform-linked (collaboration + remote preview)
smbls project create <project-name> --create-new
cd <project-name>
npm start
```

### Authentication

```bash
smbls login --check    # check login status
smbls login            # sign in
smbls servers          # list servers
smbls servers --select # switch server
```

### Sync & Collaboration

```bash
smbls push             # upload local → platform
smbls fetch --update   # download platform → local
smbls sync             # two-way sync (interactive conflict handling)
smbls collab           # live collaboration watch mode (separate terminal)
```

### File Management

```bash
smbls files list
smbls files upload
smbls files download
smbls files rm
```

### Linking an Existing Platform Project

```bash
smbls project link .                     # interactive picker
smbls project link . --key <key>.symbo.ls  # non-interactive
smbls project link . --id <projectId>
```

### Shell Auto-completion

```bash
smbls completion zsh --install
smbls completion bash --install
```

---

## Remote Preview URLs

After linking and pushing a project, the preview URLs follow this pattern:

```
Preview:   https://<app>.<user>.preview.symbo.ls/
Dev env:   https://dev.<app>.<user>.preview.symbo.ls/
With path: https://<app>.<user>.preview.symbo.ls/<subpath>
```

Where:
- `<user>` — Symbols username or org
- `<app>` — project identifier
- `<env>` — optional environment (`dev`, `stage`, etc.)

Example for user `nikoloza`, project `my-app`:
```
https://my-app.nikoloza.preview.symbo.ls/
https://dev.my-app.nikoloza.preview.symbo.ls/
```

---

## AI Integration

To instruct an AI coding assistant to follow project conventions:

```
Use instructions from all .md files in the /docs folder
```

Best tools for Symbols development: Claude Code > Cursor > Copilot

Workflows that work best with AI assistance:
- Extending existing Symbols apps
- Migrating existing projects to Symbols
- Scaffolding new projects from screenshots or Figma

---

## Troubleshooting

| Problem                       | Fix                                          |
| ----------------------------- | -------------------------------------------- |
| Auth required / access denied | `smbls login`                                |
| Missing project key           | Check `symbols.json` or `smbls project link .` |
| Need verbose output           | Add `--verbose` to any command               |
| CLI not found                 | `npm i -g @symbo.ls/cli`                     |
| Build fails on new pkg method | Add method to `METHODS` in `keys.js` AND `set.js` |

### Build order for monorepo changes

When changing smbls source, rebuild in dependency order:

```bash
cd smbls/packages/utils && npm run build:esm   # utils first
cd smbls/packages/element && npm run build:esm  # then element
# consumer apps pick up via parcel --watch-dir=../smbls/packages
```
