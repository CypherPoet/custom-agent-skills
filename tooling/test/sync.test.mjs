import assert from "node:assert/strict";
import {
  existsSync,
  readFileSync,
  unlinkSync,
} from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { synchronizePlugins } from "../dist/index.js";
import {
  commitAll,
  initializeGitRepository,
  temporaryDirectory,
  writeJson,
  writePluginManifest,
  writePluginRegistry,
  writeText,
} from "./support.mjs";

function interfaceMetadata(name) {
  return {
    displayName: name[0].toUpperCase() + name.slice(1),
    shortDescription: `Use the ${name} fixture`,
    capabilities: ["Read", "Write"],
    defaultPrompt: [`Use the ${name} fixture for this task.`],
  };
}

function makePlugin(root, name, version = "0.1.0") {
  writePluginManifest(root, name, {
    version,
    description: `${name} fixture`,
    author: { name: "Test" },
    homepage: `https://example.com/${name}`,
  });
}

function writeConfiguration(root, vendoredSkills, pluginNames) {
  writePluginRegistry(
    root,
    vendoredSkills,
    Object.fromEntries(
      pluginNames.map((name) => [
        name,
        {
          category: "Developer Tools",
          interface: interfaceMetadata(name),
        },
      ]),
    ),
  );
}

function fixture(testContext) {
  const root = temporaryDirectory(testContext);
  makePlugin(root, "source");
  makePlugin(root, "bundle");
  writeText(
    join(root, "plugins/source/skills/shared/SKILL.md"),
    "---\nname: shared\ndescription: Shared fixture.\n---\n",
  );
  writeConfiguration(
    root,
    [
      {
        source: "plugins/source/skills/shared",
        targets: ["plugins/bundle/skills/shared"],
      },
    ],
    ["source", "bundle"],
  );
  return root;
}

function configuration(root) {
  return JSON.parse(readFileSync(join(root, "plugin-registry.json"), "utf8"));
}

function writeCurrentConfiguration(root, value) {
  writeJson(join(root, "plugin-registry.json"), value);
}

test("sync writes vendored skills and complete Codex manifests", (t) => {
  const root = fixture(t);
  assert.deepEqual(synchronizePlugins(root, true), []);
  assert.equal(
    readFileSync(join(root, "plugins/bundle/skills/shared/SKILL.md"), "utf8"),
    readFileSync(join(root, "plugins/source/skills/shared/SKILL.md"), "utf8"),
  );
  const manifest = JSON.parse(
    readFileSync(join(root, "plugins/bundle/.codex-plugin/plugin.json"), "utf8"),
  );
  assert.deepEqual(manifest.interface, {
    displayName: "Bundle",
    shortDescription: "Use the bundle fixture",
    longDescription: "bundle fixture",
    developerName: "Test",
    category: "Developer Tools",
    capabilities: ["Read", "Write"],
    websiteURL: "https://example.com/bundle",
    defaultPrompt: ["Use the bundle fixture for this task."],
  });
  assert.ok(existsSync(join(root, "plugin-registry.json")));
  assert.equal(existsSync(join(root, "scripts")), false);
  assert.deepEqual(synchronizePlugins(root, false), []);
});

test("missing optional skills uses the repository default", (t) => {
  const root = fixture(t);
  const manifest = JSON.parse(
    readFileSync(join(root, "plugins/source/.claude-plugin/plugin.json"), "utf8"),
  );
  assert.equal(Object.hasOwn(manifest, "skills"), false);
  assert.deepEqual(synchronizePlugins(root, true), []);
  assert.ok(existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
});

test("sync ignores Claude-only invocation frontmatter and preserves vendored bytes", (t) => {
  const root = fixture(t);
  const skillManifest =
    "---\r\nname: shared\r\ndescription: Shared fixture.\r\n" +
    "disable-model-invocation: true\r\n---\r\n\r\n# Shared\r\n";
  writeText(
    join(root, "plugins/source/skills/shared/SKILL.md"),
    skillManifest,
  );
  writeText(
    join(root, "plugins/source/skills/shared/agents/openai.yaml"),
    "interface:\n  display_name: Shared\n  short_description: Use the shared fixture\n" +
      "policy:\n  allow_implicit_invocation: false\n",
  );

  assert.deepEqual(synchronizePlugins(root, true), []);
  assert.equal(
    readFileSync(join(root, "plugins/source/skills/shared/SKILL.md"), "utf8"),
    skillManifest,
  );
  assert.equal(
    readFileSync(join(root, "plugins/bundle/skills/shared/SKILL.md"), "utf8"),
    skillManifest,
  );
  assert.ok(existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
  assert.ok(existsSync(join(root, "plugins/bundle/.codex-plugin/plugin.json")));
  assert.deepEqual(synchronizePlugins(root, false), []);
});

test("explicit null skills do not inherit the optional default", (t) => {
  const root = fixture(t);
  const manifestPath = join(root, "plugins/source/.claude-plugin/plugin.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  manifest.skills = null;
  writeJson(manifestPath, manifest);
  const problems = synchronizePlugins(root, true);
  assert.ok(problems.some((problem) => problem.includes("skills (custom path)")));
  assert.ok(!existsSync(join(root, "plugins/bundle/.codex-plugin/plugin.json")));
});

test("invalid authored metadata blocks every generated write", async (t) => {
  const cases = [
    ["category", "", "category must be a non-empty string"],
    ["displayName", "", "displayName must be a non-empty string"],
    ["displayName", "x".repeat(31), "displayName must be at most 30"],
    ["displayName", "two\nlines", "displayName must be a single line"],
    ["shortDescription", "x".repeat(31), "shortDescription must be at most 30"],
    ["capabilities", [], "capabilities must contain at least 1"],
    ["capabilities", [{ name: "Read" }], "capabilities[0] must be a non-empty string"],
    ["defaultPrompt", [], "defaultPrompt must contain at least 1"],
    ["defaultPrompt", ["one", "two", "three", "four"], "defaultPrompt must contain at most 3"],
  ];
  for (const [field, value, expected] of cases) {
    await t.test(`${field}: ${expected}`, (caseContext) => {
      const root = fixture(caseContext);
      assert.deepEqual(synchronizePlugins(root, true), []);
      const sourceManifest = join(root, "plugins/source/.codex-plugin/plugin.json");
      const before = readFileSync(sourceManifest);
      const bundleManifest = join(root, "plugins/bundle/.codex-plugin/plugin.json");
      unlinkSync(bundleManifest);

      const registry = configuration(root);
      const metadata = registry.dual_harness_plugins.source;
      if (field === "category") {
        metadata.category = value;
      } else {
        metadata.interface[field] = value;
      }
      writeCurrentConfiguration(root, registry);
      const problems = synchronizePlugins(root, true);
      assert.ok(problems.some((problem) => problem.includes(expected)), problems.join("\n"));
      assert.deepEqual(readFileSync(sourceManifest), before);
      assert.ok(!existsSync(bundleManifest));
    });
  }
});

test("duplicate normalized display names block all manifests", (t) => {
  const root = fixture(t);
  const registry = configuration(root);
  registry.dual_harness_plugins.bundle.interface.displayName = "Ｓｏｕｒｃｅ";
  writeCurrentConfiguration(root, registry);
  const problems = synchronizePlugins(root, true);
  assert.ok(problems.some((problem) => problem.includes("displayName duplicates")));
  assert.ok(!existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
  assert.ok(!existsSync(join(root, "plugins/bundle/.codex-plugin/plugin.json")));
});

test("invalid generated interface sources block all manifests", async (t) => {
  for (const [field, value, expected] of [
    ["description", "x".repeat(1_025), "Claude manifest description must be at most 1024"],
    ["description", "valid\u2028invalid", "Claude manifest description contains unsupported text"],
    ["author", { name: "x".repeat(81) }, "developerName must be at most 80"],
    ["homepage", "http://example.com", "websiteURL must be an absolute https URL"],
  ]) {
    await t.test(field, (caseContext) => {
      const root = fixture(caseContext);
      const path = join(root, "plugins/source/.claude-plugin/plugin.json");
      const manifest = JSON.parse(readFileSync(path, "utf8"));
      manifest[field] = value;
      writeJson(path, manifest);
      const problems = synchronizePlugins(root, true);
      assert.ok(problems.some((problem) => problem.includes(expected)), problems.join("\n"));
      assert.ok(!existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
      assert.ok(!existsSync(join(root, "plugins/bundle/.codex-plugin/plugin.json")));
    });
  }
});

test("one to three starter prompts are emitted unchanged", (t) => {
  const root = fixture(t);
  const prompts = ["First task.", "Second task.", "Third task."];
  const registry = configuration(root);
  registry.dual_harness_plugins.source.interface.defaultPrompt = prompts;
  writeCurrentConfiguration(root, registry);
  assert.deepEqual(synchronizePlugins(root, true), []);
  const manifest = JSON.parse(
    readFileSync(join(root, "plugins/source/.codex-plugin/plugin.json"), "utf8"),
  );
  assert.deepEqual(manifest.interface.defaultPrompt, prompts);
});

test("malformed registry input reports without writing", (t) => {
  const root = fixture(t);
  writeText(join(root, "plugin-registry.json"), "[]\n");
  const problems = synchronizePlugins(root, true);
  assert.ok(problems.some((problem) => problem.includes("must contain an object")));
  assert.ok(!existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
});

test("vendored drift is detected and repaired", (t) => {
  const root = fixture(t);
  assert.deepEqual(synchronizePlugins(root, true), []);
  writeText(
    join(root, "plugins/bundle/skills/shared/SKILL.md"),
    "---\nname: shared\ndescription: Hand-edited.\n---\n",
  );
  assert.ok(synchronizePlugins(root, false).some((problem) => problem.includes("out of sync")));
  assert.deepEqual(synchronizePlugins(root, true), []);
  assert.deepEqual(synchronizePlugins(root, false), []);
});

test("vendoring validates every source before writing any target", (t) => {
  const root = fixture(t);
  const existingTarget =
    "---\nname: shared\ndescription: Preserve this until the plan is valid.\n---\n";
  writeText(join(root, "plugins/bundle/skills/shared/SKILL.md"), existingTarget);
  const registry = configuration(root);
  registry.vendored_skills.push({
    source: "plugins/source/skills/missing",
    targets: ["plugins/bundle/skills/missing"],
  });
  writeCurrentConfiguration(root, registry);

  const problems = synchronizePlugins(root, true);
  assert.ok(problems.some((problem) => problem.includes("source missing")), problems.join("\n"));
  assert.equal(
    readFileSync(join(root, "plugins/bundle/skills/shared/SKILL.md"), "utf8"),
    existingTarget,
  );
  assert.ok(!existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
  assert.ok(!existsSync(join(root, "plugins/bundle/.codex-plugin/plugin.json")));
});

test("retiring a vendored edge deletes clean content but preserves local work", async (t) => {
  await t.test("clean", (caseContext) => {
    const root = fixture(caseContext);
    assert.deepEqual(synchronizePlugins(root, true), []);
    initializeGitRepository(root);
    commitAll(root, "baseline");
    writeConfiguration(root, [], ["source", "bundle"]);
    assert.ok(synchronizePlugins(root, false).some((problem) => problem.includes("stale generated copy")));
    assert.deepEqual(synchronizePlugins(root, true), []);
    assert.ok(!existsSync(join(root, "plugins/bundle/skills/shared")));
  });
  await t.test("modified", (caseContext) => {
    const root = fixture(caseContext);
    assert.deepEqual(synchronizePlugins(root, true), []);
    initializeGitRepository(root);
    commitAll(root, "baseline");
    writeText(
      join(root, "plugins/bundle/skills/shared/SKILL.md"),
      "---\nname: shared\ndescription: Local work.\n---\n",
    );
    writeConfiguration(root, [], ["source", "bundle"]);
    assert.ok(synchronizePlugins(root, true).some((problem) => problem.includes("refusing to remove")));
    assert.ok(existsSync(join(root, "plugins/bundle/skills/shared/SKILL.md")));
  });
  await t.test("untracked ignored directory", (caseContext) => {
    const root = fixture(caseContext);
    assert.deepEqual(synchronizePlugins(root, true), []);
    initializeGitRepository(root);
    commitAll(root, "baseline");
    writeText(join(root, "plugins/bundle/skills/shared/evals/evals.json"), "{}\n");
    writeConfiguration(root, [], ["source", "bundle"]);
    assert.ok(synchronizePlugins(root, true).some((problem) => problem.includes("refusing to remove")));
    assert.ok(existsSync(join(root, "plugins/bundle/skills/shared/evals/evals.json")));
  });
});

test("gitignored local files are never vendored", (t) => {
  const root = fixture(t);
  initializeGitRepository(root);
  writeText(join(root, ".gitignore"), "*.log\n");
  commitAll(root, "baseline");
  writeText(join(root, "plugins/source/skills/shared/debug.log"), "local junk\n");
  assert.deepEqual(synchronizePlugins(root, true), []);
  assert.ok(!existsSync(join(root, "plugins/bundle/skills/shared/debug.log")));
});

test("vendoring rejects undeclared identical copies, duplicate targets, and chains", async (t) => {
  await t.test("undeclared identical copy", (caseContext) => {
    const root = fixture(caseContext);
    makePlugin(root, "authored");
    writeText(
      join(root, "plugins/authored/skills/shared/SKILL.md"),
      readFileSync(join(root, "plugins/source/skills/shared/SKILL.md"), "utf8"),
    );
    writeConfiguration(root, [
      {
        source: "plugins/source/skills/shared",
        targets: ["plugins/bundle/skills/shared"],
      },
    ], ["source", "bundle", "authored"]);
    assert.ok(synchronizePlugins(root, false).some((problem) => problem.includes("undeclared byte-identical copy")));
  });
  await t.test("duplicate target", (caseContext) => {
    const root = fixture(caseContext);
    makePlugin(root, "other");
    writeText(join(root, "plugins/other/skills/other/SKILL.md"), "---\nname: other\n---\n");
    writeConfiguration(root, [
      { source: "plugins/source/skills/shared", targets: ["plugins/bundle/skills/shared"] },
      { source: "plugins/other/skills/other", targets: ["plugins/bundle/skills/shared"] },
    ], ["source", "bundle", "other"]);
    assert.ok(synchronizePlugins(root, true).some((problem) => problem.includes("duplicate target")));
  });
  await t.test("vendoring chain", (caseContext) => {
    const root = fixture(caseContext);
    makePlugin(root, "downstream");
    writeConfiguration(root, [
      { source: "plugins/source/skills/shared", targets: ["plugins/bundle/skills/shared"] },
      { source: "plugins/bundle/skills/shared", targets: ["plugins/downstream/skills/shared"] },
    ], ["source", "bundle", "downstream"]);
    assert.ok(synchronizePlugins(root, true).some((problem) => problem.includes("vendoring chains")));
  });
});

test("Claude-only components block Codex generation", (t) => {
  const root = fixture(t);
  const path = join(root, "plugins/source/.claude-plugin/plugin.json");
  const manifest = JSON.parse(readFileSync(path, "utf8"));
  manifest.agents = "./agents/";
  writeJson(path, manifest);
  const problems = synchronizePlugins(root, true);
  assert.ok(problems.some((problem) => problem.includes("Claude-only components")));
  assert.ok(!existsSync(join(root, "plugins/source/.codex-plugin/plugin.json")));
});
