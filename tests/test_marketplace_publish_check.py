import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from support import (
    ROOT,
    commit_all,
    fixture_directory,
    git,
    initialize_git_repo,
    run,
    write_json,
)


SCRIPT = ROOT / (
    "plugins/cypherpoet-marketplace-kit/skills/"
    "marketplace-publish-check/scripts/needs_marketplace_publish.py"
)


class MarketplacePublishCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The baseline fixture repo is identical for every test; build it once
        # and copy it per test — git init + config + commit subprocesses were
        # the dominant cost of the whole suite.
        cls.template_directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.template_directory.cleanup)
        template = Path(cls.template_directory.name) / "repo"
        template.mkdir()
        initialize_git_repo(template)
        cls.write_manifest_at(template, version="0.1.0", description="Fixture plugin")
        cls.write_dual_config_at(template, category="Developer Tools")
        commit_all(template, "baseline")
        cls.template = template

    def setUp(self):
        self.repo = fixture_directory(self) / "repo"
        shutil.copytree(self.template, self.repo)

    @staticmethod
    def write_manifest_at(repo, version, description):
        write_json(
            repo / "plugins/example/.claude-plugin/plugin.json",
            {
                "name": "example",
                "version": version,
                "description": description,
                "homepage": "https://example.com",
            },
        )

    @staticmethod
    def write_dual_config_at(
        repo,
        category,
        display_name="Example",
    ):
        write_json(
            repo / "scripts/plugin-registry.json",
            {
                "vendored_skills": [],
                "dual_harness_plugins": {
                    "example": {
                        "category": category,
                        "interface": {
                            "displayName": display_name,
                            "shortDescription": "Use the example plugin",
                            "capabilities": ["Read", "Write"],
                            "defaultPrompt": ["Use the example plugin for this task."],
                        },
                    }
                },
                "claude_only_plugins": {},
            },
        )

    def write_manifest(self, version, description):
        self.write_manifest_at(self.repo, version, description)

    def write_dual_config(
        self,
        category,
        display_name="Example",
    ):
        self.write_dual_config_at(
            self.repo,
            category,
            display_name,
        )

    def run_check(self):
        return run([sys.executable, str(SCRIPT), "main"], self.repo, check=False)

    def feature_branch(self):
        git(self.repo, "switch", "-c", "feature")

    def test_version_only_change_needs_no_publish(self):
        self.feature_branch()
        self.write_manifest(version="0.1.1", description="Fixture plugin")
        commit_all(self.repo, "version")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)

    def test_description_change_needs_publish(self):
        self.feature_branch()
        self.write_manifest(version="0.1.1", description="Changed description")
        commit_all(self.repo, "description")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed description", result.stdout)

    def test_codex_category_change_needs_publish(self):
        self.feature_branch()
        self.write_dual_config(category="Creativity")
        commit_all(self.repo, "category")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed Codex category", result.stdout)

    def test_codex_interface_change_needs_no_publish(self):
        self.feature_branch()
        self.write_dual_config(category="Developer Tools", display_name="Example Tools")
        commit_all(self.repo, "interface")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)

    def test_malformed_manifest_is_error_not_publish_signal(self):
        self.feature_branch()
        path = self.repo / "plugins/example/.claude-plugin/plugin.json"
        path.write_text("[]\n", encoding="utf-8")
        commit_all(self.repo, "malformed")
        result = self.run_check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("manifest must be a JSON object", result.stderr)

    def test_malformed_dual_harness_config_is_error_not_removal(self):
        self.feature_branch()
        (self.repo / "scripts/plugin-registry.json").write_text("[]\n", encoding="utf-8")
        commit_all(self.repo, "malformed config")
        result = self.run_check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("plugin-registry.json", result.stderr)

    def test_plugin_rename_is_detected_as_remove_and_add(self):
        self.feature_branch()
        source = self.repo / "plugins/example"
        target = self.repo / "plugins/renamed"
        source.rename(target)
        manifest = target / ".claude-plugin/plugin.json"
        data = json.loads(manifest.read_text())
        data["name"] = "renamed"
        write_json(manifest, data)
        commit_all(self.repo, "rename")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("example", result.stdout)
        self.assertIn("renamed", result.stdout)

    def test_registry_rename_boundary_reads_legacy_name_at_base(self):
        # A base ref that predates the plugin-registry.json rename still has
        # scripts/dual-harness.json; category comparison must read it there.
        repo = fixture_directory(self) / "legacy"
        repo.mkdir()
        initialize_git_repo(repo)
        self.write_manifest_at(repo, version="0.1.0", description="Fixture plugin")
        legacy = repo / "scripts/dual-harness.json"
        registry = repo / "scripts/plugin-registry.json"
        self.write_dual_config_at(repo, category="Developer Tools")
        registry.rename(legacy)
        commit_all(repo, "pre-rename baseline")
        git(repo, "switch", "-c", "feature")
        legacy.unlink()
        self.write_dual_config_at(repo, category="Creativity")
        commit_all(repo, "rename registry and change category")
        result = run([sys.executable, str(SCRIPT), "main"], repo, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("changed Codex category", result.stdout)

    def test_merge_base_does_not_blame_feature_for_later_base_change(self):
        self.feature_branch()
        git(self.repo, "switch", "main")
        self.write_manifest(version="0.1.0", description="Changed on main")
        commit_all(self.repo, "main moves")
        git(self.repo, "switch", "feature")
        self.write_manifest(version="0.1.1", description="Fixture plugin")
        commit_all(self.repo, "feature version")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No publish needed", result.stdout)


if __name__ == "__main__":
    unittest.main()
