#!/usr/bin/env node
import { resolve } from "node:path";
import { SYNC_COMMAND } from "./constants.js";
import { findRepositoryRoot, synchronizeVendoredSkills } from "./sync.js";
const defaultOutput = {
    stdout: (message) => console.log(message),
    stderr: (message) => console.error(message),
};
function usage() {
    return `Usage: ${SYNC_COMMAND} [--check] [--root <path>]`;
}
export function runPluginSyncCli(arguments_, output = defaultOutput) {
    let check = false;
    let rootArgument;
    for (let index = 0; index < arguments_.length; index += 1) {
        const argument = arguments_[index];
        if (argument === "--check") {
            check = true;
        }
        else if (argument === "--root") {
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
    const problems = synchronizeVendoredSkills(root, !check);
    if (problems.length > 0) {
        for (const problem of problems) {
            output.stderr(problem);
        }
        if (check) {
            output.stderr(`\n${problems.length} issue(s). Run: ${SYNC_COMMAND}`);
        }
        return 1;
    }
    output.stdout(`plugin sync: ${check ? "checked" : "written"} (no issues)`);
    return 0;
}
process.exitCode = runPluginSyncCli(process.argv.slice(2));
//# sourceMappingURL=plugin-sync-cli.js.map