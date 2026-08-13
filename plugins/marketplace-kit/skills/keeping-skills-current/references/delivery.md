# Delivery and Transactions

**Contents:** [Local Report](#local-report) · [GitHub Pull Request](#github-pull-request) · [Ownership](#ownership) · [State-Only Auto-Merge](#state-only-auto-merge) · [Recovery](#recovery)

## Local Report

Write the current report, manifest state, and any authorized corrections into the local working tree. Never stage, commit, push, or create a pull request. Allow report-only operation outside Git. Require a Git worktree before `applyHighConfidenceCorrections` so a durable diff and restoration boundary exist.

Create the report only after the first actual review. Preserve it unchanged when no skills are due. Version-control history remains the project's responsibility.

## GitHub Pull Request

Require a Git worktree, GitHub remote, authenticated compatible GitHub client, permission to push and open pull requests, and no conflicting unowned branch or pull request. Derive the default branch from the repository and store only the stable `branchName`.

Use one stable branch and at most one open pull request per project. Mark both as workflow-owned. Inspect the authoritative owned state before selection, but do not move the owned branch merely to discover that nothing is due. At the start of a run:

1. Fetch the default and owned remote refs without checking out or moving the local owned branch. Inspect the owned pull request and validate its marker.
2. Compare any local owned tip with the fetched tip. Use the newer owned tip when one is a linear descendant; stop on divergence or uncertain ownership. When no owned tip exists, use the fetched default tip as the preview base.
3. Inspect any existing owned worktree before the no-due optimization. If uncommitted changes touch the locator, active manifest, or a managed skill's functional files, committed refs do not represent the complete review state. A no-question run must stop for reconciliation instead of reporting that nothing is due; an interactive run may reconcile the work without discarding it.
4. Create a disposable detached worktree from the preview base. Incorporate the fetched default branch only in the disposable worktree when the preview began from an owned tip, then run preflight and due selection there.
5. If nothing is due and no relevant owned-worktree edits require reconciliation, delete the disposable worktree and make no owned-branch, manifest, report, commit, push, or pull-request change.
6. If work is selected, establish the stable branch in its isolated worktree. Create it from the fetched default tip when no owned tip exists. Otherwise fast-forward a behind local branch to the fetched owned tip, preserve local-ahead commits as preexisting work, stop on divergence, and incorporate the fetched default without rewriting history or force-pushing.
7. Repeat authoritative preflight and selection from the established branch before research. Treat human commits as preexisting work and do not automatically modify the same files during a no-question run.

Commit each skill transaction separately, including its state and authorized edits or supporting artifacts. Build all commits locally, push once after the complete run, then update the pull-request body immediately. Never expose a half-reported remote run.

Make a completed review with corrections, suggestions, or human decisions ready for human review. Use draft status for an incomplete review or a temporary fallback report. A later run updates the existing branch and pull request rather than opening another.

Use the pull-request body as the report. If it exceeds the platform limit, commit the configured fallback Markdown report, leave the pull request draft, put a summary and link in the body, and remove the temporary file before permitting merge. If it is merged manually, offer an interactive cleanup pull request later; never write silently to the default branch.

After a verified merge, delete only the marked owned branch. If the pull request was closed without merge, pause no-question delivery and request interactive reconciliation: restore it, record decisions, or discard the marked automation branch and start from the current default branch.

## Ownership

Put a durable hidden marker in every owned report region and pull-request body. Put a `Keeping-Skills-Current: <project identity>` trailer in every automation commit. Include project identity and the intended branch in generated scheduler instructions.

Adopt an existing artifact only interactively after showing exactly what will be marked. Never overwrite, delete, or rename unmarked or ambiguously owned content.

Use one project-level run lock. Store it in Git-private metadata for Git repositories and temporary storage keyed to the resolved root outside Git. Compare the starting manifest and branch revision again immediately before writing. Stop if another run advanced either. Never force-push.

## State-Only Auto-Merge

Treat `autoMergeStrategy: stateOnly` as a narrow acceptance gate, not edit authorization. Permit unattended merge only when semantic comparison proves that exclusively approved per-skill state fields changed, the report contains no active or retained findings or failures, the branch is conflict-free, and required checks are green.

Do not allow schedule, source, decision, correction, report-fallback, configuration, or skill-content changes through this gate. Keep `autoMergeStrategy: none` when repository auto-merge capability is unavailable.

## Recovery

Publish report content before advancing manifest state. Trust a completed state only when the delivered owned marker carries the matching review-state fingerprint.

If delivery fails after local commits but before the report updates, mark the run interrupted and reconcile it before trusting freshness. A later no-question run may recover only when ownership is valid and no conflict exists, by reviewing affected skills again and replacing the interrupted result. Never promote partial state or reconstruct omitted findings.

If the owned branch advances during a run, stop before pushing. Preserve all new commits and never rewrite history. Dirty files elsewhere in the repository do not block work; dirty target files follow the protected-work rule.
