# Symbols Snippets — Production Component Patterns

11 production-tested component patterns. Use as starting points for common UI needs.

---

## 1. Navigation Header

Sticky responsive header with logo, nav links, and mobile menu button.

```js
export const Header = {
  tag: 'header',
  position: 'sticky',
  top: '0',
  width: '100%',
  zIndex: '100',
  padding: 'Z2 B',
  align: 'center space-between',
  theme: 'header',

  Logo: {
    extends: 'Link',
    href: '/',
    text: 'Brand',
    fontWeight: '700',
    fontSize: 'B',
    textDecoration: 'none',
    onClick: (e, el) => {
      e.preventDefault()
      el.router('/', el.getRoot())
    }
  },

  Nav: {
    gap: 'B',
    align: 'center',

    children: ['Home', 'About', 'Contact'],
    childrenAs: 'state',
    childExtends: 'Link',
    childProps: {
      text: '{{ value }}',
      href: (el, s) => '/' + s.value.toLowerCase(),
      textDecoration: 'none',
      ':hover': { opacity: '.7' },
      onClick: (e, el, s) => {
        e.preventDefault()
        el.router('/' + s.value.toLowerCase(), el.getRoot())
      }
    },

    '@tabletS': { display: 'none' }
  },

  MenuButton: {
    extends: 'IconButton',
    icon: 'menu',
    display: 'none',
    '@tabletS': { display: 'flex' }
  }
}
```

---

## 2. Hero Section

Full-width hero with heading, description, and CTA buttons.

```js
export const Hero = {
  flow: 'y',
  align: 'center center',
  padding: 'F A',
  gap: 'B',
  textAlign: 'center',

  Tag: {
    tag: 'span',
    text: 'NEW',
    padding: 'X A',
    round: 'Z2',
    theme: 'primary',
    fontSize: 'Y',
    fontWeight: '600',
    letterSpacing: '1px'
  },

  H: {
    tag: 'h1',
    text: 'Build faster with Symbols',
    maxWidth: 'H',
    fontSize: 'E',
    fontWeight: '800',
    lineHeight: '1.1',
    '@tabletS': { fontSize: 'D' },
    '@mobileL': { fontSize: 'C2' }
  },

  P: {
    text: 'Design system framework for building modern interfaces',
    maxWidth: 'G',
    fontSize: 'A2',
    opacity: '.7',
    lineHeight: '1.6'
  },

  Actions: {
    gap: 'A',
    align: 'center',
    Button_Primary: {
      text: 'Get Started',
      theme: 'primary',
      padding: 'Z2 B'
    },
    Button_Secondary: {
      text: 'Learn More',
      theme: 'secondary',
      padding: 'Z2 B'
    }
  }
}
```

---

## 3. Feature Card

Card with icon, title, and description.

```js
export const FeatureCard = {
  flow: 'y',
  gap: 'A',
  padding: 'B',
  round: 'A',
  theme: 'card',

  Icon: {
    name: 'star',
    boxSize: 'B',
    color: 'primary'
  },

  H: {
    tag: 'h3',
    text: 'Feature Title',
    fontSize: 'A2',
    fontWeight: '600'
  },

  P: {
    text: 'Description of the feature goes here.',
    opacity: '.7',
    lineHeight: '1.5'
  }
}
```

---

## 4. Feature Grid

Responsive grid of feature cards using `children` + `childExtends`.

```js
export const FeatureGrid = {
  extends: 'Grid',
  columns: 'repeat(3, 1fr)',
  gap: 'B',
  padding: 'D A',

  '@tabletS': { columns: 'repeat(2, 1fr)' },
  '@mobileL': { columns: '1fr' },

  children: [
    { icon: 'zap', title: 'Fast', description: 'Lightning fast rendering' },
    {
      icon: 'shield',
      title: 'Secure',
      description: 'Built-in security features'
    },
    { icon: 'code', title: 'Clean', description: 'No-import architecture' }
  ],
  childrenAs: 'state',
  childExtends: 'FeatureCard',
  childProps: {
    Icon: { name: '{{ icon }}' },
    H: { text: '{{ title }}' },
    P: { text: '{{ description }}' }
  }
}
```

---

## 5. Pricing Card

Pricing option with features list and CTA.

```js
export const PriceCard = {
  flow: 'y',
  padding: 'C',
  round: 'A',
  theme: 'card',
  gap: 'B',
  minWidth: 'F',

  Header: {
    flow: 'y',
    gap: 'X2',
    H: {
      tag: 'h3',
      text: 'Pro Plan',
      fontSize: 'A2'
    },
    Price: {
      align: 'end',
      gap: 'X',
      H2: {
        tag: 'span',
        text: '$29',
        fontSize: 'D',
        fontWeight: '800'
      },
      P: {
        text: '/month',
        opacity: '.5',
        marginBottom: 'X2'
      }
    }
  },

  Features: {
    flow: 'y',
    gap: 'Z2',
    children: [
      'Unlimited projects',
      'Priority support',
      'Custom themes',
      'Team collaboration'
    ],
    childrenAs: 'state',
    childExtends: 'Flex',
    childProps: {
      align: 'center',
      gap: 'Z',
      Icon: { name: 'check', color: 'green', boxSize: 'Z2' },
      Text: { text: '{{ value }}' }
    }
  },

  Button: {
    text: 'Get Started',
    theme: 'primary',
    width: '100%',
    padding: 'Z2'
  }
}
```

---

## 6. Testimonial Card

User testimonial with avatar and quote.

```js
export const TestimonialCard = {
  flow: 'y',
  gap: 'A2',
  padding: 'B',
  round: 'A',
  theme: 'card',

  Quote: {
    tag: 'blockquote',
    text: '"This framework changed how we build interfaces."',
    fontSize: 'A1',
    lineHeight: '1.6',
    fontStyle: 'italic',
    opacity: '.85'
  },

  Author: {
    align: 'center',
    gap: 'A',
    Avatar: {
      extends: 'Img',
      round: '100%',
      boxSize: 'B2 B2'
    },
    Info: {
      flow: 'y',
      gap: '0',
      Name: { text: 'Jane Doe', fontWeight: '600', fontSize: 'Z2' },
      Role: { text: 'CTO at Acme', opacity: '.6', fontSize: 'Y' }
    }
  }
}
```

---

## 7. Search with Dropdown

Search input with filtered results dropdown.

```js
export const SearchDropdown = {
  state: {
    query: '',
    items: ['Dashboard', 'Settings', 'Profile', 'Analytics', 'Reports']
  },
  position: 'relative',

  Input: {
    placeholder: 'Search...',
    padding: 'Z2 A',
    width: '100%',
    onInput: (e, el, s) => s.update({ query: el.node.value })
  },

  Results: {
    if: (el, s) => s.query.length > 0,
    position: 'absolute',
    top: '100%',
    left: '0',
    width: '100%',
    theme: 'dropdown',
    round: '0 0 Z Z',
    maxHeight: 'E',
    overflow: 'auto',
    zIndex: '10',

    children: (el, s) =>
      s.items.filter((i) => i.toLowerCase().includes(s.query.toLowerCase())),
    childrenAs: 'state',
    childExtends: 'Box',
    childProps: {
      text: '{{ value }}',
      padding: 'Z A',
      cursor: 'pointer',
      ':hover': { background: 'hover' },
      onClick: (e, el, s) => {
        s.root.update({ query: s.value })
      }
    }
  }
}
```

---

## 8. Footer

Responsive footer with column layout.

```js
export const Footer = {
  tag: 'footer',
  flow: 'y',
  gap: 'C',
  padding: 'D B',
  theme: 'footer',

  Columns: {
    extends: 'Grid',
    columns: 'repeat(4, 1fr)',
    gap: 'C',
    '@tabletS': { columns: 'repeat(2, 1fr)' },
    '@mobileL': { columns: '1fr' },

    Column_Product: {
      flow: 'y',
      gap: 'Z2',
      H: { tag: 'h4', text: 'Product', fontSize: 'Z2', fontWeight: '600' },
      Link_1: { text: 'Features', href: '/features' },
      Link_2: { text: 'Pricing', href: '/pricing' },
      Link_3: { text: 'Docs', href: '/docs' }
    },

    Column_Company: {
      flow: 'y',
      gap: 'Z2',
      H: { tag: 'h4', text: 'Company', fontSize: 'Z2', fontWeight: '600' },
      Link_1: { text: 'About', href: '/about' },
      Link_2: { text: 'Blog', href: '/blog' },
      Link_3: { text: 'Careers', href: '/careers' }
    }
  },

  Bottom: {
    align: 'center space-between',
    borderTop: '1px solid',
    borderTopColor: 'gray3',
    paddingTop: 'A',
    P: {
      text: '© 2025 Brand. All rights reserved.',
      opacity: '.5',
      fontSize: 'Y'
    }
  }
}
```

---

## 9. Data Table

Structured data table from state array.

```js
export const DataTable = {
  state: {
    rows: [
      { name: 'Alice', role: 'Engineer', status: 'Active' },
      { name: 'Bob', role: 'Designer', status: 'Away' },
      { name: 'Carol', role: 'Manager', status: 'Active' }
    ]
  },

  tag: 'table',
  width: '100%',
  borderCollapse: 'collapse',

  Thead: {
    tag: 'thead',
    Tr: {
      tag: 'tr',
      Th_Name: { tag: 'th', text: 'Name', padding: 'Z A', textAlign: 'left' },
      Th_Role: { tag: 'th', text: 'Role', padding: 'Z A', textAlign: 'left' },
      Th_Status: {
        tag: 'th',
        text: 'Status',
        padding: 'Z A',
        textAlign: 'left'
      }
    }
  },

  Tbody: {
    tag: 'tbody',
    children: (el, s) => s.rows,
    childrenAs: 'state',
    childExtends: {
      tag: 'tr',
      borderBottom: '1px solid',
      borderBottomColor: 'gray2'
    },
    childProps: {
      Td_Name: { tag: 'td', text: '{{ name }}', padding: 'Z A' },
      Td_Role: { tag: 'td', text: '{{ role }}', padding: 'Z A' },
      Td_Status: { tag: 'td', text: '{{ status }}', padding: 'Z A' }
    }
  }
}
```

---

## 10. Layout with Sidebar

App layout with sidebar navigation and main content area.

```js
export const AppLayout = {
  flow: 'x',
  width: '100%',
  minHeight: '100vh',

  Sidebar: {
    flow: 'y',
    width: 'F',
    padding: 'A',
    gap: 'X2',
    theme: 'sidebar',
    '@tabletS': { display: 'none' },

    children: [
      { label: 'Dashboard', icon: 'home', path: '/' },
      { label: 'Projects', icon: 'folder', path: '/projects' },
      { label: 'Settings', icon: 'settings', path: '/settings' }
    ],
    childrenAs: 'state',
    childExtends: 'Flex',
    childProps: {
      align: 'center',
      gap: 'Z',
      padding: 'Z A',
      round: 'Z2',
      cursor: 'pointer',
      ':hover': { background: 'hover' },
      Icon: { name: '{{ icon }}', boxSize: 'Z2' },
      Text: { text: '{{ label }}' },
      onClick: (e, el, s) => el.router(s.path, el.getRoot())
    }
  },

  Main: {
    flow: 'y',
    flex: '1',
    padding: 'B',
    overflow: 'auto'
  }
}
```

---

## 11. Notification Toast

Auto-dismissing fixed-position notification.

```js
export const Toast = {
  align: 'center',
  gap: 'A',
  padding: 'A B',
  round: 'Z2',
  position: 'fixed',
  bottom: 'B',
  right: 'B',
  zIndex: '1000',
  theme: 'dialog',
  transition: 'opacity 0.3s, transform 0.3s',

  Icon: {
    name: 'check',
    boxSize: 'A'
  },

  Text: {
    text: 'Operation successful',
    fontSize: 'Z2'
  },

  CloseButton: {
    extends: 'IconButton',
    icon: 'x',
    boxSize: 'A',
    onClick: (e, el) => {
      el.parent.node.style.opacity = '0'
      setTimeout(() => el.parent.update({ if: false }), 300)
    }
  }
}
```

---

## 12. Contact Form

Multi-field form with submit handling.

```js
export const ContactForm = {
  tag: 'form',
  flow: 'y',
  gap: 'A',
  maxWidth: 'G',

  state: {
    name: '',
    email: '',
    message: '',
    submitted: false
  },

  Field_Name: {
    extends: 'Field',
    label: 'Name',
    Input: {
      placeholder: 'Your name',
      onInput: (e, el, s) => s.update({ name: el.node.value })
    }
  },

  Field_Email: {
    extends: 'Field',
    label: 'Email',
    Input: {
      type: 'email',
      placeholder: 'you@example.com',
      onInput: (e, el, s) => s.update({ email: el.node.value })
    }
  },

  Field_Message: {
    extends: 'Field',
    label: 'Message',
    Textarea: {
      placeholder: 'Your message...',
      rows: 4,
      onInput: (e, el, s) => s.update({ message: el.node.value })
    }
  },

  Button: {
    text: (el, s) => (s.submitted ? 'Sent!' : 'Send Message'),
    theme: 'primary',
    width: '100%',
    onClick: async (e, el, s) => {
      e.preventDefault()
      s.update({ submitted: true })
    }
  }
}
```
