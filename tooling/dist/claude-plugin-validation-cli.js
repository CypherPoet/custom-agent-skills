#!/usr/bin/env node
import { resolve } from "node:path";
import { validateAuthoredClaudePlugins } from "./claude-plugin-validation.js";
import { findRepositoryRoot } from "./sync.js";
const defaultOutput = {
    stdout: (message) => console.log(message),
    stderr: (message) => console.error(message),
};
function usage() {
    return "Usage: cypherpoet-validate-claude-plugins [--root <path>]";
}
export function runClaudeValidationCli(arguments_, output = defaultOutput) {
    let rootArgument;
    for (let index = 0; index < arguments_.length; index += 1) {
        const argument = arguments_[index];
        if (argument === "--root") {
            const value = arguments_[index + 1];
            if (value === undefined) {
                output.stderr("--root requires a path");
                output.stderr(usage());
                return 2;
            }
            rootArgument = value;
            index += 1;
        }
        else if (argument === "--help" || argument === "-h") {
            output.stdout(usage());
            return 0;
        }
        else {
            output.stderr(`unknown argument: ${String(argument)}`);
            output.stderr(usage());
            return 2;
        }
    }
    let root;
    try {
        root = findRepositoryRoot(resolve(rootArgument ?? process.cwd()));
    }
    catch (error) {
        output.stderr(error instanceof Error ? error.message : String(error));
        return 1;
    }
    const problems = validateAuthoredClaudePlugins(root);
    if (problems.length > 0) {
        problems.forEach((problem) => output.stderr(problem));
        return 1;
    }
    output.stdout("Claude plugins: strict validation passed");
    return 0;
}
process.exitCode = runClaudeValidationCli(process.argv.slice(2));
//# sourceMappingURL=claude-plugin-validation-cli.js.map