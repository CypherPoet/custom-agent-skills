import json
import shutil
import unittest

from support import (
    commit_all,
    fixture_directory,
    initialize_git_repo,
    load_module,
    write,
    write_dual_harness_config,
    write_plugin_manifest,
)


sync_dual_harness = load_module(
    "sync_dual_harness",
    "scripts/sync_dual_harness.py",
)


class SyncDualHarnessTests(unittest.TestCase):
    def setUp(self):
        self.root = fixture_directory(self)
        self.make_plugin("source")
        self.make_plugin("bundle")
        write(
            self.root / "plugins/source/skills/shared/SKILL.md",
            "---\nname: shared\ndescription: Shared fixture.\n---\n",
        )
        self.write_config(
            vendored_skills=[
                {
                    "source": "plugins/source/skills/shared",
                    "targets": ["plugins/bundle/skills/shared"],
                }
            ],
            plugins=("source", "bundle"),
        )

    def make_plugin(self, name, version="0.1.0"):
        write_plugin_manifest(
            self.root,
            name,
            version=version,
            description=f"{name} fixture",
            author={"name": "Test"},
        )

    def write_config(self, vendored_skills, plugins):
        write_dual_harness_config(
            self.root,
            vendored_skills,
            {name: {"category": "Test"} for name in plugins},
        )

    def state_path(self):
        return self.root / "scripts/dual-harness-state.json"

    def state_entries(self):
        return json.loads(self.state_path().read_text())["vendored"]

    def test_write_creates_copy_state_and_codex_manifests(self):
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertEqual(
            (self.root / "plugins/bundle/skills/shared/SKILL.md").read_text(),
            (self.root / "plugins/source/skills/shared/SKILL.md").read_text(),
        )
        entry = self.state_entries()["plugins/bundle/skills/shared"]
        self.assertEqual(entry["source"], "plugins/source/skills/shared")
        self.assertEqual(len(entry["tree_sha256"]), 64)
        self.assertEqual(sync_dual_harness.sync(self.root, write=False), [])

    def test_missing_state_file_is_drift_and_write_repairs_it(self):
        sync_dual_harness.sync(self.root, write=True)
        self.state_path().unlink()
        problems = sync_dual_harness.sync(self.root, write=False)
        self.assertTrue(any("state file out of sync" in problem for problem in problems))
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertTrue(self.state_path().is_file())

    def test_removed_edge_deletes_proven_generated_copy(self):
        sync_dual_harness.sync(self.root, write=True)
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        problems = sync_dual_harness.sync(self.root, write=False)
        self.assertTrue(any("stale generated copy" in problem for problem in problems))
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertFalse((self.root / "plugins/bundle/skills/shared").exists())
        self.assertFalse(self.state_path().exists())
        self.assertEqual(sync_dual_harness.sync(self.root, write=False), [])

    def test_removed_edge_preserves_locally_changed_copy(self):
        sync_dual_harness.sync(self.root, write=True)
        write(
            self.root / "plugins/bundle/skills/shared/SKILL.md",
            "---\nname: shared\ndescription: Locally authored now.\n---\n",
        )
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("refusing to remove" in problem for problem in problems))
        self.assertTrue((self.root / "plugins/bundle/skills/shared/SKILL.md").is_file())
        self.assertIn("plugins/bundle/skills/shared", self.state_entries())

    def test_removed_edge_preserves_ignored_local_content(self):
        # evals/ and *-workspace/ are excluded from vendoring, but they are
        # still local content: retiring an edge must not silently delete them.
        sync_dual_harness.sync(self.root, write=True)
        write(
            self.root / "plugins/bundle/skills/shared/evals/evals.json",
            '{"cases": []}\n',
        )
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("refusing to remove" in problem for problem in problems))
        self.assertTrue(
            (self.root / "plugins/bundle/skills/shared/evals/evals.json").is_file()
        )

    def test_stale_state_entry_without_copy_is_cleaned(self):
        sync_dual_harness.sync(self.root, write=True)
        shutil.rmtree(self.root / "plugins/bundle/skills/shared")
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertFalse(self.state_path().exists())

    def test_malformed_state_file_is_fatal_and_non_destructive(self):
        sync_dual_harness.sync(self.root, write=True)
        self.state_path().write_text("not json\n", encoding="utf-8")
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("malformed state file" in problem for problem in problems))
        self.assertTrue((self.root / "plugins/bundle/skills/shared/SKILL.md").is_file())
        self.assertEqual(self.state_path().read_text(), "not json\n")

    def test_unmarked_authored_skill_is_never_inferred_as_generated(self):
        sync_dual_harness.sync(self.root, write=True)
        self.make_plugin("authored")
        write(
            self.root / "plugins/authored/skills/shared/SKILL.md",
            (self.root / "plugins/source/skills/shared/SKILL.md").read_text(),
        )
        self.write_config(
            vendored_skills=[
                {
                    "source": "plugins/source/skills/shared",
                    "targets": ["plugins/bundle/skills/shared"],
                }
            ],
            plugins=("source", "bundle", "authored"),
        )
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertTrue((self.root / "plugins/authored/skills/shared/SKILL.md").is_file())

    def test_gitignored_files_are_not_vendored_or_digested(self):
        # A gitignored machine-local file must not reach the copy or the
        # recorded digest — otherwise a clean checkout (CI) reports phantom
        # state drift that the dirty machine can neither see nor regenerate.
        initialize_git_repo(self.root)
        write(self.root / ".gitignore", "*.log\n")
        commit_all(self.root)
        write(self.root / "plugins/source/skills/shared/debug.log", "local junk\n")
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertFalse(
            (self.root / "plugins/bundle/skills/shared/debug.log").exists()
        )
        (self.root / "plugins/source/skills/shared/debug.log").unlink()
        self.assertEqual(sync_dual_harness.sync(self.root, write=False), [])

    def test_duplicate_target_is_rejected_before_vendoring(self):
        self.make_plugin("other")
        write(
            self.root / "plugins/other/skills/other/SKILL.md",
            "---\nname: other\ndescription: Other fixture.\n---\n",
        )
        self.write_config(
            vendored_skills=[
                {
                    "source": "plugins/source/skills/shared",
                    "targets": ["plugins/bundle/skills/shared"],
                },
                {
                    "source": "plugins/other/skills/other",
                    "targets": ["plugins/bundle/skills/shared"],
                },
            ],
            plugins=("source", "bundle", "other"),
        )
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("duplicate target" in problem for problem in problems))
        self.assertFalse(self.state_path().exists())

    def test_vendoring_chain_is_rejected(self):
        self.make_plugin("downstream")
        self.write_config(
            vendored_skills=[
                {
                    "source": "plugins/source/skills/shared",
                    "targets": ["plugins/bundle/skills/shared"],
                },
                {
                    "source": "plugins/bundle/skills/shared",
                    "targets": ["plugins/downstream/skills/shared"],
                },
            ],
            plugins=("source", "bundle", "downstream"),
        )
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("vendoring chains are not allowed" in problem for problem in problems))

    def test_custom_claude_components_block_codex_manifest(self):
        manifest = json.loads(
            (self.root / "plugins/source/.claude-plugin/plugin.json").read_text()
        )
        manifest["agents"] = "./agents/"
        write_plugin_manifest(self.root, "source", **{k: v for k, v in manifest.items() if k != "name"})
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("Claude-only components" in problem for problem in problems))
        self.assertFalse((self.root / "plugins/source/.codex-plugin/plugin.json").exists())


if __name__ == "__main__":
    unittest.main()
