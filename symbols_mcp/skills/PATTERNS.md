# Symbols / DOMQL Patterns Reference

Use these patterns as recipes when building Symbols/DOMQL components. Each pattern is self-contained: apply it directly.

---

## UI Patterns

### Loading State

When to use: Any component that fetches data asynchronously.

```js
export const DataList = {
  state: { items: [], loading: true, error: null },

  Loader: { if: ({ state }) => state.loading, extends: 'Spinner' },
  Error: {
    if: ({ state }) => Boolean(state.error),
    role: 'alert',
    text: ({ state }) => state.error
  },
  Items: {
    if: ({ state }) => !state.loading && !state.error,
    children: ({ state }) => state.items,
    childExtends: 'ListItem'
  },

  onRender: async (el, state) => {
    try {
      const items = await el.call('fetchItems')
      state.update({ items, loading: false })
    } catch (e) {
      state.update({ error: e.message, loading: false })
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
    attr: (el, s) => ({
      'aria-expanded': s.open,
      'aria-controls': 'accordion-body'
    }),
    onClick: (ev, el) => { el.parent.state.toggle('open') }
  },
  Body: {
    id: 'accordion-body',
    if: ({ state }) => state.open,
    html: ({ props }) => props.content
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
    isActive: ({ key, state }) => state.active === key,
    '.active': { fontWeight: '600', color: 'primary' },
    onClick: (ev, el, state) => { state.update({ active: el.key }) }
  }
}
```

### Modal (v3 complete pattern)

When to use: Dialog overlays with backdrop, focus trapping, and animated open/close.

```js
// components/ModalCard.js
export const ModalCard = {
  position: 'absolute', align: 'center center',
  top: 0, left: 0, boxSize: '100% 100%',
  transition: 'all C defaultBezier',
  opacity: '0', visibility: 'hidden', pointerEvents: 'none', zIndex: '-1',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': { opacity: '1', zIndex: 999999, visibility: 'visible', pointerEvents: 'initial' },

  // Close on backdrop click, prevent close on content click
  onClick: (event, element) => { element.call('closeModal') },
  childProps: { onClick: (ev) => { ev.stopPropagation() } },

  // ARIA
  role: 'dialog',
  attr: { 'aria-modal': 'true', 'aria-label': 'Dialog' },

  // Trap focus
  onRender: (el) => {
    const focusable = el.node.querySelectorAll('button, [href], input, [tabindex]:not([tabindex="-1"])')
    if (focusable.length) focusable[0].focus()
  },
  onKeydown: (e, el) => {
    if (e.key === 'Escape') el.call('closeModal')
  },

  InnerContent: { /* ... */ }
}

// functions/showModal.js
export const showModal = function showModal(path) {
  const modalEl = this.lookup('ModalCard')
  const modalNode = modalEl.node
  // FadeIn: force browser to paint opacity:0 before transition to opacity:1
  modalNode.style.opacity = '0'
  modalNode.style.visibility = 'visible'
  this.state.root.update({ activeModal: true }, { onlyUpdate: 'ModalCard' })
  modalNode.style.opacity = '0'
  modalNode.offsetHeight  // force reflow
  modalNode.style.opacity = ''
}

// functions/closeModal.js
export const closeModal = function closeModal() {
  const modalEl = this.lookup('ModalCard')
  const modalNode = modalEl.node
  modalNode.style.opacity = '0'
  setTimeout(() => {
    modalNode.style.opacity = ''
    modalNode.style.visibility = ''
    this.state.root.update({ activeModal: false }, { onlyUpdate: 'ModalCard' })
  }, 280)  // match CSS transition duration
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
      text: 'Home',
      onClick: (e, el, s) => s.update({ activeTab: 'home' })
    },
    ExploreBtn: {
      extends: 'Button',
      text: 'Explore',
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

When to use: Conditionally applying a style class based on props or state.

```js
export const Button = {
  '.active': { background: 'primary', color: 'white' },
  isActive: ({ props }) => props.active  // adds/removes .active class
}
```

### Dynamic Form / Async Submit

When to use: Forms with async submission, loading indicators, and inline error display.

```js
export const LoginForm = {
  tag: 'form',
  state: { loading: false, error: null },
  attr: { 'aria-live': 'polite' },

  onSubmit: async (event, el, state) => {
    event.preventDefault()
    state.update({ loading: true, error: null })
    try {
      await el.call('login', new FormData(el.node))
      el.router('/dashboard', el.getRoot())
    } catch (e) {
      state.update({ loading: false, error: e.message })
    }
  },

  Field: {
    Input: { type: 'email', name: 'email', required: 'true' }
  },
  Error: {
    if: ({ state }) => Boolean(state.error),
    role: 'alert',
    text: ({ state }) => state.error,
    color: 'red'
  },
  SubmitButton: {
    attr: (el, s) => ({ 'aria-busy': s.loading }),
    text: ({ state }) => state.loading ? 'Signing in…' : 'Sign in'
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
Button: { text: 'Submit' }                           // <button>
Link: { text: 'Dashboard', href: '/dashboard' }      // <a>
Input: { placeholder: 'Search...' }                  // <input>
Nav: { Link: { text: 'Home', href: '/' } }           // <nav>
Header: {}                                           // <header>
Footer: {}                                           // <footer>
Main: {}                                             // <main>

// WRONG -- loses semantics
Box: { tag: 'div', text: 'Submit', onClick: fn }    // div is not a button
```

### ARIA Attributes

```js
// Landmark roles
Box: { role: 'alert', text: 'Error occurred' }
Box: { role: 'status', aria: { live: 'polite' }, text: '3 results found' }

// Labels — three equivalent forms:
Input: { ariaLabel: 'Search networks' }                    // camelCase
Button: { icon: 'x', aria: { label: 'Close dialog' } }    // object shorthand
Icon: { name: 'settings', 'aria-hidden': 'true' }         // kebab-case

// Dynamic state via attr block (functions)
Button: {
  attr: (el, s) => ({ 'aria-expanded': s.isOpen, 'aria-controls': 'dropdown-menu' }),
  onClick: (e, el, s) => s.update({ isOpen: !s.isOpen })
}

// Dynamic state via conditional cases
Button: {
  '.isOpen': { aria: { expanded: true } },
  '!isOpen': { ariaHidden: true },
  onClick: (e, el, s) => s.update({ isOpen: !s.isOpen })
}
```

### Keyboard Navigation

When to use: Custom interactive widgets (listbox, dropdown, menu).

```js
// Custom keyboard interaction (listbox pattern)
{
  flow: 'y',
  role: 'listbox', tabindex: '0',
  attr: { 'aria-label': 'Select option' },
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
  ':focus-visible': { outline: 'solid Y blue.3', outlineOffset: '2px' }
}
```

### Accessible Forms

```js
// Visible label association
Label: { text: 'Email', for: 'email-input' }
Input: { id: 'email-input', type: 'email', required: 'true', attr: { 'aria-required': 'true' } }

// Described by helper text
Input: { id: 'password', type: 'password', attr: { 'aria-describedby': 'password-hint' } }
P: { id: 'password-hint', text: 'Must be at least 8 characters' }

// Error state
Input: {
  attr: (el, s) => ({
    'aria-invalid': s.hasError ? 'true' : undefined,
    'aria-describedby': s.hasError ? 'error-msg' : undefined
  })
}
P: { id: 'error-msg', role: 'alert', color: 'red', text: (el, s) => s.errorMessage }
```

### Images and Icons

```js
// Informative image
Img: { src: 'chart.png', alt: 'Network uptime over last 30 days' }

// Decorative image
Img: { src: 'decoration.png', alt: '', attr: { 'aria-hidden': 'true' } }

// Icon-only button
Button: { icon: 'x', attr: { 'aria-label': 'Close' } }

// Decorative icon next to text
Button: { Icon: { name: 'search', attr: { 'aria-hidden': 'true' } }, text: 'Search' }
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
  attr: {
    'aid-type': 'main',
    'aid-desc': 'Primary hero section with CTA',
    'aid-state': 'idle',
    'aid-cnt-type': 'info'
  },
  H1: { text: 'Welcome to Symbols' },
  P: { text: 'Build UIs with declarative objects.' },
  Button: { text: 'Get Started', theme: 'primary' }
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
  attr: {
    'data-mcp-tool': 'checkOrderStatus',
    'data-mcp-description': 'Check the status of an order by ID'
  },
  Input: { type: 'text', name: 'orderId', placeholder: 'Order ID' },
  Button: { type: 'submit', text: 'Check' }
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
