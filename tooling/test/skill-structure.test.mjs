import assert from "node:assert/strict";
import { join } from "node:path";
import test from "node:test";

import { auditSkillStructure } from "../dist/skill-structure.js";
import { temporaryDirectory, writeText } from "./support.mjs";

function fixture(testContext) {
  const root = temporaryDirectory(testContext);
  const skill = join(root, "plugins/example/skills/example");
  writeText(
    join(skill, "SKILL.md"),
    "---\nname: example\ndescription: Example fixture.\n---\n",
  );
  return { root, skill };
}

test("oversized skills are reported", (t) => {
  const { root, skill } = fixture(t);
  writeText(join(skill, "SKILL.md"), Array.from({ length: 501 }, () => "line").join("\n"));
  assert.ok(
    auditSkillStructure(join(root, "plugins")).errors.some((finding) =>
      finding[2].includes(">500"),
    ),
  );
});

test("relative links that leave a plugin fail everywhere shipped Markdown can appear", async (t) => {
  const cases = [
    ["plugins/example/README.md", "../other/skills/other/SKILL.md", "example", "README.md"],
    [
      "plugins/example/commands/publish.md",
      "../../other/skills/other/SKILL.md",
      "example",
      "commands/publish.md",
    ],
    [
      "plugins/example/references/nested/guide.md",
      "../../../other/skills/other/SKILL.md",
      "example",
      "references/nested/guide.md",
    ],
    [
      "plugins/example/skills/example/evals/fixtures/case.md",
      "../../../../../other/skills/other/SKILL.md",
      "example/example",
      "evals/fixtures/case.md",
    ],
    ["plugins/bundle/README.md", "../example/skills/example/SKILL.md", "bundle", "README.md"],
  ];
  for (const [path, target, expectedLabel, expectedLocation] of cases) {
    await t.test(path, (caseContext) => {
      const { root } = fixture(caseContext);
      writeText(join(root, path), `# Fixture\n\n[Other](${target})\n`);
      assert.ok(
        auditSkillStructure(join(root, "plugins")).errors.some(
          ([label, location]) => label === expectedLabel && location === expectedLocation,
        ),
      );
    });
  }
});

test("in-plugin, absolute, fenced, and non-Markdown links do not fail", async (t) => {
  await t.test("valid Markdown links", (caseContext) => {
    const { root } = fixture(caseContext);
    writeText(
      join(root, "plugins/example/README.md"),
      "# Example\n\n[Skill](skills/example/SKILL.md)\n" +
        "[Sibling](https://github.com/CypherPoet/custom-agent-skills/tree/main/plugins/other)\n",
    );
    assert.deepEqual(auditSkillStructure(join(root, "plugins")).errors, []);
  });
  await t.test("fenced example", (caseContext) => {
    const { root } = fixture(caseContext);
    writeText(
      join(root, "plugins/example/README.md"),
      "# Example\n\n```markdown\n[Other](../other/skills/other/SKILL.md)\n```\n",
    );
    assert.deepEqual(auditSkillStructure(join(root, "plugins")).errors, []);
  });
  await t.test("non-Markdown", (caseContext) => {
    const { root } = fixture(caseContext);
    writeText(
      join(root, "plugins/example/commands/config.json"),
      '{"link":"../../other/skills/other/SKILL.md"}\n',
    );
    assert.deepEqual(auditSkillStructure(join(root, "plugins")).errors, []);
  });
});
