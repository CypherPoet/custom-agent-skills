import { existsSync, readFileSync, } from "node:fs";
import { dirname, resolve } from "node:path";
import { VENDORED_SKILLS_CONFIGURATION } from "./constants.js";
import { repositoryVisibleFiles } from "./file-tree.js";
import { isJsonObject } from "./types.js";
import { applyVendoredSkillsPlan, prepareVendoredSkillsPlan, } from "./vendored-skills.js";
function loadConfiguration(root) {
    const path = resolve(root, VENDORED_SKILLS_CONFIGURATION);
    let text;
    try {
        text = readFileSync(path, "utf8");
    }
    catch (error) {
        return {
            problems: [
                `[config] could not read ${VENDORED_SKILLS_CONFIGURATION}: ${String(error)}`,
            ],
        };
    }
    let value;
    try {
        value = JSON.parse(text);
    }
    catch (error) {
        return {
            problems: [
                `[config] ${VENDORED_SKILLS_CONFIGURATION} is not valid JSON: ${String(error)}`,
            ],
        };
    }
    if (!isJsonObject(value)) {
        return {
            problems: [`[config] ${VENDORED_SKILLS_CONFIGURATION} must contain an object`],
        };
    }
    if (!Array.isArray(value.skills)) {
        return { problems: ["[config] skills must be an array"] };
    }
    return {
        configuration: value,
        problems: [],
    };
}
export function synchronizeVendoredSkills(rootPath, write) {
    const root = resolve(rootPath);
    const loaded = loadConfiguration(root);
    if (loaded.configuration === undefined) {
        return loaded.problems;
    }
    const visible = repositoryVisibleFiles(root);
    const plan = prepareVendoredSkillsPlan(root, loaded.configuration, write, visible);
    if (write && plan.problems.length === 0) {
        applyVendoredSkillsPlan(root, plan);
    }
    return plan.problems;
}
export function findRepositoryRoot(start) {
    let candidate = resolve(start);
    for (;;) {
        if (existsSync(resolve(candidate, "plugins")) &&
            existsSync(resolve(candidate, VENDORED_SKILLS_CONFIGURATION))) {
            return candidate;
        }
        const parent = dirname(candidate);
        if (parent === candidate) {
            throw new Error(`could not locate repo root (needs plugins/ and ${VENDORED_SKILLS_CONFIGURATION})`);
        }
        candidate = parent;
    }
}
//# sourceMappingURL=sync.js.map