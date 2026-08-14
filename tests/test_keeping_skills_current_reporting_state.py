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


class ReportingStateTests(KeepingSkillsCurrentTestCase):
    def test_report_renders_all_categories_and_preserves_human_text(self):
        self.configured_manifest()
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        write_json(result_path, self.valid_result(findings=[self.correction_finding()]))
        write(report_path, "Human introduction.\n")
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        rendered = report_path.read_text()
        self.assertTrue(rendered.startswith("Human introduction."))
        for heading in (
            "## 🛠 Corrections",
            "## 💡 Improvement Suggestions",
            "## 🚩 Human Decisions Needed",
            "## ⚠️ Retrieval or Processing Failures",
        ):
            self.assertIn(heading, rendered)
        self.assertGreaterEqual(rendered.count("No findings."), 3)

        write_json(result_path, self.valid_result())
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        rerendered = report_path.read_text()
        self.assertEqual(rerendered.count("keeping-skills-current:start"), 1)
        self.assertIn("Human introduction.", rerendered)
        self.assertIn("\nNo findings.\n", rerendered)

    def test_report_lists_source_less_drafts_without_result_or_state(self):
        draft_path = "plugins/example/skills/draft"
        write(
            self.project / draft_path / "SKILL.md",
            "---\nname: draft\ndescription: Draft.\n---\n\n# Draft\n",
        )
        draft_record = skill_record()
        draft_record["path"] = draft_path
        self.configure(
            manifest(
                {
                    "draft": draft_record,
                    "example": skill_record(
                        sources={"example-documentation": source()}
                    ),
                }
            )
        )
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        write_json(result_path, self.valid_result())

        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )

        rendered = report_path.read_text()
        self.assertIn("- Reviewed skills: `example`", rendered)
        self.assertIn(
            "- Skipped drafts: `draft` (no configured sources)", rendered
        )
        draft_row = "| `draft` | Draft — skipped (no configured sources) | 0 |"
        example_row = "| `example` | completed — reviewed this run | 1 |"
        self.assertIn(draft_row, rendered)
        self.assertIn(example_row, rendered)
        self.assertLess(rendered.index(draft_row), rendered.index(example_row))

        payload = HELPER_MODULE.existing_report_payload(rendered, self.project.name)
        self.assertEqual(set(payload["skills"]), {"example"})
        configured = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        self.assertNotIn("state", configured["skills"]["draft"])

    def test_report_preserves_unselected_results_and_marks_changed_inputs_stale(self):
        second_path = "plugins/example/skills/second"
        write(
            self.project / second_path / "SKILL.md",
            "---\nname: second\ndescription: Second.\n---\n\n# Second\n",
        )
        second_record = skill_record(sources={"example-documentation": source()})
        second_record["path"] = second_path
        self.configure(
            manifest(
                {
                    "example": skill_record(
                        sources={"example-documentation": source()}
                    ),
                    "second": second_record,
                }
            )
        )
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        write_json(result_path, self.valid_result(findings=[self.correction_finding()]))
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )

        write_json(
            result_path,
            self.valid_result(
                skill_id="second",
                skill_path=second_path,
                reviewed_at="2026-08-14T23:00:00Z",
            ),
        )
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        retained = report_path.read_text()
        self.assertIn("The current guidance is obsolete.", retained)
        self.assertIn("`example` | completed — retained from", retained)
        self.assertIn("`second` | completed — reviewed this run", retained)

        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nChanged guidance.\n",
        )
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        stale = report_path.read_text()
        self.assertIn("`example` | completed — retained; new review due", stale)
        self.assertIn("Based on an earlier configuration or skill revision", stale)

    def test_report_upgrades_results_created_before_fingerprint_binding(self):
        self.configured_manifest()
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        result = self.valid_result()
        write_json(result_path, result)
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )

        current_report = report_path.read_text()
        payload_match = HELPER_MODULE.REPORT_PAYLOAD_PATTERN.search(current_report)
        fingerprint_match = HELPER_MODULE.REPORT_FINGERPRINT_PATTERN.search(current_report)
        assert payload_match is not None and fingerprint_match is not None
        payload, _ = HELPER_MODULE.decoded_report_payload(payload_match.group(1))
        payload["skills"]["example"]["result"].pop("inputFingerprint")
        legacy_payload_marker = HELPER_MODULE.encoded_report_payload(payload)
        legacy_report_fingerprint = HELPER_MODULE.report_state_fingerprint(payload)
        legacy_report = current_report.replace(
            payload_match.group(1),
            legacy_payload_marker,
            1,
        ).replace(
            fingerprint_match.group(1),
            legacy_report_fingerprint,
            1,
        )
        write(report_path, legacy_report)

        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        upgraded_report = report_path.read_text()
        upgraded_match = HELPER_MODULE.REPORT_PAYLOAD_PATTERN.search(upgraded_report)
        assert upgraded_match is not None
        upgraded_payload, _ = HELPER_MODULE.decoded_report_payload(upgraded_match.group(1))
        self.assertEqual(
            upgraded_payload["skills"]["example"]["result"]["inputFingerprint"],
            result["inputFingerprint"],
        )

    def test_decisions_suppress_matching_findings_until_a_deferral_expires(self):
        finding = self.correction_finding()
        configured = manifest(
            {
                "example": skill_record(
                    sources={"example-documentation": source()}
                )
            }
        )
        configured["skills"]["example"]["deferredFindings"] = [
            {
                "details": finding["details"],
                "reason": "Wait for the next release cycle.",
                "decidedAt": "2026-08-01T00:00:00Z",
                "revisitAfter": "2026-09-01T00:00:00Z",
            }
        ]
        self.configure(configured)
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        write_json(result_path, self.valid_result(findings=[finding]))
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )
        active = report_path.read_text()
        self.assertIn("## 🗃️ Deferred and Declined Findings", active)
        self.assertIn("deferred (active)", active)
        corrections = active.split("## 🛠 Corrections", 1)[1].split(
            "## 💡 Improvement Suggestions", 1
        )[0]
        self.assertIn("No findings.", corrections)

        configured["skills"]["example"]["deferredFindings"][0][
            "revisitAfter"
        ] = "2026-08-02T00:00:00Z"
        self.configure(configured)
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        expired = report_path.read_text()
        self.assertIn("The current guidance is obsolete.", expired)
        self.assertIn("inactive — revisit date passed", expired)

    def test_completed_state_requires_valid_result_and_matching_delivered_report(self):
        self.configured_manifest("interval")
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        write_json(result_path, self.valid_result())
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )
        self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--delivered-report",
            str(report_path),
        )
        updated = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        state = updated["skills"]["example"]["state"]
        self.assertEqual(state["lastAttemptStatus"], "completed")
        self.assertEqual(state["lastCompletedReview"], "2026-08-13T23:00:00Z")

        write_json(result_path, {"status": "completed"})
        failed = self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--delivered-report",
            str(report_path),
            check=False,
        )
        self.assertEqual(failed.returncode, 2)
        after = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        self.assertEqual(after["skills"]["example"]["state"], state)

    def test_state_rejects_tampered_reports_and_stale_review_inputs(self):
        self.configured_manifest("interval")
        result_path = self.project / "result.json"
        report_path = self.project / "report.md"
        write_json(result_path, self.valid_result())
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )
        original = report_path.read_text()
        write(
            report_path,
            original.replace(
                'reviewStateFingerprint="sha256:',
                'reviewStateFingerprint="sha256:0',
                1,
            ),
        )
        tampered = self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--delivered-report",
            str(report_path),
            check=False,
        )
        self.assertEqual(tampered.returncode, 2)
        self.assertIn("ownership markers", tampered.stderr)

        write(report_path, original)
        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nChanged after review.\n",
        )
        stale = self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--delivered-report",
            str(report_path),
            check=False,
        )
        self.assertEqual(stale.returncode, 2)
        self.assertIn("does not match the current reviewed files", stale.stderr)
        unchanged = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        self.assertNotIn("state", unchanged["skills"]["example"])

    def test_apply_state_validates_current_fingerprint_only_for_selected_skill(self):
        write(
            self.project / "plugins/example/skills/second/SKILL.md",
            "---\nname: second\ndescription: Second.\n---\n\n# Second\n\nCurrent guidance.\n",
        )
        self.configure(
            manifest(
                {
                    "example": skill_record(
                        schedule={"recurrence": "interval", "intervalDays": 28},
                        sources={"example-documentation": source()},
                    ),
                    "second": {
                        **skill_record(
                            schedule={"recurrence": "interval", "intervalDays": 28},
                            sources={"second-documentation": source()},
                        ),
                        "path": "plugins/example/skills/second",
                    },
                }
            )
        )
        example_result = self.valid_result()
        second_result = self.valid_result(
            skill_id="second",
            skill_path="plugins/example/skills/second",
        )
        report_input = {
            "projectIdentity": self.project.name,
            "reviewedAt": "2026-08-13T23:00:00Z",
            "skillResults": [example_result, second_result],
        }
        result_path = self.project / "results.json"
        report_path = self.project / "report.md"
        write_json(result_path, report_input)
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--output",
            str(report_path),
        )
        write(
            self.project / "plugins/example/skills/second/SKILL.md",
            "---\nname: second\ndescription: Second.\n---\n\n# Second\n\nChanged after review.\n",
        )

        all_skills = self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--delivered-report",
            str(report_path),
            check=False,
        )
        self.assertEqual(all_skills.returncode, 2)
        self.assertIn("does not match the current reviewed files", all_skills.stderr)

        self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--delivered-report",
            str(report_path),
            "--skill-id",
            "example",
        )

        configured = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        self.assertEqual(
            configured["skills"]["example"]["state"]["lastAttemptStatus"],
            "completed",
        )
        self.assertNotIn("state", configured["skills"]["second"])

    def test_incomplete_attempt_preserves_prior_completed_state(self):
        self.configured_manifest("interval")
        complete_path = self.project / "complete.json"
        incomplete_path = self.project / "incomplete.json"
        report_path = self.project / "report.md"
        write_json(complete_path, self.valid_result())
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(complete_path),
            "--output",
            str(report_path),
        )
        self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(complete_path),
            "--delivered-report",
            str(report_path),
        )
        incomplete = self.valid_result(status="incomplete")
        incomplete["reviewedAt"] = "2026-08-14T23:00:00Z"
        write_json(incomplete_path, incomplete)
        self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(incomplete_path),
            "--existing-report",
            str(report_path),
            "--output",
            str(report_path),
        )
        self.run_helper(
            "apply-state",
            "--project-root",
            str(self.project),
            "--input",
            str(incomplete_path),
            "--delivered-report",
            str(report_path),
        )
        state = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )["skills"]["example"]["state"]
        self.assertEqual(state["lastAttemptStatus"], "incomplete")
        self.assertEqual(state["lastAttemptedReview"], "2026-08-14T23:00:00Z")
        self.assertEqual(state["lastCompletedReview"], "2026-08-13T23:00:00Z")
