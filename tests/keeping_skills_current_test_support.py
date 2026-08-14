import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from support import ROOT, fixture_directory, write, write_json


SKILL_ROOT = ROOT / "plugins/marketplace-kit/skills/keeping-skills-current"
HELPER = SKILL_ROOT / "scripts/keeping_skills_current.py"
BUNDLED_PYTHON = Path(
    "/Users/ethan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)
HELPER_PYTHON = BUNDLED_PYTHON if BUNDLED_PYTHON.exists() else Path(sys.executable)
HELPER_SPEC = importlib.util.spec_from_file_location("keeping_skills_current_helper", HELPER)
assert HELPER_SPEC is not None and HELPER_SPEC.loader is not None
HELPER_MODULE = importlib.util.module_from_spec(HELPER_SPEC)
sys.modules[HELPER_SPEC.name] = HELPER_MODULE
HELPER_SPEC.loader.exec_module(HELPER_MODULE)


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


class KeepingSkillsCurrentTestCase(unittest.TestCase):
    def setUp(self):
        self.project = fixture_directory(self)
        write(
            self.project / "plugins/example/skills/example/SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n# Example\n\nCurrent guidance.\n",
        )

    def run_helper(self, *arguments, check=True, input_text=None, environment=None):
        return subprocess.run(
            [str(HELPER_PYTHON), str(HELPER), *arguments],
            cwd=self.project,
            input=input_text,
            capture_output=True,
            text=True,
            check=check,
            env=environment,
        )

    def configure(self, value):
        write_json(self.project / ".keeping-skills-current/manifest.json", value)

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
        configured = json.loads(
            (self.project / ".keeping-skills-current/manifest.json").read_text()
        )
        configured_sources = configured["skills"][skill_id]["sources"]
        fingerprint = json.loads(
            self.run_helper(
                "fingerprint",
                "--project-root",
                str(self.project),
                "--skill-id",
                skill_id,
            ).stdout
        )["inputFingerprint"]
        return {
            "schemaVersion": 1,
            "projectIdentity": self.project.name,
            "skillId": skill_id,
            "skillPath": skill_path,
            "inputFingerprint": fingerprint,
            "reviewedAt": reviewed_at,
            "status": status,
            "sourceOutcomes": [
                {
                    "sourceId": source_id,
                    "rootUrl": configured_sources[source_id]["url"],
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
                for source_id in sorted(configured_sources)
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

    def provisional_fingerprint(self, result, result_path):
        provisional = copy.deepcopy(result)
        for finding in provisional["findings"]:
            if finding["details"]["category"] in {
                "correction",
                "improvementSuggestion",
            }:
                finding["editDisposition"] = "proposed"
        provisional["validation"] = {"status": "notApplicable", "checks": []}
        write_json(result_path, provisional)
        validated = self.run_helper(
            "render-report",
            "--project-root",
            str(self.project),
            "--input",
            str(result_path),
            "--validate-only",
            "--provisional",
        )
        return json.loads(validated.stdout)["provisionalFingerprint"]
