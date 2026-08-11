import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  auditPluginManifests,
  synchronizeVendoredSkills,
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

test("all generated vendored skills and repository gates are clean", () => {
  assert.deepEqual(synchronizeVendoredSkills(root, false), []);
  assert.deepEqual(auditPluginManifests(root).problems, []);
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

test("declared skill eval input files exist within their skill root", () => {
  const paths = git(
    "ls-files",
    "--cached",
    "-z",
    "--",
    "plugins/*/skills/*/evals/evals.json",
  )
    .split("\0")
    .filter(Boolean);
  assert.ok(paths.length > 0);
  for (const path of paths) {
    const fullPath = resolve(root, path);
    const skillRoot = dirname(dirname(fullPath));
    const data = JSON.parse(readFileSync(fullPath, "utf8"));
    for (const evalCase of data.evals ?? []) {
      const label = `${path}: eval ${evalCase.id}`;
      for (const input of evalCase.files ?? []) {
        assert.ok(!isAbsolute(input), `${label}: ${input}`);
        const inputPath = resolve(skillRoot, input);
        const pathFromSkillRoot = relative(skillRoot, inputPath);
        assert.ok(
          pathFromSkillRoot !== ".." &&
            !pathFromSkillRoot.startsWith(`..${sep}`) &&
            !isAbsolute(pathFromSkillRoot),
          `${label}: ${input}`,
        );
        assert.ok(existsSync(inputPath) && statSync(inputPath).isFile(), `${label}: ${input}`);
      }
    }
  }
});

test("manifest presence declares platform support", () => {
  const audit = auditPluginManifests(root);
  assert.deepEqual(audit.problems, []);
  assert.equal(audit.plugins.filter(({ claude }) => claude !== undefined).length, 25);
  assert.equal(audit.plugins.filter(({ codex }) => codex !== undefined).length, 23);
});

test("the package exposes the expected Node contract", () => {
  const packageJson = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  assert.equal(packageJson.name, "@cypherpoet/plugin-sync");
  assert.equal(packageJson.version, "0.2.1");
  assert.equal(
    packageJson.description,
    "Synchronizes vendored skills and checks CypherPoet plugin repositories.",
  );
  assert.equal(packageJson.engines.node, ">=24");
  assert.equal(
    packageJson.bin["cypherpoet-plugin-sync"],
    "tooling/dist/plugin-sync-cli.js",
  );
  assert.equal(
    packageJson.bin["cypherpoet-plugin-version-check"],
    "tooling/dist/version-bumps-cli.js",
  );
  assert.equal(
    packageJson.bin["cypherpoet-repository-test"],
    "tooling/dist/test-runner-cli.js",
  );
  assert.equal(
    packageJson.bin["cypherpoet-skill-structure-check"],
    "tooling/dist/skill-structure-cli.js",
  );
  assert.equal(
    packageJson.bin["cypherpoet-validate-claude-plugins"],
    "tooling/dist/claude-plugin-validation-cli.js",
  );
  assert.equal(packageJson.dependencies, undefined);
  assert.equal(packageJson.devDependencies["@anthropic-ai/claude-code"], "2.1.226");
  assert.equal(packageJson.scripts.prepare, undefined);
  assert.equal(packageJson.scripts.postinstall, undefined);
  assert.ok(existsSync(resolve(root, "package-lock.json")));
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
    "tooling/src/codex-" + "manifest.ts",
    "tooling/src/codex-submission-" + "preflight.ts",
    "plugin-" + "registry.json",
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

test("Codex scaffold preflight is documented as non-authoritative", () => {
  for (const path of ["docs/PLUGIN-CONVENTIONS.md", "tooling/README.md"]) {
    const documentation = readFileSync(join(root, path), "utf8");
    assert.match(documentation, /local `plugin-creator` scaffold preflight/u, path);
    assert.match(documentation, /non-authoritative/u, path);
    assert.doesNotMatch(documentation, /Codex(?:'s)? bundled (?:helper|validator)/u, path);
  }
});
