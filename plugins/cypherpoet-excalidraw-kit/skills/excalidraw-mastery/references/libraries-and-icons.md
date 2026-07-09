# Libraries & Icons

Reusable stamps — cloud/service icons (AWS, GCP, Azure, Kubernetes), UI kits, shape
sets — that you drop into a scene instead of drawing by hand. Most useful for
architecture diagrams. Uses the bundled [`scripts/`](../scripts/).

## The `.excalidrawlib` Format

A **library** file, not a scene. Its top level is different from
[`.excalidraw`](file-format.md):

```json
{
  "type": "excalidrawlib",
  "version": 2,
  "source": "https://excalidraw.com",
  "libraryItems": [
    {
      "id": "abc",
      "status": "published",
      "name": "EC2",
      "elements": [ /* ExcalidrawElement[] making up this one stamp */ ]
    }
  ]
}
```

Each `libraryItems[]` entry is a named stamp whose `elements` are ordinary Excalidraw elements
(usually grouped via a shared `groupIds`). Browse and download sets at
[libraries.excalidraw.com](https://libraries.excalidraw.com/).

## Why Split a Library

A single `.excalidrawlib` can hold hundreds of icons and be megabytes of JSON — too much to load
into context. `split_excalidraw_library.py` explodes it into one file per icon plus a lightweight
`reference.md` lookup table, so you read the table to find an icon and load only that icon's JSON.

```bash
# 1. Download a set into libraries/<set>/<set>.excalidrawlib, then:
python ../scripts/split_excalidraw_library.py libraries/aws-architecture-icons/
# -> libraries/aws-architecture-icons/icons/EC2.json, S3.json, ...
# -> libraries/aws-architecture-icons/reference.md   (name -> filename table)
```

## Insert an Icon Into a Scene

`add_icon_to_diagram.py` loads an icon's elements, offsets them to a target position, and
**regenerates every `id` and `groupId`** (rewriting internal bindings, `containerId`s, and
`boundElements` to match) so the stamp can't collide with the scene it's dropped into.

```bash
python ../scripts/add_icon_to_diagram.py scene.excalidraw EC2 500 300 \
    --label "Web Server" --library-path libraries/aws-architecture-icons
```

- `<x> <y>` is the icon's top-left target position.
- `--label` adds a centered caption below the icon.
- Writes atomically (temp file + `os.replace`), so an interrupted write leaves the original
  scene intact rather than corrupting it.

Then connect icons with bound arrows ([`elements.md`](elements.md#binding-arrows-to-shapes)) or the
quick `add_arrow.py` helper, and **validate + render** as usual
([`authoring-workflow.md`](authoring-workflow.md)).

## When to Use Scripts vs. Hand Authoring

- **Hand-author** the diagram's *layout and structure* (boxes, flow, connectors that carry meaning).
  This is where design judgment lives — a script can't compose a diagram.
- **Use the scripts** for the *mechanical* parts: stamping many pre-built icons, generating collision-free
  ids, and appending simple connectors. This is exactly the token-heavy, error-prone work worth automating.

## Licensing

Downloaded icon sets carry their **own** licenses — the AWS Content License for AWS Architecture
Icons, Google's brand terms for GCP, etc. Splitting and using them locally is generally fine;
**redistributing** the split icon files must comply with the original set's terms. Do not commit
third-party icon libraries into a repo without checking. (That's why
[`.gitignore`](../.gitignore) excludes `scripts/libraries/`.)
