import json
import unittest

from support import (
    commit_all,
    fixture_directory,
    initialize_git_repo,
    load_module,
    write,
    write_plugin_registry,
    write_plugin_manifest,
)


sync_plugins = load_module(
    "sync_plugins",
    "scripts/sync_plugins.py",
)


class SyncPluginsTests(unittest.TestCase):
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
        write_plugin_registry(
            self.root,
            vendored_skills,
            {name: {"category": "Test"} for name in plugins},
        )

    def commit_baseline(self):
        initialize_git_repo(self.root)
        commit_all(self.root, "baseline")

    def test_write_creates_copy_and_codex_manifests_with_no_state(self):
        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        self.assertEqual(
            (self.root / "plugins/bundle/skills/shared/SKILL.md").read_text(),
            (self.root / "plugins/source/skills/shared/SKILL.md").read_text(),
        )
        self.assertTrue(
            (self.root / "plugins/bundle/.codex-plugin/plugin.json").is_file()
        )
        self.assertEqual(
            sorted(path.name for path in (self.root / "scripts").iterdir()),
            ["plugin-registry.json"],
        )
        self.assertEqual(sync_plugins.sync(self.root, write=False), [])

    def test_copy_drift_is_detected_and_write_repairs_it(self):
        sync_plugins.sync(self.root, write=True)
        write(
            self.root / "plugins/bundle/skills/shared/SKILL.md",
            "---\nname: shared\ndescription: Hand-edited.\n---\n",
        )
        problems = sync_plugins.sync(self.root, write=False)
        self.assertTrue(any("out of sync" in problem for problem in problems))
        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        self.assertEqual(sync_plugins.sync(self.root, write=False), [])

    def test_removed_edge_deletes_committed_clean_copy(self):
        sync_plugins.sync(self.root, write=True)
        self.commit_baseline()
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        problems = sync_plugins.sync(self.root, write=False)
        self.assertTrue(any("stale generated copy" in problem for problem in problems))
        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        self.assertFalse((self.root / "plugins/bundle/skills/shared").exists())
        self.assertEqual(sync_plugins.sync(self.root, write=False), [])

    def test_removed_edge_refuses_uncommitted_changes(self):
        sync_plugins.sync(self.root, write=True)
        self.commit_baseline()
        write(
            self.root / "plugins/bundle/skills/shared/SKILL.md",
            "---\nname: shared\ndescription: Locally authored now.\n---\n",
        )
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("refusing to remove" in problem for problem in problems))
        self.assertTrue((self.root / "plugins/bundle/skills/shared/SKILL.md").is_file())

    def test_removed_edge_refuses_untracked_content(self):
        # evals/ and *-workspace/ are excluded from vendoring, but they are
        # still local work: retiring an edge must never silently delete them.
        sync_plugins.sync(self.root, write=True)
        self.commit_baseline()
        write(
            self.root / "plugins/bundle/skills/shared/evals/evals.json",
            '{"cases": []}\n',
        )
        self.write_config(vendored_skills=[], plugins=("source", "bundle"))
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("refusing to remove" in problem for problem in problems))
        self.assertTrue(
            (self.root / "plugins/bundle/skills/shared/evals/evals.json").is_file()
        )

    def test_undeclared_identical_copy_is_flagged(self):
        sync_plugins.sync(self.root, write=True)
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
        problems = sync_plugins.sync(self.root, write=False)
        self.assertTrue(any("undeclared byte-identical copy" in problem for problem in problems))

    def test_diverged_authored_twin_is_not_flagged(self):
        sync_plugins.sync(self.root, write=True)
        self.make_plugin("authored")
        write(
            self.root / "plugins/authored/skills/shared/SKILL.md",
            "---\nname: shared\ndescription: Independently authored.\n---\n",
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
        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        self.assertEqual(sync_plugins.sync(self.root, write=False), [])

    def test_gitignored_files_are_not_vendored(self):
        # A gitignored machine-local file must not reach the copy — otherwise
        # one machine's junk becomes another machine's phantom drift.
        self.commit_baseline()
        write(self.root / ".gitignore", "*.log\n")
        commit_all(self.root, "ignore logs")
        write(self.root / "plugins/source/skills/shared/debug.log", "local junk\n")
        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        self.assertFalse(
            (self.root / "plugins/bundle/skills/shared/debug.log").exists()
        )
        self.assertEqual(sync_plugins.sync(self.root, write=False), [])

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
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("duplicate target" in problem for problem in problems))
        self.assertFalse((self.root / "plugins/bundle/skills/shared").exists())

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
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("vendoring chains are not allowed" in problem for problem in problems))

    def test_custom_claude_components_block_codex_manifest(self):
        manifest = json.loads(
            (self.root / "plugins/source/.claude-plugin/plugin.json").read_text()
        )
        manifest["agents"] = "./agents/"
        write_plugin_manifest(self.root, "source", **{k: v for k, v in manifest.items() if k != "name"})
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("Claude-only components" in problem for problem in problems))
        self.assertFalse((self.root / "plugins/source/.codex-plugin/plugin.json").exists())


if __name__ == "__main__":
    unittest.main()
