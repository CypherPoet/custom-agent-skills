import re
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIRECTORY = (
    REPOSITORY_ROOT
    / "plugins"
    / "session-handoff"
    / "skills"
    / "session-handoff"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import create_handoff  # noqa: E402


SOURCE_ARTIFACTS_HEADING = "## 📚 Source Artifacts"
SOURCE_ARTIFACTS_HEADING_PATTERN = re.compile(
    rf"^{re.escape(SOURCE_ARTIFACTS_HEADING)}$", re.MULTILINE
)


class SessionHandoffTemplateTests(unittest.TestCase):
    def test_reference_exposes_source_artifacts_route(self) -> None:
        reference = (
            REPOSITORY_ROOT
            / "plugins"
            / "session-handoff"
            / "skills"
            / "session-handoff"
            / "references"
            / "handoff-template.md"
        ).read_text()

        self.assertRegex(reference, SOURCE_ARTIFACTS_HEADING_PATTERN)
        self.assertIn(
            "| [📚 Source Artifacts](#-source-artifacts) |",
            reference,
        )

    def test_rendering_preserves_source_artifacts_heading(self) -> None:
        template_body = create_handoff.load_template_body()
        common_fields = {
            "timestamp": "2026-08-23T00:00:00Z",
            "branch_line": "main",
            "repo_line": "",
            "pr_line": "",
            "commits_section": "  - abc123 Test commit",
            "modified_files_section": "- [no modified files detected at scaffold time]",
        }
        optional_sections = (
            ("empty", "", ""),
            (
                "handoff chain only",
                create_handoff.build_chain_section({"exists": False}),
                "",
            ),
            (
                "handoff chain and active plan",
                create_handoff.build_chain_section({"exists": False}),
                create_handoff.build_plan_section(
                    Path.home() / ".claude" / "plans" / "test-plan.md"
                ),
            ),
        )

        for case_name, chain_section, plan_section in optional_sections:
            with self.subTest(case=case_name):
                rendered = create_handoff.render_template(
                    template_body,
                    {
                        **common_fields,
                        "chain_section": chain_section,
                        "plan_section": plan_section,
                    },
                )

                self.assertEqual(
                    SOURCE_ARTIFACTS_HEADING_PATTERN.findall(rendered),
                    [SOURCE_ARTIFACTS_HEADING],
                )


if __name__ == "__main__":
    unittest.main()
