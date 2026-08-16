# Findings, State, and Reports

## Table of Contents

| Section | Covers |
|---|---|
| [Human Decisions](#human-decisions) | Persist decisions inside the corresponding skill record |
| [Review State](#review-state) | Require attempted timestamp and status together |
| [Due Calculation](#due-calculation) | Manual records are never selected automatically but remain available for explicit runs |
| [Input Fingerprint](#input-fingerprint) | Skill identity, reviewed bytes, source boundaries, change behavior, validation, review version, exclusions, and canonical SHA-256 encoding |
| [Report Contract](#report-contract) | Begin with a compact project run summary containing completion status |

## Human Decisions

Persist decisions inside the corresponding skill record. Use `deferredFindings` for conclusions intentionally postponed and `declinedFindings` for conclusions intentionally rejected.

Each record contains:

```json
{
  "details": {
    "category": "improvementSuggestion",
    "summary": "Configured evidence supports a safer replacement.",
    "target": {
      "filePath": "plugins/example/skills/example/references/workflow.md",
      "currentText": "Exact current text"
    },
    "sources": {
      "vendor-guide": {
        "url": "https://developer.example.com/guide",
        "retrieval": { "strategy": "page" }
      }
    },
    "proposedAction": "Replace the fragile workflow with the documented procedure."
  },
  "reason": "Adoption is deferred until the next release cycle.",
  "decidedAt": "2026-08-13T23:00:00Z",
  "revisitAfter": "2026-10-01T05:00:00Z"
}
```

Require exactly one of `currentText` and `anchorText`. Require `revisitAfter` for deferred records and forbid it for declined records. Use ISO 8601 UTC instants.

Suppress a later finding only when category, target, normalized source definitions, and proposed action still match. Ignore paraphrased summary, reason, and timestamps for matching. Any material target, source boundary, category, or action change resurfaces the finding.

Retain expired deferrals, mark them inactive, and display their findings again. Never delete or renew decisions unattended. Never defer or decline retrieval and processing failures.

## Review State

Use this optional shape:

```json
{
  "lastAttemptedReview": "2026-08-13T23:00:00Z",
  "lastAttemptStatus": "completed",
  "lastCompletedReview": "2026-08-13T23:00:00Z",
  "inputFingerprint": "sha256:0123456789abcdef..."
}
```

Require attempted timestamp and status together. Permit `completed` and `incomplete` only. Require completed timestamp and fingerprint together. Never persist error text.

Advance `lastCompletedReview` only after every configured source and functional file was processed, the complete result validated, and report delivery succeeded. Corrections, improvement suggestions, human decisions, 404/410 findings, and disabled post-edit validation are completed outcomes. Any retrieval, processing, structured-output, edit-validation, or delivery failure leaves completed state unchanged.

Fingerprint the final reviewed file state: corrected files after validated applied corrections, or unchanged files in report-only mode. Carry that fingerprint in the validated research result, report payload, and completed state. A mismatch at either delivery step invalidates the result. Do not advance completed state after reverted corrections.

## Due Calculation

Manual records are never selected automatically but remain available for explicit runs.

An interval record is currently due for review when:

- It has never completed a review.
- Its current input fingerprint differs from stored state.
- `now >= lastCompletedReview + intervalDays × 24 hours`.
- Its last attempt was incomplete and the 24-hour automatic retry backoff has elapsed.

Use `lastAttemptedReview` only for incomplete-attempt backoff. An explicit manual invocation may force an immediate retry. Findings do not make a completed skill immediately due again.

If no interval records are due, output `No skills are due.` and do not rewrite any artifact.

## Input Fingerprint

Calculate `sha256:` plus lowercase hexadecimal over canonical UTF-8 JSON containing:

- The stable skill ID and configured path.
- Every reviewed functional file's relative path and exact bytes.
- Normalized source definitions and retrieval boundaries.
- Effective change-preparation behavior: the configured local correction strategy or fixed GitHub pull-request diff behavior.
- Project `changeValidation`.
- The helper's internal review-procedure version.

Sort object keys and file/source entries, use compact JSON separators, and exclude schedules, timestamps, scheduler choice, delivery settings, and deferred or declined decisions.

A changed fingerprint immediately invalidates retained current-state presentation. Preserve previous findings but label them `Based on an earlier configuration or skill revision; a new review is due.` Never state-only auto-merge that mismatch.

## Report Contract

Begin with a compact project run summary containing completion status, review time, reviewed skill IDs, and source retrieval status with successful and attempted page counts. Follow it with one per-skill status table. Distinguish `Reviewed this run` from retained results for unselected skills. Always list configured source-less records as `Draft — skipped (no configured sources)` with zero sources, even when runnable skills were reviewed. Never include those drafts in reviewed IDs or synthesize review results or state for them.

Use these project-wide headings when any active finding exists:

```markdown
## 🛠 Corrections
## 💡 Improvement Suggestions
## 🚩 Human Decisions Needed
## ⚠️ Retrieval or Processing Failures
```

Render every heading and put `No findings.` in empty categories. Follow them with `## 🗃️ Deferred and Declined Findings` when decisions exist. If no active or retained decision findings exist, make the findings portion only `No findings.` If no runnable skills were reviewed, say `No runnable skills were reviewed.` and list skipped records instead.

For every finding include the managed skill ID, repository-relative file path, exact current text or durable anchor, concise explanation, configured source ID and root URL, exact evidence-page URL, short supporting excerpt, and proposed action when applicable. Use line numbers only as navigation aids.

Keep one current-state report rather than an accumulating changelog. In local delivery, rewrite the owned region at the configured Markdown path. In GitHub delivery, rewrite the owned pull-request-body region and use a committed fallback report only for platform size limits.

Bound the region with:

```markdown
<!-- keeping-skills-current:start project="<identity>" reportVersion="1" reviewStateFingerprint="sha256:..." -->
...
<!-- keeping-skills-current:payload <encoded-current-state-results> -->
<!-- keeping-skills-current:end -->
```

The encoded payload is workflow-owned state for retaining unselected results and verifying delivery; it is not a source cache. Preserve human text outside the region. Missing, duplicated, malformed, or inconsistent markers require interactive reconciliation. Before advancing completed state, require the delivered payload to contain the validated current result and current input fingerprint. Recover a clearly owned interrupted run by reviewing affected skills again, never by reconstructing missing findings.
