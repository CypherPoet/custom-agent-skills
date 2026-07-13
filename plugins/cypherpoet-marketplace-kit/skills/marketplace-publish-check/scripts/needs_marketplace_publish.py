#!/usr/bin/env python3
"""Read-only check: does the current branch require a marketplace-publish?

Diffs the *marketplace catalog surface* between a base ref (default: main) and
HEAD, and reports the plugins whose surface changed:
  - every plugins/*/.claude-plugin/plugin.json — a plugin added or removed, or
    its name / description / homepage edited (the Claude catalog fields);
  - scripts/dual-harness.json — a plugin's dual-harness classification or its
    Codex `category` changed (the Codex catalog fields).
A version-only bump does NOT count: that's content, gated by the version key,
and reaches installs without a catalog re-publish.

Both snapshots are taken at the merge base of the base ref and HEAD, so changes
that landed on the base after this branch forked are never attributed to it.

Use it when opening a PR to decide whether to apply the `marketplace-publish`
label. Stdlib only — no jq, no network. Exit status is 1 when a publish is
needed (something actionable), else 0; 2 on error (including a malformed
scripts/dual-harness.json — never silently treated as a catalog removal).

Usage: python3 .../needs_marketplace_publish.py [base-ref]   # base-ref defaults to "main"
"""

import json
import subprocess
import sys
from pathlib import Path

# The manifest fields the Claude marketplace catalog (marketplace.json) actually stores.
CATALOG_FIELDS = ("name", "description", "homepage")
MANIFEST_GLOB = "plugins/*/.claude-plugin/plugin.json"
# The config whose classification + categories the Codex catalog stores.
DUAL_HARNESS_PATH = "scripts/dual-harness.json"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def repo_root():
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(res.stdout.strip()) if res.returncode == 0 else Path.cwd()


def signature(root, ref, path):
    """The catalog fields of <path> at <ref>, or None if the file is absent there."""
    res = git(root, "show", f"{ref}:{path}")
    if res.returncode != 0:
        return None
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError:
        return None
    return {k: data.get(k) for k in CATALOG_FIELDS}


def plugin_name(path):
    # path is plugins/<name>/.claude-plugin/plugin.json
    return Path(path).parts[1]


def codex_categories(root, ref):
    """{plugin: category} from dual_harness_plugins in scripts/dual-harness.json at <ref>.

    {} when the file doesn't exist at <ref> (no Codex catalog surface there — e.g. the
    commit that first introduces it). A file that exists but is malformed raises
    ValueError: that's an error to surface (exit 2), not a mass catalog removal."""
    res = git(root, "show", f"{ref}:{DUAL_HARNESS_PATH}")
    if res.returncode != 0:
        return {}
    try:
        entries = json.loads(res.stdout).get("dual_harness_plugins", {})
        return {name: entry.get("category") for name, entry in entries.items()}
    except (json.JSONDecodeError, AttributeError) as e:
        raise ValueError(f"{DUAL_HARNESS_PATH} at {ref} is malformed: {e}")


def merge_base(root, base):
    """SHA of the merge base of <base> and HEAD; falls back to <base> when unresolvable."""
    res = git(root, "merge-base", base, "HEAD")
    sha = res.stdout.strip()
    return sha if res.returncode == 0 and sha else base


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    root = repo_root()
    # Snapshot "before" at the merge base, not the base tip — the diff below already uses
    # merge-base semantics (base...HEAD), so reading file contents at the tip would blame
    # this branch for changes that landed on the base after it forked.
    mb = merge_base(root, base)

    diff = git(root, "diff", "--name-only", "--diff-filter=AMD", f"{base}...HEAD", "--", MANIFEST_GLOB)
    if diff.returncode != 0:
        print(f"ERROR: could not diff {base}...HEAD ({diff.stderr.strip()})", file=sys.stderr)
        return 2

    reasons_by_plugin = {}

    def flag(name, reason):
        reasons_by_plugin.setdefault(name, []).append(reason)

    for path in (line for line in diff.stdout.splitlines() if line.strip()):
        before = signature(root, mb, path)
        after = signature(root, "HEAD", path)
        if before == after:
            continue  # manifest touched, but catalog fields unchanged (e.g. a version-only bump)
        if before is None:
            reason = "added"
        elif after is None:
            reason = "removed"
        else:
            reason = "changed " + ", ".join(k for k in CATALOG_FIELDS if before.get(k) != after.get(k))
        flag(plugin_name(path), reason)

    try:
        before_codex = codex_categories(root, mb)
        after_codex = codex_categories(root, "HEAD")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    for name in set(before_codex) | set(after_codex):
        if name not in before_codex:
            flag(name, "added to the Codex catalog surface")
        elif name not in after_codex:
            flag(name, "left the Codex catalog surface")
        elif before_codex[name] != after_codex[name]:
            flag(name, "changed Codex category")

    affected = sorted((name, "; ".join(reasons)) for name, reasons in reasons_by_plugin.items())
    if not affected:
        print(f"marketplace-publish-check — no catalog-surface change vs {base}. No publish needed.")
        return 0

    plural = "plugin" if len(affected) == 1 else "plugins"
    verb = "needs" if len(affected) == 1 else "need"
    print(f"marketplace-publish-check — {len(affected)} {plural} {verb} a marketplace-publish vs {base}:\n")
    width = max(len(name) for name, _ in affected)
    for name, reason in affected:
        print(f"  {name:<{width}}  ({reason})")
    print("\nApply the `marketplace-publish` label to this PR.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
