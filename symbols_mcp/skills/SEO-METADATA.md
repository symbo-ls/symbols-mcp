# SEO Metadata

Symbols provides comprehensive SEO metadata support through the `@symbo.ls/helmet` plugin. Define a declarative `metadata` object on your app, pages, or any component. The same code works at runtime (updates DOM `<head>` tags) and during SSR (generates HTML via brender).

The system automatically:

- Generates correct `<title>`, `<meta>`, and `<link>` elements
- Expands array values into multiple tags
- Handles namespace prefixes (`og:`, `twitter:`, `article:`, `product:`, `DC:`, `itemprop:`, `http-equiv:`)
- Outputs valid HTML head markup
- Supports function values receiving `(element, state)` for dynamic metadata
- Merges metadata from global SEO settings, app-level, and page-level (page wins)

---

# Complete Unified Example

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

# Dynamic Metadata

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

# Merge Priority

When metadata is defined at multiple levels, higher priority wins:

1. `data.integrations.seo` — global SEO settings (lowest)
2. `data.app.metadata` — app-level defaults
3. `page.metadata` — page-level overrides (highest)

If no `title` is found after merging, it falls back to `page.state.title`, then `data.name`.
