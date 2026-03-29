# Default Library — Fundamental Component Layer

## What It Contains

The default library (`default.symbo.ls`) provides 127+ pre-built, production-ready components. Included automatically when creating projects via `smbls create` (Default option) or the Symbols platform. Choose "Blank" for an empty project.

---

## Component Tables

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
| `Icon` | SVG icon from icon set |
| `IconText` | Icon + text combination |
| `IconHeading` | Icon + heading |

---

## Extension Chain

Components form a three-level inheritance chain:

```
UIKit Atom (Box, Flex, etc.)
  -> Default Library Component (Button, Avatar, etc.)
    -> Your Project Component (MyButton, ProfileAvatar, etc.)
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

---

## Design System Integration

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

See PROJECT_STRUCTURE.md for full project layout, router pattern, and entry point setup.
