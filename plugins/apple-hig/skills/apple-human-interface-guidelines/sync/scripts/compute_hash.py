#!/usr/bin/env python3
"""Canonicalize and hash distilled HIG content (canonicalization v1).

Shared by the manifest seeding step and diff_hig.py so identical content
always yields identical hashes. Hashes are computed over *distilled* markdown
(never raw HTML), so Apple's cosmetic/markup churn can't move them — only a
real change in distilled guidance does.

Canonicalization v1:
  1. Drop file-level volatile header lines (`> Source:`, `> Last synced:`).
  2. Strip trailing whitespace from every line.
  3. Collapse runs of blank lines to a single blank line.
  4. Normalize line endings to \n and strip leading/trailing blank lines.

Nothing semantic is reordered or lowercased — a real reordering of guidance
is a real change and must move the hash.
"""

import hashlib
import re
import sys

CANONICALIZATION_VERSION = "v1"

_VOLATILE_LINE = re.compile(r"^>\s*(Source|Last synced):", re.IGNORECASE)


def canonicalize(text: str) -> str:
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if _VOLATILE_LINE.match(line.strip()):
            continue
        lines.append(line.rstrip())
    collapsed = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return collapsed.strip() + "\n"


def content_hash(text: str) -> str:
    digest = hashlib.sha256(canonicalize(text).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def split_entries(reference_file_text: str) -> dict:
    """Split a distilled reference file into {entry_title: entry_text} by `### ` headings."""
    entries = {}
    current_title = None
    current_lines = []
    for line in reference_file_text.split("\n"):
        if line.startswith("### "):
            if current_title is not None:
                entries[current_title] = "\n".join(current_lines)
            current_title = line[4:].strip()
            current_lines = [line]
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        entries[current_title] = "\n".join(current_lines)
    return entries


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: compute_hash.py <file>", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        print(content_hash(f.read()))
