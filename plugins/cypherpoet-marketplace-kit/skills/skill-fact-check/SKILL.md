---
name: skill-fact-check
description: Re-check this skills monorepo's time-sensitive facts (OS/SDK versions, device specs, external URLs, API/CLI syntax) against primary sources and open a PR with high-confidence, cited corrections — flagging anything uncertain. Use when running or configuring the scheduled fact-check routine, or to manually fact-check the repo's skills. Fans out one subagent per skill, applies only sourced edits, bumps plugin versions, and obeys repo conventions (no marketplace-publish, no catalog refresh, never edits skill descriptions or eval/workspace files). Not for general web fact-checking or non-skill content.
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
2. Run Steps 1–7 **once per cloned repo**, each time with the working directory set to that repo's clone, so every relative path (`plugins/…`, `docs/automated-routines/skill-fact-check-manifest.json`) resolves within the repo being checked.
3. Each repo carries its **own** manifest (tiers reference that repo's unit IDs) and gets its **own** branch and PR. A repo with no findings gets no PR.

The private repo has no copy of this procedure — that's intentional. It's fact-checked because the routine clones it alongside the public repo; don't run a private-only routine without also cloning `custom-agent-skills`.

## What this does (and guarantees)

Each run, re-check the time-sensitive factual claims in a repo's skills against primary sources, then open **one pull request** with:

- **Corrections** applied automatically — but only high-confidence ones that carry a primary-source citation with a verbatim supporting quote.
- **Flags** for anything uncertain, ambiguous, or out of bounds — surfaced in the PR body, never silently edited.

Guarantees: never touches `main` (pushes only to a `claude/`-prefixed branch and opens a PR — a human merges); never applies an edit without a citation; stays within per-run caps so PRs remain reviewable; and obeys this repo's plugin conventions (version bumps, no marketplace-publish, no catalog refresh).

## Operating constraints (non-negotiable)

- **PR-only.** Work on the stable branch `claude/skill-fact-check`; open or update exactly one PR per repo. Never commit to `main`.
- **Every applied edit needs a citation** — a `source_url` plus a `source_quote` that literally contains the new value. No quote ⇒ not applied (it becomes a flag).
- **Fact corrections only.** No stylistic edits, no rewrites, no scope creep. Change the smallest span that makes the fact correct.
- **Respect the protected surface** (see [What this routine must NEVER do](#what-this-routine-must-never-do)).
- **Caps:** at most **12 units** researched per run, at most **10 edits** auto-applied per run (across all repos in one routine run). Overflow is deferred or downgraded to a flag and noted in the PR.

## Scope & exclusions

A **unit** is one skill: its `SKILL.md` plus the sibling `references/**` next to it. Enumerate units (with the cwd set to the repo being checked) with:

```bash
find plugins -name SKILL.md -not -path '*/evals/*' -not -path '*-workspace/*'
```

For each `plugins/<plugin>/skills/<skill>/SKILL.md`, the unit's directory is its parent, its `unit_id` is `<plugin>/<skill>`, and its plugin manifest is `plugins/<plugin>/.claude-plugin/plugin.json`.

Fact-check the `SKILL.md` body and **all** `references/**/*.md` under the unit (≈80% of volatile facts live in references). **Exclude** everything under `**/evals/` (test fixtures) and `**/*-workspace/` (regenerable scratch). Never edit YAML frontmatter `description:`.

## Inputs

- **Manifest:** `docs/automated-routines/skill-fact-check-manifest.json` (in the repo being checked) — maps units to a volatility tier (`weekly`, `monthly`, `never`); unlisted units default to `monthly`. See [Manifest reference](#manifest-reference).
- **Datelines** (the freshness cursor). Parse these formats, all real in this repo family:
  - `**Verified:** 2026-05-30`
  - `verified 2026-05-30` (inline, e.g. "specs here verified 2026-05-30")
  - `**(as of 2026-06)**` and `*As of 2026-06; trust the screen*` (month precision → treat as the 1st)
- **Source markers:** `**Source:**` and `**Source of truth:**` — the URL a skill declares as its own authority. Check this first.
- **Caps:** `MAX_UNITS_PER_RUN = 12`, `MAX_AUTOAPPLY = 10`.

## Step 1 — Compute the due set

A unit is **due** when its tier's interval has elapsed since its newest dateline. This is age-gated, not run-gated: the dateline *is* the cursor, so a unit skipped by a crash or a cap stays due next time. Run this deterministically (don't eyeball dates), with the cwd set to the repo being checked:

```python
import json, re, subprocess, datetime, pathlib

today = datetime.date.fromisoformat(
    subprocess.check_output(['date', '-u', '+%F']).decode().strip())
m = json.loads(pathlib.Path('docs/automated-routines/skill-fact-check-manifest.json').read_text())
tier_of = {u: 'weekly' for u in m.get('weekly', [])}
tier_of.update({u: 'never' for u in m.get('never', [])})
default_tier = m.get('defaults', {}).get('tier', 'monthly')

DATE = re.compile(
    r'\*\*Verified:\*\*\s*(\d{4}-\d{2}-\d{2})'      # **Verified:** YYYY-MM-DD
    r'|verified\s+(\d{4}-\d{2}-\d{2})'              # verified YYYY-MM-DD
    r'|as of\s+(\d{4})-(\d{2})', re.I)             # (as of) YYYY-MM

def newest(unit_dir: pathlib.Path) -> datetime.date:
    found = []
    for p in unit_dir.rglob('*.md'):
        if '/evals/' in str(p) or '-workspace/' in str(p):
            continue
        for g in DATE.finditer(p.read_text(errors='ignore')):
            if g.group(1):   found.append(g.group(1))
            elif g.group(2): found.append(g.group(2))
            elif g.group(3): found.append(f"{g.group(3)}-{g.group(4)}-01")
    return max((datetime.date.fromisoformat(d) for d in found),
               default=datetime.date(1970, 1, 1))

INTERVAL = {'weekly': 7, 'monthly': 28}
due = []
skills = subprocess.check_output(
    ['bash', '-c',
     "find plugins -name SKILL.md -not -path '*/evals/*' -not -path '*-workspace/*'"]
).decode().split()
for s in skills:
    parts = pathlib.Path(s).parts          # plugins/<plugin>/skills/<skill>/SKILL.md
    unit_id = f"{parts[1]}/{parts[3]}"
    tier = tier_of.get(unit_id, default_tier)
    if tier == 'never':
        continue
    last = newest(pathlib.Path(s).parent)
    age = (today - last).days
    if age >= INTERVAL[tier]:
        due.append((age, unit_id, str(pathlib.Path(s).parent), tier, last.isoformat()))

due.sort(reverse=True)                      # most overdue first
for row in due[:12]:                         # MAX_UNITS_PER_RUN
    print(*row, sep='\t')
print(f"# {len(due)} due, {min(len(due),12)} this run, {max(0,len(due)-12)} deferred")
```

The first runs will surface a large backlog (most units have no dateline yet → epoch → always due). That's expected: the cap drains it most-overdue-first, and the set shrinks as merged PRs stamp datelines.

## Step 2 — Idempotency check (per repo)

One stable branch, one long-lived PR, reused every run — so repeated runs converge instead of piling up duplicate PRs.

```bash
gh pr list --state open  --head claude/skill-fact-check --json number -q '.[0].number'   # open?
gh pr list --state merged --head claude/skill-fact-check --json number -q '.[0].number'   # last merged?
```

- **Open PR exists →** reuse it. `git fetch origin`, recreate the branch from `origin/main` (`git switch -C claude/skill-fact-check origin/main`), re-apply this run's net findings, `git push --force-with-lease`, and **rewrite** the PR body to the current state (`gh pr edit <n> --body-file -`). Do not append.
- **No open PR, last one merged (or none) →** start fresh from `origin/main`. The merged work is already in `main` and its datelines advanced, so fewer units are due.
- **A run that produces no net change** vs. what's already on the branch → push nothing, leave the PR untouched, log "no new findings; PR #N still current."

## Step 3 — Fan out (one subagent per due unit)

Deep-researching 12 units in the orchestrator's own context would overflow it. Instead, spawn **one `Task` subagent per due unit**, in batches of **≤6 concurrent**. The orchestrator never reads skill bodies — subagents do the reading and research and return a compact JSON result.

Give each subagent: the unit's `unit_dir` and `plugin_dir`, the [verification procedure](#step-3a--subagent-verification-procedure-paste-verbatim) **pasted verbatim** (subagents do not inherit this file), and the JSON contract below. Subagents **propose**; they never edit files.

**Return contract (the subagent's entire final message — strict JSON, nothing else):**

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
      "source_quote": "verbatim quote from the source that contains the new value 1290×2796",
      "confidence": "high",
      "note": ""
    }
  ],
  "checked_count": 14,
  "newest_dateline": "2026-05-30"
}
```

`status` is one of: `CORRECT` (current text is wrong; `new` ≠ `old`; cite the fix), `CONFIRMED_UNCHANGED` (verified correct; `new` == `old`), `FLAG_UNCERTAIN`, `FLAG_AMBIGUOUS`, `FLAG_DESCRIPTION_FRONTMATTER`, or `ERROR` (couldn't verify). `locator` must be an **exact, unique substring** of the live file (not a line number — those drift).

## Step 3a — Subagent verification procedure (paste verbatim)

> You are fact-checking ONE skill. Read its `SKILL.md` and every `references/**/*.md` under `{unit_dir}` (ignore anything under `evals/` or `*-workspace/`). Extract the **verifiable, time-sensitive** claims — versions/"latest" (iOS 27, Swift 6.x, three.js r###, Blender 5.1, Expo SDK ##), dated/"as of" stamps, specs (device pixel dimensions, symbol counts, bitrates, limits), external URLs, and API/CLI syntax (flag names, renamed properties). Ignore methodology, process steps, and design guidance — only check facts.
>
> For each claim, apply this gate. A claim may be returned as `CORRECT` (an applied edit) **only if every step passes**; otherwise downgrade to a `FLAG_*` or `ERROR`.
>
> 1. **Pick the primary source by type.** VERSION/"latest" → the vendor's own release channel (GitHub Releases/tags for the real project, Apple "What's New"/release notes, Blender release notes). SPEC → the vendor's official reference page. EXTERNAL_URL → resolve the URL itself (HTTP 200 at the same canonical content = ok; 301 to a new canonical = changed; 404/410/soft-404 = gone). API_SYNTAX → the tool's official docs or its migration/changelog for that version. **Blogs, aggregators, and forums are not primary.**
> 2. **Honor the skill's own cited source first.** If the file declares `**Source:**`/`**Source of truth:** <url>`, fetch THAT as the primary check. If it's unreachable or gone and you fall back to another source, the result is a **flag** (the skill's own source may be stale and needs human attention) — never a silent edit.
> 3. **Both-conditions gate.** The source must establish BOTH that the current text is wrong AND what the correct value is. A source that says "this changed" but not "to what" → `FLAG_UNCERTAIN`.
> 4. **Adversarial / two-source rule for value changes.** Before proposing a changed value, confirm it from a second independent authoritative source, or at two stable locations on the vendor's own site. One source only, or sources disagree → `FLAG_AMBIGUOUS` (return both URLs). (Re-confirming an UNCHANGED value needs only one authoritative source → `CONFIRMED_UNCHANGED`.)
> 5. **Confidence.** `high` only if 1–4 all pass against vendor-primary sources. Anything resting on inference or a single non-vendor source → `medium`/`low` → flag, don't apply.
> 6. **Citation is mandatory.** Every `CORRECT` claim must include `source_url` and a `source_quote` that literally contains the value in `new`. If you can't produce that quote, it is not a correction — flag it.
> 6b. **Surgical edits only.** A `CORRECT` must be a *localized* replacement — a token, a value, a single import/line. If the accurate fix needs a multi-sentence rewrite or prose restructuring (even at high confidence), return `FLAG_UNCERTAIN` with the proposed wording in `note`. Keep auto-edits small and reviewable.
> 7. **Frontmatter guard.** If a wrong fact lives in a `description:` value in `SKILL.md` YAML frontmatter, return `FLAG_DESCRIPTION_FRONTMATTER` — never edit it. (Only when the value is actually wrong; if it's correct, it's `CONFIRMED_UNCHANGED` — don't flag a frontmatter value just for being in frontmatter.)
> 8. **Fetch fallback.** Prefer the Firecrawl connector for bot-walled sources (Apple developer docs especially); fall back to `WebFetch`/`WebSearch`. If a source is unreachable every way, return `ERROR` for that claim (it will be flagged, not edited) — do not guess.
>
> Return ONLY the JSON object defined in the contract. No prose, no edited files.

## Step 4 — Reduce & apply (orchestrator)

Collect the subagents' JSON. The orchestrator now performs every mutation — editing authority is centralized so the caps and guards are enforced in one place.

For each claim with `status == "CORRECT"`, in most-overdue-unit order, apply it **only if** all hold:

- `source_url` is non-empty **and** `source_quote` literally contains `new` (validate the substring — this is the hard anti-hallucination gate; a claim failing it becomes a flag).
- `confidence == "high"`.
- The edit is a **localized** replacement (`old` → `new` is a token/value/line, not a multi-sentence rewrite). If `old` spans more than a sentence or two, downgrade it to a flag.
- The target file is not under `evals/` or `*-workspace/`, and the edit is not to a `description:` frontmatter line or a protected `plugin.json` field.
- The `MAX_AUTOAPPLY` budget isn't exhausted (otherwise downgrade remaining corrections to "would-apply, deferred for review" flags).

Apply with an exact-substring `Edit` using `locator` → replace `old` with `new`. Group edits by plugin. Track which plugins were touched (for the version bump).

## Step 5 — Version bumps

After editing any file under a plugin, bump that plugin's `.claude-plugin/plugin.json` `version` **once** (dedupe — a plugin touched by two skills bumps once):

- **Applied content correction → MINOR bump** (`0.1.0 → 0.2.0`). Per `docs/PLUGIN-CONVENTIONS.md`, pre-1.0 the default bump for anything user-visible is MINOR, and a fact correction is user-visible.
- **Dateline-only re-stamp with no content change → no version bump.** A date stamp isn't user-visible guidance; `version` is the user-update cache key, so don't churn it. (The committed date still advances the age-gate.)
- Edit **only** the `version` field. Never touch `name`/`description`/`homepage`.

## Step 6 — Datelines

- **`CONFIRMED_UNCHANGED`** section that carries a dateline → **re-stamp** it to today's date (this is what lets a re-verified unit go quiet until its next interval; without it the unit re-researches every run forever). Re-stamp in place; no version bump.
- **No dateline but a `**Source:**`/`**Source of truth:**` marker exists** → append `**Verified:** <today>` right after that marker so future runs can age-gate the unit. (This bootstraps the private repo's units, which start with no datelines.)
- **`ERROR`** (couldn't verify) → **never** re-stamp; leaving the date stale correctly keeps the unit due.
- **`CORRECT`** → the correction already bumps the version; re-stamp the section's dateline to today as part of the same edit.

## Step 7 — Open or update the PR (per repo)

Open a PR **only if** the repo had ≥1 applied correction, ≥1 new flag, or ≥1 dateline change worth shipping. Commit **per plugin** so the PR reviews cleanly:

```
🩹 fix(<skill>): <one-line fact correction> [skill-fact-check]

- references/<file>.md: <old> → <new>  (per <source>)
- bump <plugin> <oldver> → <newver>
```

Match the repo's commit style (it uses gitmoji — see `cypherpoet-git-flow/emoji-commits`). Branch `claude/skill-fact-check`. Each cloned repo gets its **own** branch and PR via `gh pr create --repo <owner>/<repo>` / `gh pr edit --repo …`.

**PR title:** `🔍 Skill fact-check: N corrections, M flagged (<repo> <YYYY-MM-DD>)`

**PR body** (rewritten each run — current state, not a changelog):

```markdown
Automated skill fact-check (the `skill-fact-check` skill in `cypherpoet-marketplace-kit`).
Branch `claude/skill-fact-check`. Units due: X · checked this run: Y · deferred (cap): Z.
Auto-applied: A corrections (all high-confidence, sourced). Flagged: B.

## ✅ Corrections applied (cited)
| Plugin | File | Type | Old → New | Source | Quote |
|---|---|---|---|---|---|

## 🚩 Flagged for human review (NOT changed)
| Plugin | File | Why | Detail | Source(s) |
|---|---|---|---|---|

## 🔁 Re-verified unchanged (datelines re-stamped)
- <unit>: <what was confirmed> (source)

## ⚠️ Could not verify (errors)
- <unit/file>: <reason, e.g. host_not_allowed — is the Firecrawl connector attached?>

## ⬆️ Version bumps
- <plugin>: <old> → <new>

## ⏭️ Deferred to next run (per-run cap)
- <unit>, <unit>
```

## Failure modes & guardrails

| Failure | Guardrail |
|---|---|
| Firecrawl connector missing / `host_not_allowed` 403 | Fall back to WebFetch/WebSearch; if still unreachable → `ERROR` → claim is **flagged, not edited**. Run does not fail; note it under "Could not verify" so the connector can be fixed. |
| Subagent proposes an unsourced / hallucinated fix | Orchestrator drops any `CORRECT` whose `source_quote` doesn't contain `new`. Subagents can't write files, so a hallucination becomes a flag at worst. |
| Ambiguous / conflicting sources | `FLAG_AMBIGUOUS` with both URLs; never auto-resolved. |
| Runaway PR / rate limits / usage | `MAX_UNITS_PER_RUN=12`, `MAX_AUTOAPPLY=10`, batches ≤6, age-gated due set. A throttled run just leaves units un-restamped → still due next week. |
| Partial completion (orchestrator dies mid-run) | Per-plugin commits + age-gating → finished plugins persist, un-restamped units stay due, the open PR is folded into next run (Step 2). "Green run" status ≠ task success — the PR body's "Could not verify" / "Deferred" sections are the real signal. |
| A correction would touch a protected surface | The guards in Steps 4 and below → flag instead. |

## What this routine must NEVER do

- Never commit to `main`, never widen branch-push beyond `claude/`-prefixed.
- Never apply an edit without a `source_url` + a `source_quote` containing the new value.
- Never edit a `description:` frontmatter field, or `plugin.json` `name`/`description`/`homepage` (only `version`).
- Never add the `marketplace-publish` label (fact edits don't touch the marketplace catalog surface).
- Never refresh `docs/CATALOG.md` (component counts don't change).
- Never edit anything under `**/evals/` or `**/*-workspace/`.
- Never open a second PR while one is open (reuse the stable branch).
- Never re-stamp a dateline for a claim it couldn't actually verify.

## Manifest reference

`docs/automated-routines/skill-fact-check-manifest.json` is repo-local (lists only that repo's units). Shape:

```json
{
  "defaults": { "tier": "monthly" },
  "weekly": ["<plugin>/<skill>", "..."],
  "never":  ["<plugin>/<skill>", "..."]
}
```

Tiers: **weekly** (≥7 days) for fast-drifting skills (Apple OS/App Store specs, SwiftUI "what's new", SF Symbols, three.js, Blender); **never** for evergreen methodology (session handoff/harvest, emoji commits, changelog, readme badges, GDScript); **monthly** (≥28 days, the default) for everything else. To re-tier a skill, move its `unit_id` between lists — no skill change needed. A `unit_id` not in any list is `monthly`.
