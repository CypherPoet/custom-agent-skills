---
name: session-harvest
description: >
  Systematic pre-exit sweep of the current conversation for learnings worth
  preserving in memory. Use this skill whenever the user says "harvest
  learnings", "anything worth remembering?", "what should I save?", "before I
  go...", or any variation of asking whether there are takeaways from the
  session — including when they're wrapping up a long or complex session. The
  skill surfaces corrections, project context, preferences, and references,
  deduplicates against existing memory, and presents findings for the user to
  approve. It never auto-saves.
---

# Session Harvest

Claude already saves memories during a conversation when something obviously worth keeping comes up. But ad-hoc saving has blind spots — small corrections accumulate without being captured, validated approaches go unrecorded, and project context that felt obvious in the moment evaporates when the session ends. This skill does a deliberate, structured sweep at the end of a session to catch what slipped through.

The goal is to present candidates, not to auto-save. The user decides what's worth keeping.


## Phase 1: Load Existing Memory

Before scanning the conversation, understand what's already been captured so you don't suggest duplicates.

1. Read `MEMORY.md` from the current project's memory directory.
2. Read each memory file listed in the index — skim for titles, types, and key content.
3. Build a mental inventory: what topics, corrections, preferences, and references are already on file.

If no memory directory or `MEMORY.md` exists yet, note that everything found will be new.


## Phase 2: Scan the Conversation

Review the full conversation looking for moments that carry information useful to future sessions. Focus on these categories:

### Feedback (`feedback`)

The highest-value finds — corrections the user gave, approaches that worked unusually well, and mistakes whose root cause was identified. These are easy to miss when they happen casually mid-task, and they're exactly the kind of thing that makes the next session smoother.

**What to look for:**

*Corrections and preferences*
- Direct corrections: "no, do X instead", "stop doing Y", "that's not right"
- Preference statements: "I prefer...", "always use...", "never do..."
- Frustration followed by explanation: the user pushed back and then explained the right approach
- Positive confirmation of a non-obvious choice: "yes, exactly", "perfect — keep doing that", accepting an unusual approach without pushback

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

URLs, tools, documentation, or services that were useful during the session and would be useful again.

**What to look for:**
- Documentation pages that solved a problem
- Tools or services the user relies on
- Tutorials, articles, or repositories mentioned as useful
- API endpoints or dashboards referenced

**What to capture:** The reference and why it's useful — what kind of task it helps with.


## Phase 3: Filter and Deduplicate

For each candidate, apply these filters:

1. **Already captured?** Compare against the existing memory inventory from Phase 1. Check both titles and content — a memory titled "No cd chaining" already covers a candidate about "use absolute paths instead of cd &&". If an existing memory covers the same ground but could be strengthened with new detail, note that as an update rather than a new memory.

2. **Ephemeral?** Skip task-specific details that don't generalize. "We fixed the off-by-one error on line 47 of parser.ts" is not a learning unless it reveals a recurring pattern.

3. **Derivable from code or git?** The codebase records what was built. Git history records what changed and when. Memory is for things that live outside those records — the *why* behind decisions, preferences that shaped choices, context that motivated the work.

4. **Universal or obvious?** "Test before committing" or "read the error message" aren't memory-worthy — they're general practice, not session-specific insights.

5. **Durable?** Will this matter in a week? A month? Corrections and preferences tend to be durable. A specific bug's details usually aren't, unless the pattern recurs.


## Phase 4: Present Findings

Group surviving candidates by memory type. Each type that has findings gets its own heading — don't mix types under the same heading. A `user` type item goes under `### User`, not under `### Feedback`, even if it was discovered alongside feedback items.

For each finding, show:
- A proposed title (what you'd use as the memory's `name` field)
- A proposed filename (must match the type in the heading — a finding under `### User` gets a `user_` prefix)
- A content preview — 2-3 sentences summarizing what would be saved

Format like this:

```
### Feedback (N items)

1. **Title of the learning**
   `feedback_slug.md`
   > Content preview summarizing what would be saved — the rule,
   > why it matters, and when to apply it.

### User (N items)

2. **A user trait or preference**
   `user_slug.md`
   > Content preview here.

### Project (N items)

3. **A project decision**
   `project_slug.md`
   > Content preview here.
```

Number items sequentially across all groups so the user can reference them easily. Only include headings for types that have findings — skip empty categories.

After presenting, ask:

> Which of these should I save? You can say "all", list numbers (e.g. "1, 3, 5"), "none", or ask me to edit any item before saving.

**If no findings survive filtering**, say so directly:

> I reviewed the session and didn't find learnings that aren't already captured or worth persisting. Your existing memories cover the key points.

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
- **Respect user edits.** If the user modifies a proposed memory before saving, use their version exactly.
