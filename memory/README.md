# Shared Project Memory

This directory contains reusable, non-secret project knowledge for initialized
repositories. Bootstrap copies it to `.agents/memory/` in the target project.

Memory files are context, not authority. The active `workflow.md`, `plan.json`,
`AGENTS.md`, and `.agents/rules/` always take precedence. Read only the memory
file relevant to the current task; do not preload the entire directory.

Keep task-specific temporary findings in `.agentflow/runs/`, not here. Do not
store credentials, tokens, customer data, or private URLs in shared memory.

## Files

- `global.md`: cross-project conventions and reusable lessons.
- `shopify.md`: Shopify theme and live-theme workflow knowledge.
- `java.md`: Java project workflow knowledge.
- `workflows.md`: reusable workflow execution notes.
- `integrations.md`: external integration notes and unresolved questions.
