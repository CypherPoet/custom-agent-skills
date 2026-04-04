---
name: creating-effective-stitch-prompts
description: Use when writing, generating, or refining a text prompt for Stitch to generate or edit mobile or web application UIs
---

# Writing Effective Stitch Prompts

## Overview

Stitch generates UIs for mobile and web applications from text prompts. Writing effective prompts requires specificity, design system awareness, thematic adjectives, and disciplined iteration. This skill codifies patterns learned from extensive real-world Stitch usage.

## When to Use

- When writing a prompt to generate a new screen in Stitch
- When refining an existing Stitch screen design via `edit_screens`
- When a user asks for help crafting a prompt for a UI component or page
- When modifying an application theme (colors, typography, spacing) via Stitch

---

## Prompt Structure

Every Stitch generation prompt should follow this three-block structure:

```markdown
[Overall vibe, mood, and purpose of the page — 1-2 sentences
setting the tone and context]

**DESIGN SYSTEM (REQUIRED):**
- Platform: [Web/Mobile], [Desktop/Mobile]-first
- Dark/Light mode: [base color] (#hex)
- Accents: [Name] (#hex for role), [Name] (#hex for role)
- Fonts: [Display font] (headlines), [Body font] (body/labels)
- Shapes: [radius description], [geometry motifs]
- Glassmorphism: [recipe if applicable]
- Glows: [shadow descriptions]

**PAGE STRUCTURE:**
1. **[Section Name]:** [Detailed description]
2. **[Section Name]:** [Detailed description]
3. **[Section Name]:** [Detailed description]

**ATMOSPHERE:**
- [Visual mood and behavioral notes]
- [Scroll behavior, transitions, effects]
```

### Why the DESIGN SYSTEM Block Matters

Stitch generates its own design system if you don't provide one. By pasting your tokens explicitly, you maintain visual consistency across screens. If you have a `DESIGN.md` or equivalent, extract the relevant tokens into this block for every prompt.

---

## Core Principles

### 1. One Screen at a Time

**Do not attempt to build the entire app at once.** Focus on one screen or component per generation. Stitch projects share context — establishing core visual patterns on anchor screens first ensures consistency when you generate subsequent screens.

### 2. Specificity Over Vagueness

Tell Stitch "what" and "how." Clearly identify the element and the exact modification.

- **Vague:** "Make the button better."
- **Specific:** "Change the primary CTA button to use a frosted glass background (bg-black/50, backdrop-blur-md) with a sweeping gradient border (Neon Blue to Deep Purple, 6-8s rotation)."

### 3. Setting the "Vibe" with Adjectives

Use descriptive adjectives to set the overall mood. The adjectives directly influence the generated design system.

- **Colors:** "Deep ocean blue", "energetic neon cyan" — not just "blue"
- **Fonts:** "Condensed bold italic" — not just "bold"
- **Layout:** "Cinematic", "broadcast-quality", "glassmorphism", "editorial"
- **Atmosphere:** "SportsCenter meets fighting game VS screen", "premium sports card aesthetic"

### 4. Balancing High-Level and Detailed Prompts

High-level prompts work for initial ideas. Explicit detail provides accuracy.

- **High-level (weak):** "A dashboard for comparing players."
- **Detailed (strong):** "A cinematic head-to-head NFL player comparison screen for a dark-themed desktop web app (1280px wide). Two player images fill the viewport, split with a 15-degree diagonal seam. Center-out tug-of-war stat bars with glassmorphic center labels."

### 5. Fine-Tuning the Theme

You have granular control over the design system:

- **Colors:** Request specific named colors or mood-based palettes
- **Borders & Shapes:** "Sharp 4px radius on cards, 15-degree slanted geometry on dividers"
- **Shadows:** "Colored box-shadows on accent elements (red glow, blue glow, gold glow)"

### 6. Coordinating Images

- **Theme coordination:** When updating theme colors, specify if images should reflect those changes
- **Specific targeting:** Use descriptive terms to identify exactly which image to modify
  - *Example:* "For the left player image (Mahomes), shift the background-position to 20% center so his face is visible within the diagonal clip area."

---

## Editing Screens: The Defensive Pattern

Editing existing screens is where most problems occur. Follow these rules:

### Limit Changes Per Edit

**1-3 targeted changes per `edit_screens` call.** Never bundle more than 3.

Batching too many changes causes destructive regressions — Stitch may regenerate sections you intended to keep. In one real session, a 12-change edit caused the entire hero section (player images, names, VS badge) to disappear and be replaced with a minimal layout.

### Always Specify What NOT to Change

Every edit prompt should explicitly state which sections to preserve:

```
Make these changes to the STAT BARS ONLY. Do not change the hero
section, navigation, radar chart, or any other part of the page.
```

This is the single most important pattern for reliable edits.

### Name Changes Specifically

- **Bad:** "Improve the layout"
- **Good:** "In the Positional Stats section, remove the background container behind the radar chart. Let the chart float directly on the page background with no box around it."

---

## Three-Pass Cadence

Design work flows through three phases per screen:

### Pass 1: Concept → First Draft

Generate the initial screen from a full prompt. Review what works and what's off. Don't expect perfection.

### Pass 2: Iterative Refinement

Fix issues one at a time with targeted `edit_screens` calls. Capture design decisions as you go — when a choice is made (e.g., "stat bar values at center, not in caps"), record it immediately so it isn't re-debated on the next screen.

### Pass 3: Polish

After the structure is locked, sweep for:
- Glow/shadow refinement
- Spacing and padding consistency
- Typography sizing and hierarchy
- Component detail (do elements match their specs?)
- Color token accuracy
- Animation specifications (even if Stitch can't render them)

---

## Stitch Rendering Limitations

Stitch's screenshot renderer cannot accurately render several CSS features. These effects will work in a real browser but won't show correctly in Stitch previews:

| Feature | Workaround |
|---------|------------|
| `backdrop-filter: blur()` on section containers | Creates hard rectangular edges. Verify in browser. |
| `-webkit-text-fill-color: transparent` (outline text) | May render as filled. Edit HTML directly. |
| `position: fixed` (parallax scroll) | Static screenshot can't show scroll behavior. Test in browser. |
| Complex SVG `viewBox` (case-sensitive) | Stitch may output lowercase `viewbox`. Fix in HTML. |
| Multi-stop CSS gradients (3+ stops) | May simplify or ignore stops. Verify in browser. |
| CSS `clip-path` polygons | May clip incorrectly in screenshots. Verify in browser. |

**Fallback: Direct HTML editing.** When Stitch can't render a CSS effect correctly, download the HTML export and edit it directly. The HTML is the ground truth, not the screenshot.

---

## Stitch API Reliability

When using Stitch via MCP or direct API calls:

- **Post-edit cooldown:** Stitch frequently becomes unavailable for 30-90 seconds after processing an `edit_screens` call. Always wait before retrying — don't spam requests.
- **MCP timeouts:** The `edit_screens` MCP tool may timeout on complex edits. Fall back to direct `curl` POST with a longer timeout (300s).
- **Retry pattern:** Check availability with a lightweight `tools/list` call before retrying a failed edit.

---

## Examples

### Generating a New Screen

❌ **Bad:**
```
Make a dashboard.
```

✅ **Good:**
```
A cinematic head-to-head NFL player comparison screen for a
dark-themed desktop web application (1280px wide). This is the
app's showcase screen — dramatic, electric, broadcast-quality.

**DESIGN SYSTEM (REQUIRED):**
- Platform: Web, Desktop-first
- Dark mode: Deep Navy (#0A0E1A) base
- Accents: Electric Red (#E63946), Neon Blue (#2196F3),
  Madden Gold (#FFD700)
- Fonts: Barlow Condensed (headlines, bold/extrabold, italic),
  Raleway SemiBold (body/labels)
- Glassmorphism: bg-white/5, border-white/10, backdrop-blur

**PAGE STRUCTURE:**
1. **Top Navigation Bar (sticky):** Full-width frosted glass bar...
2. **VS Hero Section (full viewport height):** Two player images
   split with a 15-degree diagonal seam...
3. **Positional Stats Section (two-panel):** Radar chart left,
   stat bars right...
```

### Editing an Existing Screen

❌ **Bad:**
```
Fix the stat bars and radar chart and navigation and add glows
and change the heading colors.
```

✅ **Good:**
```
Make this ONE change to the RADAR CHART ONLY. Do not change
anything else on the page.

Remove the background container behind the radar chart — let it
float directly on the page background. Add a third concentric
hexagonal grid ring (3 inner rings total). Increase vertex label
size by 25%.
```

### Changing the Theme

❌ **Bad:**
```
Make it look cooler.
```

✅ **Good:**
```
Update the section heading underlines from a single solid color
to a GRADIENT of both teams' accent colors: Chiefs red (#E31837)
on the left blending to Bills blue (#00338D) on the right.
```

---

## Common Mistakes

| Mistake | Why It Fails | Fix |
|---------|-------------|-----|
| Bundling 5+ changes in one edit | Stitch may regenerate sections you wanted to keep | Limit to 1-3 changes per call |
| Not specifying what to preserve | Unmentioned sections may be altered or removed | Always add "do not change X" |
| Omitting the DESIGN SYSTEM block | Stitch invents its own tokens, breaking consistency | Paste tokens from your design system into every prompt |
| Using generic adjectives | "Nice", "modern", "clean" produce generic designs | Use specific mood descriptors: "cinematic", "broadcast-quality", "editorial" |
| Trusting the screenshot for CSS effects | Stitch can't render blur, fixed positioning, or outline text | Verify complex CSS in a real browser |
| Retrying immediately after a failure | Stitch needs recovery time after processing | Wait 30-90 seconds before retrying |
