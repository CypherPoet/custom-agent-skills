# Symbol Animations

Distilled from the SF Symbols HIG (Animations section,
<https://developer.apple.com/design/human-interface-guidelines/sf-symbols>).
Use this when recommending a symbol *plus how it should move* — e.g. status
indicators, feedback on actions, ongoing-activity affordances. Developer API:
the Symbols framework / `SymbolEffect` (SwiftUI `.symbolEffect(...)`).

Animations work on every symbol (system and custom), in all rendering modes,
weights, and scales. Playback is controllable: once, repeating until a
condition, speed, autoreverse.

## The Presets and What They Communicate

| Preset | Motion | Communicates |
|---|---|---|
| **Appear / Disappear** | Layers gradually emerge into / recede from view | Element entering or leaving the UI |
| **Bounce** | Brief elastic scale up-or-down, returns to rest (plays once) | "An action occurred" or "act here" |
| **Scale** | Size change that *persists* until removed | Selection emphasis, focus feedback |
| **Pulse** | Opacity varies over time (annotated layers only, or all) | Ongoing activity |
| **Variable color** | Layer opacities step through thresholds; cumulative or iterative; can autoreverse or hide inactive layers | Progress, signal strength, playback, connecting |
| **Replace** | One symbol swaps for another (down-up / up-up / off-up configurations) | State change (mic → mic.slash) |
| **Magic Replace** | Smart transition between *related* shapes — slashes draw on/off, badges swap independently of the base | Default replace for same-family symbols; falls back to down-up for unrelated ones |
| **Wiggle** | Back-and-forth along an axis (lateral/rotational) | A change or call-to-action that might be missed; directional reinforcement |
| **Breathe** | Opacity *and* size swell rhythmically | Living/ongoing activity (recording) — richer than pulse |
| **Rotate** | Whole symbol or annotated layers spin (e.g. fan blades via By Layer) | Work in progress; real-world object behavior |
| **Draw On / Draw Off** (SF 7+) | Strokes draw along guide points, all-at-once / staggered / per layer | Progress (downloads), reinforcing directional meaning |

Open vs closed loop: layer arrangements that form a complete ring (circular
progress) are annotated *closed loop* and play variable-color animations
seamlessly; linear arrangements are *open loop*.

## Variable Draw (SF Symbols 8 Beta)

Variable Draw uses a numeric value with Draw annotations to represent changing
progress at finer resolution than layer-by-layer Variable Color. It is distinct
from the Draw On / Draw Off presets: those animate a symbol into or out of the
interface, while Variable Draw communicates the current value of an ongoing
quantity.

For a custom symbol, add guide points in the SF Symbols app to define the path
direction. The app carries guide-point placement across weights, while still
letting you refine Ultralight, Regular, and Black. Draw attachments, optional
bidirectionality, and adaptive end caps provide additional control.

## HIG Guidance

- Apply animations **judiciously** — too many overwhelm and distract.
- Every animation should serve a clear communicative purpose; consider how a
  combination might be misread.
- Use animation to convey information efficiently (feedback without UI bulk).
- Match animation choice to the app's tone and brand.

## Custom Symbols and Animation

Annotate layers in the SF Symbols app to control by-layer animation; Z-order
drives variable-color order (front-to-back or back-to-front), and layer
groups move together. **Test custom symbols against every preset** — paths
can behave unexpectedly in motion; drawing whole shapes with erase layers
(see [custom-symbol-design.md](custom-symbol-design.md)) is what makes
animation behave.
