# Agent System Router

Keep the global context minimal. For work in this repository:

1. In this configuration repository, read `projects/agent-system.yaml`. Register a target repository once so it has a lightweight `.agents/project.yaml` entry, then run `agentflow bootstrap` to materialize its portable `.agents/` layer and thin client adapters.
2. Run `project-onboarding` only when stable project context is missing or materially stale.
3. Select one task workflow from `allowed_workflows`.
4. Load only the agent and Skills named by the active workflow step.
5. Resolve only that step's MCP profiles and apply their tool allowlists.
6. Treat all networked tools as read-only unless a step explicitly requires approval.
7. Close step-scoped MCP connections before advancing to the next step.

## Browser and desktop UI routing

When the executor is ChatGPT or Codex and the Computer Use plugin is installed
and enabled, use Computer Use first for browser or desktop UI interaction. This
includes navigation, clicking, typing, screenshots, responsive checks, and
reproducing GUI-only bugs. Do not choose the built-in Browser, Chrome control,
or `ego-browser` merely because it is already visible or familiar.

Before declaring Computer Use unavailable, load its installed Skill and search
the delayed tool catalog for its server/tools. Fall back to the built-in
Browser, Chrome control, or `ego-browser` only after Computer Use is genuinely
unavailable or an actual Computer Use call fails; record that evidence in the
task result. In non-GPT clients, use the workflow-declared portable fallback.
This routing preference does not expand permission for remote writes or other
sensitive actions.

Do not preload every file under `skills/`, and do not connect every MCP server at startup.

Installed Skill files are a capability catalog, not preloaded prompt content. Clients should expose only metadata until a Workflow step selects a Skill. The generated client MCP files are compatibility adapters; an executor that promises strict step isolation must still activate only the current plan's profiles and close them at the step boundary.
