---
id: shared/codex-computer-use
name: codex-computer-use
description: Route browser and desktop UI work through the installed Computer Use plugin first in ChatGPT or Codex; use Browser, Chrome control, or shared/ego-browser only after Computer Use is unavailable or fails.
capabilities:
  required: [browser_preview]
  optional: [code_read]
---

# GPT/Codex Computer Use Routing

Use the installed Computer Use plugin as the primary browser and desktop UI
surface when this Workflow is executed in ChatGPT or Codex. Load the plugin's
Computer Use Skill and invoke its MCP tools for accessibility inspection,
screenshots, navigation, clicking, typing, and other visual interactions.

## Routing

1. In ChatGPT or Codex, use Computer Use before the built-in Browser, Chrome
   control, or the Ego Browser CLI. Tool visibility, familiarity, or convenience
   is not evidence that Computer Use is unavailable.
2. Start by reading the current browser/app state, then re-read state after
   every interaction before using new element references.
3. Keep interaction scoped to the browser/app and flow requested by the user.
   Do not submit forms, upload files, publish, or change remote state unless the
   active Workflow explicitly permits it and the user approved the exact action.
4. Before falling back, load the installed Computer Use Skill, search delayed
   tools for its server/actions, and make an actual scoped call when available.
   Record the discovery result or call error that caused the fallback.
5. When Computer Use is unavailable or fails, use the workflow-declared
   fallback. For portable Claude Code, OpenCode, Oh My Pi, or other non-GPT
   clients, that fallback is `shared/ego-browser` and its `browser-preview`
   profile.

Computer Use is a ChatGPT/Codex plugin capability, not a portable project MCP
server. Do not replace its plugin Skill with the legacy `node_repl` +
`@oai/sky` route, and do not assume it exists in other clients.
