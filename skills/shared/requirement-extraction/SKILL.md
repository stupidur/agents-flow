---
id: shared/requirement-extraction
capabilities:
  required: [requirement_analysis]
  optional: [project_read]
---
# Requirement Extraction

Identify the user outcome, in-scope behavior, constraints, assumptions, open risks, and measurable acceptance criteria. Prefer evidence from the current project when existing behavior matters.

When the active Workflow declares `inputs_from`, read every required input before
extracting requirements and return the declared structured output. When
`source_policy.mode` is `artifact-only`, use only the declared source artifact;
do not fill missing requirements from local specifications, branch names,
filenames, or similar features. If a required artifact is missing, malformed, or
contradictory, follow its declared policy: with `on_missing: skip_dependents`,
return an explicit `skipped`/`unavailable` status and reason, then let the
coordinator continue unrelated steps; otherwise stop instead of inferring.

If the source artifact has `status: "unavailable"`, do not extract requirements
from it and do not substitute local specs, branch names, filenames, or similar
features. Return the unavailable status so dependent specification steps are
skipped rather than fabricated.
