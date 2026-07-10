# Authoring Workflow

The end-to-end loop for producing a `.excalidraw` file that's both correct and
well-composed. Pairs the judgment in [`design-principles.md`](design-principles.md)
with the mechanics in [`elements.md`](elements.md) and the bundled
[`scripts/`](../scripts/).

## The Process

1. **Assess depth** — simple/conceptual or comprehensive/technical? For technical, **research the
   real specs first** (actual event names, JSON shapes, API names) so the diagram teaches.
2. **Understand deeply** — for each concept ask what it *does* and how it relates to the others.
   What would someone need to *see* (not read) to get it?
3. **Map concepts to patterns** — assign each major concept a visual pattern (fan-out, timeline,
   convergence, …) that mirrors its behavior. In a multi-concept diagram, vary the patterns.
4. **Sketch the flow** — trace how the eye should move (left→right, top→bottom, radial) before any JSON.
5. **Generate the JSON** — author elements with descriptive ids and the correct bindings.
   Build large diagrams **section by section** (below).
6. **Validate, then render & fix** — run the validator, then the render loop until it looks right.

## Generate: Author the Elements

- Use **descriptive string ids** (`trigger_rect`, `arrow_to_db`) so bindings stay readable.
- Wire both sides of every relationship: arrow `startBinding`/`endBinding` **and** the shape's
  `boundElements`; contained text `containerId` **and** the shape's `boundElements`
  ([`elements.md`](elements.md#binding-arrows-to-shapes)).
- Pull colors from the semantic palette, not per-element whim
  ([`design-principles.md`](design-principles.md#color--aesthetics)).
- Keep `text` to readable words only; `fontFamily: 5`, `roughness: 0` for clean diagrams.

### Large / Comprehensive Diagrams: Build Section by Section

Don't emit a big diagram in one pass — you risk truncation and worse composition. Instead:

1. Create the base file (wrapper + first section's elements).
2. Add **one section per edit**, taking time on each section's internal layout and spacing.
3. **Namespace seeds by section** (section 1 = `100xxx`, section 2 = `200xxx`, …) to avoid collisions.
4. When a new section's arrow binds to an earlier element, update that earlier element's
   `boundElements` in the same edit.
5. After all sections are in, re-read the whole file: are cross-section arrows bound on both ends?
   Is spacing balanced? Do all ids/bindings resolve?

## Validate: Catch Reference Errors Before Rendering

```bash
python ../scripts/validate_excalidraw.py your-scene.excalidraw
```

It flags the silent killers — malformed JSON, duplicate ids, dangling arrow bindings, a
`containerId` pointing nowhere, and nonstandard style values. Fix every **ERROR** (warnings are
advisory). No dependencies, so this always runs. See [`../scripts/README.md`](../scripts/README.md).

## Render & Fix: You Cannot Judge a Diagram From JSON

This is not optional for anything non-trivial. Render to PNG, **Read the image**, and fix what you
see — in a loop, typically 2–4 passes.

```bash
# one-time: (cd ../scripts && uv sync && uv run playwright install chromium)
# --project points uv at the render env in scripts/ while keeping your cwd:
uv run --project ../scripts python ../scripts/render_excalidraw.py your-scene.excalidraw
```

It rasterizes through Excalidraw's own `exportToSvg`, so the PNG matches the editor. Then:

1. **Read the PNG** and compare it to the plan from steps 1–4.
   - Does the structure match the concept? Does the eye flow as intended? Is the hero dominant?
2. **Hunt visual defects** the JSON hides:
   - text clipped or overflowing its container
   - overlapping shapes/text; arrows crossing *through* elements
   - arrows landing in empty space or on the wrong shape
   - uneven spacing; a cramped section next to an empty one
   - text too small to read at export size
3. **Fix the JSON** — widen containers for clipped text, adjust `x`/`y` for spacing, add waypoints to
   an arrow's `points` to route around a shape, resize to rebalance weight.
4. **Re-render and repeat** until it passes both the vision check and the defect check.

No render environment? Fall back to opening the file in [excalidraw.com](https://excalidraw.com) or
the VS Code Excalidraw extension — but still inspect it visually before declaring it done.

## Quality Checklist

Before shipping a diagram:

- [ ] **Depth right** — simple stayed simple; technical did the research and shows real specs.
- [ ] **Argues** — structure alone carries meaning (isomorphism test); it teaches (education test).
- [ ] **Pattern variety** — each major concept uses a different visual pattern; no uniform grid.
- [ ] **Container discipline** — under ~30% of text is boxed; the rest is free-floating.
- [ ] **Every relationship has an arrow or line**; bindings are two-sided.
- [ ] **Color is semantic** — from the palette, darker stroke + lighter fill, `opacity: 100`.
- [ ] **Text is clean** — readable words only, legible size, `fontFamily` consistent.
- [ ] **Validator passes** — no duplicate ids, no dangling references.
- [ ] **Rendered and inspected** — no clipping/overlap; arrows land right; composition balanced.

See [`examples/flowchart-basics.excalidraw`](../examples/flowchart-basics.excalidraw) and
[`examples/system-architecture.excalidraw`](../examples/system-architecture.excalidraw) for
complete, validated scenes to crib from.
