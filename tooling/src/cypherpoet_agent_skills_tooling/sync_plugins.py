#!/usr/bin/env python3
"""Generate and validate derived artifacts for CypherPoet plugin repositories.

The repository registry classifies plugins, authors Codex presentation metadata,
and declares vendored skill edges. This module composes Codex manifests from the
registry and Claude manifests, guards vendored copies, and reports drift.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Sequence
from urllib.parse import urlsplit


REGISTRY = Path("scripts") / "plugin-registry.json"
LEGACY_REGISTRY = Path("scripts") / "dual-harness.json"
CODEX_PROJECTIONS = Path("codex-plugins")

IGNORE_DIR_NAMES = {"__pycache__", "evals", ".git"}
IGNORE_DIR_GLOBS = ("*-workspace",)
IGNORE_FILE_NAMES = {".DS_Store"}
IGNORE_FILE_GLOBS = ("*.pyc",)

CODEX_MANIFEST_CARRY = ("author", "homepage", "repository", "license", "keywords")
SUPPORTED_CODEX_CATEGORIES = {
    "Productivity",
    "Creativity",
    "Developer Tools",
    "Business & Operations",
    "Data & Analytics",
    "Communication",
    "Education & Research",
    "Security",
    "Finance",
    "Healthcare",
    "Travel",
    "Entertainment",
    "Other",
}
DISPLAY_NAME_MAX_LENGTH = 30
SHORT_DESCRIPTION_MAX_LENGTH = 30
PLUGIN_DESCRIPTION_MAX_LENGTH = 1024
LONG_DESCRIPTION_MAX_LENGTH = 4000
DEVELOPER_NAME_MAX_LENGTH = 80
CAPABILITY_MAX_COUNT = 20
CAPABILITY_MAX_LENGTH = 120
DEFAULT_PROMPT_MAX_COUNT = 3
DEFAULT_PROMPT_MAX_LENGTH = 128
SOURCE_HOMEPAGE_MAX_LENGTH = 2048
WEBSITE_URL_MAX_LENGTH = 1024

_UNSUPPORTED_TEXT_CATEGORIES = {"Cf", "Cs", "Zl", "Zp"}
_UNSUPPORTED_URL_CHARACTERS = set(' <>"{}|\\^`')
_APP_MENTION = re.compile(r"(?<!\S)@\S+")
_CLAUDE_INVOCATION_FIELD = re.compile(
    r"^(disable-model-invocation|disable_model_invocation):[ \t]*"
    r"(true|false|yes|no|on|off|1|0)[ \t]*(?:#.*)?(?:\r?\n)?$",
    re.IGNORECASE,
)
_CLAUDE_INVOCATION_FIELD_PREFIX = re.compile(
    r"^(disable-model-invocation|disable_model_invocation):",
    re.IGNORECASE,
)
_YAML_FALSE_VALUES = {"false", "no", "off", "0"}
_YAML_TRUE_VALUES = {"true", "yes", "on", "1"}


def _dir_ignored(name: str) -> bool:
    return name in IGNORE_DIR_NAMES or any(
        fnmatch.fnmatch(name, pattern) for pattern in IGNORE_DIR_GLOBS
    )


def _file_ignored(name: str) -> bool:
    return name in IGNORE_FILE_NAMES or any(
        fnmatch.fnmatch(name, pattern) for pattern in IGNORE_FILE_GLOBS
    )


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None


def repo_visible_files(root: Path) -> set[str] | None:
    """Return paths visible to git, or None outside a git work tree."""
    process = _git(
        root,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
    )
    if process is None or process.returncode != 0:
        return None
    return {
        path
        for path in process.stdout.decode("utf-8", "surrogateescape").split("\0")
        if path
    }


def read_tree(base: Path, visible: set[str] | None = None) -> dict[str, bytes]:
    """Read a directory tree while applying vendoring ignore rules."""
    files: dict[str, bytes] = {}
    if not base.exists():
        return files
    for path in sorted(base.rglob("*")):
        relative_path = path.relative_to(base)
        if any(_dir_ignored(part) for part in relative_path.parts[:-1]):
            continue
        if path.is_dir() or _file_ignored(path.name):
            continue
        if visible is not None and relative_path.as_posix() not in visible:
            continue
        if path.is_file():
            files[relative_path.as_posix()] = path.read_bytes()
    return files


def write_tree(files: dict[str, bytes], destination: Path) -> None:
    """Replace a generated destination tree with the supplied file map."""
    if destination.exists():
        shutil.rmtree(destination)
    for relative_path, data in files.items():
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def tree_digest(files: dict[str, bytes]) -> str:
    """Return a stable digest that includes paths, contents, and boundaries."""
    digest = hashlib.sha256()
    for relative_path, data in sorted(files.items()):
        path_bytes = relative_path.encode("utf-8")
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def valid_skill_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        return False
    parts = path.parts
    return (
        len(parts) == 4 and parts[0] == "plugins" and parts[2] == "skills"
    ) or (
        len(parts) == 3
        and parts[0] in {".agents", ".claude"}
        and parts[1] == "skills"
    )


def desired_vendor_targets(configuration: dict) -> tuple[dict[str, str], list[str]]:
    desired: dict[str, str] = {}
    problems: list[str] = []
    for index, edge in enumerate(configuration["vendored_skills"]):
        if not isinstance(edge, dict):
            problems.append(f"[vendor] vendored_skills[{index}] must be an object")
            continue
        source = edge.get("source")
        targets = edge.get("targets")
        if not valid_skill_path(source):
            problems.append(f"[vendor] invalid source path: {source!r}")
            continue
        if not isinstance(targets, list) or not targets:
            problems.append(f"[vendor] {source}: targets must be a non-empty array")
            continue
        for target in targets:
            if not valid_skill_path(target):
                problems.append(f"[vendor] invalid target path: {target!r}")
                continue
            if target == source:
                problems.append(f"[vendor] source and target are identical: {target}")
                continue
            previous_source = desired.get(target)
            if previous_source is not None:
                problems.append(
                    f"[vendor] duplicate target {target}: declared by "
                    f"{previous_source} and {source}"
                )
                continue
            desired[target] = source
    for source in sorted(set(desired.values()) & set(desired)):
        problems.append(
            f"[vendor] vendoring chains are not allowed: source is also a target: {source}"
        )
    return desired, problems


def previous_vendor_targets(root: Path) -> set[str]:
    """Return vendored targets declared by the committed registry."""
    for candidate in (REGISTRY, LEGACY_REGISTRY):
        process = _git(root, "show", f"HEAD:{candidate.as_posix()}")
        if process is None or process.returncode != 0:
            continue
        try:
            configuration = json.loads(process.stdout.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return set()
        if (
            not isinstance(configuration, dict)
            or not isinstance(configuration.get("vendored_skills"), list)
        ):
            return set()
        previous, _ = desired_vendor_targets(configuration)
        return set(previous)
    return set()


def git_clean_under(root: Path, relative_path: str) -> bool:
    process = _git(root, "status", "--porcelain", "--", relative_path)
    return process is not None and process.returncode == 0 and not process.stdout.strip()


def skill_directories(root: Path) -> list[str]:
    """Return every directory position where a skill may be authored or shipped."""
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


def build_codex_manifest(claude_manifest: dict, plugin_metadata: dict) -> dict:
    """Compose a Codex manifest from shared identity and Codex-only metadata."""
    authored_interface = plugin_metadata["interface"]
    manifest = {
        "name": claude_manifest["name"],
        "version": claude_manifest["version"],
        "description": claude_manifest["description"],
    }
    for key in CODEX_MANIFEST_CARRY:
        if key in claude_manifest:
            manifest[key] = claude_manifest[key]
    manifest["skills"] = "./skills/"
    manifest["interface"] = {
        "displayName": authored_interface["displayName"],
        "shortDescription": authored_interface["shortDescription"],
        "longDescription": claude_manifest["description"],
        "developerName": claude_manifest["author"]["name"],
        "category": plugin_metadata["category"],
        "capabilities": authored_interface["capabilities"],
        "websiteURL": claude_manifest["homepage"],
        "defaultPrompt": authored_interface["defaultPrompt"],
    }
    return manifest


def codex_plugin_relative_path(name: str, plugin_metadata: dict) -> Path:
    """Return the catalog/install root for one generated Codex plugin."""
    if plugin_metadata.get("codexProjection") is True:
        return CODEX_PROJECTIONS / name
    return Path("plugins") / name


def _normalized_uniqueness_key(value: str, *, casefold: bool) -> str:
    normalized = " ".join(unicodedata.normalize("NFKC", value).split())
    return normalized.casefold() if casefold else normalized


def _validate_text(
    value: object,
    field: str,
    *,
    maximum_length: int,
    allow_line_feed: bool = False,
) -> list[str]:
    if not isinstance(value, str):
        return [f"{field} must be a non-empty string"]

    problems: list[str] = []
    if not value:
        problems.append(f"{field} must be a non-empty string")
        return problems
    if not value.strip():
        problems.append(f"{field} must contain non-whitespace text")
    elif value != value.strip():
        problems.append(f"{field} must not contain surrounding whitespace")
    if len(value) > maximum_length:
        problems.append(f"{field} must be at most {maximum_length} characters")
    if not allow_line_feed and "\n" in value:
        problems.append(f"{field} must be a single line")

    unsupported = False
    for character in value:
        category = unicodedata.category(character)
        if category == "Cc" and not (allow_line_feed and character == "\n"):
            unsupported = True
            break
        if category in _UNSUPPORTED_TEXT_CATEGORIES:
            unsupported = True
            break
    if unsupported:
        qualifier = " (line feeds are allowed)" if allow_line_feed else ""
        problems.append(f"{field} contains unsupported text characters{qualifier}")
    return problems


def _validate_url(value: object, field: str, *, maximum_length: int) -> list[str]:
    problems = _validate_text(
        value,
        field,
        maximum_length=maximum_length,
    )
    if not isinstance(value, str) or not value:
        return problems

    if any(character.isspace() for character in value) or any(
        character in _UNSUPPORTED_URL_CHARACTERS for character in value
    ):
        problems.append(f"{field} contains unsupported URL characters")

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        parsed = None
        hostname = None
    if parsed is None or parsed.scheme.lower() != "https" or not parsed.netloc or not hostname:
        problems.append(f"{field} must be an absolute https URL with a host")
    elif parsed.username is not None or parsed.password is not None:
        problems.append(f"{field} must not contain credentials")
    return problems


def _validate_string_list(
    value: object,
    field: str,
    *,
    minimum_count: int,
    maximum_count: int,
    maximum_item_length: int,
    casefold_duplicates: bool,
    reject_app_mentions: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        return [f"{field} must be an array"]

    problems: list[str] = []
    if not minimum_count <= len(value) <= maximum_count:
        problems.append(
            f"{field} must contain between {minimum_count} and {maximum_count} entries"
        )

    owners: dict[str, int] = {}
    for index, item in enumerate(value):
        item_field = f"{field}[{index}]"
        problems.extend(
            _validate_text(
                item,
                item_field,
                maximum_length=maximum_item_length,
            )
        )
        if not isinstance(item, str) or not item:
            continue
        normalized = _normalized_uniqueness_key(
            item,
            casefold=casefold_duplicates,
        )
        previous_index = owners.get(normalized)
        if previous_index is not None:
            problems.append(
                f"{item_field} duplicates {field}[{previous_index}] after normalization"
            )
        else:
            owners[normalized] = index
        if reject_app_mentions and _APP_MENTION.search(item):
            problems.append(f"{item_field} must not contain an app @mention")
    return problems


def validate_codex_interface(
    interface: object,
    *,
    source_homepage: object | None = None,
) -> list[str]:
    """Validate the final Codex interface contract emitted by the generator."""
    if not isinstance(interface, dict):
        return ["interface must be an object"]

    problems: list[str] = []
    problems.extend(
        _validate_text(
            interface.get("displayName"),
            "interface.displayName",
            maximum_length=DISPLAY_NAME_MAX_LENGTH,
        )
    )
    problems.extend(
        _validate_text(
            interface.get("shortDescription"),
            "interface.shortDescription",
            maximum_length=SHORT_DESCRIPTION_MAX_LENGTH,
        )
    )
    problems.extend(
        _validate_text(
            interface.get("longDescription"),
            "interface.longDescription",
            maximum_length=LONG_DESCRIPTION_MAX_LENGTH,
            allow_line_feed=True,
        )
    )
    problems.extend(
        _validate_text(
            interface.get("developerName"),
            "interface.developerName",
            maximum_length=DEVELOPER_NAME_MAX_LENGTH,
        )
    )

    category = interface.get("category")
    problems.extend(
        _validate_text(
            category,
            "interface.category",
            maximum_length=max(len(value) for value in SUPPORTED_CODEX_CATEGORIES),
        )
    )
    if isinstance(category, str) and category not in SUPPORTED_CODEX_CATEGORIES:
        allowed = ", ".join(sorted(SUPPORTED_CODEX_CATEGORIES))
        problems.append(f"interface.category must be one of: {allowed}")

    problems.extend(
        _validate_string_list(
            interface.get("capabilities"),
            "interface.capabilities",
            minimum_count=1,
            maximum_count=CAPABILITY_MAX_COUNT,
            maximum_item_length=CAPABILITY_MAX_LENGTH,
            casefold_duplicates=True,
        )
    )
    problems.extend(
        _validate_string_list(
            interface.get("defaultPrompt"),
            "interface.defaultPrompt",
            minimum_count=1,
            maximum_count=DEFAULT_PROMPT_MAX_COUNT,
            maximum_item_length=DEFAULT_PROMPT_MAX_LENGTH,
            casefold_duplicates=False,
            reject_app_mentions=True,
        )
    )

    website_url = interface.get("websiteURL")
    problems.extend(
        _validate_url(
            website_url,
            "interface.websiteURL",
            maximum_length=WEBSITE_URL_MAX_LENGTH,
        )
    )
    if source_homepage is not None:
        problems.extend(
            _validate_url(
                source_homepage,
                "source homepage",
                maximum_length=SOURCE_HOMEPAGE_MAX_LENGTH,
            )
        )
        if website_url != source_homepage:
            problems.append("interface.websiteURL must equal the source homepage")
    return problems


def validate_interface_metadata(name: str, plugin_metadata: object) -> list[str]:
    prefix = f"[config] {name}: "
    if not isinstance(plugin_metadata, dict):
        return [f"{prefix}dual_harness_plugins entry must be an object"]
    codex_projection = plugin_metadata.get("codexProjection", False)
    if not isinstance(codex_projection, bool):
        return [f"{prefix}codexProjection must be a boolean when provided"]
    interface = plugin_metadata.get("interface")
    if not isinstance(interface, dict):
        return [f"{prefix}dual_harness_plugins entry needs an interface object"]

    authored_candidate = {
        "displayName": interface.get("displayName"),
        "shortDescription": interface.get("shortDescription"),
        "longDescription": "Generated from the Claude manifest.",
        "developerName": "Generated author",
        "category": plugin_metadata.get("category"),
        "capabilities": interface.get("capabilities"),
        "websiteURL": "https://example.com/plugin",
        "defaultPrompt": interface.get("defaultPrompt"),
    }
    return [
        f"{prefix}{problem}"
        for problem in validate_codex_interface(authored_candidate)
        if not problem.startswith("interface.longDescription")
        and not problem.startswith("interface.developerName")
        and not problem.startswith("interface.websiteURL")
    ]


def dumps(value: dict) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _load_config(root: Path) -> tuple[dict | None, list[str]]:
    path = root / REGISTRY
    try:
        configuration = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        return None, [f"[config] could not read {REGISTRY.as_posix()}: {error}"]
    except json.JSONDecodeError as error:
        return None, [f"[config] {REGISTRY.as_posix()} is not valid JSON: {error}"]
    if not isinstance(configuration, dict):
        return None, [f"[config] {REGISTRY.as_posix()} must contain an object"]

    problems: list[str] = []
    expected_types = {
        "vendored_skills": list,
        "dual_harness_plugins": dict,
        "claude_only_plugins": dict,
    }
    for field, expected_type in expected_types.items():
        if not isinstance(configuration.get(field), expected_type):
            type_name = "array" if expected_type is list else "object"
            problems.append(f"[config] {field} must be an {type_name}")
    return (configuration if not problems else None), problems


def _read_json_object(path: Path, label: str) -> tuple[dict | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        return None, [f"{label}: could not read JSON: {error}"]
    except json.JSONDecodeError as error:
        return None, [f"{label}: invalid JSON: {error}"]
    if not isinstance(value, dict):
        return None, [f"{label}: JSON must contain an object"]
    return value, []


def _validate_claude_manifest_shape(name: str, claude_manifest: dict) -> list[str]:
    prefix = f"[codex-manifest] {name}: "
    problems: list[str] = []
    for field in ("name", "version", "homepage"):
        value = claude_manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{prefix}Claude manifest needs non-empty {field}")
    problems.extend(
        f"{prefix}{problem}"
        for problem in _validate_text(
            claude_manifest.get("description"),
            "Claude manifest description",
            maximum_length=PLUGIN_DESCRIPTION_MAX_LENGTH,
            allow_line_feed=True,
        )
    )
    if isinstance(claude_manifest.get("name"), str) and claude_manifest["name"] != name:
        problems.append(f"{prefix}Claude manifest name must equal the plugin directory name")
    author = claude_manifest.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        problems.append(f"{prefix}Claude manifest needs non-empty author.name")
    return problems


def _unported_components(plugin_directory: Path, claude_manifest: dict) -> list[str]:
    unported = [
        key
        for key in ("mcpServers", "hooks", "agents", "commands")
        if key in claude_manifest
    ]
    skills_value = claude_manifest.get("skills", "./skills/")
    if not (
        isinstance(skills_value, str)
        and skills_value.lstrip("./").rstrip("/") == "skills"
    ):
        unported.append("skills (custom path)")
    for component in ("commands", "agents", "hooks"):
        if (plugin_directory / component).is_dir() and component not in unported:
            unported.append(f"{component}/ (auto-discovered)")
    if (plugin_directory / ".mcp.json").is_file() and "mcpServers" not in unported:
        unported.append(".mcp.json")
    return unported


def _strip_claude_invocation_field(
    skill_manifest: bytes,
    label: str,
) -> tuple[bytes | None, bool, list[str]]:
    """Remove Claude-only invocation metadata from one Codex projection."""
    try:
        text = skill_manifest.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, False, [
            f"[codex-projection] {label}: SKILL.md is not UTF-8: {error}"
        ]
    if not text.startswith("---\n"):
        return None, False, [
            f"[codex-projection] {label}: SKILL.md must start with YAML frontmatter"
        ]

    lines = text.splitlines(keepends=True)
    frontmatter_end = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if frontmatter_end is None:
        return None, False, [
            f"[codex-projection] {label}: SKILL.md frontmatter is not closed"
        ]

    matches: list[tuple[int, bool]] = []
    problems: list[str] = []
    for index in range(1, frontmatter_end):
        line = lines[index]
        match = _CLAUDE_INVOCATION_FIELD.fullmatch(line)
        if match is not None:
            value = match.group(2).lower()
            matches.append((index, value in _YAML_TRUE_VALUES))
        elif _CLAUDE_INVOCATION_FIELD_PREFIX.match(line):
            problems.append(
                f"[codex-projection] {label}: Claude invocation field must use "
                "a YAML boolean"
            )
    if len(matches) > 1:
        problems.append(
            f"[codex-projection] {label}: Claude invocation field is duplicated"
        )
    if problems:
        return None, False, problems
    if not matches:
        return skill_manifest, False, []

    index, manual_only = matches[0]
    del lines[index]
    return "".join(lines).encode("utf-8"), manual_only, []


def _codex_policy_disables_implicit_invocation(agent_manifest: bytes) -> bool:
    try:
        text = agent_manifest.decode("utf-8")
    except UnicodeDecodeError:
        return False

    section: str | None = None
    for line in text.splitlines():
        if line and not line[0].isspace():
            match = re.match(r"^([A-Za-z0-9_-]+):(?:\s*(?:#.*)?)?$", line)
            section = match.group(1) if match is not None else None
            continue
        if section != "policy":
            continue
        match = re.match(
            r"^[ \t]+allow_implicit_invocation:[ \t]*"
            r"(true|false|yes|no|on|off|1|0)[ \t]*(?:#.*)?$",
            line,
            re.IGNORECASE,
        )
        if match is not None:
            return match.group(1).lower() in _YAML_FALSE_VALUES
    return False


def _prepare_codex_projection(
    root: Path,
    name: str,
    plugin_directory: Path,
    manifest_bytes: bytes,
    visible: set[str] | None,
) -> tuple[dict[str, bytes] | None, list[str]]:
    plugin_relative = plugin_directory.relative_to(root).as_posix()
    source_tree = read_tree(
        plugin_directory,
        _base_visible(visible, plugin_relative),
    )
    projected_tree = {
        path: data
        for path, data in source_tree.items()
        if not path.startswith(".claude-plugin/")
        and path != ".codex-plugin/plugin.json"
    }
    projected_tree[".codex-plugin/plugin.json"] = manifest_bytes

    manual_only_skills: list[str] = []
    problems: list[str] = []
    for path in sorted(projected_tree):
        parts = Path(path).parts
        if len(parts) != 3 or parts[0] != "skills" or parts[2] != "SKILL.md":
            continue
        transformed, manual_only, transform_problems = _strip_claude_invocation_field(
            projected_tree[path],
            f"{name}/{parts[1]}",
        )
        problems.extend(transform_problems)
        if transformed is None:
            continue
        projected_tree[path] = transformed
        if manual_only:
            manual_only_skills.append(parts[1])

    if not manual_only_skills and not problems:
        problems.append(
            f"[codex-projection] {name}: codexProjection requires at least one "
            "Claude-only disable-model-invocation field"
        )
    for skill_name in manual_only_skills:
        agent_path = f"skills/{skill_name}/agents/openai.yaml"
        agent_manifest = projected_tree.get(agent_path)
        if agent_manifest is None or not _codex_policy_disables_implicit_invocation(
            agent_manifest
        ):
            problems.append(
                f"[codex-projection] {name}/{skill_name}: removing Claude's manual-only "
                "field requires policy.allow_implicit_invocation: false in "
                "agents/openai.yaml"
            )
    return (projected_tree if not problems else None), problems


def _prepare_codex_manifests(
    root: Path,
    dual_plugins: dict,
    visible: set[str] | None,
) -> tuple[dict[Path, bytes], dict[Path, dict[str, bytes]], list[str]]:
    desired: dict[Path, bytes] = {}
    desired_projections: dict[Path, dict[str, bytes]] = {}
    problems: list[str] = []

    display_name_owners: dict[str, str] = {}
    for name, plugin_metadata in sorted(dual_plugins.items()):
        if not isinstance(plugin_metadata, dict):
            continue
        interface = plugin_metadata.get("interface")
        if not isinstance(interface, dict):
            continue
        display_name = interface.get("displayName")
        if not isinstance(display_name, str) or not display_name:
            continue
        key = _normalized_uniqueness_key(display_name, casefold=True)
        previous_owner = display_name_owners.get(key)
        if previous_owner is not None:
            problems.append(
                f"[config] {name}: interface.displayName duplicates {previous_owner} "
                f"after normalization: {display_name!r}"
            )
        else:
            display_name_owners[key] = name

    for name, plugin_metadata in sorted(dual_plugins.items()):
        plugin_problems = validate_interface_metadata(name, plugin_metadata)
        problems.extend(plugin_problems)

        plugin_directory = root / "plugins" / name
        claude_path = plugin_directory / ".claude-plugin" / "plugin.json"
        claude_manifest, read_problems = _read_json_object(
            claude_path,
            f"[codex-manifest] {name}",
        )
        problems.extend(read_problems)
        if claude_manifest is None:
            continue

        shape_problems = _validate_claude_manifest_shape(name, claude_manifest)
        problems.extend(shape_problems)
        unported = _unported_components(plugin_directory, claude_manifest)
        if unported:
            problems.append(
                f"[codex-manifest] {name}: Claude-only components "
                f"({', '.join(unported)}) — the generator does not carry these into "
                ".codex-plugin; port them or make the plugin Claude-only"
            )
        if plugin_problems or read_problems or shape_problems or unported:
            continue

        manifest = build_codex_manifest(claude_manifest, plugin_metadata)
        interface_problems = validate_codex_interface(
            manifest["interface"],
            source_homepage=claude_manifest["homepage"],
        )
        problems.extend(
            f"[codex-manifest] {name}: {problem}"
            for problem in interface_problems
        )
        if interface_problems:
            continue
        manifest_bytes = dumps(manifest).encode("utf-8")
        if plugin_metadata.get("codexProjection") is True:
            projection, projection_problems = _prepare_codex_projection(
                root,
                name,
                plugin_directory,
                manifest_bytes,
                visible,
            )
            problems.extend(projection_problems)
            if projection is not None:
                desired_projections[root / CODEX_PROJECTIONS / name] = projection
        else:
            desired[plugin_directory / ".codex-plugin" / "plugin.json"] = manifest_bytes
    return desired, desired_projections, problems


def _base_visible(visible: set[str] | None, base_relative: str) -> set[str] | None:
    if visible is None:
        return None
    prefix = base_relative + "/"
    return {path[len(prefix) :] for path in visible if path.startswith(prefix)}


def _sync_vendored_skills(
    root: Path,
    configuration: dict,
    *,
    write: bool,
    visible: set[str] | None,
) -> list[str]:
    problems: list[str] = []
    desired_targets, configuration_problems = desired_vendor_targets(configuration)
    problems.extend(configuration_problems)
    if configuration_problems:
        return problems

    def tree(relative_path: str) -> dict[str, bytes]:
        return read_tree(
            root / relative_path,
            _base_visible(visible, relative_path),
        )

    handled: set[str] = set(desired_targets)
    for target in sorted(previous_vendor_targets(root) - set(desired_targets)):
        destination = root / target
        handled.add(target)
        if not destination.exists() and not destination.is_symlink():
            continue
        if not write:
            problems.append(
                f"[vendor] stale generated copy: {target} "
                f"(edge removed from {REGISTRY.as_posix()}; run: "
                "python3 scripts/sync_plugins.py)"
            )
            continue
        if (
            destination.is_symlink()
            or not destination.is_dir()
            or not git_clean_under(root, target)
        ):
            problems.append(
                "[vendor] retired copy has uncommitted or untracked content; "
                f"refusing to remove: {target} (commit or move that work first, "
                "or delete the directory yourself to adopt it)"
            )
            continue
        shutil.rmtree(destination)

    source_trees: dict[str, dict[str, bytes]] = {}
    for target, source in sorted(desired_targets.items()):
        if not (root / source).exists():
            problems.append(f"[vendor] source missing: {source}")
            continue
        if source not in source_trees:
            source_trees[source] = tree(source)
        source_tree = source_trees[source]
        if not source_tree:
            problems.append(f"[vendor] source has no vendorable files: {source}")
            continue
        if write:
            write_tree(source_tree, root / target)
        elif tree(target) != source_tree:
            problems.append(
                f"[vendor] out of sync: {target} != {source} "
                "(run: python3 scripts/sync_plugins.py)"
            )

    source_digests = {
        tree_digest(files): source
        for source, files in source_trees.items()
        if files
    }
    if source_digests:
        for skill_directory in skill_directories(root):
            if skill_directory in handled or skill_directory in source_trees:
                continue
            files = tree(skill_directory)
            if not files:
                continue
            matching_source = source_digests.get(tree_digest(files))
            if matching_source is not None:
                problems.append(
                    f"[vendor] undeclared byte-identical copy of {matching_source}: "
                    f"{skill_directory} — declare a vendored_skills edge, delete the "
                    "directory, or change its content to adopt it as authored"
                )
    return problems


def _apply_codex_manifest_plan(
    root: Path,
    desired_manifests: dict[Path, bytes],
    desired_projections: dict[Path, dict[str, bytes]],
    projected_plugins: set[str],
    claude_only_plugins: set[str],
    existing_plugins: set[str],
    *,
    write: bool,
    visible: set[str] | None,
) -> list[str]:
    problems: list[str] = []
    for path, desired_bytes in sorted(desired_manifests.items()):
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(desired_bytes)
        elif not path.exists() or path.read_bytes() != desired_bytes:
            problems.append(
                f"[codex-manifest] out of sync: {path.relative_to(root)} "
                "(run: python3 scripts/sync_plugins.py)"
            )

    for path, desired_tree in sorted(desired_projections.items()):
        relative_path = path.relative_to(root).as_posix()
        if write:
            write_tree(desired_tree, path)
        elif read_tree(path, _base_visible(visible, relative_path)) != desired_tree:
            problems.append(
                f"[codex-projection] out of sync: {relative_path} "
                "(run: python3 scripts/sync_plugins.py)"
            )

    for name in sorted(projected_plugins & existing_plugins):
        stale_manifest = (
            root / "plugins" / name / ".codex-plugin" / "plugin.json"
        )
        if not stale_manifest.exists() and not stale_manifest.is_symlink():
            continue
        relative_path = stale_manifest.relative_to(root).as_posix()
        if not write:
            problems.append(
                f"[codex-projection] stale in-place Codex manifest: {relative_path} "
                "(run: python3 scripts/sync_plugins.py)"
            )
        elif stale_manifest.is_symlink() or not stale_manifest.is_file():
            problems.append(
                f"[codex-projection] refusing to remove non-file generated path: {relative_path}"
            )
        else:
            stale_manifest.unlink()
            try:
                stale_manifest.parent.rmdir()
            except OSError:
                pass

    projections_root = root / CODEX_PROJECTIONS
    existing_projection_names = (
        {
            path.name
            for path in projections_root.iterdir()
            if path.is_dir() or path.is_symlink()
        }
        if projections_root.is_dir()
        else set()
    )
    for name in sorted(existing_projection_names - projected_plugins):
        stale = projections_root / name
        relative_path = stale.relative_to(root).as_posix()
        if not write:
            problems.append(
                f"[codex-projection] stale generated projection: {relative_path} "
                "(run: python3 scripts/sync_plugins.py)"
            )
        elif stale.is_symlink() or not stale.is_dir() or not git_clean_under(
            root, relative_path
        ):
            problems.append(
                f"[codex-projection] refusing to remove modified generated path: {relative_path}"
            )
        else:
            shutil.rmtree(stale)

    for name in sorted(claude_only_plugins & existing_plugins):
        stale = root / "plugins" / name / ".codex-plugin"
        if not stale.exists():
            continue
        if write:
            shutil.rmtree(stale)
        else:
            problems.append(
                f"[codex-manifest] stale .codex-plugin/ for Claude-only plugin {name} "
                "(run: python3 scripts/sync_plugins.py)"
            )
    return problems


def sync(root: Path, write: bool) -> list[str]:
    """Write or verify all derived artifacts and return every problem found."""
    root = root.resolve()
    configuration, configuration_problems = _load_config(root)
    if configuration is None:
        return configuration_problems

    problems: list[str] = []
    plugins_directory = root / "plugins"
    if not plugins_directory.is_dir():
        return ["[config] plugins directory is missing"]
    existing_plugins = {
        path.name for path in plugins_directory.iterdir() if path.is_dir()
    }
    dual_plugins = configuration["dual_harness_plugins"]
    claude_only_plugins = set(configuration["claude_only_plugins"])
    dual_plugin_names = set(dual_plugins)

    for name in sorted(dual_plugin_names & claude_only_plugins):
        problems.append(
            f"[config] {name} is listed as both dual-harness and Claude-only"
        )
    for name in sorted((dual_plugin_names | claude_only_plugins) - existing_plugins):
        problems.append(f"[config] {name} is classified but no plugins/{name}/ exists")
    for name in sorted(existing_plugins - dual_plugin_names - claude_only_plugins):
        problems.append(
            f"[config] plugins/{name}/ is unclassified — add it to "
            "dual_harness_plugins or claude_only_plugins"
        )

    visible = repo_visible_files(root)
    desired_manifests, desired_projections, manifest_problems = (
        _prepare_codex_manifests(
            root,
            dual_plugins,
            visible,
        )
    )
    problems.extend(manifest_problems)

    vendor_write = write and not problems
    vendor_problems = _sync_vendored_skills(
        root,
        configuration,
        write=vendor_write,
        visible=visible,
    )
    problems.extend(vendor_problems)

    if not manifest_problems and (not write or not problems):
        problems.extend(
            _apply_codex_manifest_plan(
                root,
                desired_manifests,
                desired_projections,
                {
                    name
                    for name, metadata in dual_plugins.items()
                    if isinstance(metadata, dict)
                    and metadata.get("codexProjection") is True
                },
                claude_only_plugins,
                existing_plugins,
                write=write,
                visible=visible,
            )
        )
    return problems


def find_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "plugins").is_dir() and (candidate / REGISTRY).is_file():
            return candidate
    raise SystemExit(
        f"could not locate repo root (needs plugins/ and {REGISTRY.as_posix()})"
    )


def main(
    arguments: Sequence[str] | None = None,
    *,
    default_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only; exit 1 on drift")
    parser.add_argument("--root", type=Path, help="repository root (defaults to the current repo)")
    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.root is not None:
        root = find_root(parsed_arguments.root.resolve())
    elif default_root is not None:
        root = find_root(default_root.resolve())
    else:
        root = find_root(Path.cwd().resolve())
    problems = sync(root, write=not parsed_arguments.check)

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        if parsed_arguments.check:
            print(
                f"\n{len(problems)} issue(s). Run: python3 scripts/sync_plugins.py",
                file=sys.stderr,
            )
        return 1
    status = "checked" if parsed_arguments.check else "written"
    print(f"plugin sync: {status} (no issues)")
    return 0


def console_main() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
