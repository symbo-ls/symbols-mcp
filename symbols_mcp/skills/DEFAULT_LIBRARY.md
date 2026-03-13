# Default Library — Fundamental Component Layer

## Overview

Symbols projects can include a **default library** (`default.symbo.ls`) — a foundational layer of pre-built, production-ready components. This library provides the building blocks that most applications need, so you don't start from scratch.

When creating a project via the CLI (`smbls create`), users are prompted:
- **Default (recommended)** — includes `default.symbo.ls` library
- **Blank** — empty project, no pre-built components

Projects created on the Symbols platform automatically include the default library.

---

## What the Default Library Contains

The default library includes **127+ components** organized into categories:

### Atoms (Foundation)
Core building blocks that everything else extends:

| Component | Extends | Purpose |
|-----------|---------|---------|
| `Box` | — | Generic container with CSS-in-props |
| `Text` | — | Text rendering (H1-H6, P, Caption, etc.) |
| `Flex` | `Box` | Flexbox layout |
| `Grid` | `Box` | CSS Grid layout |
| `Form` | `Box` | Form container |
| `Hgroup` | `Flex` | Heading group |
| `Img` | — | Image element |
| `Svg` | — | SVG container |
| `Video` | — | Video element |
| `Iframe` | — | Embedded frame |
| `Shape` | `Box` | Shape utilities |

### Buttons
| Component | Description |
|-----------|-------------|
| `Button` | Base button with text/icon support |
| `IconButton` | Button with icon only |
| `SquareButton` | Fixed-aspect button |
| `CircleButton` | Circular button |
| `SubmitButton` | Form submit button |
| `UploadButton` | File upload trigger |
| `CounterButton` | Button with counter badge |
| `ButtonSet` | Group of buttons |
| `ConfirmationButtons` | Confirm/Cancel pair |

### Inputs & Forms
| Component | Description |
|-----------|-------------|
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
|-----------|-------------|
| `Avatar` | User avatar (extends Img) |
| `AvatarSet` | Group of avatars |
| `AvatarStatus` | Avatar with status indicator |
| `AvatarHgroup` | Avatar + name/description |

### Data Display
| Component | Description |
|-----------|-------------|
| `Badge` | Status/count badge |
| `StatusDot` | Colored status indicator |
| `Progress` | Progress bar |
| `CircleProgress` | Circular progress |
| `Stars` | Star rating |
| `UnitValue` | Number + unit display |

### Navigation
| Component | Description |
|-----------|-------------|
| `Link` | Navigation link with router |
| `LinkSet` | Group of links |
| `Breadcrumb` | Breadcrumb navigation |
| `TabSet` | Tab navigation |
| `Pagination` | Page navigation |

### Feedback & Overlay
| Component | Description |
|-----------|-------------|
| `Modal` | Modal dialog |
| `Notification` | Notification banner |
| `Tooltip` | Hover tooltip |
| `Dropdown` | Dropdown menu |
| `Accordion` | Expandable sections |

### Icons
| Component | Description |
|-----------|-------------|
| `Icon` | SVG icon from icon set |
| `IconText` | Icon + text combination |
| `IconHeading` | Icon + heading |

---

## How Components Extend the Library

Default library components are available by PascalCase key name — no imports needed:

```js
// Your component automatically extends the library's Button
export const MyButton = {
  extends: 'Button',
  text: 'Click Me',
  theme: 'primary',
  padding: 'Z2 B',
}

// PascalCase keys auto-extend matching components
export const MyCard = {
  extends: 'Flex',
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

## Extension Chain

Components form an extension chain:

```
UIKit Atom (Box, Flex, etc.)
  → Default Library Component (Button, Avatar, etc.)
    → Your Project Component (MyButton, ProfileAvatar, etc.)
```

Example:
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

---

## Design System Integration

The default library components automatically use your project's design system tokens:

```js
// designSystem/index.js
export default {
  COLOR: {
    primary: '#2563EB',
    surface: '#F8FAFC',
    text: '#0F172A',
  },
  THEME: {
    primary: {
      background: 'primary',
      color: 'white',
    },
    card: {
      background: 'surface',
      borderRadius: 'A',
    },
  },
  TYPOGRAPHY: {
    base: 16,
    ratio: 1.25,
  },
  SPACING: {
    base: 16,
    ratio: 1.618,
  },
}
```

When you use `theme: 'primary'` on a Button, it pulls colors from YOUR design system, not hardcoded values.

---

## Project Structure with Default Library

```
project/
├── symbols.json              # { "key": "myapp.symbo.ls", "bundler": "parcel" }
├── symbols/
│   ├── index.js              # Entry: create(app, context)
│   ├── app.js                # Root app with router
│   ├── config.js             # { globalTheme: 'dark' }
│   ├── context.js            # Re-exports all modules
│   ├── state.js              # App state
│   ├── dependencies.js       # External packages
│   ├── components/           # Your custom components (extend library)
│   │   ├── index.js          # Named exports
│   │   ├── Header.js
│   │   └── Hero.js
│   ├── pages/                # Route pages
│   │   ├── index.js          # Route map: { '/': home, '/about': about }
│   │   ├── home.js
│   │   └── about.js
│   ├── designSystem/         # Your tokens override defaults
│   │   ├── index.js
│   │   ├── COLOR.js
│   │   ├── THEME.js
│   │   ├── TYPOGRAPHY.js
│   │   └── SPACING.js
│   ├── functions/            # Utility functions
│   ├── snippets/             # Reusable snippets
│   └── methods/              # Custom methods
```

---

## Router Pattern

Pages use the router with the default library's layout components:

```js
// pages/index.js
import { home } from './home.js'
import { about } from './about.js'
import { contact } from './contact.js'

export default {
  '/': home,
  '/about': about,
  '/contact': contact,
}
```

```js
// pages/home.js
export const home = {
  flow: 'y',
  width: '100%',
  minHeight: '100vh',

  Header: {},          // Uses your Header component
  Hero: {},            // Uses your Hero component
  FeatureGrid: {},     // Uses your FeatureGrid component
  Footer: {},          // Uses your Footer component
}
```

---

## App Entry Point

```js
// app.js
export const app = {
  routes: (pages) => pages,
}
```

```js
// index.js
import { create } from 'smbls'
import * as context from './context.js'
import { app } from './app.js'

create(app, context)
```

```js
// context.js
export { default as state } from './state.js'
export { default as pages } from './pages/index.js'
export { default as designSystem } from './designSystem/index.js'
export * as components from './components/index.js'
export * as functions from './functions/index.js'
export * as snippets from './snippets/index.js'
```

---

## Key Rules When Using Default Library

1. **Never import components** — reference by PascalCase key name
2. **extends is required** to inherit library behavior — `extends: 'Button'`
3. **PascalCase keys auto-extend** — `Avatar: {}` automatically extends the registered Avatar
4. **Design tokens override** — your designSystem tokens take precedence
5. **Flat folders only** — no subfolders in components/, pages/, etc.
6. **Named exports** for components — `export const MyComp = { ... }`
7. **Default exports** for state/pages/config — `export default { ... }`
