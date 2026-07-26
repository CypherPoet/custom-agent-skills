#!/usr/bin/env python3
"""Is this branch's diff nothing but re-stamped datelines?

Gate for the one PR shape skill-fact-check merges without human review. Run with
the working directory set to the repo being checked, after the branch is pushed.

Three tests, all of which must come back clean:

  1. Only skill prose changed — no plugin.json, no manifest, nothing under
     evals/ or a workspace.
  2. Every added line carries a dateline (blank lines are the filler around a
     newly stamped one).
  3. Every removed line reappears as an added line identical once dates are
     blanked.

Test 3 is the one that matters. "Every changed line mentions a date" is too
weak: the inline `verified <date>` form lets one table row carry both a spec and
a dateline, so a spec correction on that row would pass tests 1 and 2. Requiring
the removed line to come back unchanged-but-for-the-date is what pins the diff
to a pure re-stamp.

It is a whitelist and it fails closed — anything it cannot positively account
for blocks the merge, and a blocked gate is not a run failure.

Python 3 standard library only. Exit 0 = dateline-only, 1 = hold for review,
2 = git failed.
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from datelines import blank_dates, is_dateline  # noqa: E402

ALLOWED = re.compile(r'^plugins/[^/]+/skills/[^/]+/(SKILL\.md|references/.+\.md)$')
BASE = 'origin/main'


def git(*args):
    return subprocess.check_output(['git', *args]).decode(errors='ignore')


def main():
    try:
        subprocess.check_call(['git', 'fetch', '--quiet', 'origin', 'main'])
        names = git('diff', '--name-only', f'{BASE}...HEAD').splitlines()
        diff = git('diff', '-U0', f'{BASE}...HEAD').splitlines()
    except subprocess.CalledProcessError as err:
        print(f'git failed: {err}', file=sys.stderr)
        return 2

    added = [l[1:] for l in diff if l.startswith('+') and not l.startswith('+++')]
    removed = [l[1:] for l in diff if l.startswith('-') and not l.startswith('---')]

    blocked = []

    for name in names:
        if not ALLOWED.match(name) or '/evals/' in name or '-workspace/' in name:
            blocked.append(f'out-of-scope file: {name}')

    for line in added:
        if line.strip() and not is_dateline(line):
            blocked.append(f'not a dateline: {line.strip()[:80]}')

    pool = [blank_dates(l) for l in added if l.strip() and is_dateline(l)]
    for line in removed:
        if not line.strip():
            blocked.append('removed a blank line')
        elif blank_dates(line) in pool:
            pool.remove(blank_dates(line))
        else:
            blocked.append(f'not a pure re-stamp: {line.strip()[:80]}')

    if not (added or removed):
        blocked.append('empty diff — nothing to merge')

    for item in blocked:
        print(f' - {item}')
    print('HOLD for review' if blocked else 'DATELINE-ONLY')
    return 1 if blocked else 0


if __name__ == '__main__':
    sys.exit(main())
