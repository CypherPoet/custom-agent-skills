# DESIGN.md Audit — `<path/to/DESIGN.md>`

**Summary:** `<N>` errors, `<N>` warnings, `<N>` suggestions  •  spec: design.md v0.1.0

<!--
Render only the severity sections that have findings. If there are no errors,
omit "## Errors" entirely (the summary line already conveys that). Same for
warnings and suggestions. Always render the "Overall improvement ideas" section
at the end if you have any cross-cutting observations; omit it otherwise.
-->

## Errors

### `<rule-id>` <Short title>
**Where:** <line N · `## Section Name`>
**Issue:** <one or two sentences describing what's wrong, citing spec language where helpful>
**Fix:** <concrete change, with inline example if useful>

```
<optional: code snippet showing the fix>
```

### `<rule-id>` <Short title>
**Where:** <line N>
**Issue:** <…>
**Fix:** <…>

## Warnings

### `<rule-id>` <Short title>
**Where:** <line N>
**Issue:** <…>
**Fix:** <…>

## Suggestions

### `<rule-id>` <Short title>
**Where:** <line N or "(file-wide)">
**Issue:** <…>
**Fix:** <…>

## Overall improvement ideas

- <Cross-cutting observation that doesn't map to a single rule. Be specific — name sections, tokens, or examples from the file.>
- <Another idea.>
- <Three to five total. Quality over quantity.>

<!--
If the file is fully compliant and content-rich, replace the body of this
template with:

> No errors or warnings. The file conforms to design.md v0.1.0.
>
> A few small ideas if you want to push it further:
> - <idea 1>
> - <idea 2>

Or, if the file is clean and you have nothing meaningful to add:

> No errors, warnings, or suggestions. The file is in good shape.
-->
