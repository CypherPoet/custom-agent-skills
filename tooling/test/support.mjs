import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { tmpdir, devNull } from "node:os";

const gitEnvironment = {
  ...process.env,
  GIT_CONFIG_GLOBAL: devNull,
  GIT_CONFIG_SYSTEM: devNull,
};

export function temporaryDirectory(testContext) {
  const path = mkdtempSync(join(tmpdir(), "plugin-sync-test-"));
  testContext.after(() => rmSync(path, { recursive: true, force: true }));
  return path;
}

export function writeText(path, content) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content, "utf8");
}

export function writeJson(path, value) {
  writeText(path, `${JSON.stringify(value, null, 2)}\n`);
}

export function writePluginManifest(root, name, fields = {}) {
  writeJson(join(root, `plugins/${name}/.claude-plugin/plugin.json`), {
    name,
    ...fields,
  });
}

export function writePluginRegistry(root, vendoredSkills, dualPlugins, claudeOnly = {}) {
  writeJson(join(root, "scripts/plugin-registry.json"), {
    vendored_skills: vendoredSkills,
    dual_harness_plugins: dualPlugins,
    claude_only_plugins: claudeOnly,
  });
}

export function run(command, arguments_, cwd, options = {}) {
  const result = spawnSync(command, arguments_, {
    cwd,
    encoding: "utf8",
    env: options.git ? gitEnvironment : process.env,
  });
  if (options.check !== false && result.status !== 0) {
    throw new Error(
      `${command} ${arguments_.join(" ")} failed (${String(result.status)}):\n${result.stdout}\n${result.stderr}`,
    );
  }
  return result;
}

export function git(root, ...arguments_) {
  return run("git", arguments_, root, { git: true });
}

export function initializeGitRepository(root) {
  git(root, "init", "-b", "main");
  git(root, "config", "user.name", "Test User");
  git(root, "config", "user.email", "test@example.com");
}

export function commitAll(root, message = "fixture") {
  git(root, "add", "-A");
  git(root, "commit", "-m", message);
}
