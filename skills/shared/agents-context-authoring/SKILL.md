---
name: agents-context-authoring
description: Create or refresh a repository-root AGENTS.md from verified project-discovery evidence. Use during project onboarding or after major architecture changes when stable agent guidance is missing or stale; do not place task-specific plans, secrets, or temporary findings in AGENTS.md.
---

# AGENTS Context Authoring

Create or update the repository-root `AGENTS.md` only from verified repository evidence.

## Requirements

These are local repository operations. Use the client's native project file
reading and editing tools for the declared `project_read` and
`document_write` capabilities; this Skill does not require a
`project-files-workspace-write` MCP profile. Do not use this rule to substitute
for a declared remote read or remote write route.

- Preserve useful existing guidance and resolve conflicts explicitly.
- Keep the file concise and stable across tasks.
- Include project structure, verified commands, conventions, testing expectations, and safety boundaries.
- Reference scoped rule files instead of duplicating their full contents.
- When the plan declares `global_context`, first read its global `AGENTS.md`
  and applicable global rules. Add a `全局规则` section to the project
  `AGENTS.md` that references the actual global paths and retains their
  constraints. Do not silently weaken global rules with project guidance;
  follow explicit user instructions and report conflicts. Global rules supply
  conventions, not evidence of the project's architecture or requirements.
- Use the plan's explicit global Skill, Rule, memory, and MCP paths when the
  project-local layer is absent. Read the global layer without modifying it;
  write the generated project `AGENTS.md` inside the target repository.
- Record unknowns as unknowns; never guess commands, credentials, branches, stores, or deployment targets.
- Never include secret values, task-specific requirements, temporary URLs, review findings, or generated-file inventories.
- Add a short dated revision note when materially updating an existing file.
- In a Shopify theme, include the sections `项目梳理`, `团队强制规范`, and
  `规则文件匹配`, and preserve the repository's actual paths and conventions.
- In `规则文件匹配`, point to the materialized `.agents/rules/` files and
  applicable global rule paths declared by the plan, and explain that the
  relevant rule must be read before the matching change.
- If the project contains `.agents/memory/`, document its index and explain that
  memory is contextual guidance only; the active Workflow, `AGENTS.md`, and Rules
  take precedence.
- Add a `公共记忆` section to `AGENTS.md` when `.agents/memory/README.md` exists.
  Always reference `global.md`, `workflows.md`, and `integrations.md`; additionally
  reference `shopify.md` for Shopify projects or `java.md` for Java projects.
- Ensure the detected project's `.agents/project.yaml` `context.include` lists
  the same type-specific memory files. If the context entry is missing, update it
  as part of initialization when the workflow grants `document_write`.
- When the active workflow grants `document_write`, write `AGENTS.md` directly
  without an additional confirmation prompt. Preserve useful existing content;
  do not delete unrelated project guidance.

## Output

Write or update `AGENTS.md`, then report:

- evidence used;
- sections created or changed;
- unresolved questions;
- validation performed.

Do not modify any other project file unless the active workflow explicitly
selects a separate initialization skill that requires it.
