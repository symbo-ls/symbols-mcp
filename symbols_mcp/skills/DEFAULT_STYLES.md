# Default Template Styles

These are the **recommended default design system values** for all newly created Symbols apps. When generating a new project, always use these as the baseline. Never invent custom values or use font sizes smaller than what these defaults define.

---

## typography.js

```js
export default {
  base: 16,
  ratio: 1.25,
  subSequence: true,
}
```

**Important:** `base: 16` means the smallest reasonable body text is 16px (token `Z`). Never use font sizes below this for body content. The ratio `1.25` generates the scale — tokens like `A` (20px), `B` (25px), `C` (31px), etc. scale up, while `Y` (12.8px), `X` (10.2px) scale down and should only be used for captions/labels, never body text.

---

## spacing.js

```js
export default {
  base: 16,
  ratio: 1.618,
  subSequence: true,
}
```

Golden ratio (1.618) for spacing. Tokens: `A` = 16px, `B` = 26px, `C` = 42px, etc.

---

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

**Note:** Array values are `[@dark, @light]` theme pairs. Format: `'--colorName opacity tone'` where `--` is the color reference prefix, opacity is 0-1, and tone is `+N`/`-N` (RGB delta) or `=N` (HSL lightness %). Use semantic names (`title`, `caption`, `paragraph`, `disabled`, `line`) for text colors.

---

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

---

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

---

## timing.js

```js
export default {
  defaultBezier: 'cubic-bezier(.29, .67, .51, .97)',
}
```

---

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

---

## cases.js

```js
export default {
  isSafari: () => /^((?!chrome|android).)*safari/i.test(navigator.userAgent),
}
```

---

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

---

## Usage Guidelines

1. **Always start from these defaults** — don't invent typography/spacing scales from scratch
2. **Minimum body font size** — `Z` token (16px). Use `Y` or smaller only for labels/captions
3. **Use semantic color names** — `title`, `caption`, `paragraph` instead of raw hex
4. **Use theme tokens** — `document`, `dialog`, `primary`, `warning`, `success` for consistent theming
5. **Extend, don't replace** — add project-specific tokens alongside these defaults, don't remove them
