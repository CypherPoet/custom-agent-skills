import json
import shutil
import tempfile
import unittest
from pathlib import Path

from support import load_module, write, write_json


sync_dual_harness = load_module(
    "sync_dual_harness",
    "scripts/sync_dual_harness.py",
)


class SyncDualHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.make_plugin("source", "0.1.0")
        self.make_plugin("bundle", "0.1.0")
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
            dual_plugins={"source": {"category": "Test"}, "bundle": {"category": "Test"}},
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def make_plugin(self, name, version):
        write_json(
            self.root / f"plugins/{name}/.claude-plugin/plugin.json",
            {
                "name": name,
                "version": version,
                "description": f"{name} fixture",
                "author": {"name": "Test"},
            },
        )

    def write_config(self, vendored_skills, dual_plugins, claude_only=None):
        write_json(
            self.root / "scripts/dual-harness.json",
            {
                "vendored_skills": vendored_skills,
                "dual_harness_plugins": dual_plugins,
                "claude_only_plugins": claude_only or {},
            },
        )

    def marker(self):
        return self.root / "plugins/bundle/skills/.shared.dual-harness-vendor.json"

    def test_write_creates_copy_marker_and_codex_manifests(self):
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertEqual(
            (self.root / "plugins/bundle/skills/shared/SKILL.md").read_text(),
            (self.root / "plugins/source/skills/shared/SKILL.md").read_text(),
        )
        marker = json.loads(self.marker().read_text())
        self.assertEqual(marker["source"], "plugins/source/skills/shared")
        self.assertEqual(marker["target"], "plugins/bundle/skills/shared")
        self.assertEqual(len(marker["tree_sha256"]), 64)
        self.assertEqual(sync_dual_harness.sync(self.root, write=False), [])

    def test_missing_marker_is_drift_and_write_repairs_it(self):
        sync_dual_harness.sync(self.root, write=True)
        self.marker().unlink()
        problems = sync_dual_harness.sync(self.root, write=False)
        self.assertTrue(any("ownership marker out of sync" in problem for problem in problems))
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertTrue(self.marker().is_file())

    def test_removed_edge_deletes_proven_generated_copy(self):
        sync_dual_harness.sync(self.root, write=True)
        self.write_config(
            vendored_skills=[],
            dual_plugins={"source": {"category": "Test"}, "bundle": {"category": "Test"}},
        )
        problems = sync_dual_harness.sync(self.root, write=False)
        self.assertTrue(any("stale generated copy" in problem for problem in problems))
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertFalse((self.root / "plugins/bundle/skills/shared").exists())
        self.assertFalse(self.marker().exists())
        self.assertEqual(sync_dual_harness.sync(self.root, write=False), [])

    def test_removed_edge_preserves_locally_changed_copy(self):
        sync_dual_harness.sync(self.root, write=True)
        write(
            self.root / "plugins/bundle/skills/shared/SKILL.md",
            "---\nname: shared\ndescription: Locally authored now.\n---\n",
        )
        self.write_config(
            vendored_skills=[],
            dual_plugins={"source": {"category": "Test"}, "bundle": {"category": "Test"}},
        )
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("refusing to remove" in problem for problem in problems))
        self.assertTrue((self.root / "plugins/bundle/skills/shared/SKILL.md").is_file())
        self.assertTrue(self.marker().is_file())

    def test_stale_marker_without_copy_is_cleaned(self):
        sync_dual_harness.sync(self.root, write=True)
        shutil.rmtree(self.root / "plugins/bundle/skills/shared")
        self.write_config(
            vendored_skills=[],
            dual_plugins={"source": {"category": "Test"}, "bundle": {"category": "Test"}},
        )
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertFalse(self.marker().exists())

    def test_malformed_marker_is_fatal_and_non_destructive(self):
        sync_dual_harness.sync(self.root, write=True)
        self.marker().write_text("not json\n", encoding="utf-8")
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("malformed ownership marker" in problem for problem in problems))
        self.assertTrue((self.root / "plugins/bundle/skills/shared/SKILL.md").is_file())
        self.assertEqual(self.marker().read_text(), "not json\n")

    def test_unmarked_authored_skill_is_never_inferred_as_generated(self):
        sync_dual_harness.sync(self.root, write=True)
        self.make_plugin("authored", "0.1.0")
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
            dual_plugins={
                "source": {"category": "Test"},
                "bundle": {"category": "Test"},
                "authored": {"category": "Test"},
            },
        )
        self.assertEqual(sync_dual_harness.sync(self.root, write=True), [])
        self.assertTrue((self.root / "plugins/authored/skills/shared/SKILL.md").is_file())

    def test_duplicate_target_is_rejected_before_vendoring(self):
        self.make_plugin("other", "0.1.0")
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
            dual_plugins={
                "source": {"category": "Test"},
                "bundle": {"category": "Test"},
                "other": {"category": "Test"},
            },
        )
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("duplicate target" in problem for problem in problems))
        self.assertFalse(self.marker().exists())

    def test_vendoring_chain_is_rejected(self):
        self.make_plugin("downstream", "0.1.0")
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
            dual_plugins={
                "source": {"category": "Test"},
                "bundle": {"category": "Test"},
                "downstream": {"category": "Test"},
            },
        )
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("vendoring chains are not allowed" in problem for problem in problems))

    def test_custom_claude_components_block_codex_manifest(self):
        manifest = json.loads(
            (self.root / "plugins/source/.claude-plugin/plugin.json").read_text()
        )
        manifest["agents"] = "./agents/"
        write_json(
            self.root / "plugins/source/.claude-plugin/plugin.json",
            manifest,
        )
        problems = sync_dual_harness.sync(self.root, write=True)
        self.assertTrue(any("Claude-only components" in problem for problem in problems))
        self.assertFalse((self.root / "plugins/source/.codex-plugin/plugin.json").exists())


if __name__ == "__main__":
    unittest.main()
