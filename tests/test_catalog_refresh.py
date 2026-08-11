import unittest
import subprocess
import sys

from support import ROOT, fixture_directory, load_module, write, write_json


catalog_refresh = load_module(
    "catalog_refresh",
    "plugins/marketplace-kit/skills/catalog-refresh/scripts/refresh_catalog.py",
)


class CatalogRefreshTests(unittest.TestCase):
    def setUp(self):
        self.root = fixture_directory(self)

    def test_components_count_all_supported_types(self):
        plugin = self.root / "plugins/example"
        write(plugin / "skills/skill/SKILL.md", "---\nname: skill\ndescription: Skill.\n---\n")
        write(plugin / "commands/run.md", "# Run\n")
        write(plugin / "agents/reviewer.md", "# Reviewer\n")
        write_json(
            plugin / "hooks/hooks.json",
            {"hooks": {"PreToolUse": [{"hooks": [{}, {}]}]}},
        )
        write_json(
            plugin / ".mcp.json",
            {"mcpServers": {"one": {}, "two": {}}},
        )
        self.assertEqual(
            catalog_refresh.components(plugin),
            "1 skill, 1 command, 1 agent, 2 hooks, 2 MCP servers",
        )

    def test_rows_are_sorted_and_escape_pipes(self):
        for name, description in (("zeta", "Zeta"), ("alpha", "Alpha | Beta")):
            write_json(
                self.root / f"plugins/{name}/.claude-plugin/plugin.json",
                {"name": name, "description": description},
            )
        rows, problems = catalog_refresh.build_rows(self.root)
        self.assertEqual(problems, [])
        self.assertIn("[alpha]", rows[0])
        self.assertIn("Alpha \\| Beta", rows[0])
        self.assertIn("[zeta]", rows[1])

    def test_missing_description_is_reported(self):
        write_json(
            self.root / "plugins/example/.claude-plugin/plugin.json",
            {"name": "example"},
        )
        _, problems = catalog_refresh.build_rows(self.root)
        self.assertEqual(problems, ["example: manifest has no description"])

    def test_codex_only_plugin_is_included(self):
        write_json(
            self.root / "plugins/codex-only/.codex-plugin/plugin.json",
            {"name": "codex-only", "description": "Codex only"},
        )
        rows, problems = catalog_refresh.build_rows(self.root)
        self.assertEqual(problems, [])
        self.assertEqual(
            rows,
            [
                "| [codex-only](../plugins/codex-only/README.md) | "
                "Codex only | — |"
            ],
        )

    def test_claude_manifest_is_preferred_when_both_exist(self):
        plugin = self.root / "plugins/example"
        write_json(
            plugin / ".claude-plugin/plugin.json",
            {"name": "example", "description": "Claude description"},
        )
        write_json(
            plugin / ".codex-plugin/plugin.json",
            {"name": "example", "description": "Codex description"},
        )
        rows, problems = catalog_refresh.build_rows(self.root)
        self.assertEqual(problems, [])
        self.assertIn("Claude description", rows[0])
        self.assertNotIn("Codex description", rows[0])

    def test_plugin_without_a_platform_manifest_is_reported(self):
        write(self.root / "plugins/example/README.md", "# Example\n")
        rows, problems = catalog_refresh.build_rows(self.root)
        self.assertEqual(rows, [])
        self.assertEqual(
            problems,
            ["example: no Claude or Codex plugin manifest"],
        )

    def test_replace_table_preserves_surrounding_prose_and_final_newline(self):
        original = (
            "# Catalog\n\n"
            "| Plugin | Description | Components |\n"
            "|---|---|---|\n"
            "| old | old | old |\n\n"
            "## Installing\n\nKeep me.\n"
        )
        replacement = (
            "| Plugin | Description | Components |\n"
            "|---|---|---|\n"
            "| new | new | new |"
        )
        updated = catalog_refresh.replace_table(original, replacement)
        self.assertIn("| new | new | new |", updated)
        self.assertNotIn("| old | old | old |", updated)
        self.assertTrue(updated.endswith("Keep me.\n"))

    def test_repository_catalog_is_current(self):
        result = subprocess.run(
            [
                sys.executable,
                ROOT
                / "plugins/marketplace-kit/skills/catalog-refresh/"
                "scripts/refresh_catalog.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
