---
name: playwright-cli
description: Validate browser pages, responsive layouts, screenshots, and console errors with Playwright CLI when the workflow's preferred Computer Use or Ego Browser route is unavailable or unsupported.
metadata:
  requires:
    bins: [playwright-cli]
---

# Playwright CLI Browser Validation

Use this CLI Skill as the declared fallback in the `browser-preview` profile.
It is not a Playwright MCP server. Stay within the current step's
`browser_preview` capability and tool allowlist.

## Fallback and availability

- In ChatGPT/Codex, discover and try Computer Use first. If unavailable,
  unsupported for the required operation, or failing, record the evidence and
  try Ego Browser. If Ego Browser is also unavailable, unsupported, or failing,
  use Playwright CLI. Non-GPT clients start with Ego Browser.
- Check `playwright-cli --help`. If the global executable is missing, check an
  existing local installation with `npx --no-install playwright cli --help`;
  when supported, use that prefix consistently for all commands below.
- If environment setup is in scope, the official installation command is
  `npm install -g @playwright/cli@latest`. Do not change theme manifests or
  lockfiles to obtain this tool. Bootstrap copies this Skill; it does not
  install the executable or browser binaries.
- If browser launch or the required operation still fails, retain the actual
  error and follow the handoff's failure policy. Do not claim validation passed.

## Validation pattern

Use a unique task-owned session, an authorized preview URL, and evidence paths
inside the project's ignored task output directory. The following example uses
an already running local preview; it does not start or upload a Shopify theme:

Confirm `.agentflow/` and `.playwright-cli/` are ignored before running commands;
the CLI also writes snapshots and logs under `.playwright-cli/` by default.

```bash
mkdir -p .agentflow/runs/browser-validation
playwright-cli -s=theme-validation open 'http://127.0.0.1:9292'
playwright-cli -s=theme-validation resize 1920 1080
playwright-cli -s=theme-validation snapshot
playwright-cli -s=theme-validation screenshot --filename=.agentflow/runs/browser-validation/desktop.png
playwright-cli -s=theme-validation resize 768 1024
playwright-cli -s=theme-validation screenshot --filename=.agentflow/runs/browser-validation/tablet.png
playwright-cli -s=theme-validation resize 390 844
playwright-cli -s=theme-validation screenshot --filename=.agentflow/runs/browser-validation/mobile.png
playwright-cli -s=theme-validation console error
playwright-cli -s=theme-validation close
```

Read each page snapshot and inspect the saved screenshots. Use current snapshot
refs for permitted interactions, then inspect the new page state. Record the
actual browser/version, URL, viewport, fallback reasons, console findings, and
artifact paths in the step's declared output.

Follow the project's browser-testing rules. Chromium and Playwright WebKit do
not prove actual Safari or BrowserStack iPhone coverage; record missing matrix
entries explicitly.

Close only the session created for this task, including on failure. Do not use
`close-all` or `kill-all`, attach to a user-owned browser, persist credentials,
or export storage state for ordinary validation. Review generated logs before
sharing them and keep browser output out of commits.

Do not submit forms, upload files, publish, or mutate remote state unless both
the active workflow and the user authorize that action. A browser fallback
does not expand permissions or authorize uploading a theme to obtain a URL.

Official command reference: [Microsoft Playwright CLI](https://github.com/microsoft/playwright-cli).
