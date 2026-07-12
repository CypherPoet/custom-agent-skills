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
  3. Codex marketplace       — .agents/plugins/marketplace.json listing every
     dual-harness plugin.

It also validates that every plugin under plugins/ is classified as either
dual-harness or Claude-only, so adding a plugin forces an explicit decision.

Usage:
    python scripts/sync_dual_harness.py            # --write (default): (re)generate
    python scripts/sync_dual_harness.py --check    # exit 1 on any drift or misclassification

Never hand-edit a generated artifact; edit the source (skill or Claude manifest)
and re-run --write.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path

# Dev/eval material that lives only with a source skill and is never vendored.
IGNORE_DIR_NAMES = {"__pycache__", "evals", ".git"}
IGNORE_DIR_GLOBS = ("*-workspace",)
IGNORE_FILE_NAMES = {".DS_Store"}
IGNORE_FILE_GLOBS = ("*.pyc",)

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
        if _dir_ignored(path.parent.name) and path.parent != base:
            continue
        if _file_ignored(path.name):
            continue
        out[rel.as_posix()] = path.read_bytes()
    return out


def write_tree(src: Path, dst: Path) -> None:
    """Replace dst with the (ignore-filtered) contents of src."""
    import shutil

    if dst.exists():
        shutil.rmtree(dst)
    files = read_tree(src)
    for rel, data in files.items():
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


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


def build_marketplace(cfg: dict) -> dict:
    dual = cfg["dual_harness_plugins"]
    return {
        "name": cfg["codex_marketplace"]["name"],
        "plugins": [
            {
                "name": name,
                "source": {"source": "local", "path": f"./plugins/{name}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": dual[name].get("category", "Uncategorized"),
            }
            for name in sorted(dual)
        ],
    }


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

    # 1. Vendored skills.
    for edge in cfg["vendored_skills"]:
        src = root / edge["source"]
        if not src.exists():
            problems.append(f"[vendor] source missing: {edge['source']}")
            continue
        src_tree = read_tree(src)
        if not src_tree:
            problems.append(f"[vendor] source has no vendorable files: {edge['source']}")
            continue
        for target in edge["targets"]:
            dst = root / target
            if write:
                write_tree(src, dst)
            elif read_tree(dst) != src_tree:
                problems.append(f"[vendor] out of sync: {target} != {edge['source']} (run: python scripts/sync_dual_harness.py)")

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
        unported = [k for k in ("mcpServers", "hooks", "apps", "commands") if k in claude]
        if unported:
            problems.append(f"[codex-manifest] {name}: Claude manifest declares {', '.join(unported)} — the generator does not carry these into .codex-plugin; port it or make the plugin Claude-only")
        want = dumps(build_codex_manifest(claude))
        codex_path = root / "plugins" / name / ".codex-plugin" / "plugin.json"
        if write:
            codex_path.parent.mkdir(parents=True, exist_ok=True)
            codex_path.write_text(want, encoding="utf-8", newline="\n")
        elif not codex_path.exists() or codex_path.read_text(encoding="utf-8") != want:
            problems.append(f"[codex-manifest] out of sync: {codex_path.relative_to(root)} (run: python scripts/sync_dual_harness.py)")

    # 3. Codex marketplace.
    want_mkt = dumps(build_marketplace(cfg))
    mkt_path = root / cfg["codex_marketplace"]["output"]
    if write:
        mkt_path.parent.mkdir(parents=True, exist_ok=True)
        mkt_path.write_text(want_mkt, encoding="utf-8", newline="\n")
    elif not mkt_path.exists() or mkt_path.read_text(encoding="utf-8") != want_mkt:
        problems.append(f"[marketplace] out of sync: {cfg['codex_marketplace']['output']} (run: python scripts/sync_dual_harness.py)")

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
            print(f"\n{len(problems)} dual-harness issue(s). Run: python scripts/sync_dual_harness.py", file=sys.stderr)
            return 1
        # In write mode, classification/source problems are still fatal.
        fatal = [p for p in problems if p.startswith("[config]") or "source missing" in p or "missing Claude manifest" in p]
        if fatal:
            return 1
    print("dual-harness: checked" if args.check else "dual-harness: written", "(no issues)" if not problems else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
