import { type JsonObject } from "./types.js";
export interface PluginManifestSet {
    name: string;
    directory: string;
    claude?: JsonObject;
    codex?: JsonObject;
}
export interface PluginManifestAudit {
    plugins: PluginManifestSet[];
    problems: string[];
}
export declare function parsePluginVersion(value: unknown): readonly [major: number, minor: number, patch: number] | undefined;
export declare function auditPluginManifests(rootPath: string): PluginManifestAudit;
