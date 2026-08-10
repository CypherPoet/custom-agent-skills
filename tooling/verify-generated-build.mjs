import { spawnSync } from "node:child_process";
import {
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
} from "node:fs";
import { join, relative, resolve } from "node:path";
import { tmpdir } from "node:os";

const repositoryRoot = resolve(import.meta.dirname, "..");
const expectedDirectory = resolve(repositoryRoot, "tooling/dist");
const temporaryRoot = mkdtempSync(join(tmpdir(), "cypherpoet-plugin-sync-build-"));
const actualDirectory = resolve(temporaryRoot, "dist");

function filesUnder(directory) {
  const files = new Map();
  const visit = (current) => {
    for (const entry of readdirSync(current, { withFileTypes: true }).sort((left, right) =>
      left.name.localeCompare(right.name, "en"),
    )) {
      const path = resolve(current, entry.name);
      if (entry.isDirectory()) {
        visit(path);
      } else if (entry.isFile()) {
        files.set(relative(directory, path).split("\\").join("/"), readFileSync(path));
      }
    }
  };
  visit(directory);
  return files;
}

function comparableBytes(path, bytes) {
  if (!path.endsWith(".map")) {
    return bytes;
  }
  const sourceMap = JSON.parse(bytes.toString("utf8"));
  if (Array.isArray(sourceMap.sources)) {
    sourceMap.sources = sourceMap.sources.map((source) => source.split(/[\\/]/u).at(-1));
  }
  return Buffer.from(JSON.stringify(sourceMap), "utf8");
}

try {
  const compiler = resolve(repositoryRoot, "node_modules/typescript/bin/tsc");
  const result = spawnSync(
    process.execPath,
    [compiler, "--project", "tooling/tsconfig.json", "--outDir", actualDirectory],
    { cwd: repositoryRoot, encoding: "utf8" },
  );
  if (result.status !== 0) {
    process.stderr.write(result.stdout);
    process.stderr.write(result.stderr);
    process.exitCode = result.status ?? 1;
  } else {
    const expected = filesUnder(expectedDirectory);
    const actual = filesUnder(actualDirectory);
    const paths = new Set([...expected.keys(), ...actual.keys()]);
    const drift = Array.from(paths)
      .filter((path) => {
        const expectedBytes = expected.get(path);
        const actualBytes = actual.get(path);
        return expectedBytes === undefined ||
          actualBytes === undefined ||
          !comparableBytes(path, expectedBytes).equals(comparableBytes(path, actualBytes));
      })
      .sort();
    if (drift.length > 0) {
      console.error("tooling/dist is stale; run `npm run build`:");
      for (const path of drift) {
        console.error(`  ${path}`);
      }
      process.exitCode = 1;
    } else {
      console.log("plugin sync build: checked (no drift)");
    }
  }
} finally {
  rmSync(temporaryRoot, { recursive: true, force: true });
}
