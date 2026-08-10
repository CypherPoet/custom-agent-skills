import { isMap, isScalar, parseDocument } from "yaml";

import { CODEX_PACKAGES_DIRECTORY } from "./constants.js";
import { isJsonObject, type FileTree } from "./types.js";

const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });
const invocationFieldName = "disable-model-invocation";

interface FrontmatterBounds {
  contentStart: number;
  contentEnd: number;
}

interface InvocationTransform {
  transformed?: Buffer;
  manualOnly: boolean;
  problems: string[];
}

function frontmatterBounds(text: string): FrontmatterBounds | undefined {
  const firstNewline = text.indexOf("\n");
  if (firstNewline < 0 || text.slice(0, firstNewline).replace(/\r$/u, "") !== "---") {
    return undefined;
  }

  const contentStart = firstNewline + 1;
  let lineStart = contentStart;
  while (lineStart <= text.length) {
    const newline = text.indexOf("\n", lineStart);
    const lineEnd = newline < 0 ? text.length : newline;
    if (text.slice(lineStart, lineEnd).replace(/\r$/u, "") === "---") {
      return { contentStart, contentEnd: lineStart };
    }
    if (newline < 0) {
      break;
    }
    lineStart = newline + 1;
  }
  return { contentStart, contentEnd: -1 };
}

function yamlProblem(document: ReturnType<typeof parseDocument>): string | undefined {
  const error = document.errors[0];
  if (error === undefined) {
    return undefined;
  }
  return error.code === "DUPLICATE_KEY" ? "found duplicate key" : error.message;
}

export function stripClaudeInvocationField(
  skillManifest: Buffer,
  label: string,
): InvocationTransform {
  let text: string;
  try {
    text = decoder.decode(skillManifest);
  } catch (error) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md is not UTF-8: ${String(error)}`],
    };
  }

  const bounds = frontmatterBounds(text);
  if (bounds === undefined) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md must start with YAML frontmatter`],
    };
  }
  if (bounds.contentEnd < 0) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md frontmatter is not closed`],
    };
  }

  const frontmatter = text.slice(bounds.contentStart, bounds.contentEnd);
  const document = parseDocument(frontmatter, { uniqueKeys: true });
  const parseProblem = yamlProblem(document);
  if (parseProblem !== undefined) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md frontmatter is invalid: ${parseProblem}`],
    };
  }
  if (!isMap(document.contents)) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: SKILL.md frontmatter must contain a mapping`],
    };
  }

  const matchingPairs = document.contents.items.filter(
    (pair) => isScalar(pair.key) && pair.key.value === invocationFieldName,
  );
  const pair = matchingPairs[0];
  if (pair === undefined) {
    return { transformed: skillManifest, manualOnly: false, problems: [] };
  }
  if (matchingPairs.length > 1) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: Claude invocation field is duplicated`],
    };
  }
  if (
    !isScalar(pair.value) ||
    typeof pair.value.value !== "boolean" ||
    !/^(?:true|false)$/iu.test(pair.value.source ?? "")
  ) {
    return {
      manualOnly: false,
      problems: [
        `[codex-package] ${label}: ${invocationFieldName} must use the YAML boolean true or false`,
      ],
    };
  }

  const keyStart = pair.key.range?.[0];
  const valueStart = pair.value.range?.[0];
  if (keyStart === undefined || valueStart === undefined) {
    return {
      manualOnly: false,
      problems: [`[codex-package] ${label}: could not locate ${invocationFieldName}`],
    };
  }
  const keyLineStart = frontmatter.lastIndexOf("\n", keyStart - 1) + 1;
  const valueLineStart = frontmatter.lastIndexOf("\n", valueStart - 1) + 1;
  if (
    keyLineStart !== valueLineStart ||
    frontmatter.slice(keyLineStart, keyStart).trim().length > 0
  ) {
    return {
      manualOnly: false,
      problems: [
        `[codex-package] ${label}: ${invocationFieldName} must use one top-level block line`,
      ],
    };
  }

  const followingNewline = frontmatter.indexOf("\n", keyStart);
  const fieldLineEnd = followingNewline < 0 ? frontmatter.length : followingNewline + 1;
  const removeStart = bounds.contentStart + keyLineStart;
  const removeEnd = bounds.contentStart + fieldLineEnd;
  return {
    transformed: Buffer.from(`${text.slice(0, removeStart)}${text.slice(removeEnd)}`, "utf8"),
    manualOnly: pair.value.value,
    problems: [],
  };
}

export function codexManualOnlyPolicyProblem(agentManifest: Buffer): string | undefined {
  let text: string;
  try {
    text = decoder.decode(agentManifest);
  } catch {
    return "agents/openai.yaml must be UTF-8";
  }

  const document = parseDocument(text, { uniqueKeys: true });
  const parseProblem = yamlProblem(document);
  if (parseProblem !== undefined) {
    return `agents/openai.yaml is invalid: ${parseProblem}`;
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

export function codexPackageRelativePath(name: string, pluginMetadata: unknown): string {
  return isJsonObject(pluginMetadata) && pluginMetadata.separateCodexPackage === true
    ? `${CODEX_PACKAGES_DIRECTORY}/${name}`
    : `plugins/${name}`;
}

export function prepareSeparateCodexPackage(
  name: string,
  sourceTree: ReadonlyMap<string, Buffer>,
  manifestBytes: Buffer,
): { packageTree?: FileTree; problems: string[] } {
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
      `[codex-package] ${name}: separateCodexPackage requires at least one ` +
        `${invocationFieldName}: true field`,
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
