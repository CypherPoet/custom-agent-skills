#!/usr/bin/env python3
"""Implement the canonical rule contract in ../SKILL.md."""
import json
import os
import re
import sys

SKILL_OVER = 500      # hard limit (skill-creator's "<500 ideal")
SKILL_WARN = 450      # soft heads-up band below the limit
REF_TOC_FLOOR = 300   # only large reference files (skill-creator's >300-line threshold) need a Contents line
FACT_CHECK_MANIFEST = os.path.join("docs", "automated-routines", "skill-fact-check-manifest.json")
TIER_KEYS = ("weekly", "monthly", "never")


def find_repo_root(start):
    """Walk up from `start` until a directory containing a plugins/ subdir is found."""
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, "plugins")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def gh_anchor(heading):
    """GitHub's heading-anchor algorithm: lowercase, drop punctuation, spaces -> hyphens."""
    return re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")


def heading_anchors(text):
    """The set of in-file anchors, with GitHub's -1/-2 suffixing for duplicate
    headings. Fenced code is stripped first so a '## foo' line inside an example
    block can't satisfy a Contents link."""
    seen, valid = {}, set()
    for line in strip_code_fences(text).splitlines():
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if not m:
            continue
        a = gh_anchor(m.group(1).strip())
        n = seen.get(a, 0)
        valid.add(a if n == 0 else f"{a}-{n}")
        seen[a] = n + 1
    return valid


def contents_anchors(text):
    """Anchors from the file's `**Contents:**` jump-line — the single canonical
    index format (see ../SKILL.md) — or None when no populated jump-line exists.
    Fenced code is stripped first so a documented example is never parsed as the
    file's real index, and only markdown links `[text](#anchor)` count as
    entries, so prose parentheticals like '(#42)' are ignored."""
    jump_line = re.search(r"^\*\*Contents:\*\*.*$", strip_code_fences(text), re.M)
    if not jump_line:
        return None
    anchors = re.findall(r"\[[^\]]*\]\(#([^)]+)\)", jump_line.group(0))
    return anchors or None


LINK_RE = re.compile(r"\]\(([^)]+)\)")


def strip_code_fences(text):
    """Drop ``` fenced blocks so example code in a skill isn't scanned for links."""
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def escaping_links(text, md_path, plugin_root):
    """Relative markdown links in `md_path` that resolve OUTSIDE plugin_root.

    A plugin ships via a git-subdir sparse-clone of only its own directory, so a
    relative link climbing into a sibling plugin (../../../other-plugin/...) is a
    dead path once installed. Cross-plugin links must be absolute GitHub URLs.
    Returns the offending (deduped) targets; absolute URLs and in-file anchors pass.
    """
    bad, file_dir = [], os.path.dirname(md_path)
    root = os.path.abspath(plugin_root)
    for raw in LINK_RE.findall(strip_code_fences(text)):
        target = raw.split()[0].strip()                 # drop any optional "title"
        if target.startswith(("http://", "https://", "mailto:", "#", "<")):
            continue
        target = target.split("#", 1)[0]                # strip a #fragment
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(file_dir, target))
        if resolved != root and not resolved.startswith(root + os.sep):
            bad.append(target)
    return list(dict.fromkeys(bad))


def tier_findings(root, units, units_with_sources):
    """Advisory strings for fact-check manifest drift: units missing from every tier
    list, listed units that don't exist on disk, units in more than one list, and
    fact-checked (non-never) units missing their **Primary Sources** section.
    Advisory only — an unlisted unit still defaults to monthly. Returns
    (advisories, checked); checked is False when the repo has no manifest (the
    check is skipped, not passed). Keep the unit enumeration in sync with the
    fact-check skill's `find … -not -path '*-workspace/*'` (its Step 1 prints the
    same drift as `# DRIFT` lines, which covers repos without this script).
    """
    path = os.path.join(root, FACT_CHECK_MANIFEST)
    if not os.path.isfile(path):
        return [], False
    try:
        with open(path, encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
        if not isinstance(manifest, dict) or not all(
            isinstance(manifest.get(k, []), list) for k in TIER_KEYS
        ):
            raise ValueError("expected a JSON object whose tier keys hold arrays")
        listed = [u for k in TIER_KEYS for u in manifest.get(k, [])]
        never = set(manifest.get("never", []))
    except (json.JSONDecodeError, OSError, ValueError) as e:
        return [f"could not read {FACT_CHECK_MANIFEST}: {e}"], True
    advisories = []
    for u in sorted(units - set(listed)):
        advisories.append(f"{u}: not in any tier list — add it to weekly/monthly/never (defaults to monthly meanwhile)")
    for u in sorted(set(listed) - units):
        advisories.append(f"{u}: listed in the manifest but no such unit exists — remove or rename the entry")
    for u in sorted({u for u in listed if listed.count(u) > 1}):
        advisories.append(f"{u}: in more than one tier list — keep exactly one (the fact-check resolver silently lets the later list win)")
    for u in sorted((units - never) - units_with_sources):
        advisories.append(f"{u}: fact-checked unit without a ## Primary Sources section — add one (placeholder ok; see docs/PLUGIN-CONVENTIONS.md → Primary Sources)")
    return advisories, True


def audit(plugins_dir):
    errors, warnings, missing_contents = [], [], []
    units, units_with_sources = set(), set()
    for plugin in sorted(os.listdir(plugins_dir)):
        plugin_root = os.path.join(plugins_dir, plugin)
        # The plugin README ships in the sparse-clone install alongside the
        # skills, so it follows the same cross-plugin link rule as skill files.
        readme = os.path.join(plugin_root, "README.md")
        if os.path.isfile(readme):
            with open(readme, encoding="utf-8") as readme_file:
                esc = escaping_links(readme_file.read(), readme, plugin_root)
            if esc:
                errors.append((plugin, "README.md", "cross-plugin relative link(s) — dead in a sparse-clone install, use an absolute GitHub URL: " + ", ".join(esc)))
        skills_dir = os.path.join(plugin_root, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for skill in sorted(os.listdir(skills_dir)):
            base = os.path.join(skills_dir, skill)
            skill_md = os.path.join(base, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            label = f"{plugin}/{skill}"

            with open(skill_md, encoding="utf-8") as skill_file:
                skill_text = skill_file.read()
            # *-workspace dirs are gitignored /skill-creator scratch: still structure-checked
            # (they may be promoted), but not units the fact-check manifest should tier.
            if not skill.endswith("-workspace"):
                units.add(label)
                if re.search(r"^## Primary Sources$", skill_text, re.M):
                    units_with_sources.add(label)
            n = len(skill_text.splitlines())
            if n > SKILL_OVER:
                errors.append((label, "SKILL.md", f"{n} lines (>{SKILL_OVER}) — split depth into references/ files"))
            elif n >= SKILL_WARN:
                warnings.append((label, "SKILL.md", f"{n} lines — approaching the {SKILL_OVER}-line limit"))

            esc = escaping_links(skill_text, skill_md, plugin_root)
            if esc:
                errors.append((label, "SKILL.md", "cross-plugin relative link(s) — dead in a sparse-clone install, use an absolute GitHub URL: " + ", ".join(esc)))

            ref_dir = os.path.join(base, "references")
            if not os.path.isdir(ref_dir):
                continue
            for f in sorted(os.listdir(ref_dir)):
                if not f.endswith(".md"):
                    continue
                ref_path = os.path.join(ref_dir, f)
                with open(ref_path, encoding="utf-8") as reference_file:
                    text = reference_file.read()
                rlines = len(text.splitlines())
                esc = escaping_links(text, ref_path, plugin_root)
                if esc:
                    errors.append((label, f"references/{f}", "cross-plugin relative link(s) — use an absolute GitHub URL: " + ", ".join(esc)))
                indexed = contents_anchors(text)
                if indexed is None:
                    if rlines > REF_TOC_FLOOR:
                        missing_contents.append((label, f"{f} ({rlines} lines)"))
                    continue
                valid = heading_anchors(text)
                broken = [target for target in indexed if target not in valid]
                if broken:
                    errors.append((label, f"references/{f}", "stale Contents anchors: " + ", ".join("#" + b for b in broken)))
    return errors, warnings, missing_contents, units, units_with_sources


def dual_harness_drift(root):
    """Plugin sync drift as ERROR strings; [] when the tooling is absent (portable
    to repos without it) or everything is in sync. Delegates to scripts/sync_plugins.py
    so the vendored-copy / Codex-manifest generators have one source of truth."""
    scripts_dir = os.path.join(root, "scripts")
    if not (
        os.path.isfile(os.path.join(scripts_dir, "plugin-registry.json"))
        and os.path.isfile(os.path.join(scripts_dir, "sync_plugins.py"))
    ):
        return []
    sys.path.insert(0, scripts_dir)
    try:
        import sync_plugins
        from pathlib import Path

        return sync_plugins.sync(Path(root), write=False)
    except Exception as e:  # never let the guard's own failure mask a clean structure run
        return [f"dual-harness check could not run: {e}"]
    finally:
        if scripts_dir in sys.path:
            sys.path.remove(scripts_dir)


def render(rows, kind):
    cur = None
    for label, where, msg in rows:
        if label != cur:
            print(f"  {label}")
            cur = label
        print(f"    [{kind}] {where}: {msg}")


def main():
    strict = "--strict" in sys.argv[1:]
    root = find_repo_root(os.path.dirname(os.path.abspath(__file__))) or find_repo_root(os.getcwd())
    if not root:
        print("error: could not find the repo root (no plugins/ directory above this script or the cwd).", file=sys.stderr)
        return 2
    errors, warnings, missing_contents, units, units_with_sources = audit(os.path.join(root, "plugins"))
    tier_advisories, tier_checked = tier_findings(root, units, units_with_sources)
    for msg in dual_harness_drift(root):
        errors.append(("dual-harness", "sync", msg))

    if not (errors or warnings or missing_contents or tier_advisories):
        tier_note = ", and the fact-check manifest is drift-free" if tier_checked else ""
        print(f"OK — every SKILL.md is lean, large reference files are indexed, all Contents anchors resolve{tier_note}.")
        return 0

    if errors:
        print(f"{len(errors)} ERROR(s):")
        render(errors, "ERROR")
    if warnings:
        if errors:
            print()
        print(f"{len(warnings)} WARNING(s):")
        render(warnings, "WARN")
    if missing_contents:
        if errors or warnings:
            print()
        by_skill = {}
        for label, f in missing_contents:
            by_skill.setdefault(label, []).append(f)
        print(f"ADVISORY — {len(missing_contents)} large reference file(s) across {len(by_skill)} skill(s) lack a **Contents:** jump-line (non-failing):")
        for label in sorted(by_skill):
            print(f"  {label}: {', '.join(by_skill[label])}")
    if tier_advisories:
        if errors or warnings or missing_contents:
            print()
        print(f"ADVISORY — fact-check manifest drift in {FACT_CHECK_MANIFEST} (non-failing):")
        for a in tier_advisories:
            print(f"  {a}")

    print("\nRules and remediation: .claude/skills/skill-structure-check/SKILL.md")
    if errors:
        return 1
    # Bare runs are report-only for WARN/ADVISORY; --strict (used by the CI
    # health suite) fails on them too.
    return 1 if strict and (warnings or missing_contents or tier_advisories) else 0


if __name__ == "__main__":
    sys.exit(main())
