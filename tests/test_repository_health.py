import json
import os
import subprocess
import sys
import unittest

from support import ROOT


class RepositoryHealthTests(unittest.TestCase):
    def run_gate(self, *command):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=environment,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"{' '.join(command)} failed:\n{result.stdout}\n{result.stderr}",
        )
        return result

    def test_dual_harness_artifacts_are_current(self):
        self.run_gate(sys.executable, "scripts/sync_dual_harness.py", "--check")

    def test_skill_structure_has_no_errors_or_advisories(self):
        result = self.run_gate(
            sys.executable,
            ".claude/skills/skill-structure-check/scripts/check-skill-structure.py",
        )
        self.assertIn("OK —", result.stdout)
        self.assertNotIn("ADVISORY", result.stdout)

    def test_local_catalog_is_current(self):
        self.run_gate(
            sys.executable,
            "plugins/cypherpoet-marketplace-kit/skills/catalog-refresh/"
            "scripts/refresh_catalog.py",
            "--check",
        )

    def test_every_tracked_json_file_parses(self):
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
                "*.json",
            ],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        paths = [path for path in result.stdout.decode().split("\0") if path]
        self.assertGreater(len(paths), 0)
        for relative_path in paths:
            with self.subTest(path=relative_path):
                json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def test_plugin_manifests_have_required_identity_and_version(self):
        manifests = sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
        self.assertGreater(len(manifests), 0)
        for manifest_path in manifests:
            with self.subTest(path=manifest_path):
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("name"), manifest_path.parent.parent.name)
                self.assertTrue(data.get("description"))
                self.assertRegex(data.get("version", ""), r"^\d+\.\d+\.\d+$")

    def test_regeneration_docs_use_python3(self):
        for relative_path in ("AGENTS.md", "docs/PLUGIN-CONVENTIONS.md"):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(path=relative_path):
                self.assertIn("python3 scripts/sync_dual_harness.py", text)
                self.assertNotIn("python scripts/sync_dual_harness.py", text)

    def test_checker_contract_lives_in_skill_not_script_comment(self):
        script = (
            ROOT
            / ".claude/skills/skill-structure-check/scripts/check-skill-structure.py"
        ).read_text(encoding="utf-8")
        skill = (
            ROOT / ".claude/skills/skill-structure-check/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn('"""Implement the canonical rule contract in ../SKILL.md."""', script)
        for phrase in (
            "cross-plugin",
            "dual-harness drift",
            "fact-check manifest drift",
            "ownership marker",
            "## Contents",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)


if __name__ == "__main__":
    unittest.main()
