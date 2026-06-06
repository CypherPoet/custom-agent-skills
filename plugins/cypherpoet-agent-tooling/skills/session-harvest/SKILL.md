---
name: session-harvest
description: >
  Use this skill whenever the user says "harvest learnings", "anything
  worth remembering?", "what should I save?", "before I go...", or any
  variation of asking whether there are takeaways from the session —
  including when they're wrapping up a long or complex session. Runs a
  systematic pre-exit sweep of the current conversation for learnings
  worth preserving in memory: surfaces corrections, project context,
  preferences, and references, deduplicates against existing memory, and
  presents findings for the user to approve. Never auto-saves.
---

# Session Harvest

Claude already saves memories during a conversation when something obviously worth keeping comes up. But ad-hoc saving has blind spots — small corrections accumulate without being captured, validated approaches go unrecorded, and project context that felt obvious in the moment evaporates when the session ends. This skill does a deliberate, structured sweep at the end of a session to catch what slipped through.

The goal is to present candidates, not to auto-save. The user decides what's worth keeping.

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

4. **Universal or obvious?** "Test before committing" or "read the error message" aren't memory-worthy — they're general practice, not session-specific insights.

5. **Durable?** Will this matter in a week? A month? Corrections and preferences tend to be durable. A specific bug's details usually aren't, unless the pattern recurs.

6. **Worth saving, or just borderline?** The filters above remove what doesn't belong; this step decides what's worth surfacing *as a recommendation*. Rate each survivor on three axes — **durability** (will it matter next month?), **specificity** (a concrete, reusable rule, or something vague?), and **non-derivability** (absent from code and git?). A candidate strong on all three is **Worth saving**. One that's plausible but weak on any axis — a marginal reference, a mild preference, a lesson that may not recur — is **Borderline**: surface it as optional, not recommended. When you can't decide which tier, it's Borderline.

Most sessions produce a small Worth-saving tier — often empty or a single item. Resist the pull to populate all four categories; a sweep that surfaces one strong memory and nothing else has done its job well.


## Phase 4: Present Findings

Present findings under two value tiers — **Worth saving** first, then **Borderline — optional**. Within each tier, group by memory type under its own subheading; don't mix types under one subheading. A `user` item goes under `### User`, not `### Feedback`, even if it surfaced alongside feedback. Number items sequentially across both tiers so the user can reference them as "1, 3, 5". Skip any tier or type subheading that has no items — including the entire Borderline tier when nothing is marginal.

For each finding, show:
- A proposed title (the memory's `name` field)
- A proposed filename (must match the type of its subheading — a finding under `### User` gets a `user_` prefix)
- A content preview — 2-3 sentences. For Borderline items, add one phrase on *why* it's marginal.

Format like this:

```
## Worth saving

### Feedback (N items)

1. **Title of the learning**
   `feedback_slug.md`
   > Content preview — the rule, why it matters, when to apply it.

### Project (N items)

2. **A project decision**
   `project_slug.md`
   > Content preview here.

## Borderline — optional (low confidence)

### Reference (N items)

3. **A link that helped once**
   `reference_slug.md`
   > Content preview — plus why it's marginal (e.g. "solved one
   > specific bug; may not recur").
```

After presenting, ask:

> Which should I save? Say "all", list numbers (e.g. "1, 3, 5"), "none", or ask me to edit any item first. The Worth-saving items are genuine recommendations; the Borderline ones are surfaced for completeness — skipping them is a fine default.

**When nothing clears the bar** — which is common, not exceptional — say so directly and stop:

> I reviewed the session and didn't find learnings worth persisting that aren't already captured. Your existing memories cover the key points.

**If an existing memory should be updated** rather than a new one created, call that out:

> Item 2 would update your existing memory `feedback_no_bandaids.md` with additional context from this session.


## Phase 5: Verify Accuracy Before Saving

Selection is not verification. The summaries presented in Phase 4 are polished prose, and polished prose can paper over claims that were never actually checked — especially technical facts asserted with confidence. Memory writes are durable: a confidently wrong memory is worse than no memory, because future sessions will trust it.

After the user picks which items to save, but **before writing any file**, audit the concrete factual claims in each selected candidate.

### What to audit

Walk each candidate and list its concrete claims, then categorize each:

- **Session fact** ("X happened in this conversation", "the user said Y") — re-check the transcript.
- **Code / repo fact** ("file X exports Y", "function Z does W") — read the file.
- **External technical fact** ("library X behaves like Y", "browsers fire Z densely") — verify against the actual source: read the code in `node_modules/`, grep the implementation, or check the doc. Do not trust training intuition for claims about specific tool behavior, because that's exactly where polished prose tends to encode confident speculation.
- **Numerical claim** ("rejects roughly 15° of the band") — redo the math, briefly. If it varies with a parameter, say so.
- **Personal / user fact** ("user prefers X") — find the actual quote in the conversation.

The audit should be quick. The point is to surface anything that doesn't hold up, not to belabor it.

### What to do when a claim doesn't hold up

- **Wrong** — correct the memory. Don't ship the false claim.
- **Unverifiable in reasonable time** — soften or drop the unverifiable sentence. Memory writes don't need editorial flourish; they need to be correct. A memory with fewer, more accurate claims is more useful than one with confident-sounding but uncheckable ones.
- **Right but imprecise** — tighten. E.g. "approximately 15°" is fine if the actual range is 14–16°; "exactly 15°" when it varies with input is not.

### Report changes before saving

If the audit produced corrections, briefly tell the user what changed before writing. They may want to see the diff between what they approved and what gets saved.

> Verified all 4 candidates against the code. Two corrections:
> - Item 1: the claim about `material.visible` varying across releases was unverified; replaced with the actual verified behavior (it's consistently ignored).
> - Item 2: tightened "exactly 15°" to "roughly 15° — depends on camera distance".
> Saving now.

If every claim checks out, just save and say so.


## Phase 6: Save Selected Items

For each item the user approves:

### Write the memory file

Use this format:

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

After all items are saved:

> Saved N memories: `filename_1.md`, `filename_2.md`. MEMORY.md has been updated.


## Constraints

- **One concept per file.** If a learning spans multiple concerns, split it into separate memories.
- **Write for amnesia.** Memory content should make sense to a future session with zero context about this conversation. No "as we discussed" or "the issue from earlier."
- **Distill, don't transcribe.** Capture the actionable essence, not a transcript of the conversation. Keep memories concise.
- **Precision over recall.** A low-value memory has a real cost — it dilutes the index and future sessions trust it. When unsure whether something clears the bar, leave it out or mark it Borderline. The sweep's success is the *value* of what it surfaces, not the count.
- **Respect user edits.** If the user modifies a proposed memory before saving, use their version exactly.
