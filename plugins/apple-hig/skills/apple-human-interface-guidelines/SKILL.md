---
name: apple-human-interface-guidelines
description: 'Use whenever the user is designing, building, or reviewing UI for any Apple platform (iOS, iPadOS, macOS, tvOS, visionOS, watchOS): choosing components (tab bar vs sidebar, sheet vs popover), layout, navigation, color, Dark Mode, typography, SF Symbols, Liquid Glass, motion, haptics, accessibility, or wanting an app to "feel native" — even when "HIG" is never said. Includes hard specs and per-platform deltas. For App Review compliance use apple-app-store-best-practices; for submission mechanics, app-store-connect-submission; for screenshot specs, apple-app-store-screenshots.'
---

# Apple Human Interface Guidelines

*Last synced with Apple HIG: 2026-07-17*

Distillation of the complete [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines) — every Foundations, Patterns, Components, Inputs, and Technologies page, across all six platforms — compressed to the load-bearing guidance: what each element is for, when to use it over its alternatives, Apple's best practices as imperatives, the hard numbers, and how behavior differs per platform.

## Core Design Principles

Apple reintroduced a unified set of **eight design principles** (June 2026) that guide every Apple-platform decision. They live in full in [`references/foundations-ux.md`](references/foundations-ux.md) (Design principles); the essence:

- **Purpose** — make something meaningful; identify what matters most to the people you're designing for and make that great.
- **Agency** — let people do things their own way; stay out of the way, and make mistakes easy to recover from.
- **Responsibility** — act in people's best interest; be transparent about what the product does, and keep their data safe.
- **Familiarity** — build on what people already know; keep visuals, interactions, and feedback consistent.
- **Flexibility** — adapt to diverse contexts, abilities, and inputs; treat accessibility as a priority from the start.
- **Simplicity** — be clear and direct; include just what's necessary and establish a clear hierarchy.
- **Craft** — care about every detail; sweat quality, iterate, and keep the work current with the platform.
- **Delight** — make it human; create defining moments without letting decoration crowd out the core purpose.

(These supersede the older Clarity / Deference / Depth themes, which Apple no longer lists as its design principles.)

**The Liquid Glass era.** Apple's current system material is Liquid Glass: a dynamic, translucent material that reflects and refracts surrounding content while adapting to context. Let system components adopt it rather than recreating it; pair it with semantic colors and SF Symbols so the system can adapt appearance automatically. Don't apply heavy custom backgrounds to controls that the system already renders with Liquid Glass — that fights the material and dates the app instantly.

## Identify the Platform First

The same component differs meaningfully across platforms — a button on watchOS is full-width and capsule-shaped; on visionOS it gains gaze hover effects; on macOS it participates in keyboard focus rings. Before answering, identify which platform(s) the question targets. If unspecified, ask — or assume iOS and say so. For platform-wide conventions (window model, focus model, input idioms), load the matching `platform-*.md`; for a specific component, load its `components-*.md` cluster, which carries the per-platform deltas inline.

## Reference Files

Load only the rows the question touches — usually a single file. Each reference is a distilled cluster of related HIG pages with per-platform deltas inline.

| Asking about… | Read |
|---|---|
| Color, Dark Mode, materials / Liquid Glass, typography, icons, images, SF Symbols, branding | `references/foundations-visual.md` |
| Design principles, accessibility, inclusion, layout / margins / safe areas, motion, writing style, pointing devices | `references/foundations-ux.md` |
| iOS or iPadOS platform-wide conventions (multitasking, pointer, idioms) | `references/platform-ios-ipados.md` |
| macOS platform-wide conventions (menu bar, windows, panels) | `references/platform-macos.md` |
| tvOS platform-wide conventions (focus engine, remote) | `references/platform-tvos.md` |
| visionOS platform-wide conventions (spatial layout, ornaments, immersion) | `references/platform-visionos.md` |
| watchOS platform-wide conventions (Digital Crown, glanceability) | `references/platform-watchos.md` |
| Navigation structure, modality, onboarding, launching, going full screen, multitasking patterns | `references/patterns-navigation.md` |
| Adaptive layout, right-to-left, drag and drop, loading, collaboration, offering help | `references/patterns-layout-presentation.md` |
| Notifications, Live Activities, ratings and reviews, privacy prompts, feedback patterns | `references/patterns-status-feedback.md` |
| Search, settings, account management | `references/patterns-search.md` |
| Tab bars, sidebars, navigation bars, toolbars, segmented controls, path controls | `references/components-navigation-bars.md` |
| Lists and tables, collections, split views, scroll views, charts, boxes, lockups | `references/components-content-views.md` |
| Buttons, menus, context menus, pull-down / pop-up buttons, edit menus, action sheets, activity views | `references/components-menus-actions.md` |
| Text fields, text views, pickers, sliders, steppers, toggles, color wells, combo boxes | `references/components-selection-input.md` |
| Sheets, popovers, alerts, panels, windows | `references/components-presentation.md` |
| Progress indicators, activity rings, gauges, labels, badges | `references/components-status-indicators.md` |
| Widgets, controls (Control Center), complications, watch faces, App Clips, app icons, Home Screen quick actions | `references/components-system-experiences.md` |
| Gestures, keyboards, Digital Crown, Apple Pencil, game controllers, remotes, eyes / spatial input, haptics, focus and selection | `references/inputs.md` |
| Apple Pay, In-App Purchase design, Sign in with Apple, Wallet, Tap to Pay | `references/technologies-commerce-id.md` |
| Siri, App Shortcuts, Snippets, Maps, CarPlay, Game Center, designing for games, iCloud, NFC, Nearby Interactions, printing, VoiceOver, machine-learning / generative-AI surfaces | `references/technologies-system-services.md` |
| HealthKit, CareKit, ResearchKit, Workouts, HomeKit, audio / video playback, AirPlay, SharePlay, Live Photos, photo editing, ShazamKit, augmented reality | `references/technologies-health-media.md` |
| "Which component should I use?" — comparing confusable components | `references/decision-helpers.md` |
| "Is X available on platform Y?" — capability coverage across the six platforms | `references/cross-platform-matrix.md` |

For a whole-screen design review, load the relevant `components-*` cluster(s), the target `platform-*.md`, and `foundations-ux.md` (accessibility and layout always apply) — not the entire corpus.

## Design Review Workflow

When asked to review a screen or flow rather than answer a single question:

1. Identify the target platform(s) and the components in play.
2. Load the matching component cluster(s), the platform digest, and `foundations-ux.md`.
3. Check each component against its best-practices bullets and specs; verify accessibility basics (Dynamic Type, contrast, tap targets, VoiceOver labels) and layout (safe areas, margins).
4. Where a component choice looks wrong for the job, consult `decision-helpers.md` and propose the alternative with the HIG reasoning.
5. Report findings grouped by severity, each citing the HIG topic it comes from (e.g., "Buttons — tap target below 44×44 pt").
