#!/usr/bin/env python3
"""
check-skill-structure.py — audit skill structure across every plugin in this repo.

Bundled by the repo-local `skill-structure-check` skill. Encodes the repo's
skill-structure convention as runnable rules so SKILL.md files don't silently
balloon and reference indexes don't drift:

  ERROR  SKILL.md over 500 lines               split topical / once-needed depth into
                                               reference/ files (skill-creator: "<500 ideal")
  ERROR  reference/*.md over 50 lines without   it must open with a **Contents:** jump-line
         a **Contents:** jump-line
  ERROR  a **Contents:** anchor that doesn't    stale table of contents — a heading was
         resolve to a heading in its file       renamed or removed
  WARN   SKILL.md 450-500 lines                approaching the limit; plan to split

Report-only. Exits 1 if any ERROR, else 0 (warnings never fail the run).
Run from anywhere in the repo:
  python3 .claude/skills/skill-structure-check/scripts/check-skill-structure.py
"""
import os
import re
import sys

SKILL_OVER = 500      # hard limit (skill-creator's "<500 ideal")
SKILL_WARN = 450      # soft heads-up band below the limit
REF_TOC_FLOOR = 50    # reference files longer than this must carry a Contents line


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


def audit(plugins_dir):
    errors, warnings = [], []
    for plugin in sorted(os.listdir(plugins_dir)):
        skills_dir = os.path.join(plugins_dir, plugin, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for skill in sorted(os.listdir(skills_dir)):
            base = os.path.join(skills_dir, skill)
            skill_md = os.path.join(base, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            label = f"{plugin}/{skill}"

            n = len(open(skill_md, encoding="utf-8").read().splitlines())
            if n > SKILL_OVER:
                errors.append((label, "SKILL.md", f"{n} lines (>{SKILL_OVER}) — split depth into reference/ files"))
            elif n >= SKILL_WARN:
                warnings.append((label, "SKILL.md", f"{n} lines — approaching the {SKILL_OVER}-line limit"))

            ref_dir = os.path.join(base, "reference")
            if not os.path.isdir(ref_dir):
                continue
            for f in sorted(os.listdir(ref_dir)):
                if not f.endswith(".md"):
                    continue
                text = open(os.path.join(ref_dir, f), encoding="utf-8").read()
                rlines = len(text.splitlines())
                contents = re.search(r"^\*\*Contents:\*\*.*$", text, re.M)
                if not contents:
                    if rlines > REF_TOC_FLOOR:
                        errors.append((label, f"reference/{f}", f"{rlines} lines — missing a **Contents:** jump-line"))
                    continue
                valid = heading_anchors(text)
                broken = [t for t in re.findall(r"\(#([^)]+)\)", contents.group(0)) if t not in valid]
                if broken:
                    errors.append((label, f"reference/{f}", "stale **Contents:** anchors: " + ", ".join("#" + b for b in broken)))
    return errors, warnings


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
    errors, warnings = audit(os.path.join(root, "plugins"))
    if not errors and not warnings:
        print("OK — every SKILL.md is lean, reference files are indexed, and all Contents anchors resolve.")
        return 0
    if errors:
        print(f"{len(errors)} ERROR(s):")
        render(errors, "ERROR")
    if warnings:
        if errors:
            print()
        print(f"{len(warnings)} WARNING(s):")
        render(warnings, "WARN")
    print("\nRules: this skill's scripts/check-skill-structure.py is the source of truth; see docs/PLUGIN-CONVENTIONS.md -> Skill Conventions.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
