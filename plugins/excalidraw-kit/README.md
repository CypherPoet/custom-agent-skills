# excalidraw-kit

Comprehensive [Excalidraw](https://excalidraw.com) mastery: authoring `.excalidraw` scene files by hand (the JSON format, element model, arrow/text binding, and a diagrams-that-argue design methodology), plus the [`@excalidraw/excalidraw`](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api) developer API (React component, `initialData`, the `convertToExcalidrawElements` skeleton API, `restore`, SVG/PNG/clipboard export, and Mermaid-to-Excalidraw), shipped with scripts to validate a scene, render it to PNG, and insert icon-library elements — grounded in the official Excalidraw documentation.

## Installation

Install via the marketplace this plugin is published to:

```shell
# Skip if you've already added this marketplace
/plugin marketplace add CypherPoet/cypherpoet-toolchest

# Install this plugin
/plugin install excalidraw-kit@cypherpoet-toolchest
```

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [excalidraw-mastery](skills/excalidraw-mastery/SKILL.md) | Working knowledge of Excalidraw — the `.excalidraw` scene format and element model, a design methodology for diagrams that argue, the `@excalidraw/excalidraw` developer API, and Mermaid conversion, with bundled scripts for validating, rendering, and icon-library insertion. | Yes |

## Bundled Scripts

The skill ships runnable helpers under [`skills/excalidraw-mastery/scripts/`](skills/excalidraw-mastery/scripts/):

- **`validate_excalidraw.py`** — structural validation of a `.excalidraw` scene (pure standard library, no dependencies).
- **`render_excalidraw.py`** — render a scene to PNG for the design-and-verify loop (Playwright + headless Chromium).
- **`add_icon_to_diagram.py`**, **`add_arrow.py`**, **`split_excalidraw_library.py`** — insert icons from an Excalidraw library, add connectors, and split a `.excalidrawlib` into per-icon files.
