# Scheduling

**Contents:** [Strategies](#strategies) · [Generated Invocation](#generated-invocation) · [Activation](#activation) · [Reconciliation](#reconciliation)

## Strategies

Store only the portable scheduler strategy:

- `none` — no workflow-managed recurring scheduler. Manual invocation remains available and interval records can still be inspected or run explicitly.
- `agentPlatform` — a recurring agent automation invokes the installed skill.
- `githubActions` — a generated workflow invokes a user-selected agent command in GitHub Actions.

Create one scheduler per project, normally once daily. Let per-skill `intervalDays` determine what is currently due. Keep provider-specific recurrence syntax, timing, IDs, and credentials in the scheduler's own configuration, not the manifest.

Permit `localReport` with `agentPlatform` only when the automation uses a persistent local checkout. Clone-based or otherwise ephemeral agent scheduling requires `githubPullRequest`. Require `githubPullRequest` for GitHub Actions; do not add artifact-upload delivery in version 1.

## Generated Invocation

Use this exact substantive instruction in a managed scheduler:

> Use `$keeping-skills-current` to review every configured skill that is currently due for review, without asking questions, in this project.

Add only a durable ownership marker and project identity. Keep sources, intervals, delivery, correction strategy, and validation exclusively in the manifest.

For an agent-platform scheduler, prefer direct creation when the current harness exposes a scheduling interface. Otherwise provide a paste-ready title, project, prompt, and recommended daily recurrence.

For GitHub Actions, require the user to select the agent command and credential-reference mechanism before generating a marked conventional workflow file. GitHub Actions alone cannot interpret a skill. Never store secrets in the manifest or workflow body.

## Activation

During configuration:

1. Save and validate the confirmed project configuration with `scheduler: "none"`.
2. Run every source-ready skill once using the confirmed delivery behavior. Local-report delivery with `reportOnly` proposes changes without editing; GitHub pull-request delivery prepares supported changes on its owned branch. Treat findings as successful research outcomes; treat retrieval and processing failures as blockers.
3. Confirm that the scheduler environment can retrieve every configured source within its boundary and can durably deliver the report.
4. For fresh-clone scheduling, require the manifest and optional locator to be committed and reachable from the cloned branch. Do not commit or publish configuration merely because configuration was requested.
5. Create the uniquely marked scheduler after separate authorization.
6. Update the manifest strategy only after creation is verified.

If creation fails, restore the previous configuration or remove newly created configuration unless the user explicitly accepts keeping it with `none`. If the external result is uncertain, stop for reconciliation rather than creating or deleting another scheduler.

## Reconciliation

Manage only one scheduler with a unique keeping-skills-current marker for the project. Never adopt, update, or delete a shared multi-project scheduler from one project. A manually maintained orchestrator may invoke several projects, but it remains outside this workflow's ownership.

Let `status` report scheduler discrepancies without repair. Let an already-started review continue safely when scheduler state drifts. Offer changes only through interactive configuration, with the full external and manifest diff.

When no interval skills remain, offer to disable or delete the owned scheduler. During full removal, disable the uniquely marked scheduler first, reconcile owned pull-request delivery, then remove owned local configuration. Stop before deleting configuration when an external cleanup result is uncertain.
