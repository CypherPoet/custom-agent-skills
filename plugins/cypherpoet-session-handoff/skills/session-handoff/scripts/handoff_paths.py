#!/usr/bin/env python3
"""
Shared path resolution for the handoff scripts.

A handoff is a durable, shareable project artifact — not host-private config —
so its canonical home is a tool-neutral `.agents/handoffs/` at the project root,
usable by any agent (Claude Code, Codex, Cursor, …). Reads still fall back to
the legacy `.claude/handoffs/` location so handoffs written before this change
keep resolving and chaining.

An optional HANDOFF_DIR environment variable (or the `--dir` flag, which sets
it) overrides the location entirely — the escape hatch for anyone who wants a
specific directory.

This module is the single source of truth for those paths. The four scripts add
their own directory to sys.path and import it, so it resolves regardless of the
current working directory:

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from handoff_paths import resolve_write_dir, candidate_read_dirs, project_root_for
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Canonical, host-neutral handoff directory, relative to the project root.
NEUTRAL_HANDOFFS_SUBDIR = (".agents", "handoffs")
# Legacy Claude Code location — still read so existing handoffs keep resolving.
LEGACY_HANDOFFS_SUBDIR = (".claude", "handoffs")

ENV_OVERRIDE = "HANDOFF_DIR"


def _override_dir(project_path: str | os.PathLike) -> Path | None:
    """Return the HANDOFF_DIR override as a Path, or None when unset.

    A relative override is resolved against the project path so it behaves the
    same whether a script runs from the project root or elsewhere. `~` expands.
    """
    raw = os.environ.get(ENV_OVERRIDE)
    if not raw:
        return None
    override = Path(raw).expanduser()
    if not override.is_absolute():
        override = Path(project_path) / override
    return override


def resolve_write_dir(project_path: str | os.PathLike) -> Path:
    """Directory new handoffs are written to.

    The HANDOFF_DIR override if set, otherwise the neutral `.agents/handoffs/`.
    """
    override = _override_dir(project_path)
    if override is not None:
        return override
    return Path(project_path).joinpath(*NEUTRAL_HANDOFFS_SUBDIR)


def candidate_read_dirs(project_path: str | os.PathLike) -> list[Path]:
    """Existing handoff directories to read from, in priority order.

    Override (if set) → neutral `.agents/handoffs/` → legacy `.claude/handoffs/`.
    Only directories that exist are returned, deduped by resolved path, so
    callers can union their contents and still surface handoffs written before
    the neutral-dir migration.
    """
    root = Path(project_path)
    candidates: list[Path] = []
    override = _override_dir(project_path)
    if override is not None:
        candidates.append(override)
    candidates.append(root.joinpath(*NEUTRAL_HANDOFFS_SUBDIR))
    candidates.append(root.joinpath(*LEGACY_HANDOFFS_SUBDIR))

    seen: set[str] = set()
    existing: list[Path] = []
    for candidate in candidates:
        try:
            key = str(candidate.resolve())
        except OSError:
            key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_dir():
            existing.append(candidate)
    return existing


def iter_handoff_files(project_path: str | os.PathLike):
    """Yield every handoff `*.md` across the candidate read directories, once.

    Walks `candidate_read_dirs()` in priority order and dedupes by filename, so
    a handoff present in both the neutral and legacy locations surfaces only
    from the higher-priority directory. Callers layer their own per-file
    metadata extraction on top — this owns the directory-union + dedupe so the
    read-side scripts don't each re-implement it."""
    seen_names: set[str] = set()
    for handoffs_dir in candidate_read_dirs(project_path):
        for filepath in handoffs_dir.glob("*.md"):
            if filepath.name in seen_names:
                continue
            seen_names.add(filepath.name)
            yield filepath


def _git_toplevel(start: Path) -> str | None:
    """Best-effort `git rev-parse --show-toplevel` from `start`, or None."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=str(start),
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def project_root_for(handoff_file: str | os.PathLike) -> str:
    """Best-effort project root for a handoff file.

    Replaces the old fixed-depth `path.parent.parent.parent`, which only held
    for a 3-level `.claude/handoffs/` layout. Resolution order:

    1. git toplevel of the handoff's directory — handles worktrees and any
       nesting depth.
    2. else, strip a recognized `<marker>/handoffs` tail (`.agents` or
       `.claude`) from the directory path.
    3. else, the original `parent.parent.parent` fallback, which is correct for
       the 2-level `<root>/x/handoffs/` shape the markers use.

    A HANDOFF_DIR override that lives outside the project (and isn't itself in a
    git repo) can't be mapped back to the real project root from the handoff
    path alone — only the fallback's shape assumption applies. Keep such
    overrides inside the (git) project when staleness/validation need an
    accurate root.
    """
    path = Path(handoff_file).resolve()
    handoffs_dir = path.parent

    top = _git_toplevel(handoffs_dir)
    if top:
        return top

    parts = handoffs_dir.parts
    for marker in (NEUTRAL_HANDOFFS_SUBDIR, LEGACY_HANDOFFS_SUBDIR):
        n = len(marker)
        if len(parts) > n and tuple(parts[-n:]) == marker:
            return str(Path(*parts[:-n]))

    return str(path.parent.parent.parent)
