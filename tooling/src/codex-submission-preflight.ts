import {
  CAPABILITY_MAX_COUNT,
  CAPABILITY_MAX_LENGTH,
  DEFAULT_PROMPT_MAX_COUNT,
  DEFAULT_PROMPT_MAX_LENGTH,
  DEVELOPER_NAME_MAX_LENGTH,
  DISPLAY_NAME_MAX_LENGTH,
  LONG_DESCRIPTION_MAX_LENGTH,
  SHORT_DESCRIPTION_MAX_LENGTH,
  SOURCE_HOMEPAGE_MAX_LENGTH,
  SUPPORTED_CODEX_CATEGORIES,
  WEBSITE_URL_MAX_LENGTH,
} from "./constants.js";
import { isJsonObject, type CodexInterface } from "./types.js";

const unsupportedTextCategory = /[\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u;
const controlCharacter = /\p{Cc}/u;
const unsupportedUrlCharacters = new Set(' <>"{}|\\^`');
const appMention = /(?:^|\s)@\S+/u;

function characterLength(value: string): number {
  return Array.from(value).length;
}

export function normalizedUniquenessKey(value: string, ignoreCase: boolean): string {
  const normalized = value.normalize("NFKC").trim().split(/\s+/u).join(" ");
  return ignoreCase ? normalized.toLocaleLowerCase("und") : normalized;
}

export function validateSubmissionText(
  value: unknown,
  field: string,
  maximumLength: number,
  allowLineFeed = false,
): string[] {
  if (typeof value !== "string" || value.length === 0) {
    return [`${field} must be a non-empty string`];
  }

  const problems: string[] = [];
  if (value.trim().length === 0) {
    problems.push(`${field} must contain non-whitespace text`);
  } else if (value !== value.trim()) {
    problems.push(`${field} must not contain surrounding whitespace`);
  }
  if (characterLength(value) > maximumLength) {
    problems.push(`${field} must be at most ${maximumLength} characters`);
  }
  if (!allowLineFeed && value.includes("\n")) {
    problems.push(`${field} must be a single line`);
  }

  for (const character of value) {
    if (
      (controlCharacter.test(character) && !(allowLineFeed && character === "\n")) ||
      unsupportedTextCategory.test(character)
    ) {
      const qualifier = allowLineFeed ? " (line feeds are allowed)" : "";
      problems.push(`${field} contains unsupported text characters${qualifier}`);
      break;
    }
  }
  return problems;
}

function validateSubmissionUrl(value: unknown, field: string, maximumLength: number): string[] {
  const problems = validateSubmissionText(value, field, maximumLength);
  if (typeof value !== "string" || value.length === 0) {
    return problems;
  }

  if (
    /\s/u.test(value) ||
    Array.from(value).some((character) => unsupportedUrlCharacters.has(character))
  ) {
    problems.push(`${field} contains unsupported URL characters`);
  }

  let parsed: URL | undefined;
  try {
    parsed = new URL(value);
  } catch {
    parsed = undefined;
  }
  if (
    parsed === undefined ||
    !/^https:\/\/[^/]/iu.test(value) ||
    parsed.protocol.toLowerCase() !== "https:" ||
    !parsed.hostname
  ) {
    problems.push(`${field} must be an absolute https URL with a host`);
  } else if (parsed.username || parsed.password) {
    problems.push(`${field} must not contain credentials`);
  }
  return problems;
}

interface SubmissionListOptions {
  maximumCount: number;
  maximumItemLength: number;
  rejectAppMentions?: boolean;
}

function validateSubmissionStringList(
  value: unknown,
  field: string,
  options: SubmissionListOptions,
): string[] {
  if (!Array.isArray(value)) {
    return [`${field} must be an array`];
  }

  const problems: string[] = [];
  if (value.length > options.maximumCount) {
    problems.push(`${field} must contain at most ${options.maximumCount} entries`);
  }
  value.forEach((item, index) => {
    const itemField = `${field}[${index}]`;
    problems.push(...validateSubmissionText(item, itemField, options.maximumItemLength));
    if (typeof item === "string" && options.rejectAppMentions && appMention.test(item)) {
      problems.push(`${itemField} must not contain an app @mention`);
    }
  });
  return problems;
}

function duplicateListProblems(
  value: unknown,
  field: string,
  ignoreCase: boolean,
): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const owners = new Map<string, number>();
  const problems: string[] = [];
  value.forEach((item, index) => {
    if (typeof item !== "string" || item.length === 0) {
      return;
    }
    const normalized = normalizedUniquenessKey(item, ignoreCase);
    const previousIndex = owners.get(normalized);
    if (previousIndex !== undefined) {
      problems.push(`${field}[${index}] duplicates ${field}[${previousIndex}] after normalization`);
    } else {
      owners.set(normalized, index);
    }
  });
  return problems;
}

/** Codex's documented final-directory submission rules for interface metadata. */
export function validateCodexSubmissionInterface(interfaceValue: unknown): string[] {
  if (!isJsonObject(interfaceValue)) {
    return ["interface must be an object"];
  }
  const pluginInterface = interfaceValue as CodexInterface;
  const problems: string[] = [];

  problems.push(
    ...validateSubmissionText(
      pluginInterface.displayName,
      "interface.displayName",
      DISPLAY_NAME_MAX_LENGTH,
    ),
    ...validateSubmissionText(
      pluginInterface.shortDescription,
      "interface.shortDescription",
      SHORT_DESCRIPTION_MAX_LENGTH,
    ),
    ...validateSubmissionText(
      pluginInterface.longDescription,
      "interface.longDescription",
      LONG_DESCRIPTION_MAX_LENGTH,
      true,
    ),
    ...validateSubmissionText(
      pluginInterface.developerName,
      "interface.developerName",
      DEVELOPER_NAME_MAX_LENGTH,
    ),
  );

  const maximumCategoryLength = Math.max(
    ...Array.from(SUPPORTED_CODEX_CATEGORIES, (category) => category.length),
  );
  problems.push(
    ...validateSubmissionText(
      pluginInterface.category,
      "interface.category",
      maximumCategoryLength,
    ),
  );
  if (
    typeof pluginInterface.category === "string" &&
    !SUPPORTED_CODEX_CATEGORIES.has(pluginInterface.category)
  ) {
    problems.push(
      `interface.category must be one of: ${Array.from(SUPPORTED_CODEX_CATEGORIES).sort().join(", ")}`,
    );
  }

  problems.push(
    ...validateSubmissionStringList(
      pluginInterface.capabilities,
      "interface.capabilities",
      {
        maximumCount: CAPABILITY_MAX_COUNT,
        maximumItemLength: CAPABILITY_MAX_LENGTH,
      },
    ),
    ...validateSubmissionStringList(
      pluginInterface.defaultPrompt,
      "interface.defaultPrompt",
      {
        maximumCount: DEFAULT_PROMPT_MAX_COUNT,
        maximumItemLength: DEFAULT_PROMPT_MAX_LENGTH,
        rejectAppMentions: true,
      },
    ),
    ...validateSubmissionUrl(
      pluginInterface.websiteURL,
      "interface.websiteURL",
      WEBSITE_URL_MAX_LENGTH,
    ),
  );
  return problems;
}

/** CypherPoet authoring choices layered on top of Codex's submission contract. */
export function validateRepositoryInterfacePolicy(
  interfaceValue: unknown,
  sourceHomepage: unknown,
): string[] {
  if (!isJsonObject(interfaceValue)) {
    return [];
  }
  const pluginInterface = interfaceValue as CodexInterface;
  const problems: string[] = [];
  if (Array.isArray(pluginInterface.capabilities) && pluginInterface.capabilities.length === 0) {
    problems.push("interface.capabilities must contain at least 1 entry");
  }
  if (Array.isArray(pluginInterface.defaultPrompt) && pluginInterface.defaultPrompt.length === 0) {
    problems.push("interface.defaultPrompt must contain at least 1 entry");
  }
  problems.push(
    ...duplicateListProblems(pluginInterface.capabilities, "interface.capabilities", true),
    ...duplicateListProblems(pluginInterface.defaultPrompt, "interface.defaultPrompt", false),
    ...validateSubmissionUrl(sourceHomepage, "source homepage", SOURCE_HOMEPAGE_MAX_LENGTH),
  );
  if (pluginInterface.websiteURL !== sourceHomepage) {
    problems.push("interface.websiteURL must equal the source homepage");
  }
  return problems;
}

export function validateGeneratedCodexInterface(
  interfaceValue: unknown,
  sourceHomepage: unknown,
): string[] {
  return [
    ...validateCodexSubmissionInterface(interfaceValue),
    ...validateRepositoryInterfacePolicy(interfaceValue, sourceHomepage),
  ];
}

export function validateAuthoredRegistryInterface(
  name: string,
  pluginMetadata: unknown,
): string[] {
  const prefix = `[config] ${name}: `;
  if (!isJsonObject(pluginMetadata)) {
    return [`${prefix}dual_harness_plugins entry must be an object`];
  }

  const problems: string[] = [];
  if (Object.hasOwn(pluginMetadata, "codexProjection")) {
    problems.push("codexProjection is not supported; use separateCodexPackage");
  }
  if (Object.hasOwn(pluginMetadata, "separateCodexPackage")) {
    if (typeof pluginMetadata.separateCodexPackage !== "boolean") {
      problems.push("separateCodexPackage must be a boolean when provided");
    }
  }
  if (!isJsonObject(pluginMetadata.interface)) {
    problems.push("dual_harness_plugins entry needs an interface object");
    return problems.map((problem) => `${prefix}${problem}`);
  }

  const authoredInterface = pluginMetadata.interface;
  const maximumCategoryLength = Math.max(
    ...Array.from(SUPPORTED_CODEX_CATEGORIES, (category) => category.length),
  );
  problems.push(
    ...validateSubmissionText(
      authoredInterface.displayName,
      "interface.displayName",
      DISPLAY_NAME_MAX_LENGTH,
    ),
    ...validateSubmissionText(
      authoredInterface.shortDescription,
      "interface.shortDescription",
      SHORT_DESCRIPTION_MAX_LENGTH,
    ),
    ...validateSubmissionText(pluginMetadata.category, "interface.category", maximumCategoryLength),
  );
  if (
    typeof pluginMetadata.category === "string" &&
    !SUPPORTED_CODEX_CATEGORIES.has(pluginMetadata.category)
  ) {
    problems.push(
      `interface.category must be one of: ${Array.from(SUPPORTED_CODEX_CATEGORIES).sort().join(", ")}`,
    );
  }

  problems.push(
    ...validateSubmissionStringList(authoredInterface.capabilities, "interface.capabilities", {
      maximumCount: CAPABILITY_MAX_COUNT,
      maximumItemLength: CAPABILITY_MAX_LENGTH,
    }),
    ...validateSubmissionStringList(authoredInterface.defaultPrompt, "interface.defaultPrompt", {
      maximumCount: DEFAULT_PROMPT_MAX_COUNT,
      maximumItemLength: DEFAULT_PROMPT_MAX_LENGTH,
      rejectAppMentions: true,
    }),
  );
  if (Array.isArray(authoredInterface.capabilities) && authoredInterface.capabilities.length === 0) {
    problems.push("interface.capabilities must contain at least 1 entry");
  }
  if (Array.isArray(authoredInterface.defaultPrompt) && authoredInterface.defaultPrompt.length === 0) {
    problems.push("interface.defaultPrompt must contain at least 1 entry");
  }
  problems.push(
    ...duplicateListProblems(authoredInterface.capabilities, "interface.capabilities", true),
    ...duplicateListProblems(authoredInterface.defaultPrompt, "interface.defaultPrompt", false),
  );
  return problems.map((problem) => `${prefix}${problem}`);
}
