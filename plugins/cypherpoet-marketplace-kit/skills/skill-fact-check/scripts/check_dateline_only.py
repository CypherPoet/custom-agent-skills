#!/usr/bin/env python3
"""Is this branch's diff nothing but re-stamped datelines?

Gate for the one PR shape skill-fact-check merges without human review. Run with
the working directory set to the repo being checked, after the branch is pushed.

It compares the base and head **contents** of every changed file — not the text
of the diff. Reading `+`/`-` prefixes means re-deriving what git already knows,
and that leaks three ways: a removed line beginning with `--` is
indistinguishable from the `--- a/path` header, a purely added line has no
counterpart to compare against so only its own shape can be checked, and a
rename carries no content lines at all. Comparing contents makes all three moot.

One rule covers the whole shape:

    once each marker's own date is blanked, every line of every changed file
    must be unchanged — the only difference allowed is an *added* canonical
    `**Verified:** <date>` stamp

That addition is what Step 6 writes into a unit carrying no dateline yet.
Blanking only the date *inside* a marker (see datelines.blank_dates) is what
stops a correction from hiding on a dateline's own line: in

    | iOS | shipped 2026-03-01 | verified 2026-07-11 |

the spec date sits outside any marker, so editing it still reads as a rewritten
line rather than as a re-stamp.

It is a whitelist and it fails closed — anything it cannot positively account
for blocks the merge, and a blocked gate is not a run failure.

Python 3 standard library only. Exit 0 = dateline-only, 1 = hold for review,
2 = git failed.
"""
import difflib
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from datelines import blank_dates  # noqa: E402

ALLOWED = re.compile(r'^plugins/[^/]+/skills/[^/]+/(SKILL\.md|references/.+\.md)$')
STAMP = re.compile(r'^\*\*Verified:\*\* <DATE>$')   # the one line Step 6 may ADD
BASE = 'origin/main'
MAX_REPORT = 20


def git(*args):
    return subprocess.check_output(
        ['git', *args], encoding='utf-8', errors='ignore')


def normalized(rev, path):
    """`path` at `rev`, one entry per line, each dateline's own date blanked."""
    return [blank_dates(line) for line in git('show', f'{rev}:{path}').splitlines()]


def main():
    try:
        subprocess.check_call(['git', 'fetch', '--quiet', 'origin', 'main'])
        base = git('merge-base', BASE, 'HEAD').strip()
        # --no-renames so a rename becomes a delete + an add, and its content is
        # actually compared instead of vanishing into a rename header.
        changed = git('diff', '--name-status', '--no-renames',
                      base, 'HEAD').splitlines()
        pairs = []
        for row in changed:
            status, name = row.split('\t', 1)
            if not ALLOWED.match(name) or '/evals/' in name or '-workspace/' in name:
                pairs.append((name, None, None))
                continue
            pairs.append((
                name,
                [] if status.startswith('A') else normalized(base, name),
                [] if status.startswith('D') else normalized('HEAD', name),
            ))
    except subprocess.CalledProcessError as err:
        # A gate that could not run must never read as a pass. Shallow clone
        # ("no merge base"), missing origin/main, wrong cwd all land here.
        print(f'git failed: {err}', file=sys.stderr)
        return 2

    blocked = []
    for name, old, new in pairs:
        if old is None:
            blocked.append(f'out-of-scope file: {name}')
            continue
        opcodes = difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes()
        for op, i1, i2, j1, j2 in opcodes:
            if op == 'equal':
                continue
            blocked += [f'{name}: line lost or rewritten: {l.strip()[:80]}'
                        for l in old[i1:i2]]
            blocked += [f'{name}: added, not a **Verified:** stamp: {l.strip()[:80]}'
                        for l in new[j1:j2] if l.strip() and not STAMP.match(l.strip())]

    if not changed:
        blocked.append('empty diff — nothing to merge')

    for item in blocked[:MAX_REPORT]:
        print(f' - {item}')
    if len(blocked) > MAX_REPORT:          # a deleted file lists every line
        print(f' … and {len(blocked) - MAX_REPORT} more')
    print('HOLD for review' if blocked else 'DATELINE-ONLY')
    return 1 if blocked else 0


if __name__ == '__main__':
    sys.exit(main())
