import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import {
  CODEX_MANIFEST_CARRY,
  PLUGIN_DESCRIPTION_MAX_LENGTH,
} from "./constants.js";
import { validateSubmissionText } from "./codex-submission-preflight.js";
import { isJsonObject, type JsonObject } from "./types.js";

export function readJsonObject(
  path: string,
  label: string,
): { value?: JsonObject; problems: string[] } {
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

export function formatCodexManifest(value: JsonObject): Buffer {
  return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export function validateClaudeManifestForCodex(
  name: string,
  claudeManifest: JsonObject,
): string[] {
  const prefix = `[codex-manifest] ${name}: `;
  const problems: string[] = [];
  for (const field of ["name", "version", "homepage"] as const) {
    const value = claudeManifest[field];
    if (typeof value !== "string" || value.trim().length === 0) {
      problems.push(`${prefix}Claude manifest needs non-empty ${field}`);
    }
  }
  problems.push(
    ...validateSubmissionText(
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

export function unsupportedClaudeComponents(
  pluginDirectory: string,
  claudeManifest: JsonObject,
): string[] {
  const unsupported = ["mcpServers", "hooks", "agents", "commands"].filter((key) =>
    Object.hasOwn(claudeManifest, key),
  );
  const skillsValue = Object.hasOwn(claudeManifest, "skills")
    ? claudeManifest.skills
    : "./skills/";
  if (
    typeof skillsValue !== "string" ||
    skillsValue.replace(/^\.\//u, "").replace(/\/$/u, "") !== "skills"
  ) {
    unsupported.push("skills (custom path)");
  }
  for (const component of ["commands", "agents", "hooks"]) {
    const componentPath = join(pluginDirectory, component);
    if (
      existsSync(componentPath) &&
      statSync(componentPath).isDirectory() &&
      !unsupported.includes(component)
    ) {
      unsupported.push(`${component}/ (auto-discovered)`);
    }
  }
  if (existsSync(join(pluginDirectory, ".mcp.json")) && !unsupported.includes("mcpServers")) {
    unsupported.push(".mcp.json");
  }
  return unsupported;
}
