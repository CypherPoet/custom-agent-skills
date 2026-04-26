---
name: design-md-lint
description: >
  Audit a project's DESIGN.md file against the Google Labs design.md spec
  (https://github.com/google-labs-code/design.md). Use this skill whenever the
  user asks to lint, audit, validate, check, review, or QA a DESIGN.md file —
  even if they don't explicitly name the spec. Also trigger when the user says
  "what's wrong with my DESIGN.md", "is my design system spec valid", "review
  my design tokens file", "check my design.md", or asks how to make a
  DESIGN.md better. The skill produces a severity-tiered report (errors,
  warnings, suggestions) with concrete fixes and improvement ideas — it does
  not modify the file.
---

# DESIGN.md Lint

Audit a `DESIGN.md` file against the [google-labs-code/design.md](https://github.com/google-labs-code/design.md) spec and return a structured report with severity-labeled findings and improvement ideas.

The spec defines a two-part format: YAML frontmatter (machine-readable design tokens — colors, typography, spacing, rounded, components) plus a markdown body with eight ordered sections. Some rules are hard (`name` is required, no duplicate sections, broken token refs are errors); most are softer recommendations about content quality (the prose should explain rationale, primary palette should be present, typography typically spans 9–15 levels). This skill flags both kinds — and goes a step further by surfacing improvement ideas the spec doesn't enforce but that make a DESIGN.md genuinely useful to a coding agent.

The output is a report. The skill never edits the user's DESIGN.md.

## Workflow

### Phase 1: Locate the file

Look for the file in this order, stopping at the first match:

1. The path the user gave you, if any.
2. `./DESIGN.md` (project root).
3. `./docs/DESIGN.md`.

If none of those exist, ask the user where the file is rather than guessing further.

### Phase 2: Load the rule catalog

Before auditing, read `references/spec-rules.md`. It is the source of truth for every rule's ID, severity, and fix guidance. The body of this SKILL.md describes *how* to audit; the catalog describes *what* to check. Don't try to remember rules from memory — read the catalog so reports stay consistent with current rule IDs.

### Phase 3: Parse the file

Split the file into:
- **Frontmatter**: everything between the first two `---` lines (if present).
- **Body**: everything after the closing `---`.

Track line numbers throughout — every finding needs a location so the user can navigate to it.

If the file has no frontmatter delimiters at all, that's an `Error` (`structure/no-frontmatter`) and most token-related rules will be inapplicable. Run the body-only checks anyway — section ordering, prose quality, and content suggestions are still useful.

### Phase 4: Run the checks

Apply rules in this order — earlier categories surface foundational issues that make later checks more meaningful:

1. **Structure** — frontmatter delimiters present, no duplicate section headings, sections in required order. (See `structure/*` rules.)
2. **Frontmatter schema** — required `name` field, valid hex colors, typography properties, dimension formats. (`frontmatter/*`.)
3. **Token references** — `{path.to.token}` syntax, referent exists in frontmatter, primitive-only outside the components section. (`refs/*`.)
4. **Completeness** — primary color palette, typography level count, prose presence in each section, recommended component states. (`completeness/*`.)
5. **Content quality** — Overview brand tone, naming consistency, Do's and Don'ts concreteness, accessibility hints. (`content/*`.)

For each rule, decide: does this file violate it? If yes, capture a finding with the rule's ID, severity, location, what's wrong, and a concrete fix.

### Phase 5: Generate cross-cutting improvement ideas

After per-rule checks, step back and look at the whole file. Some valuable observations don't map to a single rule. Examples:

- The Overview is structurally fine but feels generic — consider tying brand tone to 2–3 concrete adjectives and reinforcing them in Typography and Shapes prose.
- Color tokens use semantic names (`primary`, `secondary`) but typography uses size-only names (`text-lg`, `text-md`) — the file would benefit from one consistent naming philosophy.
- Components section covers default states well but doesn't address `hover`, `focus`, or `disabled` for any component — a coding agent would have to guess these.

Put these in an "Overall improvement ideas" section at the end of the report. Three to five ideas is usually plenty — quality over quantity.

### Phase 6: Render the report

Use the template in `assets/report-template.md`. Fill in:

- Summary counts at the top
- Findings grouped by severity (Errors → Warnings → Suggestions)
- Each finding has: rule ID, where, issue, fix
- Cross-cutting improvement ideas at the end

Output the report directly in the conversation as markdown. If the user asked you to save it (e.g., "write the report to AUDIT.md"), do that.

## Severity model

Three tiers, mirroring the spec repo's own `lint` command so reports align with upstream tooling:

- **Error** — MUST violations. The file is non-conformant against the spec. Common causes: no frontmatter, missing `name`, duplicate section headings, sections out of order, broken token reference, invalid hex color, composite token reference outside the components section.

- **Warning** — SHOULD violations. The file is structurally valid but misses strong recommendations. Common causes: no primary color palette, typography count well outside the recommended 9–15 levels, orphaned tokens (defined but never referenced), section heading present but no prose, low-contrast color pairs, inconsistent token naming within a group.

- **Suggestion** — MAY-level / improvement ideas. The file works as-is; these are quality lifts. Common causes: shallow Overview that lacks brand tone, missing interaction states (`hover`, `focus`, `disabled`) for components, scale-name inconsistencies, missing colorblind considerations, opportunities to strengthen rationale prose.

The severity *categorizes* a finding; it doesn't gate behavior. Always report all three tiers — even a clean file usually has a few suggestions.

## Report shape

The `assets/report-template.md` file shows the canonical layout. The structure is:

```
# DESIGN.md Audit — <path>

**Summary:** N errors, N warnings, N suggestions  •  spec: design.md v0.1.0

## Errors
### [rule-id] Short title
**Where:** line/section
**Issue:** what's wrong
**Fix:** concrete change

## Warnings
…

## Suggestions
…

## Overall improvement ideas
- Cross-cutting ideas
```

Skip the Errors / Warnings / Suggestions section entirely if it's empty — don't print "Errors: none". The summary line already conveys that.

## Why each rule needs an ID

Reports get re-run as the file evolves. Stable rule IDs (e.g., `structure/duplicate-section`, `refs/broken-reference`) let the user grep across reports, suppress specific rules, or correlate against the upstream linter. Always cite the ID in findings — don't invent new wording each run.

## Constraints

- **Read-only.** Never modify the DESIGN.md being audited. Suggestions describe changes; the user applies them.
- **Cite the spec.** When reporting a MUST/SHOULD violation, the rule entry in `references/spec-rules.md` includes the spec language — reuse it so the user can trust the call.
- **Be concrete in fixes.** "Fix the section order" is unhelpful. "Move `## Shapes` above `## Components` (currently at line 142, should be at line 118)" is what the user can act on.
- **Don't pile on.** If 12 typography levels share the same root issue (missing `letterSpacing`), report once at the group level, not 12 times.
- **Stay calibrated on severity.** A subjective preference is a Suggestion, not a Warning. Reserve Errors for things the spec explicitly forbids or requires.
- **Don't guess at intent.** If a section's content is sparse but plausibly deliberate (e.g., a minimalist design system), say so in the suggestion rather than asserting it's wrong.

## When the file is clean

A DESIGN.md can be fully spec-compliant. If so, say it directly:

> No errors or warnings. The file conforms to design.md v0.1.0.

Then offer 2–3 improvement suggestions if you have any worth making. If the file is also content-rich and you have nothing meaningful to add, say that too — don't manufacture suggestions to fill space.
