# Component API Reference

Use flattened props (no `props` wrapper). CSS props go at the top level. Events use `onX` syntax.

---

## Built-in Atoms

| Atom | HTML Tag | Props | Example |
|------|----------|-------|---------|
| `Text` | `<span>` | `text`, `color`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `textTransform`, `textDecoration`, `textAlign`, `maxWidth`, `overflow`, `whiteSpace` | `Text: { text: 'Hello', fontSize: 'B', color: 'title' }` |
| `Box` | `<div>` | `padding`, `margin`, `border`, `borderRadius`, `background`, `shadow`, `width`, `height`, `minWidth`, `maxWidth`, `minHeight`, `maxHeight`, `position`, `inset`, `top`, `right`, `bottom`, `left`, `overflow`, `zIndex` | `Box: { padding: 'A B', background: 'surface', borderRadius: 'B' }` |
| `Flex` | `<div>` | `flow`/`flexFlow`, `align`, `alignItems`, `justifyContent`, `gap`, `flex`, `flexGrow`, `flexShrink`, `flexBasis`, `wrap` | `Flex: { flow: 'y', align: 'center space-between', gap: 'B' }` |
| `Grid` | `<div>` | `columns`/`gridTemplateColumns`, `rows`/`gridTemplateRows`, `gap`, `columnGap`, `rowGap`, `gridAutoFlow`, `gridAutoColumns`, `gridAutoRows` | `Grid: { columns: 'repeat(3, 1fr)', gap: 'A' }` |
| `Link` | `<a>` | `href`, `target`, `rel`, `text`, `color`, `textDecoration`, `onClick` | `Link: { text: 'Docs', href: '/docs' }` |
| `Input` | `<input>` | `type`, `name`, `value`, `placeholder`, `required`, `disabled`, `onInput`, `onChange`, `onKeydown`, `padding`, `background`, `border`, `round` | `Input: { type: 'text', name: 'title', placeholder: 'Enter title' }` |
| `Radio` | `<input>` | `name`, `value`, `checked`, `disabled`, `onChange` | `Radio: { name: 'opt', value: 'a' }` |
| `Checkbox` | `<input>` | `name`, `value`, `checked`, `disabled`, `onChange` | `Checkbox: { name: 'agree', checked: true }` |
| `Svg` | `<svg>` | `html` (inline SVG markup), `width`, `height`, `viewBox`, `fill`, `stroke`. For non-icon SVGs only (decorative/structural). Use `Icon` for icons. | `Svg: { html: '<path d="..." />', viewBox: '0 0 24 24', width: '22', height: '22' }` |
| `Icon` | `<svg>` | `name` (sprite symbol id), `size`/`boxSize`, `color` | `Icon: { name: 'chevronRight', boxSize: 'A' }` |
| `IconText` | `<div>` | `icon`, `text`, `gap`, `align`, `color` | `IconText: { icon: 'search', text: 'Search', gap: 'Z' }` |
| `Button` | `<button>` | `text`, `icon`, `type`, `disabled`, `theme`, `padding`, `round`, `onClick`, `onSubmit` | `Button: { text: 'Save', theme: 'primary', type: 'submit' }` |
| `Img` | `<img>` | `src`, `alt`, `loading`, `width`, `height`, `boxSize`, `objectFit` | `Img: { src: '/logo.png', alt: 'Logo', boxSize: 'B' }` |
| `Iframe` | `<iframe>` | `src`, `width`, `height` | `Iframe: { src: 'https://example.com', width: '100%', height: '300px' }` |
| `Video` | `<video>` | `src`, `controls`, `width`, `height` | `Video: { src: '/demo.mp4', controls: true, width: '100%' }` |

### Img — file resolution

If `src` is not a valid URL, it resolves via `context.files[filename]`. Paths starting with `/files/` have the prefix stripped automatically (`/files/logo.png` looks up `"logo.png"` in context.files).

### Svg rule

Use `Icon` (not `Svg`) for icons. `Icon: { name: 'iconName' }` references `designSystem.icons`. Use `Svg` only for decorative/structural SVGs that are not icons.

### Picture

**CRITICAL**: `<picture>` does NOT support `src`. Never put `src` on Picture — it is silently ignored. Always put `src` on the `Img` child.

The Picture `Img` child can also read `src` from `element.parent.props.src` or `state.src`.

```js
// Basic
Picture: {
  Img: { src: '/files/photo.jpg' },
  width: '100%',
  aspectRatio: '16/9'
}

// Theme-aware sources
Picture: {
  extends: 'Picture',
  Img: { src: '/files/map-dark.svg' },
  '@dark': { srcset: '/files/map-dark.svg' },
  '@light': { srcset: '/files/map-light.svg' }
}
```

---

## Cross-cutting Props (all atoms)

All atoms support these additional features:

| Feature | Syntax |
|---------|--------|
| Media queries | `@mobile`, `@tablet`, `@tabletSm`, `@dark`, `@light` |
| Pseudo selectors | `:hover`, `:active`, `:focus-visible` |
| Conditional cases | `.isActive`, `!isActive`, `$isSafari` (global from `context.cases`) |
| ARIA attributes | `ariaLabel`, `aria: { expanded: true }`, `'aria-label': 'Close'` |
| Child overrides | `childProps` — one-level child overrides |
| Children | `children` — arrays or nested object trees |
| Lifecycle events | `onInit`, `onRender`, `onUpdate`, `onStateUpdate` |

---

## Typography

All accept a `text` prop.

| Component | Tag | Use |
|-----------|-----|-----|
| `H1`–`H6` | `<h1>`–`<h6>` | Semantic section headings |
| `P` | `<p>` | Body paragraph text |
| `Caption` | `<span>` | Small labels, hints |
| `Headline` | `<span>` | Display-size heading |
| `Subhead` | `<span>` | Sub-section text |
| `Footnote` | `<span>` | Footer reference text |
| `Strong` | `<strong>` | Bold inline emphasis |
| `Italic` | `<em>` | Italic inline emphasis |
| `U` | `<u>` | Underline inline emphasis |

```js
H2: { text: 'Section title' }
P: { text: 'Body copy goes here.' }
Caption: { text: 'Updated 3 days ago', color: 'caption' }
```

---

## Dividers

| Component | Use | Example |
|-----------|-----|---------|
| `Hr` | Horizontal rule | `Hr: { minWidth: 'F' }` |
| `HrLegend` | Divider with centered label | `HrLegend: { text: 'Or' }` |

---

## Buttons

| Component | Use | Example |
|-----------|-----|---------|
| `IconButton` | Icon-only circular button | `IconButton: { Icon: { name: 'plus' }, theme: 'dialog' }` |
| `IconButtonSet` | Group of icon buttons | — |
| `CounterButton` | Button with notification badge | — |
| `CounterIconButton` | Icon button with positioned badge | — |
| `IconCounterButton` | Button with icon, label, and counter | — |
| `UploadButton` | Text button that opens file picker | — |
| `UploadIconButton` | Icon button that opens file picker | — |
| `SubmitButton` | Form submit button | `SubmitButton: { value: 'Create account' }` |
| `ButtonSet` | Group of buttons | `ButtonSet: { children: [{ text: 'Cancel' }, { text: 'Save', theme: 'primary' }] }` |
| `ConfirmationButtons` | Yes/No pair | `ConfirmationButtons: { children: [{ text: 'Cancel' }, { text: 'Delete', theme: 'warning' }] }` |
| `InputButton` | Input with inline submit button | `InputButton: { Input: { placeholder: 'Enter email' }, Button: { text: 'Sign up' } }` |

---

## Avatar

| Component | Use | Example |
|-----------|-----|---------|
| `Avatar` | Single avatar image | `Avatar: { boxSize: 'C2' }` |
| `AvatarSet` | Overlapping group of avatars | — |
| `AvatarStatus` | Avatar with online/offline dot | `AvatarStatus: { Avatar: { boxSize: 'C' }, StatusDot: { theme: 'success' } }` |
| `AvatarHgroup` | Avatar + name + subtitle | `AvatarHgroup: { H: { text: 'Nika Tomadze' }, P: { text: 'Product Designer' } }` |
| `AvatarBadgeHgroup` | Avatar + heading + badge | — |
| `AvatarChatPreview` | Avatar + message preview row | `AvatarChatPreview: { H: { text: 'Design Team' }, P: { text: 'Can you join us today?' }, Value: { text: '2:20' } }` |

---

## Badge & Notification

Themes: `primary`, `warning`, `success`, `transparent`, `bordered`, `dialog`, `field`

| Component | Use | Example |
|-----------|-----|---------|
| `Badge` | Colored label (status, category) | `Badge: { text: 'New', theme: 'primary' }` |
| `BadgeCaption` | Caption paired with badge | `BadgeCaption: { Caption: { text: 'Status' }, Badge: { text: 'Active', theme: 'success' } }` |
| `NotificationCounter` | Circular number badge | `NotificationCounter: { text: '5' }` |

---

## Form & Input

| Component | Use | Example |
|-----------|-----|---------|
| `Field` | Styled input, optionally with trailing icon | `Field: { Input: { placeholder: 'Enter name' }, Icon: { icon: 'user' } }` |
| `FieldCaption` | Field with label above | `FieldCaption: { Caption: { text: 'Email' }, Field: { Input: { placeholder: 'you@example.com' } } }` |
| `IconInput` | Input with overlaid icon | — |
| `Select` | Native select | — |
| `SelectPicker` | Styled select with chevron | `SelectPicker: { Select: { children: [{ text: 'A', value: 'a' }, { text: 'B', value: 'b' }] } }` |
| `NumberPicker` | Increment/decrement control | — |
| `Search` | Search input with icon | `Search: { Input: { placeholder: 'Search…' } }` |
| `SearchDropdown` | Filterable dropdown with search | `SearchDropdown: { state: { data: ['New York', 'Los Angeles'] } }` |
| `TextareaIconButton` | Textarea with send button | `TextareaIconButton: { Textarea: { placeholder: 'Write a message…' } }` |

---

## Composition

Pair a primary element (heading, icon, image) with text content or controls.

| Component | Use | Example |
|-----------|-----|---------|
| `ButtonHgroup` | Heading group + button | `ButtonHgroup: { H: { text: 'Upgrade plan' }, P: { text: 'Get all features' }, Button: { text: 'Upgrade' } }` |
| `IconHeading` | Icon + heading | — |
| `IconHgroup` | Large icon + heading group | — |
| `ImgHgroup` | Image + heading group | `ImgHgroup: { Img: { src: '/icon.png', boxSize: 'C' }, H: { text: 'Product' }, P: { text: 'Tagline' } }` |
| `SectionHeader` | Section header with icon buttons | `SectionHeader: { Hgroup: { H: { text: 'Activity' } }, IconButtonSet: { children: [{ Icon: { name: 'filter' } }] } }` |
| `ValueHeading` | Heading with trailing value/unit | `ValueHeading: { H: { tag: 'h6', text: 'Revenue' }, UnitValue: { Unit: { text: '$' }, Value: { text: '1,200' } } }` |
| `IconTextSet` | List of icon + text pairs | — |

---

## Selection

Three flavors: **Check**, **Radio**, **Toggle** — each in caption, hgroup, and list variants.

| Component | Use | Example |
|-----------|-----|---------|
| `CheckCaption` | Checkbox + short label | `CheckCaption: { Caption: { text: 'Accept terms' } }` |
| `CheckHgroup` | Checkbox + title + description | — |
| `CheckCaptionList` | Stacked list of CheckCaption | — |
| `RadioCaption` | Radio + short label | — |
| `RadioHgroup` | Radio + title + description | — |
| `ToggleCaption` | Toggle switch + short label | — |
| `ToggleHgroup` | Toggle switch + title + desc | `ToggleHgroup: { H: { text: 'Email alerts' }, P: { text: 'Sent daily' } }` |
| `CheckStep` | Step with completion state | `CheckStep: { H6: { text: 'Verify email' }, Progress: { value: 1 } }` |
| `RadioStep` | Step with completion state | — |

```js
// ToggleHgroupList example
ToggleHgroupList: {
  children: [
    { H: { text: 'Email alerts' }, P: { text: 'Sent daily' } },
    { H: { text: 'Push notifications' }, P: { text: 'Instant' } }
  ]
}
```

---

## Progress & Status

| Component | Use | Example |
|-----------|-----|---------|
| `Progress` | Linear progress bar (value 0–1) | `Progress: { value: 0.6, height: 'X', round: 'Y' }` |
| `CircleProgress` | Circular progress ring | `CircleProgress: { value: 0.73, boxSize: 'D' }` |
| `ValueProgress` | Progress bar + readable label | `ValueProgress: { Progress: { value: 0.73 }, UnitValue: { Value: { text: '73' }, Unit: { text: '%' } } }` |
| `ProgressStepSet` | Row of progress bars for steps | — |
| `StatusDot` | Small colored indicator dot | `StatusDot: { theme: 'success' }` |
| `Stars` | 5-star rating display | — |

---

## Navigation & Links

| Component | Use | Example |
|-----------|-----|---------|
| `Link` | Hyperlink | `Link: { text: 'Docs', href: '/docs' }` |
| `LinkSet` | Navigation list of links | `LinkSet: { tag: 'nav', children: [{ text: 'Home', href: '/' }, { text: 'Docs', href: '/docs' }] }` |
| `Breadcrumb` | Breadcrumb path navigation | `Breadcrumb: { tag: 'nav' }` |
| `TabSet` | Horizontal tab bar | `TabSet: { children: [{ text: 'Overview', isActive: true }, { text: 'Details' }] }` |
| `Pagination` | Numbered page controls | `Pagination: { Flex: { children: [{ text: '1', isActive: true }, { text: '2' }, { text: '3' }] } }` |
| `NavigationDots` | Dot indicators for carousels | — |
| `NavigationArrows` | Previous/next arrow buttons | — |
| `ScrollableList` | Vertically scrollable menu list | — |

---

## Overlay & Disclosure

| Component | Use | Example |
|-----------|-----|---------|
| `Modal` | Dialog overlay container | `Modal: { Hgroup: { H: { text: 'Confirm action' } }, IconButton: { Icon: { name: 'x' } } }` |
| `MessageModal` | Informational modal | — |
| `Accordion` | Expandable/collapsible section | `Accordion: { ButtonParagraph: { P: { text: 'How does billing work?' } }, P: { text: 'You are billed monthly…' } }` |

---

## Data Display

| Component | Use | Example |
|-----------|-----|---------|
| `UnitValue` | Unit + value pair (price, stat) | `UnitValue: { Unit: { text: '$' }, Value: { text: '99' } }` |
| `BulletCaption` | Caption with colored bullet dot | `BulletCaption: { text: 'Orders', ':before': { background: 'blue' } }` |
| `StoryCard` | Full-bleed image card with overlay | — |
| `ListingItem` | Post/listing row item | — |
| `UserNavbar` | User profile row in navbar | `UserNavbar: { H: { text: 'Nika Tomadze' }, P: { text: 'Product Designer' } }` |
| `LoadingGif` | Animated loading spinner | `LoadingGif: { opacity: '.5', boxSize: 'B' }` |

---

## Misc

| Component | Use | Example |
|-----------|-----|---------|
| `Scrollbar` | Custom scrollbar with arrow navigation | `Scrollbar: { NavigationArrows: {} }` |
