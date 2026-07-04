"""Render an Excalidraw scene to PNG with Playwright + headless Chromium.

This powers the design-and-verify loop: you cannot judge a diagram from JSON
alone, so render it, Read the PNG, and fix what you see. The scene is rasterized
through Excalidraw's own `exportToSvg`, so the output matches the real editor.

Usage:
    cd <skill>/scripts
    uv run python render_excalidraw.py <file.excalidraw> [--output out.png] [--scale 2] [--width 1920]

First-time setup (one dependency, one browser download):
    cd <skill>/scripts
    uv sync
    uv run playwright install chromium

If Playwright or Chromium is unavailable, this script exits with a clear message
and a fallback: open the `.excalidraw` file in the Excalidraw web app
(https://excalidraw.com) or the VS Code Excalidraw extension to inspect it.
Structural validation (validate_excalidraw.py) has no such dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _structural_check(data: dict) -> list[str]:
    """Fast pre-flight so a broken scene fails before we launch a browser.

    Prefers the full validator (sibling module); falls back to a minimal check.
    """
    try:
        from validate_excalidraw import Report, validate  # type: ignore

        report = Report("<scene>")
        validate(data, report)
        return report.errors
    except Exception:
        errors: list[str] = []
        if data.get("type") != "excalidraw":
            errors.append(f"Expected type 'excalidraw', got {data.get('type')!r}")
        elements = data.get("elements")
        if not isinstance(elements, list):
            errors.append("'elements' must be an array")
        elif not any(not e.get("isDeleted") for e in elements if isinstance(e, dict)):
            errors.append("'elements' has nothing to render")
        return errors


def compute_bounding_box(elements: list[dict]) -> tuple[float, float, float, float]:
    """Bounding box (min_x, min_y, max_x, max_y) across live elements."""
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for el in elements:
        if el.get("isDeleted"):
            continue
        x, y = el.get("x", 0), el.get("y", 0)
        w, h = el.get("width", 0), el.get("height", 0)
        if el.get("type") in ("arrow", "line") and isinstance(el.get("points"), list):
            for pt in el["points"]:
                px, py = pt[0], pt[1]
                min_x, min_y = min(min_x, x + px), min(min_y, y + py)
                max_x, max_y = max(max_x, x + px), max(max_y, y + py)
        else:
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x + abs(w)), max(max_y, y + abs(h))
    if min_x == float("inf"):
        return (0, 0, 800, 600)
    return (min_x, min_y, max_x, max_y)


def render(excalidraw_path: Path, output_path: Path | None, scale: int, max_width: int) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _fail(
            "Playwright is not installed.",
            "Run: cd <skill>/scripts && uv sync && uv run playwright install chromium",
        )

    data = json.loads(excalidraw_path.read_text(encoding="utf-8"))
    errors = _structural_check(data)
    if errors:
        print("ERROR: scene failed structural validation:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("Fix these (see validate_excalidraw.py) before rendering.", file=sys.stderr)
        sys.exit(1)

    elements = [e for e in data["elements"] if not e.get("isDeleted")]
    min_x, min_y, max_x, max_y = compute_bounding_box(elements)
    padding = 80
    vp_width = min(int(max_x - min_x + padding * 2), max_width)
    vp_height = max(int(max_y - min_y + padding * 2), 600)

    output_path = output_path or excalidraw_path.with_suffix(".png")
    template_path = Path(__file__).parent / "render_template.html"
    if not template_path.exists():
        _fail(f"Render template not found at {template_path}", None)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:
            if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc):
                _fail(
                    "Chromium is not installed for Playwright.",
                    "Run: cd <skill>/scripts && uv run playwright install chromium",
                )
            raise

        page = browser.new_page(
            viewport={"width": vp_width, "height": vp_height},
            device_scale_factor=scale,
        )
        page.goto(template_path.as_uri())
        page.wait_for_function("window.__moduleReady === true", timeout=30000)

        result = page.evaluate(f"window.renderDiagram({json.dumps(data)})")
        if not result or not result.get("success"):
            msg = result.get("error", "unknown") if result else "renderDiagram returned null"
            browser.close()
            _fail(f"Render failed: {msg}", None)

        page.wait_for_function("window.__renderComplete === true", timeout=15000)
        svg_el = page.query_selector("#root svg")
        if svg_el is None:
            browser.close()
            _fail("No SVG element produced after render.", None)
        svg_el.screenshot(path=str(output_path))
        browser.close()

    return output_path


def _fail(message: str, hint: str | None) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(hint, file=sys.stderr)
    print(
        "Fallback: open the .excalidraw file in https://excalidraw.com or the "
        "VS Code Excalidraw extension to inspect it visually.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an .excalidraw scene to PNG.")
    parser.add_argument("input", type=Path, help="Path to the .excalidraw file")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output PNG path")
    parser.add_argument("--scale", "-s", type=int, default=2, help="Device scale factor (default 2)")
    parser.add_argument("--width", "-w", type=int, default=1920, help="Max viewport width (default 1920)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(render(args.input, args.output, args.scale, args.width))


if __name__ == "__main__":
    main()
