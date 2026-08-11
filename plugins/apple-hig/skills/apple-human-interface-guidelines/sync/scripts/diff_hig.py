#!/usr/bin/env python3
"""Detect drift between Apple's live HIG and this skill's recorded corpus.

Model-free, stdlib-only, no network, no writes. Runs as the first step of a
re-sync: re-scrape the live pages, then this script buckets what moved so only
the affected pages get re-distilled.

  diff_hig.py --manifest <hig-sync-manifest.json>
              [--url-map <firecrawl-map.json>]   # live page URLs (ADDED/REMOVED/MOVED)
              [--scrapes <dir of raw/<slug>.md>]  # fresh raw scrapes (CHANGED)
              [--format text|json]

Buckets:
  ADDED        live page with no manifest row (and not a skipped index page)
  REMOVED      manifest page no longer in the live URL map
  MAYBE-MOVED  an ADDED/REMOVED pair whose slugs look like a rename
  CHANGED      a still-present page whose fresh scrape's canonical hash differs
               from the manifest's recorded raw_hash baseline

CHANGED is a *candidate* signal computed from raw scrapes (pre-distillation), so
it can flag cosmetic edits too. The precise check — did the distilled guidance
actually change — happens after re-distillation by comparing the new
content_hash against the manifest (see build_manifest.py / compute_hash.py).

Exit codes: 0 = no drift, 1 = drift found, 2 = input or canonicalization error.
"""
import argparse
import difflib
import json
import os
import sys

# Reuse the seeding step's canonicalization so identical content hashes match.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compute_hash as ch

MOVE_SIMILARITY_THRESHOLD = 0.6


def slug_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def load_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pair_moves(added: set, removed: set):
    """Greedily pair likely renames (ADDED slug ~ REMOVED slug). Returns
    (moves, remaining_added, remaining_removed)."""
    moves = []
    a_left, r_left = set(added), set(removed)
    candidates = []
    for a in added:
        for r in removed:
            ratio = difflib.SequenceMatcher(None, a, r).ratio()
            if ratio >= MOVE_SIMILARITY_THRESHOLD:
                candidates.append((ratio, a, r))
    for ratio, a, r in sorted(candidates, reverse=True):
        if a in a_left and r in r_left:
            moves.append({"from": r, "to": a, "similarity": round(ratio, 3)})
            a_left.discard(a)
            r_left.discard(r)
    return moves, a_left, r_left


def main():
    ap = argparse.ArgumentParser(description="Detect HIG corpus drift.")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--url-map", help="firecrawl map JSON of live page URLs")
    ap.add_argument("--scrapes", help="directory of fresh raw <slug>.md scrapes")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args()

    if not args.url_map and not args.scrapes:
        print("error: pass --url-map and/or --scrapes (nothing to compare)", file=sys.stderr)
        return 2

    try:
        manifest = load_json(args.manifest)
    except (OSError, ValueError) as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        return 2

    canon = manifest.get("hash_canonicalization")
    if canon != ch.CANONICALIZATION_VERSION:
        print(f"error: manifest canonicalization {canon!r} != script "
              f"{ch.CANONICALIZATION_VERSION!r}; re-seed before diffing", file=sys.stderr)
        return 2

    recorded = {slug_of(p["url"]): p for p in manifest["pages"]}
    skipped = set(manifest.get("skipped_index_pages", []))

    added = removed = set()
    moves = []
    if args.url_map:
        try:
            live = {slug_of(p["url"]) for p in load_json(args.url_map)["pages"]}
        except (OSError, ValueError, KeyError) as e:
            print(f"error: cannot read url-map: {e}", file=sys.stderr)
            return 2
        added = live - set(recorded) - skipped
        removed = set(recorded) - live
        moves, added, removed = pair_moves(added, removed)

    changed, unchecked = [], []
    if args.scrapes:
        if not os.path.isdir(args.scrapes):
            print(f"error: --scrapes is not a directory: {args.scrapes}", file=sys.stderr)
            return 2
        if any("raw_hash" not in p for p in manifest["pages"]):
            print("error: manifest lacks raw_hash baseline (re-seed with schema_version >= 2)",
                  file=sys.stderr)
            return 2
        live_present = set(recorded)
        if args.url_map:
            live_present &= live
        for slug in sorted(live_present):
            scrape = os.path.join(args.scrapes, f"{slug}.md")
            if not os.path.exists(scrape):
                unchecked.append(slug)
                continue
            fresh = ch.content_hash(open(scrape, encoding="utf-8").read())
            if fresh != recorded[slug]["raw_hash"]:
                changed.append(slug)

    result = {
        "added": sorted(added),
        "removed": sorted(removed),
        "maybe_moved": moves,
        "changed": sorted(changed),
        "unchecked": sorted(unchecked),
    }
    drift = bool(result["added"] or result["removed"] or result["maybe_moved"] or result["changed"])

    if args.format == "json":
        print(json.dumps({"drift": drift, **result}, indent=2))
    else:
        def section(label, items):
            print(f"{label} ({len(items)}):")
            for it in items:
                print(f"  - {it}")
        section("ADDED", result["added"])
        section("REMOVED", result["removed"])
        print(f"MAYBE-MOVED ({len(moves)}):")
        for m in moves:
            print(f"  - {m['from']} -> {m['to']}  (similarity {m['similarity']})")
        section("CHANGED", result["changed"])
        if unchecked:
            print(f"unchecked (no fresh scrape; {len(unchecked)}): " + ", ".join(unchecked))
        print("\nDRIFT" if drift else "\nno drift")

    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
