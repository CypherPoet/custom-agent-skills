#!/usr/bin/env python3
"""Read-only check: does the current branch require a marketplace-publish?

Diffs the *marketplace catalog surface* between a base ref (default: main) and
HEAD, and reports the plugins whose surface changed:
  - every plugins/*/.claude-plugin/plugin.json — a plugin added or removed, or
    its name / description / homepage edited (the Claude catalog fields);
  - scripts/plugin-registry.json — a plugin's dual-harness classification,
    `category`, or generated Codex source path changed (the Codex catalog surface).
A version-only bump does NOT count: that's content, gated by the version key,
and reaches installs without a catalog re-publish.

Both snapshots are taken at the merge base of the base ref and HEAD, so changes
that landed on the base after this branch forked are never attributed to it.

Use it when opening a PR to decide whether to apply the `marketplace-publish`
label. Stdlib only — no jq, no network. Exit status is 1 when a publish is
needed (something actionable), else 0; 2 on error (including a malformed
scripts/plugin-registry.json or plugin manifest — never silently treated as a
catalog removal).

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
PLUGIN_REGISTRY_PATH = "scripts/plugin-registry.json"
# The registry was named dual-harness.json before 2026-07; reading refs that
# predate the rename must keep working.
LEGACY_REGISTRY_PATH = "scripts/dual-harness.json"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8")


def repo_root():
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8")
    return Path(res.stdout.strip()) if res.returncode == 0 else Path.cwd()


def signature(root, ref, path):
    """The catalog fields of <path> at <ref>, or None if the file is absent there.

    A file that exists but is malformed raises ValueError: that's an error to
    surface (exit 2), never silently read as an addition or removal."""
    res = git(root, "show", f"{ref}:{path}")
    if res.returncode != 0:
        return None
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} at {ref} is malformed: {e}")
    if not isinstance(data, dict):
        raise ValueError(f"{path} at {ref} is malformed: manifest must be a JSON object")
    return {k: data.get(k) for k in CATALOG_FIELDS}


def plugin_name(path):
    # path is plugins/<name>/.claude-plugin/plugin.json
    return Path(path).parts[1]


def codex_entries(root, ref):
    """Codex catalog fields derived from the plugin registry at <ref>.

    Membership captures the dual-harness classification. Category is copied into
    a per-plugin Codex catalog entry; interface metadata stays in the generated
    plugin manifest and must not request a catalog publish. {} when the file doesn't
    exist at <ref>. A malformed file raises ValueError instead of looking like a
    mass catalog removal."""
    shown_path = PLUGIN_REGISTRY_PATH
    res = git(root, "show", f"{ref}:{shown_path}")
    if res.returncode != 0:
        shown_path = LEGACY_REGISTRY_PATH
        res = git(root, "show", f"{ref}:{shown_path}")
    if res.returncode != 0:
        return {}
    try:
        entries = json.loads(res.stdout).get("dual_harness_plugins", {})
        if not isinstance(entries, dict) or not all(isinstance(v, dict) for v in entries.values()):
            raise ValueError("dual_harness_plugins entries must be objects")
        return {
            name: {"category": metadata.get("category")}
            for name, metadata in entries.items()
        }
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        raise ValueError(f"{shown_path} at {ref} is malformed: {e}")


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

    # --no-renames: git's rename detection would report a renamed plugin as a single
    # R pair that --diff-filter=AMD silently drops, hiding a remove+add surface change.
    diff = git(root, "diff", "--name-only", "--no-renames", "--diff-filter=AMD", f"{base}...HEAD", "--", MANIFEST_GLOB)
    if diff.returncode != 0:
        print(f"ERROR: could not diff {base}...HEAD ({diff.stderr.strip()})", file=sys.stderr)
        return 2

    reasons_by_plugin = {}

    def flag(name, reason):
        reasons_by_plugin.setdefault(name, []).append(reason)

    try:
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

        before_codex = codex_entries(root, mb)
        after_codex = codex_entries(root, "HEAD")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    for name in set(before_codex) | set(after_codex):
        if name not in before_codex:
            flag(name, "added to the Codex catalog surface")
        elif name not in after_codex:
            flag(name, "left the Codex catalog surface")
        elif before_codex[name] != after_codex[name]:
            b, a = before_codex[name], after_codex[name]
            changed = sorted(k for k in set(b) | set(a) if b.get(k) != a.get(k))
            flag(name, "changed Codex " + ", ".join(changed))

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
