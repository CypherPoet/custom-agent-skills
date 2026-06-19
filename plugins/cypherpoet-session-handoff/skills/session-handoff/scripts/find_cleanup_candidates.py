#!/usr/bin/env python3
"""
Find handoff documents that are safe to retire.

Read-only. This surfaces cleanup candidates so the session-handoff CLEANUP
workflow can present them for per-item approval — it never deletes anything
itself. Removal (git rm / trash + commit) stays under the agent's explicit,
approval-gated control, the same way the other scripts here only analyze.

A handoff becomes a candidate only when its work has demonstrably moved on:

  - 🔴 SUPERSEDED + COMPLETE (strong): a later handoff `--continues-from` it AND
    it has no remaining `[TODO:` placeholders. The chain moved past finished
    work, so the record is reference-only.
  - 🟡 VERY_STALE + COMPLETE (advisory): check_staleness rates it VERY_STALE, it
    has no TODOs, and nothing supersedes it. Old, done, unlikely to resume.

Staleness alone is never a trigger — an old handoff can be the only record of a
decision, which is legitimate to keep. Completion + supersession is the safe
signal; very-stale is advisory. A handoff that is superseded but still carries
unfinished TODOs is surfaced as KEEP + REVIEW, never auto-retired.

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
import subprocess
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
from check_staleness import check_staleness  # noqa: E402


# `**Continues from**: [<filename>](./<filename>)` — the auto-generated chain
# link. Fresh handoffs emit `**Continues from**: None (fresh start)` (no
# brackets), so this naturally matches only real predecessors.
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
        supersedes_line = SUPERSEDES_RE.search(content)
        if supersedes_line:
            for name in HANDOFF_FILENAME_RE.findall(supersedes_line.group(1)):
                superseded.setdefault(name, h["filename"])
    return superseded


def is_git_tracked(filepath: Path, project_root: str) -> bool:
    """Whether git tracks this handoff — decides git rm vs trash at removal."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(filepath)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
    return result.returncode == 0


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
    results: list[dict] = []

    for h in handoffs:
        path: Path = h["path"]
        complete: bool = h["complete"]
        is_superseded = h["filename"] in superseded
        # A handoff that itself `--continues-from` another is the live tip of a
        # chain — current state, not a disposable record. Age alone must not
        # retire it, so it's excluded from the very-stale advisory tier.
        is_chain_tip = bool(CONTINUES_FROM_RE.search(h["content"]))

        stale = check_staleness(str(path))
        level = stale.get("staleness_level", "UNKNOWN")

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
        elif level == "VERY_STALE" and complete and not is_chain_tip:
            tier = "RETIRE_ADVISORY"
            reason = "very stale and complete; standalone (no successor, not a chain tip)"
        else:
            tier = "KEEP"
            reason = _keep_reason(level, complete, is_chain_tip)

        project_root = project_root_for(str(path))
        results.append({
            "filename": h["filename"],
            "title": h["title"],
            "path": str(path),
            "tier": tier,
            "reason": reason,
            "staleness": level,
            "tracked": is_git_tracked(path, project_root),
            "location": location_label(path),
        })

    # Date-prefixed filenames sort chronologically — stable, legible numbering
    # independent of filesystem glob order.
    results.sort(key=lambda r: r["filename"])
    return results


def _keep_reason(level: str, complete: bool, is_chain_tip: bool) -> str:
    if not complete:
        return "still has unfinished TODOs — active work"
    if is_chain_tip:
        return f"complete chain tip ({level.lower()}) — kept as the latest in its chain"
    if level in ("FRESH", "SLIGHTLY_STALE", "STALE"):
        return f"complete but current ({level.lower()}); no successor"
    return "complete; no successor"


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


def print_report(results: list[dict], verbose: bool) -> int:
    retire = [r for r in results if r["tier"] == "RETIRE"]
    advisory = [r for r in results if r["tier"] == "RETIRE_ADVISORY"]
    keep_review = [r for r in results if r["tier"] == "KEEP_REVIEW"]
    keep = [r for r in results if r["tier"] == "KEEP"]

    print("=" * 72)
    print("Handoff Cleanup Candidates")
    print("=" * 72)
    print(f"Scanned {len(results)} handoff(s).")

    next_index = 1
    next_index = _print_tier(
        "🔴 Retire — superseded + complete (strong candidates)", retire, next_index
    )
    next_index = _print_tier(
        "🟡 Retire candidate — very stale + complete (advisory)", advisory, next_index
    )

    if keep_review:
        print("\n⚠️  Keep + review — superseded but still has unfinished TODOs")
        print("-" * 72)
        for item in keep_review:
            print(f"  - {item['filename']}: {item['reason']}")

    candidate_count = len(retire) + len(advisory)
    if candidate_count == 0:
        print("\nNo cleanup candidates — nothing is both finished and moved-past.")
    else:
        print(
            f"\n{candidate_count} candidate(s). Staleness alone never qualifies a "
            "handoff; an old but unsuperseded record is legitimate to keep."
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
    candidate_count = print_report(results, args.verbose)
    sys.exit(1 if candidate_count else 0)


if __name__ == "__main__":
    main()
