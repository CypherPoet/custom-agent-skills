# 🤝 Handoff: User-table migration — three-phase rollout plan + Phase 1 shipped

> 🎯 **Next Action**: Phase 1 is complete (schema column added + backfill running). Hand off to the next session to run Phase 2 after the backfill drains. See "Three-phase rollout plan" below for the full sequence.

## 🧾 Session Metadata
- Created: 2026-05-12T11:14:02Z
- Branch: main

### Recent Commits (for context)
  - 1a2b3c4 Phase 1: add nullable `display_name` column to users table
  - 9d8e7f6 Add backfill script for display_name (idempotent, batched 1k rows)
  - 5c4b3a2 Migration scaffolding under migrations/

## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

## 📍 Current State Summary

Kicking off a three-phase migration to add a non-null `display_name` column to the `users` table (currently 850k rows). Phase 1 (nullable add + backfill kickoff) shipped this session. Phases 2 and 3 are in the rollout plan below — the next session will pick up Phase 2 once the backfill finishes draining.

## 💡 Important Context

**Three-phase rollout plan (canonical sequence — Phases 2 and 3 happen in later sessions):**

1. **Phase 1 (done this session)**: Add `display_name` column as nullable. Deploy backfill script (`migrations/run.py` with `--phase=1`) which copies `username` into `display_name` in batches of 1000 with a 100ms sleep between batches. Runs in the background after Phase 1 deploys.

2. **Phase 2 (next session)**: After the backfill drains (verify with `SELECT count(*) FROM users WHERE display_name IS NULL` — expect 0). Run `python migrations/run.py --phase=2 --dry-run` first and confirm output matches the expected diff in the appendix. Then run without `--dry-run`. This adds the `NOT NULL` constraint and a backing index.

3. **Phase 3 (session after that)**: Application code switches from reading `username` to reading `display_name` for the user-facing profile views. Affects `src/profile.js` and `src/api/users.js`. Deferred until Phase 2 is verified in production.

**Expected dry-run output for Phase 2** (the appendix):
```
ALTER TABLE users ALTER COLUMN display_name SET NOT NULL;
CREATE INDEX CONCURRENTLY idx_users_display_name ON users (display_name);
[dry-run] no actual changes
```

If the dry-run output deviates from the above, **stop and verify** before running for real — it's a sign the schema state isn't where we expect.

## 🚧 Pending Work

### Deferred Items

1. Phase 2 (this is the next session's job).
2. Phase 3 (the session after).
3. Drop `username` column entirely — only after Phase 3 ships and bakes in production for at least a week.

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- The backfill runs as a separate process — do not assume it's finished just because the deploy completed. Always check the row count before Phase 2.
- `migrations/run.py` is idempotent across phases but **not** across `--dry-run`/real-run. Always dry-run first.

## 🧠 Codebase Understanding

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `migrations/run.py` | Phased migration driver | Has `--phase=N` and `--dry-run` flags |
| `migrations/plan.md` | Mirror of the three-phase plan above | Source of truth if this handoff drifts |

## 🏁 Work Completed

- [x] Wrote the three-phase plan in `migrations/plan.md`
- [x] Shipped Phase 1 (nullable add + backfill kickoff)
