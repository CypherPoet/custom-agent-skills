import tempfile
import unittest
from pathlib import Path

from support import load_module, write


checker = load_module(
    "skill_structure_check",
    ".claude/skills/skill-structure-check/scripts/check-skill-structure.py",
)


class SkillStructureCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.skill = self.root / "plugins/example/skills/example"
        write(
            self.skill / "SKILL.md",
            "---\nname: example\ndescription: Example fixture.\n---\n\n## Primary Sources\n",
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def audit(self):
        return checker.audit(self.root / "plugins")

    def test_module_comment_only_points_to_canonical_skill(self):
        self.assertEqual(
            checker.__doc__,
            "Implement the canonical rule contract in ../SKILL.md.",
        )

    def test_bold_contents_line_is_accepted_and_validated(self):
        text = "# Reference\n\n**Contents:** [Topic](#topic)\n\n## Topic\n"
        self.assertEqual(checker.contents_anchors(text), ["topic"])
        self.assertIn("topic", checker.heading_anchors(text))

    def test_contents_section_is_accepted_and_validated(self):
        text = "# Reference\n\n## Contents\n\n- [Topic](#topic)\n\n## Topic\n"
        self.assertEqual(checker.contents_anchors(text), ["topic"])
        self.assertIn("topic", checker.heading_anchors(text))

    def test_duplicate_heading_suffixes_match_github_anchors(self):
        text = "# Reference\n\n**Contents:** [First](#topic) · [Second](#topic-1)\n\n## Topic\n\n## Topic\n"
        self.assertEqual(checker.contents_anchors(text), ["topic", "topic-1"])
        self.assertTrue(set(checker.contents_anchors(text)) <= checker.heading_anchors(text))

    def test_large_contents_section_is_not_reported_missing(self):
        text = "# Reference\n\n## Contents\n\n- [Topic](#topic)\n\n## Topic\n"
        text += "\n".join("detail" for _ in range(301))
        write(self.skill / "references/reference.md", text)
        errors, _, missing, _, _ = self.audit()
        self.assertEqual(errors, [])
        self.assertEqual(missing, [])

    def test_stale_contents_anchor_is_an_error(self):
        text = "# Reference\n\n## Contents\n\n- [Missing](#missing)\n\n## Topic\n"
        write(self.skill / "references/reference.md", text)
        errors, _, _, _, _ = self.audit()
        self.assertTrue(any("stale Contents anchors" in error[2] for error in errors))

    def test_large_unindexed_reference_is_an_advisory(self):
        text = "# Reference\n\n" + "\n".join("detail" for _ in range(301))
        write(self.skill / "references/reference.md", text)
        _, _, missing, _, _ = self.audit()
        self.assertEqual(
            missing,
            [("example/example", "reference.md (303 lines)")],
        )

    def test_cross_plugin_relative_link_is_an_error(self):
        write(
            self.skill / "SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n"
            "[Other](../../../other/skills/other/SKILL.md)\n",
        )
        errors, _, _, _, _ = self.audit()
        self.assertTrue(any("cross-plugin relative link" in error[2] for error in errors))

    def test_fenced_cross_plugin_example_is_ignored(self):
        fence = chr(96) * 3
        write(
            self.skill / "SKILL.md",
            "---\nname: example\ndescription: Example.\n---\n\n"
            + fence
            + "\n[Other](../../../other/skills/other/SKILL.md)\n"
            + fence
            + "\n",
        )
        errors, _, _, _, _ = self.audit()
        self.assertEqual(errors, [])

    def test_skill_over_500_lines_is_an_error(self):
        write(self.skill / "SKILL.md", "\n".join("line" for _ in range(501)))
        errors, _, _, _, _ = self.audit()
        self.assertTrue(any(">500" in error[2] for error in errors))

    def test_fact_check_findings_cover_missing_duplicate_orphan_and_sources(self):
        units = {"plugin/current", "plugin/unsourced"}
        units_with_sources = {"plugin/current"}
        manifest = self.root / checker.FACT_CHECK_MANIFEST
        write(
            manifest,
            '{"weekly":["plugin/current","plugin/current","plugin/orphan"],'
            '"monthly":[],"never":[]}\n',
        )
        findings, checked = checker.tier_findings(
            self.root,
            units,
            units_with_sources,
        )
        self.assertTrue(checked)
        rendered = "\n".join(findings)
        self.assertIn("plugin/unsourced: not in any tier", rendered)
        self.assertIn("plugin/orphan: listed", rendered)
        self.assertIn("plugin/current: in more than one tier", rendered)
        self.assertIn("plugin/unsourced: fact-checked unit without", rendered)


if __name__ == "__main__":
    unittest.main()
