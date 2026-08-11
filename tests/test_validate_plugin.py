"""Behavioral tests for the obsidian-plugin-crafting preflight validator.

Every case here is an input that a defect actually escaped through: the checks
this script performs were each added because a malformed plugin passed silently.
Adding a row when a rule changes keeps the coverage gaps visible as missing
cases rather than invisible.
"""

import unittest

from support import fixture_directory, load_module, write, write_json


validate_plugin = load_module(
    "validate_plugin",
    "plugins/obsidian-plugin-kit/skills/obsidian-plugin-crafting/scripts/validate_plugin.py",
)


VALID_MANIFEST = {
    "id": "note-sync",
    "name": "Note Sync",
    "version": "1.0.0",
    "minAppVersion": "1.5.0",
    "description": "Syncs notes between vaults.",
    "author": "A Developer",
    "isDesktopOnly": False,
}


class ValidatePluginTests(unittest.TestCase):
    def setUp(self):
        self.root = fixture_directory(self)

    def build(self, manifest=VALID_MANIFEST, *, license_name="LICENSE", readme=True):
        """A submission-ready plugin, minus whatever the case removes."""
        if manifest is not None:
            write_json(self.root / "manifest.json", manifest)
        if license_name:
            write(self.root / license_name, "MIT\n")
        if readme:
            write(self.root / "README.md", "# Note Sync\n")
        return validate_plugin.validate(self.root)

    def manifest(self, **overrides):
        return {**VALID_MANIFEST, **overrides}

    def assertNoFindings(self, report, level):
        self.assertEqual(report.messages(level), [], f"unexpected {level}(s)")

    def assertFinding(self, report, level, fragment):
        matches = [m for m in report.messages(level) if fragment in m]
        self.assertTrue(
            matches,
            f"expected a {level} containing {fragment!r}; got {report.messages(level)}",
        )

    def assertNoFinding(self, report, level, fragment):
        matches = [m for m in report.messages(level) if fragment in m]
        self.assertFalse(matches, f"unexpected {level}: {matches}")

    # ---------- baseline ----------

    def test_submission_ready_plugin_is_clean(self):
        self.build()
        write(self.root / "src/main.ts", "export default class NoteSync {}\n")
        write_json(self.root / "versions.json", {"1.0.0": "1.5.0"})
        report = validate_plugin.validate(self.root)
        self.assertNoFindings(report, "error")
        self.assertNoFindings(report, "warn")

    # ---------- manifest shape ----------

    def test_missing_manifest_reports_instead_of_raising(self):
        report = self.build(manifest=None)
        self.assertFinding(report, "error", "manifest.json not found")

    def test_manifest_of_null_reports_instead_of_raising(self):
        write(self.root / "manifest.json", "null")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "error", "must contain a JSON object")

    def test_manifest_of_array_reports_instead_of_raising(self):
        write(self.root / "manifest.json", "[]")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "error", "must contain a JSON object")

    def test_malformed_json_is_reported(self):
        write(self.root / "manifest.json", "{ not json")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "error", "not valid JSON")

    def test_missing_required_field_is_reported(self):
        manifest = self.manifest()
        del manifest["author"]
        report = self.build(manifest)
        self.assertFinding(report, "error", "manifest.author is required")

    def test_missing_is_desktop_only_is_reported(self):
        manifest = self.manifest()
        del manifest["isDesktopOnly"]
        report = self.build(manifest)
        self.assertFinding(report, "error", "manifest.isDesktopOnly is required")

    # ---------- id ----------

    def test_id_with_digits_is_rejected(self):
        report = self.build(self.manifest(id="note-sync-2"))
        self.assertFinding(report, "error", "only contain lowercase letters and hyphens")

    def test_id_ending_in_plugin_is_rejected(self):
        report = self.build(self.manifest(id="note-sync-plugin"))
        self.assertFinding(report, "error", 'must not end with "plugin"')

    def test_id_containing_obsidian_is_rejected(self):
        report = self.build(self.manifest(id="obsidian-note-sync"))
        self.assertFinding(report, "error", 'must not contain "obsidian"')

    # ---------- name ----------

    def test_name_reports_accent_and_punctuation_independently(self):
        report = self.build(self.manifest(name="Café Sync!"))
        self.assertFinding(report, "error", "Basic Latin characters only")
        self.assertFinding(report, "error", 'disallowed punctuation "!"')

    def test_ascii_name_still_reports_punctuation(self):
        report = self.build(self.manifest(name="Note@Sync"))
        self.assertFinding(report, "error", 'disallowed punctuation "@"')

    def test_name_containing_plugin_is_rejected(self):
        report = self.build(self.manifest(name="Note Sync Plugin"))
        self.assertFinding(report, "error", 'must not contain the word "Plugin"')

    def test_parentheses_and_hyphens_are_allowed_in_a_name(self):
        report = self.build(self.manifest(name="Note Sync (beta) - v2"))
        self.assertNoFinding(report, "error", "disallowed punctuation")

    # ---------- description ----------

    def test_description_flags_characters_the_linter_rejects(self):
        report = self.build(self.manifest(description="Sync notes (fast): tags & links."))
        self.assertFinding(report, "warn", '("():&")')

    def test_ordinary_description_is_not_flagged(self):
        report = self.build(self.manifest(description="Syncs notes, links, and tags."))
        self.assertNoFinding(report, "warn", "validate-manifest")

    def test_overlong_description_is_rejected(self):
        report = self.build(self.manifest(description="a" * 251 + "."))
        self.assertFinding(report, "error", "the maximum is 250")

    def test_description_without_period_is_rejected(self):
        report = self.build(self.manifest(description="Syncs notes between vaults"))
        self.assertFinding(report, "error", "must end with a period")

    def test_this_is_a_plugin_opener_is_rejected(self):
        report = self.build(self.manifest(description="This is a plugin that syncs notes."))
        self.assertFinding(report, "error", "action statement")

    # ---------- fundingUrl ----------

    def test_valid_funding_url_draws_only_the_advisory(self):
        report = self.build(self.manifest(fundingUrl="https://ko-fi.com/dev"))
        self.assertNoFinding(report, "error", "fundingUrl")
        self.assertFinding(report, "warn", "keep it only if")

    def test_malformed_funding_url_errors_without_the_advisory(self):
        report = self.build(self.manifest(fundingUrl="http://insecure.example"))
        self.assertFinding(report, "error", "must be an https URL string")
        self.assertNoFinding(report, "warn", "keep it only if")

    # ---------- versions.json ----------

    def test_versions_entry_disagreeing_with_min_app_version_is_rejected(self):
        self.build()
        write_json(self.root / "versions.json", {"1.0.0": "9.9.9"})
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "error", "they must agree")

    def test_versions_without_an_entry_for_this_version_is_accepted(self):
        self.build(self.manifest(version="2.0.0"))
        write_json(self.root / "versions.json", {"1.0.0": "1.4.0"})
        report = validate_plugin.validate(self.root)
        self.assertNoFinding(report, "error", "they must agree")

    def test_missing_versions_json_warns(self):
        report = self.build()
        self.assertFinding(report, "warn", "versions.json not found")

    # ---------- release readiness ----------

    def test_license_txt_is_accepted(self):
        report = self.build(license_name="LICENSE.txt")
        self.assertNoFinding(report, "error", "LICENSE file missing")

    def test_missing_license_is_rejected(self):
        report = self.build(license_name=None)
        self.assertFinding(report, "error", "LICENSE file missing")

    def test_missing_readme_is_rejected(self):
        report = self.build(readme=False)
        self.assertFinding(report, "error", "README.md missing")

    def test_committed_main_js_without_gitignore_entry_warns(self):
        self.build()
        write(self.root / "main.js", "// bundle\n")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "warn", "built output belongs in release assets")

    def test_gitignored_main_js_is_accepted(self):
        self.build()
        write(self.root / "main.js", "// bundle\n")
        write(self.root / ".gitignore", "node_modules\nmain.js\n")
        report = validate_plugin.validate(self.root)
        self.assertNoFinding(report, "warn", "built output belongs")

    # ---------- sample-code placeholders ----------

    def test_placeholders_are_found_in_tsx_sources(self):
        self.build()
        write(self.root / "src/view.tsx", "export class SampleModal {}\n")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "warn", "src/view.tsx")
        self.assertFinding(report, "warn", "SampleModal")

    def test_placeholders_are_found_in_svelte_sources(self):
        self.build()
        write(self.root / "src/Panel.svelte", "export class SampleSettingTab {}\n")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "warn", "src/Panel.svelte")

    def test_placeholders_are_found_in_root_siblings_of_main_ts(self):
        self.build()
        write(self.root / "main.ts", "import './settings';\n")
        write(self.root / "settings.ts", "export interface MyPluginSettings {}\n")
        report = validate_plugin.validate(self.root)
        self.assertFinding(report, "warn", "settings.ts")
        self.assertFinding(report, "warn", "MyPluginSettings")

    def test_placeholder_report_names_only_identifiers_present(self):
        self.build()
        write(self.root / "src/settings.ts", "export interface MyPluginSettings {}\n")
        report = validate_plugin.validate(self.root)
        # MyPlugin is a substring of MyPluginSettings but not a distinct identifier here.
        placeholder_warning = next(m for m in report.messages("warn") if "settings.ts" in m)
        self.assertIn("MyPluginSettings", placeholder_warning)
        self.assertNotIn("(MyPlugin,", placeholder_warning)

    def test_renamed_sources_produce_no_placeholder_warning(self):
        self.build()
        write(self.root / "src/main.ts", "export default class NoteSync {}\n")
        report = validate_plugin.validate(self.root)
        self.assertNoFinding(report, "warn", "placeholder")

    def test_built_output_is_not_scanned_for_placeholders(self):
        self.build()
        write(self.root / ".gitignore", "main.js\n")
        write(self.root / "main.js", "class MyPlugin {}\n")
        report = validate_plugin.validate(self.root)
        self.assertNoFinding(report, "warn", "placeholder")


if __name__ == "__main__":
    unittest.main()
