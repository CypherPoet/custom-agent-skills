import assert from "node:assert/strict";
import { join } from "node:path";
import test from "node:test";

import {
  auditSkillStructure,
  contentsAnchors,
  headingAnchors,
} from "../dist/skill-structure.js";
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

test("Contents jump lines and duplicate heading suffixes match GitHub anchors", () => {
  const text =
    "# Reference\n\n**Contents:** [First](#topic) · [Second](#topic-1)\n\n" +
    "## Topic\n\n## Topic\n";
  assert.deepEqual(contentsAnchors(text), ["topic", "topic-1"]);
  const headings = headingAnchors(text);
  assert.ok(contentsAnchors(text).every((anchor) => headings.has(anchor)));
});

test("only a populated, unfenced Contents jump line indexes a reference", async (t) => {
  await t.test("old Contents section", (caseContext) => {
    const { root, skill } = fixture(caseContext);
    const text =
      "# Reference\n\n## Contents\n\n- [Topic](#topic)\n\n## Topic\n\n" +
      Array.from({ length: 301 }, () => "detail").join("\n");
    writeText(join(skill, "references/reference.md"), text);
    const audit = auditSkillStructure(join(root, "plugins"));
    assert.deepEqual(audit.errors, []);
    assert.equal(audit.missingContents.length, 1);
  });
  await t.test("fenced example", (caseContext) => {
    const { root, skill } = fixture(caseContext);
    const text =
      "# Reference\n\n```markdown\n**Contents:** [Example](#not-real)\n```\n\n" +
      "**Contents:** [Topic](#topic)\n\n## Topic\n";
    assert.deepEqual(contentsAnchors(text), ["topic"]);
    writeText(join(skill, "references/reference.md"), text);
    assert.deepEqual(auditSkillStructure(join(root, "plugins")).errors, []);
  });
  await t.test("linkless line", (caseContext) => {
    const { root, skill } = fixture(caseContext);
    const text =
      "# Reference\n\n**Contents:** see below.\n\n## Topic\n\n" +
      Array.from({ length: 301 }, () => "detail").join("\n");
    writeText(join(skill, "references/reference.md"), text);
    assert.equal(auditSkillStructure(join(root, "plugins")).missingContents.length, 1);
  });
});

test("stale Contents anchors fail, including headings that exist only in fences", async (t) => {
  for (const text of [
    "# Reference\n\n**Contents:** [Missing](#missing)\n\n## Topic\n",
    "# Reference\n\n**Contents:** [Setup](#setup)\n\n```bash\n## Setup\n```\n",
  ]) {
    await t.test("stale anchor", (caseContext) => {
      const { root, skill } = fixture(caseContext);
      writeText(join(skill, "references/reference.md"), text);
      assert.ok(
        auditSkillStructure(join(root, "plugins")).errors.some((finding) =>
          finding[2].includes("stale Contents anchors"),
        ),
      );
    });
  }
});

test("large unindexed references and oversized skills are reported", async (t) => {
  await t.test("reference advisory", (caseContext) => {
    const { root, skill } = fixture(caseContext);
    const text = "# Reference\n\n" + Array.from({ length: 301 }, () => "detail").join("\n");
    writeText(join(skill, "references/reference.md"), text);
    assert.deepEqual(auditSkillStructure(join(root, "plugins")).missingContents, [
      ["example/example", "reference.md (303 lines)"],
    ]);
  });
  await t.test("skill limit", (caseContext) => {
    const { root, skill } = fixture(caseContext);
    writeText(join(skill, "SKILL.md"), Array.from({ length: 501 }, () => "line").join("\n"));
    assert.ok(
      auditSkillStructure(join(root, "plugins")).errors.some((finding) =>
        finding[2].includes(">500"),
      ),
    );
  });
});

test("cross-plugin links fail everywhere shipped Markdown can appear", async (t) => {
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
          ([label, location, message]) =>
            label === expectedLabel &&
            location === expectedLocation &&
            message.includes("cross-plugin relative link"),
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
