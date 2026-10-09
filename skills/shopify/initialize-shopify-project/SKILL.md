---
name: initialize-shopify-project
description: Initialize or standardize a local Shopify theme repository with project-level AGENTS.md guidance, Shopify and browser rules, Codex/Claude/OpenCode/OMP MCP configuration, safe .env and .gitignore merging, and project skills. Use when cloning, creating, onboarding, refreshing, or auditing a Shopify project so its root has the workspace's baseline agent capabilities.
---

# Initialize Shopify Project

Create a complete, project-local Shopify agent baseline. Preserve user files, credentials, Git state, and remote resources.

When the handoff declares `global_context`, read its global `AGENTS.md` and
applicable rules first. Pass `--global-root <global_context.root>` to both
initializer commands below. This mode reuses the global rules and client
adapter files instead of copying them into the project; `.env` placeholders
and `.gitignore` still merge locally. Add a `全局规则` section to the generated
project `AGENTS.md` with actual global instruction and rule paths. Preserve
applicable global constraints, report conflicts, and keep the global layer
read-only during project onboarding.

## Workflow

1. Resolve the target repository. Never assume the workspace root is the Shopify project when it contains multiple repositories.
2. Inspect `git status --short --branch`, the remote/default branch, and the actual Shopify structure (`layout/`, `templates/`, `sections/`, `snippets/`, `assets/`, `config/`, `locales/`, build files).
3. Run the bundled initializer in preview mode:

   ```bash
   python3 <skill-dir>/scripts/init_shopify_project.py --target <project> --dry-run
   ```

4. Review conflicts. Preserve existing files by default. Use `--force` only when the user explicitly authorizes replacing the listed local files.
5. Apply the local baseline:

   ```bash
   python3 <skill-dir>/scripts/init_shopify_project.py --target <project>
   ```

6. Read `assets/templates/guides/init-shopify-project.md` completely. Generate or merge `<project>/AGENTS.md` from repository evidence. Preserve useful existing content, add project-specific exceptions and a dated revision note, and include every copied rule under “规则文件匹配”. Do not copy generic claims into the project summary. When the active workflow grants `document_write`, create or update `AGENTS.md` without asking for a second confirmation.
7. Install project-local skills when initialization includes dependency setup:

   Skip duplicate skill installation when the required Skills already exist in
   the global layer selected by the handoff; verify their declared paths instead.

   ```bash
   npx skills add Shopify/shopify-ai-toolkit
   npx skills add https://github.com/stupidur/vibe-coding/tree/main/skills/shopify
   npx skills add github:CitroLabs/ego-lite/skills/ego-browser -a '*' -y
   ```

   Treat network tools as read-only by default. Do not publish, push, upload, or change a remote store. If a command would modify a third-party resource rather than only the local project, request explicit approval for the exact target.
8. Verify the result with the checklist below. Report skipped installs or unresolved conflicts; never claim a capability is present without checking it.

## Template Mapping

The complete source template set is bundled under `assets/templates/`. The initializer maps it as follows:

- `rules/**` → `.agents/rules/**`
- `codex/config.toml` → `.codex/config.toml`
- `claude/mcp.json` → `.claude/mcp.json`
- `opencode/opencode.json` → `.opencode/opencode.json`
- `omp/config.yml` and `omp/mcp.json` → `.omp/`
- `env/.env` → merge missing keys into `.env`
- `gitignore/shopify-project.gitignore` → append missing rules to `.gitignore`
- `guides/**` remain skill references by default; pass `--copy-guides` only when the user explicitly wants workspace guides stored in the project
- The shared `memory/**` layer is materialized by `agentflow bootstrap` into
  `.agents/memory/**`; do not copy secrets or task-specific findings into it.

Do not copy `.DS_Store`. Never copy or print secret values. MCP templates inherit `FIGMA_API_KEY` from the environment; the bundled `.env` contains only an empty placeholder.

The Shopify initialization baseline ignores local AgentFlow/client artifacts and
the project's local task directories: `.agentflow/`, `.omp/`, `.mcp.json`,
`opencode.json`, `.env.example`, `docs/`, and `tests/`. This is an explicit
project convention for local task output; if a project needs versioned docs or
tests, narrow or remove those entries before committing source files.

## AGENTS.md Requirements

Use the bundled initialization guide as the detailed source of truth. At minimum, make the project `AGENTS.md` include:

- evidence-based structure, build commands, theme conventions, reusable styles/tokens/classes, Liquid and JavaScript patterns, localization, media, dependencies, and testing notes;
- all common and Shopify rule routes installed by the initializer;
- local browser routing: in ChatGPT/Codex, the installed Computer Use plugin
  Skill/MCP tools are mandatory first; after recorded unavailability,
  unsupported operations, or an actual call failure, use Ego Browser, then
  Playwright CLI if Ego Browser is also unavailable, unsupported, or failing;
  resolve their Skill paths from the selected local or global layer;
- remote-write boundaries for Git, Shopify, Basecamp, documents, and other services;
- project-specific exceptions and a revision log when merging an existing file.

## Verification

Run:

```bash
python3 <skill-dir>/scripts/init_shopify_project.py --target <project> --dry-run --json
```

Confirm:

- the dry run reports only `unchanged` items and any intentional conflicts;
- `AGENTS.md` exists and describes the actual repository;
- all eight bundled rule files exist in the selected local or global rule layer;
- the selected client adapter files exist; global files under `clients/` still
  require integration with the executor and do not prove client activation;
- `.env` contains the `FIGMA_API_KEY` key without revealing its value;
- `.gitignore` contains the baseline without losing existing rules;
- installed Shopify and browser skills exist at the handoff's selected paths;
- `git diff --check` passes and `git status --short` contains only expected local changes.

Never run `git push`, publish a Shopify theme, or upload Content Files as part of initialization.
