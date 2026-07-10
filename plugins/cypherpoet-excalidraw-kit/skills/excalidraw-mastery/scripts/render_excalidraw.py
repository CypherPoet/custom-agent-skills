"""Render an Excalidraw scene to PNG with Playwright + headless Chromium.

This powers the design-and-verify loop: you cannot judge a diagram from JSON
alone, so render it, Read the PNG, and fix what you see. The scene is rasterized
through Excalidraw's own `exportToSvg`, so the output matches the real editor.

Usage:
    cd <skill>/scripts
    uv run python render_excalidraw.py <file.excalidraw> [--output out.png] [--scale 2]

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

# The PNG is an element screenshot of the exported SVG, which captures the SVG's
# full bounds regardless of page viewport size — so this only needs to be a sane
# default; it never clips the diagram. Output size is set by the scene + --scale.
VIEWPORT = {"width": 1280, "height": 800}


def _structural_check(data: dict) -> list[str]:
    """Fast pre-flight so a broken scene fails before we launch a browser.

    Uses the full validator (sibling module) when importable; only the *import*
    is guarded, so a real bug inside validate() surfaces instead of being hidden.
    """
    try:
        from validate_excalidraw import Report, validate  # type: ignore
    except ImportError:
        errors: list[str] = []
        if data.get("type") != "excalidraw":
            errors.append(f"Expected type 'excalidraw', got {data.get('type')!r}")
        elements = data.get("elements")
        if not isinstance(elements, list):
            errors.append("'elements' must be an array")
        elif not any(isinstance(e, dict) and not e.get("isDeleted") for e in elements):
            errors.append("'elements' has nothing to render")
        return errors

    report = Report("<scene>")
    validate(data, report)
    return report.errors


def render(excalidraw_path: Path, output_path: Path | None, scale: int) -> Path:
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

        try:
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=scale)
            page.goto(template_path.as_uri())
            try:
                page.wait_for_function("window.__moduleReady === true", timeout=30000)
            except Exception:
                _fail(
                    "Timed out loading the Excalidraw module (network/CDN issue?).",
                    "The render fetches @excalidraw/excalidraw from esm.sh — check connectivity.",
                )

            # renderDiagram is async; evaluate awaits it, so on return the SVG is
            # in the DOM and `result` reports success/failure.
            result = page.evaluate(f"window.renderDiagram({json.dumps(data)})")
            if not result or not result.get("success"):
                msg = result.get("error", "unknown") if result else "renderDiagram returned null"
                _fail(f"Render failed: {msg}", None)

            svg_el = page.query_selector("#root svg")
            if svg_el is None:
                _fail("No SVG element produced after render.", None)
            svg_el.screenshot(path=str(output_path))
        finally:
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
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(render(args.input, args.output, args.scale))


if __name__ == "__main__":
    main()
