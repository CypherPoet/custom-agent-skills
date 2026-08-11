# PR and commit format

## Commits

One commit per plugin, so the diff reviews cleanly. Match the repo's gitmoji style (see `emoji-commits/emoji-commits`).

```
🩹 fix(<skill>): <one-line fact correction> [skill-fact-check]

- references/<file>.md: <old> → <new>  (per <source>)
- bump <plugin> <oldver> → <newver>
```

## PR title

```
🔍 Skill fact-check: N corrections, M flagged (<repo> <YYYY-MM-DD>)
```

## PR body

Rewritten each run to the current state — this is a report, not a changelog. Drop sections that would be empty rather than shipping a wall of "None".

```markdown
Automated skill fact-check (the `skill-fact-check` skill in `marketplace-kit`).
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

**A green run is not a successful run.** The "Could not verify" and "Deferred" sections are the real signal — a run that finishes cleanly having verified nothing looks identical from the outside to one that verified everything.
