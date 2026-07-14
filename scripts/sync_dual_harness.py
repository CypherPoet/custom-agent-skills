#!/usr/bin/env python3
"""Generate and guard every dual-harness (Claude Code + Codex) derived artifact.

Single source of truth: scripts/dual-harness.json. From it this tool produces
three kinds of generated artifact and, in --check mode, fails if any has drifted:

  1. Vendored skill copies  — a skill authored once (its owner plugin) copied
     byte-for-byte into every plugin that ships it. Required because neither
     harness can reference a skill outside a plugin's own directory (Claude
     sparse-clones one plugin dir; Codex has no plugin-to-plugin dependencies).
  2. Codex plugin manifests — plugins/<name>/.codex-plugin/plugin.json, mirrored
     from the plugin's .claude-plugin/plugin.json plus "skills": "./skills/".
  3. Vendoring ownership markers — adjacent hidden JSON files that record which
     source owns each generated copy and its last generated content digest. They
     let write mode safely remove a copy after its config edge is deleted.

It also validates that every plugin under plugins/ is classified as either
dual-harness or Claude-only, so adding a plugin forces an explicit decision.

The marketplace catalogs (Claude and Codex) live in the marketplace repo, not
here — they're maintained by the cypherpoet-marketplace-kit publish flow.

Usage:
    python3 scripts/sync_dual_harness.py           # write mode (default): (re)generate
    python3 scripts/sync_dual_harness.py --check   # exit 1 on any drift or misclassification

Never hand-edit a generated artifact; edit the source (skill or Claude manifest)
and re-run the bare command to regenerate.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import sys
from pathlib import Path

# Dev/eval material that lives only with a source skill and is never vendored.
IGNORE_DIR_NAMES = {"__pycache__", "evals", ".git"}
IGNORE_DIR_GLOBS = ("*-workspace",)
IGNORE_FILE_NAMES = {".DS_Store"}
IGNORE_FILE_GLOBS = ("*.pyc",)
VENDOR_MARKER_SUFFIX = ".dual-harness-vendor.json"

# Manifest fields copied verbatim from .claude-plugin into .codex-plugin, in order.
CODEX_MANIFEST_CARRY = ("author", "homepage", "repository", "license", "keywords")


def _dir_ignored(name: str) -> bool:
    return name in IGNORE_DIR_NAMES or any(fnmatch.fnmatch(name, g) for g in IGNORE_DIR_GLOBS)


def _file_ignored(name: str) -> bool:
    return name in IGNORE_FILE_NAMES or any(fnmatch.fnmatch(name, g) for g in IGNORE_FILE_GLOBS)


def read_tree(base: Path) -> dict[str, bytes]:
    """Return {relative_posix_path: file_bytes} for base, applying the ignore sets."""
    out: dict[str, bytes] = {}
    if not base.exists():
        return out
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base)
        if any(_dir_ignored(part) for part in rel.parts[:-1]):
            continue
        if path.is_dir():
            continue
        if _file_ignored(path.name):
            continue
        out[rel.as_posix()] = path.read_bytes()
    return out


def write_tree(src: Path, dst: Path) -> None:
    """Replace dst with the (ignore-filtered) contents of src."""
    files = read_tree(src)
    if dst.exists():
        shutil.rmtree(dst)
    for rel, data in files.items():
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def tree_digest(files: dict[str, bytes]) -> str:
    """Stable digest of an ignore-filtered tree, including paths and boundaries."""
    digest = hashlib.sha256()
    for relative_path, data in sorted(files.items()):
        path_bytes = relative_path.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def valid_skill_path(value: str) -> bool:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        return False
    parts = path.parts
    return (
        len(parts) == 4 and parts[0] == "plugins" and parts[2] == "skills"
    ) or (
        len(parts) == 3 and parts[0] in {".agents", ".claude"} and parts[1] == "skills"
    )


def vendor_marker_path(root: Path, target: str) -> Path:
    target_path = root / target
    return target_path.parent / f".{target_path.name}{VENDOR_MARKER_SUFFIX}"


def vendor_marker(source: str, target: str, files: dict[str, bytes]) -> dict:
    return {
        "source": source,
        "target": target,
        "tree_sha256": tree_digest(files),
    }


def discover_vendor_markers(root: Path) -> tuple[dict[str, tuple[Path, dict]], list[str]]:
    """Return valid target-keyed ownership markers and non-destructive errors."""
    discovered: dict[str, tuple[Path, dict]] = {}
    problems: list[str] = []
    for marker_path in sorted(root.rglob(f"*{VENDOR_MARKER_SUFFIX}")):
        relative = marker_path.relative_to(root)
        if ".git" in relative.parts or "worktrees" in relative.parts:
            continue
        try:
            data = json.loads(marker_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            problems.append(f"[vendor] malformed ownership marker {relative}: {error}")
            continue
        if not isinstance(data, dict) or not all(
            isinstance(data.get(key), str) and data.get(key)
            for key in ("source", "target", "tree_sha256")
        ):
            problems.append(f"[vendor] malformed ownership marker {relative}: expected source, target, and tree_sha256 strings")
            continue
        target = data["target"]
        if not valid_skill_path(target) or marker_path != vendor_marker_path(root, target):
            problems.append(f"[vendor] ownership marker at unexpected path: {relative}")
            continue
        if target in discovered:
            problems.append(f"[vendor] duplicate ownership markers for {target}")
            continue
        discovered[target] = (marker_path, data)
    return discovered, problems


def desired_vendor_targets(cfg: dict) -> tuple[dict[str, str], list[str]]:
    desired: dict[str, str] = {}
    problems: list[str] = []
    for edge in cfg["vendored_skills"]:
        source = edge.get("source")
        targets = edge.get("targets")
        if not isinstance(source, str) or not valid_skill_path(source):
            problems.append(f"[vendor] invalid source path: {source!r}")
            continue
        if not isinstance(targets, list) or not targets:
            problems.append(f"[vendor] {source}: targets must be a non-empty array")
            continue
        for target in targets:
            if not isinstance(target, str) or not valid_skill_path(target):
                problems.append(f"[vendor] invalid target path: {target!r}")
                continue
            if target == source:
                problems.append(f"[vendor] source and target are identical: {target}")
                continue
            previous = desired.get(target)
            if previous is not None:
                problems.append(f"[vendor] duplicate target {target}: declared by {previous} and {source}")
                continue
            desired[target] = source
    for source in sorted(set(desired.values()) & set(desired)):
        problems.append(f"[vendor] vendoring chains are not allowed: source is also a target: {source}")
    return desired, problems


def build_codex_manifest(claude: dict) -> dict:
    manifest = {
        "name": claude["name"],
        "version": claude["version"],
        "description": claude["description"],
    }
    for key in CODEX_MANIFEST_CARRY:
        if key in claude:
            manifest[key] = claude[key]
    manifest["skills"] = "./skills/"
    return manifest


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def load_config(root: Path) -> dict:
    return json.loads((root / "scripts" / "dual-harness.json").read_text(encoding="utf-8"))


def sync(root: Path, write: bool) -> list[str]:
    """Perform (write) or verify (check) every derived artifact. Returns drift/error messages."""
    cfg = load_config(root)
    problems: list[str] = []

    # 0. Classification: every plugin must be dual-harness xor Claude-only.
    existing = {p.name for p in (root / "plugins").iterdir() if p.is_dir()}
    dual = set(cfg["dual_harness_plugins"])
    claude_only = set(cfg["claude_only_plugins"])
    for name in sorted(dual & claude_only):
        problems.append(f"[config] {name} is listed as both dual-harness and Claude-only")
    for name in sorted((dual | claude_only) - existing):
        problems.append(f"[config] {name} is classified but no plugins/{name}/ exists")
    for name in sorted(existing - dual - claude_only):
        problems.append(f"[config] plugins/{name}/ is unclassified — add it to dual_harness_plugins or claude_only_plugins")

    # 1. Vendored skills and their adjacent ownership markers.
    desired_targets, vendor_config_problems = desired_vendor_targets(cfg)
    problems.extend(vendor_config_problems)
    markers, marker_problems = discover_vendor_markers(root)
    problems.extend(marker_problems)

    if not vendor_config_problems and not marker_problems:
        for target in sorted(set(markers) - set(desired_targets)):
            marker_path, marker = markers[target]
            dst = root / target
            if not write:
                state = "copy and marker remain" if dst.exists() or dst.is_symlink() else "marker remains"
                problems.append(f"[vendor] stale generated copy: {target} ({state}; was vendored from {marker['source']})")
                continue
            if dst.exists() or dst.is_symlink():
                if dst.is_symlink() or not dst.is_dir() or tree_digest(read_tree(dst)) != marker["tree_sha256"]:
                    problems.append(f"[vendor] stale target has local changes; refusing to remove: {target} (delete {marker_path.relative_to(root)} to adopt it as authored)")
                    continue
                shutil.rmtree(dst)
            marker_path.unlink()

        for target, source in sorted(desired_targets.items()):
            src = root / source
            if not src.exists():
                problems.append(f"[vendor] source missing: {source}")
                continue
            src_tree = read_tree(src)
            if not src_tree:
                problems.append(f"[vendor] source has no vendorable files: {source}")
                continue
            dst = root / target
            expected_marker = dumps(vendor_marker(source, target, src_tree)).encode("utf-8")
            marker_path = vendor_marker_path(root, target)
            if write:
                write_tree(src, dst)
                marker_path.write_bytes(expected_marker)
            else:
                if read_tree(dst) != src_tree:
                    problems.append(f"[vendor] out of sync: {target} != {source} (run: python3 scripts/sync_dual_harness.py)")
                if not marker_path.exists() or marker_path.read_bytes() != expected_marker:
                    problems.append(f"[vendor] ownership marker out of sync: {marker_path.relative_to(root)} (run: python3 scripts/sync_dual_harness.py)")

    # 2. Codex manifests.
    for name in sorted(dual):
        if "category" not in cfg["dual_harness_plugins"][name]:
            problems.append(f"[config] {name}: dual_harness_plugins entry needs a 'category'")
        claude_path = root / "plugins" / name / ".claude-plugin" / "plugin.json"
        if not claude_path.exists():
            problems.append(f"[codex-manifest] missing Claude manifest for {name}")
            continue
        claude = json.loads(claude_path.read_text(encoding="utf-8"))
        missing = [k for k in ("name", "version", "description") if k not in claude]
        if missing:
            problems.append(f"[codex-manifest] {name}: Claude manifest missing {', '.join(missing)}")
            continue
        plugin_dir = root / "plugins" / name
        unported = [k for k in ("mcpServers", "hooks", "agents", "commands") if k in claude]
        skills_val = claude.get("skills", "./skills/")
        if not (isinstance(skills_val, str) and skills_val.lstrip("./").rstrip("/") == "skills"):
            unported.append("skills (custom path)")
        for comp in ("commands", "agents", "hooks"):
            if (plugin_dir / comp).is_dir() and comp not in unported:
                unported.append(f"{comp}/ (auto-discovered)")
        if (plugin_dir / ".mcp.json").is_file() and "mcpServers" not in unported:
            unported.append(".mcp.json")
        if unported:
            problems.append(f"[codex-manifest] {name}: Claude-only components ({', '.join(unported)}) — the generator does not carry these into .codex-plugin; port them or make the plugin Claude-only")
            continue
        want = dumps(build_codex_manifest(claude)).encode("utf-8")
        codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
        if write:
            codex_path.parent.mkdir(parents=True, exist_ok=True)
            codex_path.write_bytes(want)
        elif not codex_path.exists() or codex_path.read_bytes() != want:
            problems.append(f"[codex-manifest] out of sync: {codex_path.relative_to(root)} (run: python3 scripts/sync_dual_harness.py)")

    # 3. A Claude-only plugin must not present itself as a Codex plugin.
    for name in sorted(claude_only & existing):
        stale = root / "plugins" / name / ".codex-plugin"
        if stale.exists():
            if write:
                shutil.rmtree(stale)
            else:
                problems.append(f"[codex-manifest] stale .codex-plugin/ for Claude-only plugin {name} (run: python3 scripts/sync_dual_harness.py)")

    return problems


def find_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "plugins").is_dir() and (candidate / "scripts" / "dual-harness.json").is_file():
            return candidate
    raise SystemExit("could not locate repo root (needs plugins/ and scripts/dual-harness.json)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only; exit 1 on drift")
    args = parser.parse_args()

    root = find_root(Path(__file__).resolve().parent)
    problems = sync(root, write=not args.check)

    if problems:
        for msg in problems:
            print(msg, file=sys.stderr)
        if args.check:
            print(f"\n{len(problems)} dual-harness issue(s). Run: python3 scripts/sync_dual_harness.py", file=sys.stderr)
            return 1
        # In write mode, anything that blocked or skipped generation is still fatal.
        fatal = [p for p in problems if p.startswith(("[config]", "[vendor]")) or "missing Claude manifest" in p or "Claude manifest missing" in p or "Claude-only components" in p]
        if fatal:
            return 1
    print("dual-harness: checked" if args.check else "dual-harness: written", "(no issues)" if not problems else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
