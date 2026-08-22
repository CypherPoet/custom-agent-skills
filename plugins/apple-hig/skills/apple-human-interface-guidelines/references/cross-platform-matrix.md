# Cross-Platform Availability Matrix

> Source: Apple Human Interface Guidelines (derived from the per-platform notes in this skill's distilled references)
> Last synced: 2026-06-16

Availability of components, inputs, and technologies across the six Apple platforms, derived from each entry's stated platform support. Legend: **Yes** = explicitly supported / has guidance; **No** = the reference states "Not supported"; **—** = the reference doesn't state support either way (check the component reference). When in doubt, open the linked reference.

## Table of Contents

| Section | Covers |
|---|---|
| [Components — Navigation & Bars](#components--navigation--bars) | Platform support for tab bars, sidebars, tab views, toolbars, segmented controls, path controls, and page controls |
| [Components — Content Views](#components--content-views) | Platform support for lists, collections, split and scroll views, macOS-only views, boxes, images, web views, lockups, and charts |
| [Components — Selection & Input](#components--selection--input) | Platform support for text entry, pickers, sliders, steppers, toggles, disclosure controls, color wells, and platform-specific fields |
| [Components — Presentation](#components--presentation) | Platform support for sheets, popovers, alerts, panels, and windows |
| [Components — Status & Indicators](#components--status--indicators) | Platform support for progress indicators, gauges, activity rings, rating indicators, and labels |
| [Components — Menus & Actions](#components--menus--actions) | Platform support for buttons, menus, contextual actions, action sheets, and activity views |
| [Components — System Experiences](#components--system-experiences) | Platform support for app icons, widgets, controls, complications, watch faces, quick actions, App Clips, and iMessage extensions |
| [Inputs](#inputs) | Cross-platform support for focus, keyboards, gestures, haptics, hardware controls, and sensors |
| [Technologies](#technologies) | Platform support for commerce and identity, Siri and AI, system services, games, accessibility, media, health, home, and augmented reality |

## Components — Navigation & Bars

Source: [components-navigation-bars.md](components-navigation-bars.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Tab bars | Yes | Yes | Yes | Yes | Yes | No |
| Sidebars | Yes | Yes | Yes | Yes | Yes | No |
| Tab views | No | No | Yes | No | No | Yes |
| Toolbars | Yes | Yes | Yes | Yes | Yes | Yes |
| Segmented controls | Yes | Yes | Yes | Yes | Yes | No |
| Path controls | No | No | Yes | No | No | No |
| Page controls | Yes | Yes | No | Yes | Yes | Yes |

Notes:
- **Tab views** are macOS/AppKit; iOS/iPadOS/tvOS/visionOS are "Not supported," while watchOS displays them as page controls (`TabView`).
- **Page controls** on visionOS are present (represent and indicate the current page) but people don't interact with them; macOS is "Not supported."
- **Path controls** are macOS only.

## Components — Content Views

Source: [components-content-views.md](components-content-views.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Lists and tables | Yes | Yes | Yes | Yes | — | Yes |
| Collections | Yes | Yes | Yes | Yes | Yes | No |
| Split views | Yes | Yes | Yes | Yes | Yes | Yes |
| Scroll views | Yes | Yes | Yes | Yes | Yes | Yes |
| Outline views | No | No | Yes | No | No | No |
| Column views | No | No | Yes | No | No | No |
| Boxes | Yes | Yes | Yes | No | Yes | No |
| Image views | Yes | Yes | Yes | Yes | Yes | Yes |
| Web views | Yes | Yes | Yes | No | Yes | No |
| Lockups | No | No | No | Yes | No | No |
| Charts | Yes | Yes | Yes | Yes | Yes | Yes |
| Charting data | Yes | Yes | Yes | Yes | Yes | Yes |

Notes:
- **Lists and tables** has per-platform deltas for iOS/iPadOS/visionOS, macOS, tvOS, and watchOS; visionOS appears only in a shared "iOS/iPadOS/visionOS" delta about info buttons (no standalone support statement), so it's left "—".
- **Outline views** and **Column views** are macOS only.
- **Boxes** are "Not supported" in tvOS/watchOS; visionOS has "No additional considerations."
- **Lockups** are a tvOS component, "Not supported" on the other five platforms.

## Components — Selection & Input

Source: [components-selection-input.md](components-selection-input.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Entering data | Yes | Yes | Yes | Yes | Yes | Yes |
| Text fields | Yes | Yes | Yes | Yes | Yes | Yes |
| Text views | Yes | Yes | Yes | Yes | Yes | Yes |
| Combo boxes | No | No | Yes | No | No | No |
| Token fields | No | No | Yes | No | No | No |
| Pickers | Yes | Yes | Yes | Yes | Yes | Yes |
| Digit entry views | No | No | No | Yes | No | No |
| Sliders | Yes | Yes | Yes | No | Yes | Yes |
| Steppers | Yes | Yes | Yes | No | Yes | No |
| Toggles | Yes | Yes | Yes | Yes | Yes | Yes |
| Disclosure controls | Yes | Yes | Yes | No | Yes | No |
| Color wells | Yes | Yes | Yes | No | Yes | No |
| Image wells | No | No | Yes | No | No | No |

Notes:
- **Combo boxes**, **Token fields**, and **Image wells** are macOS only.
- **Digit entry views** are tvOS only.
- **Sliders** are "Not supported in tvOS"; all other platforms have per-platform guidance.
- **Steppers** are "Not supported in watchOS or tvOS."
- **Disclosure controls** and **Color wells** are available on macOS / iOS / iPadOS / visionOS and "Not supported in tvOS or watchOS."

## Components — Presentation

Source: [components-presentation.md](components-presentation.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Sheets | Yes | Yes | Yes | Yes | Yes | Yes |
| Popovers | Yes | Yes | Yes | No | Yes | No |
| Alerts | Yes | Yes | Yes | Yes | Yes | Yes |
| Panels | No | No | Yes | No | No | No |
| Windows | No | Yes | Yes | No | Yes | No |

Notes:
- **Popovers** adapt to a full-screen sheet in a compact iOS environment; reserve them for wide views. "Not supported" in tvOS and watchOS.
- **Panels** are a macOS component; "Not supported" in iOS/iPadOS/tvOS/visionOS/watchOS.
- **Windows** has explicit "Not supported" for iOS, tvOS, and watchOS; iPadOS/macOS/visionOS have per-platform guidance.

## Components — Status & Indicators

Source: [components-status-indicators.md](components-status-indicators.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Progress indicators | Yes | Yes | Yes | Yes | Yes | Yes |
| Gauges | Yes | Yes | Yes | No | Yes | Yes |
| Activity rings | Yes | Yes | No | No | No | Yes |
| Rating indicators | No | No | Yes | No | No | No |
| Labels | Yes | Yes | Yes | Yes | Yes | Yes |

Notes:
- **Gauges** are "Not supported in tvOS"; macOS adds a level indicator.
- **Activity rings** are "Not supported" in macOS, tvOS, and visionOS; iOS shows three rings with a paired Apple Watch (Move-only without one).
- **Rating indicators** are macOS only ("Not supported" stated for iOS, iPadOS, tvOS, visionOS, watchOS).

## Components — Menus & Actions

Source: [components-menus-actions.md](components-menus-actions.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Buttons | Yes | Yes | Yes | Yes | Yes | Yes |
| Menus | Yes | Yes | Yes | Yes | Yes | Yes |
| Context menus | Yes | Yes | Yes | Yes | Yes | No |
| Pull-down buttons | Yes | Yes | Yes | No | Yes | No |
| Pop-up buttons | Yes | Yes | Yes | No | Yes | No |
| Edit menus | Yes | Yes | Yes | No | Yes | No |
| Action sheets | Yes | Yes | Yes | Yes | No | Yes |
| Activity views | Yes | Yes | Yes | No | Yes | No |

Notes:
- **Context menus** have deltas for iOS/iPadOS, macOS, visionOS, and tvOS; "Not supported in watchOS."
- **Pull-down buttons** and **Pop-up buttons** are "Not supported in tvOS or watchOS."
- **Edit menus** are "Not supported in tvOS or watchOS"; visionOS opens them via pinch and hold.
- **Action sheets** are "Not supported in visionOS"; macOS/tvOS have "No additional considerations."
- **Activity views** are "Not supported in tvOS or watchOS"; macOS has no activity view but share/action extensions still work.

## Components — System Experiences

Source: [components-system-experiences.md](components-system-experiences.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| App icons | Yes | Yes | Yes | Yes | Yes | Yes |
| Widgets | Yes | Yes | Yes | No | Yes | Yes |
| Controls | Yes | Yes | Yes | No | No | No |
| Complications | No | No | No | No | No | Yes |
| Watch faces | No | No | No | No | No | Yes |
| Home Screen quick actions | Yes | Yes | No | No | No | No |
| App Clips | Yes | Yes | No | No | No | No |
| iMessage apps and stickers | Yes | Yes | No | No | No | No |

Notes:
- **Widgets** are "Not supported" in tvOS; visionOS, watchOS, and Mac each have dedicated guidance.
- **Controls** are available on iOS/iPadOS/macOS; "Not supported" in watchOS, tvOS, visionOS.
- **Complications** and **Watch faces** are watchOS only ("Not supported in iOS, iPadOS, macOS, tvOS, or visionOS").
- **Home Screen quick actions**, **App Clips**, and **iMessage apps and stickers** are iOS/iPadOS only ("Not supported" on macOS, tvOS, visionOS, watchOS).

## Inputs

Source: [inputs.md](inputs.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Gestures | Yes | Yes | Yes | Yes | Yes | Yes |
| Focus and selection | No | Yes | Yes | Yes | Yes | No |
| Keyboards | Yes | Yes | Yes | Yes | Yes | No |
| Virtual keyboards | Yes | Yes | No | Yes | Yes | Yes |
| Playing haptics | Yes | — | Yes | — | — | Yes |
| Digital Crown | No | No | No | No | Yes | Yes |
| Apple Pencil and Scribble | No | Yes | No | No | No | No |
| Camera Control | Yes | No | No | No | No | No |
| Action button | Yes | No | No | No | No | Yes |
| Game controls | Yes | Yes | Yes | Yes | Yes | No |
| Remotes | No | No | No | Yes | No | No |
| Eyes | No | No | No | No | Yes | No |
| Gyroscope and accelerometer | Yes | Yes | Yes | Yes | Yes | Yes |

Notes:
- **Focus and selection**: iOS and watchOS are explicitly "Not supported"; iPadOS, tvOS, and visionOS have focus-system guidance. macOS is referenced (full keyboard access) within the iPadOS/macOS best practice, so marked Yes.
- **Keyboards**: "Not supported" in watchOS; iOS/iPadOS/macOS/tvOS have "No additional considerations" and visionOS has its own guidance.
- **Virtual keyboards**: macOS is "Not supported"; iOS/iPadOS, tvOS, visionOS, and watchOS each have guidance.
- **Playing haptics**: the entry gives per-platform deltas only for iOS, macOS, and watchOS (and Magic Trackpad on Mac); iPadOS/tvOS/visionOS aren't stated as supported or not, so they're "—".
- **Digital Crown** is for Apple Vision Pro and Apple Watch; "Not supported" in iOS/iPadOS/macOS/tvOS.
- **Apple Pencil and Scribble**: the deltas list iOS/macOS/tvOS/visionOS/watchOS as "Not supported," leaving iPadOS as the supported platform (Apple Pencil works on iPad).
- **Camera Control** is iPhone-only (iOS); "Not supported" in iPadOS/macOS/watchOS/tvOS/visionOS.
- **Action button**: "Not supported" in iPadOS/macOS/tvOS/visionOS; supported on iOS and watchOS.
- **Game controls**: iOS/iPadOS/macOS/tvOS have "No additional considerations"; visionOS has guidance; watchOS is "Not supported" (physical game controllers).
- **Remotes** (Siri Remote) is tvOS only; "Not supported" in iOS/iPadOS/macOS/visionOS/watchOS.
- **Eyes** is visionOS only; "Not supported" in iOS/iPadOS/macOS/tvOS/watchOS.
- **Gyroscope and accelerometer**: all six platforms have "No additional considerations" (the availability note also calls out iOS/iPadOS/watchOS data and tvOS Siri Remote gyroscope).

## Technologies

Sources: [technologies-commerce-id.md](technologies-commerce-id.md), [technologies-system-services.md](technologies-system-services.md), [technologies-health-media.md](technologies-health-media.md)

| Element | iOS | iPadOS | macOS | tvOS | visionOS | watchOS |
|---|---|---|---|---|---|---|
| Apple Pay | Yes | Yes | Yes | No | Yes | Yes |
| In-app purchase | Yes | Yes | Yes | Yes | Yes | Yes |
| Wallet | Yes | Yes | Yes | No | Yes | Yes |
| Sign in with Apple | Yes | Yes | Yes | Yes | Yes | Yes |
| Tap to Pay on iPhone | Yes | No | No | No | No | No |
| ID Verifier | Yes | No | No | No | No | No |
| Siri | — | — | — | — | — | — |
| App Shortcuts | Yes | Yes | Yes | No | Yes | Yes |
| Snippets | Yes | Yes | Yes | No | No | No |
| Generative AI | — | — | — | — | — | — |
| Machine learning | — | — | — | — | — | — |
| Maps | Yes | Yes | Yes | Yes | Yes | Yes |
| Nearby interactions | Yes | Yes | No | No | No | Yes |
| NFC | Yes | Yes | No | No | No | No |
| CarPlay | Yes | No | No | No | No | No |
| Game Center | Yes | Yes | Yes | Yes | Yes | Yes |
| Designing for games | Yes | Yes | Yes | Yes | Yes | Yes |
| iCloud | Yes | Yes | Yes | Yes | Yes | Yes |
| Printing | Yes | Yes | Yes | No | Yes | No |
| VoiceOver | Yes | Yes | Yes | Yes | Yes | Yes |
| Playing audio | Yes | Yes | Yes | Yes | Yes | Yes |
| Playing video | Yes | Yes | Yes | Yes | Yes | Yes |
| AirPlay | Yes | Yes | Yes | Yes | Yes | No |
| SharePlay | Yes | Yes | Yes | Yes | Yes | No |
| Live Photos | Yes | Yes | Yes | Yes | Yes | No |
| Photo editing | Yes | Yes | Yes | No | No | No |
| ShazamKit | Yes | Yes | Yes | Yes | Yes | Yes |
| HealthKit | Yes | Yes | No | No | No | Yes |
| CareKit | Yes | Yes | No | No | No | No |
| ResearchKit | Yes | Yes | No | No | No | No |
| Workouts | Yes | Yes | No | No | No | Yes |
| HomeKit | Yes | Yes | Yes | Yes | Yes | Yes |
| Augmented reality | Yes | Yes | No | No | Yes | No |

Notes:
- **Apple Pay** and **Wallet** have "No additional considerations" on iOS/iPadOS/macOS/visionOS/watchOS and are "Not supported" in tvOS.
- **Tap to Pay on iPhone** and **ID Verifier** are iOS only ("Not supported" in iPadOS/macOS/tvOS/visionOS/watchOS).
- **Siri**, **Generative AI**, and **Machine learning** state no per-platform support breakdown (Siri has "No platform-specific section"; the other two say "No additional considerations" for all platforms but never assert per-platform availability) — all cells are "—" because the entries don't enumerate explicit support. They read as system-wide topics rather than per-platform components.
- **App Shortcuts**: "Not supported in tvOS"; macOS supports App Intents actions (not App Shortcuts themselves) but the entry still has a macOS delta, so marked Yes; visionOS/watchOS have "No additional considerations."
- **Snippets** has "No additional considerations" for iOS/iPadOS/macOS and is "Not supported in tvOS, visionOS, or watchOS."
- **Nearby interactions**: iOS and watchOS have explicit guidance, iPadOS has "No additional considerations"; "Not supported in macOS, tvOS, or visionOS."
- **NFC** is iOS/iPadOS ("No additional considerations"); "Not supported in macOS, tvOS, visionOS, or watchOS."
- **CarPlay** is iOS only ("Not supported in iPadOS, macOS, tvOS, visionOS, or watchOS").
- **Printing** is supported on iOS/iPadOS/visionOS (and macOS, per its delta); "Not supported in tvOS or watchOS."
- **AirPlay**, **SharePlay**, and **Live Photos** are "Not supported in watchOS"; all others supported.
- **Photo editing** is iOS/iPadOS/macOS; "Not supported in tvOS/visionOS/watchOS."
- **HealthKit** and **Workouts** are iOS/iPadOS/watchOS; "Not supported in macOS/tvOS/visionOS."
- **CareKit** and **ResearchKit** are iOS/iPadOS; "Not supported in macOS/tvOS/visionOS/watchOS."
- **Augmented reality** is iOS/iPadOS plus visionOS (ARKit with permission); "Not supported in macOS/tvOS/watchOS."
- **Game Center**: iOS/iPadOS/macOS/visionOS have "No additional considerations," tvOS and watchOS have dedicated guidance (watchOS exposes the API but has no system Game Center UI) — all marked Yes.
