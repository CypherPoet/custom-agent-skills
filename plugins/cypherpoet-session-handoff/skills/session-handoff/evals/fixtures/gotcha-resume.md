# 🤝 Handoff: Legacy-adapter cleanup — paused; do NOT delete legacy_adapter.py without verification

> 🎯 **Next Action**: Confirm with the user whether `src/legacy_adapter.py` can actually be removed. Static analysis says it's unused, but the queue worker imports it via a runtime string lookup. Do not delete until that's resolved (see Potential Gotchas).

## 🧾 Session Metadata
- Created: 2026-05-15T22:10:48Z
- Branch: cleanup/remove-legacy-adapter

### Recent Commits (for context)
  - 88a1f33 Remove stale TODO comments from src/legacy_adapter.py
  - 02d3e91 Audit which callers reference legacy_adapter (ripgrep)

## 🔗 Handoff Chain

- **Continues from**: None (fresh start)
- **Supersedes**: None

## 📍 Current State Summary

Started a cleanup pass on `src/legacy_adapter.py` — a module that looked dead per static analysis (no direct imports anywhere in the codebase). Halfway through writing the deletion PR, discovered that `workers/queue.py` constructs the module name dynamically via `importlib.import_module(adapter_name)` where `adapter_name` is read from a config file. The legacy adapter is one of the configured handlers. Pausing the cleanup before any deletion lands.

## 💡 Important Context

The cleanup was triggered by a routine "what's unused" sweep. Naive grep / static analysis correctly reports `legacy_adapter` has no `import` statements pointing at it from any source file. That's the trap — `workers/queue.py:104` uses `importlib.import_module` with a string variable, so the dependency isn't visible to AST-based tools, ripgrep, or IDE "find usages."

The user previously authorized "remove anything ripgrep can't find a usage for" as a general cleanup rule. That rule does not apply here — the runtime-string-import case is the documented exception.

## 🚧 Pending Work

### Immediate Next Steps

1. Surface the deferred-import discovery to the user. Ask whether the legacy adapter is still required by any deployed queue config.
2. **Only after user confirms it's safe**: delete `src/legacy_adapter.py` and the corresponding config entry. Otherwise, close the cleanup PR as not-applicable.
3. If the legacy adapter must stay, document the deferred-import-string dependency in `src/legacy_adapter.py` as a comment at the top so future cleanup passes don't repeat this discovery.

### Blockers / Open Questions

- [ ] User confirmation: is `legacy_adapter` still referenced by any production queue config?

### Deferred Items

- Add a static-analysis hook that scans for `importlib.import_module(<string>)` calls and emits a list of strings to consider when checking for unused modules.

## ⚠️ Constraints for Resuming Agent

### Potential Gotchas

- **DO NOT delete `src/legacy_adapter.py`.** The queue worker (`workers/queue.py:104`) imports it via `importlib.import_module(adapter_name)` where `adapter_name` is read from runtime config. Deletion will silently break message processing — the worker will start fine, but message handlers will throw `ModuleNotFoundError` at the first message that routes to the legacy adapter. Failures are async and may not be noticed for hours.
- **"No grep matches" does not mean "unused"** for any file that could be a target of `importlib.import_module(string_var)`. Always check for dynamic imports before deleting a Python module flagged by static-only analysis.
- The user's general "delete-anything-ripgrep-can't-find" rule is **explicitly overridden** for this case. Surface the situation; do not act on the general rule unilaterally.

### 🧰 Skills to Use

| Skill | When to invoke | Why |
|-------|---------------|-----|
| (manual ripgrep / Read) | Verifying the queue worker reference | Just grep `workers/queue.py` for `import_module` to confirm before talking to user |

## 🧠 Codebase Understanding

### Critical Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `src/legacy_adapter.py` | Legacy queue message handler | **Do NOT delete** — see Potential Gotchas |
| `workers/queue.py` (line 104) | Queue worker dispatching to adapters via `importlib.import_module` | The reason legacy_adapter is reachable despite no static imports |
| `config/queue.yml` (if it exists in this checkout) | Names the active adapters | Listing legacy_adapter here means it's wired up |

## 🏁 Work Completed

- [x] Confirmed via ripgrep that legacy_adapter has no static `import` references.
- [x] Discovered the `importlib.import_module(adapter_name)` pattern in `workers/queue.py:104` — that's why static analysis was misleading.
- [x] Paused the cleanup PR before any destructive changes.

### Decisions Made

- **Stopped the cleanup before deletion despite the user's general "delete if unused" rule.** Discovering a runtime-string import is exactly the case that rule's exception covers. Better to spend one round-trip with the user confirming than to merge a PR that silently breaks the queue.
