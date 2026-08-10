import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

import { directoryIgnored, fileIgnored } from "./file-tree.js";
import { parsePluginVersion } from "./plugin-manifests.js";
import { isJsonObject } from "./types.js";

const manifestPaths = [
  ["Claude", "plugins/{plugin}/.claude-plugin/plugin.json"],
  ["Codex", "plugins/{plugin}/.codex-plugin/plugin.json"],
] as const;

interface CommandResult {
  status: number;
  stdout: string;
  stderr: string;
}

interface GateOutput {
  stdout(message: string): void;
  stderr(message: string): void;
}

const defaultOutput: GateOutput = {
  stdout: (message) => console.log(message),
  stderr: (message) => console.error(message),
};

function git(root: string, arguments_: readonly string[]): CommandResult {
  const result = spawnSync("git", ["-C", root, ...arguments_], {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  return {
    status: result.status ?? 2,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? result.error?.message ?? "",
  };
}

export function shippedPluginForPath(relativePath: string): string | undefined {
  const parts = relativePath.split("/");
  if (parts.length < 3 || parts[0] !== "plugins") {
    return undefined;
  }
  if (parts.slice(2, -1).some(directoryIgnored)) {
    return undefined;
  }
  const filename = parts.at(-1);
  return filename !== undefined && !fileIgnored(filename) ? parts[1] : undefined;
}

function versionGreaterThan(
  left: readonly [number, number, number],
  right: readonly [number, number, number],
): boolean {
  for (let index = 0; index < 3; index += 1) {
    const leftField = left[index];
    const rightField = right[index];
    if (leftField !== rightField) {
      return (leftField ?? 0) > (rightField ?? 0);
    }
  }
  return false;
}

function pluginVersionAt(root: string, reference: string, plugin: string): unknown {
  const versions: Array<{ harness: string; version: unknown }> = [];
  for (const [harness, template] of manifestPaths) {
    const path = template.replace("{plugin}", plugin);
    const result = git(root, ["show", `${reference}:${path}`]);
    if (result.status !== 0) {
      continue;
    }
    let manifest: unknown;
    try {
      manifest = JSON.parse(result.stdout);
    } catch (error) {
      throw new Error(`${path} at ${reference} is malformed: ${String(error)}`);
    }
    if (!isJsonObject(manifest)) {
      throw new Error(`${path} at ${reference} is malformed: manifest must be a JSON object`);
    }
    versions.push({ harness, version: manifest.version });
  }
  if (versions.length === 0) {
    return undefined;
  }
  const first = versions[0];
  if (first === undefined) {
    return undefined;
  }
  for (const entry of versions.slice(1)) {
    if (entry.version !== first.version) {
      throw new Error(
        `plugins/${plugin} at ${reference} has mismatched manifest versions: ` +
          versions.map(({ harness, version }) => `${harness}=${JSON.stringify(version)}`).join(", "),
      );
    }
  }
  return first.version;
}

function resolveBase(root: string, base: string): string {
  const candidates = [base, `origin/${base}`].filter(
    (reference) =>
      git(root, ["rev-parse", "--verify", "--quiet", `${reference}^{commit}`]).status === 0,
  );
  if (candidates.length < 2) {
    return candidates[0] ?? base;
  }
  const local = candidates[0];
  const remote = candidates[1];
  if (local === undefined || remote === undefined) {
    return base;
  }
  return git(root, ["merge-base", "--is-ancestor", local, remote]).status === 0
    ? remote
    : local;
}

function repositoryRoot(start: string): string {
  const result = spawnSync("git", ["-C", start, "rev-parse", "--show-toplevel"], {
    encoding: "utf8",
  });
  return result.status === 0 ? result.stdout.trim() : resolve(start);
}

export function runVersionBumpCheck(
  rootPath: string,
  baseArgument = "main",
  output: GateOutput = defaultOutput,
): number {
  const root = repositoryRoot(rootPath);
  const base = resolveBase(root, baseArgument);
  const mergeBaseResult = git(root, ["merge-base", base, "HEAD"]);
  const mergeBase = mergeBaseResult.stdout.trim();
  if (mergeBaseResult.status !== 0 || mergeBase.length === 0) {
    output.stdout(
      `check-version-bumps — SKIPPED: no merge base for ${base}...HEAD ` +
        `(shallow clone, or ${base} not fetched). Nothing was verified.`,
    );
    return 0;
  }

  const diff = git(root, [
    "diff",
    "--name-only",
    "--no-renames",
    `${base}...HEAD`,
    "--",
    "plugins/",
  ]);
  if (diff.status !== 0) {
    output.stderr(`ERROR: could not diff ${base}...HEAD (${diff.stderr.trim()})`);
    return 2;
  }

  const touched = new Map<string, string[]>();
  for (const line of diff.stdout.split(/\r?\n/u)) {
    const path = line.trim();
    const plugin = shippedPluginForPath(path);
    if (plugin !== undefined) {
      const paths = touched.get(plugin) ?? [];
      paths.push(path);
      touched.set(plugin, paths);
    }
  }

  const problems: Array<{ plugin: string; reason: string }> = [];
  try {
    for (const plugin of Array.from(touched.keys()).sort()) {
      const before = pluginVersionAt(root, mergeBase, plugin);
      const head = pluginVersionAt(root, "HEAD", plugin);
      if (before === undefined || head === undefined) {
        continue;
      }
      const tip = pluginVersionAt(root, base, plugin);
      const beforeParts = parsePluginVersion(before);
      const headParts = parsePluginVersion(head);
      if (headParts === undefined) {
        problems.push({ plugin, reason: `version ${JSON.stringify(head)} is not major.minor.patch` });
      } else if (head === before) {
        problems.push({ plugin, reason: `content changed, version still ${String(before)}` });
      } else if (beforeParts !== undefined && !versionGreaterThan(headParts, beforeParts)) {
        problems.push({ plugin, reason: `version went backwards: ${String(before)} -> ${String(head)}` });
      } else if (head === tip && tip !== before) {
        problems.push({ plugin, reason: `${String(head)} is already published on ${base} (absorbed bump)` });
      }
    }
  } catch (error) {
    output.stderr(`ERROR: ${error instanceof Error ? error.message : String(error)}`);
    return 2;
  }

  if (problems.length === 0) {
    output.stdout(`check-version-bumps — every plugin changed vs ${base} carries a fresh version.`);
    return 0;
  }

  output.stdout(
    `check-version-bumps — ${problems.length} ${problems.length === 1 ? "plugin" : "plugins"} ` +
      "shipping content without a usable bump:\n",
  );
  const width = Math.max(...problems.map(({ plugin }) => plugin.length));
  for (const { plugin, reason } of problems) {
    output.stdout(`  ${plugin.padEnd(width)}  (${reason})`);
  }
  output.stdout(
    "\nBump the version in every platform manifest that the plugin supports, then re-run the check.",
  );
  return 1;
}
