# DESIGN.md Lint — Rule Catalog

Source: [google-labs-code/design.md](https://github.com/google-labs-code/design.md), `docs/spec.md` (alpha / v0.1.0).

Each rule has a stable ID (`category/short-name`), a severity, what it checks, why it matters, and concrete fix guidance. The skill reads this file before auditing so reports stay aligned with upstream language.

## Rule index

| ID | Severity |
|----|----------|
| `structure/no-frontmatter` | Error |
| `structure/unclosed-frontmatter` | Error |
| `structure/duplicate-section` | Error |
| `structure/section-order` | Error |
| `structure/h1-misuse` | Suggestion |
| `frontmatter/missing-name` | Error |
| `frontmatter/invalid-hex` | Error |
| `frontmatter/typography-missing-property` | Error |
| `frontmatter/dimension-format` | Warning |
| `frontmatter/unknown-version` | Warning |
| `refs/broken-reference` | Error |
| `refs/composite-outside-components` | Error |
| `refs/malformed-syntax` | Error |
| `completeness/missing-primary` | Warning |
| `completeness/typography-count` | Warning |
| `completeness/empty-section` | Warning |
| `completeness/orphaned-tokens` | Warning |
| `completeness/missing-component-states` | Suggestion |
| `completeness/missing-overview` | Suggestion |
| `completeness/missing-dos-and-donts` | Suggestion |
| `content/shallow-overview` | Suggestion |
| `content/naming-inconsistency` | Warning |
| `content/missing-rationale` | Suggestion |
| `content/dos-and-donts-vague` | Suggestion |
| `content/contrast-risk` | Warning |
| `content/colorblind-consideration` | Suggestion |
| `content/scale-progression` | Suggestion |

---

## Structure (`structure/*`)

### `structure/no-frontmatter` — **Error**
**Checks:** The file has no `---` delimited YAML frontmatter block at the top.
**Why:** The spec defines DESIGN.md as a two-part format. Without frontmatter, there are no machine-readable tokens, and the file falls outside the format.
**Fix:** Add a frontmatter block at the top: `---\nname: <project name>\n---`. Then move design tokens (colors, typography, spacing, rounded, components) into the frontmatter as YAML.

### `structure/unclosed-frontmatter` — **Error**
**Checks:** A `---` opening delimiter exists but no closing `---` is found.
**Why:** Parsers can't distinguish frontmatter from body. The file is unparseable as DESIGN.md.
**Fix:** Add a closing `---` line after the last YAML field, before the markdown body begins.

### `structure/duplicate-section` — **Error**
**Checks:** The same `##` section heading appears more than once (e.g., two `## Colors` sections).
**Why:** The spec explicitly rejects files with duplicate section headings. Tools cannot merge them safely.
**Fix:** Combine the duplicate sections into one. If they cover distinct subtopics, use `###` subheadings within a single `##` section.

### `structure/section-order` — **Error**
**Checks:** Sections appear in an order other than: Overview → Colors → Typography → Layout → Elevation & Depth → Shapes → Components → Do's and Don'ts.
**Why:** The spec states that sections, if present, MUST follow this sequence. Sections may be omitted, but the relative order of those present must hold.
**Fix:** Reorder the sections to match the canonical sequence. Cite both the offending section and where it should be moved (line numbers).

### `structure/h1-misuse` — **Suggestion**
**Checks:** Multiple `#` h1 headings, or no h1 at all.
**Why:** A single h1 makes the document's title clear. Not a spec requirement, but conventional.
**Fix:** Use exactly one h1 at the top of the markdown body for the document title.

---

## Frontmatter schema (`frontmatter/*`)

### `frontmatter/missing-name` — **Error**
**Checks:** The frontmatter does not contain a top-level `name:` field, or it's empty.
**Why:** The spec lists `name` as the only required field.
**Fix:** Add `name: <Your Design System Name>` to the frontmatter.

### `frontmatter/invalid-hex` — **Error**
**Checks:** Any color token whose value is not a valid 6-digit sRGB hex (`#XXXXXX`). Also flags 3-digit hex (`#FFF`), named colors, `rgb()`/`rgba()`/`hsl()` functions in places where the spec calls for hex.
**Why:** The spec specifies hex `#XXXXXX` in sRGB for color tokens.
**Fix:** Convert to 6-digit hex. (If transparency is genuinely needed, that's typically expressed in component prose, not in the base color token.)

### `frontmatter/typography-missing-property` — **Error**
**Checks:** A typography token missing one of the required properties: `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`.
**Why:** Without these, a coding agent cannot reproduce the typography style.
**Fix:** Add the missing property. Cite the token name and what's missing in the report.

### `frontmatter/dimension-format` — **Warning**
**Checks:** Dimension values that lack units or use non-standard units (e.g., `fontSize: 16` without `px`, `padding: 8em` mixed with `padding: 16px` siblings).
**Why:** Mixed/missing units force consumers to guess the intended unit and undermine consistency.
**Fix:** Standardize on `px`, `rem`, or `em` within a token group. State the chosen unit if helpful.

### `frontmatter/unknown-version` — **Warning**
**Checks:** A `version:` field set to anything other than `alpha` (the only currently defined value).
**Why:** Future tooling may key behavior off the version. Unknown values may be misinterpreted.
**Fix:** Either omit the `version` field or set it to `alpha`.

---

## Token references (`refs/*`)

### `refs/broken-reference` — **Error**
**Checks:** A `{path.to.token}` reference whose target does not exist in the frontmatter.
**Why:** Broken references silently produce missing styles in consumers. The upstream linter classifies these as errors.
**Fix:** Either correct the path (typo) or define the missing token in the frontmatter.

### `refs/composite-outside-components` — **Error**
**Checks:** A reference to a composite value (e.g., a typography object) used outside the `components` section.
**Why:** The spec restricts composite references to `components`. Outside that scope, only primitives may be referenced.
**Fix:** Move the reference into a component definition, or replace it with a primitive token.

### `refs/malformed-syntax` — **Error**
**Checks:** A token reference that looks intended but doesn't use the `{path.to.token}` syntax (e.g., `$colors.primary`, `colors.primary`, `${colors.primary}`).
**Why:** Tools won't resolve non-canonical syntaxes.
**Fix:** Wrap in curly braces with dot-path notation: `{colors.primary}`.

---

## Completeness (`completeness/*`)

### `completeness/missing-primary` — **Warning**
**Checks:** The `colors` group has no `primary` palette (or single primary token).
**Why:** Primary is the anchor of the system — most components reference it directly or indirectly.
**Fix:** Add a `primary` color (or palette with `primary.500` style scale) and reference it from at least one component.

### `completeness/typography-count` — **Warning**
**Checks:** Fewer than 6 or more than 18 typography tokens.
**Why:** The spec recommends 9–15 levels. Fewer tends to under-serve real interfaces; many more usually indicates redundancy that's hard to maintain.
**Fix:** Consolidate (if too many) or expand (if too few). Aim for semantic names like `headline-lg`, `body-md`, `label-sm`.

### `completeness/empty-section` — **Warning**
**Checks:** A section heading is present but has no prose (or only a token list with no narrative).
**Why:** The spec states the prose provides context for the tokens — without it, the section's intent isn't communicable.
**Fix:** Add at least a short paragraph explaining the section's purpose, philosophy, or rules-of-use.

### `completeness/orphaned-tokens` — **Warning**
**Checks:** A token defined in frontmatter that's never referenced anywhere (neither by other tokens nor by the prose body).
**Why:** Orphaned tokens drift over time and add noise. Either they should be used or removed.
**Fix:** Reference the token from a component or section, or delete it.

### `completeness/missing-component-states` — **Suggestion**
**Checks:** A component is defined but has no variant for `hover`, `focus`, `active`, `disabled`, or `pressed`.
**Why:** Coding agents implementing the component will have to invent states, which produces inconsistency.
**Fix:** Add `<component>-<state>` entries (e.g., `button-primary-hover`) — or describe the state changes in the component's prose.

### `completeness/missing-overview` — **Suggestion**
**Checks:** No `## Overview` (or `## Brand & Style`) section at all.
**Why:** Overview anchors the rest of the document — brand tone, target audience, emotional intent. Its absence makes downstream sections feel ungrounded.
**Fix:** Add a short Overview that establishes brand personality and the kind of product this is.

### `completeness/missing-dos-and-donts` — **Suggestion**
**Checks:** No `## Do's and Don'ts` section.
**Why:** Practical guardrails (contrast minimums, weight limits, color usage rules) prevent recurring mistakes that prose alone doesn't catch.
**Fix:** Add a short list of concrete do's and don'ts.

---

## Content quality (`content/*`)

### `content/shallow-overview` — **Suggestion**
**Checks:** The Overview is present but generic — no specific brand tone, no audience, no emotional adjectives. (Heuristic: under ~50 words, or only describes "we use modern design.")
**Why:** Vague Overviews don't help an agent make stylistic judgment calls when explicit rules don't cover the case.
**Fix:** Name 2–3 concrete brand adjectives, the audience, and the emotional outcome the design aims for. Reinforce these in Typography and Shapes prose.

### `content/naming-inconsistency` — **Warning**
**Checks:** Token names within a group mix conventions (e.g., `primary-500` and `secondaryColor` in the same colors block; `text-lg` and `headline-large` in the same typography block).
**Why:** Inconsistent naming forces readers to learn multiple conventions and creates ambiguity.
**Fix:** Pick one naming convention per group and apply it across all tokens in that group.

### `content/missing-rationale` — **Suggestion**
**Checks:** A section presents tokens without explaining why those choices were made (no language like "because", "to convey", "we chose", "in order to").
**Why:** Rationale lets future contributors and AI agents make consistent decisions when extending the system.
**Fix:** For each major section, include 1–2 sentences of rationale tying tokens back to brand or function.

### `content/dos-and-donts-vague` — **Suggestion**
**Checks:** Do's and Don'ts entries are abstract (e.g., "Don't use too many colors") rather than concrete (e.g., "Don't combine `primary-600` and `error-500` in the same view").
**Why:** Vague guardrails don't prevent specific mistakes.
**Fix:** Rewrite each entry to name specific tokens, properties, or contexts.

### `content/contrast-risk` — **Warning**
**Checks:** Heuristic check for low-contrast pairings — e.g., a `textColor` and `backgroundColor` defined on the same component whose computed luminance contrast is likely under WCAG AA (4.5:1 for body text). Flag conservatively; you don't have to compute exactly, just call out plausibly risky pairs.
**Why:** Accessibility is a foundational concern that DESIGN.md should address, even if the spec doesn't enforce a number.
**Fix:** Verify contrast in a tool (e.g., WebAIM contrast checker) and adjust one of the two colors, or note the WCAG level the system targets.

### `content/colorblind-consideration` — **Suggestion**
**Checks:** Status colors (success/error/warning) are defined but the file doesn't mention colorblind considerations or non-color status indicators (icons, text labels).
**Why:** ~8% of users have some form of color vision deficiency. Status that's only conveyed by hue is invisible to them.
**Fix:** Add a Do's and Don'ts entry or a sentence in Colors prose noting that status should be reinforced by icon or label, not color alone.

### `content/scale-progression` — **Suggestion**
**Checks:** A spacing or typography scale where adjacent steps don't follow a regular progression (e.g., 4, 8, 12, 32 — the jump from 12 to 32 is conspicuous).
**Why:** Irregular scales produce visually inconsistent rhythm.
**Fix:** Adjust the outliers to fit a geometric (e.g., 1.25× or 1.5×) or linear progression — or document why the outlier exists.

---

## Notes for the auditor

- When a fixture is missing whole sections, prefer the `completeness/missing-*` rules at Suggestion level over flagging dozens of downstream rule violations. Cascading errors don't help the user.
- Rule IDs are stable. If a rule changes meaning materially, introduce a new ID rather than redefining an existing one.
- The spec is in alpha — when its language is ambiguous, lean toward Suggestion. Reserve Error for things the spec explicitly forbids or requires.
