import assert from "node:assert/strict";
import { rmSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { runVersionBumpCheck } from "../dist/version-bumps.js";
import {
  commitAll,
  git,
  initializeGitRepository,
  temporaryDirectory,
  writeJson,
  writeText,
} from "./support.mjs";

function writeManifest(root, version, name = "example") {
  writeJson(join(root, `plugins/${name}/.claude-plugin/plugin.json`), {
    name,
    version,
    description: "Fixture plugin",
  });
}

function writeSkill(root, body, name = "example") {
  writeText(join(root, `plugins/${name}/skills/demo/SKILL.md`), body);
}

function fixture(testContext) {
  const root = temporaryDirectory(testContext);
  initializeGitRepository(root);
  writeManifest(root, "0.1.0");
  writeSkill(root, "baseline body\n");
  writeJson(join(root, "plugins/example/skills/demo/evals/evals.json"), { cases: [] });
  commitAll(root, "baseline");
  return root;
}

function captureCheck(root, base = "main") {
  const stdout = [];
  const stderr = [];
  const status = runVersionBumpCheck(root, base, {
    stdout: (message) => stdout.push(message),
    stderr: (message) => stderr.push(message),
  });
  return { status, stdout: stdout.join("\n"), stderr: stderr.join("\n") };
}

test("shipped content requires a fresh forward version bump", async (t) => {
  await t.test("missing bump", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    writeSkill(root, "edited body\n");
    commitAll(root, "edit skill");
    const result = captureCheck(root);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /content changed, version still 0\.1\.0/u);
  });
  await t.test("fresh bump", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    writeSkill(root, "edited body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "edit and bump");
    const result = captureCheck(root);
    assert.equal(result.status, 0);
    assert.match(result.stdout, /carries a fresh version/u);
  });
  await t.test("backwards bump", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    writeSkill(root, "edited body\n");
    writeManifest(root, "0.0.9");
    commitAll(root, "edit and un-bump");
    const result = captureCheck(root);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /went backwards/u);
  });
});

test("separate Codex package changes require a version bump", (t) => {
  const root = fixture(t);
  writeText(
    join(root, "codex-plugins/example/skills/demo/SKILL.md"),
    "baseline generated body\n",
  );
  commitAll(root, "add generated Codex package");
  git(root, "switch", "-c", "feature");
  writeText(
    join(root, "codex-plugins/example/skills/demo/SKILL.md"),
    "edited generated body\n",
  );
  commitAll(root, "edit generated Codex package");

  const result = captureCheck(root);
  assert.equal(result.status, 1);
  assert.match(result.stdout, /content changed, version still 0\.1\.0/u);
});

test("a version already published on the base branch is rejected", async (t) => {
  await t.test("parallel identical bumps", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    writeSkill(root, "feature body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "feature bump");
    git(root, "switch", "main");
    writeSkill(root, "main body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "main bump");
    git(root, "switch", "feature");
    const result = captureCheck(root);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /absorbed bump/u);
  });
  await t.test("different feature version", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    writeSkill(root, "feature body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "feature bump");
    git(root, "switch", "main");
    writeManifest(root, "0.3.0");
    commitAll(root, "main bump");
    git(root, "switch", "feature");
    assert.equal(captureCheck(root).status, 0);
  });
});

test("non-shipping paths do not require a bump", async (t) => {
  for (const [path, content] of [
    ["plugins/example/skills/demo/evals/evals.json", '{"cases":[1]}\n'],
    ["plugins/example/skills/demo-workspace/notes.md", "scratch\n"],
    ["README.md", "docs only\n"],
  ]) {
    await t.test(path, (caseContext) => {
      const root = fixture(caseContext);
      git(root, "switch", "-c", "feature");
      writeText(join(root, path), content);
      commitAll(root, "non-shipping change");
      assert.equal(captureCheck(root).status, 0);
    });
  }
});

test("adding or removing a whole plugin does not require a bump", async (t) => {
  await t.test("new plugin", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    writeManifest(root, "0.1.0", "fresh");
    writeSkill(root, "new plugin\n", "fresh");
    commitAll(root, "new plugin");
    assert.equal(captureCheck(root).status, 0);
  });
  await t.test("removed plugin", (caseContext) => {
    const root = fixture(caseContext);
    git(root, "switch", "-c", "feature");
    rmSync(join(root, "plugins/example"), { recursive: true });
    commitAll(root, "remove plugin");
    assert.equal(captureCheck(root).status, 0);
  });
});

test("malformed manifests are errors, never silent passes", (t) => {
  const root = fixture(t);
  git(root, "switch", "-c", "feature");
  writeSkill(root, "edited body\n");
  writeText(join(root, "plugins/example/.claude-plugin/plugin.json"), "[]\n");
  commitAll(root, "malformed manifest");
  const result = captureCheck(root);
  assert.equal(result.status, 2);
  assert.match(result.stderr, /manifest must be a JSON object/u);
});

test("the freshest reachable base ref detects absorbed bumps", async (t) => {
  await t.test("origin is ahead", (caseContext) => {
    const root = fixture(caseContext);
    const baseline = git(root, "rev-parse", "HEAD").stdout.trim();
    git(root, "switch", "-c", "feature");
    writeSkill(root, "feature body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "feature bump");
    git(root, "switch", "main");
    writeSkill(root, "main body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "main bump");
    const advanced = git(root, "rev-parse", "HEAD").stdout.trim();
    git(root, "update-ref", "refs/remotes/origin/main", advanced);
    git(root, "switch", "feature");
    git(root, "branch", "-f", "main", baseline);
    const result = captureCheck(root);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /absorbed bump/u);
  });
  await t.test("local is ahead", (caseContext) => {
    const root = fixture(caseContext);
    const baseline = git(root, "rev-parse", "HEAD").stdout.trim();
    git(root, "update-ref", "refs/remotes/origin/main", baseline);
    git(root, "switch", "-c", "feature");
    writeSkill(root, "feature body\n");
    writeManifest(root, "0.2.0");
    commitAll(root, "feature bump");
    git(root, "switch", "main");
    writeManifest(root, "0.2.0");
    commitAll(root, "local main bump");
    git(root, "switch", "feature");
    const result = captureCheck(root);
    assert.equal(result.status, 1);
    assert.match(result.stdout, /absorbed bump/u);
  });
});

test("an unresolvable base reports that verification was skipped", (t) => {
  const root = fixture(t);
  git(root, "switch", "-c", "feature");
  writeSkill(root, "edited body\n");
  commitAll(root, "edit skill");
  const result = captureCheck(root, "not-a-branch");
  assert.equal(result.status, 0);
  assert.match(result.stdout, /SKIPPED/u);
  assert.match(result.stdout, /Nothing was verified/u);
});
