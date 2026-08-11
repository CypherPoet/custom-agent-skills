# The `.excalidraw` Scene File Format

The wrapper around every scene. A `.excalidraw` file is plain JSON (MIME
`application/json`); the editor, the web app, and `exportToSvg` all read this
exact shape. For the elements *inside* `elements`, see [`elements.md`](elements.md).

## Top-Level Shape

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": { "viewBackgroundColor": "#ffffff", "gridSize": 20 },
  "files": {}
}
```

That is a complete, valid, empty scene. Every field above is expected by the loader:

| Field | Value | Notes |
|---|---|---|
| `type` | `"excalidraw"` | Always. A different value (e.g. `"excalidrawlib"`) is a *library*, not a scene. |
| `version` | `2` | The current scene-format version. Not the app version, not the element `version`. |
| `source` | `"https://excalidraw.com"` | Provenance marker, not a URL to fetch. Any string is accepted. |
| `elements` | `ExcalidrawElement[]` | The drawing. `[]` is valid (empty canvas). |
| `appState` | `object` | Canvas-level state. Only a small subset is persisted (below). |
| `files` | `object` | Map of embedded binary assets (images) keyed by `fileId`. `{}` when none. |

## Coordinate System

- Origin `(0, 0)` is the **top-left**. `x` grows right, `y` grows **down**. Units are pixels.
- An element's `x`/`y` is its **top-left corner** (not its center — a common mistake).
- There is **no bounds checking**: elements can sit at negative coordinates or far off-canvas.
  Export and the editor's "zoom to fit" work from the elements' bounding box, so absolute
  position rarely matters — only relative layout does.
- `angle` (on each element) is rotation in **radians**, clockwise, about the element center.

## `appState`

Scene-level, not element-level. Excalidraw persists only a subset into the file; the rest
is editor UI state and is ignored on load. The ones worth setting by hand:

| Key | Purpose |
|---|---|
| `viewBackgroundColor` | Canvas background (hex, e.g. `"#ffffff"`). |
| `gridSize` | Grid spacing in px (commonly `20`). Presence does not force snapping. |
| `scrollX` / `scrollY` | Initial pan. Usually omit and let the viewer fit-to-content. |
| `zoom` | `{ "value": 1 }`-shaped zoom. Usually omit. |

Anything else you add to `appState` is harmless but typically dropped. Do **not** rely on
`appState` to style elements — styling lives on each element (see [`elements.md`](elements.md)).

## `files` (Embedded Images)

When a scene contains `image` elements, their bytes live in `files`, keyed by a `fileId`
that the `image` element references:

```json
"files": {
  "abc123": {
    "mimeType": "image/png",
    "id": "abc123",
    "dataURL": "data:image/png;base64,iVBORw0KGgo...",
    "created": 1700000000000
  }
}
```

The `image` element carries `"fileId": "abc123"`, plus its own `x`/`y`/`width`/`height`.
For hand-authored diagrams you rarely need this — reach for it only when embedding raster images.

## What `restore()` Forgives

Excalidraw's loader runs the scene through `restore()` / `restoreElements()`
([`developer-api.md`](developer-api.md)), which **fills missing element fields with defaults**,
repairs bindings, and normalizes fractional z-index (`index`) values. Practically:

- You can omit many per-element fields and the file still opens — `restore` supplies
  `versionNonce`, `updated`, `roundness`, `frameId`, `boundElements`, and similar.
- You should still keep the fields that carry *meaning* (geometry, color, text, bindings)
  correct, because `restore` cannot invent your intent — only defaults.
- Duplicate or dangling references are **not** reliably repaired. Unique `id`s and valid
  bindings are your responsibility — run [`../scripts/validate_excalidraw.py`](../scripts/validate_excalidraw.py).

## Related Format: `.excalidrawlib`

A **library** file has `"type": "excalidrawlib"` and a `libraryItems` array instead of
`elements` — a different top-level shape. It holds reusable stamps (icons, groups), not a
scene. See [`libraries-and-icons.md`](libraries-and-icons.md).

---
*Grounded in the official [Excalidraw docs](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api) and `@excalidraw/excalidraw` source (scene `version` 2).*
