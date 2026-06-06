#!/usr/bin/env python3
"""Regenerate the plugin table in docs/CATALOG.md from the plugin manifests.

Python 3 standard library only. Locates the repo root via git, derives each
plugin's name, description, and component counts straight from plugins/, and
rewrites ONLY the markdown table in docs/CATALOG.md — the surrounding prose
(intro line, Installing section) is preserved untouched.

The catalog is deterministically derivable from the manifests, so this is the
safe "actuator" half of the audit/actuator split: marketplace-sync-check
reports local-catalog drift, this regenerates the rows.

Usage:
    python3 .claude/skills/catalog-refresh/scripts/refresh_catalog.py          # rewrite the table
    python3 .claude/skills/catalog-refresh/scripts/refresh_catalog.py --check  # dry-run; exit 1 if stale

Exit status: 0 when in sync (or successfully rewritten with no warnings),
1 when --check finds drift or when a manifest problem needs attention.
"""
import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path


def repo_root():
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip())


def pluralize(count, singular, plural):
    return f"{count} {singular if count == 1 else plural}"


def count_skills(pdir):
    sdir = pdir / "skills"
    if not sdir.is_dir():
        return 0
    return sum(1 for d in sdir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())


def count_md(pdir, sub):
    d = pdir / sub
    return sum(1 for _ in d.rglob("*.md")) if d.is_dir() else 0


def count_hooks(pdir):
    path = pdir / "hooks" / "hooks.json"
    if not path.is_file():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return 0
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return 0
    total = 0
    for groups in hooks.values():
        if isinstance(groups, list):
            for group in groups:
                inner = group.get("hooks") if isinstance(group, dict) else None
                total += len(inner) if isinstance(inner, list) else 1
    return total


def count_mcp(pdir):
    path = pdir / ".mcp.json"
    if not path.is_file():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return 0
    servers = data.get("mcpServers", {})
    return len(servers) if isinstance(servers, dict) else 0


def components(pdir):
    # Order and pluralization per docs/PLUGIN-CONVENTIONS.md -> Top-Level Catalog.
    spec = [
        (count_skills(pdir), "skill", "skills"),
        (count_md(pdir, "commands"), "command", "commands"),
        (count_md(pdir, "agents"), "agent", "agents"),
        (count_hooks(pdir), "hook", "hooks"),
        (count_mcp(pdir), "MCP server", "MCP servers"),
    ]
    parts = [pluralize(n, s, p) for n, s, p in spec if n]
    return ", ".join(parts) if parts else "—"


def cell(text):
    return text.replace("|", "\\|").strip()


def build_rows(root):
    entries, problems = [], []
    for manifest in (root / "plugins").glob("*/.claude-plugin/plugin.json"):
        pdir = manifest.parent.parent
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"{pdir.name}: invalid plugin.json ({exc})")
            continue
        name = data.get("name") or pdir.name
        desc = (data.get("description") or "").strip()
        if not desc:
            problems.append(f"{name}: manifest has no description")
        entries.append((name, pdir.name, desc, components(pdir)))
    entries.sort(key=lambda e: e[0])
    rows = [
        f"| [{name}](../plugins/{slug}/README.md) | {cell(desc)} | {comp} |"
        for name, slug, desc, comp in entries
    ]
    return rows, problems


def render_table(rows):
    return "\n".join(["| Plugin | Description | Components |", "|---|---|---|", *rows])


def replace_table(text, table):
    lines = text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines)
         if ln.lstrip().startswith("|") and "Plugin" in ln and "Description" in ln),
        None,
    )
    if start is None:
        raise SystemExit("error: no plugin table header found in docs/CATALOG.md")
    end = start
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    rebuilt = lines[:start] + table.splitlines() + lines[end:]
    return "\n".join(rebuilt) + ("\n" if text.endswith("\n") else "")


def main():
    ap = argparse.ArgumentParser(
        description="Regenerate docs/CATALOG.md's plugin table from the plugin manifests."
    )
    ap.add_argument(
        "--check", action="store_true",
        help="report drift without writing; exit 1 if the catalog table is stale",
    )
    args = ap.parse_args()

    root = repo_root()
    catalog = root / "docs" / "CATALOG.md"
    if not catalog.is_file():
        raise SystemExit(f"error: {catalog} not found")

    rows, problems = build_rows(root)
    for problem in problems:
        print(f"warning: {problem}", file=sys.stderr)
    if not rows:
        raise SystemExit("error: no plugins found under plugins/")

    current = catalog.read_text(encoding="utf-8")
    updated = replace_table(current, render_table(rows))

    if updated == current:
        print(f"docs/CATALOG.md already in sync ({len(rows)} plugins).")
        return 1 if problems else 0

    if args.check:
        print(f"docs/CATALOG.md is STALE ({len(rows)} plugins) — run without --check to regenerate:")
        print("\n".join(difflib.unified_diff(
            current.splitlines(), updated.splitlines(),
            fromfile="docs/CATALOG.md (current)", tofile="docs/CATALOG.md (regenerated)",
            lineterm="",
        )))
        return 1

    catalog.write_text(updated, encoding="utf-8")
    print(f"docs/CATALOG.md regenerated ({len(rows)} plugins). Review the diff and commit.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
