---
name: skill-harvest
description: >
  Use when work wraps up and the user asks what their own agent skills should
  learn from it — "harvest skill improvements", "is this skill stale?" — or when
  a session catches a personal skill giving outdated or incomplete guidance.
  Maps each learning to the specific skill it should improve and ships approved
  changes as PRs following each repo's conventions. Learnings headed to memory,
  CLAUDE.md, or project docs go to session-harvest instead.
---

# Skill Harvest

A personal skill library is a maintained product, and real sessions are its field data. When a session fights stale API guidance, hits a gotcha a skill should have warned about, or performs by hand a sequence a skill should encode, that learning is worth more in the skill — where every future session gets it — than in a private memory or a fading recollection.

This is the sibling of [session-harvest](../session-harvest/SKILL.md), split by destination:

| Learning is about... | Home | Skill |
|---|---|---|
| How Claude should work with this user; cross-session context | Memory | session-harvest |
| A convention/decision of the *current project* | CLAUDE.md/AGENTS.md, docs, hooks | session-harvest |
| Domain knowledge a *personal skill or plugin* teaches | The skill's own repo, via PR | **this skill** |

## Phase 1: Gather Field Evidence

When session-harvest hands off flagged candidates, start from those instead of re-sweeping — this phase becomes a quick supplement, and the work resumes at Phase 2. Otherwise, sweep the session (and, when invoked at project close, the whole project) for moments where a personal skill's coverage was tested:

- **Guidance that turned out wrong or stale** — the session followed a skill and hit reality: an import path moved, an API signature changed, a recommended tool version no longer exists. Version churn is the classic case.
- **Gotchas discovered the hard way** — anything that burned real debugging time and would have been a one-line warning in the right skill.
- **Repeated manual sequences** — steps the session performed by hand that fall squarely in an existing skill's domain and should be part of its procedure.
- **Praised approaches** — a technique the user explicitly endorsed that the covering skill doesn't yet teach.

Check beyond the transcript: the project's memory directory often holds staleness notes written mid-session (e.g. `*-stale.md`), and handoffs/review findings record gotchas the conversation summary may have compacted away.

## Phase 2: Map Candidates to Skills

Locate the user's skill library — the local dev clones behind their personal plugin marketplaces. The harness lists the configured marketplace sources (Claude Code: `~/.claude/plugins/known_marketplaces.json`; Codex: `codex plugin marketplace list`); if the dev-clone locations aren't already known, ask. Then route each candidate:

- **Fix or extend an existing skill** — the common case. Name the exact skill and roughly where the change lands (SKILL.md body vs. a `references/` file).
- **A genuinely new skill** — out of scope here; hand it to skill-creator and say so.
- **Public vs. private repo** — anything personal, client-specific, or unpublishable routes to the private library.
- **Nothing** — a one-off anecdote that doesn't generalize. Discarding here is healthy; a harvest where every candidate survives is matching categories instead of judging value.

**Read the target before proposing.** A candidate is only a gap if the skill actually lacks it. Open the target skill's current content — SKILL.md *and* its `references/` files — and confirm the "missing" guidance isn't already there; recollection and diff hunks aren't evidence of absence, the file is. Then check `git log` on the file: material that was deliberately cut would come back as a regression, not an improvement. If the skill already covers the ground but could be sharpened, propose an update to the existing passage rather than a parallel addition.

**Generalize before proposing.** A skill ships to every future session, so a single session's workaround becomes guidance only if it holds beyond this project's particulars. Prefer "X changed in version Y — check Z" over rules overfit to today's bug.

## Phase 3: Verify Claims

A wrong claim in a skill misleads every future session that loads it. Before presenting candidates for approval, verify each one's factual assertions against a primary source — release notes, changelogs, the library's actual code — not training intuition or the session's own summary. Date-stamp or version-stamp anything version-sensitive ("as of r184") so future staleness is detectable.

Verification runs *before* presentation on purpose: what the user approves is what ships, so it must already be checked. When a claim doesn't hold up:

- **Wrong** — correct it, or drop the candidate if the correction guts it.
- **Unverifiable in reasonable time** — soften or cut the unverifiable sentence. A skill edit with fewer, verified claims beats a fuller one resting on confident-sounding speculation.
- **Right but imprecise** — tighten it ("moved in a recent release" becomes "moved in r163").

## Phase 4: Present for Approval

Show one numbered list across all candidates: the learning, the evidence (what happened this session), the target skill and file, and the shape of the change (one-line fix / new gotcha entry / new reference section). Present in two tiers, mirroring session-harvest: candidates strong on durability (matters beyond this month), generality (holds beyond this project), and evidence (traceable to something that happened) are genuine **recommendations**; anything weak on one of those axes goes under **borderline — optional**, with a phrase on why it's marginal, so skipping it reads as a fine default rather than a rejection. When you can't decide the tier, it's borderline. Then ask which to ship. Never edit a skill repo without approval of the specific items. Briefly list what was skipped and why, so the user can overrule.

## Phase 5: Ship as PRs

For each approved item, follow the target repo's own contribution conventions — look for a conventions doc (e.g. `docs/PLUGIN-CONVENTIONS.md`) and honor it: version bumps so content changes reach installed users, per-plugin README/catalog rows, validation steps. Group changes into one branch and PR per plugin, built in a worktree, with the PR description citing the field evidence.

When a fix corrects a stale fact, check the skill's eval files for the same stale premise — an eval can encode the outdated claim and then contradict the corrected skill. Realign the eval in the same PR where the repo allows it; where evals are convention-protected, flag the mismatch in the PR description instead of leaving the two silently at odds.

Ship exactly what was approved. If anything had to shift between approval and the PR — a claim tightened, a target file changed — say so in the PR description rather than letting the diff quietly diverge from what the user signed off on. Offer a `/code-review` pass on the PRs as the closing step.

## Constraints

- **Precision over recall.** An empty harvest is a healthy outcome; a speculative skill edit pollutes guidance every future session trusts.
- **Field evidence in, timeless guidance out.** Each PR should trace back to something that actually happened; each skill edit should read as durable guidance, not a war story.
- **Never bypass the repo's review norms.** Skills ship through PRs, not direct commits to the default branch.
