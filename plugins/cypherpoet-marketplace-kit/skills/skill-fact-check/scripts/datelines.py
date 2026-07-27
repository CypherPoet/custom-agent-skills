#!/usr/bin/env python3
"""The dateline dialects this repo family uses, in one place.

A **dateline** is the freshness cursor a skill carries: the explicit
verification/sync label saying when its facts were last checked. Both halves of
skill-fact-check read them — compute_due_set.py decides whether a unit is stale
enough to re-research, and check_dateline_only.py decides whether a PR is safe
to merge without review — so they share this module rather than each carrying a
copy that drifts.

Bare content dates ("released …", "Created: …", "replaced … on …") are excluded
from both: treating one as a dateline would mark a stale unit fresh and silence
it forever.

Recognized forms (each accepts YYYY-MM-DD, or YYYY-MM read as the 1st):

  labelled — a date introduced by an explicit verification/sync label
    **Verified:** 2026-05-30                              the canonical marker
    > Last synced: 2026-06-19                             label may carry trailing words
    **Audit baseline:** … verified against … (2026-06-26) parenthetical

  unlabelled — freshness cues that read as ordinary prose
    specs here verified 2026-05-30                        inline
    **(as of 2026-06)**                                   month precision

**Two patterns, on purpose.** The callers do NOT ask the same question, and a
false positive costs them opposite things:

- `DATELINE` (both kinds) answers *is this unit fresh?* A missed dateline just
  re-researches a unit that didn't need it, so recall is what matters and the
  unlabelled cues earn their place.
- `RESTAMPABLE` (labelled only) answers *may this edit merge unreviewed?* Here a
  false positive is an unreviewed merge. `as of` and inline `verified` routinely
  sit mid-sentence in ordinary prose ("requires macOS 15.4 as of 2026-03-01"),
  so treating one as a re-stamp would let a correction to that sentence through
  the gate. Every unit in the family carries at least one labelled dateline, so
  restricting the gate costs no auto-merges; a unit whose re-stamp lands on an
  unlabelled cue simply holds for a human, which is the safe direction.

Python 3 standard library only.
"""
import datetime
import pathlib
import re

EPOCH = datetime.date(1970, 1, 1)

_D = r'(\d{4}-\d{2}(?:-\d{2})?)'

_LABELLED = [
    r'\*\*verified:\*\*\s*' + _D,                       # **Verified:** <date>
    r'(?:last\s+)?synced\b[^\n:]{0,40}?:\s*' + _D,      # [Last ]synced[ with …]: <date>
    r'audit baseline\b[^\n]*?\(' + _D + r'\)',          # **Audit baseline:** … (<date>)
]

_UNLABELLED = [
    r'\bverified\s+' + _D,                              # verified <date> (inline)
    r'\bas of\s+' + _D,                                 # as of <date>
]

# Freshness: every form counts (see the two-patterns note above).
DATELINE = re.compile('|'.join(_LABELLED + _UNLABELLED), re.I)

# Merge gate: only a date an explicit label introduces.
RESTAMPABLE = re.compile('|'.join(_LABELLED), re.I)


def _raw(match):
    """The date text a match captured, whichever alternative fired."""
    return next((g for g in match.groups() if g), None)


def _parse(raw):
    """`raw` as a date, or None when the digits aren't a real calendar date.

    The pattern matches any two digits for the month, so `2026-13-01` and
    `2026-02-30` reach here. Skipping one leaves the unit reading older than it
    claims — it stays due and keeps getting researched, which is the safe
    direction — and compute_due_set.py reports it as DRIFT so the typo gets
    fixed rather than quietly costing a research wave every run.
    """
    try:
        return datetime.date.fromisoformat(raw if len(raw) == 10 else raw + '-01')
    except ValueError:
        return None


def dates_in(text):
    """Every parseable dateline date in `text`. Month precision → the 1st."""
    found = (_parse(_raw(m)) for m in DATELINE.finditer(text))
    return [date for date in found if date]


def malformed_in(text):
    """Every dateline date in `text` whose digits aren't a real calendar date."""
    raws = (_raw(m) for m in DATELINE.finditer(text))
    return [raw for raw in raws if raw and not _parse(raw)]


def blank_dates(line):
    """`line` with the date inside each **labelled** dateline replaced by `<DATE>`.

    Only the marker's own date. A bare content date elsewhere on the line
    ("shipped 2026-03-01") is deliberately left alone, so that two re-stamps of
    the same line compare equal while a correction sharing a row with a dateline
    still reads as a change. Blanking every date-shaped token instead would hide
    exactly the edit check_dateline_only.py exists to catch — and would also
    chew the leading half of an unrelated numeric range (`2048-2732`).
    """
    def one(match):
        raw = _raw(match)
        return match.group(0).replace(raw, '<DATE>') if raw else match.group(0)
    return RESTAMPABLE.sub(one, line)


def in_dateline_scope(path):
    """False for trees whose dates are not a unit's freshness cursor.

    Evals ARE fact-checked (their fixtures encode the same version-sensitive
    premises as the docs), but a date inside a fixture is scenario data, not a
    record of when this unit was last verified — counting one would falsely
    freshen the unit. Workspaces are regenerable scratch. Both are also skipped
    when enumerating units, so an eval's fixture SKILL.md is never a unit itself.
    """
    text = str(path)
    return '/evals/' not in text and '-workspace/' not in text


def scan(unit_dir):
    """`(newest dateline, malformed date tokens)` across a unit's markdown.

    EPOCH when the unit carries no parseable dateline — which reads as maximally
    overdue, so a unit that has never been stamped is always due.
    """
    found, malformed = [], []
    for path in pathlib.Path(unit_dir).rglob('*.md'):
        if in_dateline_scope(path):
            text = path.read_text(errors='ignore')
            found.extend(dates_in(text))
            malformed.extend(f'{path}: {raw}' for raw in malformed_in(text))
    return max(found, default=EPOCH), malformed


def newest(unit_dir):
    """The freshest dateline across a unit's markdown, or EPOCH when it carries none."""
    return scan(unit_dir)[0]
