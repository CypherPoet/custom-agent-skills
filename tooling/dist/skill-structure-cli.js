#!/usr/bin/env node
import { runSkillStructureCheck } from "./skill-structure.js";
const arguments_ = process.argv.slice(2);
const invalid = arguments_.filter((argument) => argument !== "--strict");
if (invalid.length > 0) {
    console.error("Usage: check-skill-structure [--strict]");
    process.exitCode = 2;
}
else {
    process.exitCode = runSkillStructureCheck(process.cwd(), arguments_.includes("--strict"));
}
//# sourceMappingURL=skill-structure-cli.js.map