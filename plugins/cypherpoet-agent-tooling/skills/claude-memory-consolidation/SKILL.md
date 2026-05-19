---
name: claude-memory-consolidation
description: >
  Audit and consolidate Claude's per-project auto-memory directory
  (~/.claude/projects/<encoded-cwd>/memory/). Use this skill whenever the user
  says "clean up memory", "consolidate memory", "audit memory", "prune
  memories", "dedupe memory", "tidy my memory", "memory housekeeping", or asks
  to review, optimize, or shrink the project memory system. Also trigger when
  the user complains about stale or duplicated memories, when recent sessions
  surfaced memory references that no longer resolve, or when MEMORY.md is
  approaching the 200-line truncation cap. Produces a severity-tiered audit
  (broken references, likely duplicates, index repair, description drift,
  brevity pressure), waits for per-cluster approval, then applies edits.
  Never modifies memory without explicit confirmation.
---

# Consolidate Memory

Claude saves memories during conversations, but nothing ever prunes them. Over months, a project's memory directory accretes near-duplicates, references to files that have since been renamed, project facts about initiatives that have since shipped, and entries whose `description:` field has drifted away from what the body actually says. The `MEMORY.md` index can also fall out of sync — pointing at deleted files, missing entries for files that exist, or carrying one-line hooks that no longer match the underlying memory.

This skill does a deliberate audit pass over the project's memory directory and proposes consolidations. It is the destructive counterpart to `session-harvest`: where that skill *adds* memories from a conversation, this one *dedupes, repairs, rewrites, and prunes* them.

Surfacing candidates is the point. The skill never edits memory files without the user's explicit, per-cluster approval.


## Phase 1: Locate the memory directory

The project's memory directory lives at:

```
~/.claude/projects/<url-encoded-cwd>/memory/
```

The encoding replaces every `/` in the working directory path with `-` and prepends a leading `-`. For example, the directory for a project at `/Users/alice/code/widgets` becomes `~/.claude/projects/-Users-alice-code-widgets/memory/`.

In practice you don't need to derive this from scratch — the path is usually visible from existing context:

1. **If the user named an explicit path** (e.g., "audit the memory at `/tmp/fixture-memory/`"), use that one. This is the right way to run the skill against a test fixture or another project's memory directory.
2. Otherwise, the auto-memory system injects the current `MEMORY.md` into the conversation. The header for that injection includes the absolute path. Use it directly.
3. If that's not visible either, run `pwd` to get the working directory and construct the encoded path.

If the memory directory doesn't exist, or exists but contains only an empty `MEMORY.md`, report that there's nothing to consolidate and stop. This isn't an error — fresh projects start empty.


## Phase 2: Inventory and parse

Read `MEMORY.md` and every memory file in the directory.

For each memory file, parse the YAML frontmatter into `{name, description, type, file_path}` and keep the body text. Capture:

- Total file count, and a breakdown by `type` (`feedback`, `project`, `user`, `reference`).
- `MEMORY.md` line count.
- Body length for each file (word count is fine).
- Modification times — older files are more likely to have decayed.

Build a single in-memory inventory keyed by filename. Every subsequent check operates on this inventory rather than re-reading files. This baseline also drives the report's summary line.


## Phase 3: Run audit checks

Run six checks against the inventory. Each one produces a list of *candidates* — not actions. Candidates carry a severity that controls how they're presented later.

The point of these checks is to surface things a careful human would notice on a slow re-read. They are not infallible heuristics, and several of them deliberately under-trigger to avoid pushing the user into deleting memory that still has value.

### 🔴 Broken references

Memories sometimes name specific files, functions, command flags, or URLs. When those things move or get deleted, the memory becomes a pointer to nothing.

For each memory body, extract concrete references:

- File paths (`src/auth/middleware.ts`, `scripts/build.sh`)
- Symbols that look like function or identifier names in code voice
- Command-line flags (`--no-verify`, `-uall`)
- URLs

For each reference, verify it resolves in the current working directory: Glob for file paths, Grep for symbols, `curl -I` for URLs. Failures become 🔴 candidates with the proposed action "delete this memory" *or* "update this memory's reference to <new location>" if you can find an obvious replacement.

Important: a broken reference does not always mean the memory is wrong. A `reference` memory documenting "we used the legacy `--full-page` flag in the old playwright CLI" is intentionally historical. Surface the finding, but lean toward "ask the user" rather than "recommend deletion."

### 🔴 Dead index lines

Every entry in `MEMORY.md` should point to a real file whose `name:` frontmatter roughly matches the line's hook.

For each `MEMORY.md` entry:

- The target file exists. If not → 🔴 candidate "remove dead line."
- The target file's `name:` matches the line's title (allowing for minor cosmetic differences). If not → 🔴 candidate "fix line to match file."

This check is unambiguous — these are real errors, not judgment calls.

### 🟡 Likely duplicates

Memories about the same topic accrete over time, especially `feedback` entries where the same correction is captured twice in slightly different words.

Within each `type`, compare descriptions and bodies pairwise. A pair is a duplicate candidate when:

- The descriptions overlap heavily (same nouns and verbs in different word order)
- The bodies make the same load-bearing claim, even if the framing differs

Borderline cases are 💡 suggestions, not 🟡 warnings. Two memories that share a topic but make distinct points — one about *when* a rule applies and one about *why* — are not duplicates; surface them only if the user is actively trying to shrink the directory.

For each duplicate candidate, propose a merged memory that preserves all unique signal from both originals. Don't drop information just to shorten.

### 🟡 Description-frontmatter drift

The `description:` field is what helps a future session decide whether the memory is relevant. When the body grows or the topic shifts, the description can fall behind.

For each memory, judge whether the `description:` would help a future Claude find it. Flag as 🟡 when:

- The description is generic ("notes on testing") and the body has a specific load-bearing claim
- The description references a scope that doesn't match the body
- The description lacks any when-to-use signal — it summarizes the content but not the trigger

Propose a rewritten description in the candidate. Don't touch the body.

### 💡 Orphan files

Memory files that exist on disk but aren't listed in `MEMORY.md` are invisible to future sessions.

For each file not in the index → 💡 candidate "add to MEMORY.md" with a proposed one-line hook derived from the file's frontmatter `description:`.

### 💡 Brevity pressure

`MEMORY.md` is truncated after roughly 200 lines, so very long indexes start to silently lose entries. Long memory bodies also burn context when loaded.

Trigger this check when *any* of:

- `MEMORY.md` is ≥ 150 lines (75% of the cap — strong nudge at 180+)
- Any individual body is > 300 words
- Total memory file count is > 50

If none of these hold, skip the check entirely — current real-world projects sit comfortably under these thresholds, and surfacing brevity findings on a small directory is just noise.

When triggered, propose targeted condensations: bodies that could lose redundant prose without losing signal, `MEMORY.md` hooks that could shed words, two short related memories that could merge into one.

This is the only check that should produce suggestions for an otherwise-healthy directory. When in doubt, don't fire it.


## Phase 4: Present the report

Group findings by severity, then by check. Number items sequentially across the whole report so the user can reference them as "1, 3, 5".

Use this shape:

```
# Memory Audit — <project name>

**Inventory:** 47 memories (28 feedback, 14 project, 3 user, 2 reference)  •  MEMORY.md: 53 lines

**Summary:** 2 errors, 4 warnings, 3 suggestions

## 🔴 Errors

### Broken references
1. **feedback_no_cd_chaining.md** references `scripts/lint.sh` which no longer exists
   Proposed: delete this memory, or update reference if it moved.

### Dead index lines
2. **MEMORY.md line 12** points to `feedback_old_topic.md` which doesn't exist on disk
   Proposed: remove the line.

## 🟡 Warnings

### Likely duplicates
3. **feedback_test_isolation.md** and **feedback_no_mocked_db.md** make overlapping claims
   Proposed merge: <show the merged memory's frontmatter + body>

### Description drift
4. **project_auth_rewrite.md** description says "auth notes" but body covers session token storage compliance
   Proposed description: "Auth rewrite is driven by legal/compliance on session token storage, not tech-debt cleanup"

## 💡 Suggestions

### Orphan files
5. **feedback_writing_clearly.md** is on disk but missing from MEMORY.md
   Proposed entry: `- [feedback_writing_clearly.md](feedback_writing_clearly.md) — Default to no comments; explain why, not what`

### Brevity pressure
6. **project_migration_history.md** is 412 words; the second half restates the first
   Proposed condensation: <show the shorter version>
```

Skip any heading whose section is empty — don't print "Errors: none." The summary line already says it.

If nothing was found, say so plainly:

> Memory looks clean. Nothing to consolidate.

After presenting the report, ask:

> Which of these should I apply? You can say "all", list numbers (e.g. "1, 3, 5"), "skip errors / warnings / suggestions", "edit N" to revise a proposal before applying, or "none".


## Phase 5: Apply approved changes

Apply changes in this order — it matters because some operations invalidate others:

1. **Merges first.** Write the new consolidated memory file, then delete the originals. Do this before any other deletes so you don't accidentally remove a file the merge depended on.
2. **Edits second.** Description rewrites and body condensations. Read-modify-write the affected files.
3. **Plain deletes third.** Memories the user approved for outright removal.
4. **Index repair last.** Rebuild `MEMORY.md` from the filesystem ground truth rather than patching individual lines. After every other change has landed, list the directory, read each file's frontmatter, and write a fresh `MEMORY.md`:

   ```
   # Memory Index
   
   - [filename.md](filename.md) — <hook from description or proposed one-liner>
   ```

   This guarantees the index matches reality after the audit, even if intermediate steps missed something.

After applying, confirm what changed:

> Applied 6 changes. Memory now has 42 files (was 47); MEMORY.md is 48 lines (was 53).
> - Merged: `feedback_test_isolation.md` + `feedback_no_mocked_db.md` → `feedback_real_db_in_tests.md`
> - Updated description: `project_auth_rewrite.md`
> - Added index entry: `feedback_writing_clearly.md`
> - …


## Constraints

- **Never auto-modify.** Every change requires the user's explicit approval. The skill is read-only until Phase 5 begins.
- **When in doubt, leave it alone.** Borderline duplicates and ambiguous staleness should be flagged as 💡 suggestions, not 🟡 warnings. Two slightly-overlapping memories are cheaper than an incorrect merge.
- **Historical context is legitimate.** A `reference` memory documenting a deprecated tool or a past pivot is not "stale" — it's a deliberate record. Only delete reference memories the user confirms are obsolete.
- **Updates over deletes.** When merging, write a single consolidated memory that preserves every unique claim. Don't drop signal to shorten.
- **Conservative brevity.** Don't surface brevity findings unless the directory has crossed the 150-line / 50-file / 300-word thresholds. The system tolerates 200 lines; consolidation pressure belongs in the upper half of that range.
- **Respect user edits.** If the user asks to revise a proposal before applying ("edit 4"), use their version exactly — don't second-guess.
- **One pass per invocation.** If the user wants another round after applying changes, they'll ask. Don't loop automatically.
