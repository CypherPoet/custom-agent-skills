#!/usr/bin/env python3
"""Canonicalize and hash Filament corpus content (canonicalization v1).

Shared by build_manifest.py and diff_filament.py so identical content always
yields identical hashes.

Two kinds of input are hashed:
  - distilled reference markdown (references/*.md) -> content_hash
  - raw upstream sources (Markdeep books, headers, mdBook notes, samples) -> raw_hash

Canonicalization v1 (same as the upstream-agnostic scheme used elsewhere in
this repo):
  1. Drop file-level volatile header lines (`> Source:`, `> Last synced:`) so a
     re-sync that only bumps the date doesn't move the content_hash.
  2. Normalize line endings to \n.
  3. Strip trailing whitespace from every line.
  4. Collapse runs of 3+ blank lines to a single blank line.
  5. Strip leading/trailing blank lines; end with exactly one newline.

Nothing semantic is reordered or lowercased — a real change in guidance or in an
upstream source is a real change and must move the hash.
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


def hash_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return content_hash(f.read())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: compute_hash.py <file>", file=sys.stderr)
        sys.exit(2)
    print(hash_file(sys.argv[1]))
