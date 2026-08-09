interface GateOutput {
    stdout(message: string): void;
    stderr(message: string): void;
}
export declare function shippedPluginForPath(relativePath: string): string | undefined;
export declare function parseSemanticVersion(version: unknown): readonly [number, number, number] | undefined;
export declare function runVersionBumpCheck(rootPath: string, baseArgument?: string, output?: GateOutput): number;
export {};
