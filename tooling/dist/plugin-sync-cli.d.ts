#!/usr/bin/env node
interface PluginSyncCliOutput {
    stdout(message: string): void;
    stderr(message: string): void;
}
export declare function runPluginSyncCli(arguments_: readonly string[], output?: PluginSyncCliOutput): number;
export {};
