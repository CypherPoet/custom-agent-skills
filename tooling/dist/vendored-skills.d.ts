import type { FileTree, VendoredSkillsConfiguration } from "./types.js";
export interface VendoredSkillsPlan {
    targetTrees: Map<string, FileTree>;
    retiredTargets: string[];
    problems: string[];
}
export declare function prepareVendoredSkillsPlan(root: string, configuration: VendoredSkillsConfiguration, write: boolean, visible: ReadonlySet<string> | undefined): VendoredSkillsPlan;
export declare function applyVendoredSkillsPlan(root: string, plan: VendoredSkillsPlan): void;
