import assert from "node:assert/strict";
import { join } from "node:path";
import test from "node:test";

import {
  authoredClaudePluginPaths,
  validateAuthoredClaudePlugins,
} from "../dist/index.js";
import { temporaryDirectory, writeJson, writeText } from "./support.mjs";

function fixture(testContext) {
  const root = temporaryDirectory(testContext);
  for (const name of ["zeta", "alpha"]) {
    writeJson(join(root, `plugins/${name}/.claude-plugin/plugin.json`), {
      name,
      version: "0.1.0",
      description: `${name} fixture`,
    });
  }
  writeText(join(root, "plugins/not-authored/README.md"), "# Not Authored\n");
  return root;
}

test("Claude validation covers every authored plugin in stable order", (t) => {
  const root = fixture(t);
  assert.deepEqual(authoredClaudePluginPaths(root), ["plugins/alpha", "plugins/zeta"]);
  const calls = [];
  assert.deepEqual(
    validateAuthoredClaudePlugins(root, (runnerRoot, pluginPath) => {
      calls.push([runnerRoot, pluginPath]);
      return { status: 0 };
    }),
    [],
  );
  assert.deepEqual(calls, [
    [root, "plugins/alpha"],
    [root, "plugins/zeta"],
  ]);
});

test("Claude validation reports command failures and invalid fixtures", (t) => {
  const root = fixture(t);
  const problems = validateAuthoredClaudePlugins(root, (_runnerRoot, pluginPath) =>
    pluginPath === "plugins/alpha" ? { status: 1 } : { status: 0 },
  );
  assert.deepEqual(problems, [
    "[claude-validator] strict validation failed for plugins/alpha (exit 1)",
  ]);
});

test("Claude validation refuses an empty authored-plugin set", (t) => {
  const root = temporaryDirectory(t);
  assert.deepEqual(validateAuthoredClaudePlugins(root, () => ({ status: 0 })), [
    "[claude-validator] no authored Claude plugins were found",
  ]);
});
