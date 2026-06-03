# 🤝 Handoff: Finish the `cypherpoet-app-store-connect-kit` plugin + skill

> 🎯 **Next Action**: Run skill-creator's trigger/description optimization on `plugins/cypherpoet-app-store-connect-kit/skills/app-store-connect-submission` — draft the ~20 trigger eval queries (should/should-not lists in Immediate Next Steps #1), review them via skill-creator's `assets/eval_review.html`, then `python -m scripts.run_loop --eval-set <path> --skill-path <skill-path> --model <this session's model id> --max-iterations 5 --verbose` and apply the returned `best_description` to the SKILL.md frontmatter.

## 🧾 Session Metadata
- Created: 2026-06-03T00:44:01Z
- Branch: skill/app-store-connect-submission
- Repo: git@github.com:CypherPoet/custom-agent-skills.git
- Worktree: `/Users/ethan/Projects/Utilities/Agent-Skills/custom-agent-skills--asc-submission-skill` (off `origin/main`)

### Recent Commits (for context)
  - ff41766 Merge pull request #41 from CypherPoet/claude/inspiring-rosalind-b7204b
  - 5854067 📝 List plugin dependencies in their READMEs + document the convention
  - a54b0f4 ♻️ Replace npx semver with a bundled stdlib-Python audit script
  - aba00df 🔒 Make marketplace-publish manual-only (disable-model-invocation)
  - ddd6627 Merge pull request #43 from CypherPoet/feat/session-handoff-improvements

## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

> This is the first handoff for this task.

## 📚 Source Artifacts

- **PRD / spec**: none (no formal spec — the skill's own `SKILL.md` + `README.md` are the design record)
- **Session plan**: none
- **ADRs / design docs**: `plugins/cypherpoet-app-store-connect-kit/README.md` (scope + sibling hand-offs) and the skill `SKILL.md` (what it owns vs defers)
- **Issues / tickets**: none
- **Source PR**: the plugin PR for branch `skill/app-store-connect-submission` on `CypherPoet/custom-agent-skills` (opened at the end of the authoring session — find via `gh pr list`)
- **Other**:
  - Distilled from `…/Tetris-Age-of-Empires-Fusion-Apple-Platforms-App/.claude/worktrees/funny-payne-7e5be2/docs/shipping/APP_STORE_SUBMISSION.md` (itself in open PR #8 on `CypherPoet/TetraEmpire`)
  - Sibling skills it complements: `plugins/cypherpoet-mobile-dev/skills/apple-app-store-best-practices`, `plugins/cypherpoet-apple-app-store-screenshots/…/apple-app-store-screenshots`, and the `storekit` skill
  - skill-creator (for steps below): `~/.claude/plugins/cache/claude-plugins-official/skill-creator/<ver>/skills/skill-creator`
  - Marketplace repo (for step 3): `~/Projects/Utilities/Agent-Skills/cypherpoet-toolchest`

## 📍 Current State Summary

A new plugin `cypherpoet-app-store-connect-kit` with one skill, `app-store-connect-submission`, is **drafted and validated** on branch `skill/app-store-connect-submission`. Files: `.claude-plugin/plugin.json`, `README.md`, `skills/app-store-connect-submission/SKILL.md` (170 lines) + `references/{walkthrough,build-and-delivery,testing-purchases}.md`. Validation passed (valid JSON, all references linked, walkthrough TOC anchors resolve). It is **not yet** trigger-optimized and **not yet** registered in the marketplace, so it isn't installable yet. The plugin PR carries the draft + this handoff.

## 💡 Important Context

- **The scope is deliberately carved to NOT overlap three sibling skills**, and that is load-bearing: `apple-app-store-best-practices` owns review-compliance/ASO, `apple-app-store-screenshots` owns screenshot specs, `storekit` owns IAP code. This skill owns only the *operational* submission workflow + console navigation + build delivery + sandbox + dated gotchas. When optimizing the description (next step), **preserve the should-NOT-trigger near-misses** so it doesn't start stealing the siblings' triggers — that's the whole point of the carve-out.
- **Every Apple-UI fact in the skill is dated ("as of 2026-06; trust the screen")** on purpose — ASC/Xcode UIs drift. Keep that framing on any edits.
- **All app-specific Tetra Empire details were stripped and generalized** (placeholders like `com.you.YourApp`). Keep it general — this is a reusable handbook, not Tetra's doc.
- **The marketplace manifest is a SEPARATE repo** (`cypherpoet-toolchest`), not `custom-agent-skills`. Registration (step 3) is a second PR in that other repo. Note `aba00df` made "marketplace-publish manual-only" — check that repo's publish tooling/convention before adding the entry.
- Work is in a **worktree off `origin/main`**; commit on the branch and ship via PR — don't push `main` directly.

## 🚧 Pending Work

### Immediate Next Steps

1. **Trigger/description optimization** (skill-creator). Draft ~20 realistic trigger eval queries:
   - **should-trigger**: "how do I submit my app to the app store", "set up an xcode cloud archive workflow", "sandbox test my in-app purchase", "got error 90474 uploading my build", "xcode cloud 'manage workflows' is greyed out", "where do I put the privacy policy url in app store connect", "attach my IAP to the version".
   - **should-NOT-trigger** (belong to siblings): "audit my app for app review compliance / will it pass review" → best-practices; "what size should app store screenshots be / 1320x2868" → screenshots; "write my StoreKit purchase and restore code" → storekit.
   Review via skill-creator `assets/eval_review.html`, then run `run_loop.py` (command in 🎯 Next Action), apply `best_description` to `SKILL.md`.
2. *(Optional, likely SKIP)* skill-creator output eval loop — subjective knowledge/handbook skill; hard assertions add little. Reading the draft is the better check.
3. **Marketplace registration** — add a `cypherpoet-app-store-connect-kit` entry to the `cypherpoet-toolchest` marketplace manifest (separate repo, separate PR), mirroring how `cypherpoet-mobile-dev` / `cypherpoet-apple-app-store-screenshots` are listed. Required for it to be installable.
4. *(Optional)* package a `.skill` via skill-creator `python -m scripts.package_skill <skill-folder>`.
5. **Merge the plugin PR** once happy; then the marketplace PR.

### Blockers / Open Questions

- [ ] Optional: should the sibling skills' descriptions be updated to cross-reference this one (e.g. best-practices "for the submission *workflow*, see app-store-connect-submission")? Improves discoverability; not required.

### Deferred Items

- Cross-referencing the sibling skills' descriptions (above).
- Packaging a distributable `.skill` artifact (step 4).

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- The Bash tool's **cwd resets between calls** (it kept snapping back to the Tetra repo this session) — run scripts with explicit absolute paths / set cwd each call.
- skill-creator's `run_loop.py` triggers Claude via `claude -p` — pass the **model id powering your session** so the triggering test matches reality.
- **Don't** add the marketplace entry to `custom-agent-skills` — it goes in the `cypherpoet-toolchest` repo.
- **Don't** let description optimization broaden triggers into the siblings' turf (see Important Context).

### 🧰 Skills to Use

- `skill-creator:skill-creator` — **when:** running the trigger/description optimization (step 1) and optional packaging (step 4). **why:** it owns `scripts/run_loop.py` (description optimization) and `scripts/package_skill.py`.

## 🧠 Codebase Understanding

### Architecture Overview

Standard Claude Code plugin layout (see `README.md`): `plugins/<plugin>/.claude-plugin/plugin.json` + `skills/<skill>/SKILL.md` (+ `references/`). Progressive disclosure: SKILL.md is the overview/flow/glossary/troubleshooting (<500 lines); depth lives in `references/`. Mirrors the sibling `apple-app-store-best-practices` conventions.

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `plugins/cypherpoet-app-store-connect-kit/.claude-plugin/plugin.json` | Plugin manifest (name `cypherpoet-app-store-connect-kit`, v0.1.0) | Must stay in sync with the marketplace entry (step 3) |
| `…/skills/app-store-connect-submission/SKILL.md` | The skill — `description` is what step 1 optimizes | Don't broaden triggers into sibling turf |
| `…/references/{walkthrough,build-and-delivery,testing-purchases}.md` | Deep content | Keep facts dated + generalized |
| `README.md` | Scope + sibling hand-off table | The design rationale |

### Key Patterns Discovered

- `cypherpoet-` plugin-name prefix; MIT; author CypherPoet; repo `github.com/CypherPoet/custom-agent-skills`.
- Every Apple-UI fact is dated and ends with "trust the screen."
- Description explicitly defers the three adjacent concerns to siblings — keep that.

## 🏁 Work Completed

### Tasks Finished

- [x] Scaffolded the new plugin `cypherpoet-app-store-connect-kit` and authored the `app-store-connect-submission` skill (SKILL.md + 3 references), generalized from the Tetra submission doc.
- [x] Validated structure (JSON, references, anchors); renamed plugin from `cypherpoet-app-store-connect` → `…-kit` per request.

### Files Modified

- New: the 6 plugin files above + this handoff.

### Decisions Made

- **New standalone plugin rather than a skill inside `cypherpoet-mobile-dev`** — keeps `mobile-dev` focused on review/compliance and gives the submission handbook room to grow (TestFlight, pricing, etc.). (User chose this over folding into mobile-dev.)
- **Scope carved to complement, not duplicate, the three sibling skills** — see Important Context.
- **All facts dated + app-agnostic** — the source was one app's doc; the skill must serve any app and survive Apple UI drift.

## 🌐 Environment State

### Tools/Services Used

- git worktree (`custom-agent-skills--asc-submission-skill`), skill-creator, session-handoff.

### Active Processes

- none

### Environment Variables

- none

---

**Security Reminder**: Before finalizing, run `validate_handoff.py` to check for accidental secret exposure.
