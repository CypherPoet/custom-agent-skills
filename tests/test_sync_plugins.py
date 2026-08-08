import json
import unittest

from cypherpoet_agent_skills_tooling import sync_plugins

from support import (
    commit_all,
    fixture_directory,
    initialize_git_repo,
    write,
    write_json,
    write_plugin_registry,
    write_plugin_manifest,
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
            homepage=f"https://example.com/{name}",
        )

    @staticmethod
    def interface_metadata(name):
        return {
            "displayName": name.title(),
            "shortDescription": f"Use the {name} fixture",
            "capabilities": ["Read", "Write"],
            "defaultPrompt": [f"Use the {name} fixture for this task."],
        }

    def write_config(self, vendored_skills, plugins):
        write_plugin_registry(
            self.root,
            vendored_skills,
            {
                name: {
                    "category": "Developer Tools",
                    "interface": self.interface_metadata(name),
                }
                for name in plugins
            },
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
        codex_manifest = json.loads(
            (self.root / "plugins/bundle/.codex-plugin/plugin.json").read_text()
        )
        self.assertEqual(
            codex_manifest["interface"],
            {
                "displayName": "Bundle",
                "shortDescription": "Use the bundle fixture",
                "longDescription": "bundle fixture",
                "developerName": "Test",
                "category": "Developer Tools",
                "capabilities": ["Read", "Write"],
                "websiteURL": "https://example.com/bundle",
                "defaultPrompt": ["Use the bundle fixture for this task."],
            },
        )
        self.assertEqual(
            sorted(path.name for path in (self.root / "scripts").iterdir()),
            ["plugin-registry.json"],
        )
        self.assertEqual(sync_plugins.sync(self.root, write=False), [])

    def test_invalid_interface_metadata_blocks_generation(self):
        cases = (
            ("category", "", "category must be a non-empty string"),
            ("displayName", "", "displayName must be a non-empty string"),
            ("displayName", "x" * 31, "displayName must be at most 30"),
            ("shortDescription", "", "shortDescription must be a non-empty string"),
            ("shortDescription", "two\nlines", "shortDescription must be a single line"),
            ("shortDescription", "x" * 31, "shortDescription must be at most 30"),
            ("capabilities", [], "capabilities must contain between 1 and 20"),
            ("capabilities", ["x" * 121], "capabilities[0] must be at most 120"),
            ("defaultPrompt", [], "defaultPrompt must contain between 1 and 3"),
            ("defaultPrompt", ["one", "two", "three", "four"], "defaultPrompt must contain between 1 and 3"),
            ("defaultPrompt", [""], "defaultPrompt[0] must be a non-empty string"),
            ("defaultPrompt", ["x" * 129], "defaultPrompt[0] must be at most 128"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                self.write_config([], ("source", "bundle"))
                config_path = self.root / "scripts/plugin-registry.json"
                config = json.loads(config_path.read_text())
                metadata = config["dual_harness_plugins"]["source"]
                if field == "category":
                    metadata[field] = value
                else:
                    metadata["interface"][field] = value
                write_json(config_path, config)
                manifest_paths = sorted(self.root.glob("plugins/*/.codex-plugin/plugin.json"))
                before = {path: path.read_bytes() for path in manifest_paths}
                problems = sync_plugins.sync(self.root, write=True)
                self.assertTrue(any(expected in problem for problem in problems), problems)
                self.assertEqual(
                    {path: path.read_bytes() for path in manifest_paths},
                    before,
                )
                self.assertEqual(
                    list(self.root.glob("plugins/*/.codex-plugin/plugin.json")),
                    manifest_paths,
                )

    def test_missing_interface_object_blocks_generation(self):
        self.write_config([], ("source", "bundle"))
        config_path = self.root / "scripts/plugin-registry.json"
        config = json.loads(config_path.read_text())
        del config["dual_harness_plugins"]["source"]["interface"]
        write_json(config_path, config)
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("needs an interface object" in problem for problem in problems))
        self.assertFalse(
            (self.root / "plugins/source/.codex-plugin/plugin.json").exists()
        )

    def test_duplicate_display_names_block_generation(self):
        self.write_config([], ("source", "bundle"))
        config_path = self.root / "scripts/plugin-registry.json"
        config = json.loads(config_path.read_text())
        config["dual_harness_plugins"]["bundle"]["interface"]["displayName"] = "Ｓｏｕｒｃｅ"
        write_json(config_path, config)
        self.assertFalse(
            (self.root / "plugins/source/.codex-plugin/plugin.json").exists()
        )
        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("displayName duplicates" in problem for problem in problems))
        self.assertFalse(
            (self.root / "plugins/source/.codex-plugin/plugin.json").exists()
        )
        self.assertFalse(
            (self.root / "plugins/bundle/.codex-plugin/plugin.json").exists()
        )

    def test_required_claude_interface_sources_block_generation(self):
        cases = ("description", "author.name", "homepage")
        for field in cases:
            with self.subTest(field=field):
                self.make_plugin("source")
                manifest_path = self.root / "plugins/source/.claude-plugin/plugin.json"
                manifest = json.loads(manifest_path.read_text())
                if field == "author.name":
                    manifest["author"] = {"name": ""}
                else:
                    manifest[field] = ""
                write_json(manifest_path, manifest)
                existing_manifest = self.root / "plugins/bundle/.codex-plugin/plugin.json"
                before = existing_manifest.read_bytes() if existing_manifest.exists() else None
                problems = sync_plugins.sync(self.root, write=True)
                self.assertTrue(any(field in problem for problem in problems), problems)
                if before is None:
                    self.assertFalse(existing_manifest.exists())
                else:
                    self.assertEqual(existing_manifest.read_bytes(), before)

    def test_invalid_derived_interface_values_block_all_manifests(self):
        cases = (
            ("description", "x" * 4001, "longDescription must be at most 4000"),
            ("author", {"name": "x" * 81}, "developerName must be at most 80"),
            ("homepage", "http://example.com", "websiteURL must be an absolute https URL"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field):
                self.make_plugin("source")
                manifest_path = self.root / "plugins/source/.claude-plugin/plugin.json"
                manifest = json.loads(manifest_path.read_text())
                manifest[field] = value
                write_json(manifest_path, manifest)

                problems = sync_plugins.sync(self.root, write=True)
                self.assertTrue(any(expected in problem for problem in problems), problems)
                self.assertEqual(
                    list(self.root.glob("plugins/*/.codex-plugin/plugin.json")),
                    [],
                )

    def test_invalid_plugin_preserves_existing_manifests_and_creates_none(self):
        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        source_manifest = self.root / "plugins/source/.codex-plugin/plugin.json"
        bundle_manifest = self.root / "plugins/bundle/.codex-plugin/plugin.json"
        source_before = source_manifest.read_bytes()
        bundle_manifest.unlink()

        config_path = self.root / "scripts/plugin-registry.json"
        config = json.loads(config_path.read_text())
        del config["dual_harness_plugins"]["source"]["interface"]["displayName"]
        write_json(config_path, config)

        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("displayName" in problem for problem in problems), problems)
        self.assertEqual(source_manifest.read_bytes(), source_before)
        self.assertFalse(bundle_manifest.exists())

    def test_non_string_capability_reports_an_error_instead_of_raising(self):
        config_path = self.root / "scripts/plugin-registry.json"
        config = json.loads(config_path.read_text())
        config["dual_harness_plugins"]["source"]["interface"]["capabilities"] = [
            {"name": "Read"}
        ]
        write_json(config_path, config)

        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(
            any("capabilities[0] must be a non-empty string" in problem for problem in problems),
            problems,
        )
        self.assertFalse(
            (self.root / "plugins/source/.codex-plugin/plugin.json").exists()
        )

    def test_three_default_prompts_are_generated(self):
        config_path = self.root / "scripts/plugin-registry.json"
        config = json.loads(config_path.read_text())
        prompts = ["First task.", "Second task.", "Third task."]
        config["dual_harness_plugins"]["source"]["interface"]["defaultPrompt"] = prompts
        write_json(config_path, config)

        self.assertEqual(sync_plugins.sync(self.root, write=True), [])
        manifest = json.loads(
            (self.root / "plugins/source/.codex-plugin/plugin.json").read_text()
        )
        self.assertEqual(manifest["interface"]["defaultPrompt"], prompts)

    def test_malformed_registry_reports_without_writing(self):
        config_path = self.root / "scripts/plugin-registry.json"
        config_path.write_text("[]\n", encoding="utf-8")

        problems = sync_plugins.sync(self.root, write=True)
        self.assertTrue(any("must contain an object" in problem for problem in problems))
        self.assertEqual(list(self.root.glob("plugins/*/.codex-plugin/plugin.json")), [])

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
