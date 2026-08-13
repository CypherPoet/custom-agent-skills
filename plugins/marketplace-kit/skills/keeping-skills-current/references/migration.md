# One-Shot Legacy Migration

Migrate `skill-fact-check` configuration interactively. Never support the old identity, manifest shape, datelines, branch, or scheduler after cutover.

1. Refresh the live repository and open legacy pull requests. Preserve still-valid substantive corrections and runtime citations; omit obsolete session metadata and maintenance-only date edits.
2. Run `migrate-legacy` to create a proposal from the old weekly, monthly, and never lists plus each selected skill's `## Primary Sources` section.
3. Convert weekly records to seven-day intervals and monthly records to 28-day intervals. Omit former never records unless explicitly selected as manual drafts. Convert an active source-less record to a manual draft.
4. Treat every old source link as a proposal. Resolve its canonical destination, choose a descriptive source ID, select page or crawl, preview crawl boundaries, and require confirmation. Never silently import URLs.
5. Surface every old acknowledgment with its locator, reason, and dates. Permit only adding a configured source that makes the subject reviewable or discarding the old acknowledgment. Do not convert it into a deferred or declined decision without a matching current finding.
6. Write and validate the new manifest before removing the old one. Do not import Markdown datelines into `lastCompletedReview`; establish trustworthy state through an initial report-only run.
7. Preview `cleanup-legacy`, then run it with `--write` only after accepted sources are represented externally. It removes updater-only `## Primary Sources` sections and standalone verification markers. Preserve citations needed by runtime readers and substantive dates.
8. Disable the old scheduler immediately before merging the identity cutover. Activate replacement project schedulers only after their manifests are published and initial reviews succeed. Permanently delete the old scheduler after replacement runs pass.
9. Remove the old skill directory, scripts, manifests, structural checks, branches, pull-request markers, prompts, and documentation. Provide no alias, automatic migration, or compatibility fallback.

An older supported manifest may be migrated only during interactive configuration after displaying the full diff. A scheduled run stops with upgrade guidance. A newer unknown schema version always stops until the installed skill is upgraded.
