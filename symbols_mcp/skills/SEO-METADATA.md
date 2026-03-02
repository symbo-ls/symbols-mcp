# SEO Metadata

DOMQL provides comprehensive SEO metadata support through a declarative `metadata` object. All SEO, social, structured data, and platform-specific properties are configured in a single, unified, type-safe structure.

The system automatically:

- Generates correct `<title>`, `<meta>`, and `<link>` elements
- Expands array values into multiple tags
- Handles namespace prefixes (`og:`, `twitter:`, `article:`, `product:`, `DC:`, `itemprop:`, `http-equiv:`)
- Outputs valid HTML head markup

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
