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
    write,
    write_json,
)


SCRIPT = ROOT / "scripts/check_version_bumps.py"


class VersionBumpGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One baseline fixture built once and copied per test — git init +
        # commit subprocesses dominate the cost otherwise.
        cls.template_directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.template_directory.cleanup)
        template = Path(cls.template_directory.name) / "repo"
        template.mkdir()
        initialize_git_repo(template)
        cls.write_manifest_at(template, version="0.1.0")
        write(template / "plugins/example/skills/demo/SKILL.md", "baseline body\n")
        write_json(template / "plugins/example/skills/demo/evals/evals.json", {"cases": []})
        commit_all(template, "baseline")
        cls.template = template

    def setUp(self):
        self.repo = fixture_directory(self) / "repo"
        shutil.copytree(self.template, self.repo)

    @staticmethod
    def write_manifest_at(repo, version, name="example"):
        write_json(
            repo / f"plugins/{name}/.claude-plugin/plugin.json",
            {"name": name, "version": version, "description": "Fixture plugin"},
        )

    def write_manifest(self, version, name="example"):
        self.write_manifest_at(self.repo, version, name)

    def write_skill(self, body, name="example"):
        write(self.repo / f"plugins/{name}/skills/demo/SKILL.md", body)

    def feature_branch(self):
        git(self.repo, "switch", "-c", "feature")

    def run_check(self, base="main"):
        return run([sys.executable, str(SCRIPT), base], self.repo, check=False)

    def test_content_change_without_bump_fails(self):
        self.feature_branch()
        self.write_skill("edited body\n")
        commit_all(self.repo, "edit skill")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("content changed, version still 0.1.0", result.stdout)

    def test_content_change_with_bump_passes(self):
        self.feature_branch()
        self.write_skill("edited body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "edit skill and bump")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("carries a fresh version", result.stdout)

    def test_absorbed_bump_fails(self):
        # Both branches bump 0.1.0 -> 0.2.0 independently. The merge is textually
        # clean, but the branch's content would ship under a version main already
        # published, so installs never receive it.
        self.feature_branch()
        self.write_skill("feature body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "feature edit and bump")
        git(self.repo, "switch", "main")
        self.write_skill("main body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "main edit and bump")
        git(self.repo, "switch", "feature")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("absorbed bump", result.stdout)

    def test_parallel_bump_to_a_different_version_passes(self):
        self.feature_branch()
        self.write_skill("feature body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "feature edit and bump")
        git(self.repo, "switch", "main")
        self.write_manifest(version="0.3.0")
        commit_all(self.repo, "main bumps elsewhere")
        git(self.repo, "switch", "feature")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_evals_only_change_needs_no_bump(self):
        # evals/ is stripped from vendored copies by the sync, so it never
        # reaches an install and owes no bump.
        self.feature_branch()
        write_json(
            self.repo / "plugins/example/skills/demo/evals/evals.json",
            {"cases": [{"prompt": "new case"}]},
        )
        commit_all(self.repo, "add an eval case")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_workspace_only_change_needs_no_bump(self):
        self.feature_branch()
        write(self.repo / "plugins/example/skills/demo-workspace/notes.md", "scratch\n")
        commit_all(self.repo, "workspace scratch")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_eval_change_alongside_content_still_requires_a_bump(self):
        self.feature_branch()
        self.write_skill("edited body\n")
        write_json(self.repo / "plugins/example/skills/demo/evals/evals.json", {"cases": [1]})
        commit_all(self.repo, "edit both")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_backwards_bump_fails(self):
        self.feature_branch()
        self.write_skill("edited body\n")
        self.write_manifest(version="0.0.9")
        commit_all(self.repo, "edit and un-bump")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("went backwards", result.stdout)

    def test_new_plugin_needs_no_bump(self):
        self.feature_branch()
        self.write_manifest_at(self.repo, version="0.1.0", name="fresh")
        write(self.repo / "plugins/fresh/skills/demo/SKILL.md", "new plugin\n")
        commit_all(self.repo, "add a plugin")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_removed_plugin_needs_no_bump(self):
        self.feature_branch()
        shutil.rmtree(self.repo / "plugins/example")
        commit_all(self.repo, "remove the plugin")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_plugin_change_is_clean(self):
        self.feature_branch()
        write(self.repo / "README.md", "docs only\n")
        commit_all(self.repo, "docs")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_malformed_manifest_is_error_not_a_pass(self):
        self.feature_branch()
        self.write_skill("edited body\n")
        (self.repo / "plugins/example/.claude-plugin/plugin.json").write_text(
            "[]\n", encoding="utf-8"
        )
        commit_all(self.repo, "malformed")
        result = self.run_check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("manifest must be a JSON object", result.stderr)

    def test_stale_local_base_does_not_hide_an_absorbed_bump(self):
        # A local `main` left behind at an older commit would compare against a
        # stale tip and call an absorbed version fresh. When origin/main is
        # further along, that is the base to use.
        baseline = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        self.feature_branch()
        self.write_skill("feature body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "feature edit and bump")
        git(self.repo, "switch", "main")
        self.write_skill("main body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "main edit and bump")
        advanced = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        git(self.repo, "update-ref", "refs/remotes/origin/main", advanced)
        git(self.repo, "switch", "feature")
        git(self.repo, "branch", "-f", "main", baseline)  # local main goes stale
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("absorbed bump", result.stdout)

    def test_local_base_ahead_of_origin_is_preferred(self):
        # The mirror case: unpushed commits on local main must not be discarded
        # in favour of a remote-tracking ref that trails them.
        baseline = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        git(self.repo, "update-ref", "refs/remotes/origin/main", baseline)
        git(self.repo, "switch", "-c", "feature")
        self.write_skill("feature body\n")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "feature edit and bump")
        git(self.repo, "switch", "main")
        self.write_manifest(version="0.2.0")
        commit_all(self.repo, "unpushed bump on main")
        git(self.repo, "switch", "feature")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("absorbed bump", result.stdout)

    def test_unresolvable_base_reports_a_skip_rather_than_a_clean_run(self):
        self.feature_branch()
        self.write_skill("edited body\n")
        commit_all(self.repo, "edit skill")
        result = self.run_check(base="not-a-branch")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIPPED", result.stdout)
        self.assertIn("Nothing was verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
