#!/usr/bin/env python3
"""Generate and guard every derived plugin artifact from scripts/plugin-registry.json.

The registry is the single source of truth. From it this tool produces two
kinds of generated artifact and, in --check mode, fails if any has drifted:

  1. Vendored skill copies  — a skill authored once (its owner plugin) copied
     byte-for-byte into every plugin that ships it. Required because neither
     harness can reference a skill outside a plugin's own directory (Claude
     sparse-clones one plugin dir; Codex has no plugin-to-plugin dependencies).
  2. Codex plugin manifests — plugins/<name>/.codex-plugin/plugin.json, composed
     from package identity in .claude-plugin/plugin.json, presentation metadata
     in the registry, and "skills": "./skills/".

It also validates that every plugin under plugins/ is classified as either
dual-harness or Claude-only, so adding a plugin forces an explicit decision.

There is no generated state. Removing a copy edge from the registry retires the
copy on the next write run, guarded by git: a directory is deleted only when
`git status` under it is clean (committed content is always recoverable), and
any skill directory that is byte-identical to a declared source but not a
declared target is flagged as an undeclared copy.

The marketplace catalogs (Claude and Codex) live in the marketplace repo, not
here — they're maintained by the cypherpoet-marketplace-kit publish flow.

Usage:
    python3 scripts/sync_plugins.py           # write mode (default): (re)generate
    python3 scripts/sync_plugins.py --check   # exit 1 on any drift or misclassification

Never hand-edit a generated artifact; edit the source (skill or Claude manifest)
and re-run the bare command to regenerate.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REGISTRY = Path("scripts") / "plugin-registry.json"
# The registry was named dual-harness.json before 2026-07; retirement reads the
# previous commit's registry, which may predate the rename.
LEGACY_REGISTRY = Path("scripts") / "dual-harness.json"

# Dev/eval material that lives only with a source skill and is never vendored.
IGNORE_DIR_NAMES = {"__pycache__", "evals", ".git"}
IGNORE_DIR_GLOBS = ("*-workspace",)
IGNORE_FILE_NAMES = {".DS_Store"}
IGNORE_FILE_GLOBS = ("*.pyc",)

# Manifest fields copied verbatim from .claude-plugin into .codex-plugin, in order.
CODEX_MANIFEST_CARRY = ("author", "homepage", "repository", "license", "keywords")
CODEX_CAPABILITIES = {"Interactive", "Read", "Write"}


def _dir_ignored(name: str) -> bool:
    return name in IGNORE_DIR_NAMES or any(fnmatch.fnmatch(name, g) for g in IGNORE_DIR_GLOBS)


def _file_ignored(name: str) -> bool:
    return name in IGNORE_FILE_NAMES or any(fnmatch.fnmatch(name, g) for g in IGNORE_FILE_GLOBS)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None


def repo_visible_files(root: Path) -> set[str] | None:
    """Relative posix paths git would see under root (tracked + untracked minus
    gitignored), or None when root is not inside a git work tree.

    Scoping reads to git's view keeps machine-local gitignored files (*.log,
    .env, editor droppings) out of vendored copies — otherwise one machine's
    junk becomes another machine's phantom drift."""
    proc = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if proc is None or proc.returncode != 0:
        return None
    return {p for p in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if p}


def read_tree(base: Path, visible: set[str] | None = None) -> dict[str, bytes]:
    """Return {relative_posix_path: file_bytes} for base, applying the ignore
    sets; `visible` (base-relative posix paths) further restricts to git's view."""
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
        if visible is not None and rel.as_posix() not in visible:
            continue
        if not path.is_file():
            continue
        out[rel.as_posix()] = path.read_bytes()
    return out


def write_tree(files: dict[str, bytes], dst: Path) -> None:
    """Replace dst with the given tree."""
    if dst.exists():
        shutil.rmtree(dst)
    for rel, data in files.items():
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def tree_digest(files: dict[str, bytes]) -> str:
    """Stable digest of a tree, including paths and boundaries."""
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


def previous_vendor_targets(root: Path) -> set[str]:
    """Targets declared by the registry at HEAD (either name), for retirement
    detection; empty when there is no readable committed registry."""
    for candidate in (REGISTRY, LEGACY_REGISTRY):
        proc = _git(root, "show", f"HEAD:{candidate.as_posix()}")
        if proc is None or proc.returncode != 0:
            continue
        try:
            cfg = json.loads(proc.stdout.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return set()
        previous, _ = desired_vendor_targets(cfg)
        return set(previous)
    return set()


def git_clean_under(root: Path, relative: str) -> bool:
    """True when git reports no uncommitted or untracked content under the path
    — everything there is recoverable from history, so removal is safe."""
    proc = _git(root, "status", "--porcelain", "--", relative)
    return proc is not None and proc.returncode == 0 and not proc.stdout.strip()


def skill_directories(root: Path) -> list[str]:
    """Every place a skill directory may live, as registry-style relative paths."""
    found: list[str] = []
    plugins = root / "plugins"
    if plugins.is_dir():
        for plugin in sorted(plugins.iterdir()):
            skills = plugin / "skills"
            if not skills.is_dir():
                continue
            for skill in sorted(skills.iterdir()):
                if skill.is_dir() and not _dir_ignored(skill.name):
                    found.append(skill.relative_to(root).as_posix())
    for family in (".agents", ".claude"):
        skills = root / family / "skills"
        if not skills.is_dir():
            continue
        for skill in sorted(skills.iterdir()):
            if skill.is_dir() and not _dir_ignored(skill.name):
                found.append(skill.relative_to(root).as_posix())
    return found


def build_codex_manifest(claude: dict, plugin_metadata: dict) -> dict:
    authored_interface = plugin_metadata["interface"]
    manifest = {
        "name": claude["name"],
        "version": claude["version"],
        "description": claude["description"],
    }
    for key in CODEX_MANIFEST_CARRY:
        if key in claude:
            manifest[key] = claude[key]
    manifest["skills"] = "./skills/"
    manifest["interface"] = {
        "displayName": authored_interface["displayName"],
        "shortDescription": authored_interface["shortDescription"],
        "longDescription": claude["description"],
        "developerName": claude["author"]["name"],
        "category": plugin_metadata["category"],
        "capabilities": authored_interface["capabilities"],
        "websiteURL": claude["homepage"],
        "defaultPrompt": authored_interface["defaultPrompt"],
    }
    return manifest


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_interface_metadata(name: str, plugin_metadata: object) -> list[str]:
    prefix = f"[config] {name}:"
    if not isinstance(plugin_metadata, dict):
        return [f"{prefix} dual_harness_plugins entry must be an object"]

    problems: list[str] = []
    if not _non_empty_string(plugin_metadata.get("category")):
        problems.append(f"{prefix} dual_harness_plugins entry needs a non-empty 'category'")

    interface = plugin_metadata.get("interface")
    if not isinstance(interface, dict):
        problems.append(f"{prefix} dual_harness_plugins entry needs an 'interface' object")
        return problems

    display_name = interface.get("displayName")
    if not _non_empty_string(display_name):
        problems.append(f"{prefix} interface.displayName must be a non-empty string")
    elif len(display_name) > 30:
        problems.append(f"{prefix} interface.displayName must be at most 30 characters")

    short_description = interface.get("shortDescription")
    if not _non_empty_string(short_description):
        problems.append(f"{prefix} interface.shortDescription must be a non-empty string")
    elif "\n" in short_description or "\r" in short_description:
        problems.append(f"{prefix} interface.shortDescription must be a single line")
    elif len(short_description) > 240:
        problems.append(f"{prefix} interface.shortDescription must be at most 240 characters")

    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        problems.append(f"{prefix} interface.capabilities must be a non-empty array")
    elif any(capability not in CODEX_CAPABILITIES for capability in capabilities):
        allowed = ", ".join(sorted(CODEX_CAPABILITIES))
        problems.append(f"{prefix} interface.capabilities values must be one of: {allowed}")

    default_prompt = interface.get("defaultPrompt")
    if not isinstance(default_prompt, list) or len(default_prompt) != 1:
        problems.append(f"{prefix} interface.defaultPrompt must contain exactly one starter prompt")
    elif not _non_empty_string(default_prompt[0]):
        problems.append(f"{prefix} interface.defaultPrompt[0] must be a non-empty string")
    elif len(default_prompt[0]) > 128:
        problems.append(f"{prefix} interface.defaultPrompt[0] must be at most 128 characters")

    return problems


def validate_claude_interface_sources(name: str, claude: dict) -> list[str]:
    missing: list[str] = []
    if not _non_empty_string(claude.get("description")):
        missing.append("description")
    author = claude.get("author")
    if not isinstance(author, dict) or not _non_empty_string(author.get("name")):
        missing.append("author.name")
    if not _non_empty_string(claude.get("homepage")):
        missing.append("homepage")
    if not missing:
        return []
    return [
        f"[codex-manifest] {name}: Claude manifest needs non-empty "
        + ", ".join(missing)
    ]


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def load_config(root: Path) -> dict:
    return json.loads((root / REGISTRY).read_text(encoding="utf-8"))


def _base_visible(visible: set[str] | None, base_rel: str) -> set[str] | None:
    if visible is None:
        return None
    prefix = base_rel + "/"
    return {p[len(prefix):] for p in visible if p.startswith(prefix)}


def sync(root: Path, write: bool) -> list[str]:
    """Perform (write) or verify (check) every derived artifact. Returns drift/error messages."""
    cfg = load_config(root)
    problems: list[str] = []
    visible = repo_visible_files(root)

    def tree(relative: str) -> dict[str, bytes]:
        return read_tree(root / relative, _base_visible(visible, relative))

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
    desired_targets, vendor_config_problems = desired_vendor_targets(cfg)
    problems.extend(vendor_config_problems)
    handled: set[str] = set(desired_targets)

    if not vendor_config_problems:
        # 1a. Retired edges: targets the committed registry declared but the
        # current one doesn't. Deletion is git-guarded, never destructive.
        for target in sorted(previous_vendor_targets(root) - set(desired_targets)):
            dst = root / target
            handled.add(target)
            if not dst.exists() and not dst.is_symlink():
                continue
            if not write:
                problems.append(f"[vendor] stale generated copy: {target} (edge removed from {REGISTRY.as_posix()}; run: python3 scripts/sync_plugins.py)")
                continue
            if dst.is_symlink() or not dst.is_dir() or not git_clean_under(root, target):
                problems.append(f"[vendor] retired copy has uncommitted or untracked content; refusing to remove: {target} (commit or move that work first, or delete the directory yourself to adopt it)")
                continue
            shutil.rmtree(dst)

        # 1b. Configured edges: copy each source into its targets.
        source_trees: dict[str, dict[str, bytes]] = {}
        for target, source in sorted(desired_targets.items()):
            if not (root / source).exists():
                problems.append(f"[vendor] source missing: {source}")
                continue
            if source not in source_trees:
                source_trees[source] = tree(source)
            src_tree = source_trees[source]
            if not src_tree:
                problems.append(f"[vendor] source has no vendorable files: {source}")
                continue
            if write:
                write_tree(src_tree, root / target)
            elif tree(target) != src_tree:
                problems.append(f"[vendor] out of sync: {target} != {source} (run: python3 scripts/sync_plugins.py)")

        # 1c. Undeclared copies: a skill directory byte-identical to a declared
        # source must be a declared target — otherwise it is an orphaned or
        # forgotten copy (or an authored twin that should diverge).
        source_digests: dict[str, str] = {}
        for source, files in source_trees.items():
            if files:
                source_digests[tree_digest(files)] = source
        if source_digests:
            for skill_dir in skill_directories(root):
                if skill_dir in handled or skill_dir in source_trees:
                    continue
                files = tree(skill_dir)
                if not files:
                    continue
                match = source_digests.get(tree_digest(files))
                if match is not None:
                    problems.append(f"[vendor] undeclared byte-identical copy of {match}: {skill_dir} — declare a vendored_skills edge, delete the directory, or change its content to adopt it as authored")

    # 2. Codex manifests.
    display_name_owners: dict[str, str] = {}
    for name in sorted(dual):
        plugin_metadata = cfg["dual_harness_plugins"][name]
        if not isinstance(plugin_metadata, dict):
            continue
        interface = plugin_metadata.get("interface")
        if not isinstance(interface, dict):
            continue
        display_name = interface.get("displayName")
        if not _non_empty_string(display_name):
            continue
        previous = display_name_owners.get(display_name)
        if previous is not None:
            problems.append(
                f"[config] {name}: interface.displayName duplicates {previous}: {display_name!r}"
            )
        else:
            display_name_owners[display_name] = name

    for name in sorted(dual):
        plugin_metadata = cfg["dual_harness_plugins"][name]
        interface_problems = validate_interface_metadata(name, plugin_metadata)
        problems.extend(interface_problems)
        claude_path = root / "plugins" / name / ".claude-plugin" / "plugin.json"
        if not claude_path.exists():
            problems.append(f"[codex-manifest] missing Claude manifest for {name}")
            continue
        claude = json.loads(claude_path.read_text(encoding="utf-8"))
        missing = [k for k in ("name", "version") if k not in claude]
        if missing:
            problems.append(f"[codex-manifest] {name}: Claude manifest missing {', '.join(missing)}")
            continue
        source_problems = validate_claude_interface_sources(name, claude)
        problems.extend(source_problems)
        if interface_problems or source_problems:
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
        want = dumps(build_codex_manifest(claude, plugin_metadata)).encode("utf-8")
        codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
        if write:
            codex_path.parent.mkdir(parents=True, exist_ok=True)
            codex_path.write_bytes(want)
        elif not codex_path.exists() or codex_path.read_bytes() != want:
            problems.append(f"[codex-manifest] out of sync: {codex_path.relative_to(root)} (run: python3 scripts/sync_plugins.py)")

    # 3. A Claude-only plugin must not present itself as a Codex plugin.
    for name in sorted(claude_only & existing):
        stale = root / "plugins" / name / ".codex-plugin"
        if stale.exists():
            if write:
                shutil.rmtree(stale)
            else:
                problems.append(f"[codex-manifest] stale .codex-plugin/ for Claude-only plugin {name} (run: python3 scripts/sync_plugins.py)")

    return problems


def find_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "plugins").is_dir() and (candidate / REGISTRY).is_file():
            return candidate
    raise SystemExit(f"could not locate repo root (needs plugins/ and {REGISTRY.as_posix()})")


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
            print(f"\n{len(problems)} issue(s). Run: python3 scripts/sync_plugins.py", file=sys.stderr)
            return 1
        # In write mode, anything that blocked or skipped generation is still fatal.
        fatal = [
            problem
            for problem in problems
            if problem.startswith(("[config]", "[vendor]", "[codex-manifest]"))
        ]
        if fatal:
            return 1
    print("plugin sync: checked" if args.check else "plugin sync: written", "(no issues)" if not problems else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
