export type JsonObject = Record<string, unknown>;
export type FileTree = Map<string, Buffer>;

export interface PluginRegistry extends JsonObject {
  vendored_skills: unknown[];
  dual_harness_plugins: Record<string, unknown>;
  claude_only_plugins: Record<string, unknown>;
}

export interface CodexInterface extends JsonObject {
  displayName: unknown;
  shortDescription: unknown;
  longDescription: unknown;
  developerName: unknown;
  category: unknown;
  capabilities?: unknown;
  websiteURL?: unknown;
  defaultPrompt?: unknown;
}

export function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
