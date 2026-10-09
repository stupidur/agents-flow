---
description: "Shopify theme styling rule requiring reuse of existing global CSS variables, design tokens, adapters, utilities, and breakpoints before section-level hardcoding."
globs:
  - "layout/**/*.liquid"
  - "templates/**/*.{liquid,json}"
  - "sections/**/*.liquid"
  - "snippets/**/*.liquid"
  - "blocks/**/*.liquid"
  - "assets/**/*.{css,scss,liquid}"
  - "config/**/*.json"
alwaysApply: false
---

# Shopify Global Style Variable Rules

Apply this rule whenever Shopify theme work adds or changes CSS, inline custom
properties, section settings that control presentation, responsive behavior, or
Liquid markup coupled to theme styles.

## Mandatory Token-First Workflow

- **MUST** inspect the theme's existing global variables, adapters, color
  schemes, typography settings, spacing/layout tokens, radius tokens, button
  styles, utility classes, and breakpoints before writing new styles.
- **MUST** reuse an existing global CSS variable, design token, theme setting,
  helper class, or component style whenever it represents the required value.
- **MUST** prefer semantic variables such as theme color, typography, spacing,
  container, radius, and button tokens over hardcoded values in each section.
- **MUST** use the project's existing breakpoint variables or media-query
  conventions instead of inventing nearby section-specific breakpoints.
- **MUST NOT** hardcode a value in multiple sections when a global variable or
  shared token can express it once.
- **MUST NOT** hardcode font-family names, repeated brand colors, standard page
  widths, shared spacing scales, button styles, or common radii inside a section.
- **MUST NOT** duplicate an existing utility or global component style with a
  section-local copy.

## When No Suitable Global Variable Exists

- If the value is shared by multiple components or belongs to the design system,
  **MUST** add it to the project's established central token/adapter layer and
  document the consumers.
- If the value is truly unique to one component, **MAY** define a scoped custom
  property on that component's root. The name must be semantic and the property
  must not leak globally.
- **MUST** avoid creating a global token for a one-off decorative value merely
  to satisfy this rule.
- **MUST** preserve merchant-configurable theme settings and map them into
  existing variables or scoped custom properties rather than baking their
  current values into CSS.
- **MUST** explain any unavoidable hardcoded value when no suitable token,
  setting, or reusable abstraction exists.

## Shopify Implementation Pattern

Preferred:

```css
.product-card {
  color: rgb(var(--color-foreground));
  background: rgb(var(--color-background));
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}
```

Avoid:

```css
.product-card {
  color: #111111;
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
}
```

When Liquid settings must feed CSS, expose only the needed scoped custom
property and consume it in a project-controlled stylesheet. Do not place raw CSS
in Theme Editor Custom CSS or merchant-editable CSS fields; follow
`.agents/rules/shopify/media-asset-rules.md`.

## Required Verification

1. Search the repository for existing variables and equivalent styles before
   adding a new literal or custom property.
2. Confirm the chosen variable is defined in every color scheme, context, or
   fallback path where the component can render.
3. Confirm section styles remain scoped and do not override unrelated theme
   components.
4. Confirm responsive behavior uses the project's established breakpoints.
5. Review new CSS literals and document why any repeated or brand-level value
   was not represented by an existing or newly centralized token.
6. Run the viewport/browser matrix in
   `.agents/rules/common/browser-testing-rules.md` for visual changes.
