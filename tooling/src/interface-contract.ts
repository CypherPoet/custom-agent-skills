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

export function validateText(
  value: unknown,
  field: string,
  maximumLength: number,
  allowLineFeed = false,
): string[] {
  if (typeof value !== "string") {
    return [`${field} must be a non-empty string`];
  }
  if (value.length === 0) {
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

  let containsUnsupportedText = false;
  for (const character of value) {
    if (
      (controlCharacter.test(character) && !(allowLineFeed && character === "\n")) ||
      unsupportedTextCategory.test(character)
    ) {
      containsUnsupportedText = true;
      break;
    }
  }
  if (containsUnsupportedText) {
    const qualifier = allowLineFeed ? " (line feeds are allowed)" : "";
    problems.push(`${field} contains unsupported text characters${qualifier}`);
  }
  return problems;
}

export function validateUrl(value: unknown, field: string, maximumLength: number): string[] {
  const problems = validateText(value, field, maximumLength);
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

function validateStringList(
  value: unknown,
  field: string,
  options: {
    minimumCount: number;
    maximumCount: number;
    maximumItemLength: number;
    ignoreCaseForDuplicates: boolean;
    rejectAppMentions?: boolean;
  },
): string[] {
  if (!Array.isArray(value)) {
    return [`${field} must be an array`];
  }

  const problems: string[] = [];
  if (value.length < options.minimumCount || value.length > options.maximumCount) {
    problems.push(
      `${field} must contain between ${options.minimumCount} and ${options.maximumCount} entries`,
    );
  }

  const owners = new Map<string, number>();
  value.forEach((item, index) => {
    const itemField = `${field}[${index}]`;
    problems.push(...validateText(item, itemField, options.maximumItemLength));
    if (typeof item !== "string" || item.length === 0) {
      return;
    }
    const normalized = normalizedUniquenessKey(item, options.ignoreCaseForDuplicates);
    const previousIndex = owners.get(normalized);
    if (previousIndex !== undefined) {
      problems.push(`${itemField} duplicates ${field}[${previousIndex}] after normalization`);
    } else {
      owners.set(normalized, index);
    }
    if (options.rejectAppMentions && appMention.test(item)) {
      problems.push(`${itemField} must not contain an app @mention`);
    }
  });
  return problems;
}

export function validateCodexInterface(
  interfaceValue: unknown,
  options: { sourceHomepage?: unknown } = {},
): string[] {
  if (!isJsonObject(interfaceValue)) {
    return ["interface must be an object"];
  }
  const pluginInterface = interfaceValue as CodexInterface;
  const problems: string[] = [];

  problems.push(
    ...validateText(
      pluginInterface.displayName,
      "interface.displayName",
      DISPLAY_NAME_MAX_LENGTH,
    ),
    ...validateText(
      pluginInterface.shortDescription,
      "interface.shortDescription",
      SHORT_DESCRIPTION_MAX_LENGTH,
    ),
    ...validateText(
      pluginInterface.longDescription,
      "interface.longDescription",
      LONG_DESCRIPTION_MAX_LENGTH,
      true,
    ),
    ...validateText(
      pluginInterface.developerName,
      "interface.developerName",
      DEVELOPER_NAME_MAX_LENGTH,
    ),
  );

  const maximumCategoryLength = Math.max(
    ...Array.from(SUPPORTED_CODEX_CATEGORIES, (category) => category.length),
  );
  problems.push(
    ...validateText(pluginInterface.category, "interface.category", maximumCategoryLength),
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
    ...validateStringList(pluginInterface.capabilities, "interface.capabilities", {
      minimumCount: 1,
      maximumCount: CAPABILITY_MAX_COUNT,
      maximumItemLength: CAPABILITY_MAX_LENGTH,
      ignoreCaseForDuplicates: true,
    }),
    ...validateStringList(pluginInterface.defaultPrompt, "interface.defaultPrompt", {
      minimumCount: 1,
      maximumCount: DEFAULT_PROMPT_MAX_COUNT,
      maximumItemLength: DEFAULT_PROMPT_MAX_LENGTH,
      ignoreCaseForDuplicates: false,
      rejectAppMentions: true,
    }),
    ...validateUrl(pluginInterface.websiteURL, "interface.websiteURL", WEBSITE_URL_MAX_LENGTH),
  );

  if (options.sourceHomepage !== undefined) {
    problems.push(
      ...validateUrl(options.sourceHomepage, "source homepage", SOURCE_HOMEPAGE_MAX_LENGTH),
    );
    if (pluginInterface.websiteURL !== options.sourceHomepage) {
      problems.push("interface.websiteURL must equal the source homepage");
    }
  }
  return problems;
}

export function validateAuthoredInterfaceMetadata(
  name: string,
  pluginMetadata: unknown,
): string[] {
  const prefix = `[config] ${name}: `;
  if (!isJsonObject(pluginMetadata)) {
    return [`${prefix}dual_harness_plugins entry must be an object`];
  }
  const separateCodexPackage = pluginMetadata.codexProjection ?? false;
  if (typeof separateCodexPackage !== "boolean") {
    return [`${prefix}codexProjection must be a boolean when provided`];
  }
  if (!isJsonObject(pluginMetadata.interface)) {
    return [`${prefix}dual_harness_plugins entry needs an interface object`];
  }

  const authoredCandidate = {
    displayName: pluginMetadata.interface.displayName,
    shortDescription: pluginMetadata.interface.shortDescription,
    longDescription: "Generated from the Claude manifest.",
    developerName: "Generated author",
    category: pluginMetadata.category,
    capabilities: pluginMetadata.interface.capabilities,
    websiteURL: "https://example.com/plugin",
    defaultPrompt: pluginMetadata.interface.defaultPrompt,
  };
  return validateCodexInterface(authoredCandidate)
    .filter(
      (problem) =>
        !problem.startsWith("interface.longDescription") &&
        !problem.startsWith("interface.developerName") &&
        !problem.startsWith("interface.websiteURL"),
    )
    .map((problem) => `${prefix}${problem}`);
}
