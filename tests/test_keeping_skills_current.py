import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from support import ROOT, fixture_directory, write, write_json


SKILL_ROOT = ROOT / "plugins/marketplace-kit/skills/keeping-skills-current"
HELPER = SKILL_ROOT / "scripts/keeping_skills_current.py"
BUNDLED_PYTHON = Path(
    "/Users/ethan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)
HELPER_PYTHON = BUNDLED_PYTHON if BUNDLED_PYTHON.exists() else Path(sys.executable)


def source(url="https://example.com/docs/"):
    return {
        "url": url,
        "retrieval": {
            "strategy": "crawl",
            "includePaths": ["/docs/"],
            "excludePaths": [],
            "maxDepth": 2,
            "maxPages": 25,
        },
    }


def skill_record(schedule=None, sources=None):
    return {
        "path": "plugins/example/skills/example",
        "schedule": schedule or {"recurrence": "manual"},
        "sources": sources if sources is not None else {},
        "deferredFindings": [],
        "declinedFindings": [],
    }


def manifest(skills=None, delivery=None):
    return {
        "schemaVersion": 1,
        "scheduler": "none",
        "delivery": delivery
        or {
            "strategy": "localReport",
            "reportPath": ".keeping-skills-current/report.md",
        },
        "correctionStrategy": "reportOnly",
        "changeValidation": "enabled",
        "skills": skills or {},
    }


class KeepingSkillsCurrentTests(unittest.TestCase):
    def setUp(self):
        self.project = fixture_directory(self)
        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nCurrent guidance.\n",
        )

    def run_helper(self, *arguments, check=True, input_text=None):
        return subprocess.run(
            [str(HELPER_PYTHON), str(HELPER), *arguments],
            cwd=self.project,
            input=input_text,
            capture_output=True,
            text=True,
            check=check,
        )

    def configure(self, value):
        write_json(self.project / ".keeping-skills-current/manifest.json", value)

    def test_github_delivery_establishes_owned_branch_before_due_selection(self):
        procedure = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        branch_setup = procedure.index(
            "establish the marked stable branch as the working state before selecting skills"
        )
        due_selection = procedure.index("Use `due-set` there for `run due`")
        self.assertLess(branch_setup, due_selection)

    def configured_manifest(self, recurrence="manual"):
        schedule = {"recurrence": recurrence}
        if recurrence == "interval":
            schedule["intervalDays"] = 28
        value = manifest(
            {
                "example": skill_record(
                    schedule=schedule,
                    sources={"example-documentation": source()},
                )
            }
        )
        self.configure(value)
        return value

    def valid_result(
        self,
        *,
        skill_id="example",
        skill_path="plugins/example/skills/example",
        reviewed_at="2026-08-13T23:00:00Z",
        status="completed",
        findings=None,
        failures=None,
        validation=None,
    ):
        return {
            "schemaVersion": 1,
            "projectIdentity": self.project.name,
            "skillId": skill_id,
            "skillPath": skill_path,
            "reviewedAt": reviewed_at,
            "status": status,
            "sourceOutcomes": [
                {
                    "sourceId": "example-documentation",
                    "rootUrl": "https://example.com/docs/",
                    "status": "retrieved" if status == "completed" else "failed",
                    "successfulPages": 1 if status == "completed" else 0,
                    "attemptedPages": 1,
                    "limitReached": False,
                    **(
                        {}
                        if status == "completed"
                        else {"failureStage": "retrieve", "failureReason": "timeout"}
                    ),
                }
            ],
            "findings": findings or [],
            "failures": failures
            if failures is not None
            else ([] if status == "completed" else [{"stage": "retrieve", "reason": "timeout"}]),
            "validation": validation
            or {
                "status": "notApplicable" if status == "completed" else "skipped",
                "checks": [],
            },
        }

    def correction_finding(self):
        return {
            "details": {
                "category": "correction",
                "summary": "The current guidance is obsolete.",
                "target": {
                    "filePath": "plugins/example/skills/example/SKILL.md",
                    "currentText": "Current guidance.",
                },
                "sources": {"example-documentation": source()},
                "proposedAction": "Replace it with the documented current procedure.",
            },
            "evidence": [
                {
                    "sourceId": "example-documentation",
                    "sourceRootUrl": "https://example.com/docs/",
                    "evidencePageUrl": "https://example.com/docs/current",
                    "summary": "The current procedure replaces the old one.",
                    "excerpt": "Use the current documented procedure.",
                }
            ],
            "editDisposition": "proposed",
        }

    def test_template_and_generated_schemas_are_current(self):
        template = json.loads((SKILL_ROOT / "assets/manifest.template.json").read_text())
        self.configure(template)
        result = self.run_helper("preflight", "--project-root", str(self.project))
        self.assertEqual(json.loads(result.stdout)["manifest"]["schemaVersion"], 1)
        for kind, name in (
            ("manifest", "manifest.schema.v1.json"),
            ("research", "research-result.schema.v1.json"),
        ):
            checked = self.run_helper(
                "schema",
                "--kind",
                kind,
                "--check",
                str(SKILL_ROOT / "assets" / name),
            )
            self.assertEqual(json.loads(checked.stdout)["kind"], kind)

    def test_project_identity_uses_sanitized_git_origin(self):
        subprocess.run(
            ["git", "init", "--initial-branch", "main"],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://secret-token@GitHub.com/CypherPoet/example.git",
            ],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=True,
        )
        self.configured_manifest()

        result = self.run_helper("preflight", "--project-root", str(self.project))

        self.assertEqual(
            json.loads(result.stdout)["projectIdentity"],
            "github.com/CypherPoet/example",
        )
        self.assertNotIn("secret-token", result.stdout)

    def test_preflight_rejects_unknown_fields_interval_without_source_and_unsafe_paths(self):
        cases = []
        unknown = manifest()
        unknown["unexpected"] = True
        cases.append((unknown, "unknown field"))
        cases.append(
            (
                manifest(
                    {
                        "example": skill_record(
                            schedule={"recurrence": "interval", "intervalDays": 7}
                        )
                    }
                ),
                "without a source",
            )
        )
        cases.append(
            (
                manifest({"example": {**skill_record(), "path": "../escape"}}),
                "safe repository-relative",
            )
        )
        for value, message in cases:
            with self.subTest(message=message):
                self.configure(value)
                result = self.run_helper(
                    "preflight", "--project-root", str(self.project), check=False
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)

    def test_preflight_rejects_overlapping_skills_and_external_decision_targets(self):
        second = skill_record()
        second["path"] = "plugins/example/skills/example/references/nested-skill"
        self.configure(
            manifest(
                {
                    "example": skill_record(),
                    "nested-example": second,
                }
            )
        )
        overlap = self.run_helper(
            "preflight", "--project-root", str(self.project), check=False
        )
        self.assertEqual(overlap.returncode, 2)
        self.assertIn("overlap", overlap.stderr)

        record = skill_record(sources={"example-documentation": source()})
        details = self.correction_finding()["details"]
        details["target"] = {
            "filePath": "plugins/other/skills/other/SKILL.md",
            "currentText": "Other guidance.",
        }
        record["declinedFindings"] = [
            {
                "details": details,
                "reason": "Not appropriate for this project.",
                "decidedAt": "2026-08-13T23:00:00Z",
            }
        ]
        self.configure(manifest({"example": record}))
        outside = self.run_helper(
            "preflight", "--project-root", str(self.project), check=False
        )
        self.assertEqual(outside.returncode, 2)
        self.assertIn("outside the managed skill", outside.stderr)

    def test_source_contract_rejects_private_hosts_and_start_pages_outside_crawl(self):
        for configured_source, message in (
            (source("https://127.0.0.1/docs/"), "public host"),
            (
                {
                    "url": "https://example.com/reference/",
                    "retrieval": {
                        "strategy": "crawl",
                        "includePaths": ["/docs/"],
                        "maxDepth": 2,
                        "maxPages": 25,
                    },
                },
                "includePaths",
            ),
        ):
            with self.subTest(message=message):
                self.configure(
                    manifest(
                        {
                            "example": skill_record(
                                sources={"example-documentation": configured_source}
                            )
                        }
                    )
                )
                result = self.run_helper(
                    "preflight", "--project-root", str(self.project), check=False
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)

    def test_locator_override_and_redundant_default_are_supported(self):
        write_json(self.project / "configuration/review.json", manifest())
        write_json(
            self.project / ".keeping-skills-current/config.json",
            {"manifestPath": "configuration/review.json"},
        )
        result = self.run_helper("preflight", "--project-root", str(self.project))
        self.assertEqual(json.loads(result.stdout)["manifestPath"], "configuration/review.json")

        write_json(
            self.project / ".keeping-skills-current/config.json",
            {"manifestPath": ".keeping-skills-current/manifest.json"},
        )
        self.configure(manifest())
        redundant = self.run_helper("preflight", "--project-root", str(self.project))
        self.assertIn("redundantly", json.loads(redundant.stdout)["warnings"][0])

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

    def test_research_result_cannot_leave_configured_evidence_or_apply_in_report_only(self):
        self.configured_manifest()
        finding = self.correction_finding()
        finding["evidence"][0]["evidencePageUrl"] = "https://other.example/docs/current"
        result_path = self.project / "result.json"
        write_json(result_path, self.valid_result(findings=[finding]))
        invalid_origin = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(invalid_origin.returncode, 2)
        self.assertIn("configured origin", invalid_origin.stderr)

        finding = self.correction_finding()
        finding["editDisposition"] = "applied"
        write_json(result_path, self.valid_result(findings=[finding]))
        invalid_apply = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(invalid_apply.returncode, 2)
        self.assertIn("reportOnly", invalid_apply.stderr)

    def test_research_result_enforces_retrieval_and_edit_validation_boundaries(self):
        configured = self.configured_manifest()
        result_path = self.project / "result.json"

        too_many_pages = self.valid_result()
        too_many_pages["sourceOutcomes"][0]["attemptedPages"] = 26
        too_many_pages["sourceOutcomes"][0]["successfulPages"] = 26
        write_json(result_path, too_many_pages)
        boundary = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(boundary.returncode, 2)
        self.assertIn("configured boundary", boundary.stderr)

        configured["correctionStrategy"] = "applyHighConfidenceCorrections"
        self.configure(configured)
        finding = self.correction_finding()
        finding["editDisposition"] = "applied"
        write_json(result_path, self.valid_result(findings=[finding]))
        unvalidated = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(unvalidated.returncode, 2)
        self.assertIn("validation status passed", unvalidated.stderr)

        valid = self.valid_result(
            findings=[finding],
            validation={
                "status": "passed",
                "checks": [{"name": "skill integrity", "status": "passed"}],
            },
        )
        write_json(result_path, valid)
        accepted = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
        )
        self.assertTrue(json.loads(accepted.stdout)["valid"])

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
        self.assertIn("input fingerprint is stale", stale.stderr)
        unchanged = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        self.assertNotIn("state", unchanged["skills"]["example"])

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


if __name__ == "__main__":
    unittest.main()
