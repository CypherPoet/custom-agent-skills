import { type JsonObject } from "./types.js";
export declare function buildCodexManifest(claudeManifest: JsonObject, pluginMetadata: JsonObject): JsonObject;
export declare function codexPluginRelativePath(name: string, pluginMetadata: unknown): string;
export declare function synchronizePlugins(rootPath: string, write: boolean): string[];
export declare function findRepositoryRoot(start: string): string;
