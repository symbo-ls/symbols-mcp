# Symbols Design System -- Token Reference

Design system config lives in `designSystem/`. All tokens resolve to CSS via DOMQL props.

## Design System Files

| File | Purpose |
|---|---|
| `color.js` | Named color palette |
| `gradient.js` | Gradient definitions |
| `theme.js` | Semantic surface themes |
| `font.js` | Custom font faces |
| `font_family.js` | Font family stacks |
| `typography.js` | Type scale (ratio + range) |
| `spacing.js` | Spacing scale (ratio + range) |
| `timing.js` | Easing curves and duration scale |
| `class.js` | Utility CSS class overrides |
| `animation.js` | Named keyframe animations |
| `media.js` | Custom media query breakpoints |
| `reset.js` | Global CSS reset overrides |
| `vars.js` | Custom CSS properties (custom vars) |

## How Tokens Are Used in Props

```js
Card: {
  padding: 'B C',          // spacing token
  background: 'primary.08', // color + opacity
  borderRadius: 'B',       // spacing token (also via `round`)
  shadow: 'soft',          // shadow token from designSystem
  fontSize: 'B',           // typography token
  color: 'title'           // adaptive color token
}
```

---

## color

### Static colors

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

### Adaptive semantic colors

Array syntax `[darkValue, lightValue]` with relative tone shifts from gray:

| Token | Dark | Light | Use |
|---|---|---|---|
| `title` | near-white (+168) | near-black (-168) | Primary text |
| `caption` | mid-gray (+68) | mid-gray (-68) | Secondary/meta |
| `paragraph` | lighter-gray (+42) | darker-gray (-42) | Body copy |
| `disabled` | dimmer-gray (+26) | dimmer-gray (-26) | Disabled state |
| `line` | subtle-gray (+16) | subtle-gray (-16) | Borders/dividers |

### Color modifier syntax (dot-notation)

Dot = opacity. `+`/`-` = relative tone shift. `=` = absolute lightness.

```
'gray.95-68'      // 95% opacity, darkened 68 steps
'gray+168'        // full opacity, lightened 168 steps
'white-78'        // white darkened 78 steps
'primary.5'       // primary at 50% opacity
'primary+5'       // shifted tone
'gray=90'         // absolute 90% lightness
'gray.5+15'       // 50% opacity + 15 lighter
```

Opacity rules:
- `.XX` = `0.XX` -- `.1` = 0.1, `.35` = 0.35, `.0` = 0.0
- Full opacity (1.0) = no modifier needed
- Raw CSS values (`rgba()`, `hsl()`, `#hex`) pass through unchanged
- CSS variables (`--myVar`) convert to `var(--myVar)`

### Usage

```js
Text: { color: 'blue' }           // static
Caption: { color: 'caption' }     // adaptive semantic
Box: { background: 'gray.1' }     // inline tint
Card: { background: 'gray.92+8' } // with tone modifier
```

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

Apply with `theme: 'name'`. Themes define `background` + `color` pairs per dark/light mode.

### Surface themes

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
Page: { flow: 'y', theme: 'document', minHeight: '100dvh' }
Card: { flow: 'y', theme: 'dialog', round: 'A', padding: 'A' }
Input: { theme: 'field' }
Button: { theme: 'primary', text: 'Save' }
Badge: { theme: 'alert', text: 'Error' }
```

### Variant modifiers (dot-notation)

```js
Button: { theme: 'primary', '.gradient': true }  // gradient variant
Card: { theme: 'card', '.secondary': true }       // secondary variant
Label: { theme: 'label', '.dark': true }          // dark variant
```

### themeModifier

Force a color scheme regardless of global theme:

```js
DarkSection: { themeModifier: 'dark', theme: 'document' }
LightCard: { themeModifier: 'light', theme: 'card' }
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
Body: { fontSize: 'A' }
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

### fontWeight

Auto-sets `fontVariationSettings` for variable fonts:

```js
Title: { fontWeight: 700 }
// outputs: fontWeight: 700, fontVariationSettings: '"wght" 700'
```

---

## spacing

Golden Ratio scale (1.618 default). Applies to `padding`, `margin`, `gap`, `width`, `height`, `boxSize`, `borderRadius`/`round`, `inset`, `top`, `left`, `right`, `bottom`, etc.

| Token | Approx value | Use |
|---|---|---|
| `W`-`W2` | 2-4 px | Micro gaps, offsets |
| `X`-`X2` | 4-6 px | Icon padding, tight gaps |
| `Z`-`Z2` | 10-16 px | Compact padding |
| `A`-`A2` | 16-26 px | Default padding, gutters |
| `B`-`B2` | 26-42 px | Section padding |
| `C`-`C2` | 42-68 px | Container padding, avatar sizes |
| `D`-`D2` | 68-110 px | Large sections |
| `E`-`F` | 110-178 px | Hero padding, max-widths |

Sub-sequence rules: `W` and `X` only have `W`, `W1`, `W2` and `X`, `X1`, `X2`. Sub-tokens like `W4`, `X4` do NOT exist. Sub-steps `3` and `4` (e.g. `A3`, `A4`, `B3`, `B4`) only appear from `A` and above.

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

---

## CSS-in-Props Shorthand Properties

### Layout

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
| `shadow` | Resolves shadow token from designSystem, outputs `boxShadow` |
| `verticalInset` | `top bottom` (space-separated) |
| `horizontalInset` | `left right` (space-separated) |
| `paddingBlock` | `paddingBlockStart paddingBlockEnd` |
| `paddingInline` | `paddingInlineStart paddingInlineEnd` |
| `marginBlock` | `marginBlockStart marginBlockEnd` |
| `marginInline` | `marginInlineStart marginInlineEnd` |

### Grid

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

### Color/Border/Shadow

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
| `borderTop/Bottom/Left/Right` | Same parsing as `border` |
| `outline` | Same parsing as `border` |
| `textStroke` | Sets `WebkitTextStroke` with color resolution |
| `shadow` | Resolves named shadow from designSystem |
| `boxShadow` | Parses shadow with color token resolution |
| `textShadow` | Parses shadow with color token resolution |
| `columnRule` | Same parsing as `border` |

### Misc

| Prop | Behavior |
|---|---|
| `overflow` | Also sets `scrollBehavior: 'smooth'` |
| `cursor` | Supports file lookup for custom cursor images |
| `transitionProperty` | Also sets `willChange` to same value |

---

## timing

| Token | Value | Use |
|---|---|---|
| `defaultBezier` | `cubic-bezier(.29, .67, .51, .97)` | Smooth ease-out |

Scale: `base: 150, ratio: 1.333` (perfect-fourth). Duration tokens use the same letter sequence (A, B, C...) in milliseconds.

```js
Box: { transition: 'B defaultBezier', transitionProperty: 'opacity, transform' }
```

---

## animation

The scratch default animation config is empty — define your own in `designSystem/animation.js`. The default template includes `fadeInUp`, `fadeOutDown`, and `marquee` (see DEFAULT_STYLES.md).

### CSS shorthand syntax

```js
Modal: { animation: 'fadeIn 2s ease-in-out' }
Ticker: { animation: 'marquee 8s linear infinite' }
Spinner: { animation: 'spin 1s linear infinite alternate' }
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
    to: { opacity: 1, transform: 'translateY(0)' }
  }
}
```

### Custom animation in designSystem

```js
animation: {
  fadeInUp: {
    from: { opacity: 0, transform: 'translateY(12.5%)' },
    to: { opacity: 1, transform: 'translateY(0)' }
  },
  marquee: {
    from: { transform: 'translateX(0)' },
    to: { transform: 'translateX(-50%)' }
  }
}
```

---

## media

The scratch default config includes only 4 media tokens. The responsive breakpoints are added by the framework automatically from the `breakpoints` system.

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
  '@dark': { background: 'codGray' },
  '@light': { background: 'concrete' }
}
```

---

## Cases

Cases are defined in `symbols/cases.js` (not in designSystem) and added to `context.cases`. They are functions that evaluate conditions globally or per-element.

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

## Design System Configuration

Full config example:

```js
const designSystemConfig = {
  color: {
    primary: '#1f6feb',
    text: ['#0b0b0b', '#f5f5f5'],   // [dark, light] adaptive
    accent: { '@light': '#ff7a18', '@dark': '#ffb347' }
  },
  gradient: {
    'my-gradient': 'linear-gradient(to right, #ff7a18, #ffb347)'
  },
  theme: {
    document: { color: 'text', background: 'primary.02' },
    button: {
      color: 'text',
      background: 'primary',
      ':hover': { background: 'primary.85' },
      '@dark': { background: 'primary.6' },
      '.active': { background: 'primary' }
    }
  },
  typography: { base: 16, ratio: 1.25, subSequence: true },
  spacing: { ratio: 1.618, subSequence: true },
  timing: { base: 150, ratio: 1.333, unit: 'ms', subSequence: true },
  font: {
    Inter: {
      url: '/fonts/Inter-Variable.woff2',
      isVariable: true,
      fontWeight: '100 900'
    }
  },
  font_family: {
    primary: { value: ['Inter'], type: 'sans', isDefault: true },
    system: { value: ['"Helvetica Neue"', 'Helvetica', 'Arial'], type: 'sans-serif' }
  },
  icons: { search: '<svg>...</svg>' },
  svg: { logo: '<svg>...</svg>' },
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
  useVariable: true,
  useReset: true,
  useFontImport: true,
  useIconSprite: true,
  useDocumentTheme: true,
  useDefaultConfig: true,
  globalTheme: 'dark',  // 'dark', 'light', or 'auto'
}
```

### Valid top-level config keys

```
color, gradient, theme, typography, spacing, timing,
font, font_family, icons, semantic_icons, svg, svg_data,
shadow, media, grid, class, reset, unit, animation, vars
```

Do NOT wrap these under `props` or other wrappers.

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

Default icon set: `symbols`, `logo`, arrow variants, `check`, `checkCircle`, chevron variants, `copy`, `eye`, `eyeOff`, `info`, `lock`, `minus`, `plus`, `search`, `send`, `smile`, `star`, `sun`, `moon`, `upload`, `video`, `x`, `moreHorizontal`, `moreVertical`

---

## Transition Properties

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

## Design System Flags

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

## Pseudo-selectors & States in Props

```js
Button: {
  theme: 'primary',
  ':hover': { opacity: '0.85' },
  ':active': { opacity: '0.75' },
  ':focus': { outline: '2px solid blue' },
  '::placeholder': { color: 'gray+68' },
  '.isActive': { theme: 'primary', background: 'blue' },
  '.disabled': { opacity: '0.5', pointerEvents: 'none' },
  '@dark': { background: 'darkBlue' },
  '@mobileL': { fontSize: 'Z' }
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

## Runtime APIs

### init / reinit

```js
import { init, reinit } from 'smbls'

init(designSystemConfig)     // Setup design system (called once)
reinit(updatedConfig)        // Update design system at runtime
```

### applyCSS / updateVars

```js
import { applyCSS, updateVars } from 'smbls'

applyCSS('.my-class { color: red }')  // Inject raw CSS
updateVars({ color: { primary: '#ff0000' } })  // Update CSS variables only
```

---

## Common Mistakes

- **NEVER use UPPERCASE keys** (`COLOR`, `THEME`, `TYPOGRAPHY`, etc.) — always use lowercase (`color`, `theme`, `typography`). UPPERCASE is deprecated and banned.
- Do NOT nest config under `props` or other wrappers
- Use `font_family` not `fontFamily` in config
- Define `typography` and `spacing` if you use tokens like `A`, `B2`, or `C+Z`
- Use named color tokens, not raw hex, for all interactive/semantic colors
- Dot-notation for opacity: `color: 'white.7'` (not `'white .7'`)
- `flow: 'x'` or `flow: 'y'` (not `flow: 'row'` or `flow: 'column'` -- though both work)
- `align: 'center center'` (space-separated: alignItems justifyContent)
- `round` is the shorthand for `borderRadius` with spacing token support
- `shadow` resolves from designSystem; `boxShadow` takes raw shadow syntax with color tokens
- `backdropFilter` must use `style: { backdropFilter: 'blur(10px)' }` to avoid text leak
- Colors in `border` syntax: `border: '1px solid gray.5'` -- the color token is resolved
