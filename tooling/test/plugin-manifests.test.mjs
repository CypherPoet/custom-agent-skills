import assert from "node:assert/strict";
import { join } from "node:path";
import test from "node:test";

import { auditPluginManifests } from "../dist/index.js";
import {
  temporaryDirectory,
  writeCodexPluginManifest,
  writePluginManifest,
  writeText,
} from "./support.mjs";

function fields(version = "0.1.0") {
  return { version, description: "Fixture plugin" };
}

test("manifest presence supports Claude-only, Codex-only, and multi-platform plugins", (t) => {
  const root = temporaryDirectory(t);
  writePluginManifest(root, "claude-only", fields());
  writeCodexPluginManifest(root, "codex-only", fields());
  writePluginManifest(root, "both", fields());
  writeCodexPluginManifest(root, "both", fields());

  const audit = auditPluginManifests(root);
  assert.deepEqual(audit.problems, []);
  assert.deepEqual(
    audit.plugins.map(({ name, claude, codex }) => [name, claude !== undefined, codex !== undefined]),
    [
      ["both", true, true],
      ["claude-only", true, false],
      ["codex-only", false, true],
    ],
  );
});

test("every plugin needs at least one platform manifest", (t) => {
  const root = temporaryDirectory(t);
  writeText(join(root, "plugins/empty/README.md"), "empty\n");
  const audit = auditPluginManifests(root);
  assert.ok(audit.problems.some((problem) => problem.includes("needs .claude-plugin")));
});

test("manifest audit reports malformed JSON and non-object values", async (t) => {
  for (const [name, content, expected] of [
    ["invalid-json", "{\n", "not valid JSON"],
    ["non-object", "[]\n", "must contain a JSON object"],
  ]) {
    await t.test(name, (caseContext) => {
      const root = temporaryDirectory(caseContext);
      writeText(join(root, `plugins/${name}/.codex-plugin/plugin.json`), content);
      assert.ok(
        auditPluginManifests(root).problems.some((problem) => problem.includes(expected)),
      );
    });
  }
});

test("manifest audit enforces directory names and major.minor.patch versions", async (t) => {
  await t.test("name", (caseContext) => {
    const root = temporaryDirectory(caseContext);
    writePluginManifest(root, "example", { ...fields(), name: "wrong" });
    assert.ok(
      auditPluginManifests(root).problems.some((problem) =>
        problem.includes("name must equal the plugin directory name"),
      ),
    );
  });
  await t.test("version", (caseContext) => {
    const root = temporaryDirectory(caseContext);
    writePluginManifest(root, "example", fields("v1"));
    assert.ok(
      auditPluginManifests(root).problems.some((problem) =>
        problem.includes("version must use major.minor.patch"),
      ),
    );
  });
});

test("multi-platform manifests share one version", (t) => {
  const root = temporaryDirectory(t);
  writePluginManifest(root, "example", fields("0.1.0"));
  writeCodexPluginManifest(root, "example", fields("0.2.0"));
  assert.ok(
    auditPluginManifests(root).problems.some((problem) => problem.includes("versions must match")),
  );
});

test("Codex skill identities allow 64 characters and reject 65", (t) => {
  const root = temporaryDirectory(t);
  writeCodexPluginManifest(root, "p", fields());
  writeText(
    join(root, "plugins/p/skills/passing-folder/SKILL.md"),
    `---\nname: ${"a".repeat(62)}\ndescription: Passing fixture\n---\n\nPass.\n`,
  );
  writeText(
    join(root, "plugins/p/skills/failing-folder/SKILL.md"),
    `---\nname: ${"b".repeat(63)}\ndescription: Failing fixture\n---\n\nFail.\n`,
  );

  const problems = auditPluginManifests(root).problems;
  assert.equal(problems.length, 1);
  assert.match(problems[0], /Codex skill identity/u);
  assert.ok(problems[0].includes(`p:${"b".repeat(63)}`));
});

test("Codex identity length uses the skill frontmatter name, not its folder", (t) => {
  const root = temporaryDirectory(t);
  writeCodexPluginManifest(root, "frontmatter-check", fields());
  writeText(
    join(root, `plugins/frontmatter-check/skills/${"folder-".repeat(12)}/SKILL.md`),
    "---\nname: short\ndescription: Folder-independent fixture\n---\n\nPass.\n",
  );

  assert.deepEqual(auditPluginManifests(root).problems, []);
});

test("Claude-only plugins are not subject to the Codex identity limit", (t) => {
  const root = temporaryDirectory(t);
  const pluginName = `claude-${"p".repeat(40)}`;
  writePluginManifest(root, pluginName, fields());
  writeText(
    join(root, `plugins/${pluginName}/skills/example/SKILL.md`),
    `---\nname: ${"s".repeat(40)}\ndescription: Claude-only fixture\n---\n\nPass.\n`,
  );

  assert.deepEqual(auditPluginManifests(root).problems, []);
});

test("manifest audit does not enforce a plugin naming style", (t) => {
  const root = temporaryDirectory(t);
  for (const pluginName of ["plain", "focused-kit", "cypherpoet-legacy"]) {
    writeCodexPluginManifest(root, pluginName, fields());
    writeText(
      join(root, `plugins/${pluginName}/skills/example/SKILL.md`),
      "---\nname: example\ndescription: Naming fixture\n---\n\nPass.\n",
    );
  }

  assert.deepEqual(auditPluginManifests(root).problems, []);
});
