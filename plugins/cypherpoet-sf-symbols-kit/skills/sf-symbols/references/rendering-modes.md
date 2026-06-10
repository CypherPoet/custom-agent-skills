# Rendering Modes, Gradients, and Variable Color

Distilled from the SF Symbols HIG
(<https://developer.apple.com/design/human-interface-guidelines/sf-symbols>,
Rendering modes / Gradients / Variable color sections). Use this when helping
someone choose how a symbol takes color, or when annotating a custom symbol.

## Layers Are the Foundation

A symbol's paths are organized into distinct layers, and every color behavior
is defined per layer. Example: `cloud.sun.rain.fill` has three — primary
(cloud), secondary (sun), tertiary (raindrops). Custom symbols get layer
assignments through *annotation* in the SF Symbols app (gallery view → color
sidebar); the CLI's `info <name>` shows which extra rendering modes a system
symbol ships (`extra_rendering_modes`, from `layerset_availability.plist`).

## The Four Rendering Modes

| Mode | Behavior | Reach for it when |
|---|---|---|
| **Monochrome** | One color across all layers; nested paths punch transparent holes | Default; toolbar/list icons that read like text |
| **Hierarchical** | One color, but opacity steps down per layer level (primary → tertiary) | Adding depth/emphasis with a single accent color |
| **Palette** | Two or more explicit colors, one per layer (two colors over three layers → secondary and tertiary share) | Coordinating symbols with multi-color schemes |
| **Multicolor** | Intrinsic real-world colors baked into the symbol (`leaf` is green; `trash.slash` is red for data loss) | Meaning is reinforced by the object's actual color |

System-provided colors keep symbols adapting to Dark Mode, vibrancy, and
accessibility settings automatically — prefer them over raw constants.
"Automatic" picks a symbol's preferred mode, but verify legibility per
context: size and background contrast change which mode reads best.

## Gradients (SF Symbols 7+)

Gradient rendering generates a smooth linear gradient from a single source
color. Works in all rendering modes, with system or custom colors, and on
custom symbols. Renders at any size but looks best large.

## Variable Color

Represents a changing quantity — capacity, signal, progress — by coloring
layers as a value crosses thresholds between 0–100% (e.g. `speaker.wave.3`
lights one wave per loudness range; the speaker layer opts out since it never
changes). Any number of layers can participate. Works in every rendering mode.

The HIG's sharp line: **variable color communicates change; hierarchy
communicates depth.** Don't use variable color to fake visual hierarchy.

In templates, variable-color thresholds appear as
`-sfsymbols-variable-threshold` style attributes (template v4.0+, iOS 16+).

## What This Means for the CLI

- SVGs exported by `svg`/`build-all` are the **monochrome** representation
  (single path, `fill="currentColor"`) — by design, for web/THREE.js use.
- Templates emitted by `custom`/`template` are monochrome v3.0; multicolor,
  hierarchical, palette, and variable-color annotations are applied
  afterwards in the SF Symbols app GUI, which writes them back into the
  template on export.
