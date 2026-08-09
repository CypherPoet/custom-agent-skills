# Manifest reference

`docs/automated-routines/skill-fact-check-manifest.json` is repo-local — it lists only that repo's units. Read this when re-tiering a skill or accepting a flag; a normal run only needs the tier lookup.

```json
{
  "defaults": { "tier": "monthly" },
  "weekly":  ["<plugin>/<skill>", "..."],
  "monthly": ["<plugin>/<skill>", "..."],
  "never":   ["<plugin>/<skill>", "..."],
  "acknowledged": [
    {
      "unit_id": "<plugin>/<skill>",
      "locator": "unique substring of the flagged text",
      "reason": "why this flag is accepted, not a defect",
      "ack_date": "YYYY-MM-DD",
      "recheck_after": "YYYY-MM-DD"
    }
  ]
}
```

## Tiers

| Tier | Interval | For |
|---|---|---|
| `weekly` | ≥7 days | Fast-drifting skills — Apple OS/App Store specs, SwiftUI "what's new", SF Symbols, three.js, Blender |
| `monthly` | ≥28 days (the default) | Everything else |
| `never` | — | Evergreen methodology — session handoff/harvest, emoji commits, changelog, readme badges, GDScript. **Also every vendored copy** (below) |

Re-tier by moving a `unit_id` between lists; the skill itself doesn't change. A `unit_id` in no list resolves to `monthly`, so a manifest without an explicit `monthly` array still works — listing them makes tiering a deliberate per-skill choice. `compute_due_set.py` prints `# DRIFT` lines for untiered, orphaned, or double-listed entries.

### Vendored copies are always `never`

A skill shared across plugins is **vendored** — physically copied into each plugin that ships it, per the `vendored_skills` edges in `scripts/plugin-registry.json`. Copies are generated files. Tier every copy `never` and leave only the authoritative source researchable:

- Correcting a copy hand-edits a generated file. `cypherpoet-sync-plugins` rewrites it wholesale from the source on the next run, so the correction is silently discarded — the research happened, the citation was sound, and the fix is simply gone.
- Correcting the source and re-syncing propagates the same fix to every copy for free, which is why one `never` entry per copy is all this takes.
- Researching a copy also pays for the identical deep-research wave two or three times over.

When adding a `vendored_skills` edge, add the new target to `never` in the same change. Miss it and the copy defaults to `monthly` — `compute_due_set.py` will print a `# DRIFT untiered` line, but not before that run has already researched and edited it.

A `never`-tier unit is never researched, so it never needs a dateline; only `weekly` and `monthly` units carry one.

## `acknowledged`

Optional. Silences flags a human has judged acceptable — the "not wrong", "no vendor-primary source exists", or "won't change" findings that otherwise re-appear every run.

Each entry pins a `unit_id` and a `locator` (a unique substring of the flagged text, same idea as a claim's locator), a human `reason`, an `ack_date`, and a `recheck_after` — a date, or `"never"` for a permanently-accepted item. Prefer a dated `recheck_after`: a fact accepted only because it's currently undocumented should resurface if the vendor later documents it.

A matching flag lands in the PR's `🔕 Known / acknowledged` section instead of `🚩 Flagged`; once `recheck_after` passes it moves back up so the acceptance is re-confirmed.
