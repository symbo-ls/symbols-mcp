# Optimize Your Symbols Site for AI Agents

## A Practical Guide to Accessibility, ARIA, and Emerging Standards

### AI Skill Instruction for Coding Assistants

This document is the definitive guide for generating Symbols (DOMQL v3) code fully interpretable by AI agents, accessibility tools, and automated systems. All output must comply with the following rules and standards.

---

# 1. Semantic-First Architecture

Always generate semantic components instead of generic containers. Use these mappings:

| Intent                               | Required Component    |
| ------------------------------------ | --------------------- |
| Page header                          | Header                |
| Navigation                           | Nav                   |
| Primary content                      | Main                  |
| Standalone entity (product, article) | Article               |
| Thematic grouping                    | Section               |
| Sidebar                              | Aside                 |
| Footer                               | Footer                |
| H1–H6                                | Headings              |
| P                                    | Paragraphs            |
| Button                               | Actions               |
| Link                                 | Navigation            |
| Form                                 | Transactional surface |
| Input / Select                       | User input            |

Do not simulate meaning with generic divs or spans.

---

# 2. DOMQL v3 Compliance

- Use DOMQL v3 syntax exclusively.
- Set HTML attributes via `attr`.
- Prefix event handlers with `on`.
- Ensure all critical content is server-rendered and visible in the initial HTML.

---

# 3. Heading Discipline

- One H1 per page defining primary subject.
- Logical hierarchy: H1 → H2 → H3, etc.
- Nested headings should not skip levels.

Heading hierarchy is used by AI agents to determine page structure.

---

# 4. Interactive Elements

- Use native elements: Button, Link, Form, Input, Select.
- If non-native interactive elements are unavoidable, declare:

```javascript
attr: {
  role: 'button',
  tabindex: '0'
}
```

- Do not rely on visual styling to indicate interactivity.

---

# 5. Accessibility as Machine Interface

ARIA attributes define machine-readable state:

- `aria-busy`: reflects loading.
- `aria-label`: accessible name when visible text is insufficient.
- `aria-live`: indicates dynamic content.
- `autocomplete`: guides expected input format.

ARIA values must match actual runtime state.

---

# 6. AI-Specific Markup (aid-\*)

Include aid-\* attributes to optimize machine parsing:

- `aid-type`: structural role (header, nav, main, content, complementary, interactive, modal, alert, search)
- `aid-desc`: concise machine-readable description
- `aid-state`: idle, loading, processing, done, error
- `aid-cnt-type`: product, service, info

State must accurately reflect dynamic changes.

---

# 7. Structured Data (JSON-LD)

Include JSON-LD for entity representation:

- Organization
- Product / Service
- Article
- FAQPage
- BreadcrumbList

Structured data must match server-rendered content exactly.

```javascript
export const StructuredData = {
  tag: "script",
  attr: { type: "application/ld+json" },
  html: (el, s) =>
    JSON.stringify({
      "@context": "https://schema.org",
      "@type": "Product",
      name: s.name,
      description: s.description,
      offers: {
        "@type": "Offer",
        price: s.price,
        priceCurrency: s.currency,
      },
    }),
};
```

---

# 8. Form Construction Protocol

- Associate labels using `for` + `id` or nest input inside label.
- Define `name` and `type` attributes.
- Use `autocomplete` when relevant.
- Reflect submission state via `aria-busy` or `aid-state`.

Forms must be machine-submittable without heuristic inference.

---

# 9. Explicit Identifiers

Use deterministic IDs and class names for reliable referencing:

```javascript
attr: {
  id: `entity-${s.id}`,
  class: 'entity-card'
}
```

---

# 10. llms.txt Support

Provide `/llms.txt` for AI guidance:

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

## Data accuracy
- Prices, shipping, inventory levels
```

AI agents must use llms.txt for programmatic routing and content interpretation.

---

# 11. Testing Instructions

### Manual Testing

- Ask AI agents to describe page content, locate products, report prices, and identify support channels.

### Automated Testing

```javascript
export const testAgentComprehension = async function (url, prompt) {
  const response = await fetch("https://api.agent-simulator.com/ask", {
    method: "POST",
    body: JSON.stringify({ url, prompt }),
  });
  return response.json();
};
```

---

# 12. Chrome WebMCP / Tool Exposure

Use descriptive attributes for AI-accessible tools:

```javascript
export const CheckOrderTool = {
  extends: "Form",
  attr: {
    "data-mcp-tool": "checkOrderStatus",
    "data-mcp-description": "Check the status of an order by ID",
  },
  Input: { attr: { type: "text", name: "orderId", placeholder: "Order ID" } },
  Button: { type: "submit", text: "Check" },
};
```

---

# 13. Infrastructure Awareness

- Expect bursty agent traffic.
- Horizontal scaling preferred.
- Sub-200ms response targets.
- Intelligent rate limiting for abusive requests.

---

# 14. Failure Pattern Recognition

- Excessive divs without semantics
- Non-descriptive links
- Missing headings
- Critical content rendered client-side only
- Conflicting metadata

---

# 15. Output Verification Checklist

Ensure all generated code meets these requirements:

- Semantic components only
- One H1 per page
- Buttons for actions, Links for navigation
- Labeled and named forms
- Dynamic regions declare state
- JSON-LD matches content
- Server-rendered critical content

Any violation requires regeneration.

---

# Operational Principle

Generate Symbols code assuming AI agents parse and act on it before human consumption. Structure, semantics, and state define AI comprehension, safety, and interoperability. Accessibility and aid-\* attributes are part of the machine contract.
