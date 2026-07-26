#!/usr/bin/env python3
"""Fail when a plugin's shipped content changed without a version bump.

A plugin's `version` in .claude-plugin/plugin.json is each harness's update
cache key: content reaches installed users only when that version changes.
Merging to main alone never ships it. Two failure modes, both caught here:

  1. No bump — the plugin's shipped content changed vs. the merge base, but
     its version did not.
  2. Absorbed bump — the branch bumps to a version the base branch already
     published (e.g. both bump 0.5.0 -> 0.6.0 in parallel). The merge is
     textually clean, yet the branch's content ships under a version that is
     already out there, so installs never see it.

One rule covers both: when a plugin's shipped content changed vs. the merge
base, its version at HEAD must be strictly greater than the merge-base version
AND different from the version at the base tip.

"Shipped content" is defined by the sync generator, not restated here — this
imports its ignore predicates, so anything stripped from a vendored copy
(`evals/`, `*-workspace/`, `__pycache__/`, …) never reaches an install and
therefore needs no bump.

Stdlib only — no network. Exit status is 1 when a bump is missing (something
actionable), 0 when clean or when the comparison cannot be made (shallow clone,
missing base ref — always reported, never a silent pass), 2 on error.

Usage: python3 scripts/check_version_bumps.py [base-ref]   # base-ref defaults to "main"
"""

import json
import subprocess
import sys
from pathlib import Path

# Reuse the generator's own ignore predicates so "content that ships to an
# install" has exactly one definition in this repo. Importing sync_plugins is
# side-effect free (it guards its entry point).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_plugins import _dir_ignored, _file_ignored  # noqa: E402

MANIFEST = "plugins/{plugin}/.claude-plugin/plugin.json"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8"
    )


def repo_root():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8"
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()


def ships(relative_path):
    """True when this path is part of what an install actually receives.

    parts[0] is "plugins" and parts[1] the plugin name, so the directories that
    decide shippability are everything between the plugin root and the file."""
    parts = Path(relative_path).parts
    if len(parts) < 3:
        return False
    if any(_dir_ignored(part) for part in parts[2:-1]):
        return False
    return not _file_ignored(parts[-1])


def version_at(root, ref, plugin):
    """The plugin's version at <ref>, or None when it has no manifest there.

    A manifest that exists but is malformed raises ValueError: that is an error
    to surface (exit 2), never silently read as a missing plugin."""
    path = MANIFEST.format(plugin=plugin)
    result = git(root, "show", f"{ref}:{path}")
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} at {ref} is malformed: {error}")
    if not isinstance(data, dict):
        raise ValueError(f"{path} at {ref} is malformed: manifest must be a JSON object")
    return data.get("version")


def as_tuple(version):
    """(major, minor, patch) for comparison, or None when unparseable."""
    if not isinstance(version, str):
        return None
    fields = version.split(".")
    if len(fields) != 3 or not all(field.isdigit() for field in fields):
        return None
    return tuple(int(field) for field in fields)


def resolve_base(root, base):
    """The most up-to-date view of <base>: itself or its origin/ counterpart.

    Two reasons this is not just <base>. A CI checkout fetches remote branches
    into refs/remotes/origin/* without creating local branches, so a bare "main"
    is often unresolvable there. And locally, a stale `main` would hide an
    absorbed bump outright — that check compares against the base's *current*
    tip, so a base left behind at yesterday's commit reports a version as fresh
    when the real base already publishes it. When both refs exist, take whichever
    is further along; when they have diverged, the local ref wins."""
    existing = [
        ref
        for ref in (base, f"origin/{base}")
        if git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0
    ]
    if not existing:
        return base
    if len(existing) == 1:
        return existing[0]
    local, remote = existing
    behind = git(root, "merge-base", "--is-ancestor", local, remote).returncode == 0
    return remote if behind else local


def main():
    root = repo_root()
    base = resolve_base(root, sys.argv[1] if len(sys.argv) > 1 else "main")

    merge_base = git(root, "merge-base", base, "HEAD")
    if merge_base.returncode != 0 or not merge_base.stdout.strip():
        # A shallow clone or an unfetched base ref cannot be compared. Say so
        # rather than reporting a clean run that was never actually performed.
        print(
            f"check-version-bumps — SKIPPED: no merge base for {base}...HEAD "
            f"(shallow clone, or {base} not fetched). Nothing was verified."
        )
        return 0
    merge_base = merge_base.stdout.strip()

    # --no-renames: a renamed file reported as a single R pair would hide the
    # content change that a bump is owed for.
    diff = git(root, "diff", "--name-only", "--no-renames", f"{base}...HEAD", "--", "plugins/")
    if diff.returncode != 0:
        print(f"ERROR: could not diff {base}...HEAD ({diff.stderr.strip()})", file=sys.stderr)
        return 2

    touched = {}
    for line in diff.stdout.splitlines():
        path = line.strip()
        if path and ships(path):
            touched.setdefault(Path(path).parts[1], []).append(path)

    problems = []
    try:
        for plugin in sorted(touched):
            before = version_at(root, merge_base, plugin)
            head = version_at(root, "HEAD", plugin)
            if before is None or head is None:
                continue  # added or removed on this branch — nothing to bump against
            tip = version_at(root, base, plugin)

            before_parts, head_parts = as_tuple(before), as_tuple(head)
            if head_parts is None:
                problems.append((plugin, f"version {head!r} is not major.minor.patch"))
            elif head == before:
                problems.append((plugin, f"content changed, version still {before}"))
            elif before_parts is not None and head_parts <= before_parts:
                problems.append((plugin, f"version went backwards: {before} -> {head}"))
            elif head == tip and tip != before:
                problems.append((plugin, f"{head} is already published on {base} (absorbed bump)"))
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if not problems:
        print(f"check-version-bumps — every plugin changed vs {base} carries a fresh version.")
        return 0

    plural = "plugin" if len(problems) == 1 else "plugins"
    print(f"check-version-bumps — {len(problems)} {plural} shipping content without a usable bump:\n")
    width = max(len(plugin) for plugin, _ in problems)
    for plugin, reason in problems:
        print(f"  {plugin:<{width}}  ({reason})")
    print(
        "\nBump each plugin's version in .claude-plugin/plugin.json, then re-run"
        "\n`python3 scripts/sync_plugins.py` so the Codex manifest matches."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
