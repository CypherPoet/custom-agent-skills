---
name: session-harvest
description: >
  Use this skill whenever the user says "harvest learnings", "anything
  worth remembering?", "what should I save?", "before I go...", or any
  variation of asking whether there are takeaways from the session —
  including when they're wrapping up a long or complex session. Runs a
  systematic pre-exit sweep of the current conversation for learnings
  worth preserving: surfaces corrections, project context, preferences,
  and references, and routes each to its right home: a memory, or (for a
  real project convention) a suggested CLAUDE.md/AGENTS.md, docs, or hook
  edit. Deduplicates against existing memory and presents findings for
  approval. Never auto-saves or auto-edits.
---

# Session Harvest

Claude already saves memories during a conversation when something obviously worth keeping comes up. But ad-hoc saving has blind spots — small corrections accumulate without being captured, validated approaches go unrecorded, and project context that felt obvious in the moment evaporates when the session ends. This skill does a deliberate, structured sweep at the end of a session to catch what slipped through.

The goal is to present candidates, not to auto-save. The user decides what's worth keeping, and where it belongs. Not everything worth remembering belongs in memory. A project convention, decision, or rule usually belongs in the repo (a `CLAUDE.md`/`AGENTS.md` line, project docs, or a hook), where it is versioned, reviewed, and visible to teammates and other agents rather than locked in one assistant's private notes. A learning about one of the user's *own agent skills* belongs in that skill's repo — the sibling [skill-harvest](../skill-harvest/SKILL.md) skill ships those. Routing each finding to its right home is part of the sweep's job.

Most sessions yield little worth keeping — often nothing, and that's the normal, healthy outcome of a sweep, not a failure of it. A low-value memory has a real cost: it dilutes the index and future sessions *trust* it. So bias toward precision over recall — when a candidate doesn't clearly clear the bar, leave it out. A near-constant four or five findings every session is the tell that you're matching categories instead of judging value. Calibrate to the conversation, not to the list of categories below.


## Phase 1: Load Existing Memory

Before scanning the conversation, understand what's already been captured so you don't suggest duplicates.

1. Read `MEMORY.md` from the current project's memory directory.
2. Read each memory file listed in the index — skim for titles, types, and key content.
3. Build a mental inventory: what topics, corrections, preferences, and references are already on file.

If no memory directory or `MEMORY.md` exists yet, note that everything found will be new.


## Phase 2: Scan the Conversation

Review the full conversation for moments that clear the bar — information specific and durable enough that a future session would genuinely benefit from it. The four categories below are a checklist of *where* to look, not a quota to fill: a session might surface several items in one category and nothing in the others, or nothing at all. Match the conversation, not the list.

### Feedback (`feedback`)

The highest-value finds — corrections the user gave, approaches that worked unusually well, and mistakes whose root cause was identified. These are easy to miss when they happen casually mid-task, and they're exactly the kind of thing that makes the next session smoother.

**What to look for:**

*Corrections and preferences*
- Direct corrections: "no, do X instead", "stop doing Y", "that's not right"
- Preference statements: "I prefer...", "always use...", "never do..."
- Frustration followed by explanation: the user pushed back and then explained the right approach
- Explicit endorsement of a non-obvious, reusable choice the user would want repeated — ideally with a reason ("yes — always lift the query out of the component like that"). Routine sign-off ("perfect", "looks good", "ship it") is *not* an endorsement, and neither is the mere absence of pushback. Skip both.

*Validated approaches*
- A technique that resolved a stubborn issue
- The user praising a specific approach or workflow
- An approach that succeeded after alternatives were tried and failed

*Mistakes and lessons*
- An error that wasted time before being identified
- A debugging dead-end that could have been avoided
- A misunderstanding about the codebase or framework that was corrected

**What to capture:** The rule or pattern, why it matters (the incident or reasoning behind it), and when to apply it next time.

### Project Context (`project`)

Decisions, goals, and status information that future sessions need but that aren't captured in code or git history.

**What to look for:**
- Architecture decisions with rationale: "we chose X because Y"
- Deadlines, milestones, or freezes mentioned
- Current status updates: what's done, what's next, what's blocked
- Stakeholder context: who needs what, who's responsible for what
- Plans for future work: "next session we should..."

**What to capture:** The fact or decision, why it was made, and how it should shape future work. Convert relative dates ("next Thursday") to absolute dates.

### User Identity and Preferences (`user`)

Stable traits about the user that calibrate how Claude should work with them across sessions.

**What to look for:**
- Role or expertise statements: "I'm a designer", "I've been writing Go for 10 years"
- Domain knowledge signals: deep familiarity with some areas, new to others
- Communication preferences: verbosity, tone, whether they want explanations or just results
- Working style: "show me the plan first", "just do it and I'll review"

**What to capture:** The trait and how it should influence Claude's behavior.

### External References (`reference`)

Durable, reusable infrastructure the user returns to across tasks — not every link that happened to help once.

**What to look for:**
- A team wiki, dashboard, or canonical doc the user points to as the place for a recurring class of work
- A tool or service the user relies on regularly
- An API endpoint or internal resource referenced as a standing fixture

A page, article, or StackOverflow answer that solved one specific problem this session is usually ephemeral — it belongs in the Borderline tier at most (see Phase 3), not as a recommended save.

**What to capture:** The reference and why it's useful — what recurring kind of task it helps with.


## Phase 3: Filter and Deduplicate

For each candidate, apply these filters:

1. **Already captured?** Compare against the existing memory inventory from Phase 1. Check both titles and content — a memory titled "No cd chaining" already covers a candidate about "use absolute paths instead of cd &&". If an existing memory covers the same ground but could be strengthened with new detail, note that as an update rather than a new memory.

2. **Ephemeral?** Skip task-specific details that don't generalize. "We fixed the off-by-one error on line 47 of parser.ts" is not a learning unless it reveals a recurring pattern.

3. **Derivable from code or git?** The codebase records what was built. Git history records what changed and when. Memory is for things that live outside those records — the *why* behind decisions, preferences that shaped choices, context that motivated the work.

4. **Better off committed than remembered?** Filter #3 asks whether the fact is *already* in the repo. This asks what it misses: should it *be* in the repo? Memory is private to one assistant, unversioned, unreviewed, and invisible to teammates and other agents, so it is the wrong home for a *project artifact*. A convention, an architecture decision, a build/test/run command, a where-things-go rule, or a codebase-tied gotcha (anything a new contributor or a different agent would need to work on the project correctly) belongs in a committed file, not memory. Route it by kind:
   - An enforceable "always X / never Y" rule a check could verify: a **hook**, which runs automatically and cannot be forgotten.
   - A convention, decision, command, or gotcha that fits in a line or two: **`CLAUDE.md` / `AGENTS.md`**.
   - Anything longer, such as reference material, schemas, runbooks, or design rationale: a **`docs/`** page, linked from `CLAUDE.md` rather than inlined.

   Lean on one test: would a brand-new contributor, or a different agent with no memory of you, need this to work on the project correctly? If yes, route it to a committed home. If it is about how Claude should behave with *this* user, or about cross-session context that is not a project fact (user identity and preferences, a recurring false-positive finding, the user's machine quirks), keep it as a memory candidate.

   When a candidate routes to a committed home, stop treating it as a memory. Carry it into Phase 4 as a **suggested edit to the named file**. Suggest it; do not silently make it. Committed files are shared and usually go through review, so the user (or a PR) owns that change, whereas you can write a memory directly on approval. A convention occasionally earns both a one-line `CLAUDE.md` rule and a deeper `docs/` page it links to; say so when it does.

5. **Belongs in one of the user's own skills?** If the learning is domain knowledge a personal skill or plugin teaches — stale guidance the session fought, a gotcha the skill should have warned about, a sequence it should encode — its home is that skill's repo, not memory. Flag it as a skill-harvest candidate and carry it into Phase 4 under its own section. Don't verify or draft the skill edit here; [skill-harvest](../skill-harvest/SKILL.md) owns that, and runs only if the user opts in.

6. **Universal or obvious?** "Test before committing" or "read the error message" aren't memory-worthy — they're general practice, not session-specific insights.

7. **Durable?** Will this matter in a week? A month? Corrections and preferences tend to be durable. A specific bug's details usually aren't, unless the pattern recurs.

8. **Worth saving, or just borderline?** The filters above remove what doesn't belong (and route project artifacts and skill candidates to their repos); this step decides which *memory* candidates are worth surfacing *as a recommendation*. Rate each survivor on three axes — **durability** (will it matter next month?), **specificity** (a concrete, reusable rule, or something vague?), and **non-derivability** (absent from code and git?). A candidate strong on all three is **Worth saving**. One that's plausible but weak on any axis — a marginal reference, a mild preference, a lesson that may not recur — is **Borderline**: surface it as optional, not recommended. When you can't decide which tier, it's Borderline.

Most sessions produce a small Worth-saving tier — often empty or a single item. Resist the pull to populate all four categories; a sweep that surfaces one strong memory and nothing else has done its job well.


## Phase 4: Present Findings

Findings have three destinations: **committed artifacts** (the repo), **skill improvements** (the user's own skill repos, via skill-harvest), and **memory**. Lead with the committed-artifact and skill suggestions, since misfiling those into private memory is the trap this guards against, then present the memory tiers.

For **committed artifacts**, present each routed candidate under a `## Belongs in the repo (not memory)` section: name the target file, show the line or section you'd add, and say in a phrase why it belongs in the repo rather than memory.

For **skill improvements**, present each flagged candidate under a `## Belongs in a skill (skill-harvest)` section: name the target skill and state the learning and its evidence in a line or two. These are hand-off candidates, not drafted edits — approving one hands it to skill-harvest, which starts from the flagged candidates rather than re-sweeping the session.

For **memory**, present findings under two value tiers: **Worth saving** first, then **Borderline — optional**. Within each tier, group by memory type under its own subheading; don't mix types under one subheading. A `user` item goes under `### User`, not `### Feedback`, even if it surfaced alongside feedback. Number items sequentially across *all* sections (committed, skill, and memory) so the user can reference them as "1, 3, 5". Skip any empty section, tier, or subheading: the committed-artifacts or skill section when nothing routes there, the Borderline tier when nothing is marginal.

For each finding, show:
- A proposed title (the memory's `name` field)
- A proposed filename (must match the type of its subheading — a finding under `### User` gets a `user_` prefix)
- A content preview — 2-3 sentences. For Borderline items, add one phrase on *why* it's marginal.

Format like this:

```
## Belongs in the repo (not memory)

1. **A project convention better committed than remembered**
   → suggest adding to `AGENTS.md` (or `docs/<topic>.md` if it's more than a line)
   > The convention, and the exact line or section you'd add. One phrase on why
   > it belongs in the repo, not memory.

## Belongs in a skill (skill-harvest)

2. **Stale guidance in one of your skills**
   → target: `<plugin>/<skill>` — approve to hand off to skill-harvest
   > The learning and what happened this session that exposed it.

## Worth saving

### Feedback (N items)

3. **Title of the learning**
   `feedback_slug.md`
   > Content preview — the rule, why it matters, when to apply it.

### Project (N items)

4. **A project decision**
   `project_slug.md`
   > Content preview here.

## Borderline — optional (low confidence)

### Reference (N items)

5. **A link that helped once**
   `reference_slug.md`
   > Content preview — plus why it's marginal (e.g. "solved one
   > specific bug; may not recur").
```

After presenting, ask:

> Which should I act on? Say "all", list numbers (e.g. "1, 3, 5"), "none", or ask me to edit any item first. For repo items I'll make the suggested edit (or open a PR where that's the norm) rather than write a memory; for skill items I'll hand them to skill-harvest; for memory items I'll save the file. The repo, skill, and Worth-saving items are genuine recommendations. The Borderline ones are surfaced for completeness, so skipping them is a fine default.

**When nothing clears the bar** — which is common, not exceptional — say so directly and stop:

> I reviewed the session and didn't find learnings worth persisting that aren't already captured. Your existing memories cover the key points.

**If an existing memory should be updated** rather than a new one created, call that out:

> Item 2 would update your existing memory `feedback_no_bandaids.md` with additional context from this session.


## Phase 5: Verify Accuracy Before Saving

Selection is not verification. The summaries presented in Phase 4 are polished prose, and polished prose can paper over claims that were never actually checked — especially technical facts asserted with confidence. Memory writes are durable: a confidently wrong memory is worse than no memory, because future sessions will trust it. A routed repo edit deserves the same audit, with even more at stake: a wrong claim committed to `CLAUDE.md` or `docs/` misleads every contributor and is harder to retract than a private memory.

After the user picks which items to act on, but **before writing or editing any file**, audit the concrete factual claims in each selected candidate, whether it is headed for memory or the repo.

### What to audit

Walk each candidate and list its concrete claims, then categorize each:

- **Session fact** ("X happened in this conversation", "the user said Y") — re-check the transcript.
- **Code / repo fact** ("file X exports Y", "function Z does W") — read the file.
- **External technical fact** ("library X behaves like Y", "browsers fire Z densely") — verify against the actual source: read the code in `node_modules/`, grep the implementation, or check the doc. Do not trust training intuition for claims about specific tool behavior, because that's exactly where polished prose tends to encode confident speculation.
- **Numerical claim** ("rejects roughly 15° of the band") — redo the math, briefly. If it varies with a parameter, say so.
- **Personal / user fact** ("user prefers X") — find the actual quote in the conversation.

The audit should be quick. The point is to surface anything that doesn't hold up, not to belabor it.

### What to do when a claim doesn't hold up

- **Wrong** — correct the memory or repo edit. Don't ship the false claim.
- **Unverifiable in reasonable time** — soften or drop the unverifiable sentence. Memory writes don't need editorial flourish; they need to be correct. A memory with fewer, more accurate claims is more useful than one with confident-sounding but uncheckable ones.
- **Right but imprecise** — tighten. E.g. "approximately 15°" is fine if the actual range is 14–16°; "exactly 15°" when it varies with input is not.

### Report changes before saving

If the audit produced corrections, briefly tell the user what changed before writing. They may want to see the diff between what they approved and what gets saved.

> Verified all 4 candidates against the code. Two corrections:
> - Item 1: the claim about `material.visible` varying across releases was unverified; replaced with the actual verified behavior (it's consistently ignored).
> - Item 2: tightened "exactly 15°" to "roughly 15° — depends on camera distance".
> Saving now.

If every claim checks out, just save and say so.


## Phase 6: Apply Selected Items

Apply each approved item to the home it was routed to.

### Repo items (committed artifacts)

Make the suggested change in the named file: add the `CLAUDE.md`/`AGENTS.md` line, edit the `docs/` page, or set up the hook. Two cautions, mirroring the never-auto-save rule: never edit a committed file without the user's approval of *that specific edit*, and where the repo's norm is review, propose the change on a branch or PR rather than committing to the default branch. Keep `CLAUDE.md`/`AGENTS.md` lean: a one-line imperative that links to deeper `docs/`, not a transplanted essay.

### Skill items (hand-off)

Invoke [skill-harvest](../skill-harvest/SKILL.md) with the approved candidates as its input. It picks up at its mapping phase — the sweep is already done — and owns claim verification, per-item approval of the actual edits, and shipping as PRs.

### Write the memory file

For each approved memory item, use this format:

```markdown
---
name: Human-Readable Title
description: One-line summary — this appears in the MEMORY.md index
type: feedback|project|user|reference
---

The learning, distilled to its essence. Written for a future Claude session
that has no context about this conversation.

**Why:** What happened that makes this worth remembering.

**How to apply:** Concrete guidance for future sessions.
```

The `**Why:**` and `**How to apply:**` sections are important for `feedback` and `project` types — they give future sessions the reasoning needed to apply the learning intelligently. For `user` and `reference` types, use a straightforward description without those sections.

### Filename convention

`<type>_<snake_case_slug>.md` — e.g., `feedback_no_bandaid_fixes.md`, `project_auth_rewrite_decision.md`

### Update MEMORY.md

Append a new entry for each saved memory:

```
- [filename.md](filename.md) — One-line description
```

If the memory directory or `MEMORY.md` doesn't exist yet, create them.

### Confirm

After applying all approved items, report what changed in each home you touched. Skip a line for a home nothing went to, so a memory-only run still reads cleanly.

> **Repo:** added a `CLAUDE.md` line; created `docs/foo.md`.
> **Skills:** handed 1 candidate to skill-harvest (PR opened on `<repo>`).
> **Memory:** saved `feedback_x.md`, `project_y.md`; updated MEMORY.md.


## Constraints

- **One concept per file.** If a learning spans multiple concerns, split it into separate memories.
- **Write for amnesia.** Memory content should make sense to a future session with zero context about this conversation. No "as we discussed" or "the issue from earlier."
- **Distill, don't transcribe.** Capture the actionable essence, not a transcript of the conversation. Keep memories concise.
- **Precision over recall.** A low-value memory has a real cost — it dilutes the index and future sessions trust it. When unsure whether something clears the bar, leave it out or mark it Borderline. The sweep's success is the *value* of what it surfaces, not the count.
- **Respect user edits.** If the user modifies a proposed memory before saving, use their version exactly.
- **Right home before memory.** A project convention, decision, command, or rule usually belongs in a committed artifact (a hook, `CLAUDE.md`/`AGENTS.md`, or `docs/`), and a learning about one of the user's own skills belongs in that skill's repo via skill-harvest — not memory. Memory is for how Claude should work with *this* user and for cross-session context that isn't a project fact. Suggest the committed edit or hand-off; never act without approval.
