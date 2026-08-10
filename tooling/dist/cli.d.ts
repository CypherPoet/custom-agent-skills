#!/usr/bin/env node
interface CliOutput {
    stdout(message: string): void;
    stderr(message: string): void;
}
export declare function runCli(arguments_: readonly string[], output?: CliOutput): number;
export {};
