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

import { parseDocument } from "yaml";

import {
  CODEX_MANIFEST_CARRY,
  CODEX_PACKAGES_DIRECTORY,
  PLUGIN_DESCRIPTION_MAX_LENGTH,
  REGISTRY,
  SYNC_COMMAND,
} from "./constants.js";
import {
  baseVisibleFiles,
  desiredVendorTargets,
  fileTreesEqual,
  gitCleanUnder,
  pathExistsOrIsSymbolicLink,
  pathIsSymbolicLink,
  previousVendorTargets,
  readTree,
  repositoryVisibleFiles,
  skillDirectories,
  treeDigest,
  writeTree,
} from "./file-tree.js";
import {
  normalizedUniquenessKey,
  validateAuthoredInterfaceMetadata,
  validateCodexInterface,
  validateText,
} from "./interface-contract.js";
import {
  isJsonObject,
  type FileTree,
  type JsonObject,
  type PluginRegistry,
} from "./types.js";

const decoder = new TextDecoder("utf-8", { fatal: true });
const claudeInvocationField = /^(disable-model-invocation|disable_model_invocation):[ \t]*(true|false|yes|no|on|off|1|0)[ \t]*(?:#.*)?(?:\r?\n)?$/iu;
const claudeInvocationFieldPrefix = /^(disable-model-invocation|disable_model_invocation):/iu;
const yamlTrueValues = new Set(["true", "yes", "on", "1"]);

interface CodexPlan {
  manifests: Map<string, Buffer>;
  packages: Map<string, FileTree>;
  problems: string[];
}

function formatJson(value: JsonObject): string {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function readJsonObject(path: string, label: string): { value?: JsonObject; problems: string[] } {
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch (error) {
    return { problems: [`${label}: could not read JSON: ${String(error)}`] };
  }

  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch (error) {
    return { problems: [`${label}: invalid JSON: ${String(error)}`] };
  }
  if (!isJsonObject(value)) {
    return { problems: [`${label}: JSON must contain an object`] };
  }
  return { value, problems: [] };
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
    ? { configuration: value as PluginRegistry, problems }
    : { problems };
}

export function buildCodexManifest(
  claudeManifest: JsonObject,
  pluginMetadata: JsonObject,
): JsonObject {
  const authoredInterface = pluginMetadata.interface;
  if (!isJsonObject(authoredInterface)) {
    throw new TypeError("plugin metadata needs an interface object");
  }
  const author = claudeManifest.author;
  if (!isJsonObject(author)) {
    throw new TypeError("Claude manifest needs an author object");
  }

  const manifest: JsonObject = {
    name: claudeManifest.name,
    version: claudeManifest.version,
    description: claudeManifest.description,
  };
  for (const key of CODEX_MANIFEST_CARRY) {
    if (Object.hasOwn(claudeManifest, key)) {
      manifest[key] = claudeManifest[key];
    }
  }
  manifest.skills = "./skills/";
  manifest.interface = {
    displayName: authoredInterface.displayName,
    shortDescription: authoredInterface.shortDescription,
    longDescription: claudeManifest.description,
    developerName: author.name,
    category: pluginMetadata.category,
    capabilities: authoredInterface.capabilities,
    websiteURL: claudeManifest.homepage,
    defaultPrompt: authoredInterface.defaultPrompt,
  };
  return manifest;
}

export function codexPluginRelativePath(name: string, pluginMetadata: unknown): string {
  return isJsonObject(pluginMetadata) && pluginMetadata.codexProjection === true
    ? `${CODEX_PACKAGES_DIRECTORY}/${name}`
    : `plugins/${name}`;
}

function validateClaudeManifestShape(name: string, claudeManifest: JsonObject): string[] {
  const prefix = `[codex-manifest] ${name}: `;
  const problems: string[] = [];
  for (const field of ["name", "version", "homepage"] as const) {
    const value = claudeManifest[field];
    if (typeof value !== "string" || value.trim().length === 0) {
      problems.push(`${prefix}Claude manifest needs non-empty ${field}`);
    }
  }
  problems.push(
    ...validateText(
      claudeManifest.description,
      "Claude manifest description",
      PLUGIN_DESCRIPTION_MAX_LENGTH,
      true,
    ).map((problem) => `${prefix}${problem}`),
  );
  if (typeof claudeManifest.name === "string" && claudeManifest.name !== name) {
    problems.push(`${prefix}Claude manifest name must equal the plugin directory name`);
  }
  const author = claudeManifest.author;
  if (!isJsonObject(author) || typeof author.name !== "string" || author.name.trim().length === 0) {
    problems.push(`${prefix}Claude manifest needs non-empty author.name`);
  }
  return problems;
}

function unportedComponents(pluginDirectory: string, claudeManifest: JsonObject): string[] {
  const unported = ["mcpServers", "hooks", "agents", "commands"].filter((key) =>
    Object.hasOwn(claudeManifest, key),
  );
  const skillsValue = claudeManifest.skills ?? "./skills/";
  if (
    typeof skillsValue !== "string" ||
    skillsValue.replace(/^\.\//u, "").replace(/\/$/u, "") !== "skills"
  ) {
    unported.push("skills (custom path)");
  }
  for (const component of ["commands", "agents", "hooks"]) {
    const componentPath = join(pluginDirectory, component);
    if (
      existsSync(componentPath) &&
      statSync(componentPath).isDirectory() &&
      !unported.includes(component)
    ) {
      unported.push(`${component}/ (auto-discovered)`);
    }
  }
  if (existsSync(join(pluginDirectory, ".mcp.json")) && !unported.includes("mcpServers")) {
    unported.push(".mcp.json");
  }
  return unported;
}

function stripClaudeInvocationField(
  skillManifest: Buffer,
  label: string,
): { transformed?: Buffer; manualOnly: boolean; problems: string[] } {
  let text: string;
  try {
    text = decoder.decode(skillManifest);
  } catch (error) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md is not UTF-8: ${String(error)}`],
    };
  }
  if (!text.startsWith("---\n")) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md must start with YAML frontmatter`],
    };
  }

  const lines = text.match(/.*(?:\r?\n|$)/gu)?.filter((line) => line.length > 0) ?? [];
  const frontmatterEnd = lines.findIndex(
    (line, index) => index > 0 && line.replace(/\r?\n$/u, "") === "---",
  );
  if (frontmatterEnd < 0) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md frontmatter is not closed`],
    };
  }

  const matches: Array<{ index: number; manualOnly: boolean }> = [];
  const problems: string[] = [];
  for (let index = 1; index < frontmatterEnd; index += 1) {
    const line = lines[index];
    if (line === undefined) {
      continue;
    }
    const match = claudeInvocationField.exec(line);
    if (match !== null) {
      matches.push({
        index,
        manualOnly: yamlTrueValues.has(match[2]?.toLowerCase() ?? ""),
      });
    } else if (claudeInvocationFieldPrefix.test(line)) {
      problems.push(
        `[codex-package] ${label}: Claude invocation field must use a YAML boolean`,
      );
    }
  }
  if (matches.length > 1) {
    problems.push(`[codex-package] ${label}: Claude invocation field is duplicated`);
  }
  if (problems.length > 0) {
    return { manualOnly: false, problems };
  }
  const match = matches[0];
  if (match === undefined) {
    return { transformed: skillManifest, manualOnly: false, problems: [] };
  }
  lines.splice(match.index, 1);
  return {
    transformed: Buffer.from(lines.join(""), "utf8"),
    manualOnly: match.manualOnly,
    problems: [],
  };
}

function codexManualOnlyPolicyProblem(agentManifest: Buffer): string | undefined {
  let text: string;
  try {
    text = decoder.decode(agentManifest);
  } catch {
    return "agents/openai.yaml must be UTF-8";
  }

  const document = parseDocument(text, { uniqueKeys: true });
  if (document.errors.length > 0) {
    const error = document.errors[0];
    const detail = error?.code === "DUPLICATE_KEY" ? "found duplicate key" : error?.message;
    return `agents/openai.yaml is invalid: ${detail ?? "YAML parsing failed"}`;
  }
  const configuration: unknown = document.toJS();
  if (!isJsonObject(configuration)) {
    return "agents/openai.yaml must contain a mapping";
  }
  const policy = configuration.policy;
  if (!isJsonObject(policy)) {
    return "agents/openai.yaml must contain a policy mapping";
  }
  if (policy.allow_implicit_invocation !== false) {
    return "policy.allow_implicit_invocation must be the boolean false";
  }
  return undefined;
}

function prepareCodexPackage(
  root: string,
  name: string,
  pluginDirectory: string,
  manifestBytes: Buffer,
  visible: ReadonlySet<string> | undefined,
): { packageTree?: FileTree; problems: string[] } {
  const pluginRelative = relative(root, pluginDirectory).split("\\").join("/");
  const sourceTree = readTree(pluginDirectory, baseVisibleFiles(visible, pluginRelative));
  const packageTree: FileTree = new Map(
    Array.from(sourceTree).filter(
      ([path]) => !path.startsWith(".claude-plugin/") && path !== ".codex-plugin/plugin.json",
    ),
  );
  packageTree.set(".codex-plugin/plugin.json", manifestBytes);

  const manualOnlySkills: string[] = [];
  const problems: string[] = [];
  for (const [path, data] of Array.from(packageTree.entries()).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    const parts = path.split("/");
    if (parts.length !== 3 || parts[0] !== "skills" || parts[2] !== "SKILL.md") {
      continue;
    }
    const skillName = parts[1];
    if (skillName === undefined) {
      continue;
    }
    const transformed = stripClaudeInvocationField(data, `${name}/${skillName}`);
    problems.push(...transformed.problems);
    if (transformed.transformed !== undefined) {
      packageTree.set(path, transformed.transformed);
    }
    if (transformed.manualOnly) {
      manualOnlySkills.push(skillName);
    }
  }

  if (manualOnlySkills.length === 0 && problems.length === 0) {
    problems.push(
      `[codex-package] ${name}: codexPackage requires at least one Claude-only disable-model-invocation field`,
    );
  }
  for (const skillName of manualOnlySkills) {
    const agentPath = `skills/${skillName}/agents/openai.yaml`;
    const agentManifest = packageTree.get(agentPath);
    const policyProblem =
      agentManifest === undefined
        ? "agents/openai.yaml is missing"
        : codexManualOnlyPolicyProblem(agentManifest);
    if (policyProblem !== undefined) {
      problems.push(
        `[codex-package] ${name}/${skillName}: removing Claude's manual-only field requires ` +
          `policy.allow_implicit_invocation: false in agents/openai.yaml (${policyProblem})`,
      );
    }
  }
  return problems.length === 0 ? { packageTree, problems } : { problems };
}

function prepareCodexPlan(
  root: string,
  dualPlugins: Record<string, unknown>,
  visible: ReadonlySet<string> | undefined,
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
        `[config] ${name}: interface.displayName duplicates ${previousOwner} after normalization: ${JSON.stringify(displayName)}`,
      );
    } else {
      displayNameOwners.set(key, name);
    }
  }

  for (const [name, pluginMetadata] of Object.entries(dualPlugins).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    const pluginProblems = validateAuthoredInterfaceMetadata(name, pluginMetadata);
    problems.push(...pluginProblems);

    const pluginDirectory = resolve(root, "plugins", name);
    const manifestRead = readJsonObject(
      join(pluginDirectory, ".claude-plugin", "plugin.json"),
      `[codex-manifest] ${name}`,
    );
    problems.push(...manifestRead.problems);
    if (manifestRead.value === undefined) {
      continue;
    }

    const shapeProblems = validateClaudeManifestShape(name, manifestRead.value);
    problems.push(...shapeProblems);
    const unported = unportedComponents(pluginDirectory, manifestRead.value);
    if (unported.length > 0) {
      problems.push(
        `[codex-manifest] ${name}: Claude-only components (${unported.join(", ")}) — ` +
          "the generator does not carry these into .codex-plugin; port them or make the plugin Claude-only",
      );
    }
    if (
      pluginProblems.length > 0 ||
      manifestRead.problems.length > 0 ||
      shapeProblems.length > 0 ||
      unported.length > 0 ||
      !isJsonObject(pluginMetadata)
    ) {
      continue;
    }

    const manifest = buildCodexManifest(manifestRead.value, pluginMetadata);
    const interfaceProblems = validateCodexInterface(manifest.interface, {
      sourceHomepage: manifestRead.value.homepage,
    });
    problems.push(
      ...interfaceProblems.map((problem) => `[codex-manifest] ${name}: ${problem}`),
    );
    if (interfaceProblems.length > 0) {
      continue;
    }

    const manifestBytes = Buffer.from(formatJson(manifest), "utf8");
    if (pluginMetadata.codexProjection === true) {
      const prepared = prepareCodexPackage(
        root,
        name,
        pluginDirectory,
        manifestBytes,
        visible,
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

function synchronizeVendoredSkills(
  root: string,
  configuration: PluginRegistry,
  write: boolean,
  visible: ReadonlySet<string> | undefined,
): string[] {
  const { desired: desiredTargets, problems } = desiredVendorTargets(configuration);
  if (problems.length > 0) {
    return problems;
  }

  const tree = (relativePath: string): FileTree =>
    readTree(resolve(root, relativePath), baseVisibleFiles(visible, relativePath));
  const handled = new Set(desiredTargets.keys());
  for (const target of Array.from(previousVendorTargets(root)).sort()) {
    if (desiredTargets.has(target)) {
      continue;
    }
    const destination = resolve(root, target);
    handled.add(target);
    if (!pathExistsOrIsSymbolicLink(destination)) {
      continue;
    }
    if (!write) {
      problems.push(
        `[vendor] stale generated copy: ${target} (edge removed from ${REGISTRY}; run: ${SYNC_COMMAND})`,
      );
      continue;
    }
    if (
      pathIsSymbolicLink(destination) ||
      !statSync(destination).isDirectory() ||
      !gitCleanUnder(root, target)
    ) {
      problems.push(
        `[vendor] retired copy has uncommitted or untracked content; refusing to remove: ${target} ` +
          "(commit or move that work first, or delete the directory yourself to adopt it)",
      );
      continue;
    }
    rmSync(destination, { recursive: true });
  }

  const sourceTrees = new Map<string, FileTree>();
  for (const [target, source] of Array.from(desiredTargets.entries()).sort(([left], [right]) =>
    left.localeCompare(right, "en"),
  )) {
    if (!pathExistsOrIsSymbolicLink(resolve(root, source))) {
      problems.push(`[vendor] source missing: ${source}`);
      continue;
    }
    const sourceTree = sourceTrees.get(source) ?? tree(source);
    sourceTrees.set(source, sourceTree);
    if (sourceTree.size === 0) {
      problems.push(`[vendor] source has no vendorable files: ${source}`);
      continue;
    }
    if (write) {
      writeTree(sourceTree, resolve(root, target));
    } else if (!fileTreesEqual(tree(target), sourceTree)) {
      problems.push(`[vendor] out of sync: ${target} != ${source} (run: ${SYNC_COMMAND})`);
    }
  }

  const sourceDigests = new Map<string, string>();
  for (const [source, files] of sourceTrees) {
    if (files.size > 0) {
      sourceDigests.set(treeDigest(files), source);
    }
  }
  if (sourceDigests.size > 0) {
    for (const skillDirectory of skillDirectories(root)) {
      if (handled.has(skillDirectory) || sourceTrees.has(skillDirectory)) {
        continue;
      }
      const files = tree(skillDirectory);
      if (files.size === 0) {
        continue;
      }
      const matchingSource = sourceDigests.get(treeDigest(files));
      if (matchingSource !== undefined) {
        problems.push(
          `[vendor] undeclared byte-identical copy of ${matchingSource}: ${skillDirectory} — ` +
            "declare a vendored_skills edge, delete the directory, or change its content to adopt it as authored",
        );
      }
    }
  }
  return problems;
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
    } else if (!fileTreesEqual(readTree(path, baseVisibleFiles(visible, relativePath)), desiredTree)) {
      problems.push(`[codex-package] out of sync: ${relativePath} (run: ${SYNC_COMMAND})`);
    }
  }

  for (const name of Array.from(separatePackagePlugins).filter((value) => existingPlugins.has(value)).sort()) {
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
  for (const name of Array.from(existingPackageNames).filter((value) => !separatePackagePlugins.has(value)).sort()) {
    const stale = resolve(packagesRoot, name);
    const relativePath = relative(root, stale).split("\\").join("/");
    if (!write) {
      problems.push(`[codex-package] stale generated package: ${relativePath} (run: ${SYNC_COMMAND})`);
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

  for (const name of Array.from(claudeOnlyPlugins).filter((value) => existingPlugins.has(value)).sort()) {
    const stale = resolve(root, "plugins", name, ".codex-plugin");
    if (!pathExistsOrIsSymbolicLink(stale)) {
      continue;
    }
    if (write) {
      rmSync(stale, { recursive: true, force: true });
    } else {
      problems.push(
        `[codex-manifest] stale .codex-plugin/ for Claude-only plugin ${name} (run: ${SYNC_COMMAND})`,
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

  for (const name of Array.from(dualPluginNames).filter((value) => claudeOnlyPlugins.has(value)).sort()) {
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
  const plan = prepareCodexPlan(root, dualPlugins, visible);
  problems.push(...plan.problems);

  const vendorProblems = synchronizeVendoredSkills(
    root,
    configuration,
    write && problems.length === 0,
    visible,
  );
  problems.push(...vendorProblems);

  if (plan.problems.length === 0 && (!write || problems.length === 0)) {
    const separatePackagePlugins = new Set(
      Object.entries(dualPlugins)
        .filter(([, metadata]) => isJsonObject(metadata) && metadata.codexProjection === true)
        .map(([name]) => name),
    );
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
