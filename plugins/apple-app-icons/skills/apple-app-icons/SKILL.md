---
name: apple-app-icons
description: >
  Creating, designing, auditing, or A/B-testing an Apple app icon — both making
  it convert on the App Store (design principles, audit rubric, Product Page
  Optimization tests) and shipping it correctly (Liquid Glass Icon Composer
  .icon files, Xcode wiring, .appiconset fallback for OS versions below 26).
  Also for debugging icon problems: off-center artwork, edge borders,
  alpha-channel rejections, wrong sizes, or icons that read poorly at small
  sizes. Triggers on "app icon", "Icon Composer", ".icon", "appiconset",
  "actool".
---

# Apple App Icons (Icon Composer + appiconset)

**Verified:** 2026-07-24

## Overview

An app icon has two jobs: **earn the tap** in the App Store (a design / conversion problem) and **ship correctly** across every OS version and appearance (an engineering problem). This skill covers both — settle the design first, then build and wire the assets.

Modern Apple app icons come in two formats that coexist:

- **`.icon`** — an Icon Composer bundle (iOS/iPadOS/macOS/watchOS **26+**). One source, rendered by the system into every size, the per-platform shape (squircle, circle), and the **Default / Dark / Clear** appearance variants. This is the Liquid Glass icon.
- **`.appiconset`** — the classic asset-catalog icon set (one PNG per idiom/size/scale). The fallback for **OS versions below 26**, which can't read `.icon`.

You usually ship **both**, named the same (`AppIcon`), and let the build system pick per OS version. Drop the appiconset only if your deployment target is 26+.

## When to Use

- Designing or auditing an icon so it stands out and converts in the App Store
- Creating or refreshing an app icon from source artwork
- Wiring an Icon Composer `.icon` into an Xcode project
- Adding a flat fallback for pre-26 OS versions
- Planning an icon A/B test, or briefing a designer
- Debugging: off-center art, white edge border, alpha/size rejections, icon missing on some OS versions

## Design so it earns the tap

A technically perfect icon that nobody taps is still a failure. The icon is the **first thing** a user sees in search and browse — before the title, rating, or screenshots — so a stronger one can lift tap-through meaningfully with no other change. Pressure-test the design *before* you generate assets:

- **It reads at 60×60 pt.** That's the size in iPhone search results; fine detail disappears there. Aim for one recognizable mark, ~2 elements max, and no text. If you can't name it in three words ("bold orange flame"), keep simplifying until you can.
- **It survives light *and* dark.** The App Store shows your icon on a light background and a dark one, and so does the Home Screen. A near-white or near-black full-bleed fill dissolves into one of them. This is exactly why the `.icon`'s **Dark** appearance variant is worth authoring deliberately rather than letting it default — design for both contexts.
- **It differs from its category.** Pull up your top ~20 competitors' icons and design to be the one that stands out, not the one that blends in.

Settle the design first, then build the assets from that one mark — author the `.icon` in Icon Composer, and run the [generation script](#generation-script) below for the appiconset fallback.

For the full audit rubric, an iOS A/B-test workflow (App Store Connect → Product Page Optimization), and a designer brief template, see [`references/icon-design-and-aso.md`](references/icon-design-and-aso.md).

## Quick Reference

| Concern | Answer |
|---|---|
| New Liquid Glass icon | `Foo.icon` authored in Icon Composer; lives in the project, **not** inside `.xcassets` |
| Older-OS fallback | `AppIcon.appiconset` in `.xcassets`, same `AppIcon` name |
| Ship both | `ASSETCATALOG_COMPILER_INCLUDE_ALL_APPICON_ASSETS = YES` |
| Tell Xcode which icon | `ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon` (resolves to the `.icon` by base name) |
| iOS 1024 marketing PNG | **no alpha channel** (App Store rejects alpha); full-bleed, system masks corners |
| App Store listing icon | derived from the build's asset-catalog **default** appearance — there's no separate App Store upload; a *dark* listing icon means making dark the build default (which also flips the Home Screen) |
| Verify | `xcodebuild … build`, then inspect the compiled `Assets.car` |
| Generate the appiconset fallback | `scripts/generate-app-icons.py` (cleans the source, writes the macOS ladder; author the `.icon` in Icon Composer) |

## The `.icon` bundle

A `.icon` is a folder, not a single file:

```
AppIcon.icon/
  icon.json          # manifest: groups → layers, fill, supported-platforms
  Assets/
    app-icon.png     # the layer artwork (referenced by name from icon.json)
```

A minimal single-layer `icon.json`:

```json
{
  "fill": { "automatic-gradient": "extended-srgb:0.0,0.53,1.0,1.0" },
  "groups": [
    {
      "name": "App Icon",
      "layers": [
        {
          "image-name": "app-icon.png",
          "name": "app-icon",
          "position": { "scale": 0.52, "translation-in-points": [0, 0] }
        }
      ]
    }
  ],
  "supported-platforms": { "circles": ["watchOS"], "squares": "shared" }
}
```

Key points:

- **`position.scale` / `translation-in-points` are the layer transform**, not the pixels. Icon Composer stores centering/sizing as numbers in `icon.json` — the embedded PNG keeps its original framing. So a PNG that looks off-center on disk can still render centered, and vice versa. Prefer **baking the final framing into the PNG you import** and leaving `translation-in-points: [0, 0]` — what you see in the file is then what ships.
- `scale` maps the source onto the ~1024 pt tile (a 2048 px source at `0.52` ≈ fills it with slight bleed); the exact value is artwork-dependent — fit it in Icon Composer's canvas.
- `fill` is the backdrop shown through transparent areas; irrelevant for a full-bleed opaque layer.

## Layering & appearances (Dark, Tinted, Clear)

The reason to ship a `.icon` over a flat PNG is that the system re-renders your **layers** per appearance — Default, Dark, Tinted (monochrome), and Clear. Per-appearance values live in `icon.json` as a `<property>-specializations` array on a layer: the **first entry is the default (no `appearance` key)** and each later entry overrides one appearance. The simplest two-edition icon is two flat composites swapped by opacity:

```json
"layers": [
  { "image-name": "icon-light.png", "name": "icon-light",
    "opacity-specializations": [
      { "value": 1 },
      { "appearance": "dark",   "value": 0 },
      { "appearance": "tinted", "value": 0 }
    ] },
  { "image-name": "icon-dark.png", "name": "icon-dark",
    "opacity-specializations": [
      { "value": 0 },
      { "appearance": "dark",   "value": 1 },
      { "appearance": "tinted", "value": 1 }
    ] }
]
```

Icon Composer writes this `opacity-specializations` shape for you. But note this flat-composite swap *is* the washout problem: the `tinted` entries just hand the system one flat composite to tint — there's no separate foreground for it to render. The next point is the fix.

**Give the emblem its own transparent layer.** Tinted and Clear are generated by the system from your layers' shapes and alpha, *at runtime* — so verify them on device, not just in the editor. A single flat, full-bleed layer gives the system nothing to separate, so it washes out in Tinted/Clear (the whole tile just gets tinted). Real depth there needs the foreground (logo/emblem) as its own layer on transparency over a separate background layer.

**Anti-pattern: don't carve the foreground out of a finished flat composite.** It's tempting to take the shipped flat PNG and luminance-key the emblem back out to make the layered version. It's too lossy to ship: the extracted emblem has soft, semi-transparent edges that Liquid Glass bevels into a melted look; inpainting the hole leaves a ghost of the emblem in the background; and compensating with `fill` shifts the light-mode look. Get **clean source art from the original design file** — the emblem on full transparency, plus the background as its own full-bleed layer — not reconstructed from the bake.

## Source-art requirements

- **Full-bleed, opaque, square.** The system applies the rounded mask — don't pre-round. macOS also renders the proper shape from a full-bleed source (no manual rounded-rect-with-margin needed for `.icon`).
- **No edge frame.** A thin bright/white border baked into the source (a common export artifact) shows as a visible rim once the icon is masked. Trim it.
- **Center the dominant element** against the icon grid. The geometric center of the main shape should sit at the tile center.
- **No alpha on the iOS 1024 marketing PNG** — App Store validation rejects an alpha channel there. Flatten to RGB.

## Wiring into Xcode

- Add `AppIcon.icon` to the project (a normal file; with a synced file-system group it's auto-included).
- Keep the appiconset at `Assets.xcassets/AppIcon.appiconset` for the fallback, named `AppIcon`.
- Build settings:
  - `ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon`
  - `ASSETCATALOG_COMPILER_INCLUDE_ALL_APPICON_ASSETS = YES` (bundles both so the system picks per OS)
- Going 26-only? Delete the appiconset and drop `INCLUDE_ALL_APPICON_ASSETS`; `APPICON_NAME = AppIcon` then resolves to the `.icon` alone.

## Verify (don't trust the editor preview)

```shell
xcodebuild -scheme <Scheme> -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO build
```

In the log, `actool` should run over **both** the `.icon` and `.xcassets` with `--app-icon AppIcon --include-all-app-icons`. Inspect the compiled catalog:

```shell
xcrun --sdk iphonesimulator assetutil --info <App>.app/Assets.car | grep -i AppIcon
```

Expect Liquid Glass layer renditions plus `AppIcon … UIAppearanceAny` / `…Dark`, and the fallback springboard PNGs emplaced in the `.app`.

## Generation script

`scripts/generate-app-icons.py` (Pillow; paths relative to this skill's directory) cleans one source and emits the **`.appiconset`** fallback. Author the Liquid Glass `.icon` itself in **Icon Composer** — its material and Default / Dark / Clear appearance variants can't be produced by a script.

```shell
python3 scripts/generate-app-icons.py \
  source.png --clean --recenter \
  --appiconset path/to/AppIcon.appiconset
```

`--clean` trims a uniform edge frame, `--recenter` centers the dominant content, every PNG is flattened to RGB (no alpha). Run `--help` for options.

**You rarely need to generate the iOS sizes.** Xcode 14+ has a **"Single Size"** app-icon slot — drop one 1024 and the build generates every iOS and watchOS size for you. macOS has no equivalent, so the size ladder the script writes earns its keep on **macOS**; the iOS entry it emits is just that single 1024.

## Common Mistakes

- **White/bright border** on every rendered size → an edge frame baked into the source art. Trim it (`--clean`).
- **Looks centered in Finder but ships off-center** (or the reverse) → centering lived in `icon.json`'s `translation-in-points`, not in the pixels. Bake the framing into the PNG and zero the translation.
- **App Store upload rejected** → the 1024 PNG has an alpha channel. Flatten to RGB.
- **Icon shows on iOS 26 but is blank on iOS 18** → you shipped only the `.icon`. Add an `.appiconset` and `INCLUDE_ALL_APPICON_ASSETS = YES`.
- **Square icon on the Mac Dock** → full-bleed flat PNG with no system shaping; fine for the `.icon` (the system shapes it on 26+), but pre-26 appiconset Mac icons render as authored.
- **Raising the deployment target just to use the `.icon`** → unnecessary, and it drops users. Ship both instead.
- **Flat icon looks dead in Tinted/Clear** → a single full-bleed layer has nothing for the system to separate. Split the emblem onto its own transparent layer over a background layer; verify on device (those appearances render at runtime).
- **Wanted a dark icon on the App Store listing** → the listing icon is the build's *default* appearance — there's no separate upload, and making it dark also makes dark the Home Screen default. Pick which look is your default and design both appearances to that.

## Primary Sources

- [HIG: App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons) — authoritative for sizes, appearances (dark/tinted/clear), and per-platform shape rules.
- [Creating your app icon using Icon Composer](https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer) — authoritative for the `.icon` format and Icon Composer workflow.
