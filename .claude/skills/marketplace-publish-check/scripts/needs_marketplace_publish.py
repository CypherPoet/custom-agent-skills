#!/usr/bin/env python3
"""Read-only check: does the current branch require a marketplace-publish?

Diffs every plugins/*/.claude-plugin/plugin.json between a base ref (default:
main) and HEAD, and reports the plugins whose *marketplace catalog surface*
changed — a plugin added or removed, or its name / description / homepage
edited. A version-only bump does NOT count: that's content, gated by the
version key, and reaches installs without a catalog re-publish.

Use it when opening a PR to decide whether to apply the `marketplace-publish`
label. Stdlib only — no jq, no network. Following the repo's other audit
script, exit status is 1 when there's something actionable (a publish is
needed), else 0; 2 on error.

Usage: python3 .../needs_marketplace_publish.py [base-ref]   # base-ref defaults to "main"
"""

import json
import subprocess
import sys
from pathlib import Path

# The manifest fields the marketplace catalog (marketplace.json) actually stores.
CATALOG_FIELDS = ("name", "description", "homepage")
MANIFEST_GLOB = "plugins/*/.claude-plugin/plugin.json"


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


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    root = repo_root()

    diff = git(root, "diff", "--name-only", "--diff-filter=AMD", f"{base}...HEAD", "--", MANIFEST_GLOB)
    if diff.returncode != 0:
        print(f"ERROR: could not diff {base}...HEAD ({diff.stderr.strip()})", file=sys.stderr)
        return 2

    affected = []
    for path in (line for line in diff.stdout.splitlines() if line.strip()):
        before = signature(root, base, path)
        after = signature(root, "HEAD", path)
        if before == after:
            continue  # manifest touched, but catalog fields unchanged (e.g. a version-only bump)
        if before is None:
            reason = "added"
        elif after is None:
            reason = "removed"
        else:
            reason = "changed " + ", ".join(k for k in CATALOG_FIELDS if before.get(k) != after.get(k))
        affected.append((plugin_name(path), reason))

    affected.sort()
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
