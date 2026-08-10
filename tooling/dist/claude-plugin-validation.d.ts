interface CommandResult {
    error?: Error;
    status: number | null;
}
export type ClaudeValidatorRunner = (root: string, pluginPath: string) => CommandResult;
export declare function authoredClaudePluginPaths(root: string): string[];
export declare function validateAuthoredClaudePlugins(root: string, runner?: ClaudeValidatorRunner): string[];
export {};
