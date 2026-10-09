---
id: shared/review-aggregation
capabilities:
  required: [project_read, document_write]
---
# Review Aggregation

Read every completed review result from the declared `inputs_from` references.
Do not perform a new independent review and do not silently omit a reviewer.

Normalize findings by severity, preserve each reviewer's evidence and reviewer
ID, deduplicate only when the evidence and root cause are the same, and write
the declared aggregate artifact. If any required review result is missing or
malformed, stop instead of producing a partial review.
