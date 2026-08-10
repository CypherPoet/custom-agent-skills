import {
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { dirname, isAbsolute, join, posix, relative, resolve, sep } from "node:path";
import { spawnSync, type SpawnSyncReturns } from "node:child_process";

import {
  IGNORED_DIRECTORY_NAMES,
  VENDORED_SKILLS_CONFIGURATION,
} from "./constants.js";
import { isJsonObject, type FileTree, type VendoredSkillsConfiguration } from "./types.js";

function toPosixPath(value: string): string {
  return value.split(sep).join("/");
}

export function directoryIgnored(name: string): boolean {
  return IGNORED_DIRECTORY_NAMES.has(name) || name.endsWith("-workspace");
}

export function fileIgnored(name: string): boolean {
  return name === ".DS_Store" || name.endsWith(".pyc");
}

export function runGit(
  root: string,
  arguments_: readonly string[],
): SpawnSyncReturns<Buffer> | undefined {
  try {
    return spawnSync("git", ["-C", root, ...arguments_], {
      encoding: "buffer",
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch {
    return undefined;
  }
}

export function gitText(root: string, arguments_: readonly string[]): string | undefined {
  const result = runGit(root, arguments_);
  if (result === undefined || result.status !== 0 || result.stdout === null) {
    return undefined;
  }
  return result.stdout.toString("utf8");
}

export function repositoryVisibleFiles(root: string): Set<string> | undefined {
  const result = runGit(root, [
    "ls-files",
    "-z",
    "--cached",
    "--others",
    "--exclude-standard",
  ]);
  if (result === undefined || result.status !== 0 || result.stdout === null) {
    return undefined;
  }
  return new Set(
    result.stdout
      .toString("utf8")
      .split("\0")
      .filter((entry) => entry.length > 0),
  );
}

function walkTree(
  base: string,
  current: string,
  visible: ReadonlySet<string> | undefined,
  files: FileTree,
): void {
  const entries = readdirSync(current, { withFileTypes: true }).sort((left, right) =>
    left.name.localeCompare(right.name, "en"),
  );
  for (const entry of entries) {
    const absolutePath = join(current, entry.name);
    const relativePath = toPosixPath(relative(base, absolutePath));
    if (entry.isDirectory()) {
      if (!directoryIgnored(entry.name)) {
        walkTree(base, absolutePath, visible, files);
      }
      continue;
    }
    if (fileIgnored(entry.name) || (visible !== undefined && !visible.has(relativePath))) {
      continue;
    }
    if (entry.isFile()) {
      files.set(relativePath, readFileSync(absolutePath));
      continue;
    }
    if (entry.isSymbolicLink()) {
      try {
        if (statSync(absolutePath).isFile()) {
          files.set(relativePath, readFileSync(absolutePath));
        }
      } catch {
        // Broken links are not vendorable files.
      }
    }
  }
}

export function readTree(
  base: string,
  visible?: ReadonlySet<string>,
): FileTree {
  const files: FileTree = new Map();
  if (!existsSync(base) || !statSync(base).isDirectory()) {
    return files;
  }
  walkTree(base, base, visible, files);
  return files;
}

export function writeTree(files: ReadonlyMap<string, Buffer>, destination: string): void {
  if (pathExistsOrIsSymbolicLink(destination)) {
    rmSync(destination, { recursive: true, force: true });
  }
  for (const [relativePath, data] of Array.from(files.entries()).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    const target = resolve(destination, relativePath);
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, data);
  }
}

export function fileTreesEqual(
  left: ReadonlyMap<string, Buffer>,
  right: ReadonlyMap<string, Buffer>,
): boolean {
  if (left.size !== right.size) {
    return false;
  }
  for (const [path, data] of left) {
    const other = right.get(path);
    if (other === undefined || !data.equals(other)) {
      return false;
    }
  }
  return true;
}

export function treeDigest(files: ReadonlyMap<string, Buffer>): string {
  const digest = createHash("sha256");
  for (const [relativePath, data] of Array.from(files.entries()).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    const pathBytes = Buffer.from(relativePath, "utf8");
    const pathLength = Buffer.alloc(8);
    pathLength.writeBigUInt64BE(BigInt(pathBytes.length));
    const dataLength = Buffer.alloc(8);
    dataLength.writeBigUInt64BE(BigInt(data.length));
    digest.update(pathLength);
    digest.update(pathBytes);
    digest.update(dataLength);
    digest.update(data);
  }
  return digest.digest("hex");
}

export function validSkillPath(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.includes("\\") ||
    isAbsolute(value)
  ) {
    return false;
  }
  const parts = value.split("/");
  if (
    parts.some((part) => part.length === 0 || part === "." || part === "..") ||
    posix.normalize(value) !== value
  ) {
    return false;
  }
  return (
    (parts.length === 4 && parts[0] === "plugins" && parts[2] === "skills") ||
    (parts.length === 3 &&
      (parts[0] === ".agents" || parts[0] === ".claude") &&
      parts[1] === "skills")
  );
}

export function desiredVendorTargets(
  configuration: VendoredSkillsConfiguration,
): { desired: Map<string, string>; problems: string[] } {
  const desired = new Map<string, string>();
  const problems: string[] = [];
  configuration.skills.forEach((edge, index) => {
    if (!isJsonObject(edge)) {
      problems.push(`[vendor] skills[${index}] must be an object`);
      return;
    }
    const source = edge.source;
    const targets = edge.targets;
    if (!validSkillPath(source)) {
      problems.push(`[vendor] invalid source path: ${JSON.stringify(source)}`);
      return;
    }
    if (!Array.isArray(targets) || targets.length === 0) {
      problems.push(`[vendor] ${source}: targets must be a non-empty array`);
      return;
    }
    for (const target of targets) {
      if (!validSkillPath(target)) {
        problems.push(`[vendor] invalid target path: ${JSON.stringify(target)}`);
        continue;
      }
      if (target === source) {
        problems.push(`[vendor] source and target are identical: ${target}`);
        continue;
      }
      const previousSource = desired.get(target);
      if (previousSource !== undefined) {
        problems.push(
          `[vendor] duplicate target ${target}: declared by ${previousSource} and ${source}`,
        );
        continue;
      }
      desired.set(target, source);
    }
  });

  const sources = new Set(desired.values());
  for (const source of Array.from(sources).sort()) {
    if (desired.has(source)) {
      problems.push(
        `[vendor] vendoring chains are not allowed: source is also a target: ${source}`,
      );
    }
  }
  return { desired, problems };
}

function vendorTargetsAt(root: string, reference: string): Set<string> {
  const text = gitText(root, [
    "show",
    `${reference}:${VENDORED_SKILLS_CONFIGURATION}`,
  ]);
  if (text === undefined) {
    return new Set();
  }
  let configuration: unknown;
  try {
    configuration = JSON.parse(text);
  } catch {
    return new Set();
  }
  if (!isJsonObject(configuration) || !Array.isArray(configuration.skills)) {
    return new Set();
  }
  return new Set(
    desiredVendorTargets(configuration as VendoredSkillsConfiguration).desired.keys(),
  );
}

function vendoringComparisonBase(root: string): string | undefined {
  for (const reference of ["origin/main", "main"]) {
    const mergeBase = gitText(root, ["merge-base", reference, "HEAD"])?.trim();
    if (mergeBase) {
      return mergeBase;
    }
  }
  return gitText(root, ["rev-parse", "HEAD^"])?.trim() || undefined;
}

export function previousVendorTargets(root: string): Set<string> {
  const targets = vendorTargetsAt(root, "HEAD");
  const comparisonBase = vendoringComparisonBase(root);
  if (comparisonBase !== undefined) {
    for (const target of vendorTargetsAt(root, comparisonBase)) {
      targets.add(target);
    }
  }
  return targets;
}

export function gitCleanUnder(root: string, relativePath: string): boolean {
  const result = runGit(root, ["status", "--porcelain", "--", relativePath]);
  return (
    result !== undefined &&
    result.status === 0 &&
    result.stdout !== null &&
    result.stdout.toString("utf8").trim().length === 0
  );
}

export function skillDirectories(root: string): string[] {
  const found: string[] = [];
  const pluginsDirectory = resolve(root, "plugins");
  if (existsSync(pluginsDirectory)) {
    for (const plugin of readdirSync(pluginsDirectory, { withFileTypes: true }).sort((a, b) =>
      a.name.localeCompare(b.name, "en"),
    )) {
      if (!plugin.isDirectory()) {
        continue;
      }
      const skillsDirectory = join(pluginsDirectory, plugin.name, "skills");
      if (!existsSync(skillsDirectory)) {
        continue;
      }
      for (const skill of readdirSync(skillsDirectory, { withFileTypes: true }).sort((a, b) =>
        a.name.localeCompare(b.name, "en"),
      )) {
        if (skill.isDirectory() && !directoryIgnored(skill.name)) {
          found.push(`plugins/${plugin.name}/skills/${skill.name}`);
        }
      }
    }
  }
  for (const family of [".agents", ".claude"]) {
    const skillsDirectory = resolve(root, family, "skills");
    if (!existsSync(skillsDirectory)) {
      continue;
    }
    for (const skill of readdirSync(skillsDirectory, { withFileTypes: true }).sort((a, b) =>
      a.name.localeCompare(b.name, "en"),
    )) {
      if (skill.isDirectory() && !directoryIgnored(skill.name)) {
        found.push(`${family}/skills/${skill.name}`);
      }
    }
  }
  return found;
}

export function baseVisibleFiles(
  visible: ReadonlySet<string> | undefined,
  baseRelative: string,
): Set<string> | undefined {
  if (visible === undefined) {
    return undefined;
  }
  const prefix = `${baseRelative}/`;
  return new Set(
    Array.from(visible)
      .filter((path) => path.startsWith(prefix))
      .map((path) => path.slice(prefix.length)),
  );
}

export function pathIsSymbolicLink(path: string): boolean {
  try {
    return lstatSync(path).isSymbolicLink();
  } catch {
    return false;
  }
}

export function pathExistsOrIsSymbolicLink(path: string): boolean {
  try {
    lstatSync(path);
    return true;
  } catch {
    return false;
  }
}
