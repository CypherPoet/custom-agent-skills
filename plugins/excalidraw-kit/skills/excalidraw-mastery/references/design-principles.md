# Design Principles: Diagrams That Argue

How to make a diagram *say something*, not just label boxes. This is the judgment
layer on top of the mechanical [`elements.md`](elements.md); the step-by-step
process that applies it is [`authoring-workflow.md`](authoring-workflow.md).

## Table of Contents

| Section | Covers |
|---|---|
| [Core Philosophy](#core-philosophy) | Structural argument, label-independent meaning, and concrete educational value |
| [Depth Assessment](#depth-assessment) | Conceptual versus comprehensive depth, explanation scope, and research for real formats, events, APIs, and endpoints |
| [Evidence Artifacts](#evidence-artifacts) | Code, JSON, event timelines, UI mockups, and real inputs rendered as concrete proof rather than labels |
| [Visual Pattern Library](#visual-pattern-library) | Fan-out, convergence, trees, timelines, cycles, clouds, transformations, comparisons, phase breaks, and line-first structure |
| [Multi-Zoom Architecture](#multi-zoom-architecture) | Summary flow, responsibility or phase boundaries, and evidence-rich detail in one technical diagram |
| [Container Discipline](#container-discipline) | Focal, connectable, semantic, and distinct elements that merit shapes versus labels and metadata that rely on typography |
| [Shape Meaning](#shape-meaning) | Free text, markers, endpoints, decisions, processes, abstract states, and hierarchies mapped to distinct visual forms |
| [Layout](#layout) | Element scale, whitespace, flow direction, required connections, and spacing rules for readable diagrams |
| [Color & Aesthetics](#color--aesthetics) | Semantic fill and stroke pairs, text hierarchy, palette reuse, roughness, valid stroke widths, opacity, and marker sizing |

## Core Philosophy

**A diagram should ARGUE, not DISPLAY.** It is a visual argument about relationships,
causality, and flow — not formatted text. The *shape* should carry the meaning.

Two tests before you ship:

- **Isomorphism test** — if you deleted every label, would the structure alone still
  communicate the idea? If not, the layout isn't doing its job; redesign.
- **Education test** — could someone learn something concrete from it, or does it just name
  parts? Good technical diagrams show real formats, real event names, real examples.

## Depth Assessment

Decide this *first* — it changes everything downstream:

- **Simple / conceptual** — a mental model or philosophy. Abstract shapes, generic labels
  (`Input → Process → Output`), ~30 seconds to explain. Fine when the concept *is* the abstraction.
- **Comprehensive / technical** — a real system, protocol, or architecture meant to teach.
  Concrete names and formats, evidence artifacts, ~2–3 minutes of content.

**For comprehensive diagrams, research first.** Look up the actual JSON shapes, event names,
API/method names, and endpoints. `AG-UI streams RUN_STARTED / STATE_DELTA` beats `Protocol → Frontend`.
Real terminology makes a diagram both accurate *and* educational.

## Evidence Artifacts

Concrete proof embedded in a technical diagram — they make it teach and show it's correct:

| Artifact | When | How to render |
|---|---|---|
| Code snippet | APIs, integration points | Dark rectangle (`#1e293b`) + light/syntax-colored text |
| JSON / data example | Data formats, payloads | Dark rectangle + green text (`#22c55e`) |
| Event / step sequence | Protocols, lifecycles | Timeline: a line + small dots + free-floating labels |
| UI mockup | Actual output | Nested rectangles mimicking the real UI |
| Real input | What goes into a system | A rectangle showing sample content, not the word "Input" |

The principle: **show what things actually look like**, not just what they're called.

## Visual Pattern Library

Match each concept to the pattern that mirrors its *behavior*. In a multi-concept diagram,
**give each major concept a different pattern** — no grid of identical boxes.

| If the concept… | Pattern | Built from |
|---|---|---|
| Spawns many outputs | **Fan-out** | one node + radial arrows |
| Merges inputs to one | **Convergence** | arrows funneling to a single node |
| Has hierarchy/nesting | **Tree** | `line` trunk/branches + free-floating text (no boxes) |
| Is a sequence of steps | **Timeline** | a `line` + small dots + labels beside each |
| Loops / iterates | **Spiral / Cycle** | nodes with an arrow returning to the start |
| Is an abstract state | **Cloud** | overlapping ellipses |
| Transforms in→out | **Assembly line** | `before → [process] → after` |
| Compares two things | **Side-by-side** | parallel structures with contrast |
| Separates phases | **Gap / Break** | whitespace or a dashed divider line |

Lines + free-floating text often read cleaner than boxes + contained text — reach for `line`
elements as primary structure (timelines, trees, spines), not just as connectors.

## Multi-Zoom Architecture

Comprehensive diagrams work at three zoom levels at once, like a map showing both country
borders and street names:

1. **Summary flow** — a one-line overview of the whole pipeline (top or bottom).
2. **Section boundaries** — labeled regions grouping related parts (by responsibility, phase, or actor).
3. **Detail** — evidence artifacts and concrete examples inside each section. This is where the teaching lives.

Aim to include all three in a technical diagram: the summary gives context, sections organize, details teach.

## Container Discipline

**Not every label needs a box.** Default to free-floating text; add a shape only when it earns its keep.
Aim for **under ~30%** of text elements sitting inside containers.

| Use a container when… | Use free-floating text when… |
|---|---|
| It's a section's focal point | It's a label or description |
| Arrows must connect to it | It's supporting detail / metadata |
| The shape itself means something (a decision diamond) | Typography alone gives enough hierarchy |
| It's a distinct "thing" in the system | It's a title, subtitle, or annotation |

Typography *is* hierarchy: a 28px colored title needs no rectangle around it.

## Shape Meaning

| Concept | Shape |
|---|---|
| Label, title, annotation, detail | **none** (free-floating text) |
| Timeline marker, connection node | small `ellipse` (10–20px dot) |
| Start, trigger, input; end, output | `ellipse` |
| Decision, condition | `diamond` |
| Process, action, step | `rectangle` |
| Abstract state, context | overlapping `ellipse`s |
| Hierarchy | `line`s + text, no boxes |

## Layout

- **Hierarchy through scale** — hero ~300×150 (most important, most whitespace), primary ~180×90,
  secondary ~120×60, marker ~10–20px.
- **Whitespace = importance** — the key element gets the most empty space around it (200px+).
- **Flow direction** — guide the eye: left→right or top→bottom for sequences, radial for hub-and-spoke.
- **Connections are required** — position alone doesn't show a relationship. If A relates to B, draw an arrow.
- **Spacing rules of thumb** — 200–300px horizontal between elements, 100–150px vertical between rows,
  50px min margin from content edge, 20–30px arrow-to-shape clearance.

## Color & Aesthetics

Color **encodes meaning**, it isn't decoration. A workable semantic palette (fill / stroke):

| Purpose | Fill | Stroke |
|---|---|---|
| Start / trigger | `#ffd8a8` | `#e8590c` |
| Process / neutral | `#a5d8ff` | `#1971c2` |
| Decision | `#ffec99` | `#f08c00` |
| Success / end | `#b2f2bb` | `#2f9e44` |
| Warning / reset | `#ffec99` | `#f08c00` |
| Error / stop | `#ffc9c9` | `#e03131` |
| AI / special | `#eebefa` | `#9c36b5` |

Always pair a **darker stroke with a lighter fill**. Text hierarchy via color: title `#1971c2`,
detail `#868e96`, on-fill body `#1e1e1e`. Don't invent new colors per element — reuse the palette.

Aesthetics:

- **`roughness`** — `0` for crisp, modern, technical diagrams; `1` for a hand-drawn/informal feel. Default `0` for professional work.
- **`strokeWidth`** — `1` thin (dividers, subtle links), `2` standard (shapes, primary arrows), `4` bold (sparingly, for emphasis). `3` is not valid.
- **`opacity`** — keep `100`; create hierarchy with color/size/weight, not transparency.
- **Small markers** — 10–20px dots instead of full shapes for timeline points, bullets, and anchors.

---
*Methodology adapted, with thanks, from the community Excalidraw diagram skills by
[coleam00](https://github.com/coleam00/excalidraw-diagram-skill) and
[awesome-copilot](https://github.com/github/awesome-copilot); mechanics grounded in the official Excalidraw docs.*
