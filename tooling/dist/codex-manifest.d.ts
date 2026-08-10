import { type JsonObject } from "./types.js";
export declare function readJsonObject(path: string, label: string): {
    value?: JsonObject;
    problems: string[];
};
export declare function buildCodexManifest(claudeManifest: JsonObject, pluginMetadata: JsonObject): JsonObject;
export declare function formatCodexManifest(value: JsonObject): Buffer;
export declare function validateClaudeManifestForCodex(name: string, claudeManifest: JsonObject): string[];
export declare function unsupportedClaudeComponents(pluginDirectory: string, claudeManifest: JsonObject): string[];
