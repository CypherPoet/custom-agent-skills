---
name: dependency-tag-check
description: Manually-triggered, read-only audit of git-tag coverage for version-constrained plugin dependencies. Confirms every pinned dependency has a satisfying `<plugin>--v<version>` tag on the source repo, so a depended-on plugin won't fail to install with `no-matching-tag`. Reports MISSING / UNSATISFIABLE / DRIFT / OK and points at `claude plugin tag` for fixes — never writes anything.
disable-model-invocation: true
---

# dependency-tag-check

Report whether every **version-constrained** plugin dependency in this repo has a git tag that can actually satisfy it. A constrained dependency on a `git-subdir` source resolves its range against tags named `<plugin-name>--v<version>` on the **source repo** (this one), and with no satisfying tag the install hard-fails with `no-matching-tag`. This skill catches that gap *before* a consumer hits it.

**Read-only** — never create or push a tag, never edit a `plugin.json`, never commit or open a PR. Just report coverage and hand off to `claude plugin tag` for anything the user wants to fix.

The audit logic is a bundled script — Python 3 standard library only (no `node`/`npx`, no installs, and no network beyond `git ls-remote` to this repo's own origin). Run it and relay what it prints; don't reimplement it inline.

## When this matters (and when it's a clean no-op)

This repo's default is **bare-string** dependencies (`"dependencies": ["other-plugin"]`), which track latest and need no tags. Tags only enter the picture for a **constrained** dependency — an object with a `version` range, e.g. `{ "name": "other-plugin", "version": "~0.1.0" }` — which is the deliberate exception (a pinned line, e.g. holding a consumer on `0.1.x` while a `0.2.x` line develops). See [`docs/PLUGIN-CONVENTIONS.md`](../../../docs/PLUGIN-CONVENTIONS.md) → Dependencies for the full rationale.

So if the audit finds zero constrained dependencies, "nothing to check — all clean" is the **expected, correct** result, not a sign something is wrong. Say so plainly and stop.

## Run the audit

From anywhere in the repo:

```shell
python3 .claude/skills/dependency-tag-check/scripts/audit_dependency_tags.py
```

It locates the repo root via git, walks every `plugins/*/.claude-plugin/plugin.json`, keeps only the dependency entries that carry a `version` (bare strings are skipped — they need no tags), queries `origin`'s tags, and prints each constrained dependency in exactly one bucket. Exit status is non-zero when anything is actionable.

**Relay the script's report to the user and stop — change nothing.** If it prints "No version-constrained dependencies found," that's the expected clean result here; say so and stop.

### What the buckets mean

| Bucket | Meaning | Fix (hand off — see below) |
|---|---|---|
| **OK** | A pushed tag on `origin` satisfies the range. | none |
| **MISSING** | No satisfying tag on `origin` — either the current version satisfies the range but is untagged, or a satisfying tag exists only locally (unpushed). | tag it / push it |
| **UNSATISFIABLE** | No tag satisfies *and* the dependency's current version is outside the range (e.g. dep at `0.2.0`, dependent pins `~0.1.0`). | widen the constraint, or maintain an older tagged line |
| **DRIFT** | A satisfying tag exists but points at a commit whose manifest version ≠ the tag's version — a force-moved or stale tag. | decide whether the tag should move |
| **UNKNOWN** | The range uses an expression the script doesn't recognize (e.g. `\|\|` or hyphen ranges). It refuses to guess. | verify that one by hand |
| **EXTERNAL** | The dependency isn't a local plugin, or names another `marketplace` — its tags live in a different source repo. | audit it in that repo |

## Remediation (handoff only — never run it yourself)

- **MISSING, current version satisfies the range** → once that version is on `main`, the user runs, from the depended-on plugin's directory:
  ```bash
  claude plugin tag --push   # creates <plugin>--v<version> on origin
  ```
- **MISSING, satisfying tag is local-only** → the user pushes the existing tag (`git push origin <dep>--v<version>`).
- **UNSATISFIABLE** → tagging won't fix it. The user either widens the dependent's constraint in its `plugin.json` (and republishes that plugin per the version-bump rule) or deliberately maintains an older tagged line.
- **DRIFT** → the user decides whether the tag should move; this skill only flags the mismatch.

Re-running after a fix re-confirms coverage. This skill never writes anything — it only tells the user what to run.
