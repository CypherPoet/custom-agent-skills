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

    def test_plugin_content_changes_carry_a_version_bump(self):
        # A plugin's version is each harness's update cache key, so content that
        # changed vs. the merge base must ship under a fresh one. Exits 0 (with a
        # SKIPPED notice) when there is no merge base to compare against.
        self.run_gate(sys.executable, "scripts/check_version_bumps.py")

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

    def test_skill_eval_inputs_are_portable(self):
        eval_paths = sorted(ROOT.glob("plugins/*/skills/*/evals/evals.json"))
        self.assertGreater(len(eval_paths), 0)
        for eval_path in eval_paths:
            skill_root = eval_path.parent.parent.resolve()
            data = json.loads(eval_path.read_text(encoding="utf-8"))
            for eval_case in data.get("evals", []):
                case_label = f"{eval_path}: eval {eval_case.get('id')}"
                prompt = eval_case.get("prompt", "")
                with self.subTest(case=case_label):
                    self.assertNotIn("{WS}", prompt)
                    self.assertNotIn("{OUTPUTS}", prompt)
                for relative_input in eval_case.get("files", []):
                    with self.subTest(case=case_label, input=relative_input):
                        self.assertFalse(os.path.isabs(relative_input))
                        input_path = (skill_root / relative_input).resolve()
                        self.assertTrue(input_path.is_relative_to(skill_root))
                        self.assertTrue(input_path.is_file())

    def test_plugin_manifests_have_required_identity_and_version(self):
        manifests = sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
        self.assertGreater(len(manifests), 0)
        for manifest_path in manifests:
            with self.subTest(path=manifest_path):
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(data.get("name"), manifest_path.parent.parent.name)
                self.assertTrue(data.get("description"))
                self.assertRegex(data.get("version", ""), r"^\d+\.\d+\.\d+$")

    def test_no_tracked_file_references_the_stale_generator_name(self):
        # The generator's old name (sync + _dual_harness) must not linger; nothing tracked
        # should still point at the old name. (The old dual-harness.json config
        # name is NOT guarded: legacy-fallback constants reference it on
        # purpose.) The needle is split so this file never matches itself.
        needle = "sync_dual" + "_harness"
        match = git(ROOT, "grep", "-l", "--fixed-strings", needle, check=False)
        self.assertEqual(match.returncode, 1, f"stale reference in:\n{match.stdout}")

    def test_no_tracked_file_instructs_bare_python_for_the_sync(self):
        # The sync must always be invoked as python3 (macOS ships no bare
        # `python`). Split the needle so this file never matches itself.
        needle = "python scripts/sync" + "_plugins.py"
        match = git(ROOT, "grep", "-l", "--fixed-strings", needle, check=False)
        self.assertEqual(match.returncode, 1, f"stale instruction in:\n{match.stdout}")


if __name__ == "__main__":
    unittest.main()
