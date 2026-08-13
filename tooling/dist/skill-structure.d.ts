export declare const SKILL_LINE_LIMIT = 500;
export declare const SKILL_LINE_WARNING = 450;
export declare const REFERENCE_CONTENTS_THRESHOLD = 300;
export type StructureFinding = readonly [label: string, location: string, message: string];
export interface StructureAudit {
    errors: StructureFinding[];
    warnings: StructureFinding[];
    missingContents: Array<readonly [label: string, file: string]>;
}
interface GateOutput {
    stdout(message: string): void;
    stderr(message: string): void;
}
export declare function findStructureRepositoryRoot(start: string): string | undefined;
export declare function githubHeadingAnchor(heading: string): string;
export declare function stripCodeFences(text: string): string;
export declare function headingAnchors(text: string): Set<string>;
export declare function contentsAnchors(text: string): string[] | undefined;
export declare function escapingLinks(text: string, markdownPath: string, pluginRoot: string): string[];
export declare function auditSkillStructure(pluginsDirectory: string): StructureAudit;
export declare function runSkillStructureCheck(rootPath: string, strict: boolean, output?: GateOutput): number;
export {};
