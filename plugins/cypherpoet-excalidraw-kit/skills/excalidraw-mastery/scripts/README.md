# Scripts

Runnable helpers for the `excalidraw-mastery` skill. Run them from this `scripts/`
directory. Two tiers by dependency:

| Script | Dependencies | Purpose |
|---|---|---|
| `validate_excalidraw.py` | none (stdlib) | Structural validation of a scene |
| `add_arrow.py` | none (stdlib) | Append a straight connector |
| `split_excalidraw_library.py` | none (stdlib) | Split a `.excalidrawlib` into per-icon files |
| `add_icon_to_diagram.py` | none (stdlib) | Drop a library icon into a scene |
| `render_excalidraw.py` | Playwright + Chromium | Render a scene to PNG |

## `validate_excalidraw.py`

Catches what silently breaks a hand-authored scene: bad JSON, wrong wrapper,
duplicate ids, and dangling references (an arrow bound to a missing element, a
`containerId` that points nowhere). No dependencies.

```bash
python validate_excalidraw.py scene.excalidraw
python validate_excalidraw.py scene.excalidraw --strict   # warnings fail too
python validate_excalidraw.py scene.excalidraw --json     # machine-readable
```

Exit code is `0` when every file passes (`1` on any error, or on any warning under `--strict`).

## `render_excalidraw.py`

Rasterizes a scene through Excalidraw's own `exportToSvg` for the design-and-verify
loop. Requires Playwright and headless Chromium (the only external dependency in
this skill). The render template loads `@excalidraw/excalidraw` from a CDN, so
rendering needs network access; **validation does not.**

```bash
# One-time setup
uv sync
uv run playwright install chromium

# Render (writes scene.png next to the file)
uv run python render_excalidraw.py scene.excalidraw --scale 2
```

If Playwright or Chromium is missing, the script exits with a clear message and
points you at the fallback: open the `.excalidraw` file in
[the web app](https://excalidraw.com) or the VS Code Excalidraw extension.

## Icon libraries — `split_excalidraw_library.py`, `add_icon_to_diagram.py`

For cloud/architecture diagrams built from icon sets (AWS, GCP, Azure, ...).

1. Download a set from [libraries.excalidraw.com](https://libraries.excalidraw.com/)
   into `libraries/<set>/<set>.excalidrawlib`.
2. Split it: `python split_excalidraw_library.py libraries/<set>/` — writes
   `icons/<Name>.json` files and a `reference.md` lookup table.
3. Insert an icon (ids are regenerated so nothing collides):

```bash
python add_icon_to_diagram.py scene.excalidraw EC2 500 300 --label "Web Server" \
    --library-path libraries/aws-architecture-icons
```

The scene is written atomically (temp file + `os.replace`), so an interrupted
write leaves the original intact rather than corrupting it.

**Licensing:** downloaded icon sets carry their own terms (AWS Content License,
Google's marks, etc.). Confirm the license before redistributing split icon files.

## `add_arrow.py`

Appends a straight connector between two points, optionally labeled/styled.

```bash
python add_arrow.py scene.excalidraw 300 200 500 300 --label "HTTP" --style dashed
```

This arrow is positional (not bound to shapes). For connectors that stay attached
when shapes move, author a bound arrow (`startBinding`/`endBinding` → element ids)
per [`../references/elements.md`](../references/elements.md).
