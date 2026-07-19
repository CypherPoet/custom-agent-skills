---
name: excalidraw-mastery
description: >
  Use whenever the user is creating or editing Excalidraw diagrams or using the
  Excalidraw library — authoring .excalidraw scene JSON, designing
  flowchart/architecture/mind-map diagrams that read well, or embedding
  @excalidraw/excalidraw in React (initialData, exports, Mermaid-to-Excalidraw).
  Trigger on "make a diagram/flowchart", pasted Excalidraw JSON, or
  .excalidraw/.excalidrawlib files — even when "Excalidraw" is never named but
  an editable hand-drawn diagram is meant. For non-Excalidraw vector work use
  svg-tools.
---

# Excalidraw Mastery

**Verified:** 2026-07-17

*Grounded in the official [Excalidraw documentation](https://docs.excalidraw.com/) and the `@excalidraw/excalidraw` v0.18.1 source (scene format `version` 2). Design methodology adapted from the community Excalidraw skills by [coleam00](https://github.com/coleam00/excalidraw-diagram-skill) and [awesome-copilot](https://github.com/github/awesome-copilot).*

Working knowledge of [Excalidraw](https://excalidraw.com) — the virtual whiteboard for hand-drawn-style diagrams. Use this to author correct `.excalidraw` files, design diagrams that actually communicate, drive the `@excalidraw/excalidraw` API from code, and convert Mermaid — grounded in the docs and the source, not training-data guesses.

## Mental Model (read this first — it prevents most mistakes)

- **A `.excalidraw` file is just JSON.** A wrapper (`type`/`version`/`elements`/`appState`/`files`) around a flat array of elements. You can author it directly — no editor required. See [`references/file-format.md`](references/file-format.md).
- **A diagram should ARGUE, not display.** The *shape* should carry the meaning: if you removed every label, the structure alone should still communicate. Default to free-floating text; add a box only when it earns its place. See [`references/design-principles.md`](references/design-principles.md).
- **Binding is two-sided.** An arrow attaches to a shape via the arrow's `startBinding`/`endBinding` **and** the shape's `boundElements`. Contained text needs the text's `containerId` **and** the shape's `boundElements`. One-sided links render wrong.
- **You cannot judge a diagram from JSON.** Author, **validate**, then **render to PNG and Read the image**, and fix what you see — in a loop. This is core to the workflow, not a final check.
- **Exact values matter.** `fontFamily` is a numeric id (`5` = Excalifont, the default; `8` = Comic Shanns/code), `strokeWidth` is `1`/`2`/`4` (not `3`), `roundness: { type: 3 }` rounds rectangles. The two most-cited community skills disagree on these — trust [`references/elements.md`](references/elements.md), which quotes the source constants.

## Identify the Task First

The concepts are shared, but the entry point differs — pick one:

- **Author / edit a `.excalidraw` file** (the common case) → [`file-format.md`](references/file-format.md) + [`elements.md`](references/elements.md) + [`design-principles.md`](references/design-principles.md), then the workflow below.
- **Design well** (which shape, which pattern, which color) → [`design-principles.md`](references/design-principles.md).
- **Integrate `@excalidraw/excalidraw` in an app** (React component, programmatic scene, export, skeleton API, Mermaid) → [`developer-api.md`](references/developer-api.md).
- **Add pre-built icons** (AWS/GCP/Azure architecture) → [`libraries-and-icons.md`](references/libraries-and-icons.md).

## Reference Files

Load only the rows the task touches — usually one or two.

| Asking about… | Read |
|---|---|
| The `.excalidraw` file wrapper, `appState`, `files`, coordinates, what `restore` fills | [`references/file-format.md`](references/file-format.md) |
| Element types, shared properties, the exact constants, arrow/text binding, full JSON examples | [`references/elements.md`](references/elements.md) |
| Designing a diagram that argues: patterns, evidence artifacts, container discipline, color, layout | [`references/design-principles.md`](references/design-principles.md) |
| The step-by-step process, section-by-section for big diagrams, validate + render loop, checklist | [`references/authoring-workflow.md`](references/authoring-workflow.md) |
| Embedding the component, `initialData`, `convertToExcalidrawElements`, `restore`, export, Mermaid | [`references/developer-api.md`](references/developer-api.md) |
| `.excalidrawlib` format, splitting a library, inserting cloud/architecture icons | [`references/libraries-and-icons.md`](references/libraries-and-icons.md) |
| A complete, validated scene to crib from | [`examples/flowchart-basics.excalidraw`](examples/flowchart-basics.excalidraw), [`examples/system-architecture.excalidraw`](examples/system-architecture.excalidraw) |
| Runnable helpers (validate, render, split library, add icon/arrow) | [`scripts/README.md`](scripts/README.md) |

## Core Workflows

### Author a diagram
1. **Assess depth** (simple vs. technical) and, for technical, **research the real specs** first.
2. **Map concepts to visual patterns** and sketch the eye's flow — [`design-principles.md`](references/design-principles.md).
3. **Write the elements** with descriptive ids and two-sided bindings — [`elements.md`](references/elements.md). Build large diagrams **section by section**.
4. **Validate**: `python scripts/validate_excalidraw.py scene.excalidraw` — fix every ERROR.
5. **Render & fix**: `uv run --project scripts python scripts/render_excalidraw.py scene.excalidraw`, **Read the PNG**, fix defects, repeat (2–4 passes). (`--project scripts` points `uv` at the render env in `scripts/`.) Full loop in [`authoring-workflow.md`](references/authoring-workflow.md).

### Generate a scene from code
Use `convertToExcalidrawElements([...])` — specify only `type`/`x`/`y` (+ `label`, `start`/`end` to bind arrows) and it fills the rest; pass the result to `initialData` or `api.updateScene`. See [`developer-api.md`](references/developer-api.md).

### Convert Mermaid → Excalidraw
`parseMermaidToExcalidraw(mermaidText)` → `{ elements, files }` (skeletons) → `convertToExcalidrawElements` → `updateScene`. The fastest route from a textual spec to an *editable* diagram. See [`developer-api.md`](references/developer-api.md#mermaid--excalidraw).

### Embed the editor
Install `@excalidraw/excalidraw` + React, import the component and `index.css`, load it client-only (dynamic import in SSR frameworks), and capture `excalidrawAPI` to drive it. See [`developer-api.md`](references/developer-api.md).

### Add library icons
Download a `.excalidrawlib`, split it (`scripts/split_excalidraw_library.py`), then `scripts/add_icon_to_diagram.py scene.excalidraw <Icon> <x> <y>` — ids are regenerated to avoid collisions. See [`libraries-and-icons.md`](references/libraries-and-icons.md).

## Accuracy Notes

- **The render script pins `@excalidraw/excalidraw@0.18.0`** in its CDN import: esm.sh's `?bundle` currently 404s on a transitive import for the *unpinned* tag **and** for the latest `0.18.1`, while `0.18.0` bundles cleanly. The current npm release is `0.18.1` (the documented API is unchanged). To move the pin, bump it in [`scripts/render_template.html`](scripts/render_template.html) and re-test the render.
- **Rendering needs a browser + network** (Playwright/Chromium + the CDN); **validation does not**. With no render environment, open the file in [excalidraw.com](https://excalidraw.com) or the VS Code Excalidraw extension — but still inspect it before shipping.
- **`restore()` fills missing element fields with defaults** but cannot invent intent — keep geometry, color, text, and bindings correct yourself, and validate for unique ids and live references.
- Excalidraw evolves; the newest arrowhead types and font families may post-date this corpus. If exact current behavior matters, verify against the installed package version.

## Primary Sources

- [Excalidraw developer documentation](https://docs.excalidraw.com/) — official component API, integration, customization, and utility reference.
- [Excalidraw releases](https://github.com/excalidraw/excalidraw/releases) — official release notes and breaking changes.
- [`@excalidraw/excalidraw` on npm](https://www.npmjs.com/package/@excalidraw/excalidraw) — authoritative published package versions and installation metadata.
