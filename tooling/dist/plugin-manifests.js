import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { isJsonObject } from "./types.js";
const CODEX_SKILL_IDENTITY_MAXIMUM_LENGTH = 64;
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
function readSkillFrontmatterName(path) {
    let text;
    try {
        text = readFileSync(path, "utf8");
    }
    catch {
        return undefined;
    }
    const frontmatter = text.match(/^---[ \t]*\r?\n([\s\S]*?)\r?\n---(?:[ \t]*\r?\n|[ \t]*$)/u);
    const nameMatch = frontmatter?.[1]?.match(/^name:[ \t]*(.*?)[ \t]*$/mu);
    if (nameMatch?.[1] === undefined) {
        return undefined;
    }
    const value = nameMatch[1];
    if (value.startsWith('"') && value.endsWith('"')) {
        try {
            const parsed = JSON.parse(value);
            return typeof parsed === "string" && parsed.length > 0 ? parsed : undefined;
        }
        catch {
            return undefined;
        }
    }
    if (value.startsWith("'") && value.endsWith("'")) {
        const parsed = value.slice(1, -1).replaceAll("''", "'");
        return parsed.length > 0 ? parsed : undefined;
    }
    const parsed = value.replace(/[ \t]+#.*$/u, "").trim();
    return parsed.length > 0 ? parsed : undefined;
}
function validateCodexSkillIdentities(plugin) {
    if (plugin.codex === undefined) {
        return [];
    }
    const skillsDirectory = join(plugin.directory, "skills");
    if (!existsSync(skillsDirectory) || !statSync(skillsDirectory).isDirectory()) {
        return [];
    }
    const pluginName = typeof plugin.codex.name === "string" ? plugin.codex.name : plugin.name;
    const problems = [];
    for (const entry of readdirSync(skillsDirectory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name, "en"))) {
        if (!entry.isDirectory()) {
            continue;
        }
        const skillName = readSkillFrontmatterName(join(skillsDirectory, entry.name, "SKILL.md"));
        if (skillName === undefined) {
            continue;
        }
        const identity = `${pluginName}:${skillName}`;
        if ([...identity].length > CODEX_SKILL_IDENTITY_MAXIMUM_LENGTH) {
            problems.push(`[manifest] ${plugin.name} Codex skill identity ${JSON.stringify(identity)} ` +
                `must be ${CODEX_SKILL_IDENTITY_MAXIMUM_LENGTH} characters or fewer`);
        }
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
        problems.push(...validateCodexSkillIdentities(plugin));
        plugins.push(plugin);
    }
    return { plugins, problems };
}
//# sourceMappingURL=plugin-manifests.js.map