---
id: shared/basecamp-source-verification
capabilities:
  required: [requirement_analysis]
---
# Basecamp Source Verification

Validate the local Basecamp context artifact before any specification is
written, and validate the generated specification when that artifact is also
declared as an input. This is a hard gate for dependent steps, not a reason to
terminate unrelated workflow branches.

## Required checks

1. The context artifact exists and is valid JSON.
2. It contains the requested source URL, a stable Basecamp record ID, a
   non-empty card or task title, and the complete readable body.
3. The source URL/ID and title are consistent with the record returned from the
   requested Basecamp URL.
4. Requirements evidence cites the context artifact and does not replace
   missing body content with local files, branch names, filenames, old specs, or
   assumptions about similar features.
5. Any missing, ambiguous, truncated, or contradictory source data produces a
   failed verification artifact with `disposition: "skip_dependents"` when the
   handoff declares that policy. It skips every dependent specification or
   implementation step, but does not stop unrelated workflow branches.
6. When validating a specification, its title must match the Basecamp title,
   every requirement must trace to the source context, and assumptions must not
   be presented as confirmed requirements.

## Output contract

Write the declared verification artifact with:

- `passed`: boolean;
- `source_url`, `source_id`, and `title`;
- `checks`: each check with `status`, `evidence`, and `failure_reason` when it fails;
- `blocking_reason` when `passed` is false.
- `disposition`: `"skip_dependents"` when the source gate fails under the
  continuation policy.

Never mark the gate passed merely because Basecamp was opened successfully.
