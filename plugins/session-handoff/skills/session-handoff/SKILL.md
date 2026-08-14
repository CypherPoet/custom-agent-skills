---
name: session-handoff
description: Use when the user says "create handoff", "save state", "I need to pause", or "context is getting full", and when resuming — "load handoff", "continue where we left off". Also tidies the handoffs directory ("clean up / prune / retire handoffs"). Writes a structured handoff document so a fresh agent can pick up long-running work, and retires completed or superseded handoffs.
---

# Handoff

Creates structured handoff documents so a fresh AI agent can continue long-running work with the original context, decisions, and next steps intact.

The generated document is ordered for the **resuming agent**, not the author — the load-bearing instructions (🎯 Next Action, Important Context, Pending Work) sit near the top, and "what already shipped" is at the bottom because it's reference data once a session is over.

## Reference, don't duplicate

A handoff is connective tissue between sessions, not a re-write of every artifact the work touched. When something is already captured in a PRD, a session plan (`~/.claude/plans/`), an ADR, a design doc, a Linear/Jira/GitHub issue, a PR description, or a commit message — **link to it by path or URL** instead of restating it. Capture only what those artifacts don't already say: the in-flight state, the gotchas, the next concrete step.

Restating ages badly (the canonical artifact updates, the handoff doesn't) and creates two sources of truth. The 📚 Source Artifacts section near the top of the document is where those links live; the rest of the body assumes the resuming agent has them open.

## Mode Selection

**Creating a handoff?** User wants to save current state or pause work — follow the CREATE workflow below.

**Resuming from a handoff?** User wants to continue previous work or mentions an existing handoff — follow the RESUME workflow below.

**Cleaning up old handoffs?** User wants to retire completed or superseded handoffs (e.g. "clean up handoffs", "prune old handoffs") — follow the CLEANUP workflow below.

## CREATE Workflow

Pin down the next-session focus first — the single outcome the resuming agent should drive toward (use the skill's invocation argument as that focus if one was given). It's the lens for the whole document. Then scaffold:

```bash
python3 scripts/create_handoff.py [task-slug]   # add --continues-from <file> to chain
```

**Write the handoff into the tree where the work lives, not where your shell happens to sit.** A session often keeps its cwd in the main checkout while editing worktree files by absolute path — and a handoff written to the main checkout is invisible to the next session that opens the worktree. Resolve the project root from the directory of the files this session changed (`git -C <that-dir> rev-parse --show-toplevel` — returns the worktree root inside a worktree, the repo root otherwise) and pass it via `--project` whenever it differs from your cwd.

Fill the 🎯 **Next Action** line first — it's the single most load-bearing field; a triaging agent may read only that line. Capture deltas and non-obvious context, not restatements of linked artifacts ([Reference, don't duplicate](#reference-dont-duplicate)). Then validate:

```bash
python3 scripts/validate_handoff.py <handoff-file>   # verdict: READY / NEEDS_WORK / BLOCKED (runs the secret scan)
```

The full step-by-step — focus-setting, the session-plan confirmation, the prioritized fill order, and validation verdicts — lives in [references/create-workflow.md](references/create-workflow.md). Read it before authoring.

## RESUME Workflow

```bash
python3 scripts/list_handoffs.py                    # find handoffs
python3 scripts/check_staleness.py <handoff-file>   # FRESH → VERY_STALE, plus drift signals
```

Read by triage, not cover to cover: the 🎯 **Next Action** line is the load-bearing instruction, and the 📚 Source Artifacts it links are assumed open. **Before acting, verify the handoff's assumptions still hold** — right project and branch, referenced files still exist, blockers not already resolved. Treat missing files or substantial branch divergence as a stop-and-reassess signal, not a green light. Then execute the Next Action.

The full step-by-step — the read strategy, the verify-context red flags, and when to chain a new handoff rather than edit the consumed one — lives in [references/resume-workflow.md](references/resume-workflow.md). Read it before resuming.

## CLEANUP Workflow

Handoffs accumulate over time. When work has moved on, retire the completed and superseded ones. Start with the read-only detector:

```bash
python3 scripts/find_cleanup_candidates.py
```

It flags 🔴 superseded + complete handoffs to retire — a later handoff `--continues-from` them and they carry no open TODOs — and lists ⚠️ superseded-but-incomplete ones to review. **Supersession is the only trigger; staleness/age is not** — an old but unsuperseded record can be the only trace of a decision's rationale, so it's kept. Present candidates and remove only with explicit per-item approval (`git rm` for tracked, `trash` for untracked); never auto-run this workflow.

The full procedure — candidate tiers, the approval gate, and the removal mechanics — lives in [references/cleanup-workflow.md](references/cleanup-workflow.md). Read it before running a cleanup.

## Handoff Chaining

For long-running projects, chain handoffs together to maintain context lineage:

```
handoff-1.md (initial work)
    ↓
handoff-2.md --continues-from handoff-1.md
    ↓
handoff-3.md --continues-from handoff-2.md
```

Each handoff in the chain:
- Links to its predecessor.
- Can mark older handoffs as superseded.
- Documents only the current session's deltas — relies on the predecessor for stable context (architecture, long-running decisions).

When resuming from a chain, read the most recent handoff first, then reference predecessors as needed.

## Unattended Loops

When a handoff → compact → resume cycle runs without a human watching (`/loop`, a scheduled task), the two known loop-killers are permission prompts and transient API drops. Before the loop starts, verify that every step it performs — compaction, git commands, script execution — is allowed without prompting in the session's permission mode; a `/compact` that stalls on an approval dialog silently ends the run. If a step will prompt, say so up front so the user can pre-approve it, rather than letting the loop discover it mid-flight.

## Storage Location

Handoffs are stored in: `.agents/handoffs/`

This location is **host-neutral on purpose.** A handoff is a shared project artifact, not host-private config, so it doesn't belong in any single agent's directory (`.claude/`, `.codex/`, …) — keeping it neutral is what lets a session in one agent resume a handoff another agent wrote. The scripts also **still read** the legacy `.claude/handoffs/` location, so handoffs created before this change keep resolving and chaining; nothing needs migrating, though you can `git mv` them into `.agents/handoffs/` if you want everything in one place. To force a different directory, set the `HANDOFF_DIR` env var or pass `--dir` to `create_handoff.py` — keep an override inside the (git) project, since staleness and validation derive the project root from the handoff's own location.

Whether handoffs are tracked in git, gitignored, or committed is a repo/user decision — not this skill's concern. Its job stops at getting the file into `.agents/handoffs/` at the right project root; leave `.gitignore` entries and commit timing to the user's own conventions, and don't ask about or nudge toward either. The `validate_handoff.py` secret scan still runs regardless, since a handoff can end up in git with no explicit action from anyone (e.g. no `.gitignore` entry present), and secrets shouldn't be written into a shared project directory in the first place.

Naming convention: `YYYY-MM-DD-HHMMSS-[slug].md`

Example: `2024-01-15-143022-implementing-auth.md`

## Resources

### scripts/

| Script | Purpose |
|--------|---------|
| `create_handoff.py [slug] [--continues-from <file>] [--project <root>]` | Generate new handoff with smart scaffolding; `--project` targets the tree the work lives in when it isn't the cwd |
| `list_handoffs.py [path]` | List available handoffs in a project |
| `validate_handoff.py <file>` | Check completeness and security; emits a structured pass/fail/warn report and a READY/NEEDS_WORK/BLOCKED verdict |
| `check_staleness.py <file>` | Assess if handoff context is still current |
| `find_cleanup_candidates.py [path] [--verbose]` | Detect superseded + complete handoffs that are safe to retire (read-only) |

### references/

- [handoff-template.md](references/handoff-template.md) — Canonical template structure with placeholder documentation. The `create_handoff.py` script renders from this file; it is the single source of truth.
- [create-workflow.md](references/create-workflow.md) — Full CREATE procedure: focus-setting, scaffold, session-plan confirmation, the prioritized fill order, validation, and commit. The in-body CREATE section summarizes; this is the step-by-step.
- [resume-workflow.md](references/resume-workflow.md) — Full RESUME procedure: list, staleness, read strategy, the verify-context red flags, and updating/chaining. The in-body RESUME section summarizes; this is the step-by-step.
- [cleanup-workflow.md](references/cleanup-workflow.md) — Full CLEANUP procedure: candidate tiers, the approval gate, and the `git rm` / `trash` removal mechanics. The in-body CLEANUP section summarizes; this is the step-by-step.
