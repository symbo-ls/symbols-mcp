# Symbols Design System — Tokens, Themes & Configuration

The design system lives in `designSystem/` and controls all visual tokens consumed by DOMQL props.

---

## Design System Files

| File             | Purpose                                                      |
| ---------------- | ------------------------------------------------------------ |
| `COLOR.js`       | Named color palette                                          |
| `GRADIENT.js`    | Gradient definitions                                         |
| `THEME.js`       | Semantic surface themes (document, dialog, field, primary…)  |
| `FONT.js`        | Custom font faces                                            |
| `FONT_FAMILY.js` | Font family stacks                                           |
| `TYPOGRAPHY.js`  | Type scale (ratio + range)                                   |
| `SPACING.js`     | Spacing scale (ratio + range)                                |
| `TIMING.js`      | Named easing curves                                          |
| `CLASS.js`       | Utility CSS class overrides                                  |
| `ANIMATION.js`   | Named keyframe animations                                    |
| `MEDIA.js`       | Custom media query breakpoints                               |
| `CASES.js`       | Conditional environment flags                                |
| `RESET.js`       | Global CSS reset overrides                                   |

---

## How Tokens Are Used in Props

Props accept design tokens as strings. The system resolves them into CSS values via sequences, themes, and colors.

```js
Card: {
  padding: 'B C',          // spacing token
  background: 'primary.08', // color + opacity
  borderRadius: 'B',       // spacing token
  shadow: 'soft',          // shadow token
  fontSize: 'B',           // typography token
  color: 'title'           // adaptive color token
}
```

---

## COLOR

### Static colors

| Token        | Value           | Use                      |
| ------------ | --------------- | ------------------------ |
| `green`      | `#389d34`       | Success states           |
| `red`        | `#e15c55`       | Warning/error states     |
| `yellow`     | `#EDCB38`       | Attention states         |
| `orange`     | `#e97c16`       | Accent states            |
| `blue`       | `#0474f2`       | Primary interactive      |
| `black`      | `black`         | Pure black               |
| `white`      | `#ffffff`       | Pure white               |
| `gray`       | `#4e4e50`       | Neutral mid-tone         |
| `codGray`    | `#171717`       | Near-black page bg       |
| `transparent`| `rgba(0,0,0,0)` | Fully transparent        |

### Adaptive semantic colors (dark/light aware)

| Token       | Dark value         | Light value        | Use                |
| ----------- | ------------------ | ------------------ | ------------------ |
| `title`     | near-white         | near-black         | Primary text       |
| `caption`   | mid-gray           | mid-gray           | Secondary/meta     |
| `paragraph` | lighter-gray       | darker-gray        | Body copy          |
| `disabled`  | dimmer-gray        | dimmer-gray        | Disabled state     |
| `line`      | subtle-gray        | subtle-gray        | Borders/dividers   |

### Color modifier syntax (dot-notation)

Color tokens use dot-notation for opacity and `+`/`-` for relative tone shifts, `=` for absolute lightness:

```js
'gray.95-68'      // gray at 95% opacity, darkened 68 steps
'gray+168'        // gray at full opacity, lightened 168 steps
'white-78'        // white darkened 78 steps
'primary.5'       // primary at 50% opacity
'primary+5'       // shifted tone
'gray=90'         // gray at absolute 90% lightness
'gray.5+15'       // 50% opacity + 15 shade lighter
```

Opacity rules:
- `.XX` always means `0.XX` — e.g., `.1` = 0.1, `.35` = 0.35, `.0` = 0.0
- Full opacity (1.0) = no modifier needed (just the color name)
- Raw CSS values (`rgba()`, `hsl()`, `#hex`) pass through unchanged

### Usage in components

```js
// Static
Text: { color: 'blue' }

// Adaptive semantic
Caption: { color: 'caption' }

// Inline tint
Box: { background: 'gray.1' }

// With tone modifier
Card: { background: 'gray.92+8' }
```

---

## THEME

Apply with `theme: 'name'` on any element. Themes define `background` + `color` pairs per dark/light mode.

### Available themes

| Theme             | Use                                               |
| ----------------- | ------------------------------------------------- |
| `document`        | Page root surface                                 |
| `dialog`          | Elevated card/panel with glass blur               |
| `dialog-elevated` | Higher elevation (selected tabs)                  |
| `field`           | Input control surface                             |
| `field-dialog`    | Slightly elevated input inside dialog             |
| `primary`         | CTA: blue background, white text                  |
| `warning`         | Destructive/alert: red background, white text     |
| `success`         | Positive: green background, white text            |
| `transparent`     | No background, inherits text color                |
| `bordered`        | Transparent + 1px border                          |
| `none`            | Resets both color and background to `none`        |

```js
Page: { extends: 'Flex', theme: 'document', minHeight: '100dvh' }
Card: { extends: 'Flex', theme: 'dialog', round: 'A', padding: 'A' }
Input: { theme: 'field' }
Button: { theme: 'primary', text: 'Save' }
Badge: { theme: 'warning', text: 'Error' }
Tab: { '.isActive': { theme: 'dialog-elevated' } }
```

### Custom theme definition

```js
theme: {
  button: {
    color: 'text',
    background: 'primary',
    ':hover':  { background: 'primary.85' },
    ':active': { background: 'primary.75' },
    '@dark':   { background: 'primary.6' }
  }
}
```

---

## TYPOGRAPHY — Type Scale

Scale is generated using a ratio (Major Third = 1.25 by default). Tokens map to the sequence:

| Token range   | Approx size | Common use                  |
| ------------- | ----------- | --------------------------- |
| `W4`–`W1`     | ~8–10 px    | Micro text                  |
| `Z4`–`Z`      | ~10–12 px   | Caption, footnote           |
| `Y4`–`A`      | ~12–16 px   | Body text, small headings   |
| `A1`–`B`      | ~18–24 px   | Headings, large body        |
| `B1`–`C`      | ~28–40 px   | Display headings            |
| `C1`–`C2`     | ~48–64 px   | Hero headlines              |

```js
Heading: { fontSize: 'C' }
Caption: { fontSize: 'Z2' }
Body: { fontSize: 'A' }
```

Config:
```js
typography: {
  base: 16,        // root font size
  ratio: 1.25,     // Major Third scale
  range: [-5, 12],
  subSequence: true  // enables B2, C1 etc.
}
```

---

## SPACING — Layout Scale

Golden Ratio scale (1.618 by default). Used for `padding`, `margin`, `gap`, `width`, `height`, `boxSize`, `borderRadius`, etc.

| Token    | Approx value | Common use                      |
| -------- | ------------ | ------------------------------- |
| `W2`–`W` | 2–4 px       | Micro gaps, offsets             |
| `X4`–`X` | 4–6 px       | Icon padding, tight gaps        |
| `Z4`–`Z` | 10–16 px     | Compact padding                 |
| `A`–`A4` | 16–26 px     | Default padding, gutters        |
| `B`–`B4` | 26–42 px     | Section padding                 |
| `C`–`C4` | 42–68 px     | Container padding, avatar sizes |
| `D`–`D4` | 68–110 px    | Large sections                  |
| `E`–`F`  | 110–178 px   | Hero padding, max-widths        |

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

---

## TIMING — Easing Curves

| Token           | Value                              | Use              |
| --------------- | ---------------------------------- | ---------------- |
| `defaultBezier` | `cubic-bezier(.29, .67, .51, .97)` | Smooth ease-out  |

```js
Box: { transition: 'B defaultBezier', transitionProperty: 'opacity, transform' }
```

Timing scale (in ms): `base: 150, ratio: 1.333`

---

## ANIMATION

Named keyframe animations:

| Name          | Effect                          | Use              |
| ------------- | ------------------------------- | ---------------- |
| `fadeInUp`    | Fade in + slide up from 12.5%   | Entrance         |
| `fadeOutDown` | Fade out + slide down to 12.5%  | Exit             |
| `marquee`     | Scroll left by 50%              | Ticker           |

```js
Modal: { animation: 'fadeInUp B defaultBezier' }
Ticker: { animation: 'marquee 8s linear infinite' }
```

---

## MEDIA — Breakpoints

Built-in breakpoints:

| Token      | Query                    | Direction    |
| ---------- | ------------------------ | ------------ |
| `tv`       | `min-width: 2780px`      | up           |
| `screenL`  | `max-width: 1920px`      | down         |
| `tabletL`  | `max-width: 1366px`      | down         |
| `tabletS`  | `max-width: 1024px`      | down         |
| `mobileL`  | `max-width: 768px`       | down         |
| `mobileM`  | `max-width: 560px`       | down         |
| `mobileS`  | `max-width: 480px`       | down         |
| `light`    | `prefers-color-scheme: light` | —      |
| `dark`     | `prefers-color-scheme: dark`  | —      |

Add `<` suffix for min-width (upward): `tabletL<` = `min-width: 1366px`

```js
Grid: {
  columns: 'repeat(4, 1fr)',
  '@tabletSm': { columns: 'repeat(2, 1fr)' },
  '@mobileL': { columns: '1fr' }
}
Box: {
  '@dark': { background: 'codGray' },
  '@light': { background: 'concrete' }
}
```

---

## CASES — Conditional Environment Flags

| Case       | Condition                                 |
| ---------- | ----------------------------------------- |
| `isSafari` | `true` when browser is Safari             |

```js
Element: { $isSafari: { top: 'Z2', right: 'Z2' } }
```

---

## Design System Configuration

Define a single config object. Keys map directly to design system categories:

```js
const designSystemConfig = {
  color: {
    primary: '#1f6feb',
    text: ['#0b0b0b', '#f5f5f5'],   // [dark, light] adaptive
    accent: {
      '@light': '#ff7a18',
      '@dark': '#ffb347'
    }
  },
  theme: {
    document: { color: 'text', background: 'primary.02' },
    button: { color: 'text', background: 'primary' }
  },
  typography: { base: 16, ratio: 1.25, subSequence: true },
  spacing: { base: 16, ratio: 1.618, subSequence: true },
  timing: { base: 150, ratio: 1.333, unit: 'ms' },
  font: {
    Inter: {
      url: '/fonts/Inter-Variable.woff2',
      isVariable: true,
      fontWeight: '100 900'
    }
  },
  font_family: {
    primary: { value: ['Inter'], type: 'sans', isDefault: true }
  },
  icons: { search: '<svg>...</svg>' },
  svg: { logo: '<svg>...</svg>' },
  shadow: {
    soft: 'black.15 0px 10px 30px 0px',
    hard: ['black.25 0px 8px 16px 0px', 'black.35 0px 10px 24px 0px']  // [light, dark]
  },
  media: {
    mobile: '(max-width: 768px)',
    desktop: '(min-width: 1024px)'
  },

  // Configuration flags
  useVariable: true,    // emit CSS custom properties
  useReset: true,       // apply CSS reset
  useFontImport: true,  // load fonts via @font-face
  useIconSprite: true,  // inline SVG sprite
  useDocumentTheme: true, // apply document theme to <html>
  useDefaultConfig: true, // merge smbls default design system
  globalTheme: 'dark',  // force dark/light mode globally
}
```

### Valid top-level config keys

```
color, gradient, theme, typography, spacing, timing,
font, font_family, icons, semantic_icons, svg, svg_data,
shadow, media, grid, class, reset, unit, animation, cases
```

**Do NOT** wrap these under `props` or other wrappers.

---

## Fonts

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
  inter: {
    400: { url: '/fonts/Inter-Regular.woff2', fontWeight: 400 },
    700: { url: '/fonts/Inter-Bold.woff2', fontWeight: 700 }
  }
}
```

---

## Icons & SVG

```js
icons: {
  search: '<svg>...</svg>'    // converted to sprite
},
semantic_icons: {
  logo: true                  // NOT converted to sprite (used as-is)
},
svg: {
  logo: '<svg>...</svg>'      // general SVG assets
}
```

Default icon set includes: `symbols`, `logo`, arrow variants, `check`, `checkCircle`, chevron variants, `copy`, `eye`, `eyeOff`, `info`, `lock`, `minus`, `plus`, `search`, `send`, `smile`, `star`, `sun`, `moon`, `upload`, `video`, `x`, `moreHorizontal`, `moreVertical`

---

## Design System Flags

| Flag               | Default | Effect                                    |
| ------------------ | ------- | ----------------------------------------- |
| `useReset`         | `true`  | Apply CSS reset                           |
| `useVariable`      | `true`  | Emit CSS custom properties for all tokens |
| `useFontImport`    | `true`  | Load FONT entries via @font-face          |
| `useIconSprite`    | `true`  | Inline the ICONS SVG sprite into the DOM  |
| `useSvgSprite`     | `true`  | Inline SVG sprite definitions             |
| `useDefaultConfig` | `true`  | Merge smbls default design system config  |
| `useDocumentTheme` | `true`  | Apply document theme to `<html>`          |
| `verbose`          | `false` | Suppress design system debug output       |

---

## Common Mistakes

- Do not nest config under `props` or other wrappers
- Use `font_family` instead of `fontFamily`
- Define `typography` and `spacing` if you use tokens like `A`, `B2`, or `C+Z`
- Use named color tokens, not raw hex, for all interactive/semantic colors
- Use dot-notation for color opacity: `color: 'white.7'` (not `'white .7'`)
