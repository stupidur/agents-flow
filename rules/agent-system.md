# Agent System Rules

- Permissions are intersected across project, workflow, agent, and step scopes.
- External write operations require an explicit approval step.
- Skills declare capabilities; workflows choose concrete MCP profiles.
- Project roots never include parent directories or user configuration directories.
- Explicit global registration/bootstrap may write the shared global layer;
  task workflows only read it and keep all task writes inside the repository.
- Generated project AGENTS.md must reference applicable global instructions
  and rules when the handoff declares global_context; project guidance must
  not silently weaken global constraints.
