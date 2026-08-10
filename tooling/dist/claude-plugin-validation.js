import { spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { join, relative, resolve } from "node:path";
const defaultRunner = (root, pluginPath) => {
    const result = spawnSync(process.platform === "win32" ? "claude.cmd" : "claude", ["plugin", "validate", "--strict", pluginPath], {
        cwd: root,
        stdio: "inherit",
    });
    return {
        ...(result.error === undefined ? {} : { error: result.error }),
        status: result.status,
    };
};
export function authoredClaudePluginPaths(root) {
    const pluginsDirectory = resolve(root, "plugins");
    if (!existsSync(pluginsDirectory)) {
        return [];
    }
    return readdirSync(pluginsDirectory, { withFileTypes: true })
        .filter((entry) => entry.isDirectory() &&
        existsSync(join(pluginsDirectory, entry.name, ".claude-plugin", "plugin.json")))
        .map((entry) => relative(root, join(pluginsDirectory, entry.name)))
        .sort((left, right) => left.localeCompare(right, "en"));
}
export function validateAuthoredClaudePlugins(root, runner = defaultRunner) {
    const pluginPaths = authoredClaudePluginPaths(root);
    if (pluginPaths.length === 0) {
        return ["[claude-validator] no authored Claude plugins were found"];
    }
    const problems = [];
    for (const pluginPath of pluginPaths) {
        const result = runner(root, pluginPath);
        if (result.error !== undefined) {
            problems.push(`[claude-validator] could not run Claude Code for ${pluginPath}: ${result.error.message}. ` +
                "Run npm ci to install the repository's pinned validator.");
        }
        else if (result.status !== 0) {
            problems.push(`[claude-validator] strict validation failed for ${pluginPath} ` +
                `(exit ${String(result.status ?? "unknown")})`);
        }
    }
    return problems;
}
//# sourceMappingURL=claude-plugin-validation.js.map