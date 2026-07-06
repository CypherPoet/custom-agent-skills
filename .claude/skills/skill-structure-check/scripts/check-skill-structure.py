#!/usr/bin/env python3
"""
check-skill-structure.py — audit skill structure across every plugin in this repo.

Bundled by the repo-local `skill-structure-check` skill. Encodes the repo's
skill-structure convention as runnable rules so SKILL.md files don't silently
balloon and large reference files stay navigable:

  ERROR     SKILL.md over 500 lines              split topical / once-needed depth into
                                                 references/ files (skill-creator: "<500 ideal")
  ERROR     a **Contents:** anchor that doesn't   stale table of contents — a heading was
            resolve to a heading in its file      renamed or removed
  ERROR     a cross-plugin relative link in a     dead path in an installed sparse-clone (only
            SKILL.md / references file            this plugin's dir is fetched) — use an
                                                  absolute GitHub URL instead
  WARNING   SKILL.md 450-500 lines               approaching the limit; plan to split
  ADVISORY  references/*.md over 300 lines        large reference files get a **Contents:** jump-line
            without a **Contents:** jump-line     so they stay navigable (summarized, non-failing)
  ADVISORY  a unit missing from the fact-check    every unit should be deliberately tiered in
            manifest's tier lists (or a listed    docs/automated-routines/skill-fact-check-manifest.json
            unit that no longer exists)           (an unlisted unit still defaults to monthly)

The skill-level "table of contents" is the routing table in SKILL.md that points
at the references/ files; that's a soft convention, not machine-checked here.
Short reference files don't need their own Contents line.

Report-only. Exits 1 if any ERROR, else 0 (warnings/advisories never fail the run).
Run from anywhere in the repo:
  python3 .claude/skills/skill-structure-check/scripts/check-skill-structure.py
"""
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
    """The set of in-file anchors, with GitHub's -1/-2 suffixing for duplicate headings."""
    seen, valid = {}, set()
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if not m:
            continue
        a = gh_anchor(m.group(1).strip())
        n = seen.get(a, 0)
        valid.add(a if n == 0 else f"{a}-{n}")
        seen[a] = n + 1
    return valid


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


def tier_findings(root, units):
    """Units missing from the fact-check manifest's tier lists, and listed units that
    don't exist on disk. Advisory only — an unlisted unit still defaults to monthly —
    and skipped entirely (empty result) when the repo has no manifest.
    """
    path = os.path.join(root, FACT_CHECK_MANIFEST)
    if not os.path.isfile(path):
        return [], [], None
    try:
        manifest = json.load(open(path, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return [], [], f"could not read {FACT_CHECK_MANIFEST}: {e}"
    tiered = {u for k in TIER_KEYS for u in manifest.get(k, [])}
    untiered = sorted(units - tiered)
    orphaned = sorted(tiered - units)
    return untiered, orphaned, None


def audit(plugins_dir):
    errors, warnings, missing_contents, units = [], [], [], set()
    for plugin in sorted(os.listdir(plugins_dir)):
        skills_dir = os.path.join(plugins_dir, plugin, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for skill in sorted(os.listdir(skills_dir)):
            base = os.path.join(skills_dir, skill)
            skill_md = os.path.join(base, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            if skill.endswith("-workspace"):
                continue
            label = f"{plugin}/{skill}"
            units.add(label)
            plugin_root = os.path.join(plugins_dir, plugin)

            skill_text = open(skill_md, encoding="utf-8").read()
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
                text = open(ref_path, encoding="utf-8").read()
                rlines = len(text.splitlines())
                esc = escaping_links(text, ref_path, plugin_root)
                if esc:
                    errors.append((label, f"references/{f}", "cross-plugin relative link(s) — use an absolute GitHub URL: " + ", ".join(esc)))
                contents = re.search(r"^\*\*Contents:\*\*.*$", text, re.M)
                if not contents:
                    if rlines > REF_TOC_FLOOR:
                        missing_contents.append((label, f"{f} ({rlines} lines)"))
                    continue
                valid = heading_anchors(text)
                broken = [t for t in re.findall(r"\(#([^)]+)\)", contents.group(0)) if t not in valid]
                if broken:
                    errors.append((label, f"references/{f}", "stale **Contents:** anchors: " + ", ".join("#" + b for b in broken)))
    return errors, warnings, missing_contents, units


def render(rows, kind):
    cur = None
    for label, where, msg in rows:
        if label != cur:
            print(f"  {label}")
            cur = label
        print(f"    [{kind}] {where}: {msg}")


def main():
    root = find_repo_root(os.path.dirname(os.path.abspath(__file__))) or find_repo_root(os.getcwd())
    if not root:
        print("error: could not find the repo root (no plugins/ directory above this script or the cwd).", file=sys.stderr)
        return 2
    errors, warnings, missing_contents, units = audit(os.path.join(root, "plugins"))
    untiered, orphaned, manifest_note = tier_findings(root, units)

    if not errors and not warnings and not missing_contents and not untiered and not orphaned and not manifest_note:
        print("OK — every SKILL.md is lean, large reference files are indexed, all Contents anchors resolve, and every unit is tiered in the fact-check manifest.")
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
    if untiered or orphaned or manifest_note:
        if errors or warnings or missing_contents:
            print()
        print(f"ADVISORY — fact-check manifest drift in {FACT_CHECK_MANIFEST} (non-failing):")
        if manifest_note:
            print(f"  {manifest_note}")
        for u in untiered:
            print(f"  {u}: not in any tier list — add it to weekly/monthly/never (defaults to monthly meanwhile)")
        for u in orphaned:
            print(f"  {u}: listed in the manifest but no such unit exists — remove or rename the entry")

    print("\nRules: this skill's scripts/check-skill-structure.py is the source of truth; see docs/PLUGIN-CONVENTIONS.md -> Skill Conventions.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
