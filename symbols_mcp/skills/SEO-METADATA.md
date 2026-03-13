# SEO Metadata

Define a declarative `metadata` object on any app, page, or component. Works at runtime (updates DOM `<head>`) and during SSR (generates HTML via brender). Provided by `@symbo.ls/helmet`.

## Supported Metadata Types

| Prefix / Type | Generates | Example Key |
|---|---|---|
| _(none)_ | `<title>`, `<meta name>`, `<link rel>` | `title`, `description`, `canonical` |
| `og:` | `<meta property="og:...">` | `og:title`, `og:image` |
| `twitter:` | `<meta name="twitter:...">` | `twitter:card`, `twitter:site` |
| `article:` | `<meta property="article:...">` | `article:published_time` |
| `product:` | `<meta property="product:...">` | `product:price:amount` |
| `DC:` | `<meta name="DC....">` | `DC:title`, `DC:creator` |
| `itemprop:` | `<meta itemprop="...">` | `itemprop:name` |
| `http-equiv:` | `<meta http-equiv="...">` | `http-equiv:cache-control` |
| `apple:` | `<meta name="apple:...">` | `apple:mobile-web-app-capable` |
| `msapplication:` | `<meta name="msapplication:...">` | `msapplication:TileColor` |
| `alternate` | `<link rel="alternate" ...>` | `alternate: [{ hreflang, href }]` |
| `customMeta` | `<meta ...attrs>` | `customMeta: { name, content }` |

**Behaviors:**
- Array values expand into multiple tags
- Function values receive `(element, state)` for dynamic metadata
- Merges metadata from global, app-level, and page-level (page wins)

---

## Complete Example

```js
export default {
  metadata: {
    // Basic metadata
    title: "My Awesome Website",
    description: "This is an awesome website with great content",
    keywords: "awesome, website, content",
    author: "John Doe",
    robots: "index, follow",
    canonical: "https://example.com/page",

    // Open Graph
    "og:title": "My Awesome Website",
    "og:description": "This is an awesome website with great content",
    "og:type": "website",
    "og:url": "https://example.com",
    "og:image": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg",
    ],
    "og:site_name": "Example Site",
    "og:locale": "en_US",

    // Twitter Cards
    "twitter:card": "summary_large_image",
    "twitter:site": "@example",
    "twitter:creator": "@johndoe",
    "twitter:title": "My Awesome Website",
    "twitter:description": "This is an awesome website with great content",
    "twitter:image": "https://example.com/twitter-image.jpg",

    // Article metadata
    "article:published_time": "2023-01-01T00:00:00Z",
    "article:modified_time": "2023-01-02T00:00:00Z",
    "article:author": ["John Doe", "Jane Smith"],
    "article:section": "Technology",
    "article:tag": ["web", "development", "javascript"],

    // Product metadata
    "product:price:amount": "29.99",
    "product:price:currency": "USD",
    "product:availability": "in stock",
    "product:condition": "new",
    "product:brand": "Example Brand",
    "product:category": "Electronics",

    // Dublin Core
    "DC:title": "My Awesome Website",
    "DC:creator": ["John Doe", "Jane Smith"],
    "DC:subject": ["web development", "javascript"],
    "DC:description": "This is an awesome website with great content",
    "DC:publisher": "Example Publisher",
    "DC:date": "2023-01-01",
    "DC:type": "Text",
    "DC:language": "en",

    // Mobile app metadata
    "apple:mobile-web-app-capable": "yes",
    "apple:mobile-web-app-status-bar-style": "black-translucent",
    "apple:mobile-web-app-title": "My App",
    "msapplication:TileColor": "#ffffff",
    "msapplication:TileImage": "/mstile-144x144.png",
    "msapplication:task": [
      "name=Task 1;action-uri=/task1;icon-uri=/task1.ico",
      "name=Task 2;action-uri=/task2;icon-uri=/task2.ico",
    ],

    // HTTP-Equiv directives
    "http-equiv:cache-control": "no-cache",
    "http-equiv:expires": "Tue, 01 Jan 1980 1:00:00 GMT",

    // Structured data & verification
    "itemprop:name": "My Awesome Website",
    "itemprop:description": "This is an awesome website with great content",
    "google-site-verification": "abc123def456",
    "fb:app_id": "123456789",
    "geo.region": "US-NY",
    "geo.placename": "New York City",
    "geo.position": "40.7128;-74.0060",

    // Alternate language links
    alternate: [
      { hreflang: "es", href: "https://example.com/es/" },
      { hreflang: "fr", href: "https://example.com/fr/" },
    ],

    // Custom metadata
    customMeta: {
      name: "custom-property",
      content: "custom-value",
      "data-custom": "additional-data",
    },
  },
};
```

---

## Dynamic Metadata

Metadata values can be functions receiving `(element, state)`. Both the whole object and individual properties support this:

```js
// Whole metadata as function
export const productPage = {
  metadata: (el, s) => ({
    title: s.product.name + ' — My Store',
    description: s.product.description,
    'og:image': s.product.image
  })
}

// Individual properties as functions
export const profilePage = {
  metadata: {
    title: (el, s) => `${s.user.name} — My App`,
    description: (el, s) => s.user.bio,
    'og:image': '/default-avatar.png'  // static fallback
  }
}
```

---

## Merge Priority

Higher priority wins. Later levels override earlier ones.

| Priority | Source | Scope |
|---|---|---|
| 1 (lowest) | `data.integrations.seo` | Global SEO settings |
| 2 | `data.app.metadata` | App-level defaults |
| 3 (highest) | `page.metadata` | Page-level overrides |

**Fallback chain for `title`:** `page.metadata.title` -> `page.state.title` -> `data.name`
