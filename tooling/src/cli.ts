#!/usr/bin/env node

import { resolve } from "node:path";

import { SYNC_COMMAND } from "./constants.js";
import { findRepositoryRoot, synchronizeVendoredSkills } from "./sync.js";

interface CliOutput {
  stdout(message: string): void;
  stderr(message: string): void;
}

const defaultOutput: CliOutput = {
  stdout: (message) => console.log(message),
  stderr: (message) => console.error(message),
};

function usage(): string {
  return `Usage: ${SYNC_COMMAND} [--check] [--root <path>]`;
}

export function runCli(arguments_: readonly string[], output: CliOutput = defaultOutput): number {
  let check = false;
  let rootArgument: string | undefined;
  for (let index = 0; index < arguments_.length; index += 1) {
    const argument = arguments_[index];
    if (argument === "--check") {
      check = true;
    } else if (argument === "--root") {
      const value = arguments_[index + 1];
      if (value === undefined) {
        output.stderr("--root requires a path");
        output.stderr(usage());
        return 2;
      }
      rootArgument = value;
      index += 1;
    } else if (argument === "--help" || argument === "-h") {
      output.stdout(usage());
      return 0;
    } else {
      output.stderr(`unknown argument: ${String(argument)}`);
      output.stderr(usage());
      return 2;
    }
  }

  let root: string;
  try {
    root = findRepositoryRoot(resolve(rootArgument ?? process.cwd()));
  } catch (error) {
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

process.exitCode = runCli(process.argv.slice(2));
