# Configuration Contract

## Table of Contents

| Section | Covers |
|---|---|
| [Project Lookup](#project-lookup) | Store durable workflow files together by default |
| [Manifest](#manifest) | Use schema version 2 and the property order shown in `assets/manifest.template.json` |
| [Skill Records](#skill-records) | Key `skills` by stable project-local IDs matching `^[a-z0-9]+(?:-[a-z0-9]+)*$` |
| [Sources](#sources) | Authoritative references that ground this guidance |
| [Helper Interface](#helper-interface) | Stable helper commands for configuration, review, and state operations |
| [Configure Transaction](#configure-transaction) | Discover candidate skills inside the resolved root, respect project ignore rules, and never follow directory symlinks |

## Project Lookup

Store durable workflow files together by default:

```text
.keeping-skills-current/
├── manifest.json
├── config.json       # only when manifestPath overrides the default
└── report.md         # only after the first local-report review
```

Resolve an explicit manifest argument before `.keeping-skills-current/config.json`, then use `.keeping-skills-current/manifest.json`. Accept `config.json` only as an object containing one `manifestPath` string. Reject unknown fields. A redundant locator pointing to the default is valid but can be removed interactively.

Resolve every stored path against the project root. Require a nonempty repository-relative forward-slash path, reject absolute paths, `.` or `..` segments, backslashes, non-JSON manifest targets, symlink escapes, and resolved targets outside the root. Keep manifests, locators, and reports outside every managed skill directory.

When an override is active and a separate default manifest remains, treat the override as authoritative but stop automated mutation until interactive configuration reconciles the inactive owned file.

Own exact files, not the entire directory. Preserve unknown files and remove `.keeping-skills-current/` only after verified owned files are removed and the directory is empty.

## Manifest

Use schema version 2 and the property order shown in `assets/manifest.template.json`:

1. `schemaVersion`
2. `scheduler`
3. `delivery`
4. `changeValidation`
5. `skills`

Require every field. Reject unknown fields and unknown enum values.

`scheduler` is one of `none`, `agentPlatform`, or `githubActions`.

`delivery` is exactly one of:

```json
{
  "strategy": "localReport",
  "reportPath": ".keeping-skills-current/report.md",
  "correctionStrategy": "reportOnly"
}
```

```json
{
  "strategy": "githubPullRequest",
  "branchName": "automation/keeping-skills-current",
  "autoMergeStrategy": "none",
  "fallbackReportPath": ".keeping-skills-current/report.md"
}
```

Omit `fallbackReportPath` unless a pull-request body reaches its size limit. Permit `autoMergeStrategy` values `none` and `stateOnly` only.

For local-report delivery, `correctionStrategy` is `reportOnly` or `applyHighConfidenceCorrections`. GitHub pull-request delivery has no correction strategy: it always prepares supported corrections and concrete improvements on its owned branch because the diff is the proposal. `autoMergeStrategy` independently controls acceptance. `changeValidation` is `enabled` or `disabled`.

Write canonical UTF-8 JSON using two-space indentation and one trailing newline. Preserve the fixed property order, sort skill and source keys by ID, sort crawl paths lexically, and preserve chronological decision-array order.

## Skill Records

Key `skills` by stable project-local IDs matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Require unique paths and reject two records whose functional file sets overlap.

Each record contains, in order:

```json
{
  "path": "plugins/example/skills/example",
  "schedule": { "recurrence": "manual" },
  "sources": {},
  "deferredFindings": [],
  "declinedFindings": []
}
```

Use `{"recurrence":"interval","intervalDays":28}` for recurring review. Require a positive integer and at least one source. A manual record may be a source-less draft. Unlisted skills are unmanaged; there is no `never` value.

Point `path` to a directory containing exactly one root `SKILL.md`. Moving a managed skill changes `path`, not its ID. A missing path fails that skill and never guesses a replacement.

Add `state` only after an attempt. See [`findings-and-state.md`](findings-and-state.md) for its shape.

## Sources

Key sources by lowercase kebab-case IDs unique within their skill. Store each source directly beside the skill path:

```json
{
  "url": "https://developer.example.com/documentation/",
  "retrieval": {
    "strategy": "crawl",
    "includePaths": ["/documentation/"],
    "excludePaths": [],
    "maxDepth": 2,
    "maxPages": 25
  }
}
```

Page retrieval contains only `{"strategy":"page"}`. Crawl retrieval requires `includePaths`, `maxDepth`, and `maxPages`; `excludePaths` is optional. Allow `maxDepth` 1–5 and `maxPages` 1–100.

Accept only public anonymous HTTPS URLs. Reject user information, embedded credentials, fragments, loopback and private-network hosts, custom headers, and opaque or executable resources. Preserve page query strings; reject query strings on crawl roots.

Normalize paths before storage. Require leading slashes, ignore query and fragment components during authorization, match on segment boundaries, and let exclusions win. Require the canonical starting path to match an inclusion prefix.

Reject exact duplicate source requests within one skill. Permit the same URL when retrieval strategy or boundaries differ materially and permit matching requests across skills.

## Helper Interface

Use one public entry point:

```bash
python3 scripts/keeping_skills_current.py <command> [arguments]
```

Commands emit structured JSON on standard output, diagnostics on standard error, and nonzero status on failure. The same declarative Python model generates the bundled schemas and validates normalized runtime values; procedural checks add path, evidence-boundary, and state semantics that JSON Schema cannot express:

- `preflight` — resolve and validate configuration; add `--mutation` for a write-intending preflight.
- `canonicalize` — validate and atomically rewrite the manifest using the canonical property and key order.
- `status` — return read-only project and per-skill state.
- `due-set` — return due interval records in deterministic order. Use `--now` for tests and `--force-failed` only for an explicit manual retry.
- `fingerprint --skill-id <id>` — calculate the final review-input fingerprint and list functional files. Put this value in the structured research result after edits and validation finish.
- `render-report --input <result.json> --validate-only --provisional` — validate the pre-edit result and exact target locators against unchanged reviewed files. Its JSON response includes the `provisionalFingerprint` that binds a later edit-capable final pass.
- `render-report --input <result.json> [--provisional-fingerprint <sha256:...>] [--existing-report <path>] [--output <path>]` — validate final selected results, retain unselected current-state results, and render or atomically update an owned Markdown region. Require the fingerprint returned by the provisional pass whenever the configured delivery can edit files.
- `apply-state --input <result.json> --delivered-report <path> [--skill-id <id>]` — validate the research result, its current input fingerprint, and its matching delivered report payload, then atomically update only review state.
- `migrate-manifest [--write]` — preview or atomically migrate the active version-1 manifest to version 2 during interactive configuration. Never call unattended.
- `migrate-legacy --legacy-manifest <path> [--write]` — create a version-2 proposal from the retired fact-check format or, after interactive confirmation, write it. Never call unattended.
- `cleanup-legacy [--write]` — preview or remove updater-only `## Primary Sources` sections and standalone `**Verified:**` markers from configured skills after their sources are represented in the manifest.
- `schema --kind <manifest|research> [--version <n>] [--output <path>|--check <path>]` — render or verify a bundled schema; omit `--version` for the current version.

Accept `--project-root` and optional `--manifest` on project commands. Require Python 3.11 before any command.

## Configure Transaction

Discover candidate skills inside the resolved root, respect project ignore rules, and never follow directory symlinks. Display candidates without enrollment side effects.

For existing configuration, prefill all values and preserve every unedited field. Before writing, display:

- The manifest diff.
- Locator creation, update, or removal.
- Delivery artifact moves or cleanup.
- Scheduler creation, update, disablement, or deletion.
- Skills added or removed and the exact state or decisions that removal discards.

Confirm the complete transaction once. Prepare the new manifest, resolve it through normal lookup, and validate it before removing an old owned manifest. A failure must leave at least one usable configuration and never leave `config.json` pointing to a missing file.

Do not create a report during configuration. Do not stage, commit, push, or merge configuration unless separately authorized. Before clone-based scheduling, require the finalized configuration to be committed and reachable from the cloned branch.
