---
description: "Shopify theme SEO rules for document metadata, structured data, heading hierarchy, links, images, Core Web Vitals, and validation."
globs:
  - "layout/**/*.liquid"
  - "templates/**/*.{liquid,json}"
  - "sections/**/*.liquid"
  - "snippets/**/*.liquid"
  - "assets/**/*.{css,js}"
  - "config/**/*.json"
  - "locales/**/*.json"
alwaysApply: false
---

# Shopify SEO Rules for Codex/Agent

Source: [InsCoder training manual, Chapter 05 - Performance and SEO](https://inscoder.notion.site/05-SEO-36847c1ee932803eba1fdec0539e69c5)

Apply this rule whenever work can change document metadata, indexability,
structured data, heading hierarchy, breadcrumbs, links, image markup, or
SEO-related performance.

## Mandatory Rules

### Shopify SEO Baseline

- **MUST** preserve Shopify's generated `sitemap.xml`, `robots.txt`, canonical
  URLs, language/currency output, and `content_for_header` unless the task
  explicitly requires a supported customization.
- **MUST NOT** hardcode store domains, canonical URLs, robots directives, or
  duplicate platform-generated SEO tags.
- **MUST** inspect the rendered page and existing theme head snippets before
  adding metadata or structured data.

### Title And Meta Description

- **MUST** render a descriptive page title with store context, using the theme's
  existing equivalent of `{{ page_title }} - {{ shop.name }}`.
- **MUST NOT** append `shop.name` a second time when `page_title` already
  contains it.
- **MUST** render one meta description and provide the equivalent of
  `page_description | default: shop.description` when the theme does not already
  provide a safe fallback.
- **MUST** escape dynamic title and description values for HTML attributes or
  text context.
- **MUST NOT** introduce duplicate `<title>`, meta description, canonical, or
  robots tags.

### Structured Data

- **MUST** use `<script type="application/ld+json">` for JSON-LD.
- **MUST** prefer Shopify's `structured_data` filter for supported resources,
  for example `{{ product | structured_data }}`.
- **MUST** output `BreadcrumbList` structured data when visible breadcrumbs are
  added or changed.
- **MUST** keep structured data consistent with visible page content, current
  URLs, price, availability, and locale.
- **MUST NOT** emit duplicate or conflicting Product, BreadcrumbList,
  Organization, Article, or other schemas.

### Headings And Semantic Content

- **MUST** render exactly one meaningful `<h1>` on each page.
- **MUST** preserve a logical heading hierarchy after the `<h1>`.
- **MUST** use semantic HTML for controls and landmarks; do not use clickable
  `<div>` elements where a link or button is appropriate.
- **MUST** use descriptive anchor text that communicates destination or purpose.
  Generic text such as "Click here" is prohibited.

### Links

- **MUST** preserve internal links as crawlable `<a href="...">` elements.
- **MUST** add `rel="noopener"` to external links opened with
  `target="_blank"`.
- **MUST** add `nofollow` to external links when required by the task, store
  policy, or link relationship; do not use it on internal navigation.
- **MUST NOT** replace essential navigation with JavaScript-only click handlers.

### Images And LCP

- **MUST** provide an `alt` attribute for every image.
- **MUST** use concise, meaningful alt text for informative images.
- **MUST** use `alt=""` for decorative images, including decorative hero
  backgrounds, while retaining the attribute.
- **MUST** use `image_url` and `image_tag` with explicit dimensions, responsive
  `widths`, and appropriate `sizes` for Shopify-hosted content images.
- **MUST** reserve `loading: 'eager'` and `fetchpriority: 'high'` for the actual
  first-viewport LCP image. At most one first-viewport image may receive this
  treatment.
- **MUST** lazy-load non-critical images and use low/default fetch priority.
- **MUST NOT** preload an image unless it is the verified LCP candidate. Avoid
  duplicate preloads or preloads that compete with critical CSS, fonts, or the
  real LCP image.

## Performance Targets That Affect SEO

- LCP: **2.5 seconds or less**
- INP: **200 milliseconds or less**
- CLS: **0.1 or less**
- Lighthouse Performance: **80 or higher**
- Lighthouse Accessibility: **95 or higher**
- Lighthouse Best Practices: **95 or higher**
- Lighthouse SEO: **100**

Treat these as validation targets, not permission to remove required storefront
behavior. Measure on a development theme or development store and document the
test page, viewport, and any limitation.

## Implementation Guidance

- Cache repeated Liquid lookups in an `assign` before reuse.
- Paginate product and collection loops instead of rendering unbounded lists.
- Avoid expensive repeated work inside Liquid loops.
- Prefer `render` and existing theme snippets over duplicated markup.
- Prefer native HTML behavior and zero-dependency solutions before adding
  JavaScript libraries.
- Load feature JavaScript only where needed and use dynamic imports for large,
  optional dependencies.
- Preserve visible focus, keyboard access, reduced-motion behavior, sufficient
  contrast, and 44px touch targets because accessibility defects can also make
  indexed content difficult to use.

## Required Verification

For SEO-affecting changes, perform the narrowest relevant checks:

1. Search the theme for existing title, description, canonical, robots, and
   JSON-LD output before editing.
2. Inspect rendered HTML for exactly one title, one meta description, one
   canonical URL, one meaningful H1, valid alt attributes, and no conflicting
   structured data.
3. Run Shopify Theme Check and address newly introduced SEO, Liquid, image
   loading, remote asset, missing template, and translation-key errors.
4. Run Lighthouse against representative development-store pages when a
   preview is available; record SEO, performance, accessibility, LCP, INP, and
   CLS results.
5. Validate JSON-LD syntax and confirm schema values match visible content.
6. Check representative product, collection, page, article, search, and
   localized URLs when the change affects shared layout or SEO snippets.

If a preview, Theme Check, or Lighthouse cannot be run, report the skipped check
and remaining risk. Never upload or publish a Shopify theme solely to perform
verification without explicit user approval for that exact remote action.
