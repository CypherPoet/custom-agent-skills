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


class SchedulingTests(KeepingSkillsCurrentTestCase):
    def test_fingerprint_tracks_functional_inputs_not_assets_or_schedule(self):
        value = self.configured_manifest()
        write(self.project / "plugins/example/skills/example/references/guide.md", "Guide A\n")
        write(self.project / "plugins/example/skills/example/assets/image.txt", "asset A\n")
        first = json.loads(
            self.run_helper(
                "fingerprint",
                "--project-root",
                str(self.project),
                "--skill-id",
                "example",
            ).stdout
        )
        self.assertIn(
            "plugins/example/skills/example/references/guide.md", first["files"]
        )
        self.assertNotIn("plugins/example/skills/example/assets/image.txt", first["files"])

        write(self.project / "plugins/example/skills/example/assets/image.txt", "asset B\n")
        value["skills"]["example"]["schedule"] = {
            "recurrence": "interval",
            "intervalDays": 90,
        }
        self.configure(value)
        second = json.loads(
            self.run_helper(
                "fingerprint",
                "--project-root",
                str(self.project),
                "--skill-id",
                "example",
            ).stdout
        )
        self.assertEqual(first["inputFingerprint"], second["inputFingerprint"])

        write(self.project / "plugins/example/skills/example/references/guide.md", "Guide B\n")
        third = json.loads(
            self.run_helper(
                "fingerprint",
                "--project-root",
                str(self.project),
                "--skill-id",
                "example",
            ).stdout
        )
        self.assertNotEqual(first["inputFingerprint"], third["inputFingerprint"])

    def test_due_set_uses_interval_input_change_and_failed_attempt_backoff(self):
        self.configured_manifest("interval")
        first = json.loads(
            self.run_helper(
                "due-set",
                "--project-root",
                str(self.project),
                "--now",
                "2026-08-13T23:00:00Z",
            ).stdout
        )
        self.assertEqual(first["due"][0]["reason"], "never completed")

        value = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        value["skills"]["example"]["state"] = {
            "lastAttemptedReview": "2026-08-13T22:00:00Z",
            "lastAttemptStatus": "incomplete",
        }
        self.configure(value)
        backed_off = json.loads(
            self.run_helper(
                "due-set",
                "--project-root",
                str(self.project),
                "--now",
                "2026-08-13T23:00:00Z",
            ).stdout
        )
        self.assertEqual(backed_off["due"], [])
        self.assertIn("24-hour backoff", backed_off["skipped"][0]["reason"])

        current_fingerprint = json.loads(
            self.run_helper(
                "fingerprint",
                "--project-root",
                str(self.project),
                "--skill-id",
                "example",
            ).stdout
        )["inputFingerprint"]
        value["skills"]["example"]["state"] = {
            "lastAttemptedReview": "2026-08-13T22:00:00Z",
            "lastAttemptStatus": "incomplete",
            "lastCompletedReview": "2026-08-01T00:00:00Z",
            "inputFingerprint": current_fingerprint,
        }
        self.configure(value)
        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nChanged guidance.\n",
        )
        changed_but_backed_off = json.loads(
            self.run_helper(
                "due-set",
                "--project-root",
                str(self.project),
                "--now",
                "2026-08-13T23:00:00Z",
            ).stdout
        )
        self.assertEqual(changed_but_backed_off["due"], [])
        self.assertIn(
            "24-hour backoff",
            changed_but_backed_off["skipped"][0]["reason"],
        )
