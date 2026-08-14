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


class ConfigurationTests(KeepingSkillsCurrentTestCase):
    def test_skill_routes_actions_to_single_owned_contracts(self):
        procedure = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        routes = {
            "`configure`": (
                "references/configuration.md",
                "references/scheduling.md",
            ),
            "`run`, `run all`, or `run due`": (
                "references/research.md",
                "references/findings-and-state.md",
                "references/delivery.md",
            ),
            "`status`": ("references/configuration.md#helper-interface",),
        }
        lines = procedure.splitlines()
        for action, references in routes.items():
            with self.subTest(action=action):
                row = next(
                    (line for line in lines if line.startswith(f"| {action} |")),
                    None,
                )
                self.assertIsNotNone(row)
                for reference in references:
                    self.assertIn(f"]({reference})", row)

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
            (source("https://127.1/docs/"), "public host"),
            (source("https://2130706433/docs/"), "public host"),
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

        with mock.patch(
            "socket.getaddrinfo",
            side_effect=AssertionError("configuration validation must not perform DNS"),
        ):
            unresolved = HELPER_MODULE.normalize_source_url(
                "https://not-yet-resolved.example/docs/",
                "source URL",
                False,
            )
        self.assertEqual(unresolved, "https://not-yet-resolved.example/docs/")
        self.assertEqual(
            HELPER_MODULE.normalize_source_url(
                "https://[2606:4700:4700::1111]/docs/",
                "source URL",
                False,
            ),
            "https://[2606:4700:4700::1111]/docs/",
        )
        self.assertEqual(
            HELPER_MODULE.normalize_source_url(
                "https://8.8.8.8/docs/",
                "source URL",
                False,
            ),
            "https://8.8.8.8/docs/",
        )

    def test_preflight_rejects_invalid_git_refs_and_active_manifests_inside_skills(self):
        for branch_name in ("review~1", "review^next", "topic.lock", "HEAD", "@{-1}"):
            with self.subTest(branch_name=branch_name):
                self.configure(
                    manifest(
                        delivery={
                            "strategy": "githubPullRequest",
                            "branchName": branch_name,
                            "autoMergeStrategy": "none",
                        }
                    )
                )
                result = self.run_helper(
                    "preflight", "--project-root", str(self.project), check=False
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("safe Git branch name", result.stderr)

        inside_path = "plugins/example/skills/example/references/review.json"
        inside_manifest = self.project / inside_path
        write_json(inside_manifest, manifest({"example": skill_record()}))
        for locator_arguments in (
            ("--manifest", inside_path),
            (),
        ):
            with self.subTest(locator_arguments=locator_arguments):
                if not locator_arguments:
                    write_json(
                        self.project / ".keeping-skills-current/config.json",
                        {"manifestPath": inside_path},
                    )
                result = self.run_helper(
                    "preflight",
                    "--project-root",
                    str(self.project),
                    *locator_arguments,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("must remain outside managed skill", result.stderr)

        symlink_target = self.project / "plugins/example/skills/example/references"
        symlink_parent = self.project / "config-link"
        symlink_parent.symlink_to(symlink_target, target_is_directory=True)
        write_json(symlink_target / "manifest.json", manifest({"example": skill_record()}))
        symlinked_parent = self.run_helper(
            "preflight",
            "--project-root",
            str(self.project),
            "--manifest",
            "config-link/manifest.json",
            check=False,
        )
        self.assertEqual(symlinked_parent.returncode, 2)
        self.assertIn("must remain outside managed skill", symlinked_parent.stderr)

    def test_status_reports_unavailable_git_without_rejecting_configuration(self):
        self.configure(
            manifest(
                delivery={
                    "strategy": "githubPullRequest",
                    "branchName": "automation/keeping-skills-current",
                    "autoMergeStrategy": "none",
                }
            )
        )
        environment = {**os.environ, "PATH": str(self.project / "missing-bin")}

        status = self.run_helper(
            "status",
            "--project-root",
            str(self.project),
            environment=environment,
        )
        self.assertFalse(json.loads(status.stdout)["capabilities"]["gitAvailable"])
        mutation = self.run_helper(
            "preflight",
            "--project-root",
            str(self.project),
            "--mutation",
            check=False,
            environment=environment,
        )
        self.assertEqual(mutation.returncode, 2)
        self.assertIn("requires Git before mutation", mutation.stderr)

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
