import unittest

from support import ROOT


class MarketplacePublishContractTests(unittest.TestCase):
    def test_mapping_registry_carries_codex_display_names(self):
        mappings = (
            ROOT
            / "plugins/cypherpoet-marketplace-kit/references/marketplaces.md"
        ).read_text(encoding="utf-8")
        self.assertIn("CypherPoet Toolchest`", mappings)
        self.assertIn("CypherPoet Toolchest Private`", mappings)
        self.assertIn("which user-facing Codex display name", mappings)

    def test_publish_procedure_seeds_and_pins_marketplace_display_name(self):
        procedure = (
            ROOT
            / "plugins/cypherpoet-marketplace-kit/skills/marketplace-publish/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("EXPECTED_CODEX_DISPLAY_NAME", procedure)
        self.assertIn(
            '"interface": {"displayName": "<Codex-display-name>"}',
            procedure,
        )
        self.assertIn('"path": "plugins/<plugin>"', procedure)


if __name__ == "__main__":
    unittest.main()
