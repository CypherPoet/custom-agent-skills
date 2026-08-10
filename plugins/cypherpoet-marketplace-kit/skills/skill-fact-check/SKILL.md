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
- **PR-only.** Work on the stable branch `claude/skill-fact-check`; open or update exactly one PR per repo; never commit to `main` and never push outside a `claude/`-prefixed branch.
  The single carve-out is a PR whose diff is *nothing but* re-stamped datelines — no guidance changed, so there is nothing to review. [Step 8](#step-8--auto-merge-a-dateline-only-pr-per-repo) merges that one shape behind a scripted gate; every PR touching content waits for a human.

**Batches, not ceilings.** Research the due set most-overdue-first in waves of ~12 units per repo, ≤6 subagents concurrent, and keep launching waves until the set drains or the session genuinely runs short of budget. Anything deferred is listed in the PR and stays due next run — deferral is the fallback for real resource pressure, not the design.

### Never

Every one of these is a hard stop, not a judgment call. The linked step says why.

| Never | Instead |
|---|---|
| Commit to `main`, or push outside a `claude/`-prefixed branch | Open a PR ([Step 7](#step-7--open-or-update-the-pr-per-repo)) |
| Open a second PR while one is open | Reuse the stable branch ([Step 2](#step-2--idempotency-check-per-repo)) |
| Apply an edit without cited primary-source evidence | Flag it with proposed wording ([Step 4](#step-4--reduce--apply-orchestrator)) |
| Edit a `description:` in `SKILL.md` frontmatter | `FLAG_DESCRIPTION_FRONTMATTER` ([Step 5](#step-5--version-bumps)) |
| Edit any `plugin.json` field but `version` | — ([Step 5](#step-5--version-bumps)) |
| Edit a vendored skill copy | Correct its source, then re-sync ([Step 5](#step-5--version-bumps)) |
| Edit anything under `*-workspace/`, or refresh `docs/CATALOG.md` | — ([Step 4](#step-4--reduce--apply-orchestrator)) |
| Add the `marketplace-publish` label, or spend a step checking for it | — ([Step 5](#step-5--version-bumps)) |
| Re-stamp a dateline for a claim it couldn't verify | Leave it stale so the unit stays due ([Step 6](#step-6--datelines)) |
| Write a dateline into an eval fixture | Stamp the unit's own docs ([Step 6](#step-6--datelines)) |
| Edit the manifest to silence a `# DRIFT` line | Report it for a human to re-tier ([Step 1](#step-1--compute-the-due-set)) |
| Let an `acknowledged` entry suppress a `CORRECT` or an `ERROR` | Suppress `FLAG_*` only ([Step 4](#step-4--reduce--apply-orchestrator)) |
| Merge a PR the gate did not pass, or that carries an unread flag | Leave it open and report the blocker ([Step 8](#step-8--auto-merge-a-dateline-only-pr-per-repo)) |

## Step 1 — Compute the due set

**Read [`references/scope-and-inputs.md`](references/scope-and-inputs.md) first.** It defines what a unit is, the three exclusions, and every input a run reads — the manifest, the dateline forms, source markers, declared sources, and change-signal leads. Steps 1 and 3 both depend on it.

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
- **A run producing no net change** vs. what's already on the branch → push nothing, leave the PR untouched, log "no new findings; PR #N still current." Then **still take that inherited PR through [Step 8](#step-8--auto-merge-a-dateline-only-pr-per-repo)** before moving on.

That last hand-off is what keeps a mergeable PR from stranding. Step 7 only reaches Step 8 when *this* run produced something to ship, so without it a dateline-only PR that Step 8 held once — a checks timeout, a transient hold — is never gated again: every later run re-derives the same re-stamps, finds no net change, and leaves it sitting. That is exactly the stall Step 8 exists to clear.

## Step 3 — Fan out (one subagent per due unit)

Deep-researching a wave of units in the orchestrator's own context would overflow it. Spawn **one `Task` subagent per due unit**, ≤6 concurrent, wave after wave until the due set drains.

- The orchestrator never reads skill bodies — subagents read and research, and return compact JSON.
- Subagents **propose**; they cannot edit files. That is what makes an unsourced fix structurally unable to land.

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

`status` is one of:

| Status | Means |
|---|---|
| `CORRECT` | The current text is wrong; `new` ≠ `old`; cite the fix |
| `CONFIRMED_UNCHANGED` | Verified correct; `new` == `old` |
| `FLAG_UNCERTAIN` · `FLAG_AMBIGUOUS` · `FLAG_DESCRIPTION_FRONTMATTER` | Needs a human |
| `ERROR` | Couldn't verify |

`locator` must be an **exact, unique substring** of the live file — not a line number, those drift. A fix touching several sites (an API rename used throughout a file) is one *finding* returned as multiple `CORRECT` claims, one per site, sharing the citation.

## Step 4 — Reduce & apply (orchestrator)

Collect the subagents' JSON. The orchestrator performs every mutation — editing authority is centralized so the guards live in one place, and because subagents research while the orchestrator *reviews*. Read each proposed correction the way a PR reviewer would.

Apply a `CORRECT` claim, in most-overdue-unit order, when:

- The cited `source_url` is a primary source and the `source_quote` genuinely establishes both that the old text is wrong and that `new` is right. Spot-check anything surprising or load-bearing — fetch the source, resolve the URL yourself. The subagent did the research; the orchestrator owns the edit.
- `confidence == "high"`. Anything lower ships as a flag with its evidence attached.
- It's a fact correction, not a stylistic rewrite wearing a correction's clothes.
- **The target is an editable surface.** Never apply an edit that lands on any of these — flag it instead:
  - a `description:` value in `SKILL.md` YAML frontmatter → `FLAG_DESCRIPTION_FRONTMATTER`
  - any `plugin.json` field other than `version`
  - anything under `*-workspace/`
  - a vendored skill copy — correct its authoritative source instead ([`references/manifest.md`](references/manifest.md#vendored-copies-are-always-never))

  [Step 5](#step-5--version-bumps) says why each surface is protected. The list belongs here too because this is where the orchestrator — the only actor that can write — decides.

**Size is not a gate.** A sourced multi-site rename or corrected snippet applies just like a token swap — never downgrade a correction to a flag for being numerous.

- Apply each site with an exact-substring `Edit` using its `locator`.
- If one unit's corrections would dominate the PR, give them their own commit so the diff reviews cleanly.
- Group edits by plugin, and track which plugins were touched — [Step 5](#step-5--version-bumps) needs that list.

**Suppress acknowledged flags.** Build the manifest's `acknowledged` list once per repo, then reduce every `FLAG_*` claim against it. A flag is acknowledged when a live entry shares its `unit_id` and the entry's `locator` is a substring of the flag's `locator` (or, if that's empty, its `old`/`note`). For a match:

- `recheck_after` is `"never"` or a future date → drop it from the active `🚩 Flagged` table, list it under `🔕 Known / acknowledged` instead, and exclude it from the flagged count.
- `recheck_after` has passed → **do not suppress**; keep it flagged and annotate `(acknowledgment expired <date> — re-confirm or renew)`.

Acknowledgments silence `FLAG_*` findings **only** — never a sourced `CORRECT`, never an unverifiable `ERROR`. The subagent still researches the fact every run, so a fact that quietly *changed* still surfaces: its `locator`/`old` shifts and stops matching.

## Step 5 — Version bumps

After editing a plugin's **shipped** content, bump every platform manifest that plugin supports to the same version — a plugin touched by two skills still bumps once:

- **Applied content correction → MINOR bump** (`0.1.0 → 0.2.0`). Per `docs/PLUGIN-CONVENTIONS.md`, pre-1.0 the default bump for anything user-visible is MINOR, and a fact correction is user-visible.
- **Dateline-only re-stamp → no bump.** A date stamp isn't user-visible guidance, and `version` is the user-update cache key, so don't churn it. The committed date still advances the age-gate.
- **Eval-only correction → no bump.** `evals/` is stripped from vendored copies and never reaches an install, so bumping for it would push an update carrying nothing the user receives.

### Then synchronize vendored copies

```bash
npm run sync
```

Run it **after the last edit and the last bump**, before committing. A corrected skill that is vendored into other plugins otherwise leaves every generated copy stale: `[vendor] out of sync: <copy> != <source>`.

The repository health suite runs that same check, so drift turns the PR's checks red. The sync is deterministic and touches only vendored targets, so re-running it when nothing changed is free.

### Surfaces this routine leaves alone

**`version` is the only `plugin.json` field it may touch.**

- `name` / `description` / `homepage` are the Claude catalog fields. Staying off them keeps every run clear of the marketplace catalog surface, so **no run ever needs the `marketplace-publish` label** — don't add it, and don't spend a step checking, since a version-only bump never counts as a catalog change.
- Component counts don't change either, so `docs/CATALOG.md` never needs refreshing.

**A `description:` in `SKILL.md` YAML frontmatter is never edited.**

It is the skill's *triggering* signal, judged by the model at routing time, so changing it changes **when the skill fires**. That's a behavior change wearing a fact-fix's clothes, and it's outside this routine's remit even when the text is genuinely wrong — hence `FLAG_DESCRIPTION_FRONTMATTER`.

**A vendored skill copy is never edited.**

Copies are generated. Correct the authoritative source and let the sync above propagate it; editing a copy directly gets the fix silently overwritten on the next sync. Every copy is tiered `never` so it is never researched in the first place — see [`references/manifest.md`](references/manifest.md#vendored-copies-are-always-never).

## Step 6 — Datelines

- **`CONFIRMED_UNCHANGED`** section carrying a recognized dateline → **re-stamp** it to today, in whichever marker form the unit already uses. This is what lets a re-verified unit go quiet until its next interval; without it the unit re-researches every run forever.
- **No recognized dateline anywhere in the unit** → stamp `**Verified:** <today>`, but only when the unit was actually verified this run (≥1 `CONFIRMED_UNCHANGED` or `CORRECT`). Place it right after a `**Source:**`/`**Source of truth:**` marker if one exists, otherwise directly under the unit's `SKILL.md` H1.
  This converges every unit on the canonical marker, so the age-gate stops depending on legacy dialects. (`never`-tier units are never researched and so never need one.)
- **`ERROR`** → **never** re-stamp. Leaving the date stale correctly keeps the unit due.
- **`CORRECT`** → re-stamp the section's dateline as part of the same edit; the correction already bumps the version.

Re-stamping never bumps a version, and a dateline belongs in the unit's own docs — never write one into an eval fixture.

**Labelled markers auto-merge; unlabelled cues hold.** `scripts/datelines.py` recognizes two kinds:

- **Labelled** — the date is introduced by an explicit verification/sync label: `**Verified:**`, `Last synced:`, the audit-baseline parenthetical.
- **Unlabelled** — the date reads as ordinary prose: inline `verified <date>`, `as of <month>`.

Both count toward freshness. Only labelled ones can be re-stamped unreviewed, because "requires macOS 15.4 as of 2026-03-01" is a fact, not a stamp, and no automated check can tell which you meant.

Re-stamp whichever form the unit already uses. A PR whose only change lands on an unlabelled cue just waits for a human — every unit in the family carries at least one labelled marker today, so this costs no auto-merges, and the second bullet above converges the rest on `**Verified:**` over time.

## Step 7 — Open or update the PR (per repo)

Open a PR **only if** the repo had ≥1 applied correction, ≥1 new flag, or ≥1 dateline change worth shipping — then take it through [Step 8](#step-8--auto-merge-a-dateline-only-pr-per-repo).

Commit per plugin, and use the commit, title, and body formats in [`references/pr-format.md`](references/pr-format.md). Branch `claude/skill-fact-check`; each cloned repo gets its own branch and PR via `gh pr create --repo <owner>/<repo>`.

Per-plugin commits plus age-gating are what make a partial run safe: if the orchestrator dies mid-run, finished plugins persist and un-restamped units simply stay due.

## Step 8 — Auto-merge a dateline-only PR (per repo)

A run that corrects nothing still opens a PR, because re-stamping datelines is what lets a re-verified unit go quiet ([Step 6](#step-6--datelines)). Merge exactly that shape, nothing else:

- Nothing in it is reviewable — [Step 5](#step-5--version-bumps) already treats a dateline as carrying no user-visible guidance.
- Left sitting, it stalls the next run into [Step 2](#step-2--idempotency-check-per-repo)'s "reuse the open PR" path.

Merge only when **all** of these hold; otherwise leave the PR open and report which one blocked it:

**1. Nothing in the PR is waiting on a human.**

This run applied **0** `CORRECT` claims and hit **0** `ERROR`s, *and* the PR body's `🚩 Flagged for human review` section is empty **as the body now stands**.

- Read the body; don't just count this run's findings. A flag never touches the diff, so no diff check can see one — and a flags-only PR inherited from an earlier run (via [Step 2](#step-2--idempotency-check-per-repo)'s "no net change" path) reports zero findings *this* run while still carrying findings nobody has read.
- One `ERROR` disqualifies the PR even when the diff looks clean. An unverifiable fact is precisely what a human should see.

**2. The diff is nothing but re-stamped datelines.**

```bash
python3 scripts/check_dateline_only.py
```

- Run it; don't eyeball the diff. It gates the branch **as pushed to origin**, and prints the remote, branch, and sha range it checked — confirm that line names the PR you are about to merge.
- Exit 0 is the only pass. Exit 1 is a hold. Exit 2 means the gate itself couldn't run — also a hold, never a pass.

**3. CI is green and the PR is actually mergeable.**

```bash
gh pr view <n> --repo <owner>/<repo> --json mergeable,mergeStateStatus,isDraft,statusCheckRollup
timeout 900 gh pr checks <n> --repo <owner>/<repo> --watch --fail-fast
```

- `mergeable` / `mergeStateStatus` / `isDraft` must read `MERGEABLE` / `CLEAN` / not draft.
- **Read `statusCheckRollup` before watching.** An empty rollup means this repo reports no checks at all, and `gh pr checks` then exits **1** — the same code it uses for a failing check.
  - empty rollup → no CI to wait on; the mergeable fields alone decide
  - non-empty rollup plus exit 1 → a real failure, hold

  Without that split, a repo with no workflow can never satisfy this condition, and its dateline-only PRs hold forever on a check that will never report.
- **Bound the wait.** A check that never reports — a workflow awaiting approval, a required status context nothing posts — leaves a bare `--watch` polling forever and hangs the run. Exit `124` means the `timeout` fired, which is a hold. `gh` also uses exit `8` for still-pending checks.
- Neither repo enables GitHub's own auto-merge, so `gh pr merge --auto` is unavailable; wait on the checks here instead.

The script is a whitelist and it fails closed: a correction, a version bump, an out-of-scope path, a deleted dateline, a renamed file, or newly-added prose all block the merge — as does the script's own failure. Then:

```bash
gh pr merge <n> --repo <owner>/<repo> --squash --delete-branch
```

`--delete-branch` can exit non-zero after the merge already succeeded — confirm with `gh pr view <n> --json state` (expect `MERGED`) rather than trusting the exit code. Report it as `"dateline-only, auto-merged #N"` so a merge never reads as a skip. A blocked gate is **not** a run failure.
