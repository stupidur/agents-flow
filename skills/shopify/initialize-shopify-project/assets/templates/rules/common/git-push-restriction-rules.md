---
alwaysApply: true
---

# Git Push Policy (Customer Confirmation)

## MANDATORY RULES

### Push Rules
- **MUST** obtain **explicit customer confirmation** before any `git push` (or equivalent) to a **remote branch**; the confirmation must state the **exact remote name** (e.g. `origin`) and **branch name** (e.g. `main`, `feature/x`).
- **MUST NOT** push without that confirmation, even if the assistant believes the change is correct.
- **MUST NOT** perform **force push** (`--force`, `--force-with-lease` to rewrite remote history) unless the customer **explicitly** approves force push and the target branch.
- **MUST NOT** delete remote branches or push tag changes that alter shared refs without **explicit customer approval** for that operation and target.
- **MUST NOT** treat silence or vague assent (“ok”, “go ahead”) as confirmation unless the **remote + branch** are clearly identified in the same exchange.

### Local Operation Rules
- **ALLOW** all local git operations (commit, branch, merge, rebase) that do not require customer confirmation for remote targets.
- **ALLOW** fetching and pulling updates from remote (read-only sync of history into the local clone).
- **ALLOW** cloning repositories and viewing remote configuration (`git remote -v`, branch lists).

## IMPLEMENTATION GUIDELINES

### Before Push Checklist
1. State intended **`remote` / `branch`** in plain language.
2. Ask the customer to confirm **in writing** (same thread) that this push is authorized.
3. Only then run push; if the customer declines or is unclear, **do not push**.

### Example Assistant Prompt to Customer
```text
I am about to push local branch <local-branch> to <remote>/<branch>.
Please confirm explicitly: “Yes, push to <remote> <branch>.”
If you want a different remote or branch, specify it before I run git push.
```

### Error / Refusal Pattern
- If confirmation is missing or ambiguous: refuse push and list what is needed (remote + branch + explicit yes).
- Do not substitute your own judgment for customer intent on **shared** remotes.

### Exceptions
- **Personal forks / sandboxes**: If the customer states that the remote is solely theirs and confirms push, the same **explicit remote + branch** rule still applies once per push target change.
- **CI or automation**: Out of scope for this document; human-in-the-loop confirmation is assumed for assistant-driven pushes.

## RATIONALE

This policy ensures that:
1. Shared remote state changes only after **clear customer intent** on **where** code goes.
2. Wrong-branch or accidental production pushes are reduced.
3. Local work stays fast; **remote writes** stay gated.
4. Force push and destructive remote operations stay rare and **explicitly** approved.
