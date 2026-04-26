# Symbols / DOMQL Patterns Reference

Use these patterns as recipes when building Symbols/DOMQL components (flat element API, signal-based reactivity, modern smbls stack — fetch / polyglot / helmet / router). Each pattern is self-contained: apply it directly.

---

## UI Patterns

### Loading State

When to use: Any component that fetches data asynchronously.

```js
export const DataList = {
  state: { items: [], loading: true, error: null },

  Loader: { if: (el, s) => s.loading, extends: 'Spinner' },
  Error: {
    if: (el, s) => Boolean(s.error),
    role: 'alert',
    text: (el, s) => s.error
  },
  Items: {
    if: (el, s) => !s.loading && !s.error,
    children: (el, s) => s.items,
    childExtends: 'ListItem'
  },

  onRender: async (el, s) => {
    try {
      const items = await el.call('fetchItems')
      s.update({ items, loading: false })
    } catch (e) {
      s.update({ error: e.message, loading: false })
    }
  }
}
```

### Toggle / Accordion

When to use: Expandable/collapsible content sections.

```js
export const Accordion = {
  state: { open: false },
  Header: {
    flow: 'x',
    'aria-expanded': (el, s) => s.open,
    'aria-controls': 'accordion-body',
    onClick: (e, el, s) => s.parent.toggle('open')
  },
  Body: {
    id: 'accordion-body',
    if: (el, s) => s.open,
    html: (el, s) => el.content
  }
}
```

### Active List Item

When to use: Navigation menus or lists where one item is selected.

```js
export const Menu = {
  state: { active: null },
  childExtends: 'NavLink',
  childProps: {
    isActive: (el, s) => s.active === el.key,
    '.isActive': { fontWeight: '600', color: 'primary' },
    onClick: (e, el, s) => s.update({ active: el.key })
  }
}
```

`.isX` blocks are reactive — the framework re-applies the block whenever the state read by `isX` changes.

### Modal (complete pattern)

When to use: Dialog overlays with backdrop, focus trapping, and animated open/close.

```js
// components/ModalCard.js — reactive open/close via .isActive block
export const ModalCard = {
  position: 'absolute', align: 'center center',
  top: 0, left: 0, boxSize: '100% 100%',
  transition: 'all C defaultBezier',
  opacity: '0', visibility: 'hidden', pointerEvents: 'none', zIndex: '-1',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': { opacity: '1', zIndex: 999999, visibility: 'visible', pointerEvents: 'initial' },

  // Close on backdrop click, prevent close on content click
  onClick: (e, el) => el.call('closeModal'),
  childProps: { onClick: (e) => e.stopPropagation() },

  // ARIA
  role: 'dialog',
  'aria-modal': 'true',
  'aria-label': '{{ dialog | polyglot }}',

  // Trap focus on first focusable child after render
  onRender: (el) => { el.call('focusFirstChild') },
  onKeydown: (e, el) => {
    if (e.key === 'Escape') el.call('closeModal')
  },

  InnerContent: { /* ... */ }
}

// functions/showModal.js — declarative state update; CSS transitions handle the fade
export const showModal = function showModal (path) {
  this.state.root.update({ activeModal: true }, { onlyUpdate: 'ModalCard' })
}

// functions/closeModal.js
export const closeModal = function closeModal () {
  this.state.root.update({ activeModal: false }, { onlyUpdate: 'ModalCard' })
}
```

### Tab Switching

When to use: Multi-view tab interfaces. Use state to track active view — never DOM manipulation.

```js
// Page with tabs
export const dashboard = {
  extends: 'Page',
  state: { activeTab: 'home' },

  Navbar: {
    flow: 'x',
    gap: 'A',
    HomeBtn: {
      extends: 'Button',
      text: '{{ home | polyglot }}',
      onClick: (e, el, s) => s.update({ activeTab: 'home' })
    },
    ExploreBtn: {
      extends: 'Button',
      text: '{{ explore | polyglot }}',
      onClick: (e, el, s) => s.update({ activeTab: 'explore' })
    },
  },

  HomeView: {
    flow: 'y',
    if: (el, s) => s.activeTab === 'home',
  },
  ExploreView: {
    flow: 'y',
    if: (el, s) => s.activeTab === 'explore',
  },
}
```

### Dynamic Class Toggle

When to use: Conditionally applying a style based on props or state. Use the `.isX` block for grouped reactive CSS — the framework re-applies the block whenever the state read by `isX` changes.

```js
export const Button = {
  background: 'transparent',
  color: 'currentColor',
  isActive: (el, s) => s.active,
  '.isActive': { background: 'primary', color: 'white' }
}
```

For a single property switching on a condition, a direct reactive CSS prop function is also fine:

```js
export const Button = {
  background: (el, s) => s.active ? 'primary' : 'transparent'
}
```

### Dynamic Form / Async Submit

When to use: Forms with async submission, loading indicators, and inline error display.

```js
export const LoginForm = {
  tag: 'form',
  state: { loading: false, error: null },
  'aria-live': 'polite',

  onSubmit: async (event, el, s) => {
    event.preventDefault()
    s.update({ loading: true, error: null })
    try {
      await el.call('login', new FormData(el.node))
      el.router('/dashboard', el.getRoot())
    } catch (e) {
      s.update({ loading: false, error: e.message })
    }
  },

  Field: {
    Input: { type: 'email', name: 'email', required: true }
  },
  Error: {
    if: (el, s) => Boolean(s.error),
    role: 'alert',
    text: (el, s) => s.error,
    color: 'red'
  },
  SubmitButton: {
    'aria-busy': (el, s) => s.loading,
    text: (el, s) => s.loading ? '{{ signing_in | polyglot }}' : '{{ sign_in | polyglot }}'
  }
}
```

### Responsive Layout

When to use: Grid-based layouts that adapt across breakpoints.

```js
export const Layout = {
  extends: 'Grid',
  columns: 'repeat(4, 1fr)',
  gap: 'B',

  '@tabletS': { columns: 'repeat(2, 1fr)' },
  '@mobileL': { columns: '1fr', gap: 'A' },
}
```

---

## Accessibility

### Semantic Atoms First

Always prefer built-in semantic atoms over generic containers.

```js
// CORRECT -- semantic atoms
Button: { text: '{{ submit | polyglot }}' }                                   // <button>
Link: { text: '{{ dashboard | polyglot }}', href: '/dashboard' }              // <a>
Input: { placeholder: '{{ search_placeholder | polyglot }}' }                 // <input>
Nav: { Link: { text: '{{ home | polyglot }}', href: '/' } }                   // <nav>
Header: {}                                                                    // <header>
Footer: {}                                                                    // <footer>
Main: {}                                                                      // <main>

// WRONG -- loses semantics
Box: { tag: 'div', text: '{{ submit | polyglot }}', onClick: fn }            // div is not a button
```

### ARIA Attributes

```js
// Landmark roles
Box: { role: 'alert', text: '{{ error_occurred | polyglot }}' }
Box: { role: 'status', aria: { live: 'polite' }, text: (el, s) => s.resultsLabel }

// Labels — three equivalent forms:
Input: { ariaLabel: '{{ search_networks | polyglot }}' }                       // camelCase
Button: { icon: 'x', aria: { label: '{{ close_dialog | polyglot }}' } }        // object shorthand
Icon: { name: 'settings', 'aria-hidden': 'true' }                              // kebab-case

// Dynamic state via flat reactive props (preferred — flat access)
Button: {
  'aria-expanded': (el, s) => s.isOpen,
  'aria-controls': 'dropdown-menu',
  onClick: (e, el, s) => s.update({ isOpen: !s.isOpen })
}

// Or via reactive conditional cases (.isX / '!isX') — also reactive
Button: {
  isOpen: (el, s) => s.isOpen,
  '.isOpen': { aria: { expanded: true } },
  '!isOpen': { ariaHidden: true }
}
```

### Keyboard Navigation

When to use: Custom interactive widgets (listbox, dropdown, menu).

```js
// Custom keyboard interaction (listbox pattern)
{
  flow: 'y',
  role: 'listbox', tabindex: '0',
  'aria-label': '{{ select_option | polyglot }}',
  onKeydown: (e, el, s) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      s.update({ activeIndex: Math.min(s.activeIndex + 1, s.items.length - 1) })
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      s.update({ activeIndex: Math.max(s.activeIndex - 1, 0) })
    }
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      el.call('selectItem', s.items[s.activeIndex])
    }
    if (e.key === 'Escape') el.call('closeDropdown')
  }
}
```

#### Tabindex Rules

| Value | Behavior |
|-------|----------|
| `tabindex: '0'` | Element is in the natural tab order |
| `tabindex: '-1'` | Focusable programmatically only (not via Tab key) |
| `tabindex > 0` | **Never use.** Breaks natural tab order. |

### Focus Styles

```js
Button: {
  ':focus': { outline: 'none' },
  ':focus-visible': { outline: 'solid Y blue.3', outlineOffset: 'X' }
}
```

### Accessible Forms

```js
// Visible label association
Label: { text: '{{ email | polyglot }}', for: 'email-input' }
Input: { id: 'email-input', type: 'email', required: true, 'aria-required': 'true' }

// Described by helper text
Input: { id: 'password', type: 'password', 'aria-describedby': 'password-hint' }
P: { id: 'password-hint', text: '{{ password_hint | polyglot }}' }

// Error state — flat reactive ARIA props
Input: {
  'aria-invalid': (el, s) => s.hasError ? 'true' : undefined,
  'aria-describedby': (el, s) => s.hasError ? 'error-msg' : undefined
}
P: { id: 'error-msg', role: 'alert', color: 'red', text: (el, s) => s.errorMessage }
```

### Images and Icons

```js
// Informative image
Img: { src: 'chart.png', alt: '{{ chart_alt | polyglot }}' }

// Decorative image
Img: { src: 'decoration.png', alt: '', 'aria-hidden': 'true' }

// Icon-only button
Button: { icon: 'x', 'aria-label': '{{ close | polyglot }}' }

// Decorative icon next to text
Button: { Icon: { name: 'search', 'aria-hidden': 'true' }, text: '{{ search | polyglot }}' }
```

### Color and Contrast

- Do NOT rely on color alone for error/success states -- always combine with icon + text.
- Use `title`, `caption`, `paragraph` semantic tokens for sufficient contrast.
- Low opacity colors (`gray 0.3`) likely fail WCAG AA -- verify contrast ratio.

---

## AI Agent Optimization

### `aid-*` Attributes for Machine Parsing

Add `aid-*` attributes so AI agents can parse structural intent.

```js
export const HeroSection = {
  extends: 'Section',
  'aid-type': 'main',
  'aid-desc': 'Primary hero section with CTA',
  'aid-state': 'idle',
  'aid-cnt-type': 'info',
  H1: { text: '{{ hero_title | polyglot }}' },
  P: { text: '{{ hero_subtitle | polyglot }}' },
  Button: { text: '{{ get_started | polyglot }}', theme: 'primary' }
}
```

#### `aid-type` Values

| Value | Meaning |
|-------|---------|
| `header` | Page header |
| `nav` | Navigation |
| `main` | Primary content |
| `content` | Content section |
| `complementary` | Supplementary (sidebar, aside) |
| `interactive` | Form, control panel |
| `modal` | Dialog overlay |
| `alert` | Error or notification |
| `search` | Search interface |

#### `aid-state` Values

| Value | Meaning |
|-------|---------|
| `idle` | Default state |
| `loading` | Fetching data |
| `processing` | Submitting/computing |
| `done` | Completed |
| `error` | Error state |

### JSON-LD Structured Data

When to use: Entity representation for AI agents and search engines.

```js
export const StructuredData = {
  tag: 'script',
  type: 'application/ld+json',
  html: (el, s) => JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: s.name,
    description: s.description,
    offers: {
      '@type': 'Offer',
      price: s.price,
      priceCurrency: s.currency,
    },
  }),
}
```

Supported schema types: `Organization`, `Product`, `Service`, `Article`, `FAQPage`, `BreadcrumbList`.

Structured data must match server-rendered content exactly.

### Semantic Heading Structure

- One `H1` per page defining the primary subject.
- Logical hierarchy: H1 then H2 then H3 -- never skip levels.
- AI agents use heading hierarchy to determine page structure.

### AI-Accessible Tool Exposure (Chrome WebMCP)

When to use: Exposing form-based tools for AI agent interaction via MCP.

```js
export const CheckOrderTool = {
  extends: 'Form',
  'data-mcp-tool': 'checkOrderStatus',
  'data-mcp-description': 'Check the status of an order by ID',
  Input: { type: 'text', name: 'orderId', placeholder: '{{ order_id | polyglot }}' },
  Button: { type: 'submit', text: '{{ check | polyglot }}' }
}
```

### llms.txt Support

Provide `/llms.txt` at your project root for AI routing guidance.

```text
# Organization Name
# Purpose: Platform description

## Key pages
- /products
- /api/docs
- /support

## Preferred interactions
- /api/v2/ programmatic access
- /search?q= for search

## Data accuracy notes
- Prices, shipping, inventory levels
```

### Server-Rendered Critical Content

- All critical content (text, headings, prices, key data) must be server-rendered in the initial HTML.
- Do not rely on client-side-only rendering for content AI agents need to parse.
- Set `aria-busy="true"` while loading; `aria-busy="false"` when complete.

### Anti-Patterns (Failure Pattern Recognition)

Avoid these -- they break AI comprehension:

- Excessive divs/boxes without semantic meaning.
- Non-descriptive link text ("click here", "read more").
- Missing or skipped heading levels.
- Critical content rendered client-side only.
- Conflicting metadata (page title vs. H1 vs. JSON-LD).
- Missing `alt` text on informative images.

---

## Modern Stack (mandatory for non-trivial apps)

### Declarative `fetch:` prop

When to use: Any element that needs server data. **Never call `window.fetch` from a component.** Use the declarative `fetch:` prop — Symbols dedupes, caches, and re-runs the request reactively.

```js
// CORRECT — declarative fetch
export const ProjectList = {
  state: { items: [] },

  fetch: {
    url: (el, s) => `/api/projects?org=${s.root.orgId}`,
    method: 'GET',
    onSuccess: (data, el, s) => s.update({ items: data.projects }),
    onError: (err, el, s) => s.update({ error: err.message })
  },

  childExtends: 'ProjectTile',
  children: (el, s) => s.items
}

// WRONG — imperative fetch in lifecycle
export const ProjectList = {
  onRender: async (el, s) => {
    const res = await window.fetch('/api/projects')   // ❌ no
    const json = await res.json()
    s.update({ items: json.projects })
  }
}
```

The `fetch:` prop:
- Re-runs whenever the reactive `url` changes.
- Hands `data` to `onSuccess(data, el, s)`.
- Hands errors to `onError(err, el, s)`.
- Aborts in-flight requests on element teardown.

### Polyglot — internationalised strings

**All user-facing strings MUST go through polyglot.** Never hardcode text. Use the `{{ key | polyglot }}` template — values resolve from `context.polyglot.translations` (or root-level `lang.js`, NOT inside `designSystem/`).

```js
// CORRECT
H1: { text: '{{ welcome | polyglot }}' }
Button: { text: '{{ get_started | polyglot }}' }
Input: { placeholder: '{{ search_placeholder | polyglot }}' }
Img: { alt: '{{ profile_avatar_alt | polyglot }}' }

// WRONG — hardcoded English breaks every locale
H1: { text: 'Welcome' }
Button: { text: 'Get Started' }
```

Reactive variants:

```js
// String key from state
text: (el, s) => `{{ ${s.heading_key} | polyglot }}`

// With interpolation
text: '{{ greeting | polyglot }}'   // locale: { greeting: 'Hello, {{name}}!' }
```

Locale file:

```js
// symbols/lang.js  (root-level — NOT inside designSystem/)
//   OR set context.polyglot.translations = { en: {...}, ka: {...}, ... } in context.js
export default {
  en: { welcome: 'Welcome', get_started: 'Get Started' },
  ka: { welcome: 'მოგესალმებით', get_started: 'დაიწყე' },
  ru: { welcome: 'Добро пожаловать', get_started: 'Начать' }
}
```

### Helmet — page metadata

When to use: Page-level head/meta updates (title, description, OG tags, canonical). Use the declarative `metadata:` prop (NOT `helmet:` — the prop name is `metadata`) via `@symbo.ls/helmet`. Never write to `document.title`.

```js
// CORRECT — declarative metadata
export const productPage = {
  extends: 'Page',
  state: { product: null },

  metadata: (el, s) => ({
    title:        s.product ? `${s.product.name} — Symbols` : '{{ loading | polyglot }}',
    description:  s.product?.description || '',
    canonical:    s.product ? `https://symbols.app/products/${s.product.slug}` : '',
    'og:title':   s.product?.name,
    'og:image':   s.product?.heroImage,
    'og:type':    'product',
    'twitter:card': 'summary_large_image'
  }),

  // ... rest of page
}

// WRONG — never use document or window APIs
export const productPage = {
  onRender: (el, s) => {
    document.title = s.product.name    // ❌ no
  }
}
```

### Theme handling — `@dark` / `@light` and `theme:` token

Symbols supports OS-level theme switching automatically. Two ways to make a component theme-aware:

```js
// 1. Variant blocks — render-time theme overrides
Card: {
  background: 'surface',                          // base (light)
  '@dark': { background: 'surfaceDark' },         // dark mode override
  '@light': { boxShadow: 'A' }                    // explicit light override
}

// 2. theme: token — pull from designSystem.theme
Button: {
  theme: 'primary',                               // resolves to design system theme block
  '@dark': { theme: 'primaryDark' }
}

// 3. Reactive theme based on state
Banner: {
  theme: (el, s) => s.danger ? 'warning' : 'info'
}
```

Never read `prefers-color-scheme` manually — Symbols wires it through `context.theme` and the `@dark` / `@light` variant blocks. Toggle the theme by updating the root state:

```js
// Toggle dark mode — wrap changeGlobalTheme in a registered project function.

// functions/switchTheme.js
import { changeGlobalTheme } from 'smbls'
export function switchTheme () {
  const next = this.context.globalTheme === 'dark' ? 'light' : 'dark'
  changeGlobalTheme(next, this.context.designSystem)
  try { (this.context.window || window).localStorage.setItem('my-app-theme', next) } catch (e) {}
}

// components/ToggleThemeButton.js
ToggleThemeButton: {
  text: '{{ toggle_theme | polyglot }}',
  onClick: (e, el) => el.call('switchTheme')
}
```

### Router — declarative navigation

```js
// CORRECT — declarative routing
NavLink: {
  extends: 'Link',
  href: '/dashboard',
  text: '{{ dashboard | polyglot }}',
  onClick: (e, el) => {
    e.preventDefault()
    el.router('/dashboard', el.getRoot())
  }
}

// WRONG — never touch window.location
NavLink: {
  onClick: () => { window.location = '/dashboard' }   // ❌ no
}
```

---

## Design Principles

### Component Button Hierarchy

| Level | Component | Use |
|-------|-----------|-----|
| Primary | `theme: 'primary'` | Main CTA (one per view) |
| Secondary | `theme: 'dialog'` | Supporting actions |
| Tertiary | `theme: 'transparent'` | Least important |
| Destructive | `theme: 'warning'` | Irreversible actions |

### Responsive Behavior

When to use: Mobile-first progressive enhancement.

```js
Component: {
  padding: 'A',                              // mobile base
  '@tabletS': { padding: 'B' },             // tablet
  '@screenS': { padding: 'C' },             // desktop
}
```

### Transitions and Micro-interactions

```js
// Standard transition
Component: {
  transition: 'B defaultBezier',            // B = 280ms
  transitionProperty: 'opacity, transform'
}

// Hover feedback
Button: {
  ':hover': { opacity: 0.9, transform: 'scale(1.015)' },
  ':active': { opacity: 1, transform: 'scale(0.995)' }
}
```

Easing: `defaultBezier` = `cubic-bezier(.29, .67, .51, .97)` (smooth ease-out).

Do NOT animate layout properties (`width`, `height`, `top`, `left`) -- they force reflow. Animate `transform` and `opacity` instead.

---

### Page Entry Animation

When to use: Any page or main content area that should fade in when navigated to.

Define a custom keyframe in `designSystem/animation.js`, then apply it via `style.animation` on the layout container:

```js
// designSystem/animation.js
export default {
  fadeInPage: {
    keyframes: {
      '0%': { opacity: '0', transform: 'translateY(10px)' },
      '100%': { opacity: '1', transform: 'translateY(0)' },
    },
  },
}

// pages/dashboard.js
export const dashboard = {
  extends: 'Page',

  Layout: {
    flow: 'y',
    flex: '1',
    style: { animation: 'fadeInPage 0.3s ease' },
    // ... rest of layout
  },
}
```

Apply on the outermost content container (not the page root or nav) so the nav stays stable during the transition.

---

### Inline Dot Separator

When to use: Horizontal meta rows (e.g. "Category · City · $$$") where items are conditionally shown.

Use explicit sibling separator elements rather than embedding dots in text strings. This keeps each item independently reactive:

```js
MetaRow: {
  flow: 'x', gap: 'X', align: 'center', flexWrap: 'wrap',

  TypeTag: {
    text: (el, s) => s.type || '',
    fontSize: 'Z', color: 'accent', fontWeight: '600',
  },
  Sep1: {
    show: (el, s) => !!(s.city),
    text: '·', fontSize: 'Z', color: 'neutral400',
  },
  CityTag: {
    text: (el, s) => s.city || '',
    fontSize: 'Z', color: 'neutral400',
  },
  Sep2: {
    show: (el, s) => !!(s.price),
    text: '·', fontSize: 'Z', color: 'neutral400',
  },
  PriceTag: {
    show: (el, s) => !!(s.price),
    text: (el, s) => s.price || '',
    fontSize: 'Z', color: 'neutral400',
  },
}
```

Each separator's `show` mirrors the adjacent item's condition so dots never appear orphaned.
