import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ROOT, commit_all, git, initialize_git_repo, write_json


SCRIPT = ROOT / (
    "plugins/cypherpoet-marketplace-kit/skills/"
    "marketplace-publish-check/scripts/needs_marketplace_publish.py"
)


class MarketplacePublishCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary_directory.name)
        initialize_git_repo(self.repo)
        self.write_manifest(version="0.1.0", description="Fixture plugin")
        self.write_dual_config(category="Developer Tools")
        commit_all(self.repo, "baseline")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_manifest(self, version, description):
        write_json(
            self.repo / "plugins/example/.claude-plugin/plugin.json",
            {
                "name": "example",
                "version": version,
                "description": description,
                "homepage": "https://example.com",
            },
        )

    def write_dual_config(self, category):
        write_json(
            self.repo / "scripts/dual-harness.json",
            {
                "vendored_skills": [],
                "dual_harness_plugins": {"example": {"category": category}},
                "claude_only_plugins": {},
            },
        )

    def run_check(self):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "main"],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

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
        self.write_dual_config(category="Design")
        commit_all(self.repo, "category")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed Codex category", result.stdout)

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
        (self.repo / "scripts/dual-harness.json").write_text("[]\n", encoding="utf-8")
        commit_all(self.repo, "malformed config")
        result = self.run_check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("dual-harness.json", result.stderr)

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
