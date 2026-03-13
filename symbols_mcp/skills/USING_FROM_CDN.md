# Using Symbols from CDN

Use Symbols directly in the browser with zero build step via ESM CDN imports. No npm, no bundler — just an `index.html`.

---

## Quick Start

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
        extends: 'Flex',
        flow: 'column',
        padding: 'C',
        text: 'Hello from Symbols!'
      })
    </script>
  </body>
</html>
```

Open the file directly or serve with any static server (`npx serve .`).

---

## Available Builds

The `smbls` package ships four build formats, all self-contained (dependencies bundled in):

| Format  | Path                     | Usage                                   |
| ------- | ------------------------ | --------------------------------------- |
| ESM     | `dist/esm/index.js`     | `import` with bundler (unbundled files) |
| CJS     | `dist/cjs/index.js`     | `require('smbls')` (Node)               |
| Browser | `dist/browser/index.js`  | Bundled ESM for direct browser/CDN use  |
| IIFE    | `dist/iife/index.js`    | `<script>` tag → `window.Smbls` global  |

- **ESM** — individual transpiled files, meant for bundler-based projects (`npm install smbls`)
- **CJS** — same but CommonJS format for Node/legacy bundlers
- **Browser** — single bundled + minified ESM file, ideal for CDN `<script type="module">` imports
- **IIFE** — single bundled + minified file exposing `window.Smbls`, for classic `<script>` tag usage

---

## CDN Providers

### ESM imports (`<script type="module">`)

Any ESM-capable CDN works. Pick the one that suits your needs:

#### esm.sh (recommended)

Converts npm packages to ES modules on the fly. Handles all sub-dependencies automatically.

```js
import { create } from 'https://esm.sh/smbls'
import { create } from 'https://esm.sh/smbls@3.6.6'    // pinned version
```

#### jsDelivr

Serves files directly from npm. Use `/+esm` for ES module format.

```js
import { create } from 'https://cdn.jsdelivr.net/npm/smbls/+esm'
import { create } from 'https://cdn.jsdelivr.net/npm/smbls@3.6.6/+esm'  // pinned
```

#### Skypack

ESM-first CDN with built-in optimization and minification.

```js
import { create } from 'https://cdn.skypack.dev/smbls'
import { create } from 'https://cdn.skypack.dev/smbls@3.6.6'  // pinned
```

#### unpkg

Serves files from npm as-is. Use `?module` for ESM resolution.

```js
import { create } from 'https://unpkg.com/smbls?module'
import { create } from 'https://unpkg.com/smbls@3.6.6?module'  // pinned
```

### IIFE / classic `<script>` tag

For non-module usage, load the IIFE build directly. jsDelivr and unpkg auto-resolve the `unpkg`/`jsdelivr` fields in `package.json` to `dist/iife/index.js`:

```html
<script src="https://cdn.jsdelivr.net/npm/smbls"></script>
<script src="https://unpkg.com/smbls"></script>
```

This exposes `window.Smbls` as a global with all dependencies bundled and minified:

```html
<script src="https://cdn.jsdelivr.net/npm/smbls"></script>
<script>
  Smbls.create({
    extends: 'Flex',
    text: 'Hello from Symbols!'
  })
</script>
```

### Comparison

| CDN        | ESM native | Auto-resolves deps | Minified | IIFE support |
| ---------- | ---------- | ------------------ | -------- | ------------ |
| esm.sh     | yes        | yes                | yes      | no           |
| jsDelivr   | `/+esm`    | yes                | yes      | yes          |
| unpkg      | `?module`  | no                 | no       | yes          |
| Skypack    | yes        | yes                | yes      | no           |

> **Recommendation**: Use `esm.sh` or `Skypack` for the smoothest experience — they handle smbls's deep dependency tree automatically. `jsDelivr` with `/+esm` is also reliable. `unpkg` without `?module` serves the IIFE build by default.

---

## How It Works

- `<script type="module">` enables ESM `import` syntax in the browser
- The CDN serves the `smbls` package as a browser-compatible ES module, resolving all dependencies
- `create(App)` renders the DOMQL element tree into `document.body`
- All v3 syntax rules apply — `extends`, `childExtends`, `flexAlign`, `state.update()`, etc.

---

## Full Example — Counter + Cards

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1" />
    <title>smbls CDN Example</title>
  </head>
  <body>
    <script type="module">
      import { create } from 'https://esm.sh/smbls'

      const App = {
        extends: 'Flex',
        flow: 'column',
        gap: 'B',
        padding: 'C',
        maxWidth: 'G3',
        margin: '0 auto',

        Header: {
          tag: 'header',
          extends: 'Flex',
          flow: 'column',
          gap: 'A',
          padding: 'B 0',
          borderBottom: '1px solid gray.1',

          Title: {
            tag: 'h1',
            text: 'smbls CDN Example',
            fontSize: 'E',
            fontWeight: '700',
            margin: '0'
          },
          Subtitle: {
            tag: 'p',
            text: 'Loaded directly from CDN using ESM imports',
            fontSize: 'B',
            color: 'gray+30',
            margin: '0'
          }
        },

        Counter: {
          extends: 'Flex',
          flow: 'column',
          gap: 'A',
          padding: 'B',
          round: 'A',
          background: 'gray.05',

          state: { count: 0 },

          Label: {
            tag: 'span',
            text: ({ state }) => `Count: ${state.count}`,
            fontSize: 'C',
            fontWeight: '600'
          },

          Buttons: {
            extends: 'Flex',
            flexAlign: 'center center',
            gap: 'A',

            Decrement: {
              extends: 'Button',
              text: '-',
              onClick: (event, el, state) => {
                state.update({ count: state.count - 1 })
              }
            },

            Increment: {
              extends: 'Button',
              text: '+',
              onClick: (event, el, state) => {
                state.update({ count: state.count + 1 })
              }
            }
          }
        },

        Cards: {
          extends: 'Flex',
          gap: 'B',
          flexWrap: 'wrap',

          Card1: {
            extends: 'Flex',
            flow: 'column',
            gap: 'Z',
            padding: 'B',
            round: 'A',
            background: 'white.95',
            border: '1px solid gray.1',
            flex: '1 1 200px',

            Title: {
              tag: 'h3',
              margin: '0',
              fontSize: 'B',
              fontWeight: '600',
              text: 'Declarative'
            },
            Description: {
              tag: 'p',
              margin: '0',
              fontSize: 'A',
              color: 'gray+20',
              text: 'Build UIs with plain objects - no JSX, no templates.'
            }
          },

          Card2: {
            extends: 'Flex',
            flow: 'column',
            gap: 'Z',
            padding: 'B',
            round: 'A',
            background: 'white.95',
            border: '1px solid gray.1',
            flex: '1 1 200px',

            Title: {
              tag: 'h3',
              margin: '0',
              fontSize: 'B',
              fontWeight: '600',
              text: 'No Build Step'
            },
            Description: {
              tag: 'p',
              margin: '0',
              fontSize: 'A',
              color: 'gray+20',
              text: 'Works directly in the browser via CDN import.'
            }
          },

          Card3: {
            extends: 'Flex',
            flow: 'column',
            gap: 'Z',
            padding: 'B',
            round: 'A',
            background: 'white.95',
            border: '1px solid gray.1',
            flex: '1 1 200px',

            Title: {
              tag: 'h3',
              margin: '0',
              fontSize: 'B',
              fontWeight: '600',
              text: 'Design Tokens'
            },
            Description: {
              tag: 'p',
              margin: '0',
              fontSize: 'A',
              color: 'gray+20',
              text: 'Built-in spacing, typography, and theming system.'
            }
          }
        }
      }

      create(App)
    </script>
  </body>
</html>
```

---

## Key Differences from Project Setup

| Full project                          | CDN single-file                        |
| ------------------------------------- | -------------------------------------- |
| `components/`, `pages/` folders       | Everything in one `<script>` block     |
| `export const Foo = { ... }`          | Inline objects in the tree             |
| `childExtends: 'ComponentName'`       | Repeat shared styles per element (no component registry) |
| `npm install smbls`                   | `import from 'https://esm.sh/smbls'`  |
| Pages extend `'Page'`                 | Root element extends `'Flex'` (no router) |

---

## What You Can Use

Everything exported from the `smbls` package is available:

```js
import { create, Flex, Button, Icon, Link } from 'https://esm.sh/smbls'
```

This includes:
- `create()` — render an app
- All UIKit components (`Flex`, `Button`, `Input`, `Link`, `Icon`, etc.)
- Design tokens (spacing, typography, colors)
- State management via `state` + `state.update()`
- Events (`onClick`, `onRender`, etc.)
- CSS-in-props

---

## Limitations

- **No component registry** — you can't use `childExtends: 'MyComponent'` since there's no `components/index.js` to register named components. Repeat shared styles inline or define JS variables.
- **No file-based routing** — no `pages/` folder, no `$router`. For multi-view apps, use the tab/view switching pattern with DOM IDs.
- **No SSR** — CDN usage is client-side only.
- **Load time** — first load fetches dependencies from esm.sh (cached after).
