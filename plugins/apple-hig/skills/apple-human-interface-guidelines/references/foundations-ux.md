# Foundations — UX

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Foundations pages: Design principles, Accessibility, Inclusion, Layout, Motion, Pointing devices, Writing.

## Table of Contents

| Section | Covers |
|---|---|
| [Design principles](#design-principles) | Purpose, agency, responsibility, familiarity, flexibility, simplicity, craft, and delight as non-rigid decision tools |
| [Accessibility](#accessibility) | Vision, hearing, mobility, speech, and cognitive support; testing and App Store declarations; sizing and contrast; and visionOS comfort |
| [Inclusion](#inclusion) | Respectful language, imagery, gender and disability representation, cultural assumptions, accessibility, internationalization, and localization |
| [Layout](#layout) | Content hierarchy and grouping, adaptive context changes, safe areas and type scaling, device dimensions, and platform-specific layout rules |
| [Motion](#motion) | Purposeful and optional feedback, multimodal alternatives, cancellation, game frame rates, and visionOS and watchOS comfort constraints |
| [Pointing devices](#pointing-devices) | System gestures and unified input, pointer effects and hit regions, custom pointers, modifier behavior, and iPadOS, macOS, and visionOS patterns |
| [Writing](#writing) | Voice and tone, plain inclusive language, action labels, multi-step flows, platform terms, empty states, errors, settings, and text-field guidance |

## Design principles
*Last changed: 2026-06*

**Purpose:** Eight foundational principles that guide design across every Apple platform — tools for weighing competing priorities and making key decisions, not rigid rules. Apple reintroduced this page in June 2026; there's no single right way to apply the principles.

**The eight principles:**
- **Purpose — make something meaningful.** *Create value:* keep a constant orientation toward what makes the product genuinely useful; ask what it's for and whether the design serves that. *Keep focused:* prioritize the most important features and make those truly great. *Find new ways to solve the problem:* investigate existing solutions instead of re-creating them; define what sets the product apart.
- **Agency — let people do things their own way.** *Stay out of the way:* get people directly to the task or content; the best designs are unobtrusive and present when needed. *Give freedom to explore:* don't lock people into specific flows or modes; make guided flows easy to skip or escape. *Help people recover from mistakes:* build in forgiveness so reversing an action or returning to a previous state is easy.
- **Responsibility — act in people's best interest.** *Be transparent about what the product does and why:* give a clear rationale when requesting permission; be clear about what data you collect and how you use it. *Keep information safe:* collect only what the product needs, anticipate misuse, and put protections in place.
- **Familiarity — build on what people know.** *Use concepts people know:* draw on the real world and other software. *Keep visuals and interactions consistent:* apply an established behavior or appearance throughout. *Provide clear feedback:* signal what's happening, show when controls are available, and use system patterns for alerts and choices.
- **Flexibility — adapt to diverse contexts and needs.** *Design for everyone:* treat accessibility as a priority from the start; design inclusively. *Preserve a person's context:* keep content and controls in consistent, predictable positions; use natural animations to ease transitions. *Consider a variety of input methods:* support voice, touch, keyboard, and more. *Approach every platform with intention:* give each supported platform the same level of care.
- **Simplicity — be clear and direct.** *Include just what's necessary:* simplicity isn't minimalism — keep important things close and let others fall away. *Be concise:* choose exactly the words needed for a concept or control. *Establish hierarchy:* prioritize recognizable controls and consistent structure so people know where they are and what comes next.
- **Craft — care about every detail.** *Quality sets the tone:* be deliberate with each decision; strive for stunning visuals, smooth animations, precise wording, thoughtful audio. *Experiment and iterate:* prototype early, discard what doesn't work, test in real-world settings. *Maintain your craft:* shipping isn't the finish line — keep the interface current with the latest platform capabilities and patterns.
- **Delight — make it human.** *Identify the emotion to inspire:* know the feeling you want to evoke and let it shape the design. *Create defining moments:* treat each interaction (even an error message) as a chance to add character. *Don't mistake delight for decoration:* never let delight for its own sake get in the way of the product's core purpose. *Consider the whole:* delight is the sum of intent, focus, and care across the entire experience.

**Platform deltas:**
- All platforms: the principles apply universally; they're decision-making tools rather than platform-specific rules.

## Accessibility
*Last changed: 2025-06*

**Purpose:** Make interfaces intuitive, perceivable, and adaptable so everyone can use your app or game regardless of capability — covering vision, hearing, mobility, speech, and cognitive needs. Audit with Accessibility Inspector; declare support via Accessibility Nutrition Labels in App Store Connect.

**Best practices:**

*Vision*
- Let people enlarge text by at least 200% (140% in watchOS), via Dynamic Type or custom UI.
- Use thicker font weights at small sizes; if using a thin weight, go larger than the recommended size.
- Meet WCAG Level AA contrast (see Specs). If defaults fall short, provide a higher-contrast scheme when Increase Contrast is on; check both light and dark appearances.
- Prefer system-defined colors — they adapt automatically to Increase Contrast and light/dark.
- Never convey information with color alone; add distinct shapes or icons, and consider user-customizable color schemes.
- Describe interface and content for VoiceOver.

*Hearing*
- Don't communicate dialogue or crucial information through audio alone. Choose the right text alternative: captions (text synced live with game cutscenes/clips), subtitles (translated onscreen dialogue for shows/movies), audio descriptions (narration of visual-only info in pauses), transcripts (complete text of audible + visual content for long-form media). Let people customize the text presentation.
- Pair audio cues (chimes, error sounds, game feedback) with matching haptics; in iOS/iPadOS use Music Haptics and audio graphs.
- Augment audio cues with visual indicators pointing toward off-screen content, especially in games and spatial apps.

*Mobility*
- Meet per-platform minimum control sizes (see Specs).
- Treat spacing as important as size: ~12 pt padding around bezeled elements; ~24 pt around the visible edges of bezel-less elements.
- Use the simplest gesture possible for frequent interactions; avoid custom multifinger and multihand gestures.
- Offer onscreen alternatives to every gesture (e.g., a delete button in addition to swipe-to-delete).
- Label elements appropriately so Voice Control works; integrate Siri/Shortcuts for voice-only task automation.
- Test against VoiceOver, AssistiveTouch, Full Keyboard Access, Pointer Control, and Switch Control.

*Speech*
- Support Full Keyboard Access for navigation and interaction; avoid overriding system-defined keyboard shortcuts.
- Support Switch Control (separate hardware, game controllers, or sound-triggered input).

*Cognitive*
- Prefer familiar system gestures over custom ones people must learn.
- Minimize time-boxed UI; prefer explicit dismissal over auto-dismiss timers.
- In games, consider difficulty accommodations: reduced success criteria, adjustable reaction time, control assistance.
- Don't autoplay audio/video without discoverable start/stop controls; consider a global opt-out.
- Respond to the Dim Flashing Lights setting in video playback.
- When Reduce Motion is on: reduce automatic and repetitive animations (zooming, scaling, peripheral motion); tighten animation springs to cut bounce; track animations directly with gestures; avoid animating z-axis depth changes; replace x/y/z transitions with fades; avoid animating into/out of blurs.
- For Assistive Access (iOS/iPadOS): pare to core functionality, one interaction per screen, and confirm twice before hard-to-recover actions like deleting a file.

**Specs:**

Default and minimum sizes for custom type styles:

| Platform | Default type size | Minimum type size |
|---|---|---|
| iOS, iPadOS | 17 pt | 11 pt |
| macOS | 13 pt | 10 pt |
| tvOS | 29 pt | 23 pt |
| visionOS | 17 pt | 12 pt |
| watchOS | 16 pt | 12 pt |

WCAG AA contrast minimums (used by Accessibility Inspector):

| Text size | Text weight | Minimum contrast ratio |
|---|---|---|
| Up to 17 pt | All | 4.5:1 |
| 18 pt | All | 3:1 |
| All | Bold | 3:1 |

Control sizes:

| Platform | Default control size | Minimum control size |
|---|---|---|
| iOS, iPadOS | 44x44 pt | 28x28 pt |
| macOS | 28x28 pt | 20x20 pt |
| tvOS | 66x66 pt | 56x56 pt |
| visionOS | 60x60 pt | 28x28 pt |
| watchOS | 44x44 pt | 28x28 pt |

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/watchOS: no additional considerations.
- visionOS: prioritize comfort — keep elements within the field of view; prefer horizontal layouts over neck-straining vertical ones; don't demand attention in different locations in quick succession; reduce speed/intensity of animated objects in peripheral vision; be gentle with camera and video motion; never anchor content to the wearer's head (feels confining and blocks Pointer Control); minimize large, repetitive gestures.

## Inclusion

**Purpose:** Design respectful experiences that welcome everyone by examining your assumptions about language, imagery, gender, ability, and culture — an inoffensive app isn't automatically an inclusive one.

**Best practices:**
- Review tone from multiple perspectives; be clear, direct, and respectful (an academic tone can read as education-gated).
- Address people directly as "you/your"; avoid "the user/the player"; reserve "we/our" for your company or software.
- Define specialized or technical terms, or replace them with plain language.
- Replace colloquial expressions — they're culture-specific, hard to translate, and some (e.g., "grandfathered in") carry exclusionary origins.
- Consider carefully before using humor; it translates poorly and wears thin on repeat.
- Make the app approachable: clear, platform-consistent interface plus skippable, step-by-step onboarding.
- Avoid unnecessary gender references in copy ("Subscribers can post recipes" over "his or her"); this also eases localization into gendered languages.
- Use nongendered imagery for generic people (SF Symbols `person.crop.circle`, `person.3.fill`, `figure.wave`); let people customize avatars/characters.
- If you must collect gender (health/legal), offer options like nonbinary, self-identify, and decline to state; consider letting people specify pronouns.
- Portray a range of races, body types, ages, and abilities; avoid stereotyped occupations, family structures, and affluence-heavy settings.
- Avoid context-specific assumptions (e.g., security questions about college or cars); base prompts on universal experiences.
- Support accessibility features (VoiceOver, Display Accommodations, captions, Switch Control, Speak Screen); remember each disability is a spectrum and includes temporary and situational forms.
- Use people-first language about disability; never use disability to express a negative quality; learn how communities self-identify.
- Internationalize, then localize; SF Symbols includes language-specific and LTR/RTL glyphs.
- Verify color meanings per locale — the same color signals death in one culture and purity in another.

**Platform deltas:**
- All platforms: no additional considerations.

## Layout
*Last changed: 2025-09*

**Purpose:** Build a consistent, adaptive layout that grounds people in content, respects each platform's safe areas and system features, and survives context changes like rotation, resizing, and text-size shifts.

**Best practices:**
- Group related items with negative space, background shapes, colors, materials, or separators; keep content and controls clearly distinct.
- Give essential information space; move secondary detail to other window areas or additional views.
- Extend backgrounds and scrollable content edge-to-edge; controls and navigation (sidebars, tab bars) float above content — use a background extension view to appear behind them when content doesn't span the window.
- Differentiate controls from content with Liquid Glass; use a scroll edge effect (not a background) to transition between content and control areas.
- Place the most important items near the top and leading side (reading order); account for right-to-left languages.
- Align components to aid scanning; use alignment and indentation to show hierarchy.
- Use progressive disclosure (disclosure controls, partially visible items) to hint at hidden content.
- Space and group controls logically; crowded controls are hard to distinguish.
- Handle common context changes: screen sizes/resolutions/color spaces, portrait/landscape, Dynamic Island and camera controls, external displays/Display Zoom/resizable iPad windows, Dynamic Type, and locale features (RTL, date/time/number formats, font variation, text length).
- Respect system safe areas, margins, and layout guides; safe areas avoid Dynamic Island, camera housings, and bars, and reposition content when sizes change.
- Support Dynamic Type (iOS, iPadOS, tvOS, visionOS, watchOS); use Apple's accessibility plug-in for Unity games.
- Preview on multiple devices, orientations, localizations, and text sizes; test the largest and smallest layouts first.
- Scale (never stretch) artwork when aspect ratio changes; keep important visual content visible.

**Specs:**

tvOS grid layouts (all use 40 pt horizontal spacing, 100 pt minimum vertical spacing):

| Columns | Unfocused content width |
|---|---|
| 2 | 860 pt |
| 3 | 560 pt |
| 4 | 410 pt |
| 5 | 320 pt |
| 6 | 260 pt |
| 7 | 217 pt |
| 8 | 184 pt |
| 9 | 160 pt |

iOS/iPadOS screen dimensions (portrait, grouped by shared size):

| Dimensions | Models |
|---|---|
| 1032x1376 pt (2064x2752 px @2x) | iPad Pro 13" |
| 1024x1366 pt (2048x2732 px @2x) | iPad Pro 12.9", iPad Air 13" |
| 834x1210 pt (1668x2420 px @2x) | iPad Pro 11" 5th–6th gen |
| 834x1194 pt (1668x2388 px @2x) | iPad Pro 11" 1st–4th gen |
| 834x1112 pt (1668x2224 px @2x) | iPad Pro 10.5", iPad Air 10.5" |
| 820x1180 pt (1640x2360 px @2x) | iPad Air 11", iPad Air 10.9", iPad 11" |
| 810x1080 pt (1620x2160 px @2x) | iPad 10.2" |
| 768x1024 pt (1536x2048 px @2x) | iPad Pro 9.7", iPad Air 9.7", iPad 9.7", iPad mini 7.9" |
| 744x1133 pt (1488x2266 px @2x) | iPad mini 8.3" |
| 440x956 pt (1320x2868 px @3x) | iPhone 17 Pro Max, 16 Pro Max |
| 430x932 pt (1290x2796 px @3x) | iPhone 16 Plus, 15 Pro Max, 15 Plus, 14 Pro Max |
| 428x926 pt (1284x2778 px @3x) | iPhone 14 Plus, 13 Pro Max, 12 Pro Max |
| 420x912 pt (1260x2736 px @3x) | iPhone Air |
| 414x896 pt (1242x2688 px @3x) | iPhone 11 Pro Max, XS Max |
| 414x896 pt (828x1792 px @2x) | iPhone 11, XR |
| 414x736 pt (1080x1920 px @3x) | iPhone 8 Plus, 7 Plus, 6s Plus, 6 Plus |
| 402x874 pt (1206x2622 px @3x) | iPhone 17 Pro, 17, 16 Pro |
| 393x852 pt (1179x2556 px @3x) | iPhone 16, 15 Pro, 15, 14 Pro |
| 390x844 pt (1170x2532 px @3x) | iPhone 16e, 14, 13 Pro, 13, 12 Pro, 12 |
| 375x812 pt (1125x2436 px @3x) | iPhone 11 Pro, XS, X |
| 375x667 pt (750x1334 px @2x) | iPhone 8, 7, 6s, 6, SE 4.7" |
| 360x780 pt (1080x2340 px @3x) | iPhone 13 mini, 12 mini |
| 320x568 pt (640x1136 px @2x) | iPhone SE 4", iPod touch 5th gen+ |

iOS/iPadOS size classes (regular = larger screen or landscape; compact = smaller screen or portrait):
- All iPads: regular width x regular height in both orientations.
- All iPhones, portrait: compact width x regular height.
- iPhone landscape: regular width x compact height on Max/Plus models, iPhone Air, iPhone 11, and iPhone XR; compact width x compact height on all other models.

watchOS screen dimensions (pixels):

| Model | Size | W x H px |
|---|---|---|
| Apple Watch Ultra 3 | 49mm | 422x514 |
| Ultra 1–2 | 49mm | 410x502 |
| Series 10, 11 | 46mm | 416x496 |
| Series 10, 11 | 42mm | 374x446 |
| Series 7–9 | 45mm | 396x484 |
| Series 7–9 | 41mm | 352x430 |
| Series 4–6, SE (all) | 44mm | 368x448 |
| Series 4–6, SE (all) | 40mm | 324x394 |
| Series 1–3 | 42mm | 312x390 |
| Series 1–3 | 38mm | 272x340 |

**Platform deltas:**
- iOS: aim to support both orientations; landscape-only apps must work with either rotation direction (don't tell people to rotate). Prefer full-bleed games that accommodate corner radius, sensor housing, and Dynamic Island, optionally offering letterbox/pillarbox. Avoid full-width buttons — inset from screen edges per system margins; if full-width is necessary, harmonize with hardware curvature and safe areas. Hide the status bar only for in-depth experiences (games, media).
- iPadOS: windows resize freely down to a minimum size — design for full screen first and defer switching to a compact view as long as possible; hide tertiary columns (e.g., inspectors) as views narrow. Test at system-provided sizes (halves, thirds, quadrants) and minimize jarring changes at min/max sizes. Consider a convertible tab bar (`sidebarAdaptable`) that switches between sidebar and tab bar.
- macOS: avoid controls or critical information at the bottom of a window (people push it offscreen); avoid displaying content within the camera housing at the top edge.
- tvOS: the same interface renders on every TV size — test across sizes. Inset primary content 60 pt from top/bottom and 80 pt from sides; allow only deliberate offscreen flow outside this zone. Pad focusable elements (they grow when focused); add extra vertical spacing for titled rows; keep spacing consistent; keep partially hidden offscreen content symmetrical on both sides.
- visionOS: consider centering the most important content and controls. Keep content within window bounds — system window controls sit just outside in the XY plane. Use ornaments for controls that don't belong in the window. Space interactive components so button centers are at least 60 pt apart, leaving room for the hover effect.
- watchOS: extend content edge-to-edge (the bezel supplies padding); minimize padding between elements. Show at most three glyph buttons or two text buttons per row; prefer full-width text buttons. Support autorotation in views people might show others (e.g., QR codes).

## Motion
*Last changed: 2025-09*

**Purpose:** Use motion to convey status, give feedback, and enrich the experience without distracting or causing discomfort — system components animate automatically (Liquid Glass responds more emphatically to touch, more subdued to trackpad), so these rules govern custom motion.

**Best practices:**
- Add motion purposefully; gratuitous animation distracts and can cause physical discomfort.
- Make motion optional — never the only channel for important information; supplement with haptics and audio.
- Make feedback motion realistic and matched to gestures (a view revealed by sliding down shouldn't dismiss by sliding sideways).
- Keep feedback animations brief and precise; succinct beats prominent.
- In apps, avoid adding motion to frequent UI interactions — the system already animates standard elements.
- Let people cancel or skip animations; don't make them wait, especially repeatedly.
- Consider animated symbols (SF Symbols 5+) where they make sense.
- Games: target a consistent 30–60 fps by default on each platform, using device graphics capabilities without requiring settings changes; let people customize visuals for performance or battery (e.g., power modes when external power is detected).

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS: no additional considerations.
- visionOS: avoid motion at the edges of the field of view — peripheral motion distracts and can make people feel they're moving; if needed, match the object's brightness to surrounding content. For large objects that occlude passthrough, increase translucency or lower contrast so movement doesn't read as self-motion. Fade objects out/in instead of animating relocation when the movement carries no meaning. Avoid rotating a virtual world — use instantaneous directional changes during a quick fade. Give people a stationary frame of reference. Avoid sustained oscillation, especially near 0.2 Hz; keep amplitude low and content translucent if oscillation is required.
- watchOS: prefer SwiftUI for motion; use `WKInterfaceImage` for WatchKit animations and image sequences.

## Pointing devices
*Last changed: 2023-06*

**Purpose:** Support trackpad and mouse input consistently with the system — on Mac as the primary input alongside a keyboard, on iPad and Apple Vision Pro as an addition to (not replacement for) touch, eyes, and gestures.

**Best practices:**
- Respond to mouse/trackpad gestures the way the system does; people expect gestures to work identically across apps.
- Never redefine systemwide trackpad gestures (e.g., revealing the Dock or Mission Control), even in games.
- Provide one consistent experience whether people use gestures, eyes, a pointer, or a keyboard.
- Let the pointer reveal and hide auto-minimizing controls (e.g., hover to reveal a minimized toolbar or video playback controls).
- Keep modifier-key behavior identical across touch and pointer (e.g., Option-drag duplicates either way).

**Platform deltas:**
- iOS: no additional considerations. tvOS/watchOS: not supported.
- iPadOS:
  - Pointer adapts to context (circle by default, I-beam over text). Support band selection in custom multi-select views (`UIBandSelectionInteraction`); standard non-list collection views get it free.
  - Distinguish pointer from finger input only when it adds value (e.g., precise seek in a scrubber).
  - Use system content effects by design intent: **highlight** (translucent rounded-rect pointer + parallax) for small elements with transparent backgrounds — default for bar buttons, tab bars, segmented controls, edit menus; **lift** (scale + shadow + specular highlight, pointer fades out) for small elements with opaque backgrounds — default for app icons and Control Center buttons; **hover** (custom scale/tint/shadow, pointer keeps its shape) for large elements.
  - Prefer system pointer appearances for standard buttons and text-entry areas.
  - Hit regions: add ~12 pt padding around bezeled elements, ~24 pt around bezel-less ones; make adjacent bar-button hit regions contiguous so the pointer doesn't flicker back to default between them; specify the corner radius for nonstandard lift-effect shapes (e.g., circles).
  - Magnetism pulls the pointer toward lift/highlight elements and text-entry areas (not hover elements — they'd feel jarring).
  - Custom pointers: keep shapes simple and self-evident; useful annotations are fine (e.g., X/Y values, width x height while resizing); never display instructional text. Pointer accessories: use clear, simple images; use accessory transitions to signal state changes (e.g., `plus` → `circle.slash` when add becomes unavailable).
  - Custom hover effects: reserve scaling for elements with room to grow (not table rows); use tint without scale/shadow in tight spaces; never use shadow without scale.
- macOS:
  - Standard gestures (people can customize them) — mouse and trackpad: primary click (select/activate), secondary click (contextual menu), scrolling, smart zoom, swipe between pages, swipe between full-screen apps, Mission Control. Trackpad only: lookup/data detectors (force click or three-finger tap), tap to click, force click (Quick Look/lookup, pressure-sensitive controls), pinch zoom, rotate, Notification Center (edge swipe), App Exposé (three/four-finger swipe down), Launchpad (pinch thumb + three fingers), Show Desktop (spread thumb + three fingers).
  - Use standard pointer styles to communicate state: arrow (standard); horizontal/vertical I-beam (text selection/insertion); pointing hand (link); open/closed hand (content drag possible/in progress); crosshair (precise rectangular selection); contextual menu (Control key held); drag copy (Option-drag duplicates); drag link (Option-Command-drag creates alias); disappearing item (drop removes the dragged item); operation not allowed (can't drop here); resize up/down/left/right/left-right/up-down.
- visionOS: where the person looks determines pointer context — the system focuses the element under the pointer and transitions between windows automatically; no app work needed. The pointer hides while people gesture on a trackpad/mouse and reappears where they're looking when moved.

## Writing
*Last changed: 2025-12*

**Purpose:** Treat interface text as core UX — establish a voice, adapt tone to context, and write copy that is clear, action-oriented, and inclusive.

**Best practices:**
- Determine your app's voice from your audience's vocabulary; keep a list of common terms and use them consistently.
- Match tone to the situation (serious and direct for a fall alert; light and congratulatory for a fitness streak).
- Be clear: choose easily understood words, cut every word that isn't needed, read copy aloud when in doubt.
- Write for everyone: plain language, no jargon or gendered terms, with accessibility and localization in mind.
- Put the most important information first on each screen; break multiple ideas across screens.
- Be action-oriented: use verbs for button labels; prefer "Send" over clever labels like "Let's do it!"; for links use descriptive phrases, never "Click here" (critical for screen readers).
- Build consistent language patterns and capitalization rules per UI element type (title case reads formal, sentence case casual); apply each consistently app-wide.
- In multi-step flows: open with "Get Started," advance with one consistent term ("Continue" or "Next"), close with "Done."
- Use possessive pronouns sparingly ("Favorites," not "Your Favorites") and never switch perspectives; avoid "we" entirely — "Unable to load content" beats "We're having trouble loading this content."
- Use device-correct interaction terms (tap, not click, on iPhone/iPad); be brief on small screens and on TVs (large text, shared viewing — consider who you're addressing).
- Give empty states clear next steps with a button or link; don't put crucial information in a state that disappears.
- Write error messages close to the problem, without blame, stating the fix: "Choose a password with at least 8 characters," not "That password is too short." Skip insincere interjections ("oops!", "uh-oh"). If language can't fix a common error, rethink the interaction.
- Label settings practically; describe only what the on state does (people infer the off state). Link directly to a setting rather than describing its location.
- In text fields, label every field and use hint text to show the format ("name@example.com", "Your name"); show errors next to the field and instruct rather than scold — "Use only letters for your name," never "Invalid name."

**Platform deltas:**
- All platforms: no additional considerations.
