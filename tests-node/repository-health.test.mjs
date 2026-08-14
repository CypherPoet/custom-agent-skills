import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const root = resolve(import.meta.dirname, "..");

function git(...arguments_) {
  const result = spawnSync("git", ["-C", root, ...arguments_], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}

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

test("the package exposes installable command entry points", () => {
  const packageJson = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  assert.equal(packageJson.name, "@cypherpoet/plugin-sync");
  assert.deepEqual(
    Object.keys(packageJson.bin).sort(),
    [
      "cypherpoet-plugin-sync",
      "cypherpoet-plugin-version-check",
      "cypherpoet-repository-test",
      "cypherpoet-skill-structure-check",
      "cypherpoet-validate-claude-plugins",
    ].sort(),
  );
  for (const [command, path] of Object.entries(packageJson.bin)) {
    assert.equal(typeof path, "string", command);
    assert.ok(existsSync(resolve(root, path)), `${command}: ${path}`);
  }
});
