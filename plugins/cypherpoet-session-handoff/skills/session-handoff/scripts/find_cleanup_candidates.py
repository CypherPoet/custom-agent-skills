#!/usr/bin/env python3
"""
Find handoff documents that are safe to retire.

Read-only. This surfaces cleanup candidates so the session-handoff CLEANUP
workflow can present them for per-item approval — it never deletes anything
itself. Removal (git rm / trash + commit) stays under the agent's explicit,
approval-gated control, the same way the other scripts here only analyze.

A handoff is a candidate only when its work has demonstrably moved on:

  - 🔴 SUPERSEDED + COMPLETE: a later handoff `--continues-from` it (or names it
    under `**Supersedes**:`) AND it has no remaining `[TODO:` placeholders. The
    chain moved past finished work, so the record is reference-only.

Supersession is the only reliable "moved-past" signal, so it's the only trigger.
Age/staleness is deliberately NOT used: an old handoff can be the only record of
a decision, and "stale" (repo churn) says nothing about whether the work is done
or abandoned — run `list_handoffs.py` (it shows dates) or `check_staleness.py` to
eyeball age on demand. A handoff that is superseded but still carries unfinished
TODOs is surfaced as KEEP + REVIEW, never auto-retired.

Scans the neutral `.agents/handoffs/` and the legacy `.claude/handoffs/`
locations (plus any HANDOFF_DIR override) through the shared resolver, so
candidates surface wherever they live and the report says which directory each
one is in.

Usage:
    python3 find_cleanup_candidates.py [project-path]   # defaults to cwd
    python3 find_cleanup_candidates.py --verbose         # also list kept handoffs

Exit code: 0 when there are no candidates, 1 when at least one candidate exists.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Import the shared resolver and the read-side helpers the same way the sibling
# scripts do, so this resolves regardless of the current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from handoff_paths import (  # noqa: E402
    LEGACY_HANDOFFS_SUBDIR,
    NEUTRAL_HANDOFFS_SUBDIR,
    iter_handoff_files,
    project_root_for,
)
from list_handoffs import check_completion_status, extract_title  # noqa: E402
from check_staleness import run_cmd  # noqa: E402


# `**Continues from**: [<filename>](./<filename>)` — the auto-generated chain
# link emitted by create_handoff.build_chain_section (the single producer of
# this format; keep this parser in sync if that writer changes). Fresh handoffs
# emit `**Continues from**: None (fresh start)` (no brackets), so this naturally
# matches only real predecessors.
CONTINUES_FROM_RE = re.compile(r"\*\*Continues from\*\*:\s*\[([^\]]+)\]")
# `**Supersedes**:` is author free-text. Only treat tokens that look like an
# actual handoff filename as a signal, so the scaffold's placeholder text
# ("[list any older handoffs ...]") is ignored.
SUPERSEDES_RE = re.compile(r"\*\*Supersedes\*\*:\s*(.+)")
HANDOFF_FILENAME_RE = re.compile(r"\d{4}-\d{2}-\d{2}-\d{6}-[^\s\]\)/]+\.md")


def build_supersession_index(handoffs: list[dict]) -> dict[str, str]:
    """Map each superseded handoff filename -> the filename that supersedes it.

    Primary signal: a handoff's `**Continues from**: [<file>]` link names its
    predecessor (the machine-reliable, auto-generated marker). Secondary signal:
    any handoff filename listed on a `**Supersedes**:` line (author-declared).
    """
    superseded: dict[str, str] = {}
    for h in handoffs:
        content = h["content"]
        for match in CONTINUES_FROM_RE.finditer(content):
            predecessor = Path(match.group(1).strip()).name
            superseded.setdefault(predecessor, h["filename"])
        # finditer (not search) so a multi-line `**Supersedes**:` block — one
        # handoff retiring several predecessors — indexes every listed file.
        for supersedes_line in SUPERSEDES_RE.finditer(content):
            for name in HANDOFF_FILENAME_RE.findall(supersedes_line.group(1)):
                superseded.setdefault(name, h["filename"])
    return superseded


def is_git_tracked(filepath: Path, project_root: str) -> bool:
    """Whether git tracks this handoff — decides git rm vs trash at removal."""
    success, _ = run_cmd(
        ["git", "ls-files", "--error-unmatch", str(filepath)], cwd=project_root
    )
    return success


def location_label(filepath: Path) -> str:
    """Short tag for which handoff directory a file lives in."""
    parts = filepath.resolve().parts
    if tuple(parts[-3:-1]) == NEUTRAL_HANDOFFS_SUBDIR:
        return "neutral"
    if tuple(parts[-3:-1]) == LEGACY_HANDOFFS_SUBDIR:
        return "legacy"
    return "override"


def classify(handoffs: list[dict]) -> list[dict]:
    """Tag every handoff with a tier and a human-readable reason."""
    superseded = build_supersession_index(handoffs)
    # project_root_for shells out to git but depends only on a handoff's parent
    # directory, so derive it once per directory rather than once per file.
    root_by_dir: dict[Path, str] = {}
    results: list[dict] = []

    for h in handoffs:
        path: Path = h["path"]
        complete: bool = h["complete"]
        is_superseded = h["filename"] in superseded

        if is_superseded and not complete:
            tier = "KEEP_REVIEW"
            reason = (
                f"superseded by {superseded[h['filename']]} but still has "
                "unfinished TODOs — review before retiring"
            )
        elif is_superseded and complete:
            tier = "RETIRE"
            reason = (
                f"superseded by {superseded[h['filename']]}; complete (no TODOs)"
            )
        else:
            tier = "KEEP"
            reason = (
                "still has unfinished TODOs — active work"
                if not complete
                else "complete; no successor"
            )

        if path.parent not in root_by_dir:
            root_by_dir[path.parent] = project_root_for(str(path))
        results.append({
            "filename": h["filename"],
            "title": h["title"],
            "path": str(path),
            "tier": tier,
            "reason": reason,
            "tracked": is_git_tracked(path, root_by_dir[path.parent]),
            "location": location_label(path),
        })

    # Date-prefixed filenames sort chronologically — stable, legible numbering
    # independent of filesystem glob order.
    results.sort(key=lambda r: r["filename"])
    return results


def collect_handoffs(project_path: str) -> list[dict]:
    handoffs: list[dict] = []
    for filepath in iter_handoff_files(project_path):
        try:
            content = filepath.read_text()
        except OSError:
            continue
        handoffs.append({
            "path": filepath,
            "filename": filepath.name,
            "title": extract_title(filepath),
            "content": content,
            "complete": check_completion_status(filepath) == "Complete",
        })
    return handoffs


def _print_tier(title: str, items: list[dict], start_index: int) -> int:
    if not items:
        return start_index
    print(f"\n{title}")
    print("-" * 72)
    index = start_index
    for item in items:
        removal = "git rm" if item["tracked"] else "trash (untracked)"
        print(f"  {index}. {item['filename']}  [{item['location']}]")
        print(f"     title:   {item['title']}")
        print(f"     reason:  {item['reason']}")
        print(f"     removal: {removal}")
        index += 1
    return index


def print_report(results: list[dict], project_path: str, verbose: bool) -> int:
    retire = [r for r in results if r["tier"] == "RETIRE"]
    keep_review = [r for r in results if r["tier"] == "KEEP_REVIEW"]
    keep = [r for r in results if r["tier"] == "KEEP"]

    print("=" * 72)
    print("Handoff Cleanup Candidates")
    print("=" * 72)
    # Name the scanned root so a wrong-directory run (it defaults to cwd) is
    # obvious rather than a silent "no candidates" false negative.
    print(f"Scanned {len(results)} handoff(s) in {Path(project_path).resolve()}.")

    _print_tier("🔴 Retire — superseded + complete", retire, 1)

    if keep_review:
        print("\n⚠️  Keep + review — superseded but still has unfinished TODOs")
        print("-" * 72)
        for item in keep_review:
            print(f"  - {item['filename']}: {item['reason']}")

    candidate_count = len(retire)
    if candidate_count == 0:
        print("\nNo cleanup candidates — nothing is both superseded and complete.")
    else:
        print(
            f"\n{candidate_count} candidate(s) — each superseded by a later handoff "
            "and free of open TODOs. Staleness/age is not a trigger; an old but "
            "unsuperseded record is legitimate to keep."
        )
        print(
            "Present these for per-item approval before removing. Removal: "
            "`git rm <path>` for tracked files (git history is the undo), "
            "`trash <path>` for untracked ones — then commit the removals."
        )

    if verbose and keep:
        print(f"\n⚪ Keeping {len(keep)} handoff(s):")
        print("-" * 72)
        for item in keep:
            print(f"  - {item['filename']}: {item['reason']}")
    elif keep:
        print(f"\n(Keeping {len(keep)} other handoff(s); pass --verbose to list.)")

    return candidate_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find handoff documents that are safe to retire (read-only)."
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Project root to scan (default: current directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also list the handoffs being kept and why",
    )
    args = parser.parse_args()

    handoffs = collect_handoffs(args.project_path)
    if not handoffs:
        print(
            f"No handoffs found in {args.project_path} "
            "(.agents/handoffs/ or .claude/handoffs/). Nothing to clean up."
        )
        sys.exit(0)

    results = classify(handoffs)
    candidate_count = print_report(results, args.project_path, args.verbose)
    sys.exit(1 if candidate_count else 0)


if __name__ == "__main__":
    main()
