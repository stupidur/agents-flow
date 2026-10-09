---
description: "When copying or reusing an existing Shopify section (instead of modifying in place): versioned section names (cust-*-v1.liquid), new wrapper classes, JSON template section type updates, and asset isolation. Apply when creating a new section by copying an existing one in sections/ or when editing templates that reference sections."
globs: ["sections/**/*.liquid", "templates/**/*.json"]
alwaysApply: false
---

# Section Reuse Development Rules for Augment AI

## MANDATORY RULES

### Section Copying Rules
- **MUST** copy existing section and rename with version suffix: `cust-original-name.liquid`
- **MUST** add version suffix if duplicates exist: `cust-original-name-v1.liquid`
- **MUST** update corresponding JSON file section type reference
- **MUST** add new wrapper class to outermost element to avoid conflicts

### Code Isolation Rules
- **MUST** ensure modifications don't affect original section functionality
- **MUST** add new wrapper classes instead of modifying existing ones
- **MUST** add documentation comments for all changes

### Asset Management Rules
- **PREFER** independent CSS/JS files for substantial additions
- **ALLOW** inline styles/scripts for minimal changes
- **MUST** clearly separate new styles from existing ones

## DEVELOPMENT GUIDELINES

### Section Modification Process
1. **COPY** original section file with versioned name
2. **ADD** new wrapper class to prevent style conflicts
3. **UPDATE** JSON template to reference new section type
4. **ISOLATE** new functionality from existing code

### Code Structure Guidelines
```liquid
<!-- Original section structure -->
<section class="original-class new-wrapper-class">
  <!-- modified content -->
</section>

<!-- CSS approach -->
.new-wrapper-class {
  /* new styles that don't conflict with original */
}
```

### Asset File Strategy
- **Small changes**: Use inline `{% style %}` or `{% javascript %}` tags
- **Large changes**: Create independent asset files following naming convention

### AI Assistant Behavior
- **WARN** about potential impacts on pages using original section
- **SUGGEST** versioning strategy for section files
- **RECOMMEND** wrapper class approach for style isolation
- **VERIFY** JSON template updates are included
