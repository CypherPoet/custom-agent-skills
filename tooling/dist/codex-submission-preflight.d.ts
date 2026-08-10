export declare function normalizedUniquenessKey(value: string, ignoreCase: boolean): string;
export declare function validateSubmissionText(value: unknown, field: string, maximumLength: number, allowLineFeed?: boolean): string[];
/** Codex's documented final-directory submission rules for interface metadata. */
export declare function validateCodexSubmissionInterface(interfaceValue: unknown): string[];
/** CypherPoet authoring choices layered on top of Codex's submission contract. */
export declare function validateRepositoryInterfacePolicy(interfaceValue: unknown, sourceHomepage: unknown): string[];
export declare function validateGeneratedCodexInterface(interfaceValue: unknown, sourceHomepage: unknown): string[];
export declare function validateAuthoredRegistryInterface(name: string, pluginMetadata: unknown): string[];
