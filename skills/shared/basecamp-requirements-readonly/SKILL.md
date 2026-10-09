---
name: basecamp-requirements-readonly
description: Read Basecamp projects, todos, cards, messages, documents, files, schedules,
  and check-ins to gather product requirements without changing remote state. Use
  only for requirement analysis when Basecamp is an explicit source; never create,
  update, complete, comment, upload, subscribe, or delete anything.
---

# Basecamp Requirements Read-only

Use Basecamp only to gather evidence for `product-spec`. When this Skill is the
active `remote_read` route, use the Basecamp CLI directly; do not attempt an MCP
route.

## Read-only CLI Route

Use the Basecamp CLI in read-only mode:

1. Parse the supplied URL first with `basecamp url parse "<url>" --json`.
2. Use `--agent --json` or `--json` for list/show/search/download operations.
3. Read only the task's relevant todos, cards, messages, documents, files,
   schedules, check-ins, and attachments.
4. Never run a mutating command, even if the CLI exposes it.

## Required Artifact

Before completing the step, write the workflow-declared `basecamp_context`
artifact as valid JSON. When the card is readable, it must contain the requested
URL, stable record ID, card/task title, complete body text, source URLs for
referenced messages or attachments, and an explicit list of unreadable or
missing fields. A successful CLI read without this artifact is a failed step.

If the card body, authentication, project scope, or CLI route is unavailable and
the active route declares `on_unavailable: skip_dependents`, still write the
artifact with `status: "unavailable"`, the requested URL, the exact error or
missing fields, and no fabricated requirements. Mark this step unavailable and
let the coordinator skip only steps that depend on this artifact; continue
independent workflow steps. Do not switch to MCP, a browser, local specs, or
another remote route.

Do not use shell presence checks to decide whether the CLI is available. If the
CLI or authentication/project scope is missing, record the exact error in the
unavailable artifact when the workflow policy permits continuation; otherwise
stop the step according to the handoff.

## Output

1. Resolve the explicit Basecamp URL or project supplied by the user.
2. Record source URLs or stable IDs with each extracted requirement.
3. Separate explicit requirements from assumptions and unresolved questions.
4. Return structured evidence to the requirement analysis step. An unavailable
   artifact is a valid status result, not evidence that may be replaced by
   guesses.
