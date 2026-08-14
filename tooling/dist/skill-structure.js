import { existsSync, readFileSync, readdirSync, statSync, } from "node:fs";
import { dirname, join, normalize, relative, resolve, sep } from "node:path";
export const SKILL_LINE_LIMIT = 500;
export const SKILL_LINE_WARNING = 450;
const defaultOutput = {
    stdout: (message) => console.log(message),
    stderr: (message) => console.error(message),
};
function lineCount(text) {
    if (text.length === 0) {
        return 0;
    }
    const count = text.split(/\r\n|\r|\n/u).length;
    return /(?:\r\n|\r|\n)$/u.test(text) ? count - 1 : count;
}
export function findStructureRepositoryRoot(start) {
    let candidate = resolve(start);
    for (;;) {
        const plugins = join(candidate, "plugins");
        if (existsSync(plugins) && statSync(plugins).isDirectory()) {
            return candidate;
        }
        const parent = dirname(candidate);
        if (parent === candidate) {
            return undefined;
        }
        candidate = parent;
    }
}
export function stripCodeFences(text) {
    const output = [];
    let insideFence = false;
    for (const line of text.split(/\r?\n/u)) {
        if (line.trimStart().startsWith("```")) {
            insideFence = !insideFence;
        }
        else if (!insideFence) {
            output.push(line);
        }
    }
    return output.join("\n");
}
export function escapingLinks(text, markdownPath, pluginRoot) {
    const bad = [];
    const root = resolve(pluginRoot);
    for (const match of stripCodeFences(text).matchAll(/\]\(([^)]+)\)/gu)) {
        const raw = match[1];
        if (raw === undefined) {
            continue;
        }
        let target = raw.split(/\s/u)[0]?.trim() ?? "";
        if (target.startsWith("http://") ||
            target.startsWith("https://") ||
            target.startsWith("mailto:") ||
            target.startsWith("#") ||
            target.startsWith("<")) {
            continue;
        }
        target = target.split("#", 1)[0] ?? "";
        if (target.length === 0) {
            continue;
        }
        const resolvedTarget = normalize(resolve(dirname(markdownPath), target));
        if (resolvedTarget !== root && !resolvedTarget.startsWith(`${root}${sep}`)) {
            if (!bad.includes(target)) {
                bad.push(target);
            }
        }
    }
    return bad;
}
function markdownFiles(root) {
    const found = [];
    const visit = (directory) => {
        for (const entry of readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name, "en"))) {
            const path = join(directory, entry.name);
            if (entry.isDirectory()) {
                visit(path);
            }
            else if (entry.isFile() && entry.name.endsWith(".md")) {
                found.push(path);
            }
        }
    };
    visit(root);
    return found;
}
function findingLabel(path, plugin, pluginRoot) {
    const relativePath = relative(pluginRoot, path);
    const parts = relativePath.split(sep);
    if (parts.length > 2 && parts[0] === "skills" && parts[1] !== undefined) {
        return [`${plugin}/${parts[1]}`, parts.slice(2).join("/")];
    }
    return [plugin, parts.join("/")];
}
function escapingLinkErrors(plugin, pluginRoot) {
    const findings = [];
    for (const path of markdownFiles(pluginRoot)) {
        const links = escapingLinks(readFileSync(path, "utf8"), path, pluginRoot);
        if (links.length > 0) {
            const [label, location] = findingLabel(path, plugin, pluginRoot);
            findings.push([
                label,
                location,
                "relative link(s) leave this standalone plugin; use an absolute GitHub URL: " +
                    links.join(", "),
            ]);
        }
    }
    return findings;
}
export function auditSkillStructure(pluginsDirectory) {
    const errors = [];
    const warnings = [];
    for (const pluginEntry of readdirSync(pluginsDirectory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name, "en"))) {
        if (!pluginEntry.isDirectory()) {
            continue;
        }
        const plugin = pluginEntry.name;
        const pluginRoot = join(pluginsDirectory, plugin);
        errors.push(...escapingLinkErrors(plugin, pluginRoot));
        const skillsDirectory = join(pluginRoot, "skills");
        if (!existsSync(skillsDirectory) || !statSync(skillsDirectory).isDirectory()) {
            continue;
        }
        for (const skillEntry of readdirSync(skillsDirectory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name, "en"))) {
            if (!skillEntry.isDirectory()) {
                continue;
            }
            const skill = skillEntry.name;
            const skillRoot = join(skillsDirectory, skill);
            const skillManifest = join(skillRoot, "SKILL.md");
            if (!existsSync(skillManifest)) {
                continue;
            }
            const label = `${plugin}/${skill}`;
            const skillText = readFileSync(skillManifest, "utf8");
            const skillLines = lineCount(skillText);
            if (skillLines > SKILL_LINE_LIMIT) {
                errors.push([
                    label,
                    "SKILL.md",
                    `${skillLines} lines (>${SKILL_LINE_LIMIT}) — split depth into references/ files`,
                ]);
            }
            else if (skillLines >= SKILL_LINE_WARNING) {
                warnings.push([
                    label,
                    "SKILL.md",
                    `${skillLines} lines — approaching the ${SKILL_LINE_LIMIT}-line limit`,
                ]);
            }
        }
    }
    return { errors, warnings };
}
function renderFindings(rows, kind, output) {
    let current;
    for (const [label, location, message] of rows) {
        if (label !== current) {
            output.stdout(`  ${label}`);
            current = label;
        }
        output.stdout(`    [${kind}] ${location}: ${message}`);
    }
}
export function runSkillStructureCheck(rootPath, strict, output = defaultOutput) {
    const root = findStructureRepositoryRoot(rootPath);
    if (root === undefined) {
        output.stderr("error: could not find the repo root (no plugins/ directory above the current path).");
        return 2;
    }
    const audit = auditSkillStructure(resolve(root, "plugins"));
    if (audit.errors.length === 0 && audit.warnings.length === 0) {
        output.stdout("OK — every SKILL.md is lean and relative Markdown links stay within each plugin.");
        return 0;
    }
    if (audit.errors.length > 0) {
        output.stdout(`${audit.errors.length} ERROR(s):`);
        renderFindings(audit.errors, "ERROR", output);
    }
    if (audit.warnings.length > 0) {
        output.stdout(`${audit.warnings.length} WARNING(s):`);
        renderFindings(audit.warnings, "WARN", output);
    }
    output.stdout("\nRules and remediation: .claude/skills/skill-structure-check/SKILL.md");
    if (audit.errors.length > 0) {
        return 1;
    }
    return strict && audit.warnings.length > 0 ? 1 : 0;
}
//# sourceMappingURL=skill-structure.js.map