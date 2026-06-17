# Components — System Experiences

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Components pages: App icons, Widgets, Controls, Complications, Watch faces, Home Screen quick actions, App Clips, iMessage apps and stickers.

## Contents
- [App icons](#app-icons)
- [Widgets](#widgets)
- [Controls](#controls)
- [Complications](#complications)
- [Watch faces](#watch-faces)
- [Home Screen quick actions](#home-screen-quick-actions)
- [App Clips](#app-clips)
- [iMessage apps and stickers](#imessage-apps-and-stickers)

### App icons
*Last changed: 2026-06*

**Purpose:** A unique, memorable icon that expresses your app's or game's purpose and personality and helps people recognize it at a glance across the Home Screen, search, notifications, settings, and share sheets.

**Best practices:**
- Provide layered icons (not flat) for the most control; the system applies Liquid Glass effects — specular highlights, refraction, translucency — that adapt with icon size and can differ between system versions.
- iOS, iPadOS, macOS, watchOS icons: a background layer plus one or more foreground layers. tvOS: 2–5 layers for a parallax/dynamism effect when focused. visionOS: a background layer plus one or two top layers forming a 3D object.
- For iOS/iPadOS/macOS/watchOS, build foreground layers in Icon Composer (in Xcode / Apple Developer site); define the background, adjust placement, apply effects, annotate default/dark/mono variants, preview, export. For tvOS and visionOS, add layers directly to an Xcode image stack.
- Prefer clearly defined edges in foreground layers; avoid soft/feathered edges so system highlights and shadows render well.
- Vary opacity in foreground layers to add depth; import fully opaque layers and adjust transparency in Icon Composer.
- Design a background that stands out and emphasizes foreground content; Icon Composer supports solid colors and gradients, so importing a custom background is usually unnecessary. If you import one, make it full-bleed and opaque.
- Prefer vector graphics (SVG, PDF) for layers; outline artwork and convert text to outline. Use PNG (lossless) for mesh gradients and raster art.
- Provide unmasked square layers for iOS/iPadOS/macOS/visionOS/watchOS and rectangular layers for tvOS; the system applies masking. Pre-masked layers harm specular highlights and create jagged edges.
- Keep primary content centered to survive corner adjustment and masking — especially for visionOS and watchOS circular masking. Use the grids in Apple Design Resources templates.
- Embrace simplicity: a single core concept expressed in a minimal number of shapes; avoid fine features that look busy with system shadows/highlights or vanish at small sizes.
- Keep the icon design visually consistent across every platform you support.
- Consider basing the design on filled, overlapping shapes (with transparency/blurring) for depth.
- Include text only when essential to your experience or brand; text doesn't support accessibility or localization and can clutter the icon. Avoid nonessential words ("Watch", "Play", "New", "For visionOS"). In tvOS, place any text above other layers so the parallax effect doesn't crop it.
- Prefer illustrations to photos; avoid extremely thin line weights and sharp corners (lost at small sizes); don't replicate standard UI components or use screenshots.
- Don't use replicas of Apple hardware products (copyrighted).
- Let the system handle blurring, shadows, beveled edges, glows, and other effects — don't bake them in. Test custom effects in Icon Composer, Device Hub, or on device.
- Create layer groupings in Icon Composer to apply effects to multiple layers at once; groups expose extra Liquid Glass options (specular highlights, refraction, translucency).
- iOS/iPadOS/macOS Home Screen appearances: default, dark, clear, tinted (the system auto-generates variants you don't supply). Keep core features consistent across appearances; don't swap elements per variant.
- Use the light icon as the basis for the dark icon; choose complementary colors, avoid excessively bright images; color backgrounds give the best contrast in dark icons.
- Consider offering alternate app icons (iOS, iPadOS, tvOS, and compatible apps in visionOS) via app settings.

Canonical implementations: Icon Composer (Xcode) for iOS/iPadOS/macOS/watchOS layered icons; asset catalog image stack for tvOS and visionOS.

**Specs:**

| Platform | Layout shape | Shape after masking | Layout size | Style | Appearances |
| --- | --- | --- | --- | --- | --- |
| iOS, iPadOS, macOS | Square | Rounded rectangle (square) | 1024x1024 px | Layered | Default, dark, clear light, clear dark, tinted light, tinted dark |
| tvOS | Rectangle (landscape) | Rounded rectangle (rectangular) | 800x480 px | Layered (Parallax) | N/A |
| visionOS | Square | Circular | 1024x1024 px | Layered (3D) | N/A |
| watchOS | Square | Circular | 1088x1088 px | Layered | N/A |

Color spaces: sRGB (color); Gray Gamma 2.2 (grayscale); Display P3 (wide-gamut color in iOS, iPadOS, macOS, tvOS, watchOS only). The system auto-scales smaller variants (Settings, notifications).

**Platform deltas:**
- iOS/iPadOS/macOS: No additional considerations.
- tvOS: Include a safe zone — focusing scales and moves the icon and may crop edges (foreground layers cropped more than background); safe zone varies by image size, layer depth, and motion.
- visionOS: Avoid a shape meant to look like a hole or concave area in the background layer — system shadow and specular highlights make it stand out instead of recede.
- watchOS: Avoid black backgrounds; lighten so the icon doesn't blend into the display.

### Widgets
*Last changed: 2025-12*

**Purpose:** Quick access to essential, glanceable information and focused interactions from your app in additional contexts (Home Screen, Lock Screen, Today View, StandBy, CarPlay, Notification Center, Mac desktop, Smart Stack, visionOS surfaces).

**Use it when / not when:**
- Use when: you can surface timely, dynamic, glanceable content and useful actions/deep links.
- Prefer Live Activities when: you need real-time updates for a task or event over a limited time — widgets don't show real-time information (iOS/iPadOS; same underlying frameworks, develop in tandem).
- Prefer complications design principles when: building Lock Screen widgets (functionally similar to watch complications; a design often works for both).

**Best practices:**
- Choose simple ideas tied to your app's main purpose; include timely content and relevant functionality; don't just replicate the app icon.
- Offer multiple sizes only when each adds value; small typically shows a single piece of information, larger sizes add layers; don't just expand a small widget to fill a larger area.
- Balance information density — neither sparse nor overly dense; use a larger size or graphics over text if too dense.
- Use brand elements thoughtfully; a small logo in the top-right corner is sufficient when needed (e.g. multi-source content).
- Tap/click a non-interactive area launches the app; deep link to the specific relevant location. Buttons and toggles can act without launching. Inline accessory widgets offer only one tap target.
- Refresh content periodically (no continuous real-time updates; the system may throttle). Let the system refresh dates/times to preserve update opportunities. Use animated transitions up to two seconds for updates.
- Use standard margins — 16 points for most widgets; tighter 11-point margins work for content groupings; widgets use smaller margins on the Mac desktop and on the Lock Screen (including StandBy).
- Coordinate content corner radius with the widget's corner radius via a SwiftUI container (`ContainerRelativeShape`).
- Prefer the system font, text styles, and SF Symbols; display text at 11 points or larger; never rasterize text (breaks scaling and VoiceOver).
- Convey meaning without relying on color alone (widgets can appear monochrome/tinted; watchOS may invert colors). Use full-color images judiciously — the system desaturates them in tinted/clear appearances by default; reserve full-color for media (e.g. album art) at smaller dimensions than the widget.
- Design a realistic gallery preview (real or realistic simulated data) and placeholder content (static components plus semi-opaque shapes for dynamic content).
- Write a succinct gallery description starting with an action verb; use sentence-style capitalization; group all sizes under one description. Optionally color the Add button to match your brand.
- Appearances: full-color (light/dark), clear (desaturated + translucency + highlights + Liquid Glass), tinted (desaturated + user tint color). Rendering modes: full-color, accented, vibrant.
- Accented mode: split the view hierarchy into an accent group and a primary group (`widgetAccentable(_:)`). On iPhone/iPad/Mac the system tints both white; on Apple Watch primary is white and accented takes the watch-face color.
- Vibrant mode: render content at full opacity; use white/light gray for prominent content and darker grayscale for secondary; use opaque grayscale values (not opacities of white) for the best material effect.

Canonical implementations: WidgetKit; SwiftUI views; `WidgetRenderingMode` (`fullColor`, `accented`, `vibrant`); `widgetAccentable(_:)`; `ContainerRelativeShape`; ActivityKit (Live Activities); RelevanceKit (watchOS Smart Stack); `WidgetMountingStyle` (`elevated`, `recessed`) and `WidgetTexture` (`paper`, `glass`) for visionOS; `LevelOfDetail` (`simplified`, `default`).

**Specs:**

System family widget contexts:

| Widget size | iPhone | iPad | Mac | Apple Vision Pro |
| --- | --- | --- | --- | --- |
| System small | Home Screen, Today View, StandBy, CarPlay | Home Screen, Today View, Lock Screen | Desktop, Notification Center | Horizontal and vertical surfaces |
| System medium | Home Screen, Today View | Home Screen, Today View | Desktop, Notification Center | Horizontal and vertical surfaces |
| System large | Home Screen, Today View | Home Screen, Today View | Desktop, Notification Center | Horizontal and vertical surfaces |
| System extra large | Not supported | Home Screen, Today View | Desktop, Notification Center | Horizontal and vertical surfaces |
| System extra large portrait | Not supported | Not supported | Not supported | Horizontal and vertical surfaces |

Accessory widget contexts:

| Widget size | iPhone | iPad | Apple Watch |
| --- | --- | --- | --- |
| Accessory circular | Lock Screen | Lock Screen | Watch complications and Smart Stack |
| Accessory corner | Not supported | Not supported | Watch complications |
| Accessory inline | Lock Screen | Lock Screen | Watch complications |
| Accessory rectangular | Lock Screen | Lock Screen | Watch complications and Smart Stack |

Rendering mode by platform:

| Platform | Full-color | Accented | Vibrant |
| --- | --- | --- | --- |
| iPhone | Home Screen, Today view, StandBy, CarPlay (background removed) | Home Screen, Today view | Lock Screen, StandBy in low-light |
| iPad | Home Screen, Today view | Home Screen, Today view | Lock Screen |
| Apple Watch | Smart Stack, complications | Smart Stack, complications | Not supported |
| Mac | Desktop, Notification Center | Not supported | Desktop |
| Apple Vision Pro | Horizontal and vertical surfaces | Horizontal and vertical surfaces | Not supported |

iOS dimensions (portrait, pt):

| Screen size | Small | Medium | Large | Circular | Rectangular | Inline |
| --- | --- | --- | --- | --- | --- | --- |
| 430×932 | 170x170 | 364x170 | 364x382 | 76x76 | 172x76 | 257x26 |
| 428x926 | 170x170 | 364x170 | 364x382 | 76x76 | 172x76 | 257x26 |
| 414x896 | 169x169 | 360x169 | 360x379 | 76x76 | 160x72 | 248x26 |
| 414x736 | 159x159 | 348x157 | 348x357 | 76x76 | 170x76 | 248x26 |
| 393x852 | 158x158 | 338x158 | 338x354 | 72x72 | 160x72 | 234x26 |
| 390x844 | 158x158 | 338x158 | 338x354 | 72x72 | 160x72 | 234x26 |
| 375x812 | 155x155 | 329x155 | 329x345 | 72x72 | 157x72 | 225x26 |
| 375x667 | 148x148 | 321x148 | 321x324 | 68x68 | 153x68 | 225x26 |
| 360x780 | 155x155 | 329x155 | 329x345 | 72x72 | 157x72 | 225x26 |
| 320x568 | 141x141 | 292x141 | 292x311 | N/A | N/A | N/A |

iPadOS dimensions (canvas / device, pt), selected screens:

| Screen size | Target | Small | Medium | Large | Extra large |
| --- | --- | --- | --- | --- | --- |
| 768x1024 | Canvas | 141x141 | 305.5x141 | 305.5x305.5 | 634.5x305.5 |
| 768x1024 | Device | 120x120 | 260x120 | 260x260 | 540x260 |
| 1024x1366 | Canvas | 170x170 | 378.5x170 | 378.5x378.5 | 795x378.5 |
| 1024x1366 | Device | 160x160 | 356x160 | 356x356 | 748x356 |

(Other iPad screens: 744x1133, 810x1080, 820x1180, 834x1112, 834x1194, 954x1373*, 970x1389*, 1192x1590*; * = Display Zoom set to More Space, where canvas equals device. See Apple Design Resources for the full table.)

visionOS dimensions:

| Widget | Size in pt | Size in mm (100%) |
| --- | --- | --- |
| Small | 158x158 | 268x268 |
| Medium | 338x158 | 574x268 |
| Large | 338x354 | 574x600 |
| Extra large | 450x338 | 763x574 |
| Extra large portrait | 338x450 | 574x763 |

watchOS Smart Stack widget dimensions (pt):

| Apple Watch size | Smart Stack widget |
| --- | --- |
| 40mm | 152x69.5 |
| 41mm | 165x72.5 |
| 44mm | 173x76.5 |
| 45mm | 184x80.5 |
| 49mm | 191x81.5 |

**Platform deltas:**
- iOS/iPadOS: Lock Screen widgets follow Complications principles; three Lock Screen shapes — inline text (above the clock), circular and rectangular (below the clock). Support the Always-On display on iPhone (reduced luminance; use gray levels with enough contrast).
- iOS StandBy and CarPlay: StandBy shows two small system widgets side-by-side scaled up; both StandBy and CarPlay use the small system family widget with the background removed. Don't use background colors in StandBy (blend with the black background). In low-light conditions the system renders StandBy widgets monochromatic with a red tint.
- macOS: No additional considerations.
- visionOS: Widgets are 3D objects placed on horizontal/vertical surfaces; persist across power cycles; full-color by default, accented when tinted with a system palette. Two proximity thresholds — `simplified` (distance: fewer details, larger type, no interactive elements) and `default` (nearby: more details, smaller type). People scale widgets 75–125%. Mounting styles: elevated (default; horizontal and vertical surfaces; tilts back on horizontal) and recessed (vertical surfaces only). Treatment styles: paper (print-like, responds to ambient lighting) and glass (layered, foreground stays bright/legible). Test across all system color palettes and lighting; test elevated designs at each system-provided frame width.
- watchOS: Smart Stack widgets default to a black background; consider a custom background color that conveys meaning. Use RelevanceKit relevance (location- or activity-based) to elevate the widget in the Smart Stack.
- tvOS: Not supported.

### Controls
*Last changed: 2024-06*

**Purpose:** A button or toggle that provides quick access to an app feature from Control Center, the Lock Screen, or the Action button.

**Use it when / not when:**
- Use when: an action provides the most benefit without launching the app (e.g. launching a Live Activity, toggling a state).
- Control buttons: perform an action, link to an area of the app, or launch a locked-device camera experience. Control toggles: switch between two states (on/off).

**Best practices:**
- Controls contain a symbol image, a title, and an optional value. Display varies by surface: Control Center shows the symbol and (at larger sizes) the title and value; Lock Screen shows only the symbol; Action button press-and-hold shows the symbol (and value if present) in the Dynamic Island.
- Update controls on interaction, on action completion, or remotely via push notification; reflect in-progress state.
- Choose a descriptive symbol (SF Symbols or custom) that conveys the action without title/value; for toggles supply a symbol for both on and off states (e.g. `door.garage.open` / `door.garage.closed`).
- Use symbol animations for state changes: toggles animate the on/off transition; buttons with a duration animate indefinitely while performing and stop on completion (`SymbolEffect`).
- Select a brand tint color; the system applies it to a toggle's symbol in its on state and to the value/symbol in the Dynamic Island when triggered from the Action button.
- Prompt for configuration when a control requires it (e.g. selecting a specific light) on first add; people can reconfigure anytime (`promptsForUserConfiguration()`).
- Provide Action button hint text using verbs (e.g. "Hold for Silent") via `controlWidgetActionHint(_:)`.
- Include a placeholder when title/value can vary, shown in the gallery before assignment.
- Hide sensitive information when the device is locked — have the system redact title/value (and optionally the symbol state, displaying the off-state symbol).
- Require authentication for security-affecting actions (e.g. unlocking a door, starting a car) via `IntentAuthenticationPolicy`.
- Camera experiences on a locked device (iOS 18+): a control can launch directly to your camera experience while locked; any task beyond capture requires unlock (`LockedCameraCapture`). Use the same camera UI in the app and the experience; provide instructions for adding the control.

Canonical implementations: WidgetKit; SwiftUI `ControlWidgetConfiguration`; `SymbolEffect`; `controlWidgetActionHint(_:)`; `IntentAuthenticationPolicy` (App Intents); `LockedCameraCapture`.

**Platform deltas:**
- iOS/iPadOS/macOS: No additional considerations.
- watchOS, tvOS, visionOS: Not supported.

### Complications
*Last changed: 2023-10*

**Purpose:** Display timely, relevant, glanceable information on the watch face that people see each time they raise their wrist.

**Best practices:**
- Identify essential, dynamic content people want at a glance; static complications are less likely to stay on the face.
- Support all complication families when possible (more families = more watch faces); if you can't show useful data for a family, supply an image (e.g. app icon) that still launches the app.
- Consider multiple complications per family, each deep-linking to its most relevant area; a different deep link per complication works best.
- Keep privacy in mind with the Always-On Retina display (info may be visible to others).
- Provide data as a timeline; the system limits timeline updates per day and stores a limited number of entries — choose update times that enhance usefulness.
- Choose a ring/gauge style by data: closed (percentage of a whole, e.g. battery), open (arbitrary min/max, e.g. speed), segmented (app-defined range, rapid changes, e.g. Noise).
- Make images look good in tinted mode (the system desaturates full-color images and applies a single color based on the wearer's selected color); don't rely on color alone; supply an alternative tinted-mode image if the desaturated version looks poor. With legacy templates, tinted mode applies only to graphic complications.
- Use line widths of two points or greater for complication content.
- Provide static placeholder images for each complication (sizes vary per layout/template and may not match the actual image size).
- Modern families (watchOS 9+): Circular, Corner, Inline, Rectangular. Rectangular layouts (watchOS 10+) may appear in the Smart Stack — optimize with background color/content, intents for relevancy, and a custom Smart-Stack layout.
- Legacy templates: Circular small, Modular small, Modular large, Extra large (nongraphic styles that don't take the wearer's color).

Canonical implementations: WidgetKit (migrated from ClockKit); `WidgetRenderingMode`; `WidgetFamily.accessoryRectangular`; `TimelineProvider.placeholder(in:)`.

**Specs:**

Circular family — regular-size image sizes (pt; px @2x):

| Image | 40mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- |
| Image | 42x42 (84x84) | 44.5x44.5 (89x89) | 47x47 (94x94) | 50x50 (100x100) |
| Closed gauge | 27x27 (54x54) | 28.5x28.5 (57x57) | 31x31 (62x62) | 32x32 (64x64) |
| Open gauge | 11x11 (22x22) | 11.5x11.5 (23x23) | 12x12 (24x24) | 13x13 (26x26) |
| Stack (not text) | 28x14 (56x28) | 29.5x15 (59x30) | 31x16 (62x32) | 33.5x16.5 (67x33) |

Regular circular default SwiftUI text: Rounded, Medium; 12 pt (40mm), 12.5 pt (41mm), 13 pt (44mm), 14.5 pt (45mm/49mm). Bezel text fills nearly 180° before truncating.

Circular family — extra-large (X-Large watch face) image sizes (pt; px @2x):

| Image | 40mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- |
| Image | 120x120 (240x240) | 127x127 (254x254) | 132x132 (264x264) | 143x143 (286x286) |
| Open gauge | 31x31 (62x62) | 33x33 (66x66) | 33x33 (66x66) | 37x37 (74x74) |
| Closed gauge | 77x77 (154x154) | 81.5x81.5 (163x163) | 87x87 (174x174) | 91.5x91.5 (183x183) |
| Stack | 80x40 (160x80) | 85x42 (170x84) | 87x44 (174x88) | 95x48 (190x96) |

Extra-large circular default SwiftUI text: Rounded, Medium; 34.5 pt (40mm), 36.5 pt (41mm), 36.5 pt (44mm), 41 pt (45mm/49mm).

Corner family — image sizes (pt; px @2x):

| Image | 40mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- |
| Circular | 32x32 (64x64) | 34x34 (68x68) | 36x36 (72x72) | 38x38 (76x76) |
| Gauge | 20x20 (40x40) | 21x21 (42x42) | 22x22 (44x44) | 24x24 (48x48) |
| Text | 20x20 (40x40) | 21x21 (42x42) | 22x22 (44x44) | 24x24 (48x48) |

Corner default SwiftUI text: Rounded, Semibold; 10 pt (40mm), 10.5 pt (41mm), 11 pt (44mm), 12 pt (45mm/49mm).

Inline family (utilitarian small image sizes, pt; px @2x):

| Content | 38mm | 40mm/42mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- | --- |
| Flat | 9-21x9 (18-42x18) | 10-22x10 (20-44x20) | 10.5-23.5x21 (21-47x21) | N/A | 12-26x12 (24-52x24) |
| Ring | 14x14 (28x28) | 14x14 (28x28) | 15x15 (30x30) | 16x16 (32x32) | 16.5x16.5 (33x33) |
| Square | 20x20 (40x40) | 22x22 (44x44) | 23.5x23.5 (47x47) | 25x25 (50x50) | 26x26 (52x52) |

Utilitarian large is primarily text with a leading interface icon, spanning the bottom of the face (Flat content: 9-21x9 pt at 38mm up to 12-26x12 pt at 45mm/49mm).

Rectangular family — image sizes (pt; px @2x):

| Content | 40mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- |
| Large image with title | 150x47 (300x94) | 159x50 (318x100) | 171x54 (342x108) | 178.5x56 (357x112) |
| Large image without title | 162x69 (324x138) | 171.5x73 (343x146) | 184x78 (368x156) | 193x82 (386x164) |
| Standard body | 12x12 (24x24) | 12.5x12.5 (25x25) | 13.5x13.5 (27x27) | 14.5x14.5 (29x29) |
| Text gauge | 12x12 (24x24) | 12.5x12.5 (25x25) | 13.5x13.5 (27x27) | 14.5x14.5 (29x29) |

Rectangular default SwiftUI text: Rounded, Medium; 16.5 pt (40mm), 17.5 pt (41mm), 18 pt (44mm), 19.5 pt (45mm/49mm).

Legacy templates (image sizes, pt; px @2x):

Circular small:

| Image | 38mm | 40mm/42mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- | --- |
| Ring | 20x20 (40x40) | 22x22 (44x44) | 23.5x23.5 (47x47) | 24x24 (48x48) | 26x26 (52x52) |
| Simple | 16x16 (32x32) | 18x18 (36x36) | 19x19 (38x38) | 20x20 (40x40) | 21.5x21.5 (43x43) |
| Stack | 16x7 (32x14) | 17x8 (34x16) | 18x8.5 (36x17) | 19x9 (38x18) | 19x9.5 (38x19) |

Modular small:

| Image | 38mm | 40mm/42mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- | --- |
| Ring | 18x18 (36x36) | 19x19 (38x38) | 20x20 (40x40) | 21x21 (42x42) | 22.5x22.5 (45x45) |
| Simple | 26x26 (52x52) | 29x29 (58x58) | 30.5x30.5 (61x61) | 32x32 (64x64) | 34.5x34.5 (69x69) |
| Stack | 26x14 (52x28) | 29x15 (58x30) | 30.5x16 (61x32) | 32x17 (64x34) | 34.5x18 (69x36) |

Modular large (up to three rows; Columns / Standard body / Table content): 11-32x11 pt (38mm) up to 14.5-44x14.5 pt (45mm/49mm).

Extra large:

| Image | 38mm | 40mm/42mm | 41mm | 44mm | 45mm/49mm |
| --- | --- | --- | --- | --- | --- |
| Ring | 63x63 (126x126) | 66.5x66.5 (133x133) | 70.5x70.5 (141x141) | 73x73 (146x146) | 79x79 (158x158) |
| Simple | 91x91 (182x182) | 101.5x101.5 (203x203) | 107.5x107.5 (215x215) | 112x112 (224x224) | 121x121 (242x242) |
| Stack | 78x42 (156x84) | 87x45 (174x90) | 92x47.5 (184x95) | 96x51 (192x102) | 103.5x53.5 (207x107) |

**Platform deltas:**
- watchOS only. Not supported in iOS, iPadOS, macOS, tvOS, or visionOS.

### Watch faces

**Purpose:** A view people choose as their primary watchOS view and customize with their favorite complications; shareable in watchOS 7 and later.

**Best practices:**
- Help people discover your app by sharing watch faces that feature your complications; ideally support multiple complications and a curated configuration. For some faces you can specify a system accent color, images, or styles. If people add your face without the app installed, the system prompts them to install it.
- Display a preview of each shared face (email it to yourself via the iOS Watch app to get one with an illustrated bezel, or composite a high-fidelity hardware bezel from Apple Design Resources).
- Aim to offer shareable faces for all Apple Watch devices. Faces available on Series 4 and later: California, Chronograph Pro, Gradient, Infograph, Infograph Modular, Meridian, Modular Compact, Solar Dial. Explorer is available on Series 3 (cellular) and later. Offer a similar configuration on a face available on Series 3 and earlier when you use one of these.
- Respond gracefully to an incompatible face: the system sends an error when people try an incompatible face on Series 3 or earlier — offer an alternative compatible configuration instead of showing an error.

Canonical implementations: ClockKit (Sharing an Apple Watch face).

**Platform deltas:**
- watchOS only. Not supported in iOS, iPadOS, macOS, tvOS, or visionOS.

### Home Screen quick actions

**Purpose:** Let people perform app-specific actions directly from the Home Screen by touching and holding an app icon.

**Best practices:**
- Create quick actions for compelling, high-value tasks that don't require opening the app. People expect at least one useful quick action; you can provide a total of four.
- Each quick action has a title, an interface icon (on the left or right depending on the icon's Home Screen position), and an optional subtitle; title/subtitle are left-aligned in left-to-right languages.
- Dynamic quick actions can stay relevant (location, recent activity, time of day, settings) but must change predictably.
- Give a succinct title that communicates the result (e.g. "Directions Home", "New Message"); add a subtitle for context; don't include the app name or extraneous info; keep text short to avoid truncation; account for localization.
- Provide a familiar interface icon — prefer SF Symbols (see Standard icons). If you design your own, use the Quick Action Icon Template in Apple Design Resources for iOS and iPadOS.
- Don't use an emoji in place of a symbol — quick action symbols are monochromatic and adapt in Dark Mode for contrast.

Canonical implementations: UIKit (Add Home Screen quick actions).

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS, tvOS, visionOS, watchOS: Not supported.

### App Clips
*Last changed: 2025-06*

**Purpose:** A lightweight, instantly available version of your app or game that delivers an on-the-go task experience or a demo without requiring a full App Store download.

**Use it when / not when:**
- Use when: the experience is an in-the-moment task over a finite time, or a demo that showcases the full app before purchase/subscription.
- Avoid web views — App Clips use native components for an app-quality experience; if only web components are available, offer a link to your website instead of an App Clip.
- Don't use App Clips solely for marketing; they must provide real value, and don't display ads.

**Best practices:**
- Let people complete a task or demo without installing the full app (a full demo, a finished level, a saved document).
- Focus on essential features; reserve advanced/complex features for the full app.
- Design a linear, focused UI — no tab bars, complex navigation, or settings; minimize screens and entry forms.
- On launch show the most relevant part for the context; include all required assets, omit splash screens, never make people wait.
- Keep the App Clip small so it launches fast (especially on limited bandwidth); reduce code, remove unused assets, avoid downloading extra data.
- Make the App Clip shareable via Messages links, including links to specific points.
- Make payment easy — consider Apple Pay for express checkout. Avoid requiring an account before value; if required, limit info and consider Sign in with Apple.
- After the full app installs it replaces the App Clip; invocations then launch the app. Don't require people to log in again on transition.
- Privacy: App Clips can't perform background operations. Store minimal data and store it securely off-device (the system may remove the App Clip and delete its data between launches). Consider Sign in with Apple and Apple Pay.
- Showcasing the full app: people don't manage App Clips and they don't appear on the Home Screen; the system removes them after inactivity. The App Clip card and system app banner link to the App Store; you can also show an `SKOverlay` to download the full app — pick a natural pause, be nonintrusive, don't use push notifications to prompt installation.
- Notifications: App Clips can schedule/receive notifications for up to 8 hours after launch; request extended permission only if functionality spans more than a day; keep notifications focused and task-related, never purely promotional.
- App Clip card: be informative; prefer photography/graphics over UI screenshots; avoid text in the image; use a 1800x1200 px PNG or JPEG without transparency; title ≤ 30 characters, subtitle ≤ 56 characters (both required); action-button verb is View (media/info/education), Play (games), or Open (all others).
- App Clip Codes are the best discovery method; always use Apple-generated codes (App Store Connect or the App Clip Code Generator CLI). Choose the badge design with the App Clip logo, or a design without it when space is at a premium. Variants: scan-only (camera icon) or NFC-integrated (iPhone icon); use NFC-integrated when physically accessible, scan-only when inaccessible or digital.
- Don't modify generated codes (no filters, glows, shadows, gradients, reflections, aspect-ratio changes); place on flat or cylindrical surfaces only (on a cylinder, code width ≤ one-sixth / 60° of circumference); keep flat, unobstructed, upright; ensure good lighting.
- Color: each code uses a foreground, a background, and a third generated color; choose default pairs or custom colors with enough contrast (tools won't generate a poor-contrast code).
- Use clear call-to-action messaging next to codes, especially without the logo.

Canonical implementations: App Clip (framework); `SKOverlay` (StoreKit); App Store Connect / App Clip Code Generator CLI; Apple Pay; Sign in with Apple.

**Specs:**

App Clip Code minimum sizes:

| Type | Minimum size |
| --- | --- |
| Printed communications | Diameter ≥ 3/4 inch (1.9 cm) |
| Digital communications | ≥ 256×256 px; PNG or SVG |
| NFC-integrated | Embedded NFC tag ≥ 35 mm diameter (or equivalent); e.g. a 35 mm tag → printed code ≥ 1.37 inch (3.48 cm) diameter |

App Clip card image: 1800x1200 px PNG/JPEG, no transparency. Card title ≤ 30 chars; subtitle ≤ 56 chars.

Scanning ratios: distance-to-code-size ≤ 20:1; prefer 10:1 (e.g. scanned from 40 in / 101 cm → ≥ 4 in / 10.16 cm diameter). When near a QR or other code, size the App Clip Code at least as large. Clear space around a code = the space between the center glyph and the circular code.

Printing: matte finishes, non-textured; avoid shine/gloss/reflective/holographic; UV-resistant outdoors; flexographic (pro) or inkjet (desktop). Rasterize SVG at ≥ 600 ppi; print at ≥ 300 dpi. Convert sRGB → CMYK with relative colorimetric (media-relative) intent; Generic CMYK ICC profile (CMYK printers) or Gracol 2013 ICC profile (CMYKOV printers); color tolerance CIELab Delta E of 2.5. Grayscale-only printers: generate grayscale codes. NFC tags: Type 5, ≥ 35 mm diameter.

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS, tvOS, visionOS, watchOS: Not supported.

### iMessage apps and stickers
*Last changed: 2023-05*

**Purpose:** An iMessage app helps people share content, collaborate, and play games within a Messages conversation; stickers are images people use to decorate a conversation (and both appear in Messages and FaceTime effects).

**Best practices:**
- Prefer one primary experience per iMessage app; create a separate app for each distinct type of functionality or content collection.
- Consider surfacing shareable content from your iOS/iPadOS app (a shopping list, an itinerary) or a simple collaborative task.
- Present essential features in the compact view (appears below the transcript, roughly the keyboard's size); reserve additional content for the expanded view. Generally let people edit text only in the expanded view so content stays visible.
- Create stickers that are expressive, inclusive, and versatile — legible against varied backgrounds and when rotated/scaled; use transparency to integrate with text, photos, and other stickers.
- Provide a localized alternative description per sticker for VoiceOver.
- Pick one sticker size and prepare all stickers at that size — don't mix sizes within a pack. The system generates @2x and @1x by downscaling the @3x images at runtime (`MSStickerSize`).

**Specs:**

iMessage app / sticker pack icon sizes (square-cornered; system rounds the corners):

| Usage | @2x (px) | @3x (px) |
| --- | --- | --- |
| Messages, notifications | 148x110 | – |
| Messages, notifications | 143x100 | – |
| Messages, notifications | 120x90 | 180x135 |
| Messages, notifications | 64x48 | 96x72 |
| Messages, notifications | 54x40 | 81x60 |
| Settings | 58x58 | 87x87 |
| App Store | 1024x1024 | 1024x1024 |

Sticker @3x dimensions (system generates @2x / @1x by downscaling):

| Sticker size | @3x dimensions (px) |
| --- | --- |
| Small | 300x300 |
| Regular | 408x408 |
| Large | 618x618 |

Sticker file size ≤ 500 KB. Supported formats: PNG (8-bit transparency, no animation), APNG (8-bit transparency, animated), GIF (single-color transparency, animated), JPEG (no transparency, no animation).

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS, tvOS, visionOS, watchOS: Not supported.
