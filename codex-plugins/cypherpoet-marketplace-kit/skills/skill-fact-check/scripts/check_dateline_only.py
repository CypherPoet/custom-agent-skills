#!/usr/bin/env python3
"""Is this branch's diff nothing but re-stamped datelines?

Gate for the one PR shape skill-fact-check merges without human review. Run with
the working directory set to the repo being checked, after the branch is pushed.

It gates **what `gh pr merge` will actually squash** — the branch as it exists on
`origin`, not the local checkout. A gate that reads local `HEAD` authorizes a
commit nobody may have pushed, and says nothing about the one that merges. For
the same reason it prints the remote, branch, and both shas: a routine runs these
steps once per cloned repo, and output that names nothing is output you cannot
tell apart from the other clone's.

It compares the base and head **contents** of every changed file — not the text
of the diff. Reading `+`/`-` prefixes means re-deriving what git already knows,
and that leaks three ways: a removed line beginning with `--` is
indistinguishable from the `--- a/path` header, a purely added line has no
counterpart to compare against so only its own shape can be checked, and a
rename carries no content lines at all. Comparing contents makes all three moot.

One rule covers the whole shape:

    once each labelled marker's own date is blanked, every line of every changed
    file must be unchanged — the only difference allowed is an *added* canonical
    `**Verified:** <date>` stamp

That addition is what Step 6 writes into a unit carrying no dateline yet.
Blanking only the date *inside* a labelled marker (see datelines.blank_dates and
the two-patterns note above it) is what stops a correction from hiding on a
dateline's own line: in

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
from datelines import blank_dates, in_dateline_scope  # noqa: E402

ALLOWED = re.compile(r'^plugins/[^/]+/skills/[^/]+/(SKILL\.md|references/.+\.md)$')
STAMP = re.compile(r'^\*\*Verified:\*\* <DATE>$')   # the one line Step 6 may ADD
BASE_BRANCH = 'main'
MAX_REPORT = 20


def git(*args):
    return subprocess.check_output(
        ['git', *args], encoding='utf-8', errors='ignore')


def fetched(ref):
    """`ref` as it exists on origin right now, as a sha.

    One ref per fetch so `FETCH_HEAD` is unambiguous, and read straight back
    rather than through `origin/<ref>` — whether a remote-tracking ref exists
    for a given branch depends on how the clone's refspec is configured, and a
    gate must not be the thing that assumes.
    """
    git('fetch', '--quiet', 'origin', ref)
    return git('rev-parse', 'FETCH_HEAD').strip()


def normalized(rev, path):
    """`path` at `rev`, one entry per line, each labelled dateline's date blanked."""
    return [blank_dates(line) for line in git('show', f'{rev}:{path}').splitlines()]


def collect():
    """`(identity, [(path, base lines, head lines)])` for the pushed branch.

    `base lines` / `head lines` are None for a path outside the re-stampable
    surface — the caller blocks on those without reading them.
    """
    branch = git('rev-parse', '--abbrev-ref', 'HEAD').strip()
    if branch == 'HEAD':
        raise ValueError('detached HEAD — no branch to resolve on origin')

    head = fetched(branch)
    base = git('merge-base', fetched(BASE_BRANCH), head).strip()
    identity = (f'{git("remote", "get-url", "origin").strip()} '
                f'{branch} {base[:9]}..{head[:9]}')

    pairs = []
    # --no-renames so a rename becomes a delete + an add, and its content is
    # actually compared instead of vanishing into a rename header.
    for row in git('diff', '--name-status', '--no-renames', base, head).splitlines():
        status, name = row.split('\t', 1)
        if not ALLOWED.match(name) or not in_dateline_scope(name):
            pairs.append((name, None, None))
            continue
        pairs.append((
            name,
            [] if status.startswith('A') else normalized(base, name),
            [] if status.startswith('D') else normalized(head, name),
        ))
    return identity, pairs


def blockers(pairs):
    """Every reason this diff is not a pure re-stamp."""
    found = []
    for name, old, new in pairs:
        if old is None:
            found.append(f'out-of-scope file: {name}')
            continue
        opcodes = difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes()
        for op, i1, i2, j1, j2 in opcodes:
            if op == 'equal':
                continue
            found += [f'{name}: line lost or rewritten: {line.strip()[:80]}'
                      for line in old[i1:i2]]
            found += [f'{name}: added, not a **Verified:** stamp: {line.strip()[:80]}'
                      for line in new[j1:j2]
                      if line.strip() and not STAMP.match(line.strip())]
    if not pairs:
        found.append('empty diff — nothing to merge')
    return found


def main():
    try:
        identity, pairs = collect()
    except (subprocess.CalledProcessError, ValueError) as err:
        # A gate that could not run must never read as a pass. Shallow clone
        # ("no merge base"), an unpushed branch, missing origin, wrong cwd, and
        # a detached HEAD all land here.
        print(f'gate could not run: {err}', file=sys.stderr)
        return 2

    found = blockers(pairs)
    print(f'gated: {identity}')
    for item in found[:MAX_REPORT]:
        print(f' - {item}')
    if len(found) > MAX_REPORT:            # a deleted file lists every line
        print(f' … and {len(found) - MAX_REPORT} more')
    print('HOLD for review' if found else 'DATELINE-ONLY')
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main())
