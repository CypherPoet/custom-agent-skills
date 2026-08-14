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


class ResearchTests(KeepingSkillsCurrentTestCase):
    def test_github_delivery_authorizes_changes_in_the_pull_request_diff(self):
        configured = manifest(
            {
                "example": skill_record(
                    sources={"example-documentation": source()},
                )
            },
            delivery={
                "strategy": "githubPullRequest",
                "branchName": "automation/keeping-skills-current",
                "autoMergeStrategy": "none",
            }
        )
        self.configure(configured)
        result_path = self.project / "result.json"
        finding = self.correction_finding()
        finding["details"]["category"] = "improvementSuggestion"
        finding["details"]["summary"] = "The documented addition materially improves reliability."
        finding["editDisposition"] = "applied"
        result = self.valid_result(
            findings=[finding],
            validation={
                "status": "passed",
                "checks": [{"name": "skill integrity", "status": "passed"}],
            },
        )
        provisional_fingerprint = self.provisional_fingerprint(result, result_path)
        write_json(result_path, result)

        accepted = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional-fingerprint",
            provisional_fingerprint,
        )

        self.assertTrue(json.loads(accepted.stdout)["valid"])

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

    def test_research_result_binds_evidence_to_cited_sources_and_reviewed_inputs(self):
        second_source = {
            "url": "https://example.com/reference/",
            "retrieval": {"strategy": "page"},
        }
        self.configure(
            manifest(
                {
                    "example": skill_record(
                        sources={
                            "example-documentation": source(),
                            "example-reference": second_source,
                        }
                    )
                }
            )
        )
        result_path = self.project / "result.json"
        finding = self.correction_finding()
        finding["evidence"][0] = {
            "sourceId": "example-reference",
            "sourceRootUrl": second_source["url"],
            "evidencePageUrl": second_source["url"],
            "summary": "The reference describes the replacement.",
            "excerpt": "Use the replacement.",
        }
        write_json(result_path, self.valid_result(findings=[finding]))
        mismatched_source = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(mismatched_source.returncode, 2)
        self.assertIn("not configured for the skill", mismatched_source.stderr)

        all_sources_finding = self.correction_finding()
        all_sources_finding["details"]["sources"]["example-reference"] = second_source
        write_json(
            result_path,
            self.valid_result(findings=[all_sources_finding]),
        )
        missing_cited_evidence = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(missing_cited_evidence.returncode, 2)
        self.assertIn("does not represent cited source", missing_cited_evidence.stderr)

        result = self.valid_result()
        write_json(result_path, result)
        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nChanged after research.\n",
        )
        stale_result = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(stale_result.returncode, 2)
        self.assertIn("does not match the current reviewed files", stale_result.stderr)

    def test_provisional_result_requires_locator_in_unchanged_target(self):
        self.configured_manifest()
        result_path = self.project / "result.json"
        finding = self.correction_finding()
        finding["details"]["target"]["currentText"] = "Guidance that is not present."
        write_json(result_path, self.valid_result(findings=[finding]))

        invalid_locator = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional",
            check=False,
        )

        self.assertEqual(invalid_locator.returncode, 2)
        self.assertIn("does not match the unchanged reviewed file", invalid_locator.stderr)

        finding["details"]["target"]["currentText"] = "Current guidance."
        write_json(result_path, self.valid_result(findings=[finding]))
        valid_locator = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional",
        )
        self.assertTrue(json.loads(valid_locator.stdout)["valid"])

    def test_provisional_correction_requires_a_complete_research_pass(self):
        configured = self.configured_manifest()
        configured["correctionStrategy"] = "applyHighConfidenceCorrections"
        configured["skills"]["example"]["sources"]["secondary-reference"] = {
            "url": "https://example.com/secondary",
            "retrieval": {"strategy": "page"},
        }
        self.configure(configured)
        result = self.valid_result(
            status="incomplete",
            findings=[self.correction_finding()],
            validation={"status": "notApplicable", "checks": []},
        )
        result["sourceOutcomes"][0] = {
            "sourceId": "example-documentation",
            "rootUrl": source()["url"],
            "status": "retrieved",
            "successfulPages": 1,
            "attemptedPages": 1,
            "limitReached": False,
        }
        result_path = self.project / "result.json"
        write_json(result_path, result)

        rejected = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional",
            check=False,
        )

        self.assertEqual(rejected.returncode, 2)
        self.assertIn("provisional changes require every configured source", rejected.stderr)

    def test_final_correction_is_bound_to_the_validated_provisional_result(self):
        configured = self.configured_manifest()
        configured["correctionStrategy"] = "applyHighConfidenceCorrections"
        self.configure(configured)
        result_path = self.project / "result.json"
        final_result = self.valid_result(
            findings=[self.correction_finding()],
            validation={
                "status": "passed",
                "checks": [{"name": "skill integrity", "status": "passed"}],
            },
        )
        final_result["findings"][0]["editDisposition"] = "applied"
        provisional_fingerprint = self.provisional_fingerprint(final_result, result_path)
        write_json(result_path, final_result)

        missing_binding = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(missing_binding.returncode, 2)
        self.assertIn(
            "edit-capable delivery requires --provisional-fingerprint",
            missing_binding.stderr,
        )

        omitted_finding_result = copy.deepcopy(final_result)
        omitted_finding_result["findings"] = []
        omitted_finding_result["validation"] = {
            "status": "notApplicable",
            "checks": [],
        }
        write_json(result_path, omitted_finding_result)
        omitted_binding = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(omitted_binding.returncode, 2)
        self.assertIn("requires --provisional-fingerprint", omitted_binding.stderr)

        write_json(result_path, final_result)
        accepted = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional-fingerprint",
            provisional_fingerprint,
        )
        self.assertTrue(json.loads(accepted.stdout)["valid"])

        final_result["findings"][0]["details"]["proposedAction"] = (
            "Replace the guidance with a different action."
        )
        write_json(result_path, final_result)
        changed_finding = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional-fingerprint",
            provisional_fingerprint,
            check=False,
        )
        self.assertEqual(changed_finding.returncode, 2)
        self.assertIn("differs from the validated provisional result", changed_finding.stderr)

    def test_final_improvement_can_be_applied_as_a_pull_request_change(self):
        configured = self.configured_manifest()
        configured["correctionStrategy"] = "applyHighConfidenceCorrections"
        self.configure(configured)
        result_path = self.project / "result.json"
        finding = self.correction_finding()
        finding["details"]["category"] = "improvementSuggestion"
        finding["details"]["summary"] = "The documented addition materially improves reliability."
        finding["editDisposition"] = "applied"
        result = self.valid_result(
            findings=[finding],
            validation={
                "status": "passed",
                "checks": [{"name": "skill integrity", "status": "passed"}],
            },
        )
        provisional_fingerprint = self.provisional_fingerprint(result, result_path)
        write_json(result_path, result)

        accepted = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional-fingerprint",
            provisional_fingerprint,
        )

        self.assertTrue(json.loads(accepted.stdout)["valid"])

    def test_render_report_rechecks_current_result_fingerprint(self):
        self.configured_manifest()
        configuration = HELPER_MODULE.load_configuration(str(self.project), None)
        result = HELPER_MODULE.validate_research_result(
            self.valid_result(),
            configuration,
        )
        payload = HELPER_MODULE.build_report_payload(
            configuration,
            [result],
            "",
        )
        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nChanged during rendering.\n",
        )

        with self.assertRaisesRegex(
            HELPER_MODULE.ContractError,
            "review inputs changed before report publication",
        ):
            HELPER_MODULE.render_report(configuration, result, payload)

    def test_research_result_rejects_applied_edits_after_failures_or_failed_checks(self):
        configured = self.configured_manifest()
        configured["correctionStrategy"] = "applyHighConfidenceCorrections"
        configured["skills"]["example"]["sources"]["secondary-reference"] = {
            "url": "https://example.com/secondary",
            "retrieval": {"strategy": "page"},
        }
        self.configure(configured)
        finding = self.correction_finding()
        finding["editDisposition"] = "applied"
        result_path = self.project / "result.json"

        incomplete = self.valid_result(
            status="incomplete",
            findings=[finding],
            validation={
                "status": "passed",
                "checks": [{"name": "skill integrity", "status": "passed"}],
            },
        )
        incomplete["sourceOutcomes"][0].update(
            {
                "status": "retrieved",
                "successfulPages": 1,
            }
        )
        incomplete["sourceOutcomes"][0].pop("failureStage")
        incomplete["sourceOutcomes"][0].pop("failureReason")
        write_json(result_path, incomplete)
        failed_source = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(failed_source.returncode, 2)
        self.assertIn("every configured source", failed_source.stderr)

        failed_check = self.valid_result(
            findings=[finding],
            validation={
                "status": "passed",
                "checks": [{"name": "project tests", "status": "failed"}],
            },
        )
        write_json(result_path, failed_check)
        inconsistent_validation = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            check=False,
        )
        self.assertEqual(inconsistent_validation.returncode, 2)
        self.assertIn("must be failed", inconsistent_validation.stderr)

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
        provisional_fingerprint = self.provisional_fingerprint(valid, result_path)
        write_json(result_path, valid)
        accepted = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional-fingerprint",
            provisional_fingerprint,
        )
        self.assertTrue(json.loads(accepted.stdout)["valid"])
