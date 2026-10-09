---
id: shared/codex-computer-use
name: codex-computer-use
description: Route browser and desktop UI work through Computer Use first in ChatGPT or Codex; use Ego Browser when it is unavailable or unsupported, then Playwright CLI if Ego Browser is also unavailable or unsupported.
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
5. When Computer Use is unavailable, unsupported for the required operation,
   or fails, record the evidence and use `shared/ego-browser` under the
   `browser-preview` profile. If Ego Browser is also unavailable, unsupported,
   or fails, record its evidence and load `shared/playwright-cli` under the
   same profile. Non-GPT clients start with Ego Browser, then Playwright CLI.
6. These fallbacks cover browser validation only. They cannot replace native
   desktop app control; report unsupported desktop operations separately.

Computer Use is a ChatGPT/Codex plugin capability, not a portable project MCP
server. Do not replace its plugin Skill with the legacy `node_repl` +
`@oai/sky` route, and do not assume it exists in other clients.
