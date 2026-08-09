export declare function normalizedUniquenessKey(value: string, ignoreCase: boolean): string;
export declare function validateText(value: unknown, field: string, maximumLength: number, allowLineFeed?: boolean): string[];
export declare function validateUrl(value: unknown, field: string, maximumLength: number): string[];
export declare function validateCodexInterface(interfaceValue: unknown, options?: {
    sourceHomepage?: unknown;
}): string[];
export declare function validateAuthoredInterfaceMetadata(name: string, pluginMetadata: unknown): string[];
