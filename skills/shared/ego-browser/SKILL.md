---
id: shared/ego-browser
name: ego-browser
description: Use the ego-browser CLI for isolated browser automation, authenticated web interaction, screenshots, and local application testing across Codex, Claude Code, OpenCode, and Oh My Pi.
capabilities:
  required: [browser_preview]
  optional: [code_read]
metadata:
  requires:
    bins: [ego-browser]
---

# Ego Browser

Use Ego Browser as the portable browser adapter. It is a CLI Skill, not an MCP server, so every client can invoke it through its shell tool without depending on a proprietary browser plugin.

## Required pattern

Run browser operations with the installed `ego-browser` CLI and an inline Node.js program. Reuse one named task space throughout a user task:

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('project browser validation')
await openOrReuseTab('http://127.0.0.1:9292', { wait: true, timeout: 20 })
cliLog(await snapshotText())
EOF
```

Prefer `snapshotText()` with semantic refs for ordinary pages. Use `captureScreenshot()` and coordinates for canvas-like or heavily virtualized interfaces. Verify page state after navigation, input, or clicks.

Never take control back from a user-owned task space without explicit confirmation. When the task is genuinely complete, close it in a dedicated final call:

```bash
ego-browser nodejs <<'EOF'
await completeTaskSpace('project browser validation', { keep: false })
EOF
```

Do not publish, submit destructive forms, upload files, or change remote state unless the active Workflow explicitly permits it and the user has approved the exact action.
