import assert from "node:assert/strict";
import test from "node:test";

import {
  validateAuthoredRegistryInterface,
  validateCodexSubmissionInterface,
  validateGeneratedCodexInterface,
  validateRepositoryInterfacePolicy,
} from "../dist/index.js";

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

function validate(interfaceValue = validInterface, sourceHomepage = validInterface.websiteURL) {
  return validateGeneratedCodexInterface(structuredClone(interfaceValue), sourceHomepage);
}

function assertInvalid(field, value, expected) {
  const interfaceValue = structuredClone(validInterface);
  interfaceValue[field] = value;
  const problems = validate(interfaceValue);
  assert.ok(
    problems.some((problem) => problem.includes(expected)),
    `${expected}: ${problems.join("; ")}`,
  );
}

test("a complete generated Codex interface passes both validation layers", () => {
  assert.deepEqual(validate(), []);
});

test("Codex submission fields enforce text and length rules", () => {
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
  assertInvalid("shortDescription", "x".repeat(31), "at most 30");
  assertInvalid("shortDescription", "two\nlines", "single line");
  assertInvalid("longDescription", "x".repeat(4_001), "at most 4000");
  assertInvalid(
    "longDescription",
    "Paragraph one.\u2028Paragraph two.",
    "unsupported text characters",
  );
  assert.deepEqual(validate({ ...validInterface, longDescription: "One.\nTwo." }), []);
});

test("developer names and categories enforce the Codex submission contract", () => {
  assertInvalid("developerName", "x".repeat(81), "at most 80");
  assertInvalid("developerName", " CypherPoet", "surrounding whitespace");
  assertInvalid("category", "Design", "must be one of");
  assertInvalid("category", "Developer Tools ", "surrounding whitespace");
});

test("Codex submission lists are free-form and bounded", () => {
  assert.deepEqual(
    validateCodexSubmissionInterface({
      ...validInterface,
      capabilities: ["Run network requests", "Transform files"],
    }),
    [],
  );
  for (const [field, value, expected] of [
    ["capabilities", Array.from({ length: 21 }, (_, index) => `Capability ${index}`), "at most 20"],
    ["capabilities", ["x".repeat(121)], "at most 120"],
    ["capabilities", [" Read"], "surrounding whitespace"],
    ["capabilities", [{ name: "Read" }], "must be a non-empty string"],
    ["defaultPrompt", ["one", "two", "three", "four"], "at most 3"],
    ["defaultPrompt", ["x".repeat(129)], "at most 128"],
    ["defaultPrompt", [" Build it."], "surrounding whitespace"],
    ["defaultPrompt", ["Ask @Linear to create an issue."], "must not contain an app @mention"],
    ["defaultPrompt", [{ prompt: "Build it." }], "must be a non-empty string"],
  ]) {
    assertInvalid(field, value, expected);
  }
});

test("repository policy requires populated unique capabilities and prompts", () => {
  for (const [field, value, expected] of [
    ["capabilities", [], "at least 1"],
    ["capabilities", ["Read", "read"], "duplicates"],
    ["capabilities", ["Read", "Ｒｅａｄ"], "duplicates"],
    ["defaultPrompt", [], "at least 1"],
    ["defaultPrompt", ["Build it.", "Build  it."], "duplicates"],
    ["defaultPrompt", ["Ａudit it.", "Audit it."], "duplicates"],
  ]) {
    assertInvalid(field, value, expected);
  }
  assert.deepEqual(
    validate({ ...validInterface, defaultPrompt: ["Build it.", "build it."] }),
    [],
  );
  assert.deepEqual(
    validateCodexSubmissionInterface({
      ...validInterface,
      capabilities: [],
      defaultPrompt: [],
    }),
    [],
  );
});

test("website submission rules and repository composition are separate", () => {
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
  assert.ok(
    validateRepositoryInterfacePolicy(validInterface, "https://example.com/other").some(
      (problem) => problem.includes("must equal the source homepage"),
    ),
  );
  assert.ok(
    validateRepositoryInterfacePolicy(
      validInterface,
      `https://example.com/${"x".repeat(2_030)}`,
    ).some((problem) => problem.includes("source homepage must be at most 2048")),
  );
});

test("authored registry validation checks only authored fields", () => {
  const metadata = {
    category: "Developer Tools",
    interface: {
      displayName: "Example Tools",
      shortDescription: "Build example workflows",
      capabilities: ["Read", "Write"],
      defaultPrompt: ["Build an example workflow for this task."],
    },
  };
  assert.deepEqual(validateAuthoredRegistryInterface("example", metadata), []);
  assert.ok(
    validateAuthoredRegistryInterface("example", {
      ...metadata,
      separateCodexPackage: null,
    }).some((problem) => problem.includes("separateCodexPackage must be a boolean")),
  );
  assert.ok(
    validateAuthoredRegistryInterface("example", {
      ...metadata,
      codexProjection: true,
    }).some((problem) => problem.includes("codexProjection is not supported")),
  );
});

test("the interface must be an object", () => {
  assert.deepEqual(validateCodexSubmissionInterface([]), ["interface must be an object"]);
});
