---
description: "When modifying existing Shopify theme sections: impact assessment, safe Liquid patterns, validation, and rollback. Apply when editing or augmenting sections in sections/."
globs: ["sections/**/*.liquid"]
alwaysApply: false
---

# Existing Section Modification Rules for Codex/Agent

## MANDATORY RULES

### Impact Assessment Rules
- **MUST** ensure modifications don't break existing functionality
- **MUST** include proper validation for all inputs and conditions
- **MUST** verify all pages using the section before suggesting changes
- **NEVER** modify existing sections without impact assessment

### Code Safety Rules
- **MUST** add null/empty checks for all new inputs
- **MUST** preserve original functionality while adding new features
- **MUST** use conditional logic to prevent breaking existing implementations
- **MUST** add comprehensive error handling

### Documentation Rules
- **MUST** document all changes with standardized comments
- **MUST** explain potential impacts in modification suggestions
- **MUST** provide rollback strategy for each change

## DEVELOPMENT GUIDELINES

### Pre-Modification Assessment
1. **SEARCH** for all pages/templates using the section
2. **IDENTIFY** existing functionality that must be preserved
3. **PLAN** modification approach that minimizes risk
4. **SUGGEST** testing strategy for affected areas

### Safe Modification Patterns
```liquid
<!-- Safe conditional additions -->
{% if new_setting and new_setting != blank %}
  <!-- new functionality -->
{% endif %}

<!-- Preserve existing behavior -->
{% if existing_condition %}
  <!-- original code preserved -->
{% else %}
  <!-- new alternative behavior -->
{% endif %}
```

### Validation Requirements
- **INPUT validation**: Check for empty/null values
- **CONDITIONAL logic**: Ensure new features don't interfere
- **FALLBACK behavior**: Provide defaults for new settings
- **ERROR handling**: Graceful degradation for edge cases

### Agent Behavior
- **ALWAYS** assess modification risks before editing
- **DO NOT** ask for extra confirmation when the user has clearly requested the
  change; proceed after impact assessment
- **ASK** for clarification only when the target section, affected template, or
  expected behavior is ambiguous
- **PROVIDE** impact assessment for each modification
- **SUGGEST** testing checklist for affected pages
- **RECOMMEND** rollback strategy before implementation

### Best Practice Approach
1. **IDENTIFY** all pages using the section via section type search
2. **TEST** modifications on development environment first
3. **VERIFY** no regression on existing implementations
4. **DOCUMENT** all changes for future reference
