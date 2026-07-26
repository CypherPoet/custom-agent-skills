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
2. Run Steps 1–7 **once per cloned repo**, each time with the working directory set to that repo's clone, so every relative path (`plugins/…`, `docs/automated-routines/skill-fact-check-manifest.json`) resolves within the repo being checked.
3. Each repo carries its **own** manifest (tiers reference that repo's unit IDs) and gets its **own** branch and PR. A repo with no findings gets no PR.

The private repo has no copy of this procedure — that's intentional. It's fact-checked because the routine clones it alongside the public repo; don't run a private-only routine without also cloning `custom-agent-skills`.

## What this does (and guarantees)

Each run, re-check the time-sensitive factual claims in a repo's skills against primary sources, then open **one pull request** with:

- **Corrections** applied directly — any fix the cited evidence genuinely establishes, from a one-token version bump to a multi-site API rename or a rewritten note whose logic was inverted.
- **Flags** for anything the evidence leaves uncertain or ambiguous, or that is an editorial judgment call rather than a factual one — surfaced in the PR body **with proposed wording**, never silently edited.

**The quality-control mechanism is git + PR review.** The routine never touches `main` (it pushes only to a `claude/`-prefixed branch and opens a PR a human merges), every applied edit cites the primary source a reviewer can check it against, and the PR body lays each change next to its evidence. Within that frame, use judgment: the standard for applying a correction is *"would a competent reviewer, shown this evidence, make this edit?"* — not a mechanical size or format rule. The routine also obeys this repo's plugin conventions (version bumps, no marketplace-publish, no catalog refresh).

## Operating constraints (non-negotiable)

- **PR-only.** Work on the stable branch `claude/skill-fact-check`; open or update exactly one PR per repo. Never commit to `main`. PR review is the quality gate — everything else here exists to make that review easy, not to substitute for it.
- **Every applied edit is evidence-backed** — it carries a `source_url` (primary source) and a `source_quote` showing what the source establishes, so a reviewer can verify the fix without redoing the research. Evidence too thin to convince a reviewer ⇒ flag with proposed wording, don't edit.
- **Fact corrections only.** Fix what the evidence shows is wrong — a token, a corrected code snippet, a rename applied at every site in a file, or a note whose logic is inverted — and nothing more. No stylistic edits, no restructuring, no scope creep beyond what the fact requires.
- **Respect the protected surface** (see [What this routine must NEVER do](#what-this-routine-must-never-do)).
- **Batches, not ceilings:** research the due set most-overdue-first in waves of ~12 units per repo (fan-out limit, keeps subagent batches manageable), and keep launching waves until the due set is drained or the session genuinely runs short of budget. Anything actually deferred is listed in the PR and stays due next run (age-gating self-heals) — but deferral is the fallback for real resource pressure, not the design.

## Scope & exclusions

A **unit** is one skill: its `SKILL.md` plus the sibling `references/**` next to it. Enumerate units (with the cwd set to the repo being checked) with:

```bash
find plugins -name SKILL.md -not -path '*/evals/*' -not -path '*-workspace/*'
```

For each `plugins/<plugin>/skills/<skill>/SKILL.md`, the unit's directory is its parent, its `unit_id` is `<plugin>/<skill>`, and its plugin manifest is `plugins/<plugin>/.claude-plugin/plugin.json`.

Fact-check the `SKILL.md` body, **all** `references/**/*.md` under the unit (≈80% of volatile facts live in references), and `evals/**` — fixtures encode the same version-sensitive premises as the docs and go stale with them, leaving an eval that contradicts the skill it grades. Evals are corrected under the same evidence gates as any other file. **Exclude** `**/*-workspace/` entirely (regenerable scratch). Never edit YAML frontmatter `description:`.

## Inputs

- **Manifest:** `docs/automated-routines/skill-fact-check-manifest.json` (in the repo being checked) — maps units to a volatility tier (`weekly`, `monthly`, `never`); unlisted units default to `monthly`. See [Manifest reference](#manifest-reference).
- **Acknowledged flags:** an optional `acknowledged` array in that same manifest lists flags a human already reviewed and accepted — the "not wrong / no vendor source / won't change" findings — so they stop re-appearing as new every run. Each entry pins a `unit_id` + a `locator` (unique substring of the flagged text), a human `reason`, and a `recheck_after` date (or `"never"`). Applied in [Step 4](#step-4--reduce--apply-orchestrator); shape in [Manifest reference](#manifest-reference).
- **Datelines** (the freshness cursor). Parse every form below — all real in this repo family. Match only these explicit verification/sync labels, never bare content dates (`released …`, `Created: …`), which would falsely mark a stale unit fresh:
  - `**Verified:** 2026-05-30` — the canonical marker this routine writes.
  - `> Last synced: 2026-06-19` and `*Last synced with Apple HIG: 2026-06-16*` — the dominant existing form (the label may carry trailing words before the colon).
  - `**Audit baseline:** … verified against … (2026-06-26)` — parenthetical date (e.g. the three.js audit marker).
  - `verified 2026-05-30` (inline, e.g. "specs here verified 2026-05-30").
  - `**(as of 2026-06)**` and `*As of 2026-06; trust the screen*` (month precision → treat as the 1st).
- **Source markers:** `**Source:**` and `**Source of truth:**` — the URL a file declares as the authority for a specific fact. Check this first.
- **Declared source set:** a `## Primary Sources` section at the end of a unit's `SKILL.md` — the skill's own list of canonical verification sources (one bullet per source, each saying what it's authoritative for). Prefer these over free-choice research; a placeholder section ("None declared yet …") means fall back to vendor-primary sources per claim.
- **Change-signal leads:** an optional per-unit `Change-Signal Sources` block lists secondary leads (e.g. a maintainer's blog) to scan for *what* may have drifted since the last dateline. Leads only — confirm against a primary source (a declared one where the claim is covered), never cite one in an edit.
- **Batch size:** `BATCH_SIZE = 12` — units per research wave, per cloned repo. A wave bound, not a per-run ceiling: waves repeat until the due set drains.

## Step 1 — Compute the due set

A unit is **due** when its tier's interval has elapsed since its newest dateline. This is age-gated, not run-gated: the dateline *is* the cursor, so a unit skipped by a crash or a deferral stays due next time. Run this deterministically (don't eyeball dates), with the cwd set to the repo being checked:

```python
import json, re, subprocess, datetime, pathlib

today = datetime.date.fromisoformat(
    subprocess.check_output(['date', '-u', '+%F']).decode().strip())
m = json.loads(pathlib.Path('docs/automated-routines/skill-fact-check-manifest.json').read_text())
tier_of = {u: 'weekly' for u in m.get('weekly', [])}
tier_of.update({u: 'monthly' for u in m.get('monthly', [])})
tier_of.update({u: 'never' for u in m.get('never', [])})
default_tier = m.get('defaults', {}).get('tier', 'monthly')

# Recognize every freshness-marker dialect in the repo family — but only
# explicit verification/sync labels, never bare content dates ("released …",
# "Created: …", "replaced … on …"), which would falsely mark a stale unit fresh.
DATE = re.compile(
    r'\*\*verified:\*\*\s*(?P<full>\d{4}-\d{2}-\d{2})'                      # **Verified:** YYYY-MM-DD (canonical)
    r'|(?:last\s+)?synced\b[^\n:]{0,40}?:\s*(?P<synced>\d{4}-\d{2}-\d{2})'  # [Last ]synced[ with …]: YYYY-MM-DD
    r'|audit baseline\b[^\n]*?\((?P<audit>\d{4}-\d{2}-\d{2})\)'             # **Audit baseline:** … (YYYY-MM-DD)
    r'|\bverified\s+(?P<vinline>\d{4}-\d{2}-\d{2})'                         # verified YYYY-MM-DD (inline)
    r'|\bas of\s+(?P<month>\d{4}-\d{2})', re.I)                            # as of YYYY-MM (month → 1st)

def newest(unit_dir: pathlib.Path) -> datetime.date:
    found = []
    for p in unit_dir.rglob('*.md'):
        if '/evals/' in str(p) or '-workspace/' in str(p):
            continue
        for m in DATE.finditer(p.read_text(errors='ignore')):
            iso = m.group('full') or m.group('synced') or m.group('audit') or m.group('vinline')
            if iso:
                found.append(iso)
            elif m.group('month'):
                found.append(m.group('month') + '-01')
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
    if age >= INTERVAL.get(tier, 28):       # unknown/typo'd tier → monthly, never crash
        due.append((age, unit_id, str(pathlib.Path(s).parent), tier, last.isoformat()))

due.sort(reverse=True)                      # most overdue first
for row in due:
    print(*row, sep='\t')
print(f"# {len(due)} due — research in waves of ~12, most-overdue-first, until drained")

# Manifest drift — works in every cloned repo; report, don't edit (see below)
unit_ids = {f"{pathlib.Path(s).parts[1]}/{pathlib.Path(s).parts[3]}" for s in skills}
listed = [u for k in ('weekly', 'monthly', 'never') for u in m.get(k, [])]
for u in sorted(set(listed) - unit_ids):
    print(f"# DRIFT orphaned: {u} listed in the manifest but not on disk")
for u in sorted({u for u in listed if listed.count(u) > 1}):
    print(f"# DRIFT double-listed: {u} in more than one tier (later list wins — keep one)")
for u in sorted(unit_ids - set(listed)):
    print(f"# DRIFT untiered: {u} not in any tier list (defaults to monthly)")
```

Early runs surface a backlog: any unit with no *recognized* dateline reads as epoch → always due. That's expected — waves drain it most-overdue-first, and the set shrinks as the parser above picks up the freshness markers already in the files and merged PRs stamp datelines (Step 6) on the units that lack one.

`# DRIFT` lines are manifest hygiene, not fact findings: never edit the manifest for them — list them in the PR body's flagged section so a human re-tiers deliberately.

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

Deep-researching a wave of units in the orchestrator's own context would overflow it. Instead, spawn **one `Task` subagent per due unit**, in batches of **≤6 concurrent**, wave after wave until the due set is drained. The orchestrator never reads skill bodies — subagents do the reading and research and return a compact JSON result.

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
      "source_quote": "verbatim passage from the source that establishes the correction",
      "confidence": "high",
      "note": ""
    }
  ],
  "checked_count": 14,
  "newest_dateline": "2026-05-30"
}
```

`status` is one of: `CORRECT` (current text is wrong; `new` ≠ `old`; cite the fix), `CONFIRMED_UNCHANGED` (verified correct; `new` == `old`), `FLAG_UNCERTAIN`, `FLAG_AMBIGUOUS`, `FLAG_DESCRIPTION_FRONTMATTER`, or `ERROR` (couldn't verify). `locator` must be an **exact, unique substring** of the live file (not a line number — those drift). A fix that touches several sites (e.g. an API rename used throughout a file) is one *finding* returned as multiple `CORRECT` claims — one per site, each with its own locator, sharing the citation.

## Step 3a — Subagent verification procedure (paste verbatim)

> You are fact-checking ONE skill. Read its `SKILL.md`, every `references/**/*.md`, and everything under `evals/` within `{unit_dir}` (ignore `*-workspace/`). Extract the **verifiable, time-sensitive** claims — versions/"latest" (iOS 27, Swift 6.x, three.js r###, Blender 5.1, Expo SDK ##), dated/"as of" stamps, specs (device pixel dimensions, symbol counts, bitrates, limits), external URLs, and API/CLI syntax (flag names, renamed properties). Ignore methodology, process steps, and design guidance — only check facts.
>
> For each claim, apply this gate. A claim may be returned as `CORRECT` (an applied edit) **only if every step passes**; otherwise downgrade to a `FLAG_*` or `ERROR`.
>
> 1. **Pick the primary source by type.** VERSION/"latest" → the vendor's own release channel (GitHub Releases/tags for the real project, Apple "What's New"/release notes, Blender release notes). SPEC → the vendor's official reference page. EXTERNAL_URL → resolve the URL itself (HTTP 200 at the same canonical content = ok; 301 to a new canonical = changed; 404/410/soft-404 = gone). API_SYNTAX → the tool's official docs or its migration/changelog for that version. **Blogs, aggregators, and forums are not primary.**
> 2. **Honor the skill's own cited sources first.** Two declaration forms, in precedence order: (a) a per-fact `**Source:**`/`**Source of truth:** <url>` marker in the file — fetch THAT as the primary check for that fact; (b) the unit's `## Primary Sources` section in its `SKILL.md` — the skill's declared source set; when a claim falls under a declared source's stated scope (versions, specs, API syntax, …), fetch that source before choosing one on your own. Only claims covered by neither fall through to your own step-1 choice. If a declared source (either form) is unreachable or gone and you fall back to another source, the result is a **flag** (the skill's own source may be stale and needs human attention) — never a silent edit.
> 2b. **Consult declared change-signal leads.** If the unit declares a **Change-Signal Sources** list (secondary leads such as a maintainer's blog), scan them first to *discover* what may have changed since the last dateline — but treat them as leads, never authorities. Anything they surface must still pass the both-conditions gate (step 3) against a **vendor-primary** source (per steps 1–2), and a lead URL must never appear in `source_url` for an applied edit. Blogs, aggregators, and forums remain non-primary (step 1).
> 3. **Both-conditions gate.** The source must establish BOTH that the current text is wrong AND what the correct value is. A source that says "this changed" but not "to what" → `FLAG_UNCERTAIN`.
> 4. **Corroborate value changes.** Before proposing a changed value, corroborate it — a second independent authoritative source, two stable locations on the vendor's own site, or direct verification (resolving the URL, hitting the documented API endpoint). If sources genuinely disagree → `FLAG_AMBIGUOUS` (return both URLs). (Re-confirming an UNCHANGED value needs only one authoritative source → `CONFIRMED_UNCHANGED`.)
> 5. **Confidence.** `high` only if 1–4 all pass against vendor-primary sources. Anything resting on inference or a single non-vendor source → `medium`/`low` → flag, don't apply.
> 6. **Cite what you fix.** Every `CORRECT` claim includes `source_url` and a `source_quote` — the passage a reviewer would check the fix against. The quote must *establish* the correction; it need not contain your replacement text verbatim (a changelog can document a rename without printing your exact line). The test is whether a reviewer reading the quote would make the same edit. No evidence you can point to ⇒ not a correction — flag it.
> 6b. **Propose the full fix the evidence supports.** A correction can be any size the evidence establishes: a token swap, a rename applied at every site in the file (one `CORRECT` claim per site, sharing the citation), a corrected code snippet, or a rewritten note whose logic was inverted. Supply exact replacement text in `new`. What makes something a correction is the evidence behind it, not the edit's size. Only when the fix is genuinely an *editorial* call — the current text isn't wrong, just incomplete or arguably framed — flag it, with your proposed wording in `note` so the human can apply it with one decision.
> 7. **Frontmatter guard.** If a wrong fact lives in a `description:` value in `SKILL.md` YAML frontmatter, return `FLAG_DESCRIPTION_FRONTMATTER` — never edit it. (Only when the value is actually wrong; if it's correct, it's `CONFIRMED_UNCHANGED` — don't flag a frontmatter value just for being in frontmatter.)
> 7b. **Eval semantics.** Evals are correctable like any other file, but read them for what they are so you don't manufacture findings. A negative assertion naming a removed API (`must not use mesh.use_auto_smooth`) is *asserting the removal* — it's correct, not stale: `CONFIRMED_UNCHANGED`. A version inside an eval `prompt` is scenario data (a user persona), not a claim about the world, so it isn't a stale fact — leave it alone. Real findings look like: a mechanism labelled by a version *point* when it holds over a range, an assertion naming an interpreter or SDK that no longer exists, or an `expected_output` describing behavior the vendor has since changed.
> 8. **Fetch fallback.** For Apple developer-docs symbols, hit the docs **JSON endpoint** first — `https://developer.apple.com/tutorials/data/documentation/<framework>/<lowercased-symbol-path>.json` (e.g. `swiftui/view/statusbarhidden(_:).json`). It is not bot-walled and returns structured availability in `metadata.platforms[]` (`introducedAt` / `deprecatedAt` / deprecation `message`); a `404` means the symbol doesn't exist. For other bot-walled sources prefer the Firecrawl connector; fall back to `WebFetch`/`WebSearch`. If a source is unreachable every way, return `ERROR` for that claim (it will be flagged, not edited) — do not guess.
>
> Return ONLY the JSON object defined in the contract. No prose, no edited files.

## Step 4 — Reduce & apply (orchestrator)

Collect the subagents' JSON. The orchestrator now performs every mutation — editing authority is centralized so the guards are enforced in one place, and because subagents research while the orchestrator *reviews*: read each proposed correction the way a PR reviewer would.

For each claim with `status == "CORRECT"`, in most-overdue-unit order, apply it when:

- The cited `source_url` is a primary source and the `source_quote` genuinely establishes both that the old text is wrong and that `new` is right. Spot-check anything surprising or load-bearing (fetch the source, resolve the URL yourself) — the subagent did the research, but the orchestrator owns the edit.
- `confidence == "high"` — anything lower ships as a flag with its evidence attached.
- It's a fact correction within scope: not under `*-workspace/`, not a `description:` frontmatter line or a protected `plugin.json` field, and not a stylistic rewrite wearing a correction's clothes.

**Size is not a gate.** A sourced multi-site rename or corrected snippet applies just like a token swap — apply each site with an exact-substring `Edit` using its `locator`. If one unit's corrections would dominate the PR (dozens of edits), give them their own commit so the diff reviews cleanly; don't downgrade them to flags for being numerous. Group edits by plugin. Track which plugins were touched (for the version bump).

**Suppress acknowledged flags.** Build the manifest's `acknowledged` list once per repo, then reduce every `FLAG_*` claim against it. A flag is **acknowledged** when a live entry shares its `unit_id` and the entry's `locator` is a substring of the flag's `locator` (or, if that's empty, its `old`/`note`). For a match:

- `recheck_after` is `"never"` or a future date → **drop the flag from the active `🚩 Flagged` table**, list it under `🔕 Known / acknowledged` (Step 7) instead, and exclude it from the flagged count.
- `recheck_after` has passed → **do not suppress**; keep it flagged and annotate `(acknowledgment expired <date> — re-confirm or renew)`.

The subagent still researches the fact every run — an acknowledgment only changes where its result lands, so a fact that quietly *changed* still surfaces (its `locator`/`old` shifts and no longer matches). Acknowledgments silence **only** `FLAG_*` findings: never suppress a `CORRECT` (a sourced fix) or an `ERROR` (a fact that couldn't be verified).

## Step 5 — Version bumps

After editing a plugin's **shipped** content, bump that plugin's `.claude-plugin/plugin.json` `version` **once** (dedupe — a plugin touched by two skills bumps once):

- **Applied content correction → MINOR bump** (`0.1.0 → 0.2.0`). Per `docs/PLUGIN-CONVENTIONS.md`, pre-1.0 the default bump for anything user-visible is MINOR, and a fact correction is user-visible.
- **Dateline-only re-stamp with no content change → no version bump.** A date stamp isn't user-visible guidance; `version` is the user-update cache key, so don't churn it. (The committed date still advances the age-gate.)
- **Eval-only correction → no version bump.** `evals/` is stripped from vendored copies and never reaches an install, so bumping for it would push an update carrying nothing the user receives.
- Edit **only** the `version` field. Never touch `name`/`description`/`homepage`.

## Step 6 — Datelines

- **`CONFIRMED_UNCHANGED`** section that carries a recognized dateline → **re-stamp** it to today's date, updating whichever marker form the unit already uses (`**Verified:**`, `Last synced:`, the audit-baseline date, etc.) — this is what lets a re-verified unit go quiet until its next interval; without it the unit re-researches every run forever. Re-stamp in place; no version bump.
- **No recognized dateline anywhere in the unit** → stamp `**Verified:** <today>` so future runs can age-gate it (only when the unit was actually verified this run — ≥1 `CONFIRMED_UNCHANGED` or `CORRECT`; never on a pure `ERROR`). Place it right after a `**Source:**`/`**Source of truth:**` marker if one exists, otherwise as a new line directly under the unit's `SKILL.md` H1 title. This drains the backlog of units that start with no dateline (the whole private repo, plus units whose only freshness cue is a version like "As of iOS 27") and converges every unit on the canonical `**Verified:**` marker — so the age-gate stops depending on legacy dialects. No version bump (a dateline isn't user-visible guidance).
- **`ERROR`** (couldn't verify) → **never** re-stamp; leaving the date stale correctly keeps the unit due.
- **`CORRECT`** → the correction already bumps the version; re-stamp the section's dateline to today as part of the same edit.

## Step 7 — Open or update the PR (per repo)

Open a PR **only if** the repo had ≥1 applied correction, ≥1 new flag, or ≥1 dateline change worth shipping. Commit **per plugin** so the PR reviews cleanly:

```
🩹 fix(<skill>): <one-line fact correction> [skill-fact-check]

- references/<file>.md: <old> → <new>  (per <source>)
- bump <plugin> <oldver> → <newver>
```

Match the repo's commit style (it uses gitmoji — see `cypherpoet-emoji-commits/emoji-commits`). Branch `claude/skill-fact-check`. Each cloned repo gets its **own** branch and PR via `gh pr create --repo <owner>/<repo>` / `gh pr edit --repo …`.

**PR title:** `🔍 Skill fact-check: N corrections, M flagged (<repo> <YYYY-MM-DD>)`

**PR body** (rewritten each run — current state, not a changelog):

```markdown
Automated skill fact-check (the `skill-fact-check` skill in `cypherpoet-marketplace-kit`).
Branch `claude/skill-fact-check`. Units due: X · checked this run: Y · deferred (budget): Z.
Applied: A corrections (all high-confidence, sourced). Flagged: B (new) · acknowledged (suppressed): C.

## ✅ Corrections applied (cited)
| Plugin | File | Type | Old → New | Source | Quote |
|---|---|---|---|---|---|

## 🚩 Flagged for human review (NOT changed)
_Each flag carries proposed wording where one exists, so accepting it is one decision, not a research task._
| Plugin | File | Why | Detail + proposed fix | Source(s) |
|---|---|---|---|---|

## 🔕 Known / acknowledged (not re-flagged)
_Flags a human already reviewed and accepted (manifest `acknowledged`) — shown for the record, excluded from the flagged count. An entry whose `recheck_after` has passed moves back up to 🚩._
| Plugin | Acknowledged item | Reason | Re-check after |
|---|---|---|---|

## 🔁 Re-verified unchanged (datelines re-stamped)
- <unit>: <what was confirmed> (source)

## ⚠️ Could not verify (errors)
- <unit/file>: <reason, e.g. host_not_allowed — is the Firecrawl connector attached?>

## ⬆️ Version bumps
- <plugin>: <old> → <new>

## ⏭️ Deferred to next run (ran short of budget)
- <unit>, <unit>
```

## Failure modes & guardrails

| Failure | Guardrail |
|---|---|
| Firecrawl connector missing / `host_not_allowed` 403 | Fall back to WebFetch/WebSearch; if still unreachable → `ERROR` → claim is **flagged, not edited**. Run does not fail; note it under "Could not verify" so the connector can be fixed. |
| Subagent proposes an unsourced or wrong fix | Subagents can't write files. The orchestrator reviews every proposal against its cited evidence and spot-checks before applying — and the PR diff with citations gives the human reviewer the final check. |
| Ambiguous / conflicting sources | `FLAG_AMBIGUOUS` with both URLs; never auto-resolved. |
| Runaway PR / rate limits / usage | Research waves of ~12 with ≤6 concurrent subagents; age-gated due set. A throttled run just leaves units un-restamped → still due next week. |
| Partial completion (orchestrator dies mid-run) | Per-plugin commits + age-gating → finished plugins persist, un-restamped units stay due, the open PR is folded into next run (Step 2). "Green run" status ≠ task success — the PR body's "Could not verify" / "Deferred" sections are the real signal. |
| A correction would touch a protected surface | The guards in Steps 4 and below → flag instead. |

## What this routine must NEVER do

- Never commit to `main`, never widen branch-push beyond `claude/`-prefixed.
- Never apply an edit without cited primary-source evidence a reviewer can check it against.
- Never edit a `description:` frontmatter field — it is the skill's *triggering* signal, judged by the model at routing time, so changing it changes **when the skill fires**. That's a behavior change wearing a fact-fix's clothes, and it's outside this routine's remit even when the text is genuinely wrong (hence `FLAG_DESCRIPTION_FRONTMATTER`).
- Never edit `plugin.json` `name`/`description`/`homepage` (only `version`) — those three are the Claude catalog fields, and editing one puts the PR on the marketplace catalog surface, which needs a `marketplace-publish` run this routine can't perform (that skill is manual-only, `disable-model-invocation`).
- Never add the `marketplace-publish` label. A version bump is **not** a catalog-surface change — per `needs_marketplace_publish.py`, "a version-only bump does NOT count: that's content, gated by the version key." Since the rule above keeps the routine off the catalog fields, no run can ever need a publish; label every one and you'd republish the catalog weekly for nothing.
- Never refresh `docs/CATALOG.md` (component counts don't change).
- Never open a second PR while one is open (reuse the stable branch).
- Never re-stamp a dateline for a claim it couldn't actually verify.
- Never let a manifest `acknowledged` entry suppress a `CORRECT` or an `ERROR` — acknowledgments silence only human-accepted `FLAG_*` findings, and an expired one (`recheck_after` in the past) must surface again.

## Manifest reference

`docs/automated-routines/skill-fact-check-manifest.json` is repo-local (lists only that repo's units). Shape:

```json
{
  "defaults": { "tier": "monthly" },
  "weekly":  ["<plugin>/<skill>", "..."],
  "monthly": ["<plugin>/<skill>", "..."],
  "never":   ["<plugin>/<skill>", "..."],
  "acknowledged": [
    {
      "unit_id": "<plugin>/<skill>",
      "locator": "unique substring of the flagged text",
      "reason": "why this flag is accepted, not a defect",
      "ack_date": "YYYY-MM-DD",
      "recheck_after": "YYYY-MM-DD"
    }
  ]
}
```

Tiers: **weekly** (≥7 days) for fast-drifting skills (Apple OS/App Store specs, SwiftUI "what's new", SF Symbols, three.js, Blender); **never** for evergreen methodology (session handoff/harvest, emoji commits, changelog, readme badges, GDScript); **monthly** (≥28 days, the default) for everything else. To re-tier a skill, move its `unit_id` between lists — no skill change needed. A `unit_id` not in any list is `monthly`, so a manifest without an explicit `monthly` array still resolves every unit; listing monthly units explicitly makes tiering a deliberate per-skill choice, and Step 1 prints `# DRIFT` lines for untiered, orphaned, or double-listed entries.

**`acknowledged`** (optional) silences flags a human has judged acceptable — the "not wrong", "no vendor-primary source exists", or "won't change" findings that otherwise re-appear every run. Each entry pins a `unit_id` and a `locator` (a unique substring of the flagged text, same idea as a claim's locator), a human `reason`, an `ack_date`, and a `recheck_after` — a date, or `"never"` for a permanently-accepted item. [Step 4](#step-4--reduce--apply-orchestrator) routes a matching flag into the PR's `🔕 Known / acknowledged` section instead of `🚩 Flagged`; once `recheck_after` passes it resurfaces so the acceptance is re-confirmed. Prefer a dated `recheck_after` over `"never"` so a fact accepted only because it's currently undocumented resurfaces if the vendor later documents it. An acknowledgment silences a `FLAG_*` only — never a sourced `CORRECT` or an unverifiable `ERROR`.
