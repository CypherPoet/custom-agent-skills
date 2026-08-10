import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { synchronizeVendoredSkills } from "../dist/index.js";
import {
  commitAll,
  initializeGitRepository,
  temporaryDirectory,
  writeCodexPluginManifest,
  writeJson,
  writePluginManifest,
  writeText,
  writeVendoredSkillsConfiguration,
} from "./support.mjs";

function makePlugin(root, name) {
  const fields = { version: "0.1.0", description: `${name} fixture` };
  writePluginManifest(root, name, fields);
  writeCodexPluginManifest(root, name, fields);
}

function fixture(testContext) {
  const root = temporaryDirectory(testContext);
  makePlugin(root, "source");
  makePlugin(root, "bundle");
  writeText(
    join(root, "plugins/source/skills/shared/SKILL.md"),
    "---\nname: shared\ndescription: Shared fixture.\n---\n",
  );
  writeVendoredSkillsConfiguration(root, [
    {
      source: "plugins/source/skills/shared",
      targets: ["plugins/bundle/skills/shared"],
    },
  ]);
  return root;
}

function configuration(root) {
  return JSON.parse(readFileSync(join(root, "vendored-skills.json"), "utf8"));
}

function writeConfiguration(root, value) {
  writeJson(join(root, "vendored-skills.json"), value);
}

test("sync writes vendored skills without rewriting authored manifests", (t) => {
  const root = fixture(t);
  const claudeManifest = readFileSync(
    join(root, "plugins/source/.claude-plugin/plugin.json"),
  );
  const codexManifest = readFileSync(
    join(root, "plugins/source/.codex-plugin/plugin.json"),
  );

  assert.deepEqual(synchronizeVendoredSkills(root, true), []);
  assert.deepEqual(
    readFileSync(join(root, "plugins/bundle/skills/shared/SKILL.md")),
    readFileSync(join(root, "plugins/source/skills/shared/SKILL.md")),
  );
  assert.deepEqual(
    readFileSync(join(root, "plugins/source/.claude-plugin/plugin.json")),
    claudeManifest,
  );
  assert.deepEqual(
    readFileSync(join(root, "plugins/source/.codex-plugin/plugin.json")),
    codexManifest,
  );
  assert.deepEqual(synchronizeVendoredSkills(root, false), []);
});

test("malformed configuration reports without writing", (t) => {
  const root = fixture(t);
  const target = join(root, "plugins/bundle/skills/shared/SKILL.md");
  writeText(join(root, "vendored-skills.json"), "[]\n");
  const problems = synchronizeVendoredSkills(root, true);
  assert.ok(problems.some((problem) => problem.includes("must contain an object")));
  assert.equal(existsSync(target), false);

  writeJson(join(root, "vendored-skills.json"), { skills: null });
  assert.ok(
    synchronizeVendoredSkills(root, true).some((problem) =>
      problem.includes("skills must be an array"),
    ),
  );
  assert.equal(existsSync(target), false);
});

test("vendored drift is detected and repaired", (t) => {
  const root = fixture(t);
  assert.deepEqual(synchronizeVendoredSkills(root, true), []);
  writeText(join(root, "plugins/bundle/skills/shared/SKILL.md"), "hand edited\n");
  assert.ok(
    synchronizeVendoredSkills(root, false).some((problem) => problem.includes("out of sync")),
  );
  assert.deepEqual(synchronizeVendoredSkills(root, true), []);
  assert.deepEqual(synchronizeVendoredSkills(root, false), []);
});

test("vendoring validates every source before writing any target", (t) => {
  const root = fixture(t);
  const target = join(root, "plugins/bundle/skills/shared/SKILL.md");
  writeText(target, "preserve this\n");
  const value = configuration(root);
  value.skills.push({
    source: "plugins/source/skills/missing",
    targets: ["plugins/bundle/skills/missing"],
  });
  writeConfiguration(root, value);

  const problems = synchronizeVendoredSkills(root, true);
  assert.ok(problems.some((problem) => problem.includes("source missing")));
  assert.equal(readFileSync(target, "utf8"), "preserve this\n");
  assert.equal(existsSync(join(root, "plugins/bundle/skills/missing")), false);
});

test("retiring an edge removes clean output and preserves local work", async (t) => {
  await t.test("clean", (caseContext) => {
    const root = fixture(caseContext);
    assert.deepEqual(synchronizeVendoredSkills(root, true), []);
    initializeGitRepository(root);
    commitAll(root, "baseline");
    writeVendoredSkillsConfiguration(root, []);
    assert.ok(
      synchronizeVendoredSkills(root, false).some((problem) =>
        problem.includes("stale generated copy"),
      ),
    );
    assert.deepEqual(synchronizeVendoredSkills(root, true), []);
    assert.equal(existsSync(join(root, "plugins/bundle/skills/shared")), false);
  });

  for (const [name, localPath, content] of [
    ["modified", "plugins/bundle/skills/shared/SKILL.md", "local work\n"],
    ["untracked", "plugins/bundle/skills/shared/evals/evals.json", "{}\n"],
  ]) {
    await t.test(name, (caseContext) => {
      const root = fixture(caseContext);
      assert.deepEqual(synchronizeVendoredSkills(root, true), []);
      initializeGitRepository(root);
      commitAll(root, "baseline");
      writeText(join(root, localPath), content);
      writeVendoredSkillsConfiguration(root, []);
      assert.ok(
        synchronizeVendoredSkills(root, true).some((problem) =>
          problem.includes("refusing to remove"),
        ),
      );
      assert.ok(existsSync(join(root, localPath)));
    });
  }
});

test("gitignored source files are never vendored", (t) => {
  const root = fixture(t);
  initializeGitRepository(root);
  writeText(join(root, ".gitignore"), "*.log\n");
  commitAll(root, "baseline");
  writeText(join(root, "plugins/source/skills/shared/debug.log"), "local junk\n");
  assert.deepEqual(synchronizeVendoredSkills(root, true), []);
  assert.equal(existsSync(join(root, "plugins/bundle/skills/shared/debug.log")), false);
});

test("vendoring rejects undeclared copies, duplicate targets, and chains", async (t) => {
  await t.test("undeclared byte-identical copy", (caseContext) => {
    const root = fixture(caseContext);
    makePlugin(root, "authored");
    writeText(
      join(root, "plugins/authored/skills/shared/SKILL.md"),
      readFileSync(join(root, "plugins/source/skills/shared/SKILL.md"), "utf8"),
    );
    assert.ok(
      synchronizeVendoredSkills(root, false).some((problem) =>
        problem.includes("undeclared byte-identical copy"),
      ),
    );
  });

  await t.test("duplicate target", (caseContext) => {
    const root = fixture(caseContext);
    makePlugin(root, "other");
    writeText(join(root, "plugins/other/skills/other/SKILL.md"), "---\nname: other\n---\n");
    writeVendoredSkillsConfiguration(root, [
      {
        source: "plugins/source/skills/shared",
        targets: ["plugins/bundle/skills/shared"],
      },
      {
        source: "plugins/other/skills/other",
        targets: ["plugins/bundle/skills/shared"],
      },
    ]);
    assert.ok(
      synchronizeVendoredSkills(root, true).some((problem) =>
        problem.includes("duplicate target"),
      ),
    );
  });

  await t.test("vendoring chain", (caseContext) => {
    const root = fixture(caseContext);
    makePlugin(root, "downstream");
    writeVendoredSkillsConfiguration(root, [
      {
        source: "plugins/source/skills/shared",
        targets: ["plugins/bundle/skills/shared"],
      },
      {
        source: "plugins/bundle/skills/shared",
        targets: ["plugins/downstream/skills/shared"],
      },
    ]);
    assert.ok(
      synchronizeVendoredSkills(root, true).some((problem) =>
        problem.includes("vendoring chains"),
      ),
    );
  });
});
