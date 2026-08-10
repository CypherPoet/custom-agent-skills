import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  rmdirSync,
  statSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

import {
  buildCodexManifest,
  formatCodexManifest,
  readJsonObject,
  unsupportedClaudeComponents,
  validateClaudeManifestForCodex,
} from "./codex-manifest.js";
import {
  normalizedUniquenessKey,
  validateAuthoredRegistryInterface,
  validateGeneratedCodexInterface,
} from "./codex-submission-preflight.js";
import {
  CODEX_PACKAGES_DIRECTORY,
  REGISTRY,
  SYNC_COMMAND,
} from "./constants.js";
import {
  baseVisibleFiles,
  fileTreesEqual,
  gitCleanUnder,
  pathExistsOrIsSymbolicLink,
  pathIsSymbolicLink,
  readTree,
  repositoryVisibleFiles,
  writeTree,
} from "./file-tree.js";
import { prepareSeparateCodexPackage } from "./separate-codex-package.js";
import { isJsonObject, type FileTree, type PluginRegistry } from "./types.js";
import {
  applyVendoredSkillsPlan,
  prepareVendoredSkillsPlan,
} from "./vendored-skills.js";

interface CodexPlan {
  manifests: Map<string, Buffer>;
  packages: Map<string, FileTree>;
  problems: string[];
}

function loadConfiguration(root: string): {
  configuration?: PluginRegistry;
  problems: string[];
} {
  const path = resolve(root, REGISTRY);
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch (error) {
    return { problems: [`[config] could not read ${REGISTRY}: ${String(error)}`] };
  }

  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch (error) {
    return { problems: [`[config] ${REGISTRY} is not valid JSON: ${String(error)}`] };
  }
  if (!isJsonObject(value)) {
    return { problems: [`[config] ${REGISTRY} must contain an object`] };
  }

  const problems: string[] = [];
  if (!Array.isArray(value.vendored_skills)) {
    problems.push("[config] vendored_skills must be an array");
  }
  if (!isJsonObject(value.dual_harness_plugins)) {
    problems.push("[config] dual_harness_plugins must be an object");
  }
  if (!isJsonObject(value.claude_only_plugins)) {
    problems.push("[config] claude_only_plugins must be an object");
  }
  return problems.length === 0
    ? { configuration: value as unknown as PluginRegistry, problems }
    : { problems };
}

function pluginTreeWithPlannedVendoring(
  root: string,
  pluginDirectory: string,
  visible: ReadonlySet<string> | undefined,
  vendoredTargetTrees: ReadonlyMap<string, FileTree>,
): FileTree {
  const pluginRelative = relative(root, pluginDirectory).split("\\").join("/");
  const sourceTree = readTree(
    pluginDirectory,
    baseVisibleFiles(visible, pluginRelative),
  );
  const pluginPrefix = `${pluginRelative}/`;
  for (const [target, targetTree] of vendoredTargetTrees) {
    if (!target.startsWith(pluginPrefix)) {
      continue;
    }
    const relativeTarget = target.slice(pluginPrefix.length);
    const relativeTargetPrefix = `${relativeTarget}/`;
    for (const path of sourceTree.keys()) {
      if (path === relativeTarget || path.startsWith(relativeTargetPrefix)) {
        sourceTree.delete(path);
      }
    }
    for (const [path, data] of targetTree) {
      sourceTree.set(`${relativeTarget}/${path}`, data);
    }
  }
  return sourceTree;
}

function prepareCodexPlan(
  root: string,
  dualPlugins: Record<string, unknown>,
  visible: ReadonlySet<string> | undefined,
  vendoredTargetTrees: ReadonlyMap<string, FileTree>,
): CodexPlan {
  const manifests = new Map<string, Buffer>();
  const packages = new Map<string, FileTree>();
  const problems: string[] = [];

  const displayNameOwners = new Map<string, string>();
  for (const [name, pluginMetadata] of Object.entries(dualPlugins).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    if (!isJsonObject(pluginMetadata) || !isJsonObject(pluginMetadata.interface)) {
      continue;
    }
    const displayName = pluginMetadata.interface.displayName;
    if (typeof displayName !== "string" || displayName.length === 0) {
      continue;
    }
    const key = normalizedUniquenessKey(displayName, true);
    const previousOwner = displayNameOwners.get(key);
    if (previousOwner !== undefined) {
      problems.push(
        `[config] ${name}: interface.displayName duplicates ${previousOwner} after normalization: ` +
          JSON.stringify(displayName),
      );
    } else {
      displayNameOwners.set(key, name);
    }
  }

  for (const [name, pluginMetadata] of Object.entries(dualPlugins).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    const authoredProblems = validateAuthoredRegistryInterface(name, pluginMetadata);
    problems.push(...authoredProblems);

    const pluginDirectory = resolve(root, "plugins", name);
    const manifestRead = readJsonObject(
      join(pluginDirectory, ".claude-plugin", "plugin.json"),
      `[codex-manifest] ${name}`,
    );
    problems.push(...manifestRead.problems);
    if (manifestRead.value === undefined) {
      continue;
    }

    const sourceProblems = validateClaudeManifestForCodex(name, manifestRead.value);
    problems.push(...sourceProblems);
    const unsupported = unsupportedClaudeComponents(pluginDirectory, manifestRead.value);
    if (unsupported.length > 0) {
      problems.push(
        `[codex-manifest] ${name}: Claude-only components (${unsupported.join(", ")}) — ` +
          "the generator does not carry these into .codex-plugin; port them or make the plugin Claude-only",
      );
    }
    if (
      authoredProblems.length > 0 ||
      sourceProblems.length > 0 ||
      unsupported.length > 0 ||
      !isJsonObject(pluginMetadata)
    ) {
      continue;
    }

    const manifest = buildCodexManifest(manifestRead.value, pluginMetadata);
    const interfaceProblems = validateGeneratedCodexInterface(
      manifest.interface,
      manifestRead.value.homepage,
    );
    problems.push(
      ...interfaceProblems.map((problem) => `[codex-manifest] ${name}: ${problem}`),
    );
    if (interfaceProblems.length > 0) {
      continue;
    }

    const manifestBytes = formatCodexManifest(manifest);
    if (pluginMetadata.separateCodexPackage === true) {
      const sourceTree = pluginTreeWithPlannedVendoring(
        root,
        pluginDirectory,
        visible,
        vendoredTargetTrees,
      );
      const prepared = prepareSeparateCodexPackage(
        name,
        sourceTree,
        manifestBytes,
      );
      problems.push(...prepared.problems);
      if (prepared.packageTree !== undefined) {
        packages.set(resolve(root, CODEX_PACKAGES_DIRECTORY, name), prepared.packageTree);
      }
    } else {
      manifests.set(resolve(pluginDirectory, ".codex-plugin", "plugin.json"), manifestBytes);
    }
  }
  return { manifests, packages, problems };
}

function applyCodexPlan(
  root: string,
  plan: CodexPlan,
  separatePackagePlugins: ReadonlySet<string>,
  claudeOnlyPlugins: ReadonlySet<string>,
  existingPlugins: ReadonlySet<string>,
  write: boolean,
  visible: ReadonlySet<string> | undefined,
): string[] {
  const problems: string[] = [];
  for (const [path, desiredBytes] of Array.from(plan.manifests.entries()).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    if (write) {
      mkdirSync(dirname(path), { recursive: true });
      writeFileSync(path, desiredBytes);
    } else if (!existsSync(path) || !readFileSync(path).equals(desiredBytes)) {
      problems.push(
        `[codex-manifest] out of sync: ${relative(root, path)} (run: ${SYNC_COMMAND})`,
      );
    }
  }

  for (const [path, desiredTree] of Array.from(plan.packages.entries()).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    const relativePath = relative(root, path).split("\\").join("/");
    if (write) {
      writeTree(desiredTree, path);
    } else if (
      !fileTreesEqual(readTree(path, baseVisibleFiles(visible, relativePath)), desiredTree)
    ) {
      problems.push(`[codex-package] out of sync: ${relativePath} (run: ${SYNC_COMMAND})`);
    }
  }

  for (const name of Array.from(separatePackagePlugins)
    .filter((value) => existingPlugins.has(value))
    .sort()) {
    const staleManifest = resolve(root, "plugins", name, ".codex-plugin", "plugin.json");
    if (!pathExistsOrIsSymbolicLink(staleManifest)) {
      continue;
    }
    const relativePath = relative(root, staleManifest).split("\\").join("/");
    if (!write) {
      problems.push(
        `[codex-package] stale in-place Codex manifest: ${relativePath} (run: ${SYNC_COMMAND})`,
      );
    } else if (pathIsSymbolicLink(staleManifest) || !statSync(staleManifest).isFile()) {
      problems.push(`[codex-package] refusing to remove non-file generated path: ${relativePath}`);
    } else {
      unlinkSync(staleManifest);
      try {
        rmdirSync(dirname(staleManifest));
      } catch {
        // The directory may contain non-generated files.
      }
    }
  }

  const packagesRoot = resolve(root, CODEX_PACKAGES_DIRECTORY);
  const existingPackageNames = existsSync(packagesRoot)
    ? new Set(
        readdirSync(packagesRoot, { withFileTypes: true })
          .filter((entry) => entry.isDirectory() || entry.isSymbolicLink())
          .map((entry) => entry.name),
      )
    : new Set<string>();
  for (const name of Array.from(existingPackageNames)
    .filter((value) => !separatePackagePlugins.has(value))
    .sort()) {
    const stale = resolve(packagesRoot, name);
    const relativePath = relative(root, stale).split("\\").join("/");
    if (!write) {
      problems.push(
        `[codex-package] stale generated package: ${relativePath} (run: ${SYNC_COMMAND})`,
      );
    } else if (
      pathIsSymbolicLink(stale) ||
      !statSync(stale).isDirectory() ||
      !gitCleanUnder(root, relativePath)
    ) {
      problems.push(`[codex-package] refusing to remove modified generated path: ${relativePath}`);
    } else {
      rmSync(stale, { recursive: true });
    }
  }

  for (const name of Array.from(claudeOnlyPlugins)
    .filter((value) => existingPlugins.has(value))
    .sort()) {
    const stale = resolve(root, "plugins", name, ".codex-plugin");
    if (!pathExistsOrIsSymbolicLink(stale)) {
      continue;
    }
    if (write) {
      rmSync(stale, { recursive: true, force: true });
    } else {
      problems.push(
        `[codex-manifest] stale .codex-plugin/ for Claude-only plugin ${name} ` +
          `(run: ${SYNC_COMMAND})`,
      );
    }
  }
  return problems;
}

export function synchronizePlugins(rootPath: string, write: boolean): string[] {
  const root = resolve(rootPath);
  const loaded = loadConfiguration(root);
  if (loaded.configuration === undefined) {
    return loaded.problems;
  }
  const configuration = loaded.configuration;
  const problems: string[] = [];
  const pluginsDirectory = resolve(root, "plugins");
  if (!existsSync(pluginsDirectory) || !statSync(pluginsDirectory).isDirectory()) {
    return ["[config] plugins directory is missing"];
  }

  const existingPlugins = new Set(
    readdirSync(pluginsDirectory, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name),
  );
  const dualPlugins = configuration.dual_harness_plugins;
  const dualPluginNames = new Set(Object.keys(dualPlugins));
  const claudeOnlyPlugins = new Set(Object.keys(configuration.claude_only_plugins));

  for (const name of Array.from(dualPluginNames)
    .filter((value) => claudeOnlyPlugins.has(value))
    .sort()) {
    problems.push(`[config] ${name} is listed as both dual-harness and Claude-only`);
  }
  for (const name of Array.from(new Set([...dualPluginNames, ...claudeOnlyPlugins])).sort()) {
    if (!existingPlugins.has(name)) {
      problems.push(`[config] ${name} is classified but no plugins/${name}/ exists`);
    }
  }
  for (const name of Array.from(existingPlugins).sort()) {
    if (!dualPluginNames.has(name) && !claudeOnlyPlugins.has(name)) {
      problems.push(
        `[config] plugins/${name}/ is unclassified — add it to dual_harness_plugins or claude_only_plugins`,
      );
    }
  }

  const visible = repositoryVisibleFiles(root);
  const vendorPlan = prepareVendoredSkillsPlan(root, configuration, write, visible);
  problems.push(...vendorPlan.problems);

  const plan = prepareCodexPlan(root, dualPlugins, visible, vendorPlan.targetTrees);
  problems.push(...plan.problems);

  if ((write && problems.length === 0) || (!write && plan.problems.length === 0)) {
    const separatePackagePlugins = new Set(
      Object.entries(dualPlugins)
        .filter(
          ([, metadata]) =>
            isJsonObject(metadata) && metadata.separateCodexPackage === true,
        )
        .map(([name]) => name),
    );
    if (write) {
      applyVendoredSkillsPlan(root, vendorPlan);
    }
    problems.push(
      ...applyCodexPlan(
        root,
        plan,
        separatePackagePlugins,
        claudeOnlyPlugins,
        existingPlugins,
        write,
        visible,
      ),
    );
  }
  return problems;
}

export function findRepositoryRoot(start: string): string {
  let candidate = resolve(start);
  for (;;) {
    if (
      existsSync(resolve(candidate, "plugins")) &&
      existsSync(resolve(candidate, REGISTRY))
    ) {
      return candidate;
    }
    const parent = dirname(candidate);
    if (parent === candidate) {
      throw new Error(`could not locate repo root (needs plugins/ and ${REGISTRY})`);
    }
    candidate = parent;
  }
}
