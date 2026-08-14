import copy
import json
import os
import subprocess
from unittest import mock

from keeping_skills_current_test_support import (
    HELPER_MODULE,
    SKILL_ROOT,
    KeepingSkillsCurrentTestCase,
    manifest,
    skill_record,
    source,
    write,
    write_json,
)


class MigrationTests(KeepingSkillsCurrentTestCase):
    def test_legacy_migration_converts_intervals_and_surfaces_acknowledgments(self):
        skill_file = self.project / "plugins/example/skills/example/SKILL.md"
        write(
            skill_file,
            skill_file.read_text()
            + "\n## Primary Sources\n\n- [Docs](https://example.com/docs/) — current API.\n",
        )
        legacy = {
            "weekly": ["example/example"],
            "monthly": [],
            "never": ["example/ignored"],
            "acknowledged": [
                {
                    "unit_id": "example/example",
                    "locator": "Current guidance",
                    "reason": "Previously accepted",
                    "ack_date": "2026-07-09",
                    "recheck_after": "never",
                }
            ],
        }
        write_json(self.project / "legacy.json", legacy)
        result = json.loads(
            self.run_helper(
                "migrate-legacy",
                "--project-root",
                str(self.project),
                "--legacy-manifest",
                "legacy.json",
            ).stdout
        )
        migrated = result["manifest"]["skills"]["example"]
        self.assertEqual(migrated["schedule"]["intervalDays"], 7)
        self.assertEqual(len(migrated["sources"]), 1)
        self.assertEqual(len(result["legacyAcknowledgments"]), 1)
        self.assertNotIn("example-ignored", result["manifest"]["skills"])

    def test_legacy_cleanup_is_previewable_and_preserves_runtime_citations(self):
        self.configured_manifest()
        skill_path = self.project / "plugins/example/skills/example/SKILL.md"
        write(
            skill_path,
            "---\nname: example\ndescription: Example.\n---\n\n"
            "# Example\n\n**Verified:** 2026-07-11\n\n"
            "Use the [runtime guide](https://example.com/runtime).\n\n"
            "## Primary Sources\n\n- [Docs](https://example.com/docs/) — updater evidence.\n",
        )
        preview = json.loads(
            self.run_helper(
                "cleanup-legacy", "--project-root", str(self.project)
            ).stdout
        )
        self.assertFalse(preview["write"])
        self.assertIn("## Primary Sources", skill_path.read_text())
        self.run_helper(
            "cleanup-legacy", "--project-root", str(self.project), "--write"
        )
        cleaned = skill_path.read_text()
        self.assertNotIn("## Primary Sources", cleaned)
        self.assertNotIn("**Verified:**", cleaned)
        self.assertIn("[runtime guide](https://example.com/runtime)", cleaned)
