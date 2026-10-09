---
id: shared/acceptance-criteria
capabilities:
  required: [requirement_analysis, document_write]
---
# Acceptance Criteria

Write observable, testable criteria. Cover the happy path, validation failures, permissions, edge cases, and explicit non-goals.

Read every required `inputs_from` artifact and pass every `requires_gates` check
before writing a specification. When `source_policy` is `artifact-only`, copy
the task title and requirements from the declared source artifact, preserve
source IDs/URLs, and keep assumptions separate. If the source body is missing,
the title conflicts, or the verification gate is absent/failed, do not write a
specification. If the relevant source policy or Gate declares
`skip_dependents`, record the skipped status and exact reason, then allow
unrelated workflow steps to continue; otherwise stop the dependent branch.
