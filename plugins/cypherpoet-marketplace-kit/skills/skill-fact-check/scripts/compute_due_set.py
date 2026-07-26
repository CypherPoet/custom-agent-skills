#!/usr/bin/env python3
"""Print the fact-check due set for the repo in the current working directory.

A unit is **due** when its tier's interval has elapsed since its newest dateline.
This is age-gated, not run-gated: the dateline *is* the cursor, so a unit skipped
by a crash or a deferral stays due next time and the schedule self-heals.

Run with the working directory set to the repo being checked — this script lives
in the custom-agent-skills clone but reads whichever repo you point it at, so
paths (plugins/…, the manifest) resolve against the target.

Output is one tab-separated row per due unit, most-overdue first:
    age_days  unit_id  unit_dir  tier  last_dateline
followed by `#`-prefixed notes: the wave hint, and manifest DRIFT lines
(orphaned / double-listed / untiered entries). DRIFT is hygiene, not a fact
finding — report it for a human to re-tier deliberately, never edit the manifest.

Python 3 standard library only. Exit 0 always: an empty due set is a valid answer.
"""
import datetime
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from datelines import newest, in_dateline_scope  # noqa: E402

MANIFEST = pathlib.Path('docs/automated-routines/skill-fact-check-manifest.json')
INTERVAL = {'weekly': 7, 'monthly': 28}
TIERS = ('weekly', 'monthly', 'never')
DEFAULT_TIER = 'monthly'
BATCH_SIZE = 12


def units():
    """Every fact-checkable unit: (unit_id, unit_dir) for each plugin skill."""
    found = []
    for path in sorted(pathlib.Path('plugins').rglob('SKILL.md')):
        if not in_dateline_scope(path):
            continue
        parts = path.parts                      # plugins/<plugin>/skills/<skill>/SKILL.md
        if len(parts) >= 5:
            found.append((f'{parts[1]}/{parts[3]}', path.parent))
    return found


def main():
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    tier_of = {}
    for tier in TIERS:
        tier_of.update({unit: tier for unit in manifest.get(tier, [])})
    default_tier = manifest.get('defaults', {}).get('tier', DEFAULT_TIER)

    today = datetime.date.fromisoformat(
        subprocess.check_output(['date', '-u', '+%F']).decode().strip())

    all_units = units()
    due = []
    for unit_id, unit_dir in all_units:
        tier = tier_of.get(unit_id, default_tier)
        if tier == 'never':
            continue
        last = newest(unit_dir)
        age = (today - last).days
        # An unknown or typo'd tier falls back to monthly rather than crashing.
        if age >= INTERVAL.get(tier, INTERVAL['monthly']):
            due.append((age, unit_id, str(unit_dir), tier, last.isoformat()))

    due.sort(reverse=True)
    for row in due:
        print(*row, sep='\t')
    print(f'# {len(due)} due — research in waves of ~{BATCH_SIZE}, '
          f'most-overdue-first, until drained')

    unit_ids = {unit_id for unit_id, _ in all_units}
    listed = [unit for tier in TIERS for unit in manifest.get(tier, [])]
    for unit in sorted(set(listed) - unit_ids):
        print(f'# DRIFT orphaned: {unit} listed in the manifest but not on disk')
    for unit in sorted({u for u in listed if listed.count(u) > 1}):
        print(f'# DRIFT double-listed: {unit} in more than one tier '
              f'(later list wins — keep one)')
    for unit in sorted(unit_ids - set(listed)):
        print(f'# DRIFT untiered: {unit} not in any tier list (defaults to {default_tier})')


if __name__ == '__main__':
    main()
