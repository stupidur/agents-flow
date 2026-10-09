---
name: project-discovery
description: Inspect a newly registered or substantially changed repository and produce the evidence-based project map used to author AGENTS.md. Use during one-time project onboarding or after major architecture changes; do not use for routine feature work.
---

# Project Discovery

Inspect the repository without modifying its source files. The only permitted
write during a discovery step is the Workflow-declared project-map artifact.

## Procedure

These are local repository operations. Use the client's native project file
reading tools for the declared `project_read` capability; this Skill does not
require a `project-files` MCP profile. Do not confuse this local route with a
remote repository or service read, which must follow the active Workflow's
declared Skill or MCP route.

1. Identify the project type from repository evidence, not its directory name.
2. Map source, tests, configuration, generated output, documentation, and deployment directories.
3. Extract verified build, development, test, lint, formatting, and deployment commands from project files.
4. Record stable architecture and conventions: entry points, modules, reusable components, style/token systems, data flow, localization, and integrations.
5. Identify repository-specific rules, protected files, secrets boundaries, remote-write boundaries, and missing documentation.
6. Separate verified facts from open questions. Never invent commands or conventions.
7. Inspect `.agents/memory/README.md` when present and identify the memory files
   applicable to the detected project type. Do not treat memory as authoritative
   over repository evidence.

## AGENTS.md Discovery Prompt

For onboarding, use this prompt as the inspection checklist and answer it with
evidence from the actual repository:

> 我正在开发/维护一个项目，希望你结合项目实际代码和目录结构，梳理一份详细、系统、可长期维护的 AGENTS.md。请说明全局样式与变量、可复用 class、栅格与响应式布局、组件/模块规范、JavaScript 作用域与事件管理、模板和数据变量复用、多语言与静态资源、第三方依赖、构建测试命令、兼容性、升级维护和团队协作边界。每条结论都引用实际文件路径；无法确认的内容标记为未知，不要猜测。

For a Shopify theme, expand the same inspection to the real `layout/`,
`templates/`, `sections/`, `snippets/`, `assets/`, `config/`, and `locales/`
directories, then also document theme editor compatibility, Liquid settings and
blocks, section isolation, asset loading, responsive breakpoints, and the
project's installed `.agents/rules/` routes.

## Output

Produce a project map containing:

- project type and primary technologies;
- important directories and entry points;
- verified commands;
- coding and testing conventions;
- external systems and required credentials by key name only;
- risks, unknowns, and evidence paths.
- applicable `.agents/memory/` files for the detected project type.

For Shopify projects, also include:

- actual theme directories and representative files;
- global tokens, reusable classes, layout and breakpoint conventions;
- Liquid, section, snippet, JavaScript, localization, and dependency patterns;
- the rule files that must be read for new, reused, or modified sections;
- local development and preview constraints.
- the applicable shared memory file, if one is materialized.

Write the complete project map to the Workflow-declared JSON artifact before
reporting completion. Do not write `AGENTS.md`; hand the project map artifact to
`agents-context-authoring`.
