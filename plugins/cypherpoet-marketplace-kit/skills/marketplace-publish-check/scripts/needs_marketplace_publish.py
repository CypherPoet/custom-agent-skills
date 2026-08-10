#!/usr/bin/env python3
"""Report source changes that require marketplace catalog publication.

Claude and Codex support are declared by their respective plugin manifests.
Only fields copied into a marketplace catalog count here; version and other
plugin-card changes ship with plugin content and do not require catalog edits.
"""

import json
import subprocess
import sys
from pathlib import Path


CLAUDE_CATALOG_FIELDS = ("name", "description", "homepage")
CLAUDE_MANIFEST_GLOB = "plugins/*/.claude-plugin/plugin.json"
CODEX_MANIFEST_GLOB = "plugins/*/.codex-plugin/plugin.json"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def repo_root():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()


def manifest(root, ref, path):
    result = git(root, "show", f"{ref}:{path}")
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} at {ref} is malformed: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} at {ref} is malformed: manifest must be a JSON object")
    return value


def claude_signature(value):
    return {field: value.get(field) for field in CLAUDE_CATALOG_FIELDS}


def codex_signature(value):
    interface = value.get("interface")
    if not isinstance(interface, dict):
        raise ValueError("Codex manifest interface must be a JSON object")
    return {"name": value.get("name"), "category": interface.get("category")}


def plugin_name(path):
    return Path(path).parts[1]


def merge_base(root, base):
    result = git(root, "merge-base", base, "HEAD")
    sha = result.stdout.strip()
    return sha if result.returncode == 0 and sha else base


def changed_paths(root, base):
    result = git(
        root,
        "diff",
        "--name-only",
        "--no-renames",
        "--diff-filter=AMD",
        f"{base}...HEAD",
        "--",
        CLAUDE_MANIFEST_GLOB,
        CODEX_MANIFEST_GLOB,
    )
    if result.returncode != 0:
        raise RuntimeError(f"could not diff {base}...HEAD ({result.stderr.strip()})")
    return [line for line in result.stdout.splitlines() if line.strip()]


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    root = repo_root()
    before_ref = merge_base(root, base)
    reasons_by_plugin = {}

    def flag(name, reason):
        reasons_by_plugin.setdefault(name, []).append(reason)

    try:
        paths = changed_paths(root, base)
        for path in paths:
            before_manifest = manifest(root, before_ref, path)
            after_manifest = manifest(root, "HEAD", path)
            is_codex = "/.codex-plugin/" in path
            signature = codex_signature if is_codex else claude_signature
            before = None if before_manifest is None else signature(before_manifest)
            after = None if after_manifest is None else signature(after_manifest)
            if before == after:
                continue

            if is_codex:
                if before is None:
                    reason = "added to the Codex catalog surface"
                elif after is None:
                    reason = "left the Codex catalog surface"
                else:
                    changed = sorted(
                        field for field in set(before) | set(after)
                        if before.get(field) != after.get(field)
                    )
                    reason = "changed Codex " + ", ".join(changed)
            elif before is None:
                reason = "added to the Claude catalog surface"
            elif after is None:
                reason = "left the Claude catalog surface"
            else:
                changed = [
                    field for field in CLAUDE_CATALOG_FIELDS
                    if before.get(field) != after.get(field)
                ]
                reason = "changed Claude " + ", ".join(changed)
            flag(plugin_name(path), reason)
    except (RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    affected = sorted(
        (name, "; ".join(reasons))
        for name, reasons in reasons_by_plugin.items()
    )
    if not affected:
        print(
            f"marketplace-publish-check — no catalog-surface change vs {base}. "
            "No publish needed."
        )
        return 0

    plural = "plugin" if len(affected) == 1 else "plugins"
    verb = "needs" if len(affected) == 1 else "need"
    print(
        f"marketplace-publish-check — {len(affected)} {plural} {verb} "
        f"a marketplace-publish vs {base}:\n"
    )
    width = max(len(name) for name, _ in affected)
    for name, reason in affected:
        print(f"  {name:<{width}}  ({reason})")
    print("\nApply the `marketplace-publish` label to this PR.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
