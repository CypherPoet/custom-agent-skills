import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { isJsonObject } from "./types.js";
export function parsePluginVersion(value) {
    if (typeof value !== "string" || !/^\d+\.\d+\.\d+$/u.test(value)) {
        return undefined;
    }
    const fields = value.split(".").map(Number);
    const major = fields[0];
    const minor = fields[1];
    const patch = fields[2];
    return major === undefined || minor === undefined || patch === undefined
        ? undefined
        : [major, minor, patch];
}
function readManifest(path, label) {
    let text;
    try {
        text = readFileSync(path, "utf8");
    }
    catch (error) {
        return { problems: [`${label} could not be read: ${String(error)}`] };
    }
    let value;
    try {
        value = JSON.parse(text);
    }
    catch (error) {
        return { problems: [`${label} is not valid JSON: ${String(error)}`] };
    }
    if (!isJsonObject(value)) {
        return { problems: [`${label} must contain a JSON object`] };
    }
    return { value, problems: [] };
}
function validateManifest(pluginName, harness, manifest) {
    const label = `[manifest] ${pluginName} ${harness}`;
    const problems = [];
    if (manifest.name !== pluginName) {
        problems.push(`${label} name must equal the plugin directory name`);
    }
    if (parsePluginVersion(manifest.version) === undefined) {
        problems.push(`${label} version must use major.minor.patch`);
    }
    return problems;
}
export function auditPluginManifests(rootPath) {
    const root = resolve(rootPath);
    const pluginsDirectory = resolve(root, "plugins");
    if (!existsSync(pluginsDirectory) || !statSync(pluginsDirectory).isDirectory()) {
        return { plugins: [], problems: ["[manifest] plugins directory is missing"] };
    }
    const plugins = [];
    const problems = [];
    for (const entry of readdirSync(pluginsDirectory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name, "en"))) {
        if (!entry.isDirectory()) {
            continue;
        }
        const directory = join(pluginsDirectory, entry.name);
        const claudePath = join(directory, ".claude-plugin", "plugin.json");
        const codexPath = join(directory, ".codex-plugin", "plugin.json");
        const hasClaude = existsSync(claudePath);
        const hasCodex = existsSync(codexPath);
        if (!hasClaude && !hasCodex) {
            problems.push(`[manifest] ${entry.name} needs .claude-plugin/plugin.json, ` +
                ".codex-plugin/plugin.json, or both");
            plugins.push({ name: entry.name, directory });
            continue;
        }
        const plugin = { name: entry.name, directory };
        if (hasClaude) {
            const read = readManifest(claudePath, `[manifest] ${entry.name} Claude manifest`);
            problems.push(...read.problems);
            if (read.value !== undefined) {
                plugin.claude = read.value;
                problems.push(...validateManifest(entry.name, "Claude", read.value));
            }
        }
        if (hasCodex) {
            const read = readManifest(codexPath, `[manifest] ${entry.name} Codex manifest`);
            problems.push(...read.problems);
            if (read.value !== undefined) {
                plugin.codex = read.value;
                problems.push(...validateManifest(entry.name, "Codex", read.value));
            }
        }
        if (plugin.claude !== undefined &&
            plugin.codex !== undefined &&
            plugin.claude.version !== plugin.codex.version) {
            problems.push(`[manifest] ${entry.name} versions must match across Claude and Codex: ` +
                `${JSON.stringify(plugin.claude.version)} != ${JSON.stringify(plugin.codex.version)}`);
        }
        plugins.push(plugin);
    }
    return { plugins, problems };
}
//# sourceMappingURL=plugin-manifests.js.map