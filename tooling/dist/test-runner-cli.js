#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { validateAuthoredClaudePlugins } from "./claude-plugin-validation.js";
import { auditPluginManifests } from "./plugin-manifests.js";
import { runSkillStructureCheck } from "./skill-structure.js";
import { findRepositoryRoot, synchronizeVendoredSkills } from "./sync.js";
import { runVersionBumpCheck } from "./version-bumps.js";
function run(root, command, arguments_, environment = process.env) {
    const result = spawnSync(command, arguments_, {
        cwd: root,
        env: environment,
        stdio: "inherit",
    });
    if (result.error !== undefined) {
        console.error(result.error.message);
        return 1;
    }
    return result.status ?? 1;
}
function testFiles(directory) {
    if (!existsSync(directory)) {
        return [];
    }
    return readdirSync(directory, { withFileTypes: true })
        .flatMap((entry) => {
        const path = resolve(directory, entry.name);
        return entry.isDirectory()
            ? testFiles(path)
            : entry.isFile() && entry.name.endsWith(".test.mjs")
                ? [path]
                : [];
    })
        .sort();
}
function pythonCommand() {
    const configured = process.env.PYTHON;
    const candidates = [];
    if (configured !== undefined) {
        candidates.push({ command: configured, prefix: [] });
    }
    candidates.push({ command: "python3", prefix: [] }, { command: "python", prefix: [] }, { command: "py", prefix: ["-3"] });
    for (const { command, prefix } of candidates) {
        const result = spawnSync(command, [...prefix, "--version"], { encoding: "utf8" });
        if (result.status === 0) {
            return { command, prefix };
        }
    }
    return undefined;
}
function parseArguments(arguments_) {
    let buildCheck;
    for (let index = 0; index < arguments_.length; index += 1) {
        if (arguments_[index] !== "--build-check" || arguments_[index + 1] === undefined) {
            console.error("Usage: cypherpoet-repository-test [--build-check <script>]");
            return { valid: false };
        }
        buildCheck = arguments_[index + 1];
        index += 1;
    }
    return buildCheck === undefined ? { valid: true } : { buildCheck, valid: true };
}
function main(arguments_) {
    const parsed = parseArguments(arguments_);
    if (!parsed.valid) {
        return 2;
    }
    const root = findRepositoryRoot(process.cwd());
    if (parsed.buildCheck !== undefined) {
        const buildStatus = run(root, process.execPath, [resolve(root, parsed.buildCheck)]);
        if (buildStatus !== 0) {
            return buildStatus;
        }
    }
    const syncProblems = synchronizeVendoredSkills(root, false);
    if (syncProblems.length > 0) {
        for (const problem of syncProblems) {
            console.error(problem);
        }
        return 1;
    }
    console.log("plugin sync: checked (no issues)");
    const manifestAudit = auditPluginManifests(root);
    if (manifestAudit.problems.length > 0) {
        for (const problem of manifestAudit.problems) {
            console.error(problem);
        }
        return 1;
    }
    console.log("plugin manifests: checked (no issues)");
    const structureStatus = runSkillStructureCheck(root, true);
    if (structureStatus !== 0) {
        return structureStatus;
    }
    const versionStatus = runVersionBumpCheck(root);
    if (versionStatus !== 0) {
        return versionStatus;
    }
    const claudeValidationProblems = validateAuthoredClaudePlugins(root);
    if (claudeValidationProblems.length > 0) {
        for (const problem of claudeValidationProblems) {
            console.error(problem);
        }
        return 1;
    }
    console.log("Claude plugins: strict validation passed");
    const nodeTests = [
        ...testFiles(resolve(root, "tooling/test")),
        ...testFiles(resolve(root, "tests-node")),
    ];
    if (nodeTests.length > 0) {
        const nodeStatus = run(root, process.execPath, ["--test", ...nodeTests]);
        if (nodeStatus !== 0) {
            return nodeStatus;
        }
    }
    const pythonTestsDirectory = resolve(root, "tests");
    const pythonTests = existsSync(pythonTestsDirectory)
        ? readdirSync(pythonTestsDirectory).filter((name) => name.startsWith("test_") && name.endsWith(".py"))
        : [];
    if (pythonTests.length > 0) {
        const python = pythonCommand();
        if (python === undefined) {
            console.error("Python 3 is required for the plugin-owned Python test suites.");
            return 1;
        }
        return run(root, python.command, [
            ...python.prefix,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_*.py",
        ], { ...process.env, PYTHONDONTWRITEBYTECODE: "1" });
    }
    return 0;
}
process.exitCode = main(process.argv.slice(2));
//# sourceMappingURL=test-runner-cli.js.map