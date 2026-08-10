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
