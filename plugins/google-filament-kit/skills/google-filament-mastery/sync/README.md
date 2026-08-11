# Corpus Sync

This skill's `references/` are distilled from the official Filament docs and the `google/filament` source, pinned to a tag (see `source_tag` in [`filament-sync-manifest.json`](filament-sync-manifest.json)). This directory tracks that provenance and detects when upstream has drifted so a re-sync only re-distills what actually changed.

- **`filament-sync-manifest.json`** — for the pinned tag: every upstream **source** (repo path, raw URL, `raw_hash`, and which reference files it feeds) and every distilled **reference file** (`content_hash`). All hashes are computed by `build_manifest.py`, never hand-edited.
- **`scripts/compute_hash.py`** — shared canonicalization (v1) + SHA-256. Drops the volatile `> Source:` / `> Last synced:` header lines so a date-only bump doesn't move a hash.
- **`scripts/build_manifest.py`** — (re)seeds the manifest from a `raw/` dir of fetched sources. Holds the authoritative source→reference map.
- **`scripts/diff_filament.py`** — model-free drift check: recomputes `raw_hash` for a fresh fetch and reports which sources `CHANGED` and the exact reference files to re-distill.

## Re-syncing to a newer Filament release

1. **Fetch** the manifest's sources at the new tag into a `raw/` dir laid out like the build workspace. The repo paths and the local layout are the `SOURCES` table in `build_manifest.py`; the per-source `url` in the manifest points at the old tag — swap the tag.
2. **Diff**: `python scripts/diff_filament.py --manifest filament-sync-manifest.json --raw-dir <fresh-raw>`. Exit 1 means drift; the output lists the `reference_files` to re-distill (and any `MISSING` sources — usually a moved/renamed upstream path to fix in `SOURCES`).
3. **Re-distill** only the impacted reference files from the fresh sources, keeping the accuracy rules (quote signatures verbatim from headers; preserve physical units; don't fabricate).
4. **Re-seed**: `python scripts/build_manifest.py --raw-dir <fresh-raw> --references-dir ../references --out filament-sync-manifest.json --tag <new-tag> --version <new-version> --date <YYYY-MM-DD>`.
5. **Bump** the plugin `version` in `plugin.json` (Claude Code's update cache key) and update the `Last synced` lines in the changed references and in `SKILL.md`.

All scripts are stdlib-only and run locally — no network calls inside them (you fetch sources yourself in step 1), no tokens, no writes except `build_manifest.py` writing the manifest.
