# The Element Model

Every entry in a scene's `elements` array. For the file wrapper see
[`file-format.md`](file-format.md); for style *meaning* (which color, when a box)
see [`design-principles.md`](design-principles.md).

**Contents:** [Shared Properties](#shared-properties) · [Verified Constants](#verified-constants) · [Shapes](#shapes-rectangle-ellipse-diamond) · [Text](#text) · [Arrows](#arrows) · [Lines](#lines) · [Binding Arrows to Shapes](#binding-arrows-to-shapes) · [Frames & Images](#frames--images) · [Gotchas](#gotchas)

## Shared Properties

Every element carries these. The ones in **bold** must be correct for the element to mean
what you intend; the rest have sensible defaults `restore()` will fill if omitted
([`file-format.md`](file-format.md#what-restore-forgives)).

| Property | Type | Notes |
|---|---|---|
| **`id`** | string | Unique across the whole scene. Duplicates cause undefined behavior. |
| **`type`** | string | `rectangle` \| `ellipse` \| `diamond` \| `arrow` \| `line` \| `text` \| `frame` \| `image`. |
| **`x`, `y`** | number | Top-left corner, in px (not the center). |
| **`width`, `height`** | number | Bounding-box size in px. |
| `angle` | number | Rotation in **radians** (clockwise), default `0`. |
| **`strokeColor`** | string | Border/line/text color (hex). |
| **`backgroundColor`** | string | Fill (hex or `"transparent"`). |
| `fillStyle` | string | `solid` \| `hachure` \| `cross-hatch` \| `zigzag`. |
| `strokeWidth` | number | `1` \| `2` \| `4` \| `8` — see constants. |
| `strokeStyle` | string | `solid` \| `dashed` \| `dotted`. |
| `roughness` | number | `0` \| `1` \| `2` — hand-drawn amount. |
| `opacity` | number | `0`–`100`. Prefer `100`; use color/size for hierarchy. |
| `roundness` | object \| null | `{ "type": 3 }` rounds corners; `null` = sharp. |
| `seed` | number | Randomness seed for the rough look. Keep unique-ish per element. |
| `version` | number | Per-element edit counter (`1` for freshly authored). |
| `versionNonce` | number | Random int bumped on edit; used for sync. |
| `isDeleted` | boolean | `false` for live elements; `true` tombstones them. |
| `groupIds` | string[] | Group membership (shared id across grouped elements); `[]` if none. |
| `frameId` | string \| null | Owning frame's id, or `null`. |
| `boundElements` | array \| null | Back-references to bound text/arrows: `[{ "type": "text", "id": "…" }]`. |
| `link` | string \| null | Optional hyperlink. |
| `locked` | boolean | Whether the element is locked in the editor. |

## Verified Constants

These are the exact values from `@excalidraw/excalidraw` (`packages/common/src/constants.ts`).
Getting them wrong is the most common source of "it looks off" — the two most-cited community
skills even disagree on the font ids, so trust these:

**`fontFamily`** (integer, on `text` elements):

| Id | Font | Role |
|---|---|---|
| `5` | Excalifont | **Default** hand-drawn font |
| `6` | Nunito | Normal (clean sans) |
| `8` | Comic Shanns | Code (monospace) |
| `1` | Virgil | Legacy hand-drawn |
| `2` | Helvetica | Legacy normal |
| `3` | Cascadia | Legacy code (monospace) |
| `7` / `9` / `10` | Lilita One / Liberation Sans / Assistant | Additional families |

There is **no `fontFamily: 4`.** For a modern hand-drawn look use `5`; for a monospace/code
look use `8` (or legacy `3`). Both `3` and `5` render fine; pick one and be consistent.

**`roundness.type`**: `1` legacy · `2` proportional radius (used for arrow/line curvature) ·
`3` adaptive radius (used to round rectangle corners). Sharp corners: `roundness: null`.

**`strokeWidth`**: `1` thin · `2` medium · `4` bold · `8` extra-bold. **`3` is not a valid
value** (a common mistake) — the editor only offers thin/medium/bold.

**`roughness`**: `0` architect (crisp) · `1` artist (default, hand-drawn) · `2` cartoonist (very rough).

**`fillStyle`**: `solid` · `hachure` (sketchy lines) · `cross-hatch` · `zigzag`. `DEFAULT_FONT_SIZE` is `20`.

## Shapes: `rectangle`, `ellipse`, `diamond`

The three container shapes. Identical schema — only `type` differs. Add `roundness: { "type": 3 }`
to round a rectangle's corners (ellipses/diamonds ignore it). A shape holds a centered label by
*binding* a `text` element to it (see [Text](#text)), not by a `text` field on the shape.

```json
{
  "type": "rectangle",
  "id": "process",
  "x": 280, "y": 120, "width": 170, "height": 70,
  "angle": 0,
  "strokeColor": "#1971c2",
  "backgroundColor": "#a5d8ff",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "groupIds": [],
  "frameId": null,
  "roundness": { "type": 3 },
  "seed": 105,
  "version": 1,
  "versionNonce": 1005,
  "isDeleted": false,
  "boundElements": [{ "type": "text", "id": "process_t" }],
  "link": null,
  "locked": false
}
```

Pair a **darker stroke with a lighter fill** for contrast. Excalidraw's default palette pairs
(fill / stroke): blue `#a5d8ff` / `#1971c2`, green `#b2f2bb` / `#2f9e44`, yellow `#ffec99` /
`#f08c00`, red `#ffc9c9` / `#e03131`, orange `#ffd8a8` / `#e8590c`, grape `#eebefa` / `#9c36b5`.

## Text

Two modes. **Free-floating** text (a label/title) has `containerId: null`. **Contained** text
(a centered label inside a shape) sets `containerId` to the shape's id **and** the shape lists it
in `boundElements`. Both directions are required — a one-sided link renders wrong.

```json
{
  "type": "text",
  "id": "process_t",
  "x": 300, "y": 143, "width": 130, "height": 25,
  "angle": 0,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
  "roughness": 0, "opacity": 100,
  "groupIds": [], "frameId": null, "roundness": null,
  "seed": 106, "version": 1, "versionNonce": 1006, "isDeleted": false,
  "boundElements": null, "link": null, "locked": false,
  "text": "Validate order",
  "originalText": "Validate order",
  "fontSize": 20,
  "fontFamily": 5,
  "textAlign": "center",
  "verticalAlign": "middle",
  "containerId": "process",
  "lineHeight": 1.25
}
```

Text-specific fields:

| Field | Notes |
|---|---|
| `text` | The rendered string. **Readable words only** — no markdown/formatting codes. Use `\n` for line breaks. |
| `originalText` | Same as `text` (pre-wrap source). Keep them equal. |
| `fontSize` | px. 16–20 for labels; larger for titles. |
| `fontFamily` | Integer id (see constants). `5` default. |
| `textAlign` | `left` \| `center` \| `right`. Use `center` for contained labels. |
| `verticalAlign` | `top` \| `middle` \| `bottom`. Use `middle` for contained labels. |
| `containerId` | Parent shape id, or `null` for free-floating. |
| `lineHeight` | Multiplier, `1.25` typical. |

For contained text, the editor recomputes exact position from the container, so approximate
`x`/`y`/`width` centered on the shape is fine — the [render loop](authoring-workflow.md) confirms it.

## Arrows

A connector. Its shape is a `points` array **relative to** the element's `x`/`y`: the first point
is always `[0, 0]`, and each later point is an offset. A straight arrow has two points; add more
for elbows/curves. Bind the ends to shapes so the arrow follows them when they move.

```json
{
  "type": "arrow",
  "id": "a2",
  "x": 452, "y": 155, "width": 106, "height": 0,
  "angle": 0,
  "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
  "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
  "roughness": 0, "opacity": 100,
  "groupIds": [], "frameId": null, "roundness": { "type": 2 },
  "seed": 107, "version": 1, "versionNonce": 1007, "isDeleted": false,
  "boundElements": null, "link": null, "locked": false,
  "points": [[0, 0], [106, 0]],
  "startBinding": { "elementId": "process", "focus": 0, "gap": 4 },
  "endBinding": { "elementId": "decision", "focus": 0, "gap": 4 },
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

- `startArrowhead` / `endArrowhead`: `null` \| `"arrow"` \| `"triangle"` \| `"bar"` \| `"dot"`
  (newer builds add `diamond`, `circle`, `crowfoot_*`, and `_outline` variants). A plain arrow is
  `startArrowhead: null`, `endArrowhead: "arrow"`.
- Curved arrow: use 3+ points, e.g. `[[0,0],[60,-20],[120,0]]`, and keep `roundness: { "type": 2 }`.

## Lines

Same as an arrow but non-directional (no arrowheads by default) — use for dividers, timelines,
tree trunks, and flow spines. `type: "line"`, a `points` array, and typically no bindings. A
closed polygon sets the first and last points equal.

## Binding Arrows to Shapes

Binding is what makes a connector *stick* to a shape. It has two halves that must agree:

1. On the **arrow**: `startBinding` / `endBinding`, each `{ "elementId", "focus", "gap" }`.
   - `elementId` — the shape's id (must exist).
   - `focus` — where on the shape edge the arrow attaches, from `-1` to `1` (`0` = center). Signed
     offset along the edge.
   - `gap` — px of clearance between the arrow tip and the shape edge (2–8 typical).
2. On the **shape**: an entry in its `boundElements` array, `{ "type": "arrow", "id": "<arrowId>" }`.

Omitting the shape-side `boundElements` entry still *draws* the arrow, but the shape won't know it's
attached, so moving the shape leaves the arrow behind. Author both sides. A shape can list many
bound elements — its text label and every arrow touching it.

## Frames & Images

- **`frame`** — a named rectangular container that owns elements (they set `frameId` to it). Use to
  group a region; rarely needed for static diagrams. Has a `name`.
- **`image`** — references bytes in the scene's `files` map via `fileId`, plus its own
  `x`/`y`/`width`/`height`. See [`file-format.md`](file-format.md#files-embedded-images).

## Gotchas

- **Unique ids.** Duplicate `id`s silently corrupt bindings. Use readable ids
  (`decision`, `arrow_to_db`) and namespace by section for big diagrams.
- **`points` are relative**, first point `[0,0]` — not absolute canvas coordinates.
- **Binding is two-sided.** Arrow `startBinding`/`endBinding` *and* the shape's `boundElements`.
- **Contained text is two-sided.** Text `containerId` *and* the shape's `boundElements`.
- **`strokeWidth: 3` is invalid** (use `1`/`2`/`4`); `fontFamily: 4` doesn't exist.
- **`y` grows downward**, and `x`/`y` is the top-left corner, not the center.
- Validate references before shipping: [`../scripts/validate_excalidraw.py`](../scripts/validate_excalidraw.py).

---
*Constants verified against `@excalidraw/excalidraw` `packages/common/src/constants.ts`.*
