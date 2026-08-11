#!/usr/bin/env python3
"""Detect drift between the recorded Filament corpus and a fresh fetch.

Model-free, stdlib-only, no network, no writes. First step of a re-sync: fetch
the sources listed in the manifest at a NEW Filament tag into a raw/ dir (same
layout build_manifest.py expects), then run this to see what moved — so only the
affected reference files get re-distilled.

  diff_filament.py --manifest <filament-sync-manifest.json>
                   --raw-dir <dir of freshly fetched sources>
                   [--format text|json]

Buckets:
  CHANGED   a source whose fresh canonical raw_hash differs from the manifest's
  MISSING   a manifest source absent from --raw-dir (couldn't be checked)

For every CHANGED source, its `reference_files` are impacted; the union of those
is the re-distillation work list.

Exit codes: 0 = no drift, 1 = drift found, 2 = input/canonicalization error.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compute_hash as ch

# Mirror build_manifest's SOURCES mapping of repo_path -> local raw path, so a
# fresh fetch laid out like the workspace raw/ dir can be located from a manifest
# entry. Kept here (not imported) so this script stays usable on its own.
try:
    import build_manifest as bm
    REPO_TO_LOCAL = {repo_path: local for (local, repo_path, _cat, _refs) in bm.SOURCES}
except Exception:  # pragma: no cover - build_manifest should sit beside us
    REPO_TO_LOCAL = {}


def main():
    ap = argparse.ArgumentParser(description="Detect Filament corpus drift.")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--raw-dir", required=True, help="dir of freshly fetched sources")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args()

    try:
        with open(args.manifest, encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError) as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        return 2

    canon = manifest.get("hash_canonicalization")
    if canon != ch.CANONICALIZATION_VERSION:
        print(f"error: manifest canonicalization {canon!r} != script "
              f"{ch.CANONICALIZATION_VERSION!r}; re-seed before diffing", file=sys.stderr)
        return 2

    if not os.path.isdir(args.raw_dir):
        print(f"error: --raw-dir is not a directory: {args.raw_dir}", file=sys.stderr)
        return 2

    changed, missing = [], []
    impacted = set()
    for src in manifest["sources"]:
        repo_path = src["repo_path"]
        local = REPO_TO_LOCAL.get(repo_path)
        # Fall back to the repo path's basename layout if no map is available.
        candidate = os.path.join(args.raw_dir, local) if local else os.path.join(args.raw_dir, repo_path)
        if not os.path.exists(candidate):
            missing.append(repo_path)
            continue
        fresh = ch.hash_file(candidate)
        if fresh != src["raw_hash"]:
            changed.append(repo_path)
            impacted.update(src.get("reference_files", []))

    result = {
        "source_tag": manifest.get("source_tag"),
        "changed": sorted(changed),
        "missing": sorted(missing),
        "impacted_reference_files": sorted(impacted),
    }
    drift = bool(changed)

    if args.format == "json":
        print(json.dumps({"drift": drift, **result}, indent=2))
    else:
        print(f"baseline tag: {result['source_tag']}")
        print(f"CHANGED ({len(changed)}):")
        for c in result["changed"]:
            print(f"  - {c}")
        print(f"MISSING ({len(missing)}; not in --raw-dir, unchecked):")
        for m in result["missing"]:
            print(f"  - {m}")
        print(f"\nRe-distill these reference files ({len(impacted)}):")
        for r in result["impacted_reference_files"]:
            print(f"  - {r}")
        print("\nDRIFT" if drift else "\nno drift")

    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
