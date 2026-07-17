import json
import os
import subprocess
import sys
import unittest

from support import ROOT, git


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

    def test_skill_structure_is_clean_in_strict_mode(self):
        # --strict fails on warnings and advisories too; the dual-harness sync
        # check runs inside this gate, so drift also fails here.
        self.run_gate(
            sys.executable,
            ".claude/skills/skill-structure-check/scripts/check-skill-structure.py",
            "--strict",
        )

    def test_local_catalog_is_current(self):
        self.run_gate(
            sys.executable,
            "plugins/cypherpoet-marketplace-kit/skills/catalog-refresh/"
            "scripts/refresh_catalog.py",
            "--check",
        )

    def test_every_tracked_json_file_parses(self):
        listing = git(ROOT, "ls-files", "--cached", "-z", "--", "*.json")
        paths = [path for path in listing.stdout.split("\0") if path]
        self.assertGreater(len(paths), 0)
        for relative_path in paths:
            full_path = ROOT / relative_path
            if not full_path.is_file():  # staged deletes stay listed by --cached
                continue
            with self.subTest(path=relative_path):
                json.loads(full_path.read_text(encoding="utf-8"))

    def test_plugin_manifests_have_required_identity_and_version(self):
        manifests = sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
        self.assertGreater(len(manifests), 0)
        for manifest_path in manifests:
            with self.subTest(path=manifest_path):
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("name"), manifest_path.parent.parent.name)
                self.assertTrue(data.get("description"))
                self.assertRegex(data.get("version", ""), r"^\d+\.\d+\.\d+$")

    def test_no_tracked_file_instructs_bare_python_for_the_sync(self):
        # The sync must always be invoked as python3 (macOS ships no bare
        # `python`). Split the needle so this file never matches itself.
        needle = "python scripts/sync_dual" + "_harness.py"
        match = git(ROOT, "grep", "-l", "--fixed-strings", needle, check=False)
        self.assertEqual(match.returncode, 1, f"stale instruction in:\n{match.stdout}")


if __name__ == "__main__":
    unittest.main()
