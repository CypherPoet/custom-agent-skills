import type { FileTree, PluginRegistry } from "./types.js";
export interface VendoredSkillsPlan {
    targetTrees: Map<string, FileTree>;
    retiredTargets: string[];
    problems: string[];
}
export declare function prepareVendoredSkillsPlan(root: string, configuration: PluginRegistry, write: boolean, visible: ReadonlySet<string> | undefined): VendoredSkillsPlan;
export declare function applyVendoredSkillsPlan(root: string, plan: VendoredSkillsPlan): void;
