export type JsonObject = Record<string, unknown>;
export type FileTree = Map<string, Buffer>;
export interface VendoredSkillsConfiguration extends JsonObject {
    skills: unknown[];
}
export declare function isJsonObject(value: unknown): value is JsonObject;
