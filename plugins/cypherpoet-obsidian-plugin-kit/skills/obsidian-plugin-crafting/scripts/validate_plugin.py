#!/usr/bin/env python3
"""Obsidian plugin submission preflight.

Validates manifest.json, versions.json, and release readiness against the rules
in Obsidian's developer docs (docs.obsidian.md — Reference/Manifest,
Releasing/Submission requirements). Complements eslint-plugin-obsidianmd's
validate-manifest rule: this runs with no install, no network, and no writes,
and covers the versions.json and release-readiness checks the linter doesn't.

Usage:
    python3 validate_plugin.py [path-to-plugin-repo]   # default: cwd

Exit code: 1 if any ERROR, else 0. WARNs are review comments in waiting.
Pure standard library — no dependencies, runs anywhere Python 3.8+ does.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

SEMVER = re.compile(r"\d+\.\d+\.\d+")
BASIC_LATIN = re.compile(r"[\x20-\x7e]+")
NON_BASIC_LATIN = re.compile(r"[^\x20-\x7e]")
# The exact set eslint-plugin-obsidianmd's validate-manifest rule permits in a
# description — narrower than Basic Latin: no parentheses, colons, or ampersands.
DESCRIPTION_ALLOWED = re.compile(r"[A-Za-z0-9\s.,!?'\"-]")
ALLOWED_IN_NAME = re.compile(r"[a-zA-Z0-9 ()+\-]")

REQUIRED_STRING_FIELDS = ("id", "name", "version", "minAppVersion", "description", "author")
LICENSE_FILENAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt")

# Cover every extension a plugin's sources can use, not just .ts — the skill
# documents React and Svelte as supported, so .tsx and .svelte carry placeholders
# just as readily. Built output (.js/.mjs) is deliberately excluded: main.js is a
# bundle, and flagging it would echo a warning already raised against its source.
SOURCE_EXTENSIONS = (".ts", ".tsx", ".mts", ".cts", ".jsx", ".svelte")

# The same placeholders the linter's sample-names rule looks for. Word-bounded so
# a file holding only MyPluginSettings isn't also reported for MyPlugin — the
# message should name the identifiers actually present.
SAMPLE_PLACEHOLDERS = tuple(
    (identifier, re.compile(rf"\b{identifier}\b"))
    for identifier in ("MyPlugin", "MyPluginSettings", "SampleModal", "SampleSettingTab")
)


class Finding(NamedTuple):
    level: str  # "error" | "warn" | "ok"
    message: str


class Report:
    """Findings in discovery order, plus the trailing release reminder.

    Kept separate from printing so tests can assert on findings directly rather
    than parsing stdout.
    """

    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.reminder: str | None = None

    def error(self, message: str) -> None:
        self.findings.append(Finding("error", message))

    def warn(self, message: str) -> None:
        self.findings.append(Finding("warn", message))

    def ok(self, message: str) -> None:
        self.findings.append(Finding("ok", message))

    def count(self, level: str) -> int:
        return sum(1 for finding in self.findings if finding.level == level)

    def messages(self, level: str | None = None) -> list[str]:
        return [f.message for f in self.findings if level is None or f.level == level]


def _is_semver(value: object) -> bool:
    return isinstance(value, str) and SEMVER.fullmatch(value) is not None


def _distinct_characters(text: str) -> str:
    """Preserve first-seen order while dropping repeats, so an error names each
    offending character once."""
    return "".join(dict.fromkeys(text))


def _as_string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _check_manifest_fields(manifest: dict, root: Path, report: Report) -> str:
    """Field-level manifest rules. Returns manifest.version for the reminder."""
    for field in REQUIRED_STRING_FIELDS:
        value = manifest.get(field)
        if not isinstance(value, str) or not value:
            report.error(f"manifest.{field} is required and must be a non-empty string.")
    if not isinstance(manifest.get("isDesktopOnly"), bool):
        report.error(
            "manifest.isDesktopOnly is required and must be a boolean "
            "(true if any Node.js/Electron API is used)."
        )

    # Coerce to strings so a malformed (non-string) field is reported above without
    # raising in the checks below — a bad manifest should still get a full report.
    identifier = _as_string(manifest.get("id"))
    name = _as_string(manifest.get("name"))
    version = _as_string(manifest.get("version"))
    min_app_version = _as_string(manifest.get("minAppVersion"))
    description = _as_string(manifest.get("description"))

    if identifier:
        # Docs/Reference/Manifest: "The ID must contain only lowercase letters and
        # hyphens" — digits included. Some long-published plugins predate the rule.
        if not re.fullmatch(r"[a-z-]+", identifier):
            report.error(
                f'manifest.id "{identifier}" may only contain lowercase letters and hyphens '
                "(no digits, underscores, or capitals). Fix this before your first release — "
                "ids can't change afterward, so already-published plugins keep the id they "
                "shipped with."
            )
        if re.search(r"plugin$", identifier, re.IGNORECASE):
            report.error(f'manifest.id "{identifier}" must not end with "plugin".')
        if re.search(r"obsidian", identifier, re.IGNORECASE):
            report.error(f'manifest.id "{identifier}" must not contain "obsidian".')
        # The id-matches-folder rule governs the vault install dir
        # (<vault>/.obsidian/plugins/<id>), so only check it when root actually is
        # one — not when pointed at a git checkout.
        inside_vault_plugins_dir = root.parent.name == "plugins" and root.parent.parent.name == ".obsidian"
        if inside_vault_plugins_dir and root.name != identifier:
            report.warn(
                f'plugin folder "{root.name}" != manifest.id "{identifier}" — inside a vault '
                "the folder must match the id, or callbacks like onExternalSettingsChange "
                "won't fire."
            )

    if name:
        if re.search(r"obsidian|obsi-|-sidian", name, re.IGNORECASE):
            report.error(f'manifest.name "{name}" must not contain "Obsidian" or variations.')
        if re.search(r"\bplugins?\b", name, re.IGNORECASE):
            report.error(f'manifest.name "{name}" must not contain the word "Plugin".')
        if not BASIC_LATIN.fullmatch(name):
            report.error(
                f'manifest.name "{name}" must use Basic Latin characters only '
                "(no emoji or extended Unicode)."
            )
        # Judge punctuation on the Basic Latin subset: a non-Latin character is
        # already reported above, and counting it here too would call it
        # "punctuation". Both defects still surface on one run.
        disallowed = ALLOWED_IN_NAME.sub("", NON_BASIC_LATIN.sub("", name))
        if disallowed:
            report.error(
                f'manifest.name "{name}" contains disallowed punctuation '
                f'"{_distinct_characters(disallowed)}" — only hyphens, "+", and '
                "parentheses are allowed."
            )

    if version and not SEMVER.fullmatch(version):
        report.error(f'manifest.version "{version}" must be SemVer x.y.z with no "v" prefix.')
    if min_app_version and not SEMVER.fullmatch(min_app_version):
        report.warn(
            f'manifest.minAppVersion "{min_app_version}" doesn\'t look like an '
            "Obsidian version (x.y.z)."
        )

    if description:
        if len(description) > 250:
            report.error(f"manifest.description is {len(description)} chars — the maximum is 250.")
        if not description.endswith("."):
            report.error("manifest.description must end with a period.")
        if re.search(r"this is a plugin", description, re.IGNORECASE):
            report.error(
                'manifest.description must not say "This is a plugin…" — start with an '
                "action statement instead."
            )
        # Basic Latin is too permissive here — validate-manifest rejects parentheses,
        # colons, and ampersands, which read as perfectly ordinary in a description.
        disallowed = _distinct_characters(DESCRIPTION_ALLOWED.sub("", description))
        if disallowed:
            report.warn(
                "manifest.description contains characters the linter's validate-manifest "
                f'rule rejects ("{disallowed}") — allowed: letters, digits, whitespace, '
                "and . , ! ? ' \" -"
            )

    if "fundingUrl" in manifest:
        funding = manifest["fundingUrl"]
        is_url_string = isinstance(funding, str) and funding.startswith("https://")
        is_label_map = (
            isinstance(funding, dict)
            and len(funding) > 0
            and all(isinstance(url, str) and url.startswith("https://") for url in funding.values())
        )
        if not is_url_string and not is_label_map:
            report.error(
                "manifest.fundingUrl must be an https URL string or a non-empty object "
                "mapping labels to https URLs."
            )
        else:
            # Only worth asking about a well-formed value — advising "keep it only
            # if…" about one just rejected as malformed inverts the order of fixes.
            report.warn(
                "fundingUrl present — keep it only if it points at actual financial "
                "support; otherwise remove it (submission requirement)."
            )

    return version


def _check_versions_json(root: Path, version: str, min_app_version: str, report: Report) -> None:
    versions_path = root / "versions.json"
    if not versions_path.exists():
        report.warn(
            "versions.json not found at repo root — the sample plugin's version-bump.mjs "
            "maintains it; older Obsidian installs use it to find a compatible release."
        )
        return

    try:
        versions = json.loads(versions_path.read_text(encoding="utf-8"))
    except ValueError as parse_error:
        report.error(f"versions.json is not valid JSON: {parse_error}")
        return

    if not isinstance(versions, dict):
        report.error("versions.json must be an object mapping plugin version -> minAppVersion.")
        return

    for plugin_version, app_version in versions.items():
        if not SEMVER.fullmatch(plugin_version):
            report.error(f'versions.json key "{plugin_version}" is not SemVer x.y.z.')
        if not _is_semver(app_version):
            report.error(
                f'versions.json["{plugin_version}"] = "{app_version}" is not a valid minAppVersion.'
            )

    # The invariant version-bump.mjs maintains: versions[manifest.version] is the
    # minAppVersion that release shipped with. A stale entry silently sends older
    # installs to the wrong release, and nothing else checks for it.
    declared = versions.get(version)
    if version and isinstance(declared, str) and declared != min_app_version:
        report.error(
            f'versions.json["{version}"] is "{declared}" but manifest.minAppVersion is '
            f'"{min_app_version}" — they must agree, or Obsidian offers older installs '
            "the wrong release."
        )

    report.ok(
        f"versions.json parses ({len(versions)} entries). "
        "Only add an entry when minAppVersion changes."
    )


def _collect_source_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in SOURCE_EXTENSIONS
    )


def _check_release_readiness(root: Path, report: Report) -> None:
    if not any((root / filename).exists() for filename in LICENSE_FILENAMES):
        report.error("LICENSE file missing at repo root — required by the developer policies.")
    if not (root / "README.md").exists():
        report.error(
            "README.md missing at repo root — required for submission "
            "(and for network/account/payment disclosures)."
        )

    if (root / "main.js").exists():
        try:
            gitignore = (root / ".gitignore").read_text(encoding="utf-8")
        except OSError:
            gitignore = ""
        ignores_main_js = any(
            line.strip().lstrip("/") in ("main.js", "*.js") for line in gitignore.split("\n")
        )
        if not ignores_main_js:
            report.warn(
                "main.js exists at repo root and .gitignore does not ignore it — built "
                "output belongs in release assets, not the repo."
            )

    # Leftover sample-plugin code is an automatic review flag. Scan the repo root
    # (classic single-file layout, plus any siblings a split left there) and
    # everything under src/ (the current sample uses src/main.ts).
    root_sources = sorted(
        path for path in root.iterdir() if path.is_file() and path.suffix in SOURCE_EXTENSIONS
    )
    for path in root_sources + _collect_source_files(root / "src"):
        source = path.read_text(encoding="utf-8", errors="replace")
        leftovers = [name for name, pattern in SAMPLE_PLACEHOLDERS if pattern.search(source)]
        if leftovers:
            relative = path.relative_to(root).as_posix()
            report.warn(
                f"{relative} still contains sample-plugin placeholder names "
                f"({', '.join(leftovers)}) — rename before submitting."
            )


def validate(root: Path) -> Report:
    """Run every check against a plugin repo, returning findings in report order."""
    root = Path(root).resolve()
    report = Report()

    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        report.error(
            f"manifest.json not found at {manifest_path} — it must live at the repo root."
        )
        return report

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ValueError as parse_error:
        report.error(f"manifest.json is not valid JSON: {parse_error}")
        return report

    # Valid JSON isn't necessarily a manifest — `null`, an array, or a bare literal
    # all parse. Bail here so the field checks can't index a non-object.
    if not isinstance(manifest, dict):
        report.error("manifest.json must contain a JSON object mapping manifest fields to values.")
        return report

    version = _check_manifest_fields(manifest, root, report)
    if report.count("error") == 0:
        report.ok("manifest.json passes field rules.")

    _check_versions_json(root, version, _as_string(manifest.get("minAppVersion")), report)
    _check_release_readiness(root, report)

    styles = ", and styles.css" if (root / "styles.css").exists() else ""
    report.reminder = (
        f'Release reminder: the GitHub release tag must exactly match manifest.version ("{version}"), '
        f"with no \"v\" prefix, and attach main.js, manifest.json{styles}."
    )
    return report


def main(argv: list[str]) -> int:
    report = validate(Path(argv[1] if len(argv) > 1 else "."))
    for finding in report.findings:
        print(f"[{finding.level.upper()}] {finding.message}")
    if report.reminder:
        print(f"\n{report.reminder}")
    print(f"\n{report.count('error')} error(s), {report.count('warn')} warning(s).")
    return 1 if report.count("error") > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
