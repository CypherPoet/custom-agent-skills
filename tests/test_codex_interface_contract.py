import copy
import unittest

from cypherpoet_agent_skills_tooling import validate_codex_interface


VALID_INTERFACE = {
    "displayName": "Example Tools",
    "shortDescription": "Build example workflows",
    "longDescription": "Build and validate example workflows.",
    "developerName": "CypherPoet",
    "category": "Developer Tools",
    "capabilities": ["Read", "Write"],
    "websiteURL": "https://example.com/plugins/example",
    "defaultPrompt": ["Build an example workflow for this task."],
}


class CodexInterfaceContractTests(unittest.TestCase):
    def validate(self, interface=None, *, source_homepage=None):
        return validate_codex_interface(
            copy.deepcopy(VALID_INTERFACE if interface is None else interface),
            source_homepage=source_homepage,
        )

    def assert_invalid(self, field, value, expected):
        interface = copy.deepcopy(VALID_INTERFACE)
        interface[field] = value
        problems = self.validate(interface)
        self.assertTrue(
            any(expected in problem for problem in problems),
            f"expected {expected!r} in {problems}",
        )

    def test_valid_complete_interface_passes(self):
        self.assertEqual(
            self.validate(source_homepage=VALID_INTERFACE["websiteURL"]),
            [],
        )

    def test_display_name_contract(self):
        cases = (
            (None, "must be a non-empty string"),
            ("", "must be a non-empty string"),
            (" Example Tools", "must not contain surrounding whitespace"),
            ("Example\nTools", "must be a single line"),
            ("x" * 31, "must be at most 30"),
            ("Example\u200bTools", "unsupported text characters"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assert_invalid("displayName", value, expected)

    def test_short_and_long_description_contracts(self):
        self.assert_invalid("shortDescription", "x" * 31, "at most 30")
        self.assert_invalid("shortDescription", "two\nlines", "single line")
        self.assert_invalid("longDescription", "x" * 4001, "at most 4000")
        self.assert_invalid(
            "longDescription",
            "Paragraph one.\u2028Paragraph two.",
            "unsupported text characters",
        )

        interface = copy.deepcopy(VALID_INTERFACE)
        interface["longDescription"] = "Paragraph one.\nParagraph two."
        self.assertEqual(self.validate(interface), [])

    def test_developer_name_and_category_contracts(self):
        self.assert_invalid("developerName", "x" * 81, "at most 80")
        self.assert_invalid("developerName", " CypherPoet", "surrounding whitespace")
        self.assert_invalid("category", "Design", "must be one of")
        self.assert_invalid("category", "Developer Tools ", "surrounding whitespace")

    def test_capabilities_are_free_form_but_bounded_and_unique(self):
        interface = copy.deepcopy(VALID_INTERFACE)
        interface["capabilities"] = ["Run network requests", "Transform files"]
        self.assertEqual(self.validate(interface), [])

        cases = (
            ([], "between 1 and 20"),
            ([f"Capability {index}" for index in range(21)], "between 1 and 20"),
            (["x" * 121], "at most 120"),
            (["Read", "read"], "duplicates"),
            (["Read", "Ｒｅａｄ"], "duplicates"),
            (["Read", "Read"], "duplicates"),
            ([" Read"], "surrounding whitespace"),
            ([{"name": "Read"}], "must be a non-empty string"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assert_invalid("capabilities", value, expected)

    def test_default_prompts_allow_one_to_three_canonical_unique_strings(self):
        interface = copy.deepcopy(VALID_INTERFACE)
        interface["defaultPrompt"] = [
            "Build the first workflow.",
            "Review the second workflow.",
            "Explain the third workflow.",
        ]
        self.assertEqual(self.validate(interface), [])

        cases = (
            ([], "between 1 and 3"),
            (["one", "two", "three", "four"], "between 1 and 3"),
            (["x" * 129], "at most 128"),
            (["Build it.", "Build  it."], "duplicates"),
            (["Ａudit it.", "Audit it."], "duplicates"),
            ([" Build it."], "surrounding whitespace"),
            (["Ask @Linear to create an issue."], "must not contain an app @mention"),
            ([{"prompt": "Build it."}], "must be a non-empty string"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assert_invalid("defaultPrompt", value, expected)

    def test_prompt_uniqueness_is_case_sensitive(self):
        interface = copy.deepcopy(VALID_INTERFACE)
        interface["defaultPrompt"] = ["Build it.", "build it."]
        self.assertEqual(self.validate(interface), [])

    def test_website_url_contract(self):
        cases = (
            ("http://example.com", "absolute https URL"),
            ("https:///missing-host", "absolute https URL"),
            ("https://user:secret@example.com", "must not contain credentials"),
            ("https://example.com/a path", "unsupported URL characters"),
            ("https://example.com/<bad>", "unsupported URL characters"),
            ("https://example.com/" + "x" * 1005, "at most 1024"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assert_invalid("websiteURL", value, expected)

    def test_source_homepage_contract_and_composition(self):
        problems = self.validate(source_homepage="https://example.com/other")
        self.assertTrue(any("must equal the source homepage" in problem for problem in problems))

        overlong_source = "https://example.com/" + "x" * 2030
        problems = self.validate(source_homepage=overlong_source)
        self.assertTrue(any("source homepage must be at most 2048" in problem for problem in problems))

    def test_interface_must_be_an_object(self):
        self.assertEqual(self.validate([]), ["interface must be an object"])


if __name__ == "__main__":
    unittest.main()
