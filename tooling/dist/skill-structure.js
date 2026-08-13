import { existsSync, readFileSync, readdirSync, statSync, } from "node:fs";
import { dirname, join, normalize, relative, resolve, sep } from "node:path";
import { synchronizeVendoredSkills } from "./sync.js";
export const SKILL_LINE_LIMIT = 500;
export const SKILL_LINE_WARNING = 450;
export const REFERENCE_CONTENTS_THRESHOLD = 300;
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
export function githubHeadingAnchor(heading) {
    return heading
        .toLocaleLowerCase("und")
        .replace(/[^\p{L}\p{N}_\s-]/gu, "")
        .trim()
        .replace(/ /gu, "-");
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
export function headingAnchors(text) {
    const seen = new Map();
    const valid = new Set();
    for (const line of stripCodeFences(text).split(/\r?\n/u)) {
        const match = /^#{1,6}\s+(.*)$/u.exec(line);
        if (match?.[1] === undefined) {
            continue;
        }
        const anchor = githubHeadingAnchor(match[1].trim());
        const occurrence = seen.get(anchor) ?? 0;
        valid.add(occurrence === 0 ? anchor : `${anchor}-${occurrence}`);
        seen.set(anchor, occurrence + 1);
    }
    return valid;
}
export function contentsAnchors(text) {
    const jumpLine = /^\*\*Contents:\*\*.*$/mu.exec(stripCodeFences(text))?.[0];
    if (jumpLine === undefined) {
        return undefined;
    }
    const anchors = Array.from(jumpLine.matchAll(/\[[^\]]*\]\(#([^)]+)\)/gu), (match) => match[1])
        .filter((value) => value !== undefined);
    return anchors.length > 0 ? anchors : undefined;
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
                "cross-plugin relative link(s) — dead in a sparse-clone install, use an absolute GitHub URL: " +
                    links.join(", "),
            ]);
        }
    }
    return findings;
}
export function auditSkillStructure(pluginsDirectory) {
    const errors = [];
    const warnings = [];
    const missingContents = [];
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
            const referencesDirectory = join(skillRoot, "references");
            if (!existsSync(referencesDirectory) || !statSync(referencesDirectory).isDirectory()) {
                continue;
            }
            for (const referenceEntry of readdirSync(referencesDirectory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name, "en"))) {
                if (!referenceEntry.isFile() || !referenceEntry.name.endsWith(".md")) {
                    continue;
                }
                const referenceText = readFileSync(join(referencesDirectory, referenceEntry.name), "utf8");
                const anchors = contentsAnchors(referenceText);
                if (anchors === undefined) {
                    const referenceLines = lineCount(referenceText);
                    if (referenceLines > REFERENCE_CONTENTS_THRESHOLD) {
                        missingContents.push([label, `${referenceEntry.name} (${referenceLines} lines)`]);
                    }
                    continue;
                }
                const validAnchors = headingAnchors(referenceText);
                const broken = anchors.filter((anchor) => !validAnchors.has(anchor));
                if (broken.length > 0) {
                    errors.push([
                        label,
                        `references/${referenceEntry.name}`,
                        `stale Contents anchors: ${broken.map((anchor) => `#${anchor}`).join(", ")}`,
                    ]);
                }
            }
        }
    }
    return { errors, warnings, missingContents };
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
    for (const message of synchronizeVendoredSkills(root, false)) {
        audit.errors.push(["vendoring", "sync", message]);
    }
    if (audit.errors.length === 0 &&
        audit.warnings.length === 0 &&
        audit.missingContents.length === 0) {
        output.stdout(`OK — every SKILL.md is lean, large reference files are indexed, ` +
            `and all Contents anchors resolve.`);
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
    if (audit.missingContents.length > 0) {
        const bySkill = new Map();
        for (const [label, file] of audit.missingContents) {
            const files = bySkill.get(label) ?? [];
            files.push(file);
            bySkill.set(label, files);
        }
        output.stdout(`ADVISORY — ${audit.missingContents.length} large reference file(s) across ` +
            `${bySkill.size} skill(s) lack a **Contents:** jump-line (non-failing):`);
        for (const [label, files] of Array.from(bySkill.entries()).sort(([left], [right]) => left.localeCompare(right, "en"))) {
            output.stdout(`  ${label}: ${files.join(", ")}`);
        }
    }
    output.stdout("\nRules and remediation: .claude/skills/skill-structure-check/SKILL.md");
    if (audit.errors.length > 0) {
        return 1;
    }
    return strict &&
        (audit.warnings.length > 0 || audit.missingContents.length > 0)
        ? 1
        : 0;
}
//# sourceMappingURL=skill-structure.js.map