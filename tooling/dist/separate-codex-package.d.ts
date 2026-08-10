import { type FileTree } from "./types.js";
interface InvocationTransform {
    transformed?: Buffer;
    manualOnly: boolean;
    problems: string[];
}
export declare function stripClaudeInvocationField(skillManifest: Buffer, label: string): InvocationTransform;
export declare function codexManualOnlyPolicyProblem(agentManifest: Buffer): string | undefined;
export declare function codexPackageRelativePath(name: string, pluginMetadata: unknown): string;
export declare function prepareSeparateCodexPackage(root: string, name: string, pluginDirectory: string, manifestBytes: Buffer, visible: ReadonlySet<string> | undefined): {
    packageTree?: FileTree;
    problems: string[];
};
export {};
