# Default Symbols Project Template

The default starter (`smbls create` → "Default" option) ships with a curated component library AND a recommended design system. This document covers both.

Two parts:

1. **Library overview** — the 127+ pre-built components that come with the default template, organized by category, with extension chain semantics.
2. **Pre-configured design system tokens** — exact values for typography, spacing, color, theme, font_family, timing, animation, cases — the recommended baseline for any new project.

> For the full source code of every default component, see DEFAULT_COMPONENTS.md.

---

# Part 1 — Library Overview

The default library (`default.symbo.ls`) provides 127+ pre-built, production-ready components — flat element API, signal reactivity. Included automatically when creating projects via `smbls create` (Default option) or the Symbols platform. Choose "Blank" for an empty project.

> Reference these by PascalCase string key in your components — `extends: 'Button'`, `extends: 'IconButton'`, etc. NEVER import them. The PascalCase auto-extend mechanism resolves them through `context.components`.

## Component tables

### Atoms (Foundation)

| Component | Extends | Purpose |
|---|---|---|
| `Box` | — | Generic container with CSS-in-props |
| `Text` | — | Text rendering (H1-H6, P, Caption, etc.) |
| `Flex` | `Box` | Flexbox layout |
| `Grid` | `Box` | CSS Grid layout |
| `Form` | `Box` | Form container |
| `Hgroup` | `Flex` | Heading group |
| `Img` | — | Image element |
| `Svg` | — | SVG container for non-icon SVGs (decorative/structural). Use `Icon` for icons |
| `Video` | — | Video element |
| `Iframe` | — | Embedded frame |
| `Shape` | `Box` | Shape utilities |

### Buttons

| Component | Description |
|---|---|
| `Button` | Base button with text/icon support |
| `IconButton` | Icon-only button |
| `SquareButton` | Fixed-aspect button |
| `CircleButton` | Circular button |
| `SubmitButton` | Form submit button |
| `UploadButton` | File upload trigger |
| `CounterButton` | Button with counter badge |
| `ButtonSet` | Group of buttons |
| `ConfirmationButtons` | Confirm/Cancel pair |

### Inputs & Forms

| Component | Description |
|---|---|
| `Input` | Text input |
| `Textarea` | Multi-line input |
| `NumberInput` | Numeric input |
| `Checkbox` | Checkbox control |
| `Radio` | Radio button |
| `Toggle` | Toggle switch |
| `Select` | Dropdown select |
| `Field` | Label + input wrapper |
| `Search` | Search input with icon |

### Avatar & Social

| Component | Description |
|---|---|
| `Avatar` | User avatar (extends Img) |
| `AvatarSet` | Group of avatars |
| `AvatarStatus` | Avatar with status indicator |
| `AvatarHgroup` | Avatar + name/description |

### Data Display

| Component | Description |
|---|---|
| `Badge` | Status/count badge |
| `StatusDot` | Colored status indicator |
| `Progress` | Progress bar |
| `CircleProgress` | Circular progress |
| `Stars` | Star rating |
| `UnitValue` | Number + unit display |

### Navigation

| Component | Description |
|---|---|
| `Link` | Navigation link with router |
| `LinkSet` | Group of links |
| `Breadcrumb` | Breadcrumb navigation |
| `TabSet` | Tab navigation |
| `Pagination` | Page navigation |

### Feedback & Overlay

| Component | Description |
|---|---|
| `Modal` | Modal dialog |
| `Notification` | Notification banner |
| `Tooltip` | Hover tooltip |
| `Dropdown` | Dropdown menu |
| `Accordion` | Expandable sections |

### Icons

| Component | Description |
|---|---|
| `Icon` | SVG icon from icon set (Rule 29 / Rule 62 — every SVG icon goes through this) |
| `IconText` | Icon + text combination |
| `IconHeading` | Icon + heading |

## Extension chain

Components form a three-level inheritance chain:

```
UIKit Atom (Box, Flex, etc.)
  → Default Library Component (Button, Avatar, etc.)
    → Your Project Component (MyButton, ProfileAvatar, etc.)
```

```js
// UIKit defines the base
// Avatar extends Img with default styling
// Your component extends Avatar with customization

export const ProfileAvatar = {
  extends: 'Avatar',
  boxSize: 'D D',
  round: 'A',
  border: '2px solid',
  borderColor: 'primary',
}
```

PascalCase keys auto-extend matching registered components:

```js
export const MyCard = {
  flow: 'y',
  gap: 'A',
  padding: 'B',
  theme: 'card',

  // "Avatar" key auto-extends the library Avatar component
  Avatar: {
    boxSize: 'C C',
  },

  // "Badge" key auto-extends the library Badge component
  Badge: {
    text: 'New',
    theme: 'primary',
  },

  H: {
    tag: 'h3',
    text: 'Card Title',
  },
}
```

See PROJECT_STRUCTURE.md for full project layout, router pattern, and entry-point setup.

---

# Part 2 — Pre-configured Design System Tokens

These are the **recommended default design system values** for all newly created Symbols apps. When generating a new project, always use these as the baseline. Never invent custom values or use font sizes smaller than what these defaults define.

> **Strict (Rule 27/28):** ALL spacing, colors, typography, durations come from these tokens. ZERO raw px, hex, rgb, hsl, raw durations.

## typography.js

```js
export default {
  base: 16,
  ratio: 1.25,
  subSequence: true,
}
```

**Important:** `base: 16` means the smallest reasonable body text is 16px. The ratio `1.25` (major-third) generates the typography sequence — `fontSize: 'B'` ≈ 20px, `'C'` ≈ 25px, `'D'` ≈ 31px scale up; `'Z'` ≈ 12.8px, `'Y'` ≈ 10.2px scale down (use only for captions/labels, never body text).

> **No custom spacing/typography tokens.** Every value comes from the generated sequence — there are no hand-named scalars. To shift the whole scale, change `base` or `ratio`. To pick a specific value, pick the right letter or sub-letter (e.g. `B1`, `B2`).

## spacing.js

```js
export default {
  base: 16,
  ratio: 1.618,
  subSequence: true,
}
```

Golden ratio (1.618) for the spacing sequence — `padding: 'A'` ≈ 16px, `'B'` ≈ 26px, `'C'` ≈ 42px, `'D'` ≈ 68px, etc.

> **`padding: 'B'` ≠ `fontSize: 'B'`.** Each family has its own base × ratio. The same letter resolves to different absolute values across typography (≈25px), spacing (≈26px), and timing (≈200ms). See DESIGN_SYSTEM.md → "Token sequences" for the cross-family table.

## color.js

```js
export default {
  green: '#389d34',
  red: '#e15c55',
  yellow: '#EDCB38',
  orange: '#e97c16',
  transparent: 'rgba(0, 0, 0, 0)',
  black: 'black',
  gray: '#4e4e50',
  white: '#ffffff',
  title: ['--gray 1 -168', '--gray 1 +168'],
  caption: ['--gray 1 -68', '--gray 1 +68'],
  paragraph: ['--gray 1 -42', '--gray 1 +42'],
  disabled: ['--gray 1 -26', '--gray 1 +26'],
  line: ['--gray 1 -16', '--gray 1 +16'],
  codGray: '#171717',
  solitude: '#e5f1ff',
  anakiwa: '#a3cdfd',
  concrete: '#f2f2f2',
  blue: '#0474f2',
  phosphorus: '#4db852',
}
```

**Note:** Array values are `[@dark, @light]` theme pairs. Format: `'--colorName opacity tone'` where `--` is the color reference prefix, opacity is 0-1, and tone is `+N`/`-N` (relative HSL lightness) or `=N` (absolute HSL lightness %). Use semantic names (`title`, `caption`, `paragraph`, `disabled`, `line`) for text colors.

## theme.js

```js
export default {
  document: {
    '@dark': { background: 'codGray', color: 'title' },
    '@light': { background: 'gray 1 +168', color: 'title' },
  },
  dialog: {
    '@dark': {
      background: 'gray 0.95 -68', color: 'title',
      backdropFilter: 'blur(3px)', borderColor: 'gray 0', outlineColor: 'blue',
    },
    '@light': {
      background: 'gray .95 +150', color: 'title',
      backdropFilter: 'blur(3px)', borderColor: 'gray 0', outlineColor: 'blue',
    },
  },
  'dialog-elevated': {
    '@dark': {
      color: 'title', background: 'gray 1 +68',
      borderColor: 'gray 0', outlineColor: 'blue', backgroundKey: 'caption',
    },
    '@light': {
      color: 'title', background: 'gray 0.95 +140',
      borderColor: 'gray 0', outlineColor: 'blue',
    },
  },
  field: {
    '@dark': {
      color: 'white', background: 'gray 0.95 -65',
      '::placeholder': { color: 'white 1 -78' },
    },
    '@light': {
      color: 'black',
      '::placeholder': { color: 'gray 1 -68' },
    },
  },
  'field-dialog': {
    '@dark': { background: 'gray 1 -16', color: 'title' },
    '@light': { color: 'title', background: 'gray 1 -96' },
  },
  primary: {
    '@dark': { background: 'blue', color: 'white' },
    '@light': { color: 'white', background: 'blue' },
  },
  warning: {
    '@dark': { background: 'red', color: 'white' },
    '@light': { color: 'white', background: 'red' },
  },
  success: {
    '@dark': { background: 'green', color: 'white' },
    '@light': { background: 'green', color: 'white' },
  },
  none: { color: 'none', background: 'none' },
  transparent: { color: 'currentColor', background: 'transparent' },
  bordered: {
    background: 'transparent',
    '@dark': { border: '1px solid #4e4e50' },
    '@light': { border: '1px solid #a3cdfd' },
  },
}
```

## font_family.js

```js
export default {
  Default: {
    isDefault: true,
    value: ['San Francisco, Helvetica Neue, Helvetica, Arial'],
    type: 'sans-serif',
  },
}
```

## timing.js

```js
export default {
  defaultBezier: 'cubic-bezier(.29, .67, .51, .97)',
}
```

The framework defaults the timing sequence to `base: 150ms, ratio: 1.333` (perfect-fourth) — `transition: 'A'` ≈ 150ms, `'B'` ≈ 200ms, `'C'` ≈ 266ms. Easing curves (`defaultBezier`, etc.) are name-based; **durations are sequence-based** like spacing/typography. `transition: 'B defaultBezier'` resolves to `200ms cubic-bezier(...)`.

## animation.js

```js
export default {
  fadeInUp: {
    from: { transform: 'translate3d(0, 12.5%, 1px)', opacity: 0 },
    to: { transform: 'translate3d(0, 0, 1px)', opacity: 1 },
  },
  fadeOutDown: {
    from: { transform: 'translate3d(0, 0, 1px)', opacity: 1 },
    to: { transform: 'translate3d(0, 12.5%, 1px)', opacity: 0 },
  },
  marquee: {
    from: { transform: 'translate3d(0, 0, 1px)' },
    to: { transform: 'translate3d(-50%, 0, 1px)' },
  },
}
```

## cases.js

```js
export default {
  isSafari: () => /^((?!chrome|android).)*safari/i.test(navigator.userAgent),
}
```

## designSystem/index.js

The full design system export:

```js
export default {
  color,
  gradient,
  theme,
  font,
  font_family,
  typography,
  spacing,
  timing,
  class: _class,
  grid,
  icons,
  shape,
  reset,
  animation,
  media,
  cases,
}
```

**Empty by default** (customize per project): `font`, `gradient`, `grid`, `icons`, `shape`, `reset`, `media`, `class`.

## Usage guidelines

1. **Always start from these defaults** — don't invent typography/spacing scales from scratch
2. **Minimum body font size** — `Z` token (16px). Use `Y` or smaller only for labels/captions
3. **Use semantic color names** — `title`, `caption`, `paragraph` instead of raw hex
4. **Use theme tokens** — `document`, `dialog`, `primary`, `warning`, `success` for consistent theming
5. **Extend, don't replace** — add project-specific tokens alongside these defaults, don't remove them

## How tokens combine with the library

Default library components automatically use your project's design system tokens:

```js
// designSystem/index.js
export default {
  color: {
    primary: '#2563EB',
    surface: '#F8FAFC',
    text: '#0F172A',
  },
  theme: {
    primary: {
      background: 'primary',
      color: 'white',
    },
    card: {
      background: 'surface',
      borderRadius: 'A',
    },
  },
  typography: {
    base: 16,
    ratio: 1.25,
  },
  spacing: {
    base: 16,
    ratio: 1.618,
  },
}
```

When you use `theme: 'primary'` on a Button, it pulls colors from YOUR design system, not hardcoded values.
