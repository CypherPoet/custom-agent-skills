---
name: apple-app-icons
description: >
  Use when creating or updating an Apple app icon — authoring a Liquid Glass
  Icon Composer `.icon`, wiring it into an Xcode target, or adding an
  `.appiconset` fallback for OS versions below 26. Also use when debugging icon
  problems: off-center artwork, a thin white/bright edge border, alpha-channel
  rejections on the 1024 marketing icon, wrong sizes, or an icon that renders on
  iOS 26 but not on older versions (or vice versa). Triggers on "app icon",
  "Icon Composer", ".icon file", "Liquid Glass icon", "appiconset", "AppIcon",
  "actool", or icon work on iOS / iPadOS / macOS / watchOS.
---

# Apple App Icons (Icon Composer + appiconset)

## Overview

Modern Apple app icons come in two formats that coexist:

- **`.icon`** — an Icon Composer bundle (iOS/iPadOS/macOS/watchOS **26+**). One source, rendered by the system into every size, the per-platform shape (squircle, circle), and the **Default / Dark / Clear** appearance variants. This is the Liquid Glass icon.
- **`.appiconset`** — the classic asset-catalog icon set (one PNG per idiom/size/scale). The fallback for **OS versions below 26**, which can't read `.icon`.

You usually ship **both**, named the same (`AppIcon`), and let the build system pick per OS version. Drop the appiconset only if your deployment target is 26+.

## When to Use

- Creating or refreshing an app icon from source artwork
- Wiring an Icon Composer `.icon` into an Xcode project
- Adding a flat fallback for pre-26 OS versions
- Debugging: off-center art, white edge border, alpha/size rejections, icon missing on some OS versions

## Quick Reference

| Concern | Answer |
|---|---|
| New Liquid Glass icon | `Foo.icon` authored in Icon Composer; lives in the project, **not** inside `.xcassets` |
| Older-OS fallback | `AppIcon.appiconset` in `.xcassets`, same `AppIcon` name |
| Ship both | `ASSETCATALOG_COMPILER_INCLUDE_ALL_APPICON_ASSETS = YES` |
| Tell Xcode which icon | `ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon` (resolves to the `.icon` by base name) |
| iOS 1024 marketing PNG | **no alpha channel** (App Store rejects alpha); full-bleed, system masks corners |
| Verify | `xcodebuild … build`, then inspect the compiled `Assets.car` |
| Generate cleaned assets | `${CLAUDE_PLUGIN_ROOT}/skills/apple-app-icons/scripts/generate-app-icons.py` |

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

- **`position.scale` / `translation-in-points` are the layer transform**, not the pixels. Icon Composer stores centering/sizing as numbers in `icon.json` — the embedded PNG keeps its original framing. So a PNG that looks off-center on disk can still render centered, and vice versa. When generating outside the GUI, prefer **baking the final framing into the PNG** and leaving `translation-in-points: [0, 0]` — what you see in the file is then what ships.
- `scale` maps the source onto the ~1024 pt tile (a 2048 px source at `0.52` ≈ fills it with slight bleed); the exact value is artwork-dependent — fit it in Icon Composer's canvas or with the script's `--scale`.
- `fill` is the backdrop shown through transparent areas; irrelevant for a full-bleed opaque layer.

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

`scripts/generate-app-icons.py` (Pillow) cleans one source and emits both formats from it — so the `.icon` layer and every appiconset size stay identical:

```shell
python3 "${CLAUDE_PLUGIN_ROOT}/skills/apple-app-icons/scripts/generate-app-icons.py" \
  source.png --clean --recenter \
  --icon path/to/AppIcon.icon \
  --appiconset path/to/AppIcon.appiconset
```

`--clean` trims a uniform edge frame, `--recenter` centers the dominant content, both formats are written flattened to RGB (no alpha). Run `--help` for options.

## Common Mistakes

- **White/bright border** on every rendered size → an edge frame baked into the source art. Trim it (`--clean`).
- **Looks centered in Finder but ships off-center** (or the reverse) → centering lived in `icon.json`'s `translation-in-points`, not in the pixels. Bake the framing into the PNG and zero the translation.
- **App Store upload rejected** → the 1024 PNG has an alpha channel. Flatten to RGB.
- **Icon shows on iOS 26 but is blank on iOS 18** → you shipped only the `.icon`. Add an `.appiconset` and `INCLUDE_ALL_APPICON_ASSETS = YES`.
- **Square icon on the Mac Dock** → full-bleed flat PNG with no system shaping; fine for the `.icon` (the system shapes it on 26+), but pre-26 appiconset Mac icons render as authored.
- **Raising the deployment target just to use the `.icon`** → unnecessary, and it drops users. Ship both instead.
