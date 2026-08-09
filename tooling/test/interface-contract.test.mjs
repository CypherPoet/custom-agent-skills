import assert from "node:assert/strict";
import test from "node:test";

import { validateCodexInterface } from "../dist/index.js";

const validInterface = {
  displayName: "Example Tools",
  shortDescription: "Build example workflows",
  longDescription: "Build and validate example workflows.",
  developerName: "CypherPoet",
  category: "Developer Tools",
  capabilities: ["Read", "Write"],
  websiteURL: "https://example.com/plugins/example",
  defaultPrompt: ["Build an example workflow for this task."],
};

function validate(interfaceValue = validInterface, sourceHomepage) {
  return validateCodexInterface(structuredClone(interfaceValue), { sourceHomepage });
}

function assertInvalid(field, value, expected) {
  const interfaceValue = structuredClone(validInterface);
  interfaceValue[field] = value;
  const problems = validate(interfaceValue);
  assert.ok(problems.some((problem) => problem.includes(expected)), `${expected}: ${problems.join("; ")}`);
}

test("a complete Codex interface passes", () => {
  assert.deepEqual(validate(validInterface, validInterface.websiteURL), []);
});

test("display names enforce text and length rules", () => {
  for (const [value, expected] of [
    [null, "must be a non-empty string"],
    ["", "must be a non-empty string"],
    [" Example Tools", "must not contain surrounding whitespace"],
    ["Example\nTools", "must be a single line"],
    ["x".repeat(31), "must be at most 30"],
    ["Example\u200bTools", "unsupported text characters"],
  ]) {
    assertInvalid("displayName", value, expected);
  }
});

test("descriptions enforce their separate limits", () => {
  assertInvalid("shortDescription", "x".repeat(31), "at most 30");
  assertInvalid("shortDescription", "two\nlines", "single line");
  assertInvalid("longDescription", "x".repeat(4_001), "at most 4000");
  assertInvalid("longDescription", "Paragraph one.\u2028Paragraph two.", "unsupported text characters");
  assert.deepEqual(validate({ ...validInterface, longDescription: "One.\nTwo." }), []);
});

test("developer names and categories enforce the Codex contract", () => {
  assertInvalid("developerName", "x".repeat(81), "at most 80");
  assertInvalid("developerName", " CypherPoet", "surrounding whitespace");
  assertInvalid("category", "Design", "must be one of");
  assertInvalid("category", "Developer Tools ", "surrounding whitespace");
});

test("capabilities are free-form, bounded, and normalized for uniqueness", () => {
  assert.deepEqual(
    validate({ ...validInterface, capabilities: ["Run network requests", "Transform files"] }),
    [],
  );
  for (const [value, expected] of [
    [[], "between 1 and 20"],
    [Array.from({ length: 21 }, (_, index) => `Capability ${index}`), "between 1 and 20"],
    [["x".repeat(121)], "at most 120"],
    [["Read", "read"], "duplicates"],
    [["Read", "Ｒｅａｄ"], "duplicates"],
    [[" Read"], "surrounding whitespace"],
    [[{ name: "Read" }], "must be a non-empty string"],
  ]) {
    assertInvalid("capabilities", value, expected);
  }
});

test("starter prompts allow one to three normalized unique strings", () => {
  assert.deepEqual(
    validate({
      ...validInterface,
      defaultPrompt: ["First task.", "Second task.", "Third task."],
    }),
    [],
  );
  for (const [value, expected] of [
    [[], "between 1 and 3"],
    [["one", "two", "three", "four"], "between 1 and 3"],
    [["x".repeat(129)], "at most 128"],
    [["Build it.", "Build  it."], "duplicates"],
    [["Ａudit it.", "Audit it."], "duplicates"],
    [[" Build it."], "surrounding whitespace"],
    [["Ask @Linear to create an issue."], "must not contain an app @mention"],
    [[{ prompt: "Build it." }], "must be a non-empty string"],
  ]) {
    assertInvalid("defaultPrompt", value, expected);
  }
  assert.deepEqual(
    validate({ ...validInterface, defaultPrompt: ["Build it.", "build it."] }),
    [],
  );
});

test("website URLs and source composition are validated", () => {
  for (const [value, expected] of [
    ["http://example.com", "absolute https URL"],
    ["https:///missing-host", "absolute https URL"],
    ["https://user:secret@example.com", "must not contain credentials"],
    ["https://example.com/a path", "unsupported URL characters"],
    ["https://example.com/<bad>", "unsupported URL characters"],
    [`https://example.com/${"x".repeat(1_005)}`, "at most 1024"],
  ]) {
    assertInvalid("websiteURL", value, expected);
  }
  assert.ok(validate(validInterface, "https://example.com/other").some((problem) =>
    problem.includes("must equal the source homepage"),
  ));
  assert.ok(validate(validInterface, `https://example.com/${"x".repeat(2_030)}`).some((problem) =>
    problem.includes("source homepage must be at most 2048"),
  ));
});

test("the interface must be an object", () => {
  assert.deepEqual(validate([]), ["interface must be an object"]);
});
