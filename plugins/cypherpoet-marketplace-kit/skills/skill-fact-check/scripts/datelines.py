#!/usr/bin/env python3
"""The dateline dialects this repo family uses, in one place.

A **dateline** is the freshness cursor a skill carries: the explicit
verification/sync label saying when its facts were last checked. Both halves of
skill-fact-check depend on recognizing exactly the same set of them —
compute_due_set.py decides whether a unit is stale enough to re-research, and
check_dateline_only.py decides whether a PR is safe to merge without review.
Those answer opposite questions, so a second encoding drifting from the first is
a real defect: this module is why there is only one.

Only explicit verification/sync labels count. Bare content dates ("released …",
"Created: …", "replaced … on …") are deliberately excluded — treating one as a
dateline would mark a stale unit fresh and silence it forever.

Recognized forms (each accepts YYYY-MM-DD, or YYYY-MM read as the 1st):
  **Verified:** 2026-05-30                              the canonical marker
  > Last synced: 2026-06-19                             label may carry trailing words
  **Audit baseline:** … verified against … (2026-06-26) parenthetical
  specs here verified 2026-05-30                        inline
  **(as of 2026-06)**                                   month precision

Python 3 standard library only.
"""
import datetime
import pathlib
import re

EPOCH = datetime.date(1970, 1, 1)

_D = r'(\d{4}-\d{2}(?:-\d{2})?)'

DATELINE = re.compile('|'.join([
    r'\*\*verified:\*\*\s*' + _D,                       # **Verified:** <date>
    r'(?:last\s+)?synced\b[^\n:]{0,40}?:\s*' + _D,      # [Last ]synced[ with …]: <date>
    r'audit baseline\b[^\n]*?\(' + _D + r'\)',          # **Audit baseline:** … (<date>)
    r'\bverified\s+' + _D,                              # verified <date> (inline)
    r'\bas of\s+' + _D,                                 # as of <date>
]), re.I)

def dates_in(text):
    """Every dateline date in `text`, as date objects. Month precision → the 1st."""
    out = []
    for match in DATELINE.finditer(text):
        raw = next((g for g in match.groups() if g), None)
        if raw:
            out.append(datetime.date.fromisoformat(
                raw if len(raw) == 10 else raw + '-01'))
    return out


def blank_dates(line):
    """`line` with the date *inside each dateline marker* replaced by `<DATE>`.

    Only the marker's own date. A bare content date elsewhere on the line
    ("shipped 2026-03-01") is deliberately left alone, so that two re-stamps of
    the same line compare equal while a correction sharing a row with a dateline
    still reads as a change. Blanking every date-shaped token instead would hide
    exactly the edit check_dateline_only.py exists to catch — and would also
    chew the leading half of an unrelated numeric range (`2048-2732`).
    """
    def one(match):
        raw = next((g for g in match.groups() if g), None)
        return match.group(0).replace(raw, '<DATE>') if raw else match.group(0)
    return DATELINE.sub(one, line)


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


def newest(unit_dir):
    """The freshest dateline across a unit's markdown, or EPOCH when it carries none."""
    found = []
    for path in pathlib.Path(unit_dir).rglob('*.md'):
        if in_dateline_scope(path):
            found.extend(dates_in(path.read_text(errors='ignore')))
    return max(found, default=EPOCH)
