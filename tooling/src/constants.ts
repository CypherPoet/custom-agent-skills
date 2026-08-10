export const REGISTRY = "scripts/plugin-registry.json";
export const LEGACY_REGISTRY = "scripts/dual-harness.json";
export const SYNC_COMMAND = "cypherpoet-plugin-sync";

export const IGNORED_DIRECTORY_NAMES = new Set(["__pycache__", "evals", ".git"]);
export const CODEX_MANIFEST_CARRY = [
  "author",
  "homepage",
  "repository",
  "license",
  "keywords",
] as const;

export const SUPPORTED_CODEX_CATEGORIES = new Set([
  "Productivity",
  "Creativity",
  "Developer Tools",
  "Business & Operations",
  "Data & Analytics",
  "Communication",
  "Education & Research",
  "Security",
  "Finance",
  "Healthcare",
  "Travel",
  "Entertainment",
  "Other",
]);

export const DISPLAY_NAME_MAX_LENGTH = 30;
export const SHORT_DESCRIPTION_MAX_LENGTH = 30;
export const PLUGIN_DESCRIPTION_MAX_LENGTH = 1_024;
export const LONG_DESCRIPTION_MAX_LENGTH = 4_000;
export const DEVELOPER_NAME_MAX_LENGTH = 80;
export const CAPABILITY_MAX_COUNT = 20;
export const CAPABILITY_MAX_LENGTH = 120;
export const DEFAULT_PROMPT_MAX_COUNT = 3;
export const DEFAULT_PROMPT_MAX_LENGTH = 128;
export const SOURCE_HOMEPAGE_MAX_LENGTH = 2_048;
export const WEBSITE_URL_MAX_LENGTH = 1_024;
