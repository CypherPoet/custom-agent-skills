# 🤝 Handoff: De-duplicate shared maintainer skills across the public + private repos

> 🎯 **Next Action**: Byte-diff the three shared maintainer skills (`catalog-refresh`, `marketplace-sync-check`, `marketplace-publish`) between `custom-agent-skills` (public) and `private-custom-agent-skills` (private) to map exactly what's identical vs repo-specific, then choose a shared-source mechanism (git submodule vs a "maintainer-toolkit" plugin vs synced-copy-with-a-check).

## 🧾 Session Metadata
- Created: 2026-06-06T00:14:25Z
- Branch: main
- Repo: git@github.com:CypherPoet/custom-agent-skills.git

### Recent Commits (for context)
  - 04bd38b Merge pull request #49 from CypherPoet/skill/catalog-refresh
  - 1a70c5d ✨ Add catalog-refresh skill to regenerate docs/CATALOG.md
  - 084b30e Merge pull request #48 from CypherPoet/skill/sync-check-catalog-audit
  - 1c423ae Merge pull request #47 from CypherPoet/docs/sync-catalog-app-store-connect-kit
  - 3afc599 ✨ Extend marketplace-sync-check to audit docs/CATALOG.md

## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

> This is the first handoff for this task.

## 📚 Source Artifacts

The canonical record for this work. Link by path or URL; do not restate their content elsewhere.

- **PRD / spec**: none
- **Session plan**: none
- **ADRs / design docs**: none
- **Issues / tickets**:
  - Parallel catalog-automation work (open): https://github.com/CypherPoet/private-custom-agent-skills/pull/14 — "Have marketplace-publish regenerate the catalog's README table". The dedup design must account for this; it touches the same maintainer-skill surface.
- **Source PR**: the work being de-duplicated shipped in —
  - Public: [#47](https://github.com/CypherPoet/custom-agent-skills/pull/47), [#48](https://github.com/CypherPoet/custom-agent-skills/pull/48), [#49](https://github.com/CypherPoet/custom-agent-skills/pull/49) (all merged)
  - Private: [#15](https://github.com/CypherPoet/private-custom-agent-skills/pull/15) (merged) — its PR description has the dedup trade-off write-up that motivated this handoff.
- **Other**:
  - Public repo: https://github.com/CypherPoet/custom-agent-skills
  - Private repo: https://github.com/CypherPoet/private-custom-agent-skills

## 📍 Current State Summary

The catalog tooling is built and live in both repos: `catalog-refresh` (regenerates `docs/CATALOG.md` from the plugin manifests via a bundled stdlib-Python script) and a `marketplace-sync-check` that now audits both the published marketplace AND `docs/CATALOG.md`. It was authored in the public repo, then hand-ported into the private repo. As a result, three maintainer skills now exist as **hand-synced copies** across the two repos, with no mechanism keeping them in sync — the duplication the user now wants to eliminate. Nothing is broken; this is a maintainability/DRY task, not a bug fix.

## 💡 Important Context

The skill sets are **overlapping, not identical** — any mechanism must handle "shared core + per-repo extras," not a blanket mirror:

- **Shared (duplicated) — the dedup target:** `catalog-refresh`, `marketplace-sync-check`, `marketplace-publish`.
- **Public-only:** `dependency-tag-check`.
- **Private-only:** `handoff` (a repo-local skill, distinct from the `cypherpoet-agent-tooling:session-handoff` plugin skill).

The duplicated skills are **not byte-identical** — they carry repo-specific deltas that a naive copy would clobber:

- `marketplace-sync-check`: marketplace name (`cypherpoet-toolchest` vs `cypherpoet-toolchest-private`); the **public** version compares `name`+`description`+`homepage` (with a homepage-fallback paragraph), the **private** version compares `name`+`description` only.
- `catalog-refresh` `SKILL.md`: one marketplace-name reference (`cypherpoet-toolchest` vs `cypherpoet-toolchest-private`).
- `marketplace-publish`: repo-specific marketplace names throughout.
- The bundled script `catalog-refresh/scripts/refresh_catalog.py` is the one piece that is **fully generic** (repo-agnostic, finds root via git) — it's identical in both repos and the cleanest thing to share. The repo-specific bits all live in `SKILL.md` prose.

**Known divergence introduced this session (small, intentional):** the **private** `marketplace-sync-check` points its `docs/CATALOG.md` hand-off at the `catalog-refresh` skill; the **public** one still says "a plain docs edit" (public #48 shipped before #49 existed). Realigning the public hand-off to mention `catalog-refresh` is a tiny follow-up that should fold into this dedup work.

## 🚧 Pending Work

### Immediate Next Steps

1. Diff the three shared skills across both repos (clone both, `diff -ru` the `.claude/skills/{catalog-refresh,marketplace-sync-check,marketplace-publish}` trees) to quantify shared-vs-repo-specific lines precisely.
2. Decide the mechanism. Candidates and the key question for each:
   - **(a) git submodule** holding the shared skills — does Claude Code discover skills under a submodule-mounted `.claude/skills/<name>/`? How do repo-specific `SKILL.md` deltas get layered on top (the submodule can't hold two marketplace names)?
   - **(b) a "maintainer-toolkit" plugin** both repos install — but these are *maintainer* skills used while developing the repos, not consumer-facing; confirm they'd be available in the dev environment without being published to end users, and how per-repo parameters (marketplace name) are supplied.
   - **(c) synced copy with a drift check** — keep copies but add a check (script/CI/another maintainer skill) that fails when they diverge. Lowest mechanism cost; doesn't actually dedupe.
3. Implement the chosen approach in both repos (PR per repo).
4. Fold in the divergence fix: make the **public** `marketplace-sync-check` hand-off point at `catalog-refresh` too.
5. Reconcile with private PR #14 (it's editing the same maintainer-skill surface — coordinate or rebase).

### Blockers / Open Questions

- [ ] Which mechanism? Needs a decision (the core of this task).
- [ ] Should the generic `refresh_catalog.py` be the *only* shared artifact (simplest), or should the full skills be shared with parameterized `SKILL.md`? Sharing just the script removes most of the duplication risk (it's the complex part) at far lower mechanism cost.
- [ ] Does private PR #14 land before or after this dedup? It may change `marketplace-publish` in the private repo, widening the gap mid-effort.

### Deferred Items

- none — the divergence fix and PR #14 reconciliation are folded into Immediate Next Steps above, not parked.

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- **Do NOT naive-copy/symlink identical files across repos** — the repo-specific deltas above (marketplace names, the public-only homepage comparison) will be silently clobbered. The shared core must be parameterized or split from the per-repo prose.
- **Skill discovery constraint:** Claude Code discovers repo-local skills at `.claude/skills/<name>/SKILL.md`. Whatever mechanism is chosen must land valid `SKILL.md` files at that path in each repo (submodule mount point, plugin install location, or generated copy) — otherwise the skills stop being invocable.
- **Private repo has a PostToolUse hook** validating every `SKILL.md` write/edit (checks YAML frontmatter has `name:` + `description:`). A generated/synced `SKILL.md` must keep valid frontmatter.
- **YAML frontmatter landmine:** avoid a bare `: ` (colon-space) inside an unquoted `description:` — it parses as a nested mapping and breaks the skill. This exact bug existed in the private `marketplace-sync-check` and was fixed this session (changed `READ-ONLY: it` → `READ-ONLY — it`). Any shared/parameterized description must stay valid YAML.
- **`dependency-tag-check` is public-only and `handoff` is private-only** — don't assume the two `.claude/skills/` dirs should become identical.

### 🧰 Skills to Use

- `plugin-dev:plugin-structure` — **when:** evaluating option (b), the "maintainer-toolkit" plugin. **why:** authoritative on plugin layout, how skills are packaged, and how Claude Code discovers/installs them.
- `plugin-dev:skill-development` — **when:** restructuring the skills for sharing/parameterization. **why:** skill structure + progressive-disclosure conventions so the split stays idiomatic.
- `marketplace-sync-check` (+ `catalog-refresh`) — **when:** after implementing, in EACH repo. **why:** confirm the deduped skills still run and the catalog/marketplace stay in sync (regression check).

## 🧠 Codebase Understanding

### Architecture Overview

Both repos are the same shape: `plugins/<name>/` (themed Claude Code plugins published via a marketplace), `docs/CATALOG.md` (local cross-plugin index), `docs/PLUGIN-CONVENTIONS.md` (conventions), and `.claude/skills/` (repo-local maintainer tooling — NOT published plugins). The maintainer skills run on local `gh`/`git` (no CI, no tokens). The conventions and the audit/actuator split (`marketplace-sync-check` reports; `catalog-refresh`/`marketplace-publish` act) are documented in each repo's `CLAUDE.md` and `docs/PLUGIN-CONVENTIONS.md`.

### Critical Files

| File (both repos unless noted) | Purpose | Relevance |
|------|---------|-----------|
| `.claude/skills/catalog-refresh/scripts/refresh_catalog.py` | Regenerates `docs/CATALOG.md` table from manifests | **Fully generic / identical in both repos — the best single thing to share.** |
| `.claude/skills/catalog-refresh/SKILL.md` | catalog-refresh docs | Repo-specific: 1 marketplace-name token. |
| `.claude/skills/marketplace-sync-check/SKILL.md` | Drift auditor | Repo-specific: marketplace name; public compares homepage, private does not. Holds the intentional divergence (CATALOG hand-off wording). |
| `.claude/skills/marketplace-publish/SKILL.md` | Publish actuator | Repo-specific marketplace names. Also the target of private PR #14. |
| `.claude/skills/dependency-tag-check/` | Tag-coverage audit | **Public-only** — don't expect it in private. |
| `docs/PLUGIN-CONVENTIONS.md` → "Top-Level Catalog" | Catalog refresh rule | Both repos now point at `catalog-refresh` here. |

### Key Patterns Discovered

- Maintainer skills here are written as **plain procedures** (prose + `gh`/`jq`), except `dependency-tag-check` and `catalog-refresh`, which bundle a **stdlib-only Python script** under `scripts/` and have the SKILL.md say "run it, relay output, don't reimplement." That script-bundling pattern is the precedent for sharing logic.
- Manual-only maintainer skills set `disable-model-invocation: true` (publish, dependency-tag-check, catalog-refresh). Read-only auditors stay model-invocable (sync-check).
- Commit style: gitmoji. Public repo uses **merge commits** for PRs; private repo uses **squash** (commit title `… (#N)`).

## 🏁 Work Completed

### Tasks Finished

- [x] Public: shipped `catalog-refresh` + extended `marketplace-sync-check` to audit `docs/CATALOG.md` (PRs #47/#48/#49, merged). See PRs for diffs.
- [x] Private: ported both, fixed a latent frontmatter YAML bug, wired docs (PR #15, merged).
- [x] This handoff opened to carry the dedup follow-up.

### Files Modified

- none in this working tree — all the above work is already merged on `main` in both repos. This session's only working-tree change is this handoff file.

### Decisions Made

- **Ported via copy + adapt, not a shared mechanism (deferred dedup).** — At porting time, a submodule/plugin was overkill for two repos; copying the generic script + adapting the SKILL.md prose was faster and lower-risk. The user has now flagged the resulting duplication as a real concern → this handoff. Rationale + trade-offs are in private PR #15's description (linked in Source Artifacts).
- **Pointed the private sync-check hand-off at `catalog-refresh`; left public as-is.** — The private port shipped alongside `catalog-refresh`, so pointing at it was coherent there; public #48 predated #49. Accepted the small divergence rather than expanding scope; flagged as a fold-in for this task.

## 🌐 Environment State

### Tools/Services Used

- `gh` CLI on local credentials (account: CypherPoet), `git`, `python3` (stdlib only). No CI, no tokens.

### Active Processes

- none

### Environment Variables

- none
