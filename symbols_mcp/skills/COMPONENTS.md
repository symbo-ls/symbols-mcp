# Symbols / DOMQL v3 — Component Reference

All components use flattened props (no `props` wrapper) and `onX` v3 events. CSS props go at the top level and are auto-promoted to `element.props`.

---

## Built-in Atoms

| Atom       | HTML tag     | Primary use                   |
| ---------- | ------------ | ----------------------------- |
| `Text`     | `<span>`     | Inline text content           |
| `Box`      | `<div>`      | Generic container             |
| `Flex`     | `<div>`      | Flexbox layout container      |
| `Grid`     | `<div>`      | CSS Grid layout container     |
| `Link`     | `<a>`        | Navigation / external link    |
| `Input`    | `<input>`    | Text input                    |
| `Radio`    | `<input>`    | Radio button                  |
| `Checkbox` | `<input>`    | Checkbox                      |
| `Svg`      | `<svg>`      | Raw SVG container             |
| `Icon`     | `<svg>`      | Icon from sprite              |
| `IconText` | `<div>`      | Icon + text combo             |
| `Button`   | `<button>`   | Actionable control            |
| `Img`      | `<img>`      | Image element                 |
| `Iframe`   | `<iframe>`   | Embedded content              |
| `Video`    | `<video>`    | Video player                  |

### Text
```js
Text: { text: 'Hello', fontSize: 'B', color: 'title' }
```
Props: `text`, `color`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `textTransform`, `textDecoration`, `textAlign`, `maxWidth`, `overflow`, `whiteSpace`

### Box
```js
Box: { padding: 'A B', background: 'surface', borderRadius: 'B' }
```
Props: `padding`, `margin`, `border`, `borderRadius`, `background`, `shadow`, `width`, `height`, `minWidth`, `maxWidth`, `minHeight`, `maxHeight`, `position`, `inset`, `top`, `right`, `bottom`, `left`, `overflow`, `zIndex`

### Flex
```js
Flex: { flow: 'y', flexAlign: 'center space-between', gap: 'B' }
```
Props: `flow` / `flexFlow`, `flexAlign` (**not** `align`), `alignItems`, `justifyContent`, `gap`, `flex`, `flexGrow`, `flexShrink`, `flexBasis`, `wrap`

### Grid
```js
Grid: { columns: 'repeat(3, 1fr)', gap: 'A' }
```
Props: `columns` / `gridTemplateColumns`, `rows` / `gridTemplateRows`, `gap`, `columnGap`, `rowGap`, `gridAutoFlow`, `gridAutoColumns`, `gridAutoRows`

### Link
```js
Link: { text: 'Docs', href: '/docs' }
```
Props: `href`, `target`, `rel`, `text`, `color`, `textDecoration`, `onClick`

### Input
```js
Input: { type: 'text', name: 'title', placeholder: 'Enter title' }
```
Props: `type`, `name`, `value`, `placeholder`, `required`, `disabled`, `onInput`, `onChange`, `onKeydown`, `padding`, `background`, `border`, `round`

### Radio / Checkbox
```js
Checkbox: { name: 'agree', checked: true }
Radio: { name: 'opt', value: 'a' }
```
Props: `name`, `value`, `checked`, `disabled`, `onChange`

### Svg
```js
Svg: { html: '<path d="..." />', viewBox: '0 0 24 24', width: '22', height: '22' }
```
Props: `html` (inline SVG markup), `width`, `height`, `viewBox`, `fill`, `stroke`

**Rule**: Use `Svg` (not `Icon`) for SVGs inside `Button` or custom controls. Key MUST be `Svg`.

### Icon
```js
Icon: { name: 'chevronRight', boxSize: 'A' }
```
Props: `name` (sprite symbol id), `size` / `boxSize`, `color`

### IconText
```js
IconText: { icon: 'search', text: 'Search', gap: 'Z' }
```
Props: `icon`, `text`, `gap`, `flexAlign`, `color`

### Button
```js
Button: { text: 'Save', theme: 'primary', type: 'submit' }
```
Props: `text`, `icon`, `type`, `disabled`, `theme`, `padding`, `round`, `onClick`, `onSubmit`

### Img
```js
Img: { src: '/logo.png', alt: 'Logo', boxSize: 'B' }
```
Props: `src`, `alt`, `loading`, `width`, `height`, `boxSize`, `objectFit`

### Iframe
```js
Iframe: { src: 'https://example.com', width: '100%', height: '300px' }
```

### Video
```js
Video: { src: '/demo.mp4', controls: true, width: '100%' }
```

---

## Cross-cutting props (all atoms)

All atoms support:
- `@media` keys: `@mobile`, `@tablet`, `@tabletSm`, `@dark`, `@light`, etc.
- Pseudo selectors: `:hover`, `:active`, `:focus-visible`, etc.
- Conditional cases: `.isActive`, `.disabled`, `.hidden`, `!isActive`, etc.
- `childProps` — one-level child overrides
- `children` — arrays or nested object trees
- `onInit`, `onRender`, `onUpdate`, `onStateUpdate`

---

## Typography Components

| Component  | Tag       | Use                          |
| ---------- | --------- | ---------------------------- |
| `H1`–`H6`  | `<h1–h6>` | Semantic section headings    |
| `P`        | `<p>`     | Body paragraph text          |
| `Caption`  | `<span>`  | Small labels, hints          |
| `Headline` | `<span>`  | Display-size heading         |
| `Subhead`  | `<span>`  | Sub-section text             |
| `Footnote` | `<span>`  | Footer reference text        |
| `Strong`   | `<strong>`| Bold inline emphasis         |
| `Italic`   | `<em>`    | Italic inline emphasis       |
| `U`        | `<u>`     | Underline inline emphasis    |

All accept a `text` prop.

```js
H2: { text: 'Section title' }
P: { text: 'Body copy goes here.' }
Caption: { text: 'Updated 3 days ago', color: 'caption' }
```

---

## Dividers

| Component   | Use                                   |
| ----------- | ------------------------------------- |
| `Hr`        | Visual horizontal rule                |
| `HrLegend`  | Divider with centered label text      |

```js
Hr: { minWidth: 'F' }
HrLegend: { text: 'Or' }
```

---

## Buttons

| Component             | Use                                        |
| --------------------- | ------------------------------------------ |
| `IconButton`          | Icon-only circular button                  |
| `IconButtonSet`       | Group of icon buttons                      |
| `CounterButton`       | Button with notification badge             |
| `CounterIconButton`   | Icon button with positioned badge          |
| `IconCounterButton`   | Button with icon, label, and counter       |
| `UploadButton`        | Text button that opens file picker         |
| `UploadIconButton`    | Icon button that opens file picker         |
| `SubmitButton`        | Form submit button                         |
| `ButtonSet`           | Group of buttons                           |
| `ConfirmationButtons` | Yes/No pair                                |
| `InputButton`         | Email/text input with submit button inline |

```js
IconButton: { Icon: { name: 'plus' }, theme: 'dialog' }
ButtonSet: { children: [{ text: 'Cancel' }, { text: 'Save', theme: 'primary' }] }
ConfirmationButtons: { children: [{ text: 'Cancel' }, { text: 'Delete', theme: 'warning' }] }
InputButton: { Input: { placeholder: 'Enter email' }, Button: { text: 'Sign up' } }
SubmitButton: { value: 'Create account' }
```

---

## Avatar

| Component                  | Use                                       |
| -------------------------- | ----------------------------------------- |
| `Avatar`                   | Single avatar image                       |
| `AvatarSet`                | Overlapping group of avatars              |
| `AvatarStatus`             | Avatar with online/offline dot            |
| `AvatarHgroup`             | Avatar + heading group (name + subtitle)  |
| `AvatarBadgeHgroup`        | Avatar + heading + badge                  |
| `AvatarChatPreview`        | Avatar + message preview row              |

```js
Avatar: { boxSize: 'C2' }
AvatarStatus: { Avatar: { boxSize: 'C' }, StatusDot: { theme: 'success' } }
AvatarHgroup: { H: { text: 'Nika Tomadze' }, P: { text: 'Product Designer' } }
AvatarChatPreview: {
  H: { text: 'Design Team' },
  P: { text: 'Can you join us today?' },
  Value: { text: '2:20' }
}
```

---

## Badge & Notification

| Component              | Use                                    |
| ---------------------- | -------------------------------------- |
| `Badge`                | Colored label (status, category)       |
| `BadgeCaption`         | Caption label paired with a badge      |
| `NotificationCounter`  | Circular number badge                  |

```js
Badge: { text: 'New', theme: 'primary' }
BadgeCaption: { Caption: { text: 'Status' }, Badge: { text: 'Active', theme: 'success' } }
NotificationCounter: { text: '5' }
```

Themes: `primary`, `warning`, `success`, `transparent`, `bordered`, `dialog`, `field`

---

## Form & Input

| Component          | Use                                          |
| ------------------ | -------------------------------------------- |
| `Field`            | Styled input, optionally with trailing icon  |
| `FieldCaption`     | Field with label above                       |
| `IconInput`        | Input with overlaid icon                     |
| `Select`           | Native select                                |
| `SelectPicker`     | Styled select with chevron                   |
| `NumberPicker`     | Increment/decrement control                  |
| `Search`           | Search input with icon                       |
| `SearchDropdown`   | Filterable dropdown with search inside       |
| `TextareaIconButton` | Textarea with send button                  |

```js
Field: { Input: { placeholder: 'Enter name' }, Icon: { icon: 'user' } }
FieldCaption: { Caption: { text: 'Email' }, Field: { Input: { placeholder: 'you@example.com' } } }
SelectPicker: { Select: { children: [{ text: 'A', value: 'a' }, { text: 'B', value: 'b' }] } }
Search: { Input: { placeholder: 'Search…' } }
SearchDropdown: { state: { data: ['New York', 'Los Angeles'] } }
TextareaIconButton: { Textarea: { placeholder: 'Write a message…' } }
```

---

## Composition

Pair a primary element (heading, icon, image) with text content or controls:

| Component          | Use                                        |
| ------------------ | ------------------------------------------ |
| `ButtonHgroup`     | Heading group + button                     |
| `IconHeading`      | Icon + heading                             |
| `IconHgroup`       | Large icon + heading group                 |
| `ImgHgroup`        | Image + heading group                      |
| `SectionHeader`    | Section header with icon buttons           |
| `ValueHeading`     | Heading with trailing value/unit           |
| `IconTextSet`      | List of icon + text pairs                  |

```js
ButtonHgroup: { H: { text: 'Upgrade plan' }, P: { text: 'Get all features' }, Button: { text: 'Upgrade' } }
ImgHgroup: { Img: { src: '/icon.png', boxSize: 'C' }, H: { text: 'Product' }, P: { text: 'Tagline' } }
ValueHeading: { H: { tag: 'h6', text: 'Revenue' }, UnitValue: { Unit: { text: '$' }, Value: { text: '1,200' } } }
SectionHeader: { Hgroup: { H: { text: 'Activity' } }, IconButtonSet: { children: [{ Icon: { name: 'filter' } }] } }
```

---

## Selection

Three flavors — **Check**, **Radio**, **Toggle** — each in caption, hgroup, and list variants:

| Component              | Use                                |
| ---------------------- | ---------------------------------- |
| `CheckCaption`         | Checkbox + short label             |
| `CheckHgroup`          | Checkbox + title + description     |
| `CheckCaptionList`     | Stacked list of CheckCaption       |
| `RadioCaption`         | Radio + short label                |
| `RadioHgroup`          | Radio + title + description        |
| `ToggleCaption`        | Toggle switch + short label        |
| `ToggleHgroup`         | Toggle switch + title + desc       |
| `CheckStep` / `RadioStep` | Step with completion state     |

```js
CheckCaption: { Caption: { text: 'Accept terms' } }
ToggleHgroup: { H: { text: 'Email alerts' }, P: { text: 'Sent daily' } }
ToggleHgroupList: {
  children: [
    { H: { text: 'Email alerts' }, P: { text: 'Sent daily' } },
    { H: { text: 'Push notifications' }, P: { text: 'Instant' } }
  ]
}
CheckStep: { H6: { text: 'Verify email' }, Progress: { value: 1 } }
```

---

## Progress & Status

| Component            | Use                                  |
| -------------------- | ------------------------------------ |
| `Progress`           | Linear progress bar (value 0–1)      |
| `CircleProgress`     | Circular progress ring               |
| `ValueProgress`      | Progress bar + readable label        |
| `ProgressStepSet`    | Row of progress bars for steps       |
| `StatusDot`          | Small colored indicator dot          |
| `Stars`              | 5-star rating display                |

```js
Progress: { value: 0.6, height: 'X', round: 'Y' }
CircleProgress: { value: 0.73, boxSize: 'D' }
ValueProgress: { Progress: { value: 0.73 }, UnitValue: { Value: { text: '73' }, Unit: { text: '%' } } }
StatusDot: { theme: 'success' }
```

---

## Navigation & Links

| Component          | Use                                    |
| ------------------ | -------------------------------------- |
| `Link`             | Hyperlink                              |
| `LinkSet`          | Navigation list of links               |
| `Breadcrumb`       | Breadcrumb path navigation             |
| `TabSet`           | Horizontal tab bar                     |
| `Pagination`       | Numbered page controls                 |
| `NavigationDots`   | Dot indicators for carousels           |
| `NavigationArrows` | Previous/next arrow buttons            |
| `ScrollableList`   | Vertically scrollable menu list        |

```js
LinkSet: { tag: 'nav', children: [{ text: 'Home', href: '/' }, { text: 'Docs', href: '/docs' }] }
TabSet: { children: [{ text: 'Overview', isActive: true }, { text: 'Details' }] }
Pagination: { Flex: { children: [{ text: '1', isActive: true }, { text: '2' }, { text: '3' }] } }
Breadcrumb: { tag: 'nav' }
```

---

## Overlay & Disclosure

| Component      | Use                               |
| -------------- | --------------------------------- |
| `Modal`        | Dialog overlay container          |
| `MessageModal` | Informational modal               |
| `Accordion`    | Expandable/collapsible section    |

```js
Modal: { Hgroup: { H: { text: 'Confirm action' } }, IconButton: { Icon: { name: 'x' } } }
Accordion: {
  ButtonParagraph: { P: { text: 'How does billing work?' } },
  P: { text: 'You are billed monthly…' }
}
```

---

## Data Display

| Component          | Use                                   |
| ------------------ | ------------------------------------- |
| `UnitValue`        | Unit + value pair (price, stat, etc.) |
| `BulletCaption`    | Caption with colored bullet dot       |
| `StoryCard`        | Full-bleed image card with overlay    |
| `ListingItem`      | Post/listing row item                 |
| `UserNavbar`       | User profile row in navbar            |
| `LoadingGif`       | Animated loading spinner              |

```js
UnitValue: { Unit: { text: '$' }, Value: { text: '99' } }
BulletCaption: { text: 'Orders', ':before': { background: 'blue' } }
UserNavbar: { H: { text: 'Nika Tomadze' }, P: { text: 'Product Designer' } }
LoadingGif: { opacity: '.5', boxSize: 'B' }
```

---

## Misc

| Component   | Use                                     |
| ----------- | --------------------------------------- |
| `Scrollbar` | Custom scrollbar with arrow navigation  |

```js
Scrollbar: { NavigationArrows: {} }
```
