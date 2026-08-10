import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from support import ROOT, commit_all, fixture_directory, git, initialize_git_repo, run, write_json


SCRIPT = ROOT / (
    "plugins/cypherpoet-marketplace-kit/skills/"
    "marketplace-publish-check/scripts/needs_marketplace_publish.py"
)


class MarketplacePublishCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.template_directory.cleanup)
        template = Path(cls.template_directory.name) / "repo"
        template.mkdir()
        initialize_git_repo(template)
        cls.write_claude_manifest_at(template)
        cls.write_codex_manifest_at(template)
        commit_all(template, "baseline")
        cls.template = template

    def setUp(self):
        self.repo = fixture_directory(self) / "repo"
        shutil.copytree(self.template, self.repo)

    @staticmethod
    def write_claude_manifest_at(
        repo,
        version="0.1.0",
        description="Fixture plugin",
        name="example",
    ):
        write_json(
            repo / "plugins/example/.claude-plugin/plugin.json",
            {
                "name": name,
                "version": version,
                "description": description,
                "homepage": "https://example.com",
            },
        )

    @staticmethod
    def write_codex_manifest_at(
        repo,
        version="0.1.0",
        category="Developer Tools",
        display_name="Example",
        name="example",
    ):
        write_json(
            repo / "plugins/example/.codex-plugin/plugin.json",
            {
                "name": name,
                "version": version,
                "description": "Fixture plugin",
                "interface": {
                    "displayName": display_name,
                    "category": category,
                },
            },
        )

    def run_check(self):
        return run([sys.executable, str(SCRIPT), "main"], self.repo, check=False)

    def feature_branch(self):
        git(self.repo, "switch", "-c", "feature")

    def test_version_only_change_needs_no_publish(self):
        self.feature_branch()
        self.write_claude_manifest_at(self.repo, version="0.1.1")
        self.write_codex_manifest_at(self.repo, version="0.1.1")
        commit_all(self.repo, "version")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)

    def test_claude_description_change_needs_publish(self):
        self.feature_branch()
        self.write_claude_manifest_at(self.repo, description="Changed description")
        commit_all(self.repo, "description")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed Claude description", result.stdout)

    def test_codex_category_change_needs_publish(self):
        self.feature_branch()
        self.write_codex_manifest_at(self.repo, category="Creativity")
        commit_all(self.repo, "category")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed Codex category", result.stdout)

    def test_other_codex_interface_changes_need_no_publish(self):
        self.feature_branch()
        self.write_codex_manifest_at(self.repo, display_name="Example Tools")
        commit_all(self.repo, "interface")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)

    def write_historical_codex_baseline(
        self,
        category,
        registry_path="scripts/plugin-registry.json",
    ):
        path = self.repo / "plugins/example/.codex-plugin/plugin.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        del manifest["interface"]
        write_json(path, manifest)
        write_json(
            self.repo / registry_path,
            {
                "dual_harness_plugins": {
                    "example": {"category": category},
                },
                "claude_only_plugins": {},
            },
        )
        commit_all(self.repo, "historical Codex metadata")
        self.feature_branch()

    def test_moving_an_unchanged_category_out_of_the_historical_registry_needs_no_publish(self):
        self.write_historical_codex_baseline("Developer Tools")
        self.write_codex_manifest_at(self.repo, category="Developer Tools")
        commit_all(self.repo, "author Codex interface")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)

    def test_historical_registry_category_change_needs_publish(self):
        self.write_historical_codex_baseline("Design")
        self.write_codex_manifest_at(self.repo, category="Creativity")
        commit_all(self.repo, "author supported Codex category")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("changed Codex category", result.stdout)

    def test_legacy_dual_harness_registry_category_is_supported(self):
        self.write_historical_codex_baseline(
            "Developer Tools",
            registry_path="scripts/dual-harness.json",
        )
        self.write_codex_manifest_at(self.repo, category="Developer Tools")
        commit_all(self.repo, "author Codex interface")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)

    def test_added_and_removed_codex_support_need_publish(self):
        self.feature_branch()
        path = self.repo / "plugins/example/.codex-plugin/plugin.json"
        path.unlink()
        commit_all(self.repo, "remove Codex support")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("left the Codex catalog surface", result.stdout)

        self.write_codex_manifest_at(self.repo)
        commit_all(self.repo, "restore Codex support")
        git(self.repo, "switch", "-c", "add-codex", "main")
        path.unlink()
        commit_all(self.repo, "Claude-only baseline")
        git(self.repo, "switch", "-c", "feature-add")
        self.write_codex_manifest_at(self.repo)
        commit_all(self.repo, "add Codex support")
        result = run([sys.executable, str(SCRIPT), "add-codex"], self.repo, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("added to the Codex catalog surface", result.stdout)

    def test_malformed_manifests_are_errors(self):
        for relative_path in [
            "plugins/example/.claude-plugin/plugin.json",
            "plugins/example/.codex-plugin/plugin.json",
        ]:
            with self.subTest(relative_path):
                repo = fixture_directory(self) / "malformed"
                shutil.copytree(self.template, repo)
                git(repo, "switch", "-c", "feature")
                (repo / relative_path).write_text("[]\n", encoding="utf-8")
                commit_all(repo, "malformed")
                result = run([sys.executable, str(SCRIPT), "main"], repo, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn("manifest must be a JSON object", result.stderr)

    def test_plugin_rename_is_detected_as_remove_and_add_for_both_platforms(self):
        self.feature_branch()
        source = self.repo / "plugins/example"
        target = self.repo / "plugins/renamed"
        source.rename(target)
        for manifest in [
            target / ".claude-plugin/plugin.json",
            target / ".codex-plugin/plugin.json",
        ]:
            data = json.loads(manifest.read_text())
            data["name"] = "renamed"
            write_json(manifest, data)
        commit_all(self.repo, "rename")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("example", result.stdout)
        self.assertIn("renamed", result.stdout)

    def test_merge_base_does_not_blame_feature_for_later_base_change(self):
        self.feature_branch()
        git(self.repo, "switch", "main")
        self.write_claude_manifest_at(self.repo, description="Changed on main")
        commit_all(self.repo, "main moves")
        git(self.repo, "switch", "feature")
        self.write_claude_manifest_at(self.repo, version="0.1.1")
        commit_all(self.repo, "feature version")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)


if __name__ == "__main__":
    unittest.main()
