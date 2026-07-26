---
name: skill-fact-check
description: >
  Re-check this repo's skills' time-sensitive facts (OS/SDK versions, device
  specs, URLs, API/CLI syntax) against primary sources and open a PR with cited,
  high-confidence corrections. Use when running or configuring the scheduled
  fact-check routine, or to manually fact-check the repo's skills. One subagent
  per skill; sourced edits only; obeys repo conventions. Not for general web
  fact-checking or non-skill content.
---

# 🔍 Skill fact-check

The complete, self-contained procedure for keeping this repo family's skills factually current. It runs two ways:

- **As a scheduled [routine](https://code.claude.com/docs/en/routines)** (the primary use) — a cloud session whose entire prompt is:
  > Find the `skill-fact-check` skill in the cloned `custom-agent-skills` repo and execute it against every cloned repo.
- **Manually** — invoke this skill inside any repo in the family to fact-check that repo's skills on demand.

It assumes only `git`, the `gh` CLI, built-in `WebSearch`/`WebFetch`, optionally a **Firecrawl** connector, and the `Task` tool for subagents. It does **not** rely on any installed plugin being active in the cloud — the routine reads this file from the cloned `custom-agent-skills` repo by path, so it works off committed source alone.

## Execution context (one skill, every cloned repo)

This skill's source lives only in `custom-agent-skills` (it ships in `cypherpoet-marketplace-kit`). A routine clones **all** its attached repos into one session — typically `custom-agent-skills` **and** `private-custom-agent-skills`. So:

1. Read this procedure once, from the `custom-agent-skills` clone.
2. Run Steps 1–8 **once per cloned repo**, each time with the working directory set to that repo's clone, so every relative path (`plugins/…`, the manifest) resolves within the repo being checked.
3. Each repo carries its **own** manifest (tiers reference that repo's unit IDs) and gets its **own** branch and PR. A repo with no findings gets no PR.

The private repo has no copy of this procedure — that's intentional. It's fact-checked because the routine clones it alongside the public repo; don't run a private-only routine without also cloning `custom-agent-skills`.

**Bundled files** (`scripts/`, `references/`) sit next to this file in the `custom-agent-skills` clone, and they read whichever repo the working directory points at — so a script path is always the public checkout's, while the cwd is the repo under check.

## What this guarantees

Each run, re-check the time-sensitive factual claims in a repo's skills against primary sources, then open **one pull request** carrying:

- **Corrections** applied directly — any fix the cited evidence genuinely establishes, from a one-token version bump to a multi-site API rename or a note whose logic was inverted.
- **Flags** for anything the evidence leaves uncertain or ambiguous, or that is an editorial judgment call rather than a factual one — surfaced in the PR body **with proposed wording**, never silently edited.

**Git + PR review is the quality gate.** Everything below exists to make that review easy, not to substitute for it. Three constraints hold it up:

- **The reviewer test.** The standard for applying a correction is *"would a competent reviewer, shown this evidence, make this edit?"* — not a mechanical size or format rule. Every applied edit carries a `source_url` and a `source_quote` so that reviewer can check it without redoing the research. Evidence too thin to pass the test ⇒ flag it with proposed wording; don't edit.
- **Fact corrections only.** Fix what the evidence shows is wrong and nothing more. No stylistic edits, no restructuring, no scope creep beyond what the fact requires.
- **PR-only.** Work on the stable branch `claude/skill-fact-check`; open or update exactly one PR per repo; never commit to `main` and never push outside a `claude/`-prefixed branch. The single carve-out is a PR whose diff is *nothing but* re-stamped datelines — no guidance changed, so there is nothing to review. [Step 8](#step-8--auto-merge-a-dateline-only-pr-per-repo) merges that one shape behind a scripted gate; every PR touching content waits for a human.

**Batches, not ceilings.** Research the due set most-overdue-first in waves of ~12 units per repo, ≤6 subagents concurrent, and keep launching waves until the set drains or the session genuinely runs short of budget. Anything deferred is listed in the PR and stays due next run — deferral is the fallback for real resource pressure, not the design.

## Scope & exclusions

A **unit** is one skill: its `SKILL.md`, the sibling `references/**`, and its `evals/**`. Its `unit_id` is `<plugin>/<skill>`, its directory is the `SKILL.md`'s parent, and its plugin manifest is `plugins/<plugin>/.claude-plugin/plugin.json`.

Fact-check all three surfaces. References hold roughly 80% of volatile facts; evals encode the same version-sensitive premises as the docs and go stale with them, leaving an eval that contradicts the skill it grades — so they're corrected under the same evidence gates as any other file, with the reading caveats in [`references/subagent-procedure.md`](references/subagent-procedure.md) so a fixture's scenario data isn't mistaken for a stale fact.

Three exclusions, each for its own reason:

- `**/*-workspace/` is regenerable scratch — never read, never edited, never counted.
- **Evals are not units.** A fixture `SKILL.md` under `evals/` is test data, not a skill to schedule.
- **Eval dates are not datelines.** A date inside a fixture is scenario data, not a record of when this unit was verified; counting one would falsely freshen the unit.

The bundled scripts enforce all three.

## Inputs

- **Manifest:** `docs/automated-routines/skill-fact-check-manifest.json` in the repo being checked — maps units to a volatility tier (`weekly`, `monthly`, `never`) and carries the `acknowledged` list. Shape, tiering guidance, and acknowledgment semantics: [`references/manifest.md`](references/manifest.md).
- **Datelines** (the freshness cursor) — the explicit verification/sync label saying when a unit's facts were last checked. [`scripts/datelines.py`](scripts/datelines.py) is the single source of truth for which forms count; it recognizes `**Verified:** <date>` (the canonical marker this routine writes), `Last synced: <date>`, the parenthetical audit-baseline date, inline `verified <date>`, and `as of <month>`. Bare content dates (`released …`, `Created: …`) are deliberately excluded — treating one as a dateline would mark a stale unit fresh forever.
- **Source markers:** `**Source:**` and `**Source of truth:**` — the URL a file declares as the authority for a specific fact. Check this first.
- **Declared source set:** a `## Primary Sources` section at the end of a unit's `SKILL.md` — the skill's own canonical verification sources, one bullet per source saying what it's authoritative for. Prefer these over free-choice research; a placeholder ("None declared yet …") means fall back to vendor-primary sources per claim.
- **Change-signal leads:** an optional per-unit `Change-Signal Sources` block listing secondary leads (e.g. a maintainer's blog) to scan for *what* may have drifted. Leads only — confirm against a primary source, never cite one in an edit.

## Step 1 — Compute the due set

A unit is **due** when its tier's interval has elapsed since its newest dateline. This is age-gated, not run-gated: the dateline *is* the cursor, so a unit skipped by a crash or a deferral stays due next time and the schedule self-heals.

With the working directory set to the repo being checked:

```bash
python3 scripts/compute_due_set.py
```

One tab-separated row per due unit, most-overdue first (`age_days  unit_id  unit_dir  tier  last_dateline`), then `#`-prefixed notes. Don't eyeball dates — the script is the authority.

`# DRIFT` lines are manifest hygiene, not fact findings: never edit the manifest for them. List them in the PR body's flagged section so a human re-tiers deliberately.

## Step 2 — Idempotency check (per repo)

One stable branch, one long-lived PR, reused every run — so repeated runs converge instead of piling up duplicate PRs.

```bash
gh pr list --state open   --head claude/skill-fact-check --json number -q '.[0].number'
gh pr list --state merged --head claude/skill-fact-check --json number -q '.[0].number'
```

- **Open PR exists →** reuse it. `git fetch origin`, recreate the branch from `origin/main` (`git switch -C claude/skill-fact-check origin/main`), re-apply this run's net findings, `git push --force-with-lease`, and **rewrite** the PR body to the current state (`gh pr edit <n> --body-file -`). Do not append, and do not open a second PR.
- **No open PR, last one merged (or none) →** start fresh from `origin/main`. The merged work is already in `main` and its datelines advanced, so fewer units are due.
- **A run producing no net change** vs. what's already on the branch → push nothing, leave the PR untouched, log "no new findings; PR #N still current."

## Step 3 — Fan out (one subagent per due unit)

Deep-researching a wave of units in the orchestrator's own context would overflow it. Spawn **one `Task` subagent per due unit**, ≤6 concurrent, wave after wave until the due set drains. The orchestrator never reads skill bodies — subagents read and research, and return compact JSON. Subagents **propose**; they cannot edit files, which is what makes an unsourced fix structurally unable to land.

Give each subagent the unit's `unit_dir` and `plugin_dir`, the contract below, and the contents of [`references/subagent-procedure.md`](references/subagent-procedure.md) **pasted verbatim** — subagents don't inherit this file.

```json
{
  "unit_id": "cypherpoet-apple-app-store-screenshots/apple-app-store-screenshots",
  "plugin_dir": "plugins/cypherpoet-apple-app-store-screenshots",
  "claims": [
    {
      "file": "plugins/.../references/device-specifications.md",
      "claim_type": "SPEC",
      "locator": "exact unique substring of the current text to find it",
      "old": "1260×2736",
      "new": "1290×2796",
      "status": "CORRECT",
      "source_url": "https://developer.apple.com/help/app-store-connect/.../screenshot-specifications",
      "source_quote": "verbatim passage from the source that establishes the correction",
      "confidence": "high",
      "note": ""
    }
  ],
  "checked_count": 14,
  "newest_dateline": "2026-05-30"
}
```

`status` is one of: `CORRECT` (current text is wrong; `new` ≠ `old`; cite the fix), `CONFIRMED_UNCHANGED` (verified correct; `new` == `old`), `FLAG_UNCERTAIN`, `FLAG_AMBIGUOUS`, `FLAG_DESCRIPTION_FRONTMATTER`, or `ERROR` (couldn't verify). `locator` must be an **exact, unique substring** of the live file — not a line number, those drift. A fix touching several sites (an API rename used throughout a file) is one *finding* returned as multiple `CORRECT` claims, one per site, sharing the citation.

## Step 4 — Reduce & apply (orchestrator)

Collect the subagents' JSON. The orchestrator performs every mutation — editing authority is centralized so the guards live in one place, and because subagents research while the orchestrator *reviews*. Read each proposed correction the way a PR reviewer would.

Apply a `CORRECT` claim, in most-overdue-unit order, when:

- The cited `source_url` is a primary source and the `source_quote` genuinely establishes both that the old text is wrong and that `new` is right. Spot-check anything surprising or load-bearing — fetch the source, resolve the URL yourself. The subagent did the research; the orchestrator owns the edit.
- `confidence == "high"`. Anything lower ships as a flag with its evidence attached.
- It's a fact correction within scope, not a stylistic rewrite wearing a correction's clothes.

**Size is not a gate.** A sourced multi-site rename or corrected snippet applies just like a token swap — apply each site with an exact-substring `Edit` using its `locator`. If one unit's corrections would dominate the PR, give them their own commit so the diff reviews cleanly; don't downgrade them to flags for being numerous. Group edits by plugin and track which plugins were touched, for Step 5.

**Suppress acknowledged flags.** Build the manifest's `acknowledged` list once per repo, then reduce every `FLAG_*` claim against it. A flag is acknowledged when a live entry shares its `unit_id` and the entry's `locator` is a substring of the flag's `locator` (or, if that's empty, its `old`/`note`). For a match:

- `recheck_after` is `"never"` or a future date → drop it from the active `🚩 Flagged` table, list it under `🔕 Known / acknowledged` instead, and exclude it from the flagged count.
- `recheck_after` has passed → **do not suppress**; keep it flagged and annotate `(acknowledgment expired <date> — re-confirm or renew)`.

Acknowledgments silence `FLAG_*` findings **only** — never a sourced `CORRECT`, never an unverifiable `ERROR`. The subagent still researches the fact every run, so a fact that quietly *changed* still surfaces: its `locator`/`old` shifts and stops matching.

## Step 5 — Version bumps

After editing a plugin's **shipped** content, bump that plugin's `.claude-plugin/plugin.json` `version` **once** — a plugin touched by two skills bumps once:

- **Applied content correction → MINOR bump** (`0.1.0 → 0.2.0`). Per `docs/PLUGIN-CONVENTIONS.md`, pre-1.0 the default bump for anything user-visible is MINOR, and a fact correction is user-visible.
- **Dateline-only re-stamp → no bump.** A date stamp isn't user-visible guidance, and `version` is the user-update cache key, so don't churn it. The committed date still advances the age-gate.
- **Eval-only correction → no bump.** `evals/` is stripped from vendored copies and never reaches an install, so bumping for it would push an update carrying nothing the user receives.

**Surfaces this routine leaves alone.** `version` is the only `plugin.json` field it may touch. `name`/`description`/`homepage` are the Claude catalog fields, and staying off them is what keeps every run clear of the marketplace catalog surface — so no run ever needs the `marketplace-publish` label: don't add it, and don't spend a step checking, since a version-only bump never counts as a catalog change. Component counts don't change either, so `docs/CATALOG.md` never needs refreshing. A `description:` in `SKILL.md` YAML frontmatter is likewise never edited: it is the skill's *triggering* signal, judged by the model at routing time, so changing it changes **when the skill fires**. That's a behavior change wearing a fact-fix's clothes, and it's outside this routine's remit even when the text is genuinely wrong — hence `FLAG_DESCRIPTION_FRONTMATTER`.

## Step 6 — Datelines

- **`CONFIRMED_UNCHANGED`** section carrying a recognized dateline → **re-stamp** it to today, in whichever marker form the unit already uses. This is what lets a re-verified unit go quiet until its next interval; without it the unit re-researches every run forever.
- **No recognized dateline anywhere in the unit** → stamp `**Verified:** <today>`, but only when the unit was actually verified this run (≥1 `CONFIRMED_UNCHANGED` or `CORRECT`). Place it right after a `**Source:**`/`**Source of truth:**` marker if one exists, otherwise directly under the unit's `SKILL.md` H1. This converges every unit on the canonical marker, so the age-gate stops depending on legacy dialects. (`never`-tier units are never researched and so never need one.)
- **`ERROR`** → **never** re-stamp. Leaving the date stale correctly keeps the unit due.
- **`CORRECT`** → re-stamp the section's dateline as part of the same edit; the correction already bumps the version.

Re-stamping never bumps a version, and a dateline belongs in the unit's own docs — never write one into an eval fixture.

## Step 7 — Open or update the PR (per repo)

Open a PR **only if** the repo had ≥1 applied correction, ≥1 new flag, or ≥1 dateline change worth shipping — then take it through [Step 8](#step-8--auto-merge-a-dateline-only-pr-per-repo).

Commit per plugin, and use the commit, title, and body formats in [`references/pr-format.md`](references/pr-format.md). Branch `claude/skill-fact-check`; each cloned repo gets its own branch and PR via `gh pr create --repo <owner>/<repo>`.

Per-plugin commits plus age-gating are what make a partial run safe: if the orchestrator dies mid-run, finished plugins persist and un-restamped units simply stay due.

## Step 8 — Auto-merge a dateline-only PR (per repo)

A run that corrects nothing still opens a PR, because re-stamping datelines is what lets a re-verified unit go quiet ([Step 6](#step-6--datelines)). Nothing in it is reviewable — [Step 5](#step-5--version-bumps) already treats a dateline as carrying no user-visible guidance — and left sitting it stalls the next run into [Step 2](#step-2--idempotency-check-per-repo)'s "reuse the open PR" path. Merge exactly that shape, nothing else.

Merge only when **all** of these hold; otherwise leave the PR open and report which one blocked it:

- This run applied **0** `CORRECT` claims, raised **0** new (unsuppressed) `FLAG_*`, and hit **0** `ERROR`s. An unverifiable fact is precisely what a human should see, so one `ERROR` disqualifies the PR even when the diff looks clean.
- `python3 scripts/check_dateline_only.py` exits 0 on the pushed branch. Run it; don't eyeball the diff.
- `gh pr checks <n> --repo <owner>/<repo> --watch --fail-fast` exits 0, and `gh pr view <n> --repo <owner>/<repo> --json mergeable,mergeStateStatus,isDraft` reports `MERGEABLE` / `CLEAN` / not draft. Neither repo enables GitHub's own auto-merge, so `gh pr merge --auto` is unavailable — wait on the checks here instead.

The script is a whitelist and it fails closed: a correction, a version bump, an out-of-scope path, a deleted dateline, or newly-added prose all block the merge. Then:

```bash
gh pr merge <n> --repo <owner>/<repo> --squash --delete-branch
```

`--delete-branch` can exit non-zero after the merge already succeeded — confirm with `gh pr view <n> --json state` (expect `MERGED`) rather than trusting the exit code. Report it as `"dateline-only, auto-merged #N"` so a merge never reads as a skip. A blocked gate is **not** a run failure.
