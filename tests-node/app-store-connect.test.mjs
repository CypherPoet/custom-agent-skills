import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = fileURLToPath(new URL("../", import.meta.url));
const packagePath = resolve(root, "plugins/app-store-connect-kit/skills/app-store-connect-submission/scripts");

test("App Store Connect offline Swift regressions and credential-free CLI preflight", {
  skip: process.platform !== "darwin" ? "Apple frameworks require macOS; covered by the macOS CI job" : false,
  timeout: 180_000,
}, () => {
  const temporary = mkdtempSync(join(tmpdir(), "asc-offline-"));
  try {
    const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("ASC_") && key !== "API_PRIVATE_KEYS_DIR"));
    env.CLANG_MODULE_CACHE_PATH = join(temporary, "modules");
    env.SWIFTPM_MODULECACHE_OVERRIDE = env.CLANG_MODULE_CACHE_PATH;
    const build = join(temporary, "build");
    const result = spawnSync("/usr/bin/xcrun", [
      "swift", "test", "--package-path", packagePath, "--scratch-path", build,
      "--cache-path", join(temporary, "cache"), "--disable-sandbox",
    ], { cwd: temporary, env, encoding: "utf8", timeout: 150_000 });
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(result.status, 0, result.stdout + result.stderr);
    const executable = join(build, "debug", "asc");
    for (const args of [["--help"], ["get", "--help"]]) {
      const help = spawnSync(executable, args, { cwd: temporary, env, encoding: "utf8" });
      assert.equal(help.status, 0, help.stderr);
      assert.match(help.stdout, /Exit 0: confirmed success/);
    }
    const unsafe = spawnSync(executable, ["get", "https://example.invalid/"], { cwd: temporary, env, encoding: "utf8" });
    assert.equal(unsafe.status, 1);
    assert.match(unsafe.stderr, /HTTPS App Store Connect API origin/);
    assert.doesNotMatch(unsafe.stderr, /Missing ASC_/);
    const missingTarget = spawnSync(executable, ["build-status"], { cwd: temporary, env, encoding: "utf8" });
    assert.equal(missingTarget.status, 1);
    assert.match(missingTarget.stderr, /Explicit --app-id is required/);
  } finally {
    rmSync(temporary, { recursive: true, force: true });
  }
});
