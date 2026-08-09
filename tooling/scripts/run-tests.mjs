import { spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

const repositoryRoot = resolve(import.meta.dirname, "../..");

function run(command, arguments_, environment = process.env) {
  const result = spawnSync(command, arguments_, {
    cwd: repositoryRoot,
    env: environment,
    stdio: "inherit",
  });
  if (result.error !== undefined) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function testFiles(directory) {
  if (!existsSync(directory)) {
    return [];
  }
  return readdirSync(directory, { withFileTypes: true })
    .flatMap((entry) => {
      const path = resolve(directory, entry.name);
      return entry.isDirectory()
        ? testFiles(path)
        : entry.isFile() && entry.name.endsWith(".test.mjs")
          ? [path]
          : [];
    })
    .sort();
}

function pythonCommand() {
  const configured = process.env.PYTHON;
  const candidates = [
    ...(configured === undefined ? [] : [[configured, []]]),
    ["python3", []],
    ["python", []],
    ["py", ["-3"]],
  ];
  for (const [command, prefix] of candidates) {
    const result = spawnSync(command, [...prefix, "--version"], { encoding: "utf8" });
    if (result.status === 0) {
      return { command, prefix };
    }
  }
  throw new Error("Python 3 is required for the plugin-owned Python test suites.");
}

run(process.execPath, [resolve(repositoryRoot, "tooling/scripts/check-build.mjs")]);
const nodeTests = [
  ...testFiles(resolve(repositoryRoot, "tooling/test")),
  ...testFiles(resolve(repositoryRoot, "tests-node")),
];
if (nodeTests.length > 0) {
  run(process.execPath, ["--test", ...nodeTests]);
}

const pythonTests = readdirSync(resolve(repositoryRoot, "tests"))
  .filter((name) => name.startsWith("test_") && name.endsWith(".py"));
if (pythonTests.length > 0) {
  const python = pythonCommand();
  run(python.command, [
    ...python.prefix,
    "-m",
    "unittest",
    "discover",
    "-s",
    "tests",
    "-p",
    "test_*.py",
  ], { ...process.env, PYTHONDONTWRITEBYTECODE: "1" });
}
