import { rmSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { SYNC_COMMAND, VENDORED_SKILLS_CONFIGURATION } from "./constants.js";
import { baseVisibleFiles, desiredVendorTargets, fileTreesEqual, gitCleanUnder, pathExistsOrIsSymbolicLink, pathIsSymbolicLink, previousVendorTargets, readTree, skillDirectories, treeDigest, writeTree, } from "./file-tree.js";
export function prepareVendoredSkillsPlan(root, configuration, write, visible) {
    const { desired: desiredTargets, problems } = desiredVendorTargets(configuration);
    const targetTrees = new Map();
    const retiredTargets = [];
    if (problems.length > 0) {
        return { targetTrees, retiredTargets, problems };
    }
    const tree = (relativePath) => readTree(resolve(root, relativePath), baseVisibleFiles(visible, relativePath));
    const handled = new Set(desiredTargets.keys());
    for (const target of Array.from(previousVendorTargets(root)).sort()) {
        if (desiredTargets.has(target)) {
            continue;
        }
        const destination = resolve(root, target);
        handled.add(target);
        if (!pathExistsOrIsSymbolicLink(destination)) {
            continue;
        }
        if (!write) {
            problems.push(`[vendor] stale generated copy: ${target} ` +
                `(edge removed from ${VENDORED_SKILLS_CONFIGURATION}; run: ${SYNC_COMMAND})`);
            continue;
        }
        if (pathIsSymbolicLink(destination) ||
            !statSync(destination).isDirectory() ||
            !gitCleanUnder(root, target)) {
            problems.push(`[vendor] retired copy has uncommitted or untracked content; refusing to remove: ${target} ` +
                "(commit or move that work first, or delete the directory yourself to adopt it)");
            continue;
        }
        retiredTargets.push(target);
    }
    const sourceTrees = new Map();
    for (const [target, source] of Array.from(desiredTargets.entries()).sort(([left], [right]) => left.localeCompare(right, "en"))) {
        if (!pathExistsOrIsSymbolicLink(resolve(root, source))) {
            problems.push(`[vendor] source missing: ${source}`);
            continue;
        }
        const sourceTree = sourceTrees.get(source) ?? tree(source);
        sourceTrees.set(source, sourceTree);
        if (sourceTree.size === 0) {
            problems.push(`[vendor] source has no vendorable files: ${source}`);
            continue;
        }
        targetTrees.set(target, sourceTree);
        if (!write && !fileTreesEqual(tree(target), sourceTree)) {
            problems.push(`[vendor] out of sync: ${target} != ${source} (run: ${SYNC_COMMAND})`);
        }
    }
    const sourceDigests = new Map();
    for (const [source, files] of sourceTrees) {
        if (files.size > 0) {
            sourceDigests.set(treeDigest(files), source);
        }
    }
    if (sourceDigests.size > 0) {
        for (const skillDirectory of skillDirectories(root)) {
            if (handled.has(skillDirectory) || sourceTrees.has(skillDirectory)) {
                continue;
            }
            const files = tree(skillDirectory);
            if (files.size === 0) {
                continue;
            }
            const matchingSource = sourceDigests.get(treeDigest(files));
            if (matchingSource !== undefined) {
                problems.push(`[vendor] undeclared byte-identical copy of ${matchingSource}: ${skillDirectory} — ` +
                    "declare a vendored skill edge, delete the directory, or change its content to adopt it as authored");
            }
        }
    }
    return { targetTrees, retiredTargets, problems };
}
export function applyVendoredSkillsPlan(root, plan) {
    for (const target of plan.retiredTargets) {
        rmSync(resolve(root, target), { recursive: true });
    }
    for (const [target, sourceTree] of plan.targetTrees) {
        writeTree(sourceTree, resolve(root, target));
    }
}
//# sourceMappingURL=vendored-skills.js.map