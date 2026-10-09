---
description: "Use when creating or scaffolding new Shopify theme sections (custom sections). Covers naming (cust-*, kebab-case), file structure (section + CSS + JS), schema with Custom Sections category, and InsCoder comment format."
globs:
  - "sections/**/*.liquid"
  - "assets/cust-*.css"
  - "assets/cust-*.js"
alwaysApply: false
---

# New Section Development Rules for Codex/Agent

## MANDATORY RULES

### Section Naming Rules
- **MUST** use functional naming with kebab-case: `sections/cust-section-name.liquid`
- **MUST** add version suffix if duplicates exist: `cust-section-name-v1.liquid`
- **MUST** create corresponding asset files: `assets/cust-section-name.css` & `assets/cust-section-name.js`

### Code Documentation Rules
- **MUST** add standardized comments to all modifications:
```liquid
/** InsCoder WANG.J YYYY-MM-DD B + [English function description] **/
[code content]
/** InsCoder WANG.J YYYY-MM-DD E + [English function description] **/
```

### File Structure Rules
- **MUST** create independent CSS and JS files for each section
- **MUST** follow standard section template structure
- **MUST** include proper schema with "Custom Sections" category

## DEVELOPMENT GUIDELINES

### Section Creation Process
1. **CONFIRM** functional section name with user
2. **SUGGEST** appropriate file structure
3. **PROVIDE** complete section template with schema
4. **INCLUDE** associated CSS/JS file templates

### Standard Section Template
```liquid
{{ 'cust-section-name.css' | asset_url | stylesheet_tag }}
<section class="section-name">
  <!-- section content -->
</section>
<script src="{{ 'cust-section-name.js' | asset_url }}" defer="defer"></script>
{% schema %}
{
  "name": "Cust Section name",
  "settings": [],
  "presets": [
    {
      "name": "Cust Section name",
      "category": "Custom Sections",
      "settings": {}
    }
  ]
}
{% endschema %}
```

### Agent Behavior
- **ASK** for section naming preferences before creating
- **SUGGEST** file organization structure
- **PROVIDE** both section file and asset file templates
- **EXPLAIN** schema configuration options
