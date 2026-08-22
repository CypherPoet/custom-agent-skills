# Foundations — Visual

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-10

Distilled from Apple's HIG Foundations pages: Branding, Color, Dark Mode, Icons, Images, Materials, SF Symbols, Typography.

## Table of Contents

| Section | Covers |
|---|---|
| [Branding](#branding) | Voice and tone, accent colors and custom fonts, unobtrusive identity, standard patterns, logo restraint, launch screens, and trademarks |
| [Color](#color) | System and custom variants, semantic consistency and noncolor cues, testing and profiles, Liquid Glass tinting, system palettes, and platform constraints |
| [Dark Mode](#dark-mode) | Light and dark support, semantic adaptive colors, contrast and transparency testing, image and icon treatment, depth cues, and platform availability |
| [Icons](#icons) | SF Symbols and custom vectors, simplicity and consistency, optical balance, localization and accessibility, standard action symbols, and macOS document icons |
| [Images](#images) | Scale factors, raster and vector formats, color profiles and device testing, tvOS layers, visionOS spatial images, and watchOS transparency and autoscaling |
| [Materials](#materials) | Liquid Glass versus content-layer materials, regular and clear variants, dimming and vibrancy, semantic thickness, and platform-specific material systems |
| [SF Symbols](#sf-symbols) | License boundaries, rendering modes, gradients and variable color, weights and variants, localization, animations, custom-symbol construction, and accessibility |
| [Typography](#typography) | System and custom fonts, Dynamic Type, sizes and weights, hierarchy and leading, font families and styles, tracking data, and platform-specific type systems |

## Branding

**Purpose:** Express a unique brand identity in ways that feel at home on the platform while always deferring to content.

**Best practices:**
- Use your brand's voice and tone in all written communication.
- Consider an accent color the system applies to interface icons, buttons, and text; in macOS, people can override it with their own accent color.
- Consider a custom font only if it's legible at all sizes and supports accessibility features like Bold Text and larger type. Pair a custom font for headlines/subheadings with system fonts for body and captions — system fonts are optimized for small-size legibility.
- Incorporate branding in refined, unobtrusive ways; don't spend screen space on elements that only display a brand asset.
- Use standard patterns consistently — expected component locations, standard symbols — even in a stylized interface.
- Don't repeat your logo throughout the app unless it's essential for context.
- Don't use the launch screen as a branding opportunity — it disappears too quickly; use a welcome or onboarding screen instead.
- Follow Apple's trademark guidelines: Apple trademarks must not appear in your app name or images.

**Platform deltas:**
- All platforms: no additional considerations.

## Color
*Last changed: 2025-12*

**Purpose:** Use color to enhance communication, evoke your brand, communicate status and feedback, and convey information hierarchy.

**Use it when / not when:**
- Use system colors when possible — they define light, dark, and increased-contrast variants automatically and adapt to vibrancy and accessibility settings.
- Prefer custom colors only when expressing brand or personality; supply light and dark variants plus an increased-contrast option for each — even if your app ships in a single appearance mode (needed for Liquid Glass adaptivity).
- Prefer system-provided color controls (`ColorPicker`) when letting people choose colors.

**Best practices:**
- Don't use the same color to mean different things; use color consistently for status and interactivity.
- Don't rely solely on color to differentiate objects, indicate interactivity, or communicate essential information — add text labels or glyph shapes.
- Consider cultural color perception (e.g., red is negative in some cultures, positive in others).
- Don't hard-code system color values — they can change between releases; use APIs like `Color`.
- Don't redefine semantic meanings of dynamic system colors (e.g., don't use `separator` as a text color or `secondaryLabel` as a background).
- Test colors under varied lighting, on multiple devices, with True Tone displays (apps can tune the effect via `UIWhitePointAdaptivityStyle`), and with different color profiles (P3 vs sRGB).
- Consider how artwork and translucency affect nearby colors (e.g., light scheme over map mode, dark over satellite).
- Liquid Glass: apply color sparingly; reserve it for elements that benefit from emphasis (status, primary actions). Tint the background of a single prominent button (like Done) rather than its symbol/text; don't tint multiple controls.
- With colorful backgrounds or rich content, prefer monochromatic toolbars/tab bars; with monochromatic content, a brand accent color works well.
- Keep the default/resting state of scrollable content legible beneath controls; avoid overlapping similar colors between content and controls.
- Apply color profiles to images; sRGB is accurate on most displays. Use Display P3 at 16 bits per pixel (per channel), exported as PNG, for wide-color displays; provide per-color-space image/color variants in asset catalogs when P3 colors clip or look indistinct on sRGB.

**Specs:**

System colors — RGB values (SwiftUI API = `Color.<name>`):

| Name | Light | Dark | Increased contrast (light) | Increased contrast (dark) |
|---|---|---|---|---|
| Red | 255,56,60 | 255,66,69 | 233,21,45 | 255,97,101 |
| Orange | 255,141,40 | 255,146,48 | 197,83,0 | 255,160,86 |
| Yellow | 255,204,0 | 255,214,0 | 161,106,0 | 254,223,67 |
| Green | 52,199,89 | 48,209,88 | 0,137,50 | 74,217,104 |
| Mint | 0,200,179 | 0,218,195 | 0,133,117 | 84,223,203 |
| Teal | 0,195,208 | 0,210,224 | 0,129,152 | 59,221,236 |
| Cyan | 0,192,232 | 60,211,254 | 0,126,174 | 109,217,255 |
| Blue | 0,136,255 | 0,145,255 | 30,110,244 | 92,184,255 |
| Indigo | 97,85,245 | 109,124,255 | 86,74,222 | 167,170,255 |
| Purple | 203,48,224 | 219,52,242 | 176,47,194 | 234,141,255 |
| Pink | 255,45,85 | 255,55,95 | 231,18,77 | 255,138,196 |
| Brown | 172,127,94 | 183,138,102 | 149,109,81 | 219,166,121 |

visionOS system colors use the default dark values.

iOS/iPadOS system grays (UIKit; SwiftUI equivalent of `systemGray` is `gray`):

| Name | Light | Dark | Increased contrast (light) | Increased contrast (dark) |
|---|---|---|---|---|
| systemGray | 142,142,147 | 142,142,147 | 108,108,112 | 174,174,178 |
| systemGray2 | 174,174,178 | 99,99,102 | 142,142,147 | 124,124,128 |
| systemGray3 | 199,199,204 | 72,72,74 | 174,174,178 | 84,84,86 |
| systemGray4 | 209,209,214 | 58,58,60 | 188,188,192 | 68,68,70 |
| systemGray5 | 229,229,234 | 44,44,46 | 216,216,220 | 54,54,56 |
| systemGray6 | 242,242,247 | 28,28,30 | 235,235,240 | 36,36,38 |

**Platform deltas:**
- iOS/iPadOS: Two dynamic background sets — system (`systemBackground`, `secondarySystemBackground`, `tertiarySystemBackground`) and grouped (`systemGroupedBackground`, `secondarySystemGroupedBackground`, `tertiarySystemGroupedBackground`). Use grouped for grouped table views; otherwise the system set. Primary = overall view, secondary = grouping within it, tertiary = grouping within secondary. Foreground dynamic colors: `label`, `secondaryLabel`, `tertiaryLabel`, `quaternaryLabel`, `placeholderText`, `separator` (translucent), `opaqueSeparator`, `link`.
- macOS: Dynamic system colors (Developer palette in the Color panel): `alternateSelectedControlTextColor`, `alternatingContentBackgroundColors`, `controlAccentColor`, `controlBackgroundColor`, `controlColor`, `controlTextColor`, `currentControlTint`, `disabledControlTextColor`, `findHighlightColor`, `gridColor`, `headerTextColor`, `highlightColor`, `keyboardFocusIndicatorColor`, `labelColor`, `linkColor`, `placeholderTextColor`, `quaternaryLabelColor`, `secondaryLabelColor`, `selectedContentBackgroundColor`, `selectedControlColor`, `selectedControlTextColor`, `selectedMenuItemTextColor`, `selectedTextBackgroundColor`, `selectedTextColor`, `separatorColor`, `shadowColor`, `tertiaryLabelColor`, `textBackgroundColor`, `textColor`, `underPageBackgroundColor`, `unemphasizedSelectedContentBackgroundColor`, `unemphasizedSelectedTextBackgroundColor`, `unemphasizedSelectedTextColor`, `windowBackgroundColor`, `windowFrameTextColor`. App accent colors (macOS 11+): your accent applies only when the system Accent color setting is "multicolor"; otherwise the user's choice replaces it, except fixed-color sidebar icons, which keep their specified color.
- tvOS: Choose a limited palette coordinating with your logo. Don't use color alone to indicate focus — scaling and responsive animation are primary.
- visionOS: Use color sparingly, especially on glass — surroundings show through and affect legibility. Prefer color in bold text and large areas, not lightweight text or small areas. In fully immersive experiences, keep brightness balanced; avoid bright objects on very dark backgrounds, especially flashing or moving ones.
- watchOS: Use background color to communicate (e.g., Activity matches ring colors), not as flourish; avoid full-screen background color in long-lived views (workouts, audio). Graphic complications may render in tinted mode using a single wearer-selected color.

## Dark Mode
*Last changed: 2024-08*

**Purpose:** A systemwide dark color palette for comfortable low-light viewing that people expect every app to respect.

**Use it when / not when:**
- Support both light and dark appearances — people also use Auto, which can switch modes while your app runs.
- Prefer a permanently dark appearance only in rare cases, e.g., immersive media viewing where UI recedes (Stocks uses dark-only).

**Best practices:**
- Don't offer an app-specific appearance setting — it duplicates the system setting and makes your app look broken when it ignores the systemwide choice.
- Test legibility in both modes with Increase Contrast and Reduce Transparency on, separately and together.
- Dark Mode colors are not simple inversions of light colors — some invert, some don't.
- Use semantic, appearance-adapting colors (`labelColor`/`controlColor` in macOS, `separator` in iOS/iPadOS); define custom colors as asset-catalog Color Sets with bright and dim variants. Never hard-code values.
- Keep contrast ratio at minimum 4.5:1; strive for 7:1 for custom foreground/background pairs, especially small text.
- Slightly darken content images with white backgrounds to prevent glow in dark contexts.
- Use SF Symbols wherever possible — they adapt automatically with dynamic colors or vibrancy.
- Design separate light/dark interface icons if needed (e.g., add a subtle border so a dark glyph stays visible on a dark background); combine variants under a single asset-catalog name.
- Use system label colors (primary–quaternary) and system text views — they adapt automatically and handle vibrancy.

**Platform deltas:**
- iOS/iPadOS: Dark Mode uses base (dimmer, receding) and elevated (brighter, advancing) background sets; elevated also separates apps in multitasking and multiple windows. Prefer system background colors so these depth cues work.
- macOS: With the graphite accent color, desktop tinting makes window backgrounds pick up the desktop picture. Add some transparency to custom component backgrounds — only for components with a visible background/bezel in a neutral (colorless) state.
- tvOS: no additional considerations.
- visionOS, watchOS: Dark Mode isn't supported.

## Icons
*Last changed: 2025-06*

**Purpose:** Interface icons (glyphs) express a single concept with streamlined shapes so people instantly understand items, actions, and modes.

**Use it when / not when:**
- Use SF Symbols (as-is or customized) when a suitable symbol exists.
- Design custom interface icons when you need something SF Symbols doesn't provide; use a vector format (PDF or SVG) so the system scales it — PNG requires multiple resolution versions.

**Best practices:**
- Create recognizable, highly simplified designs built on familiar visual metaphors; too much detail makes icons confusing.
- Keep all icons in the app consistent in size, level of detail, stroke weight, and perspective; adjust individual dimensions to balance visual weight.
- Match icon weight to adjacent text weight unless deliberately emphasizing one.
- Optically center asymmetric icons by baking small positional adjustments into the asset's padding.
- Don't supply selected-state versions for icons in standard toolbars, tab bars, and buttons — the system handles selection appearance (selected toolbar icons receive the accent color).
- Use inclusive, gender-neutral imagery that's recognizable across cultures.
- Include text only when essential; localize individual characters, and provide a flipped variant for icons that suggest reading direction (right-to-left).
- Provide alternative text labels (accessibility descriptions) for VoiceOver.
- Don't replicate Apple hardware — designs change; use only Apple Design Resources images or Apple-product SF Symbols.

**Specs:**

Standard SF Symbols for common actions:

| Action | Symbol name |
|---|---|
| Cut | `scissors` |
| Copy | `document.on.document` |
| Paste | `document.on.clipboard` |
| Done / Save | `checkmark` |
| Cancel / Close / Deselect | `xmark` |
| Delete | `trash` |
| Undo | `arrow.uturn.backward` |
| Redo | `arrow.uturn.forward` |
| Compose | `square.and.pencil` |
| Duplicate | `plus.square.on.square` |
| Rename | `pencil` |
| Move to / Folder | `folder` |
| Attach | `paperclip` |
| Add | `plus` |
| More | `ellipsis` |
| Select | `checkmark.circle` |
| Superscript | `textformat.superscript` |
| Subscript | `textformat.subscript` |
| Bold | `bold` |
| Italic | `italic` |
| Underline | `underline` |
| Align Left | `text.alignleft` |
| Center | `text.aligncenter` |
| Justified | `text.justify` |
| Align Right | `text.alignright` |
| Search | `magnifyingglass` |
| Find / Find and Replace / Find Next / Find Previous / Use Selection for Find | `text.page.badge.magnifyingglass` |
| Filter | `line.3.horizontal.decrease` |
| Share / Export | `square.and.arrow.up` |
| Print | `printer` |
| Account / User / Profile | `person.crop.circle` |
| Dislike | `hand.thumbsdown` |
| Like | `hand.thumbsup` |
| Bring to Front | `square.3.layers.3d.top.filled` |
| Send to Back | `square.3.layers.3d.bottom.filled` |
| Bring Forward | `square.2.layers.3d.top.filled` |
| Send Backward | `square.2.layers.3d.bottom.filled` |
| Alarm | `alarm` |
| Archive | `archivebox` |
| Calendar | `calendar` |

**Platform deltas:**
- iOS/iPadOS, tvOS, visionOS, watchOS: no additional considerations.
- macOS (document icons): If you don't supply one, macOS composites your app icon + file extension onto the folded-corner shape. Custom document icons combine any of background fill, center image, and text. Design simple shapes with a reduced palette — icons display as small as 16x16 px; reduce detail in small versions (fewer/thicker lines at 32x32 px, drop fine detail at 16x16 px). Avoid important content in the top-right corner (folded corner is drawn over it). Background fill sizes: 512x512 @1x / 1024x1024 @2x; 256x256 @1x / 512x512 @2x; 128x128 @1x / 256x256 @2x; 32x32 @1x / 64x64 @2x; 16x16 @1x / 32x32 @2x. Center image sizes: 256x256 @1x / 512x512 @2x; 128x128 @1x / 256x256 @2x; 32x32 @1x / 64x64 @2x; 16x16 @1x / 32x32 @2x. The center image measures half the icon canvas; keep a margin of ~10% of the canvas, with the image occupying ~80% (e.g., 205x205 px in a 256x256 px canvas). Optionally replace an unfamiliar extension with a short descriptive term (e.g., "scene" not "scn"); the system scales and capitalizes the text.

## Images
*Last changed: 2025-12*

**Purpose:** Deliver artwork at the right formats and scale factors so it looks sharp on every device you support.

**Best practices:**
- A point is an abstract unit: on 2D displays it maps to pixels by scale factor (@1x = 1:1, @2x = 2:1, @3x = 3:1); in visionOS it's an angular value that scales with viewing distance.
- Provide high-resolution assets for every bitmap image on every supported device; tag filenames with @1x/@2x/@3x in the asset catalog.
- Design at the lowest resolution and scale up; position vector control points at whole values so they stay raster-aligned at 2x and 3x.
- Include a color profile with each image.
- Always test images on a range of actual devices.

**Specs:**

| Platform | Scale factors |
|---|---|
| iPadOS, watchOS | @2x |
| iOS | @2x and @3x |
| visionOS | @2x or higher |
| macOS, tvOS | @1x and @2x |

| Image type | Format |
|---|---|
| Bitmap/raster work | De-interlaced PNG |
| PNG not needing full 24-bit color | 8-bit color palette |
| Photos | JPEG (optimized) or HEIC |
| Stereo or spatial photos | Stereo HEIC |
| Flat icons/artwork needing high-resolution scaling | PDF or SVG |

watchOS autoscaling PDF image scale (design for 40mm/42mm at 2x):

| Screen size | Image scale |
|---|---|
| 38mm | 90% |
| 40mm | 100% |
| 41mm | 106% |
| 42mm | 100% |
| 44mm | 110% |
| 45mm | 119% |
| 49mm | 119% |

**Platform deltas:**
- iOS/iPadOS, macOS: no additional considerations.
- tvOS: Layered images (2–5 layers) are required for the parallax focus effect. Use standard views/focus APIs (e.g., `FocusState`) to get parallax automatically. Foreground layers: prominent elements and text; middle: secondary content/shadows; background: must be opaque (error if not). Keep layering subtle; leave a safe zone around foreground content since layers crop during scaling; preview in Xcode, Parallax Previewer, or the Parallax Exporter plug-in, then on a real TV.
- visionOS: Create a layered app icon (2–3 layers). Prefer vector art for 2D images; the system dynamically scales image resolution. Rasterized images above @2x trade file size and runtime performance for close-up sharpness — performance suffers especially over @6x; apply high-quality image filtering. Spatial photos require stereo HEIC with spatial metadata; use the feathered glass background effect for text over them; show spatial photos/scenes in standalone views (sheet/window), not inline; spatial scenes take seconds to generate, so use explicit actions/pagination rather than many at once; prefer larger, centered spatial scenes; keep immersive UI minimal.
- watchOS: Avoid transparency to keep files small (composite the background in), except in template images (complications, menu icons) where transparency determines where color applies. Use autoscaling PDFs for one asset across all screen sizes.

## Materials
*Last changed: 2025-09*

**Purpose:** Visual effects (Liquid Glass and standard materials) that create depth, layering, and hierarchy between foreground and background elements.

**Use it when / not when:**
- Use Liquid Glass for the floating functional layer — controls and navigation (tab bars, sidebars) above content.
- Use standard materials in the content layer (e.g., app backgrounds) — never Liquid Glass there, except transient interactive elements (sliders, toggles) which adopt it while a person is actively manipulating them.
- Use the `regular` Liquid Glass variant for most components, anywhere background content might hurt legibility or text is significant (alerts, sidebars, popovers).
- Use the `clear` variant only over visually rich media backgrounds (photos, video) where content visibility matters most.

**Best practices:**
- Apply Liquid Glass effects to custom controls sparingly — standard components adopt the material automatically; overuse distracts from content.
- With clear Liquid Glass over bright content, add a dark dimming layer of 35% opacity; skip the dimming layer when content is sufficiently dark or AVKit playback controls already supply one.
- Choose standard materials by semantic purpose, never by apparent color — system settings change their appearance.
- Use vibrant colors on top of materials for legibility (e.g., not `systemGray3` labels).
- Thicker (more opaque) materials give better contrast for text and fine detail; thinner (more translucent) ones preserve context.

**Platform deltas:**
- iOS/iPadOS: Four standard materials — `ultraThin`, `thin`, `regular` (default), `thick`. Vibrancy levels for labels: `UIVibrancyEffectStyle.label` (default), `.secondaryLabel`, `.tertiaryLabel`, `.quaternaryLabel` — avoid quaternary on `thin`/`ultraThin` (contrast too low). Fills: `.fill` (default), `.secondaryFill`, `.tertiaryFill`. Separators: one default vibrancy value, works on all materials.
- macOS: Standard materials with designated purposes plus vibrant versions of all system colors (`NSVisualEffectView.Material`). Test when vibrancy helps custom views. Choose a blending mode: behind-window or within-window (`NSVisualEffectView.BlendingMode`).
- tvOS: Liquid Glass appears in navigation and system experiences (Top Shelf, Control Center); image views and buttons adopt it on focus. Standard materials: `ultraThin` for full-screen views needing a light scheme; `thin` for overlays needing a light scheme; `regular` for overlays; `thick` for overlays needing a dark scheme.
- visionOS: Windows use the system glass material (unmodifiable) that lets surroundings show through; prefer translucency over opaque colors. For custom components: `thin` highlights interactive elements (buttons, selection), `regular` separates sections (sidebar, grouped table), `thick` creates a dark element atop `regular`. Vibrancy: `label` for standard text, `secondaryLabel` for footnotes/subtitles, `tertiaryLabel` only for inactive elements where legibility isn't critical.
- watchOS: Use materials for context in full-screen modal views; don't remove or replace the default material backgrounds of modal sheets.

## SF Symbols
*Last changed: 2025-07*

**Purpose:** Thousands of configurable symbols that integrate with the San Francisco system font, auto-aligning with text across all weights and sizes.

**Use it when / not when:**
- Use symbols wherever interface icons appear — toolbars, tab bars, context menus, within text.
- Never use symbols (or confusingly similar images) in app icons, logos, or any trademarked use — prohibited by the license. Symbol availability depends on the OS version you target.

**Best practices:**
- Rendering modes: **Monochrome** (one color, all layers), **Hierarchical** (one color, opacity varies per layer level), **Palette** (two-plus colors, one per layer; two colors on a three-layer symbol means secondary and tertiary share), **Multicolor** (intrinsic colors, e.g., green `leaf`, red `trash.slash`). Layers are primary/secondary/tertiary. Use system colors so symbols adapt to accessibility settings, vibrancy, and Dark Mode. Confirm the chosen mode stays legible in every context; "automatic" gives the preferred mode but verify it.
- Gradients (SF Symbols 7+): smooth linear gradient from a single source color; works in all rendering modes and on custom symbols; best at larger sizes.
- Variable color: maps layers to thresholds between 0–100% to show changing values (capacity, strength); layers can opt out. Use it to communicate change, not depth — use Hierarchical mode for depth.
- Weights and scales: nine weights (ultralight–black) matching San Francisco font weights for precise text matching; three scales (small, medium default, large) defined relative to cap height — adjust emphasis without breaking weight matching.
- Design variants: outline (most common; pairs with text in toolbars/lists), fill (more emphasis; good for iOS tab bars, swipe actions, accent-color selection), slash (unavailability), enclosed circle/square/rectangle (better small-size legibility). Variants combine; the displaying view often picks the variant automatically (iOS tab bar prefers fill, toolbar prefers outline). Localized variants exist for Latin, Arabic, Hebrew, Hindi, Thai, Chinese, Japanese, Korean, Cyrillic, Devanagari, and several Indic numeral systems, and adapt automatically.
- Animations: Appear, Disappear, Bounce (one-shot feedback), Scale (persists until changed), Pulse (opacity; ongoing activity), Variable Color (cumulative or iterative; open-loop vs closed-loop layer arrangements), Replace (down-up, up-up, off-up), Magic Replace (default replace for related shapes; falls back to down-up), Wiggle (call attention), Breathe (opacity + size; ongoing activity), Rotate (whole symbol or By Layer), Draw On/Draw Off (SF Symbols 7+; along guide points, all-at-once, staggered, or per layer). Apply judiciously, with a clear communicative purpose matching your app's tone.
- Custom symbols: export a template from a similar symbol and edit in a vector tool; annotate layers with colors or hierarchy levels. Keep detail, optical weight, alignment, position, and perspective consistent with system symbols — simple, recognizable, inclusive, directly related to meaning. Use negative side margins for optical alignment of badged symbols (naming pattern like "left-margin-Regular-M"). Annotate layers (and Z-order) for animation; draw whole shapes plus erase layers rather than cutouts so animations behave. Use the SF Symbols component library for enclosures/badges instead of building them by hand. Provide VoiceOver alternative text. Don't replicate Apple products, and don't customize symbols representing Apple features/products.

**Platform deltas:**
- All platforms: no additional considerations.

## Typography
*Last changed: 2025-12*

**Purpose:** Typographic choices that keep text legible, convey information hierarchy, and express your brand or style.

**Use it when / not when:**
- Use the system fonts and built-in text styles when possible — consistent hierarchy plus automatic Dynamic Type and larger accessibility sizes.
- Prefer custom fonts only when brand demands it; match the recommended minimum sizes, support Dynamic Type and Bold Text yourself, and aim larger than the minimums for thin weights. In Unity games, use Apple's Unity plug-ins for Dynamic Type, or provide your own text-size controls.

**Best practices:**
- Follow per-platform default and minimum text sizes (see Specs); test legibility in context and on every platform a game ships on.
- Avoid Ultralight, Thin, and Light weights — prefer Regular, Medium, Semibold, or Bold.
- Adjust weight, size, and color to signal hierarchy; keep relative hierarchy intact when text sizes change.
- Minimize the number of typefaces — mixing too many obscures hierarchy and hinders readability.
- San Francisco (SF) family: SF Pro, SF Compact, SF Arabic, SF Armenian, SF Georgian, SF Hebrew, SF Mono, plus rounded variants of most; New York (NY) is the companion serif. Both ship as variable fonts, weights Ultralight–Black, SF also in Condensed/Expanded widths. SF Symbols weights match exactly.
- Text styles bundle weight, point size, and leading per text size; modify via symbolic traits (e.g., bold) and leading (loose for wide columns/long passages, tight for height-constrained spots — but never tight leading for 3+ lines).
- In mockups of the variable system fonts, adjust tracking per point size (see tracking table).
- Dynamic Type (iOS, iPadOS, tvOS, visionOS, watchOS): verify layouts at all sizes including Larger Accessibility Text Sizes; scale meaningful glyphs with text (SF Symbols do automatically); minimize truncation (configure labels with as many lines as needed, `numberOfLines`); at accessibility sizes switch to stacked layouts and fewer columns (`isAccessibilityCategory`); keep primary elements at the top regardless of size.

**Specs:**

Default and minimum text sizes:

| Platform | Default | Minimum |
|---|---|---|
| iOS, iPadOS | 17 pt | 11 pt |
| macOS | 13 pt | 10 pt |
| tvOS | 29 pt | 23 pt |
| visionOS | 17 pt | 12 pt |
| watchOS | 16 pt | 12 pt |

iOS/iPadOS Dynamic Type — size/leading (pt) per size category. Emphasized variants via `bold()` (SwiftUI) or `traitBold` (UIKit):

| Style | Weight (Emphasized) | xSmall | Small | Medium | Large (default) | xLarge | xxLarge | xxxLarge |
|---|---|---|---|---|---|---|---|---|
| Large Title | Regular (Bold) | 31/38 | 32/39 | 33/40 | 34/41 | 36/43 | 38/46 | 40/48 |
| Title 1 | Regular (Bold) | 25/31 | 26/32 | 27/33 | 28/34 | 30/37 | 32/39 | 34/41 |
| Title 2 | Regular (Bold) | 19/24 | 20/25 | 21/26 | 22/28 | 24/30 | 26/32 | 28/34 |
| Title 3 | Regular (Semibold) | 17/22 | 18/23 | 19/24 | 20/25 | 22/28 | 24/30 | 26/32 |
| Headline | Semibold (Semibold) | 14/19 | 15/20 | 16/21 | 17/22 | 19/24 | 21/26 | 23/29 |
| Body | Regular (Semibold) | 14/19 | 15/20 | 16/21 | 17/22 | 19/24 | 21/26 | 23/29 |
| Callout | Regular (Semibold) | 13/18 | 14/19 | 15/20 | 16/21 | 18/23 | 20/25 | 22/28 |
| Subhead | Regular (Semibold) | 12/16 | 13/18 | 14/19 | 15/20 | 17/22 | 19/24 | 21/28 |
| Footnote | Regular (Semibold) | 12/16 | 12/16 | 12/16 | 13/18 | 15/20 | 17/22 | 19/24 |
| Caption 1 | Regular (Semibold) | 11/13 | 11/13 | 11/13 | 12/16 | 14/19 | 16/21 | 18/23 |
| Caption 2 | Regular (Semibold) | 11/13 | 11/13 | 11/13 | 11/13 | 13/18 | 15/20 | 17/22 |

iOS/iPadOS larger accessibility sizes — size/leading (pt):

| Style | AX1 | AX2 | AX3 | AX4 | AX5 |
|---|---|---|---|---|---|
| Large Title | 44/52 | 48/57 | 52/61 | 56/66 | 60/70 |
| Title 1 | 38/46 | 43/51 | 48/57 | 53/62 | 58/68 |
| Title 2 | 34/41 | 39/47 | 44/52 | 50/59 | 56/66 |
| Title 3 | 31/38 | 37/44 | 43/51 | 49/58 | 55/65 |
| Headline | 28/34 | 33/40 | 40/48 | 47/56 | 53/62 |
| Body | 28/34 | 33/40 | 40/48 | 47/56 | 53/62 |
| Callout | 26/32 | 32/39 | 38/46 | 44/52 | 51/60 |
| Subhead | 25/31 | 30/37 | 36/43 | 42/50 | 49/58 |
| Footnote | 23/29 | 27/33 | 33/40 | 38/46 | 44/52 |
| Caption 1 | 22/28 | 26/32 | 32/39 | 37/44 | 43/51 |
| Caption 2 | 20/25 | 24/30 | 29/35 | 34/41 | 40/48 |

macOS built-in text styles (no Dynamic Type):

| Style | Weight | Size | Line height | Emphasized weight |
|---|---|---|---|---|
| Large Title | Regular | 26 | 32 | Bold |
| Title 1 | Regular | 22 | 26 | Bold |
| Title 2 | Regular | 17 | 22 | Bold |
| Title 3 | Regular | 15 | 20 | Semibold |
| Headline | Bold | 13 | 16 | Heavy |
| Body | Regular | 13 | 16 | Semibold |
| Callout | Regular | 12 | 15 | Semibold |
| Subheadline | Regular | 11 | 14 | Semibold |
| Footnote | Regular | 10 | 13 | Semibold |
| Caption 1 | Regular | 10 | 13 | Medium |
| Caption 2 | Medium | 10 | 13 | Semibold |

tvOS built-in text styles:

| Style | Weight | Size | Leading | Emphasized weight |
|---|---|---|---|---|
| Title 1 | Medium | 76 | 96 | Bold |
| Title 2 | Medium | 57 | 66 | Bold |
| Title 3 | Medium | 48 | 56 | Bold |
| Headline | Medium | 38 | 46 | Bold |
| Subtitle 1 | Regular | 38 | 46 | Medium |
| Callout | Medium | 31 | 38 | Bold |
| Body | Medium | 29 | 36 | Bold |
| Caption 1 | Medium | 25 | 32 | Bold |
| Caption 2 | Medium | 23 | 30 | Bold |

watchOS Dynamic Type — size/leading (pt). Weights: Headline is Semibold, all others Regular; emphasized weight is Bold for Large Title, Semibold for all other styles:

| Style | xSmall | Small (default 38mm) | Large (default 40/41/42mm) | xLarge (default 44/45/49mm) | xxLarge | xxxLarge |
|---|---|---|---|---|---|---|
| Large Title | 30/32.5 | 32/34.5 | 36/38.5 | 40/42.5 | 41/43.5 | 42/44.5 |
| Title 1 | 28/30.5 | 30/32.5 | 34/36.5 | 38/40.5 | 39/41.5 | 40/42.5 |
| Title 2 | 24/26.5 | 26/28.5 | 28/30.5 | 30/32.5 | 31/33.5 | 32/34.5 |
| Title 3 | 17/19.5 | 18/20.5 | 19/21.5 | 20/22.5 | 21/23.5 | 22/24.5 |
| Headline | 14/16.5 | 15/17.5 | 16/18.5 | 17/19.5 | 18/20.5 | 19/21.5 |
| Body | 14/16.5 | 15/17.5 | 16/18.5 | 17/19.5 | 18/20.5 | 19/21.5 |
| Caption 1 | 13/15.5 | 14/16.5 | 15/17.5 | 16/18.5 | 17/19.5 | 18/20.5 |
| Caption 2 | 12/14.5 | 13/15.5 | 14/16.5 | 15/17.5 | 16/18.5 | 17/19.5 |
| Footnote 1 | 11/13.5 | 12/14.5 | 13/15.5 | 14/16.5 | 15/17.5 | 16/18.5 |
| Footnote 2 | 10/12.5 | 11/13.5 | 12/14.5 | 13/15.5 | 14/16.5 | 15/17.5 |

watchOS larger accessibility sizes — size/leading (pt):

| Style | AX1 | AX2 | AX3 |
|---|---|---|---|
| Large Title | 44/46.5 | 45/47.5 | 46/48.5 |
| Title 1 | 42/44.5 | 43/46 | 44/47 |
| Title 2 | 34/41 | 35/37.5 | 36/38.5 |
| Title 3 | 24/26.5 | 25/27.5 | 26/28.5 |
| Headline | 21/23.5 | 22/24.5 | 23/25.5 |
| Body | 21/23.5 | 22/24.5 | 23/25.5 |
| Caption 1 | 18/20.5 | 19/21.5 | 20/22.5 |
| Caption 2 | 17/19.5 | 18/20.5 | 19/21.5 |
| Footnote 1 | 16/18.5 | 17/19.5 | 18/20.5 |
| Footnote 2 | 15/17.5 | 16/17.5 | 17/19.5 |

Tracking values (1/1000 em; the HIG also lists per-size point equivalents ≈ size x em/1000; not all apps express tracking as 1/1000 em). macOS and tvOS system tracking matches the SF Pro column. "—" = size not listed for that font:

| Size (pt) | SF Pro | SF Pro Rounded | New York | SF Compact (watchOS) | SF Compact Rounded (watchOS) |
|---|---|---|---|---|---|
| 6 | +41 | +87 | +40 | +50 | +28 |
| 7 | +34 | +80 | +32 | +30 | +26 |
| 8 | +26 | +72 | +25 | +30 | +24 |
| 9 | +19 | +65 | +20 | +30 | +22 |
| 10 | +12 | +58 | +16 | +30 | +20 |
| 11 | +6 | +52 | +11 | +24 | +18 |
| 12 | 0 | +46 | +6 | +20 | +16 |
| 13 | -6 | +40 | +4 | +16 | +14 |
| 14 | -11 | +35 | +2 | +14 | +12 |
| 15 | -16 | +30 | 0 | +4 | +10 |
| 16 | -20 | +26 | -2 | 0 | +8 |
| 17 | -26 | +22 | -4 | -4 | +6 |
| 18 | -25 | +21 | -6 | -8 | +4 |
| 19 | -24 | +20 | -8 | -12 | +2 |
| 20 | -23 | +18 | -10 | 0 | 0 |
| 21 | -18 | +17 | -10 | -2 | -2 |
| 22 | -12 | +16 | -10 | -4 | -4 |
| 23 | -4 | +16 | -11 | -6 | -6 |
| 24 | +3 | +15 | -11 | -8 | -8 |
| 25 | +6 | +14 | -11 | -10 | -10 |
| 26 | +8 | +14 | -12 | -11 | -11 |
| 27 | +11 | +14 | -12 | -12 | -12 |
| 28 | +14 | +13 | -12 | -12 | -12 |
| 29 | +14 | +13 | -12 | -14 | -14 |
| 30 | +14 | +12 | -12 | -14 | -14 |
| 31 | +13 | +12 | -13 | -15 | -15 |
| 32 | +13 | +12 | -13 | -16 | -16 |
| 33 | +12 | +12 | -13 | -17 | -17 |
| 34 | +12 | +12 | -14 | -18 | -18 |
| 35 | +11 | +11 | -14 | -18 | -18 |
| 36 | +10 | +11 | -14 | -20 | -20 |
| 37 | +10 | +10 | — | -20 | -20 |
| 38 | +10 | +10 | -14 | -20 | -20 |
| 39 | +10 | +10 | — | -20 | -20 |
| 40 | +10 | +10 | -14 | -20 | -20 |
| 41 | +9 | +10 | — | -20 | -20 |
| 42 | +9 | +10 | -14 | -20 | -20 |
| 43 | +9 | +9 | — | -20 | -20 |
| 44 | +8 | +8 | -14 | -20 | -20 |
| 45 | +8 | +8 | — | -20 | -20 |
| 46 | +8 | +8 | -14 | -20 | -20 |
| 47 | +8 | +8 | — | -20 | -20 |
| 48 | +8 | +8 | -14 | -20 | -20 |
| 49 | +7 | +8 | — | -21 | -21 |
| 50 | +7 | +7 | -14 | -21 | -21 |
| 51 | +7 | +6 | — | -21 | -21 |
| 52 | +6 | +6 | -14 | -21 | -21 |
| 53 | +6 | +6 | — | -22 | -22 |
| 54 | +6 | +6 | -15 | -22 | -22 |
| 56 | +6 | +6 | — | -22 | -22 |
| 58 | +5 | +4 | -15 | -22 | -22 |
| 60 | +4 | +4 | — | -22 | -22 |
| 62 | +4 | +4 | -15 | -22 | -22 |
| 64 | +4 | +3 | — | -23 | -23 |
| 66 | +3 | +2 | -15 | -24 | -24 |
| 68 | +2 | +2 | — | -24 | -24 |
| 70 | +2 | +2 | -16 | -24 | -24 |
| 72 | +2 | +2 | -16 | -24 | -24 |
| 76 | +1 | +1 | — | -25 | -25 |
| 80 | 0 | 0 | -16 | -26 | -26 |
| 84 | 0 | 0 | — | -26 | -26 |
| 88 | 0 | 0 | -16 | -26 | -26 |
| 92 | 0 | 0 | — | -28 | -28 |
| 96 | 0 | 0 | -16 | -28 | -28 |
| 100 | — | — | -16 | — | — |
| 120 | — | — | -16 | — | — |
| 140 | — | — | -16 | — | — |
| 160 | — | — | -16 | — | — |
| 180 | — | — | -17 | — | — |
| 200 | — | — | -17 | — | — |
| 220 | — | — | -18 | — | — |
| 240 | — | — | -18 | — | — |
| 260 | — | — | -18 | — | — |

Point sizes assume 144 ppi for @2x and 216 ppi for @3x designs (tvOS: 72 ppi @1x, 144 ppi @2x; watchOS: 144 ppi @2x).

**Platform deltas:**
- iOS/iPadOS: SF Pro is the system font; NY also available.
- macOS: SF Pro is the system font; NY only via Mac Catalyst. No Dynamic Type. Use dynamic system font variants to match standard controls: `controlContentFont(ofSize:)`, `labelFont(ofSize:)`, `menuFont(ofSize:)`, `menuBarFont(ofSize:)`, `messageFont(ofSize:)`, `paletteFont(ofSize:)`, `titleBarFont(ofSize:)`, `toolTipsFont(ofSize:)`, `userFont(ofSize:)` (document text), `userFixedPitchFont(ofSize:)` (monospaced document text), `boldSystemFont(ofSize:)`, `systemFont(ofSize:)`.
- tvOS: SF Pro is the system font; NY also available.
- visionOS: SF Pro is the system font; with NY you must specify type styles. Uses bolder body/title Dynamic Type styles and adds Extra Large Title 1 and Extra Large Title 2 for wide editorial layouts. Prefer 2D text over 3D for anything people must read; default white text gives strong contrast on the glass material; bold text without a background instead of adding shadows; billboard spatial labels (keep text facing the viewer, rotating around the y-axis).
- watchOS: SF Compact is the system font; NY also available; complications use SF Compact Rounded.
