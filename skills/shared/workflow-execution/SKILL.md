---
name: workflow-execution
description: Strictly execute a generated AgentFlow workflow handoff file in order. Use when a user provides workflow.md or an equivalent execution plan; do not skip steps, invent completion, or perform unapproved remote actions.
---

# Workflow Execution

Use this Skill when the user gives you a generated AgentFlow `workflow.md`.
The handoff file and its adjacent `plan.json` are the execution authority.

## Required Startup

1. Read the complete `workflow.md`.
2. Read the adjacent `plan.json` and confirm that its workflow, project root,
   inputs, outputs, chain, executor Skill, and selected steps match the handoff.
   The plan must declare handoff contract version `2`; otherwise stop and ask
   for a newly generated handoff.
3. Confirm the current working directory is the plan's `project_root`.
4. If `.agents/memory/README.md` exists, read it and load only memory files
   relevant to the current task. Memory is contextual guidance, not an authority
   over the handoff, `AGENTS.md`, or Rules.
5. Read every selected Skill, every listed Rule, and every MCP profile file before
   acting on the corresponding step.
6. If a required input, file, credential key, permission, Agent route, Skill,
   Rule, MCP profile, or validation environment is missing, follow the active
   handoff policy. For a source or route marked `skip_dependents`, record the
   exact reason, mark that step and its dependent branch skipped, and continue
   unrelated steps. Otherwise stop and report the exact missing prerequisite.
   Never guess and never silently skip a step.

## Strict Execution Contract

严格执行以下工作流，不得把它当作建议：

1. `workflow.md`、相邻的 `plan.json`、每一步指定的 Skill、Rules 和 MCP
   profile 是唯一执行依据。
2. workflow 中的 `Agent` 是强制执行路由：
   - 必须使用 multi-agent 工具派发给指定 Agent ID；优先查找
     `multi_agent_v1__spawn_agent`。
   - 不得由主 Agent 代替执行，不得将指定 Agent 替换成其他 Agent。
   - 即使多个步骤指定同一个 Agent，也必须按步骤分别派发、跟踪和验收。
   - 如果指定 Agent 路由不可用，先搜索延迟加载工具；确认仍不可用后立即停止，
     未经用户确认不得降级为主 Agent 执行。
3. 不允许静默跳过、重排、合并或降级任何已选择步骤。条件步骤既然出现在
   handoff 中，就视为已选择。只有在 `on_unavailable`、`on_missing` 或
   `on_failure` 明确声明 `skip_dependents` 时，才能将当前步骤及其依赖分支
   标记为 skipped，并继续执行不依赖该分支的步骤。
4. 每一步开始前必须报告：
   - step 名称和序号；
   - 实际执行 Agent ID；
   - 已完整读取的 Skill 和 Rules；
   - 将使用的 MCP profile 和工具范围。
   - 派发给子 Agent 时，必须把当前 step 的 capabilities、Skills、Rules、MCP
     scope、inputs_from、outputs（包括 transport 和精确路径）一并传递；不能只
     发送通用角色描述。
5. 完成当前步骤并验收其输出后，才能进入下一步骤。链式 Workflow 的后续
   步骤必须读取前一步声明的 artifacts，例如需求规格文件。
6. 只使用当前步骤列出的 Agent、Skill、Rules、capabilities 和 MCP profile，
   不得预加载无关能力或连接无关 MCP。
   - 如果步骤声明的是本地 `project_read` 或 `document_write` capability、但没有
     MCP profile，使用客户端原生项目文件读写能力；不要因为不存在
     `project-files` MCP 而阻塞本地 onboarding。
   - 这条本地文件规则不适用于远程仓库、Basecamp、GitHub、Figma 或 Shopify
     服务；远程读取仍必须遵循该步骤声明的 Skill 或 MCP route。
7. 对远程读取，`Remote read route` 是唯一执行路由：
   - `type: skill`：只使用声明的 Skill 及其只读接口，不尝试 MCP。
   - `type: mcp`：只使用声明的 MCP profile 及其 allowlist 工具，不尝试 Skill/CLI。
   - 选定路由不可用时，默认停止该步骤并报告确切错误；若 route 声明
     `on_unavailable: skip_dependents`，写入 unavailable artifact、跳过依赖分支
     并继续独立步骤，不得自动切换路由。
8. 每个 step 开始前验证 `inputs_from` 中所有必需 artifact 存在、格式有效且已完整读取。若上游 artifact 标记为 unavailable 或 skipped，且上游策略为 `skip_dependents`，跳过当前依赖步骤并记录原因，不得伪造输入。
9. 每个 completed 或 unavailable step 必须生成声明的 file output，或返回声明的
   structured `agent_result`；显式 skipped 的步骤必须记录跳过原因，不得伪造
   output，也不得只口头说“已读取”。
   - `file` output 必须由子 Agent 写入声明的精确路径并由协调 Agent 检查存在性和
     格式；`agent_result` 必须由子 Agent 返回可解析的结构化 JSON，不能用自然语言
     摘要代替。
10. `requires_gates` 未全部通过时不得开始步骤；Gate 失败时，若 Gate 声明 `on_failure: skip_dependents`，只跳过依赖该 Gate 的后续链路并继续独立步骤，否则停止 workflow。
11. `source_policy: artifact-only` 时，只能使用声明 artifact，禁止用本地旧规格、
    分支名、文件名或相似功能补全需求。
12. 每个 step 完成后记录证据、输出文件、状态（completed/unavailable/skipped）和失败信息；不得凭口头描述宣称完成。
13. 不运行 `agentflow run`；通过当前 Codex/客户端会话直接编排和执行 handoff。

## Delayed Tool Discovery

在判断工具不可用之前，必须搜索当前客户端的延迟加载工具或工具目录：

- Agent 路由：查找 `multi_agent_v1__spawn_agent`；
- Computer Use：在 ChatGPT/Codex 中先加载已安装的 Computer Use 插件 Skill，
  再查找其延迟加载的 MCP server/tools；
- 不得使用 shell 中的 `command -v` 或项目内 `require.resolve()` 判断 MCP
  运行时能力；
- 搜索后仍不可用时，记录实际搜索结果或工具调用错误；按当前 route 的
  `on_unavailable` 策略停止该步骤，或标记 unavailable 并跳过其依赖分支。

## Visual Validation Routing

当当前步骤是 `visual_validation` 时：

1. 在 ChatGPT/Codex 中必须先加载并使用 Computer Use 插件 Skill/MCP tools
   进行导航、可访问性检查、截图和视口验证。
2. 只有在 Computer Use 确实不可用，或实际调用失败并记录错误证据后，才能按
   Skill 降级到内置 Browser、Chrome control 或 `ego-browser`。
3. 不得因为其他浏览器工具已经可见、熟悉或方便就直接跳过 Computer Use。
4. 必须记录验证 URL、视口尺寸、截图/页面状态证据和发现的问题。

## Failure, Scope, and Approval Handling

- 如果步骤失败、指定 Agent/Skill/验证环境不可用，默认立即停止该步骤和后续
  链路，报告确切错误；不得假装成功或自行替换工具。只有当前 route、source
  policy 或 Gate 明确声明 `skip_dependents` 时，才能记录 unavailable/skipped，
  跳过依赖分支并继续独立步骤。指定 MCP、Skill 或 CLI 不可用时不得自动换路由。
- 如果用户改变范围，停止并要求生成新的 handoff，不得静默修改计划。
- 如果请求远程写入或审批动作，先确认准确目标、范围和影响；未获明确授权前
  不得执行。
- 保持所有本地修改在声明的项目根目录内，不得修改 `workflow.md`、`plan.json`
  或中央 AgentFlow 配置。
- 不得执行 `git push`、merge、publish、deploy、上传、Basecamp 评论/完成任务
  或 Shopify 远程写入，除非 handoff 和用户同时明确授权。

## Completion Report

在所有必需步骤完成前，不得宣称功能已经完成。最终报告必须逐项列出：

- 每个 workflow step 的状态；
- 实际执行 Agent/agent ID；
- 使用的 Skills、Rules、MCP profile 和工具；
- 修改文件和生成 artifacts；
- 测试结果；
- 视觉验证的 URL、视口和证据；
- 所有跳过项及确切原因；
- 未解决风险和后续动作。
