#!/usr/bin/env python3
"""Read-only audit of git-tag coverage for version-constrained plugin dependencies.

Walks every plugins/*/.claude-plugin/plugin.json, keeps dependency entries that
carry a version constraint (bare-string deps need no tags and are skipped), and
checks whether a satisfying `<plugin>--v<version>` tag exists on origin.

Stdlib only — no node/npx, no network beyond `git ls-remote` to the repo's own
origin. Never writes anything. Exit status is 1 when there are actionable
findings (MISSING / UNSATISFIABLE / UNKNOWN / DRIFT), else 0.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$")
COMPARATOR_RE = re.compile(r"^(\^|~|>=|<=|>|<|=)?\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$")


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True,
    )


def repo_root():
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(res.stdout.strip()) if res.returncode == 0 else Path.cwd()


def parse_version(s):
    m = VERSION_RE.match(s.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))


def parse_comparator(token):
    """One range token -> list of (op, (M,m,p)) constraints, or None if unrecognized."""
    m = COMPARATOR_RE.match(token)
    if not m:
        return None
    op = m.group(1) or "="
    major = int(m.group(2))
    minor_given, patch_given = m.group(3), m.group(4)
    minor, patch = int(minor_given or 0), int(patch_given or 0)
    lower = (major, minor, patch)
    if op == "~":  # ~1.2.3 -> >=1.2.3 <1.3.0 ; ~1 -> >=1.0.0 <2.0.0
        upper = (major, minor + 1, 0) if minor_given is not None else (major + 1, 0, 0)
        return [(">=", lower), ("<", upper)]
    if op == "^":  # allow changes that don't touch the left-most non-zero element
        if major > 0:
            upper = (major + 1, 0, 0)
        elif minor > 0:
            upper = (0, minor + 1, 0)
        elif patch_given is not None:
            upper = (0, 0, patch + 1)
        elif minor_given is not None:
            upper = (0, minor + 1, 0)  # ^0.0 -> <0.1.0
        else:
            upper = (1, 0, 0)  # ^0 -> <1.0.0
        return [(">=", lower), ("<", upper)]
    return [(op, lower)]


def parse_range(r):
    """Range string -> list of (op, version) constraints, or None if unrecognized."""
    r = r.strip()
    if r in ("*", "x", "X", ""):
        return [(">=", (0, 0, 0))]
    if "||" in r or " - " in r:  # OR / hyphen ranges: don't guess
        return None
    constraints = []
    for token in r.split():
        parsed = parse_comparator(token)
        if parsed is None:
            return None
        constraints.extend(parsed)
    return constraints


def satisfies(version_tuple, constraints):
    ops = {
        ">=": lambda c, v: c >= v, "<=": lambda c, v: c <= v,
        ">": lambda c, v: c > v, "<": lambda c, v: c < v, "=": lambda c, v: c == v,
    }
    return all(ops[op](version_tuple, v) for op, v in constraints)


def highest_satisfying(version_strings, constraints):
    candidates = [(parse_version(s), s) for s in version_strings]
    matches = [(t, s) for t, s in candidates if t and satisfies(t, constraints)]
    return max(matches)[1] if matches else None


def main():
    root = repo_root()
    manifests = sorted(root.glob("plugins/*/.claude-plugin/plugin.json"))

    # Map plugin name -> current version, for resolving each dependency's version.
    current = {}
    for path in manifests:
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        name = data.get("name") or path.parent.parent.name
        current[name] = data.get("version")

    # Collect constrained dependencies: (declarer, dep_name, range, has_marketplace).
    constrained = []
    for path in manifests:
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        declarer = data.get("name") or path.parent.parent.name
        for entry in data.get("dependencies") or []:
            if isinstance(entry, dict) and entry.get("version"):
                constrained.append((declarer, entry["name"], entry["version"], "marketplace" in entry))

    if not constrained:
        print("No version-constrained dependencies found.")
        print("Nothing to audit — all dependencies are bare-string (no tags needed).")
        return 0

    # Tags: one ls-remote (authoritative, what consumers resolve against) + local-only detection.
    remote = git(root, "ls-remote", "--tags", "origin")
    remote_ok = remote.returncode == 0
    remote_tags, local_tags = set(), set()
    if remote_ok:
        for line in remote.stdout.splitlines():
            ref = line.split("\t")[-1]
            if ref.startswith("refs/tags/"):
                remote_tags.add(ref[len("refs/tags/"):].removesuffix("^{}"))
    for line in git(root, "tag", "--list").stdout.splitlines():
        local_tags.add(line.strip())

    def versions_for(dep, tagset):
        prefix = dep + "--v"
        return [t[len(prefix):] for t in tagset if t.startswith(prefix)]

    findings = []
    for declarer, dep, rng, has_marketplace in constrained:
        label = f"{declarer} -> {dep} {rng}"
        if has_marketplace or dep not in current:
            findings.append(("EXTERNAL", label, "not a local plugin — audit in its own source repo"))
            continue
        constraints = parse_range(rng)
        if constraints is None:
            findings.append(("UNKNOWN", label, "unrecognized range expression — verify manually"))
            continue
        cur = current.get(dep)
        cur_tuple = parse_version(cur) if cur else None
        sat_remote = highest_satisfying(versions_for(dep, remote_tags), constraints)
        sat_local = highest_satisfying(versions_for(dep, local_tags), constraints)
        cur_satisfies = cur_tuple is not None and satisfies(cur_tuple, constraints)

        if sat_remote:
            tag = f"{dep}--v{sat_remote}"
            committed = git(root, "show", f"{tag}:plugins/{dep}/.claude-plugin/plugin.json")
            drift = None
            if committed.returncode == 0:
                try:
                    committed_version = json.loads(committed.stdout).get("version")
                    if committed_version != sat_remote:
                        drift = committed_version
                except json.JSONDecodeError:
                    pass
            if drift is not None:
                findings.append(("DRIFT", label, f"{tag} points at a commit whose manifest says {drift} — stale/force-moved tag"))
            else:
                findings.append(("OK", label, f"resolves to {tag}"))
        elif sat_local:
            findings.append(("MISSING", label, f"tag {dep}--v{sat_local} exists locally but is unpushed — push it"))
        elif cur_satisfies:
            findings.append(("MISSING", label, f"no tag; current {cur} satisfies — tag it"))
        else:
            findings.append(("UNSATISFIABLE", label, f"current {cur} is outside {rng} — widen the constraint or maintain an older tagged line"))

    order = ["UNSATISFIABLE", "DRIFT", "MISSING", "UNKNOWN", "OK", "EXTERNAL"]
    findings.sort(key=lambda f: order.index(f[0]))

    print(f"dependency-tag-check — {len(constrained)} version-constrained dependenc{'y' if len(constrained) == 1 else 'ies'}\n")
    if not remote_ok:
        print("WARNING: `git ls-remote origin` failed (offline?). Remote tag coverage is unknown;")
        print("         findings below fall back to local tags only.\n")
    width = max(len(b) for b, _, _ in findings)
    for bucket, label, detail in findings:
        print(f"  [{bucket:<{width}}]  {label}")
        print(f"  {'':<{width}}     {detail}")

    counts = {}
    for bucket, _, _ in findings:
        counts[bucket] = counts.get(bucket, 0) + 1
    print("\nSummary: " + ", ".join(f"{counts[b]} {b}" for b in order if b in counts))

    actionable = {"MISSING", "UNSATISFIABLE", "UNKNOWN", "DRIFT"}
    return 1 if any(b in actionable for b, _, _ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
