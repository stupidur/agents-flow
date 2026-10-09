---
name: github-context-readonly
description: Inspect GitHub repositories, pull requests, issues, files, branches,
  commits, CI status, and failed logs without changing remote state. Use when a Workflow
  explicitly needs remote repository context; never push, merge, comment, create branches
  or issues, rerun jobs, or modify settings.
---

# GitHub Context Read-only

Gather remote repository evidence without modifying GitHub. When this Skill is
the active `remote_read` route, use the `gh` CLI directly; do not attempt an MCP
route.

## Read-only CLI Route

Use demonstrably read-only commands such as:

- `gh repo view --json ...`;
- `gh pr view`, `gh pr checks`;
- `gh issue list`, `gh issue view`;
- `gh run list`, `gh run view`;
- `gh api` requests using GET only.

Always specify `--repo owner/repo` when outside a Git repository. Never create,
edit, comment, approve, close, merge, push, rerun, cancel, dispatch, upload, or
change settings. If authentication, repository scope, or the declared adapter
is unavailable, stop and report the exact error.

## Output

1. Resolve the explicit repository or URL.
2. Record repository, revision, PR, issue, branch, or run identifiers.
3. Return structured evidence to the active Workflow step.
