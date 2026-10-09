---
id: shopify/theme-implementation
capabilities:
  required:
  - code_read
  - code_write
  optional:
  - browser_preview
  - test_run
name: theme-implementation
description: Implement Shopify theme changes with scoped assets, accessible
  Liquid, responsive behavior, and mandatory section/rule routing.
---

# Shopify Theme Implementation

Preserve merchant settings and theme-editor compatibility. Prefer progressive
enhancement, accessible markup, scoped assets, and viewport validation.

## Required Rule Routing

Before editing a file, classify the change and read every applicable rule file
from the materialized project layer:

- new section: `.agents/rules/shopify/new-section-rules.md`
- copied or adapted section: `.agents/rules/shopify/reuse-section-rules.md`
- existing section change: `.agents/rules/shopify/modify-section-rules.md`
- styles, tokens, variables, or breakpoints: `.agents/rules/shopify/theme-style-variable-rules.md`
- images, WebP, Content Files, or CSS placement: `.agents/rules/shopify/media-asset-rules.md`
- SEO, metadata, headings, links, or structured data: `.agents/rules/shopify/seo-rules.md`
- browser or responsive validation: `.agents/rules/common/browser-testing-rules.md`
- commit, push, or any remote-affecting action: `.agents/rules/common/git-push-restriction-rules.md`

The selected rule files are also listed in the generated workflow handoff. Do
not treat this list as optional: read the full applicable files before writing.

## Implementation Boundaries

- Use `npm run start` for local development unless the user explicitly asks for another command.
- Do not add behavior, animation, or interaction that the request does not specify.
- Keep CSS scoped to the section or component; prefer a new asset file for new behavior.
- Preserve existing CSS by appending scoped overrides instead of rewriting original rules.
- Keep new JavaScript isolated from the global scope and associate it with the section lifecycle.
- Guard empty Liquid settings and blocks before rendering dynamic content.
- Use semantic HTML and the required accessibility attributes.
- Never push, publish, upload, or change a remote Shopify store without explicit user approval.

## Completion Checklist

- the relevant section rule was read and followed;
- settings and dynamic content handle blank or missing values;
- CSS and JavaScript are scoped and do not add unauthorized behavior;
- responsive behavior is checked at the theme's existing breakpoints;
- the relevant tests or browser validation were run;
- changed files and any preview/editor URL are reported.
