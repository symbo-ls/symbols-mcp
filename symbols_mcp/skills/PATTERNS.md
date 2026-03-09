# Symbols / DOMQL — UI Patterns, Accessibility & AI Optimization

---

## Part 1: UI/UX Patterns

### Loading State

```js
export const DataList = {
  state: { items: [], loading: true, error: null },

  Loader: { if: ({ state }) => state.loading, extends: 'Spinner' },
  Error: {
    if: ({ state }) => Boolean(state.error),
    attr: { role: 'alert' },
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

```js
export const Accordion = {
  state: { open: false },
  Header: {
    extends: 'Flex',
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

```js
// components/ModalCard.js
export const ModalCard = {
  position: 'absolute', flexAlign: 'center center',
  top: 0, left: 0, boxSize: '100% 100%',
  transition: 'all C defaultBezier',
  opacity: '0', visibility: 'hidden', pointerEvents: 'none', zIndex: '-1',

  isActive: (el, s) => s.root.activeModal,
  '.isActive': { opacity: '1', zIndex: 999999, visibility: 'visible', pointerEvents: 'initial' },

  // Close on backdrop click, prevent close on content click
  onClick: (event, element) => { element.call('closeModal') },
  childProps: { onClick: (ev) => { ev.stopPropagation() } },

  // ARIA
  attr: { role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Dialog' },

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

### Tab Switching (DOM ID pattern)

Use DOM IDs for view switching — NOT reactive `display` bindings (causes rendering failures).

```js
// Page definition
HomeView: { id: 'view-home', extends: 'Flex', ... },
ExploreView: { id: 'view-explore', extends: 'Flex', display: 'none', ... },

// Navbar
Navbar: {
  childExtends: 'Button',
  childProps: { onClick: (e, el) => { el.call('switchView', el.key.toLowerCase()) } }
}

// functions/switchView.js
export const switchView = function switchView(view) {
  ['home', 'explore', 'profile'].forEach(v => {
    const el = document.getElementById('view-' + v)
    if (el) el.style.display = v === view ? 'flex' : 'none'
  })
}
```

### Dynamic Class Toggle

```js
export const Button = {
  '.active': { background: 'primary', color: 'white' },
  isActive: ({ props }) => props.active  // adds/removes .active class
}
```

### Dynamic Form / Async Submit

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
      el.call('router', '/dashboard', el.__ref.root)
    } catch (e) {
      state.update({ loading: false, error: e.message })
    }
  },

  Field: {
    Input: { type: 'email', name: 'email', attr: { required: 'true' } }
  },
  Error: {
    if: ({ state }) => Boolean(state.error),
    attr: { role: 'alert' },
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

## Part 2: Accessibility

### Semantic Atoms First

Always prefer built-in semantic atoms over generic containers:

```js
// ✅ CORRECT — semantic atoms
Button: { text: 'Submit' }                           // <button>
Link: { text: 'Dashboard', href: '/dashboard' }      // <a>
Input: { placeholder: 'Search...' }                  // <input>
Nav: { Link: { text: 'Home', href: '/' } }           // <nav>
Header: {}                                           // <header>
Footer: {}                                           // <footer>
Main: {}                                             // <main>

// ❌ WRONG — loses semantics
Box: { tag: 'div', text: 'Submit', onClick: fn }    // div is not a button
```

### ARIA Attributes

```js
// Landmark roles
Box: { attr: { role: 'alert' }, text: 'Error occurred' }
Box: { attr: { role: 'status', 'aria-live': 'polite' }, text: '3 results found' }

// Labels
Input: { attr: { 'aria-label': 'Search networks' } }
Button: { icon: 'x', attr: { 'aria-label': 'Close dialog' } }
Icon: { name: 'settings', attr: { 'aria-hidden': 'true' } }

// Dynamic state
Button: {
  attr: (el, s) => ({ 'aria-expanded': s.isOpen, 'aria-controls': 'dropdown-menu' }),
  onClick: (e, el, s) => s.update({ isOpen: !s.isOpen })
}
```

### Keyboard Navigation

```js
// Custom keyboard interaction (listbox pattern)
{
  extends: 'Flex',
  attr: { role: 'listbox', tabindex: '0', 'aria-label': 'Select option' },
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

Tabindex rules:
- `tabindex: '0'` — in tab order
- `tabindex: '-1'` — focusable programmatically only
- Never use `tabindex > 0`

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
Label: { text: 'Email', attr: { for: 'email-input' } }
Input: { id: 'email-input', type: 'email', attr: { required: 'true', 'aria-required': 'true' } }

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
P: { id: 'error-msg', attr: { role: 'alert' }, color: 'red', text: (el, s) => s.errorMessage }
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

- Do NOT rely on color alone for error/success states — always combine with icon + text
- Use `title`, `caption`, `paragraph` semantic tokens for sufficient contrast
- Low opacity colors (`gray 0.3`) likely fail WCAG AA — verify contrast ratio

---

## Part 3: AI Agent Optimization

### `aid-*` Attributes for Machine Parsing

Include `aid-*` attributes so AI agents can parse structural intent:

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

| `aid-type` values | Meaning                                              |
| ----------------- | ---------------------------------------------------- |
| `header`          | Page header                                          |
| `nav`             | Navigation                                           |
| `main`            | Primary content                                      |
| `content`         | Content section                                      |
| `complementary`   | Supplementary (sidebar, aside)                       |
| `interactive`     | Form, control panel                                  |
| `modal`           | Dialog overlay                                       |
| `alert`           | Error or notification                                |
| `search`          | Search interface                                     |

| `aid-state` values | Meaning              |
| ------------------ | -------------------- |
| `idle`             | Default state        |
| `loading`          | Fetching data        |
| `processing`       | Submitting/computing |
| `done`             | Completed            |
| `error`            | Error state          |

### JSON-LD Structured Data

Include JSON-LD for entity representation by AI agents and search engines:

```js
export const StructuredData = {
  tag: 'script',
  attr: { type: 'application/ld+json' },
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

Schema types to use: `Organization`, `Product`, `Service`, `Article`, `FAQPage`, `BreadcrumbList`

Structured data must match server-rendered content exactly.

### Semantic Heading Structure

```
One H1 per page defining the primary subject.
Logical hierarchy: H1 → H2 → H3 — never skip levels.
Heading hierarchy is used by AI agents to determine page structure.
```

### AI-Accessible Tool Exposure (Chrome WebMCP)

```js
export const CheckOrderTool = {
  extends: 'Form',
  attr: {
    'data-mcp-tool': 'checkOrderStatus',
    'data-mcp-description': 'Check the status of an order by ID'
  },
  Input: { attr: { type: 'text', name: 'orderId', placeholder: 'Order ID' } },
  Button: { type: 'submit', text: 'Check' }
}
```

### llms.txt Support

Provide `/llms.txt` at your project root for AI routing guidance:

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

- All critical content (text, headings, prices, key data) must be server-rendered in the initial HTML
- Do not rely on client-side-only rendering for content AI agents need to parse
- `aria-busy="true"` while loading; `aria-busy="false"` when complete

### Failure Pattern Recognition

Watch for these anti-patterns that break AI comprehension:
- Excessive divs/boxes without semantic meaning
- Non-descriptive link text ("click here", "read more")
- Missing or skipped heading levels
- Critical content rendered client-side only
- Conflicting metadata (page title vs. H1 vs. JSON-LD)
- Missing `alt` text on informative images

---

## Part 4: Design Principles

### Visual Hierarchy

- Lead with the most important content (F-pattern, Z-pattern)
- Use typographic scale (`H1`→`H6`, `P`, `Caption`) to create hierarchy
- Adequate whitespace — breathing room improves comprehension

### Component Button Hierarchy

| Level        | Component          | Use                     |
| ------------ | ------------------ | ----------------------- |
| Primary      | `theme: 'primary'` | Main CTA (one per view) |
| Secondary    | `theme: 'dialog'`  | Supporting actions      |
| Tertiary     | `theme: 'transparent'` | Least important      |
| Destructive  | `theme: 'warning'` | Irreversible actions    |

### Responsive Behavior

```js
// Mobile-first approach
Component: {
  padding: 'A',                              // mobile base
  '@tabletS': { padding: 'B' },             // tablet
  '@screenS': { padding: 'C' },             // desktop
}
```

### Transitions & Micro-interactions

```js
// Standard transition
Component: {
  transition: 'B defaultBezier',            // B ≈ 280ms
  transitionProperty: 'opacity, transform'
}

// Hover feedback
Button: {
  ':hover': { opacity: 0.9, transform: 'scale(1.015)' },
  ':active': { opacity: 1, transform: 'scale(0.995)' }
}
```

Easing: `defaultBezier` = `cubic-bezier(.29, .67, .51, .97)` (smooth ease-out)

Do NOT animate layout properties (`width`, `height`, `top`, `left`) — they force reflow. Animate `transform` and `opacity` instead.
