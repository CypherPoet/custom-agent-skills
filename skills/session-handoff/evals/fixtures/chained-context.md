# 🤝 Handoff: User-table migration — backfill drained, ready for Phase 2

> 🎯 **Next Action**: Run `python migrations/run.py --phase=2 --dry-run` and verify the output matches the expected diff in the predecessor handoff's appendix before running for real.

## 🧾 Session Metadata
- Created: 2026-05-16T08:30:00Z
- Branch: main

### Recent Commits (for context)
  - de5ab12 Backfill drained; users.display_name NULL count = 0

## 🔗 Handoff Chain

- **Continues from**: [PREDECESSOR_FILENAME](./PREDECESSOR_FILENAME)
  - Previous title: User-table migration — three-phase rollout plan + Phase 1 shipped
- **Supersedes**: None

> Read the predecessor handoff for the full three-phase plan and the expected Phase 2 dry-run output. This handoff documents only the Phase 1 → Phase 2 transition state.

## 📍 Current State Summary

Phase 1's backfill has fully drained — every row in `users` now has a non-NULL `display_name`. We are exactly at the Phase 1 → Phase 2 boundary described in the predecessor handoff. The next session runs the Phase 2 migration (constraint + index).

## 💡 Important Context

The **three-phase plan** and the **expected Phase 2 dry-run output** live in the predecessor handoff. Read it before running Phase 2 — that's where the verification appendix is.

Verified just before writing this handoff:
- `SELECT count(*) FROM users WHERE display_name IS NULL;` → 0 (confirmed twice, 30 seconds apart).
- `migrations/plan.md` matches the predecessor's plan section — no drift.

## 🚧 Pending Work

### Immediate Next Steps

1. Dry-run Phase 2 (see 🎯 Next Action). Compare output against the predecessor's appendix.
2. If dry-run output matches, run for real: `python migrations/run.py --phase=2`.
3. After Phase 2 completes, write a new handoff for the Phase 3 session (application code swap).

### Deferred Items

See predecessor handoff — same list.

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- **Do not skip the dry-run.** The predecessor's appendix gives the exact expected SQL. A divergence means the schema state isn't what we expect and Phase 2 should not proceed.
- The backfill drained as of 08:25 UTC. If significant time has passed before resumption, **re-verify the NULL count** before dry-running — new rows may have been inserted with NULL `display_name`.

## 🧠 Codebase Understanding

Architecture unchanged from predecessor — see that handoff for the full overview.

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `migrations/run.py` | Phased migration driver | Run with `--phase=2 --dry-run` |
| `migrations/plan.md` | Three-phase rollout plan | Mirror of the predecessor's plan section |

## 🏁 Work Completed

- [x] Verified backfill drained (NULL count = 0)
- [x] Confirmed `migrations/plan.md` matches predecessor

### Decisions Made

- **Wrote a new handoff at the phase boundary rather than chaining inside the same session.** Cleaner state — the next agent's mental model starts at the Phase 2 boundary without re-reading Phase 1 history.

## 📚 Related Resources

- Predecessor handoff (the canonical three-phase plan + dry-run appendix)
- `migrations/plan.md`
