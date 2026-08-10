#!/usr/bin/env node

import { runVersionBumpCheck } from "./version-bumps.js";

const arguments_ = process.argv.slice(2);
if (arguments_.length > 1) {
  console.error("Usage: check-version-bumps [base-ref]");
  process.exitCode = 2;
} else {
  process.exitCode = runVersionBumpCheck(process.cwd(), arguments_[0]);
}
