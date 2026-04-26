# Design System — Contract + Token Reference

The complete design-system reference: the runtime contract (pipeline, multi-app isolation, `changeGlobalTheme`), the token catalog (color, theme, typography, spacing, timing, animation, media, icons), CSS-in-props shorthands, and configuration. This is the **single canonical doc** — no other file overlaps with it.

> For component-level rules (PascalCase children, flat element API, syntax) → [`FRAMEWORK.md`](./FRAMEWORK.md).
> For strict rule numbers → [`RULES.md`](./RULES.md) Rules 27/28/45/50.

---

# Part 1 — The Contract

## Pipeline

```
create(app, options)
  │
  ├─ resolveAndApplyTheme(options)      ← @symbo.ls/smbls/src/index.js
  │     URL ?globalTheme   >   localStorage[themeStorageKey]   >   options.globalTheme
  │     → early-paint: scopeRoot.setAttribute('data-theme', <concrete>)
  │           – `'auto'` is resolved to `'dark'`/`'light'` from
  │             `prefers-color-scheme` so the attribute is never empty
  │             and per-element `[data-theme="…"] &` rules always resolve
  │     → options.themeRoot = scopeRoot   (default: document.documentElement)
  │     → options.globalTheme stays `'auto'` if no user override (lets
  │       scratch.set install the live OS-preference listener)
  │
  ├─ prepareDesignSystem(...)           ← @symbo.ls/smbls/src/prepare.js
  │     → detects primary vs secondary app (_designSystemInitialized)
  │     → PRIMARY: init(designSystem, { scopeSelector: ':root', globalTheme,
  │                                     themeRoot, … })
  │     → SECONDARY:
  │           const isolated = createConfig(key, designSystem, { cleanBase: true })
  │           pushConfig(isolated) → init(isolated, …) → popConfig()
  │           – scopeSelector: `[data-smbls-app="<key>"]`
  │           – cssPrefix = key.replace(/[^a-zA-Z0-9]/g,'').substring(0,6)
  │             stored on context.cssPrefix AND isolated.varPrefix
  │             (one identifier, used for atomic class names AND CSS vars)
  │           – cleanBase: true ensures the isolated config does NOT inherit
  │             the primary's processed tokens (no editor-brand leakage into
  │             project iframes)
  │
  └─ createElement(...)                 ← @symbo.ls/element/src/create.js
        – per-element @dark / @light / custom @name blocks compile to a
          single `[data-theme="<scheme>"] &` rule with `!important`.
          No `@media (prefers-color-scheme: …)` duplicate is emitted —
          the OS-preference listener in scratch.set flips `data-theme` live.
        – CSS injection routes through `getActiveDocument()`, which reads
          the document off the active scratch config (config stack), so a
          secondary app's CSS lands in its own document (e.g. an iframe).
        – All design-system token resolution uses `getActiveConfig()` /
          `pushConfig`/`popConfig` so multi-app pages stay isolated.
```

---

## Multi-app isolation

When multiple apps share a page (or live in nested iframes), each gets full design-system isolation:

### Config isolation

`prepareDesignSystem` detects secondary apps (`_designSystemInitialized` is already true) and creates an isolated scratch config via `createConfig(key, designSystem, { cleanBase: true })`. This config has its own:

- `cssVars` / `cssMediaVars` (separate from the primary app's)
- `themeRoot` (scoped to the app's own root element)
- `varPrefix` for CSS variable namespacing
- `scopeSelector` = `[data-smbls-app="<key>"]`
- `document` (the iframe's document, when applicable)

`cleanBase: true` is what prevents the primary's already-processed tokens from bleeding into the secondary — without it, an editor's brand theme would override the embedded project's design system.

The framework's `pushConfig`/`popConfig` mechanism ensures `getActiveConfig()` returns the right config at every code path:

| Code path | Scoping mechanism |
|-----------|-------------------|
| Element creation (`applyCssInProps`) | `pushConfig(context.designSystem)` at function entry |
| Reactive effects (function-valued CSS props) | `pushConfig(context.designSystem)` inside each `createEffect` |
| Reactive conditionals (`.X` / `!X` blocks) | `pushConfig(context.designSystem)` inside the conditional effect |
| Event handlers (delegated + non-delegated) | `pushConfig(context.designSystem)` in `delegate.js → wrappedHandler` |
| Async event handlers | Config stays pushed until the returned Promise settles via `.finally()` |
| Lifecycle hooks (onCreate, onRender, onMount, …) | `pushConfig(context.designSystem)` in `triggerLifecycle` |
| `onFrame` loop | `pushConfig(context.designSystem)` in each `requestAnimationFrame` tick |

### CSS injection isolation

`getActiveDocument()` resolves the target document from the active scratch config (`config.document`), set per-app in `prepareDesignSystem`. A per-document `WeakMap` cache in `@symbo.ls/css` ensures each document gets its own `<style data-smbls>` element.

`setActiveDocument(doc)` still exists as a backward-compat shim — it writes `doc` onto the currently active config. New code should use `pushConfig` with a config that already carries `document`.

### CSS prefix isolation

Secondary apps auto-derive a single `cssPrefix` (used for both atomic class names and CSS custom properties) from the app key:

```
cssPrefix = key.replace(/[^a-zA-Z0-9]/g, '').substring(0, 6)
```

| Key | cssPrefix | Atomic class | CSS var |
|-----|-----------|--------------|---------|
| `<no key>` (primary) | `''` | `._w-100` | `--theme-X-color` |
| `myapp` | `myapp` | `._myapp_w-100` | `--myapp-theme-X-color` |
| `dashboard` | `dashbo` | `._dashbo_w-100` | `--dashbo-theme-X-color` |
| `client-portal` | `client` | `._client_w-100` | `--client-theme-X-color` |

Primary apps use no prefix → identical output to single-app pages, fully backward compatible.

### themeRoot scoping

Each app's `themeRoot` points to its own root element:

```
Primary:    CONFIG.themeRoot = document.documentElement
Secondary:  CONFIG.themeRoot = doc.querySelector(`[data-smbls-app="<key>"]`)
            (caller passes `themeRoot` in options; framework respects it)
```

`changeGlobalTheme(theme)` writes `data-theme` to `CONFIG.themeRoot`, so each app's active theme is independent.

```js
create(appA, { ...ctxA, themeRoot: document.getElementById('app-a') })
create(appB, { ...ctxB, themeRoot: document.getElementById('app-b') })
```

For iframe-embedded apps, point `themeRoot` at the `[data-smbls-app="…"]` element inside the iframe so `data-theme` CSS vars override the base vars at the same specificity level.

---

## Full theme CSS table (emitted unconditionally)

`@symbo.ls/scratch/src/system/theme.js → generateAutoVars` emits the complete switching surface for every `@scheme` variant. The table below shows what lands in the document for one CSS var `--theme-X`:

```css
/* Primary app — :root scope, unprefixed vars */
:root                                 { --theme-X: <fallback>; }
[data-theme="light"]                  { --theme-X: <light-value>; }
[data-theme="dark"]                   { --theme-X: <dark-value>; }
[data-theme="ocean"]                  { --theme-X: <ocean-value>; }   /* custom schemes too */

/* OS-preference fallback for `light`/`dark` only — applies until
   `data-theme` is forced. After resolveAndApplyTheme runs, `data-theme`
   is always set, so this is mainly an SSR/no-JS safety net. */
@media (prefers-color-scheme: dark)  { :root:not([data-theme]) { --theme-X: <dark-value>; } }
@media (prefers-color-scheme: light) { :root:not([data-theme]) { --theme-X: <light-value>; } }

/* Secondary app (key `<key>`) — scoped to app element, prefixed vars */
[data-smbls-app="<key>"]              { --<prefix>-theme-X: <fallback>; }
[data-theme="light"]                  { --<prefix>-theme-X: <light-value>; }
[data-theme="dark"]                   { --<prefix>-theme-X: <dark-value>; }
```

The `:root` fallback picks the user's forced `globalTheme` value if any, else `light`, else the first resolvable scheme. A forced initial theme only decides which value lands in the fallback — runtime switching via `changeGlobalTheme` still works because every scheme's `[data-theme="X"]` rule is always emitted.

Custom schemes (`@ocean`, `@sunset`, …) activate via `data-theme` only; `prefers-color-scheme` only has `dark` / `light` semantics.

---

## Per-element `@dark` / `@light` / custom variants

`@dark`, `@light`, or any `@name` inside a DOMQL element compiles to a single `[data-theme="<scheme>"] &` rule with `!important`:

```js
ThemeToggle: {
  SunIcon: { display: 'none', '@dark': { display: 'inline-block' } },
  MoonIcon: { display: 'inline-block', '@dark': { display: 'none' } }
}
```

Compiles to:

```css
.<cls> { display: none; }                             /* SunIcon default */
[data-theme="dark"] .<cls> { display: inline-block !important; }
```

CSS updates atomically when `data-theme` flips — no JS reactivity required. This is the preferred pattern for theme-conditional UI (icon swaps, alt copy, etc.).

If `designSystem.media.dark` / `.light` happens to be defined, that definition is ignored for `@dark` / `@light` — those keys always take the theme-selector path, never the media-query path (otherwise we'd emit invalid `@media [data-theme="…"]` rules).

---

## `changeGlobalTheme(newTheme, targetConfig?)`

Exported from `smbls`. Operates on `targetConfig` if provided, otherwise the active CONFIG (from the push stack or singleton). On every call:

1. `CONFIG.globalTheme = newTheme`.
2. Resolves the target document (`CONFIG.document` || global `document`).
3. Writes `data-theme` to `CONFIG.themeRoot` (or the document's `documentElement` if `themeRoot` isn't set):
   - **Forced** (any value other than `'auto'`): writes `newTheme` directly and mirrors it to `root.style.colorScheme` (`'dark'`/`'light'`/`'light dark'` for custom schemes) so Chrome stops re-rendering form controls in the opposite UA scheme.
   - **`'auto'`**: reads current `prefers-color-scheme`, writes the resolved `'dark'`/`'light'` to `data-theme`, sets `colorScheme = 'light dark'`, and registers a one-time `change` listener on the media query so future OS toggles flip the attribute live (`CONFIG.__prefersListener` guards against double-registration).
4. Clears every theme-prefixed entry from `CONFIG.cssVars` (matching `--theme-` or `--<varPrefix>-theme-`) and clears all `CONFIG.cssMediaVars`.
5. Re-applies the updated `CONFIG.cssVars` to the scoped stylesheet rule (`:root` for primary, `[data-smbls-app="<key>"]` for secondary).

`changeGlobalTheme` does **not** persist `newTheme` to `localStorage`. If your project wants persistence, either wrap the call or add a `storeChosenTheme` step alongside it — `themeStorageKey` is read at init time only.

The optional `targetConfig` parameter enables cross-app theme control — e.g., an editor toolbar switching the embedded project's theme:

```js
import { changeGlobalTheme } from 'smbls'

// Switch the current app's theme (uses active config from the stack)
changeGlobalTheme('dark')

// Switch a specific app's theme (explicit config)
changeGlobalTheme('light', projectApp.context.designSystem)

// Re-enter OS-follow mode
changeGlobalTheme('auto')
```

Always prefer this over mutating state or writing `data-theme` by hand.

---

## Async boundaries

The config stack (`pushConfig`/`popConfig`) is synchronous. The framework already pushes around the async-prone surfaces:

- **Event handlers** (`delegate.js → wrappedHandler`) push the config on entry and pop on exit. If the handler returns a Promise, the pop is deferred to `.finally()` so continuations see the right config.
- **Lifecycle hooks** (`triggerLifecycle`) push the config around each `onCreate`/`onRender`/`onMount`/etc. invocation.
- **`onFrame`** loop pushes the config at the start of each `requestAnimationFrame` tick.

What the framework cannot wrap is project code that schedules work via `setTimeout`, `setInterval`, or `queueMicrotask` — those create new call stacks with no active config.

```js
// ❌ Timer callback loses config scope
onClick: (ev, el) => {
  setTimeout(() => {
    el.call('someFunction')  // getActiveConfig() returns the global singleton
  }, 100)
}

// ✅ Capture context up-front; access the document/window/designSystem
//    through it. Stable across async boundaries.
onClick: (ev, el) => {
  const ctx = el.context
  setTimeout(() => {
    // ctx.designSystem, ctx.document, ctx.window are stable references
  }, 100)
}
```

---

## Project rules (theme contract)

- **Never** write `setAttribute('data-theme', …)` from project code. The framework owns the attribute; touching it from userland creates race-conditions with scratch's OS-preference listener and breaks the CSS-var clear/re-apply cycle in `changeGlobalTheme`.
- **Never** write `dataset.theme = …`, `style.colorScheme = …`, or `style.setProperty('--theme-…', …)` from project code.
- **Never** store the active theme in root state or page state. Read from `el.context.globalTheme`, write via `changeGlobalTheme`.
- **Never** import `changeGlobalTheme` directly in project functions that are serialized (e.g. by `frank`). Use `el.call('switchTheme')` with a registered function that imports `changeGlobalTheme` itself, or that resolves the active config off `this.context` and calls into the framework's API directly.
- For UI that depends on the active theme (icon swap, alt copy, etc.), prefer pure-CSS via `@dark` / `@light` blocks. `data-theme` flips atomically — no signal plumbing needed.
- For persistence (remembering the user's last choice across reloads), pass `themeStorageKey: '<your-key>'` in options so `resolveAndApplyTheme` reads it back on init, AND write the new value to the same key whenever you call `changeGlobalTheme`. The framework only reads `themeStorageKey` at init; writes are the project's responsibility.
- **Keep `useDocumentTheme: true` in `config.js` (default).** When set to `false`, the design system's `theme.document` `@light`/`@dark` blocks DO NOT apply background/color to `<body>` — pages render against the browser's default white. Symptom: dark-mode flashes white-then-dark on first paint, or never goes dark at all.
- Resolution-influencing options:
  - `globalTheme: 'auto' | 'dark' | 'light' | '<custom>'`
  - `themeStorageKey: string | false` (set `false` to opt out of any localStorage read on init)
  - `themeRoot: HTMLElement` (scope for multi-DS pages and iframes)

---

# Part 2 — The Token Catalog

## Module structure

The set of `designSystem/*.js` files a project ships varies by complexity. Common module set (pick what you need):

| File | Purpose |
|------|---------|
| `color.js` | Named color palette (incl. opacity / theme-dependent variants) |
| `gradient.js` | Named gradient tokens |
| `theme.js` | Per-scheme blocks (`@light` / `@dark` / custom); semantic surface themes |
| `font.js` | Font definitions (size, weight, family) and `fontFace` strings |
| `font_family.js` | Family name → stack mapping (use `font_family` not `fontFamily` in config) |
| `typography.js` | Named typography presets + ratio config |
| `spacing.js` | Spacing scale (`A`, `B`, `C`, …) + ratio config |
| `timing.js` | Animation durations + easing curves |
| `animation.js` | `@keyframes` definitions |
| `media.js` | Custom media query breakpoints |
| `icons.js` | Inline SVG sprite (icon registry — required for Icon component) |
| `semantic_icons.js` | Logo/branding SVGs (NOT converted to sprite) |
| `svg.js` / `svg_data.js` | General SVG assets (decorative, not icons) |
| `shape.js` | Border-radius / shape presets |
| `shadow.js` | Named shadow presets (used via `shadow:` prop) |
| `grid.js` | Grid presets |
| `class.js` | Named CSS class shortcuts |
| `reset.js` | Project-specific CSS reset overrides |
| `vars.js` | CSS custom properties (custom vars) |
| `cases.js` | Conditional predicates for `$X` / `.X` / `!X` blocks (lives at root of `symbols/`, NOT inside `designSystem/`) |

Export pattern: lowercase keys are preferred (matches scratch's normalizer):

```js
// designSystem/index.js
import color from './color.js'
import theme from './theme.js'
import font from './font.js'
import font_family from './font_family.js'
import typography from './typography.js'
import spacing from './spacing.js'
import reset from './reset.js'

export default { color, theme, font, font_family, typography, spacing, reset }
```

UPPERCASE keys (`COLOR`, `THEME`, `FONT`, …) also work historically — scratch lowercases them internally before merging — but UPPERCASE is **deprecated and banned in new code** (Rule 0). Always lowercase.

---

## Token sequences — same letter, different value per family ⚠️

Symbols ratio-based families (typography, spacing, timing) all share the **same letter alphabet**: `... W < X < Y < Z < A < B < C < D < E < F ...` plus sub-tokens (`A1, A2, A3, B1, B2 …`).

But each family configures its own `{ base, ratio }`, so the **same letter resolves to a different absolute value in each family**. There are **NO custom-named spacing tokens** — every spacing value is generated from the sequence, not hand-named.

| Family | Default base | Default ratio | What "B" resolves to | Used by |
|---|---|---|---|---|
| `typography` | `16` (px) | `1.25` (major-third) | `~25 px` | `fontSize`, `lineHeight`, `letterSpacing` |
| `spacing` | `16` (px) | `1.618` (phi / golden) | `~26 px` | `padding`, `margin`, `gap`, `width`, `height`, `boxSize`, `top/right/bottom/left`, `borderRadius` / `round`, `borderWidth`, `outlineWidth`, etc. |
| `timing` | `150` (ms) | `1.333` (perfect-fourth) | `~200 ms` | `transition` duration, `animationDuration` |

**Why this matters:**

```js
// Same letter, three different absolute values:
{
  fontSize:    'B',   // ≈ 25 px   (typography sequence)
  padding:     'B',   // ≈ 26 px   (spacing sequence)
  transition:  'B'    // ≈ 200 ms  (timing sequence)
}
```

Don't reason about "the value of B" in the abstract — always ask **B in which family?** A common bug is assuming `padding: 'B'` matches `fontSize: 'B'` because the letters look paired; they don't.

**Sub-tokens (`A1`, `A2`, `B1`, …) follow the same rule** — they're minor increments within their own family's sequence. `padding: 'A1'` and `fontSize: 'A1'` are different values.

**Custom tokens are NOT a thing for spacing/typography/timing.** Don't write `spacing: { gutterSm: 12, gutterMd: 24 }` and reference `padding: 'gutterSm'` — the design system doesn't honor custom names in these families. Pick the right letter from the sequence (or tweak `base` / `ratio` to shift the whole scale). For named values you'd reach for `colors`, `themes`, `shadows`, `gradients` — those families ARE name-based.

---

## color

### Define each color ONCE; use modifiers for shades

**Define each color as a named token** in `designSystem/color.js`. Never use raw `#hex`, `rgb()`, `rgba()` in component CSS. Generate all shades dynamically using modifiers — never define multiple shade variants of the same color (no `blue100`, `blue200`, `blue300` Tailwind-style palettes).

### Token grammar

```
<colorName>(.<alphaDigits>)?(<+N|-N|=N>)?
```

Verified at `packages/scratch/src/utils/color.js:180` (regex `/^([a-zA-Z]\w*)(?:\.(\d+))?(?:([+-]\d+|=\d+))?$/`).

| Modifier | Syntax | Example | Effect |
|----------|--------|---------|--------|
| Opacity | `.XX` | `'blue.7'` | 70% opacity (`0.XX` → `'.1'` = 0.1, `'.35'` = 0.35, `'.97'` = 0.97). Verified at `color.js:206` (`alpha = '0.' + alphaDigits`). |
| Lighten | `+N` | `'gray+50'` | Lighten by N (HSL lightness, **relative**) |
| Darken | `-N` | `'gray-68'` | Darken by N (HSL lightness, **relative**) |
| Absolute | `=N` | `'gray=90'` | Set HSL lightness to N% (**absolute**) |
| Combined | `.XX+N` | `'gray.85+8'` | 85% opacity + lighten by 8 (lightness) |

```js
// ✅ CORRECT — one base color, shades via modifiers
color: {
  blue: '#0474f2',
  gray: '#4e4e50',
}

// Use in components:
background: 'blue'       // base
background: 'blue.8'     // 80% opacity
background: 'blue+20'    // lightened
background: 'blue-30'    // darkened
color: 'gray.5+15'       // 50% opacity + 15 lighter
borderColor: 'gray+100'  // light gray border

// ❌ WRONG — Tailwind-style shade palette
color: {
  blue50: '#eff6ff', blue100: '#dbeafe', blue200: '#bfdbfe',
  blue300: '#93c5fd', blue400: '#60a5fa', blue500: '#3b82f6',
}
```

**Border-color resolution:** `borderTopColor`, `borderBottomColor`, `borderLeftColor`, `borderRightColor` resolve theme tokens just like `color` / `background`.

### Static colors (default starter set)

| Token | Value | Use |
|---|---|---|
| `blue` | `#213eb0` | Primary interactive |
| `green` | `#389d34` | Success states |
| `red` | `#e15c55` | Warning/error states |
| `yellow` | `#EDCB38` | Attention states |
| `orange` | `#e97c16` | Accent states |
| `black` | `black` | Pure black |
| `white` | `white` | Pure white |
| `gray` | `#4e4e50` | Neutral mid-tone |
| `transparent` | `rgba(0, 0, 0, 0)` | Fully transparent |

### Adaptive semantic colors (array syntax)

Array syntax `[darkValue, lightValue]` defines a token that resolves differently per active theme. Values prefixed with `--` are **color references** in the form `'--colorName opacity tone'` (NOT CSS variables — the `--` is a parser hint).

```js
title: ['--gray 1 -168', '--gray 1 +168'],
//       ↑name  ↑alpha ↑tone
// Dark: gray at full opacity, darkened by 168 (lightness)
// Light: gray at full opacity, lightened by 168 (lightness)
```

| Token | Dark | Light | Use |
|---|---|---|---|
| `title` | `'--gray 1 -168'` | `'--gray 1 +168'` | Primary text |
| `caption` | `'--gray 1 -68'` | `'--gray 1 +68'` | Secondary/meta |
| `paragraph` | `'--gray 1 -42'` | `'--gray 1 +42'` | Body copy |
| `disabled` | `'--gray 1 -26'` | `'--gray 1 +26'` | Disabled state |
| `line` | `'--gray 1 -16'` | `'--gray 1 +16'` | Borders/dividers |

### Theme-dependent named tokens

When a value depends on the active scheme, define it once in `color.js` (or as `@dark`/`@light` blocks in `theme.js`) and reference the named token in components — don't hand-write rgba per-component:

```js
// designSystem/color.js
whiteLight:  'rgba(255,255,255,0.1)',
whiteBorder: 'rgba(255,255,255,0.35)',
blackMuted:  'rgba(0,0,0,0.35)',
bgWarm:      '#f6f4f3',
```

### Branded core tokens — always pair with explicit `theme.document` overrides

If a brand customizes the core color tokens (`color.black`, `color.white`, `color.neutral`, …) to tinted values, every `theme.X` block that defaults to `'black'` / `'white'` / bare `'neutral'` will resolve to the tinted variant. For surfaces this is usually wrong — a green-brand tinted "black" `#10241A` for `theme.document.@dark.background` makes the whole page take that tint instead of a true neutral.

Always pair branded core tokens with explicit `theme.document` (and any other surface theme) blocks that step away from the tinted base via the modifier system (`+N` lighter, `-N` darker, `=N` absolute):

```js
// designSystem/color.js — brand-tinted base, intentionally
black:   '#10241A'
white:   '#F4FBF6'

// designSystem/theme.js — surfaces step the base via modifiers,
// NOT inheriting the bare tint
document: {
  '@light': { background: 'neutral+45',  color: 'neutral-45' },
  '@dark':  { background: 'neutral-45',  color: 'neutral+45' }
}
```

Use modifier expressions (`neutral+20`, `neutral-30`, `neutral=50`) for page / panel / card surfaces. Reserve bare `color.black` / `color.white` for places where the brand tint is intentional (logo, accent strokes, etc.). Letting a brand tint propagate everywhere through default theme inheritance is one of the most common "why is the dark mode greenish-tinted on prod?" classes of bug.

### Opacity rules

- `.XX` = `0.XX` — `.1` = 0.1, `.35` = 0.35, `.0` = 0.0
- Full opacity (1.0) = no modifier needed
- Raw CSS values (`rgba()`, `hsl()`, `#hex`) pass through unchanged
- CSS variables (`--myVar`) convert to `var(--myVar)`

---

## gradient

| Token | Description |
|---|---|
| `gradient-blue-light` | Linear blue-to-dark-blue |
| `gradient-blue-dark` | Linear blue gradient (hex) |
| `gradient-dark` | Subtle dark overlay |
| `gradient-dark-active` | Stronger dark overlay (active state) |
| `gradient-light` | Subtle light overlay |
| `gradient-light-active` | Stronger light overlay (active state) |
| `gradient-colorful` | Multi-color gradient (blue-purple-pink) |

```js
Hero: { background: 'gradient-colorful' }
Button: { background: 'gradient-blue-dark' }
```

Gradients with color tokens inside are auto-resolved via `resolveColorsInGradient()`.

---

## theme

Apply with `theme: 'name'`. Themes define `background` + `color` pairs per dark/light mode (and any custom scheme).

`designSystem/theme.js` keys carry `@light` / `@dark` (and any custom scheme) blocks per token. Each scheme's value compiles to one CSS var; the value used at runtime is selected by the `data-theme` attribute (see Part 1 → Pipeline).

```js
// designSystem/theme.js — values can be base tokens or modifier expressions
export default {
  document: {
    '@light': { background: 'neutral+45',  color: 'neutral-45' },
    '@dark':  { background: 'neutral-45',  color: 'neutral+45' }
  },
  panel: {
    '@light': { background: 'white',       color: 'neutral-40' },
    '@dark':  { background: 'neutral-40',  color: 'white'      }
  }
}
```

### Surface themes (default set)

| Theme | Use |
|---|---|
| `document` | Page root surface (black/white) |
| `dialog` | Elevated card/panel with glass blur |
| `card` | Card surface with `.child` and `.secondary` variants |
| `field` | Input control surface with `::placeholder` |
| `label` | Label surface with `.light` and `.dark` variants |
| `transparent` | No background, inherits text color |
| `none` | Resets both color and background to `none` |

### Priority themes

| Theme | Use |
|---|---|
| `primary` | CTA: blue/gradient background, white text; `.color-only`, `.inactive`, `.gradient` variants |
| `secondary` | Green background, white text; `.color-only` variant |
| `tertiary` | Subtle gray background |
| `quaternary` | Gradient overlay background |
| `quinary` | Interactive with `:hover`, `:focus`, `:active`, `.active` states |

### State themes

| Theme | Use |
|---|---|
| `alert` | Red background (destructive) |
| `warning` | Yellow background (caution) |
| `success` | Green background (positive) |

```js
Page:   { flow: 'y', theme: 'document', minHeight: '100dvh' }
Card:   { flow: 'y', theme: 'dialog', round: 'A', padding: 'A' }
Input:  { theme: 'field' }
Button: { theme: 'primary', text: 'Save' }
Badge:  { theme: 'alert', text: 'Error' }
```

### Variant modifiers (dot-notation)

```js
Button: { theme: 'primary', '.gradient': true }  // gradient variant
Card:   { theme: 'card', '.secondary': true }    // secondary variant
Label:  { theme: 'label', '.dark': true }        // dark variant
```

### `themeModifier`

Force a color scheme regardless of global theme:

```js
DarkSection: { themeModifier: 'dark', theme: 'document' }
LightCard:   { themeModifier: 'light', theme: 'card' }
```

### Custom theme definition

```js
theme: {
  button: {
    color: 'text',
    background: 'primary',
    ':hover':  { background: 'primary.85' },
    ':active': { background: 'primary.75' },
    '@dark':   { background: 'primary.6' },
    '@light':  { background: 'blue' },
    '.active': { background: 'primary' }
  }
}
```

---

## typography

Scale generated from ratio (Major Third = 1.25 default).

| Token range | Approx size | Use |
|---|---|---|
| `W`-`W2` | ~8-10 px | Micro text |
| `Z`-`Z2` | ~10-12 px | Caption, footnote |
| `Y`-`A` | ~12-16 px | Body text, small headings |
| `A1`-`B` | ~18-24 px | Headings, large body |
| `B1`-`C` | ~28-40 px | Display headings |
| `C1`-`C2` | ~48-64 px | Hero headlines |

```js
Heading: { fontSize: 'C' }
Caption: { fontSize: 'Z2' }
Body:    { fontSize: 'A' }
```

Config:

```js
typography: { base: 16, ratio: 1.25, subSequence: true }
```

### Sequence ratios

| Name | Value |
|---|---|
| `minor-second` | 1.067 |
| `major-second` | 1.125 |
| `minor-third` | 1.2 |
| `major-third` | 1.25 |
| `perfect-fourth` | 1.333 |
| `augmented-fourth` | 1.414 |
| `perfect-fifth` | 1.5 |
| `minor-sixth` | 1.6 |
| `phi` | 1.618 |
| `major-sixth` | 1.667 |
| `minor-seventh` | 1.778 |
| `major-seventh` | 1.875 |
| `octave` | 2 |

### `fontWeight`

Auto-sets `fontVariationSettings` for variable fonts:

```js
Title: { fontWeight: 700 }
// outputs: fontWeight: 700, fontVariationSettings: '"wght" 700'
```

---

## spacing

Golden Ratio scale (1.618 default). Applies to `padding`, `margin`, `gap`, `width`, `height`, `boxSize`, `borderRadius`/`round`, `inset`, `top`, `left`, `right`, `bottom`, etc.

### Token stepping system

Each letter is a major step. Sub-numbers are minor increments between letters. The sequence flows continuously — each sub-step is one tone increase:

```
... X < X1 < X2 < Z < Z1 < Z2 < A < A1 < A2 < A3 < B < B1 < B2 < B3 < C ...
```

How many sub-steps exist between letters depends on the range — smaller ranges (W, X) have only 1-2 sub-steps, larger ranges (A, B, C) have up to 3.

**To increase slightly:** go up one sub-step (e.g. `A` → `A1`, or `B2` → `B3`)
**To increase moderately:** go up one letter (e.g. `A` → `B`)
**To decrease:** reverse direction (e.g. `B` → `A3`, or `A` → `Z2`)

| Token range | Approx px | Use |
|---|---|---|
| `W`-`W2` | 2-4 | Micro gaps, offsets |
| `X`-`X2` | 4-6 | Icon padding, tight gaps |
| `Z`-`Z2` | 10-16 | Compact padding |
| `A`-`A3` | 16-26 | Default padding, gutters |
| `B`-`B3` | 26-42 | Section padding |
| `C`-`C3` | 42-68 | Container padding, avatar sizes |
| `D`-`D3` | 68-110 | Large sections |
| `E`-`F` | 110-178 | Hero padding, max-widths |

Typography tokens use the same letter system for `fontSize`.

### Shorthand spacing

```js
padding: 'A'           // all sides
padding: 'A B'         // vertical | horizontal
padding: 'A B C'       // top | horizontal | bottom
padding: 'A B C D'     // top | right | bottom | left
margin: '- - - auto'   // use '-' to skip a side
```

### Math in spacing

```js
Box: { padding: 'A+Z', margin: '-B', width: 'C+Z2' }
```

### Compound spacing

```js
padding: 'F+X2 - - -'    // top = F + 2*X, skip others
margin: 'D2+Y2 - B2+W -' // complex with multipliers
```

Config:

```js
spacing: { ratio: 1.618, subSequence: true }
```

### `flow:` and `align:` shorthands

Both are valid in v4+ (resolved by the shorthand plugin / scratch transforms):

- `flow: 'y'` ≡ `flexFlow: 'column'`
- `flow: 'x'` ≡ `flexFlow: 'row'`
- `align: 'center center'` ≡ `alignItems: center; justifyContent: center` (space-separated)

Either form works — pick one and stay consistent.

---

## borders

The framework supports the `border:` shorthand — `packages/scratch/src/transforms/index.js:37` (`transformBorder`) parses space-separated tokens, resolves color tokens via `getColor`, accepts spacing keys, CSS vars, and CSS keywords. Use the shorthand freely for static, hand-written borders:

```js
// ✅ Shorthand — works, color token resolves
border: '1px solid border'
border: 'A solid neutral-30'
```

Use the split form when you need to make a single field reactive without recomputing the whole shorthand string, or when the color depends on theme/state and you want the css-in-props color resolver to apply per field:

```js
// ✅ Split — granular reactivity
borderWidth: '1px',
borderStyle: 'solid',
borderColor: (el, s) => s.active ? 'primary' : 'border'
```

Both forms are valid.

---

## shadows

`packages/scratch/src/transforms/index.js:88` (`transformBoxShadow`) follows the CSS shadow grammar exactly:

- **Within a single shadow:** space-separated tokens (`<offsetX> <offsetY> <blur>? <spread>? <color>? inset?`).
- **Between multiple shadows:** comma-separated.

Each token is resolved through the framework's value resolver: spacing keys (`A`, `B`, `C`, …), CSS vars, color tokens (`black.35`, `primary+10`), CSS units, and the `inset`/`none` keywords.

```js
// ✅ Single shadow — space-separated tokens
boxShadow: '0 0 C3 black.35'
boxShadow: '0 A B primary.2'

// ✅ Multiple shadows — comma-separated, each space-internal
boxShadow: '0 1px 2px black.1, 0 4px 8px black.05'

// ❌ Forbidden — comma WITHIN a single shadow is invalid CSS
boxShadow: '0, 0, C3, black .35'
```

Color tokens inside shadows resolve via `getColor`, so opacity dot-notation (`black.35`) and tone modifiers (`primary+10`) both work without defining a separate named token in `color.js`.

Use named shadow tokens via the `shadow:` prop — they live in `designSystem/shadow.js`:

```js
shadow: {
  soft: 'black.15 0px 10px 30px 0px',
  hard: ['black.25 0px 8px 16px 0px', 'black.35 0px 10px 24px 0px']  // [light, dark]
}
// component:
Card: { shadow: 'soft' }
```

---

## timing

| Token | Value | Use |
|---|---|---|
| `defaultBezier` | `cubic-bezier(.29, .67, .51, .97)` | Smooth ease-out |

Scale: `base: 150, ratio: 1.333` (perfect-fourth). Duration tokens use the same letter sequence (A, B, C...) in milliseconds.

```js
Box: { transition: 'B defaultBezier', transitionProperty: 'opacity, transform' }
```

`transition` supports comma-separated multi-transition values via smart splitting.

---

## animation

The scratch default animation config is empty — define your own in `designSystem/animation.js`. The default template includes `fadeInUp`, `fadeOutDown`, and `marquee`.

### CSS shorthand syntax

```js
Modal:  { animation: 'fadeIn 2s ease-in-out' }
Ticker: { animation: 'marquee 8s linear infinite' }
Spinner:{ animation: 'spin 1s linear infinite alternate' }
```

Parser token identification:
- **Name**: looked up in `ANIMATION` registry
- **Duration**: `Xs`, `Xms` (first = duration, second = delay)
- **Timing**: `ease`, `linear`, `ease-in-out`, `cubic-bezier(...)`, `steps(...)`
- **Iteration**: `infinite` or number
- **Direction**: `normal`, `reverse`, `alternate`, `alternate-reverse`
- **Fill mode**: `none`, `forwards`, `backwards`, `both` (default: `both`)
- **Play state**: `running`, `paused`

### Individual animation properties

```js
Box: {
  animationName: 'fadeIn',
  animationDuration: 'B',
  animationDelay: 'A',
  animationTimingFunction: 'ease-in-out',
  animationIterationCount: 'infinite',
  animationFillMode: 'both',
  animationDirection: 'alternate',
  animationPlayState: 'running'
}
```

### Inline keyframes

```js
Box: {
  animation: {
    from: { opacity: 0, transform: 'translateY(20px)' },
    to:   { opacity: 1, transform: 'translateY(0)' }
  }
}
```

### Custom animation in designSystem

```js
animation: {
  fadeInUp: {
    from: { opacity: 0, transform: 'translateY(12.5%)' },
    to:   { opacity: 1, transform: 'translateY(0)' }
  },
  marquee: {
    from: { transform: 'translateX(0)' },
    to:   { transform: 'translateX(-50%)' }
  }
}
```

---

## media

The scratch default config includes only 4 media tokens. The responsive breakpoints are added by the framework automatically.

### Default media tokens (from scratch)

| Token | Query |
|---|---|
| `tv` | `min-width: 2780px` |
| `light` | `prefers-color-scheme: light` |
| `dark` | `prefers-color-scheme: dark` |
| `print` | `print` |

### Responsive breakpoints (auto-generated)

| Token | Query | Direction |
|---|---|---|
| `screenL` | `max-width: 1920px` | down |
| `screenM` | `max-width: 1680px` | down |
| `screenS` | `max-width: 1440px` | down |
| `tabletL` | `max-width: 1366px` | down |
| `tabletM` | `max-width: 1280px` | down |
| `tabletS` | `max-width: 1024px` | down |
| `mobileL` | `max-width: 768px` | down |
| `mobileM` | `max-width: 560px` | down |
| `mobileS` | `max-width: 480px` | down |
| `mobileXS` | `max-width: 375px` | down |

`<` suffix = min-width (upward): `tabletL<` = `min-width: 1366px`. All breakpoints have both `max-width` and `min-width` (`<`) variants.

Custom media tokens can be added in `designSystem/media.js`.

```js
Grid: {
  columns: 'repeat(4, 1fr)',
  '@tabletS': { columns: 'repeat(2, 1fr)' },
  '@mobileL': { columns: '1fr' }
}
Box: {
  '@dark':  { background: 'codGray' },
  '@light': { background: 'concrete' }
}
```

---

## icons & SVG

```js
icons: {
  search: '<svg>...</svg>'    // converted to sprite
},
semantic_icons: {
  logo: true                   // NOT converted to sprite (used as-is)
},
svg: {
  logo: '<svg>...</svg>'       // general SVG assets (decorative)
}
```

Default icon set: `symbols`, `logo`, arrow variants, `check`, `checkCircle`, chevron variants, `copy`, `eye`, `eyeOff`, `info`, `lock`, `minus`, `plus`, `search`, `send`, `smile`, `star`, `sun`, `moon`, `upload`, `video`, `x`, `moreHorizontal`, `moreVertical`.

### Icon usage in components — STRICT (Rule 29 / Rule 62)

**ALWAYS use the `Icon` component referencing `designSystem.icons` by name.** Inline SVG via `html: '<svg ...>'` for icons is FORBIDDEN — bypasses the design system, breaks theme color resolution, breaks SSR, breaks brender hydration, duplicates SVG strings across components.

```js
// ✅ Correct
SearchBtn: { Icon: { name: 'search' } }
LogoMark:  { extends: 'Icon', icon: 'logo' }

// ❌ FORBIDDEN — html: SVG markup for an icon
HiddenIcon: { html: '<svg viewBox="0 0 24 24"><path d="..." /></svg>' }

// ❌ FORBIDDEN — tag: 'svg' inline component
InlineIcon: { tag: 'svg', viewBox: '0 0 24 24', children: [{ tag: 'path', attr: { d: '...' } }] }
```

If the icon doesn't exist in `designSystem/icons` yet, **add it there first**, then reference by name. Never inline. The `Icon` component handles size, color (resolves theme tokens), accessibility, and sprite rendering.

`Svg` component is for **decorative SVG backgrounds** (illustrations, hero patterns) — NOT for icons. Decorative SVG data lives in `designSystem/svg.js` / `svg_data.js`.

---

## cases

Cases are defined in `symbols/cases.js` (NOT in `designSystem/`) and added to `context.cases`. They are functions that evaluate conditions globally or per-element.

### Defining cases

```js
// symbols/cases.js
export default {
  isSafari: () => /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent),
  isGeorgian () { return this?.state?.root?.language === 'ka' },
  isMobile: () => window.innerWidth < 768
}

// symbols/context.js
import cases from './cases.js'
export default { cases, /* ...other context */ }
```

Case functions receive `element` as `this` (and first arg), but must work without it (for global detection like `isSafari`).

### Using cases in components

```js
// $ prefix — global case from context.cases
Element: { $isSafari: { top: 'Z2', right: 'Z2' } }

// . prefix — props/state first, then context.cases
Button: { '.isActive': { background: 'blue', aria: { expanded: true } } }

// ! prefix — inverted
Card: { '!isMobile': { maxWidth: '1200px' } }
```

Cases work in both CSS props (css-in-props) and HTML attributes (attrs-in-props).

---

## CSS Custom Properties (vars)

Define initial CSS custom properties in designSystem:

```js
vars: {
  '--header-height': '60px',
  'sidebar-width': '280px',   // auto-prefixed to --sidebar-width
  gap: '1rem'                  // becomes --gap
}
```

Reference in props: `padding: '--gap'` → resolves to `var(--gap)`. Any `--` prefixed value is auto-wrapped in `var()`.

---

## fonts

### Variable font (Google Fonts)

```js
font: {
  Inter: {
    url: 'https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap',
    isVariable: true,
    fontWeight: '100 900'
  }
}
```

### Variable font (self-hosted)

```js
font: {
  Inter: { url: '/fonts/Inter-Variable.woff2', isVariable: true, fontWeight: '100 900' }
}
```

### Traditional per-weight files

```js
font: {
  inter: [
    { url: '/fonts/Inter-Regular.woff2', fontWeight: 400 },
    { url: '/fonts/Inter-Bold.woff2', fontWeight: 700 }
  ]
}
```

### Multiple format fallbacks (array URL)

```js
font: {
  Exo2: [
    {
      url: ['Exo2-Medium.woff2', 'Exo2-Medium.woff'],
      fontWeight: '500',
      fontStyle: 'normal',
      fontDisplay: 'swap'
    }
  ]
}
```

Generates comma-separated `src` with auto-detected formats per URL.

---

# Part 3 — CSS-in-Props Shorthands

Quick reference for the shorthand props the design system exposes.

## Layout

| Prop | Effect |
|---|---|
| `flow` | `display: flex` + `flexFlow` (`'x'`=row, `'y'`=column) |
| `wrap` | `display: flex` + `flexWrap` |
| `align` | `display: flex` + `alignItems justifyContent` (space-separated) |
| `round` | Alias for `borderRadius` with spacing tokens |
| `boxSize` | `height width` (space-separated) |
| `size` | `inlineSize blockSize` (space-separated) |
| `widthRange` | `minWidth maxWidth` (space-separated) |
| `heightRange` | `minHeight maxHeight` (space-separated) |
| `minSize` | `minInlineSize minBlockSize` (space-separated) |
| `maxSize` | `maxInlineSize maxBlockSize` (space-separated) |
| `show` | If returns `false`, sets `display: none !important` |
| `hide` | If truthy, sets `display: none !important` |
| `shadow` | Resolves named shadow token from designSystem, outputs `boxShadow` |
| `verticalInset` | `top bottom` (space-separated) |
| `horizontalInset` | `left right` (space-separated) |
| `paddingBlock` | `paddingBlockStart paddingBlockEnd` |
| `paddingInline` | `paddingInlineStart paddingInlineEnd` |
| `marginBlock` | `marginBlockStart marginBlockEnd` |
| `marginInline` | `marginInlineStart marginInlineEnd` |

## Grid

| Prop | CSS Output |
|---|---|
| `area` | `gridArea` |
| `template` | `gridTemplate` |
| `templateAreas` | `gridTemplateAreas` |
| `column` | `gridColumn` |
| `columns` | `gridTemplateColumns` |
| `templateColumns` | `gridTemplateColumns` |
| `autoColumns` | `gridAutoColumns` |
| `columnStart` | `gridColumnStart` |
| `row` | `gridRow` |
| `rows` | `gridTemplateRows` |
| `templateRows` | `gridTemplateRows` |
| `autoRows` | `gridAutoRows` |
| `rowStart` | `gridRowStart` |
| `autoFlow` | `gridAutoFlow` |

## Color/Border/Shadow

| Prop | Behavior |
|---|---|
| `color` | Resolves color token (theme-aware) |
| `background` | Resolves color or gradient token (theme-aware) |
| `backgroundColor` | Resolves color token (theme-aware) |
| `backgroundImage` | Resolves gradient with color tokens; supports file lookup |
| `borderColor` | Resolves color token (theme-aware) |
| `borderTopColor` | Resolves color token (theme-aware) |
| `borderBottomColor` | Resolves color token (theme-aware) |
| `borderLeftColor` | Resolves color token (theme-aware) |
| `borderRightColor` | Resolves color token (theme-aware) |
| `border` | Parses `width style color` with token resolution |
| `borderTop`/`Bottom`/`Left`/`Right` | Same parsing as `border` |
| `outline` | Same parsing as `border` |
| `textStroke` | Sets `WebkitTextStroke` with color resolution |
| `shadow` | Resolves named shadow from designSystem |
| `boxShadow` | Parses shadow with color token resolution |
| `textShadow` | Parses shadow with color token resolution |
| `columnRule` | Same parsing as `border` |

## Misc

| Prop | Behavior |
|---|---|
| `overflow` | Also sets `scrollBehavior: 'smooth'` |
| `cursor` | Supports file lookup for custom cursor images |
| `transitionProperty` | Also sets `willChange` to same value |

---

## Pseudo-selectors & states in props

```js
Button: {
  theme: 'primary',
  ':hover':       { opacity: '0.85' },
  ':active':      { opacity: '0.75' },
  ':focus':       { outline: 'solid X primary' },
  '::placeholder':{ color: 'gray+68' },
  '.isActive':    { theme: 'primary', background: 'blue' },
  '.disabled':    { opacity: '0.5', pointerEvents: 'none' },
  '@dark':        { background: 'darkBlue' },
  '@mobileL':     { fontSize: 'Z' }
}
```

### CSS combinator selectors in props

```js
Container: {
  '> *:not(:first-child)': { marginTop: 'A' },
  '+ div': { paddingTop: 'B' }
}
```

---

## Transition properties

```js
Box: {
  transition: 'B defaultBezier',
  transitionProperty: 'opacity, transform',  // also sets willChange
  transitionDuration: 'A',
  transitionDelay: 'Z',
  transitionTimingFunction: 'ease-in-out'
}
```

`transition` supports comma-separated multi-transition values via smart splitting.

---

# Part 4 — Configuration

## Full config example

```js
const designSystemConfig = {
  color: {
    primary: '#1f6feb',
    text:    ['#0b0b0b', '#f5f5f5'],   // [dark, light] adaptive
    accent:  { '@light': '#ff7a18', '@dark': '#ffb347' }
  },
  gradient: {
    'my-gradient': 'linear-gradient(to right, #ff7a18, #ffb347)'
  },
  theme: {
    document: { color: 'text', background: 'primary.02' },
    button: {
      color: 'text',
      background: 'primary',
      ':hover':  { background: 'primary.85' },
      '@dark':   { background: 'primary.6' },
      '.active': { background: 'primary' }
    }
  },
  typography: { base: 16, ratio: 1.25, subSequence: true },
  spacing:    { ratio: 1.618, subSequence: true },
  timing:     { base: 150, ratio: 1.333, unit: 'ms', subSequence: true },
  font: {
    Inter: { url: '/fonts/Inter-Variable.woff2', isVariable: true, fontWeight: '100 900' }
  },
  font_family: {
    primary: { value: ['Inter'], type: 'sans', isDefault: true },
    system:  { value: ['"Helvetica Neue"', 'Helvetica', 'Arial'], type: 'sans-serif' }
  },
  icons: { search: '<svg>...</svg>' },
  svg:   { logo: '<svg>...</svg>' },
  shadow: {
    soft: 'black.15 0px 10px 30px 0px',
    hard: ['black.25 0px 8px 16px 0px', 'black.35 0px 10px 24px 0px']  // [light, dark]
  },
  animation: {
    fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } }
  },
  media: {
    mobile: '(max-width: 768px)',
    desktop: '(min-width: 1024px)'
  },
  useVariable:       true,
  useReset:          true,
  useFontImport:     true,
  useIconSprite:     true,
  useDocumentTheme:  true,
  useDefaultConfig:  true,
  globalTheme: 'dark'  // 'dark', 'light', or 'auto'
}
```

### Valid top-level config keys

```
color, gradient, theme, typography, spacing, timing,
font, font_family, icons, semantic_icons, svg, svg_data,
shadow, media, grid, class, reset, unit, animation, vars
```

Do NOT wrap these under `props` or other wrappers.

## Design system flags

| Flag | Default | Effect |
|---|---|---|
| `useReset` | `true` | Apply CSS reset |
| `useVariable` | `true` | Emit CSS custom properties for all tokens |
| `useFontImport` | `true` | Load font entries via @font-face |
| `useIconSprite` | `true` | Inline the icons SVG sprite into the DOM |
| `useSvgSprite` | `true` | Inline SVG sprite definitions |
| `useDefaultConfig` | `true` | Merge smbls default design system config |
| `useDocumentTheme` | `true` | Apply document theme to `<html>` |
| `useDefaultIcons` | `true` | Include default icon set |
| `verbose` | `false` | Suppress design system debug output |

---

## Project config (top-level)

```js
// config.js — influences the resolver only; the runtime store comes
// from scratch CONFIG.
export default {
  useDocumentTheme: true,
  globalTheme: 'auto',
  themeStorageKey: 'my-app-theme'
}
```

---

## Switching theme at runtime — registered project function

```js
// functions/switchTheme.js — import-safe at module top
import { changeGlobalTheme } from 'smbls'

export function switchTheme () {
  const current = this.context.globalTheme === 'dark' ? 'light' : 'dark'
  changeGlobalTheme(current, this.context.designSystem)
  try {
    (this.context.window || window).localStorage.setItem('my-app-theme', current)
  } catch (e) {}
}
```

Wired in components:

```js
ThemeToggle: {
  extends: 'Button',
  onClick: (e, el) => el.call('switchTheme')
}
```

From editor/framework code (import-safe):

```js
import { changeGlobalTheme } from 'smbls'
changeGlobalTheme('dark')                                     // forced
changeGlobalTheme('auto')                                     // OS-follow
changeGlobalTheme('ocean')                                    // custom scheme — must exist in designSystem/theme.js
changeGlobalTheme('light', otherApp.context.designSystem)     // cross-app targeting
```

---

# Part 5 — Runtime APIs

```js
import { init, reinit, applyCSS, updateVars } from 'smbls'

init(designSystemConfig)                       // Setup design system (called once by create())
reinit(updatedConfig)                          // Update design system at runtime
applyCSS('.my-class { color: red }')           // Inject raw CSS
updateVars({ color: { primary: '#ff0000' } })  // Update CSS variables only
```

---

# Part 6 — Common mistakes (design-system-specific)

- **NEVER use UPPERCASE keys** (`COLOR`, `THEME`, `TYPOGRAPHY`, etc.) — always lowercase. UPPERCASE is deprecated and banned (Rule 0).
- Do NOT nest config under `props` or other wrappers.
- Use `font_family` (snake_case) not `fontFamily` in config.
- Define `typography` and `spacing` if you use tokens like `A`, `B2`, or `C+Z`.
- Use named color tokens, not raw hex, for all interactive/semantic colors (Rule 27).
- Dot-notation for opacity: `color: 'white.7'` (not `'white .7'` with space).
- `flow: 'x'` or `flow: 'y'` (not `flow: 'row'` or `flow: 'column'` — though those work too).
- `align: 'center center'` (space-separated: alignItems justifyContent).
- `round` is the shorthand for `borderRadius` with spacing-token support.
- `shadow` resolves from designSystem; `boxShadow` takes raw shadow syntax with color tokens.
- `backdropFilter` must use `style: { backdropFilter: 'blur(10px)' }` to avoid text leak (css-in-props bug on this specific property).
- Colors in `border` syntax: `border: '1px solid gray.5'` — the color token is resolved.
- **NEVER inline SVG via `html:` for icons** — use `Icon` component referencing `designSystem.icons` (Rule 29 / Rule 62).
- **NEVER write `setAttribute('data-theme', …)` from project code** — `changeGlobalTheme()` only (Rule 50).
- **NEVER store `globalTheme` / `theme` / `darkMode` in root state** — read from `el.context.globalTheme` (Rule 50).
- **Branded core colors** — pair every brand-tinted base (`color.black: '#10241A'`) with explicit `theme.document.@dark` / `@light` overrides using `neutral+45` / `neutral-45` modifiers. Otherwise the tint propagates to every surface.
