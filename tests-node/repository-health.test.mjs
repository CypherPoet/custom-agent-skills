import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  buildCodexManifest,
  codexPluginRelativePath,
  synchronizePlugins,
  validateCodexInterface,
} from "../tooling/dist/index.js";
import { runSkillStructureCheck } from "../tooling/dist/skill-structure.js";
import { runVersionBumpCheck } from "../tooling/dist/version-bumps.js";

const root = resolve(import.meta.dirname, "..");
const discardOutput = { stdout() {}, stderr() {} };

function git(...arguments_) {
  const result = spawnSync("git", ["-C", root, ...arguments_], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}

test("all generated packages and repository gates are clean", () => {
  assert.deepEqual(synchronizePlugins(root, false), []);
  assert.equal(runSkillStructureCheck(root, true, discardOutput), 0);
  assert.equal(runVersionBumpCheck(root, "main", discardOutput), 0);
});

test("every tracked JSON file parses", () => {
  const paths = git("ls-files", "--cached", "-z", "--", "*.json")
    .split("\0")
    .filter(Boolean);
  assert.ok(paths.length > 0);
  for (const path of paths) {
    const fullPath = resolve(root, path);
    if (existsSync(fullPath)) {
      assert.doesNotThrow(() => JSON.parse(readFileSync(fullPath, "utf8")), path);
    }
  }
});

test("Claude manifests own valid package identity and versions", () => {
  const pluginNames = readdirSync(resolve(root, "plugins"), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);
  assert.ok(pluginNames.length > 0);
  for (const name of pluginNames) {
    const path = resolve(root, "plugins", name, ".claude-plugin", "plugin.json");
    const manifest = JSON.parse(readFileSync(path, "utf8"));
    assert.equal(manifest.name, name, path);
    assert.ok(manifest.description, path);
    assert.match(manifest.version ?? "", /^\d+\.\d+\.\d+$/u, path);
  }
});

test("every Codex interface is composed from the two authored sources", () => {
  const registry = JSON.parse(readFileSync(resolve(root, "scripts/plugin-registry.json"), "utf8"));
  for (const [name, metadata] of Object.entries(registry.dual_harness_plugins)) {
    const pluginRoot = resolve(root, "plugins", name);
    const claudeManifest = JSON.parse(
      readFileSync(resolve(pluginRoot, ".claude-plugin/plugin.json"), "utf8"),
    );
    const codexManifest = JSON.parse(
      readFileSync(
        resolve(root, codexPluginRelativePath(name, metadata), ".codex-plugin/plugin.json"),
        "utf8",
      ),
    );
    assert.deepEqual(codexManifest, buildCodexManifest(claudeManifest, metadata), name);
    assert.deepEqual(
      validateCodexInterface(codexManifest.interface, { sourceHomepage: claudeManifest.homepage }),
      [],
      name,
    );
  }
});

test("the package exposes the frozen 0.1.0 Node contract", () => {
  const packageJson = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  assert.equal(packageJson.name, "@cypherpoet/plugin-sync");
  assert.equal(packageJson.version, "0.1.0");
  assert.equal(
    packageJson.description,
    "Generates and validates Codex packages and vendored skills for CypherPoet dual-harness plugin repositories.",
  );
  assert.equal(packageJson.engines.node, ">=24");
  assert.equal(packageJson.bin["cypherpoet-plugin-sync"], "tooling/dist/cli.js");
  assert.equal(
    packageJson.bin["cypherpoet-plugin-version-check"],
    "tooling/dist/version-bumps-cli.js",
  );
  assert.equal(
    packageJson.bin["cypherpoet-skill-structure-check"],
    "tooling/dist/skill-structure-cli.js",
  );
  assert.equal(packageJson.dependencies.yaml, "^2.9.0");
  assert.equal(packageJson.scripts.prepare, undefined);
  assert.equal(packageJson.scripts.postinstall, undefined);
  assert.ok(existsSync(resolve(root, "package-lock.json")));
  assert.ok(existsSync(resolve(root, "tooling/dist/cli.js")));
});

test("the retired Python tooling contract has no files or tracked references", () => {
  for (const path of [
    "requirements-" + "tooling.txt",
    "scripts/check_" + "version_bumps.py",
    "scripts/sync" + "_plugins.py",
    "tooling/setup.cfg",
    "tooling/setup.py",
    "tooling/pyproject.toml",
    "tooling/src/cypherpoet_agent_skills_" + "tooling",
  ]) {
    assert.ok(!existsSync(resolve(root, path)), path);
  }
  for (const needle of [
    "cypherpoet_agent_skills_" + "tooling",
    "cypherpoet-" + "sync-plugins",
    "requirements-" + "tooling.txt",
    "scripts/sync" + "_plugins.py",
  ]) {
    const result = spawnSync("git", ["-C", root, "grep", "-l", "--fixed-strings", needle], {
      encoding: "utf8",
    });
    assert.equal(result.status, 1, `${needle}:\n${result.stdout}`);
  }
});

test("the README keeps installation instructions with each plugin", () => {
  const readme = readFileSync(join(root, "README.md"), "utf8");
  assert.match(readme, /^## Prerequisites$/mu);
  assert.match(readme, /npm ci/u);
  assert.doesNotMatch(readme, /^## Installation$/mu);
});
