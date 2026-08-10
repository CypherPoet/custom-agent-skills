export type JsonObject = Record<string, unknown>;
export type FileTree = Map<string, Buffer>;

export interface VendoredSkillsConfiguration extends JsonObject {
  skills: unknown[];
}

export function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
