# Developer API: `@excalidraw/excalidraw`

Embedding the Excalidraw editor in an app, driving it programmatically, authoring
elements ergonomically, exporting, and converting Mermaid. For hand-authoring a
static `.excalidraw` file you don't need any of this — see
[`file-format.md`](file-format.md). Current package: **v0.18.1**.

## Table of Contents

| Section | Covers |
|---|---|
| [Install](#install) | `react` and `react-dom` are peer dependencies |
| [The Component & Props](#the-component--props) | All props are optional. The most useful |
| [initialData](#initialdata) | The scene the component loads with — an object (or a promise resolving to one) |
| [The Imperative API (`excalidrawAPI`)](#the-imperative-api-excalidrawapi) | Capture the API object to drive the editor after mount |
| [`convertToExcalidrawElements` (Skeleton API)](#converttoexcalidrawelements-skeleton-api) | Creating complete Excalidraw elements from concise JavaScript skeletons |
| [`restore` / `restoreElements`](#restore--restoreelements) | Normalizers that fill missing fields with defaults, repair bindings, and normalize z-index — the same pass the editor runs on load |
| [Export Utilities](#export-utilities) | All take the scene and return an image/string |
| [Constants](#constants) | Excalidraw font-family, theme, and MIME-type constants |
| [Mermaid → Excalidraw](#mermaid--excalidraw) | Convert Mermaid text into editable Excalidraw elements with the companion package `@excalidraw/mermaid-to-excalidraw` |

## Install

```bash
npm install react react-dom @excalidraw/excalidraw
```

`react` and `react-dom` are peer dependencies. Import the component and its stylesheet:

```jsx
import { Excalidraw } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
```

The editor is **client-only** (it touches `window`). In SSR frameworks (Next.js) load it dynamically:

```jsx
import dynamic from "next/dynamic";
const Excalidraw = dynamic(
  () => import("@excalidraw/excalidraw").then((m) => m.Excalidraw),
  { ssr: false },
);
```

## The Component & Props

All props are optional. The most useful:

| Prop | Type | Purpose |
|---|---|---|
| `initialData` | `object \| null \| Promise` | Scene to mount with (see below). |
| `excalidrawAPI` | `(api) => void` | Receives the imperative API once mounted. |
| `onChange` | `(elements, appState, files) => void` | Fires on every change. |
| `viewModeEnabled` | `boolean` | Read-only view mode. |
| `zenModeEnabled` | `boolean` | Hide most UI chrome. |
| `gridModeEnabled` | `boolean` | Show the grid. |
| `theme` | `"light" \| "dark"` | Editor theme (default `"light"`). |
| `name` | `string` | Drawing name (used in exports). |
| `langCode` | `string` | UI language (default `"en"`). |
| `UIOptions` | `object` | Customize/hide canvas actions and UI. |
| `onPointerUpdate`, `onPaste`, `onLibraryChange`, `renderTopRightUI` | `function` | Event/render hooks. |

Elements can also carry a `customData: Record<string, any>` object for app-specific metadata,
set via `initialData` or `updateScene`.

## initialData

The scene the component loads with — an object (or a promise resolving to one):

```jsx
<Excalidraw
  initialData={{
    elements,                                  // ExcalidrawElement[]
    appState: { viewBackgroundColor: "#a5d8ff", zenModeEnabled: true },
    scrollToContent: true,                     // center on content at mount
    libraryItems,                              // optional LibraryItems | Promise
    files,                                     // optional BinaryFiles (images)
  }}
/>
```

If `scrollToContent` is omitted/false, set `appState.scrollX`/`scrollY` yourself to position the view.

## The Imperative API (`excalidrawAPI`)

Capture the API object to drive the editor after mount:

```jsx
const [api, setApi] = useState(null);
<Excalidraw excalidrawAPI={setApi} />;

// later:
api.updateScene({ elements, appState });     // replace/patch the scene
api.updateLibrary({ libraryItems });         // update the library
const els = api.getSceneElements();          // current (non-deleted) elements
api.scrollToContent(els, { fitToContent: true });
```

`updateScene` is the main lever for programmatic drawing: build elements, then push them in.

## `convertToExcalidrawElements` (Skeleton API)

The ergonomic way to author elements **in JavaScript** — you specify only what matters and it fills
every required field (`id`, `seed`, `versionNonce`, defaults). This is the JS analog of the
by-hand JSON in [`elements.md`](elements.md); prefer it when generating a scene from code.

```js
import { convertToExcalidrawElements } from "@excalidraw/excalidraw";

const elements = convertToExcalidrawElements([
  { type: "rectangle", id: "a", x: 100, y: 100 },
  { type: "ellipse", id: "b", x: 400, y: 100 },
]);
```

**Bind arrows** with `start`/`end`, referencing a shape by `id` or spawning one by `type`, and add a
label with `label: { text }`. The label mechanism also gives shapes contained text:

```js
convertToExcalidrawElements([
  { type: "rectangle", id: "a", x: 100, y: 100, label: { text: "Client" } },
  { type: "ellipse", id: "b", x: 400, y: 100, label: { text: "API" } },
  {
    type: "arrow",
    x: 255, y: 120,
    label: { text: "request", strokeColor: "#099268" },
    start: { id: "a" },          // bind to existing element by id...
    end: { type: "ellipse" },    // ...or spawn a new one by type
  },
]);
```

Pass the result to `initialData.elements` or `api.updateScene({ elements })`.

## `restore` / `restoreElements`

Normalizers that fill missing fields with defaults, repair bindings, and normalize z-index — the
same pass the editor runs on load. Use them to sanitize partial or older element data before
mounting or exporting.

```js
import { restore, restoreElements } from "@excalidraw/excalidraw";

const elements = restoreElements(partialElements, /* localElements */ null);
const data = restore({ elements, appState, files }, null, null); // -> RestoredDataState
```

This is why hand-authored files can omit many fields ([`file-format.md`](file-format.md#what-restore-forgives)) —
`restore` supplies them. It does **not** invent geometry, color, or bindings you left wrong.

## Export Utilities

All take the scene and return an image/string. From `@excalidraw/excalidraw`:

| Function | Signature (abbreviated) | Returns |
|---|---|---|
| `exportToSvg` | `exportToSvg({ elements, appState, exportPadding, files })` | `Promise<SVGSVGElement>` |
| `exportToBlob` | `exportToBlob({ ...opts, mimeType?, quality?, exportPadding? })` | `Promise<Blob>` |
| `exportToClipboard` | `exportToClipboard({ ...opts, type: "png"\|"svg"\|"json", mimeType?, quality? })` | copies to clipboard |
| `serializeAsJSON` | `serializeAsJSON({ elements, appState })` | JSON `string` (a `.excalidraw` scene) |
| `loadFromBlob` | `loadFromBlob(blob, localAppState, localElements, fileHandle?)` | `Promise<RestoredDataState>` |
| `getSceneVersion` | `getSceneVersion(elements)` | version `number` |
| `mergeLibraryItems` | `mergeLibraryItems(localItems, otherItems)` | merged `LibraryItems` |

Defaults: `exportPadding` `10`, `mimeType` `"image/png"`, `quality` `0.92` (JPEG/WebP only). The
render script in [`../scripts/render_excalidraw.py`](../scripts/render_excalidraw.py) uses
`exportToSvg` under the hood, which is why its PNG matches the editor exactly.

## Constants

```js
import { FONT_FAMILY, THEME, MIME_TYPES } from "@excalidraw/excalidraw";
FONT_FAMILY.Excalifont; // hand-drawn (default) — 5; see elements.md for the full numeric map
THEME.LIGHT; THEME.DARK;
MIME_TYPES.json;        // and .excalidraw, .excalidrawlib, image types
```

## Mermaid → Excalidraw

Convert Mermaid text into editable Excalidraw elements with the companion package
`@excalidraw/mermaid-to-excalidraw`. Supported: flowchart, sequence, class, state, ER, and more.

```js
import { parseMermaidToExcalidraw } from "@excalidraw/mermaid-to-excalidraw";
import { convertToExcalidrawElements } from "@excalidraw/excalidraw";

const { elements: skeleton, files } = await parseMermaidToExcalidraw(
  `flowchart TD
     A[Start] --> B{Is it?}
     B -- Yes --> C[OK]
     B -- No  --> D[Not OK]`,
);
// parse returns element *skeletons* — finalize them, then load or push to the editor:
const elements = convertToExcalidrawElements(skeleton);
api.updateScene({ elements, files });
```

`parseMermaidToExcalidraw(mermaidString, config?)` returns `Promise<{ elements, files }>`; `config`
tweaks Mermaid rendering (`flowchart.curve`, `themeVariables.fontSize`, `maxEdges`, …). This is the
fastest route from a textual spec to an *editable* Excalidraw diagram (versus static SVG).

---
*Grounded in the official [`@excalidraw/excalidraw` API docs](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api) (v0.18.1) and the separately-versioned [`@excalidraw/mermaid-to-excalidraw`](https://github.com/excalidraw/mermaid-to-excalidraw) docs.*
