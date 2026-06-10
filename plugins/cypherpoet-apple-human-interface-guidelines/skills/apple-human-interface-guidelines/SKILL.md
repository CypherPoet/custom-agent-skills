---
name: apple-human-interface-guidelines
description: >
  Use this skill whenever the user is designing, building, or reviewing UI for any
  Apple platform (iOS, iPadOS, macOS, tvOS, visionOS, watchOS) — choosing or
  questioning a component (tab bar, sidebar, sheet, popover, menu, toolbar, picker,
  widget, complication…), asking about layout, navigation, color, Dark Mode,
  typography, SF Symbols, Liquid Glass, materials, motion, haptics, gestures,
  accessibility, or Dynamic Type, or wanting an app to "feel native", "look like a
  real iOS app", or "follow Apple's design guidelines". Trigger for concrete
  questions like "tab bar or sidebar?", "minimum tap target size?", "sheet or
  popover for this?", "standard margins on iPhone?", and for design reviews of
  Apple-platform screens — even when the user never says "HIG" or "Human Interface
  Guidelines". Distills the complete Apple HIG: per-component best practices, hard
  specs (sizes, type styles, color tokens), per-platform deltas, and
  choose-the-right-component decision tables. For App Review compliance or
  rejection-risk audits, use apple-app-store-best-practices instead; for App Store
  Connect submission mechanics, app-store-connect-submission; for App Store
  screenshot dimensions and capture, apple-app-store-screenshots.
---

# Apple Human Interface Guidelines

*Last synced with Apple HIG: 2026-06-10*

Distillation of the complete [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines) — every Foundations, Patterns, Components, Inputs, and Technologies page, across all six platforms — compressed to the load-bearing guidance: what each element is for, when to use it over its alternatives, Apple's best practices as imperatives, the hard numbers, and how behavior differs per platform.

## Core Design Principles

These apply to every Apple-platform design decision, so they live here rather than in a reference file.

- **Clarity** — content comes first. Text is legible at every size, icons are precise, adornments are subtle. If a decoration competes with content, remove it.
- **Deference** — the interface helps people understand and interact with content, but never competes with it. Chrome stays out of the way; fluid motion and translucency hint at depth without stealing attention.
- **Depth** — distinct visual layers and realistic motion convey hierarchy and orientation. Transitions signal where things came from and where they go.

**The Liquid Glass era.** Apple's current system material is Liquid Glass: a dynamic, translucent material that reflects and refracts surrounding content while adapting to context. Let system components adopt it rather than recreating it; pair it with semantic colors and SF Symbols so the system can adapt appearance automatically. Don't apply heavy custom backgrounds to controls that the system already renders with Liquid Glass — that fights the material and dates the app instantly.

Supporting principles, one line each:

- **Hierarchy** — establish a clear visual order; people should know what matters most at a glance.
- **Consistency** — use system components and conventions; familiarity is a feature, not a constraint.
- **Feedback** — every action gets a perceivable response (visual, haptic, or audible).
- **User control** — people initiate actions and can always cancel or undo; never take destructive action without consent.

## Identify the Platform First

The same component differs meaningfully across platforms — a button on watchOS is full-width and capsule-shaped; on visionOS it gains gaze hover effects; on macOS it participates in keyboard focus rings. Before answering, identify which platform(s) the question targets. If unspecified, ask — or assume iOS and say so. For platform-wide conventions (window model, focus model, input idioms), load the matching `platform-*.md`; for a specific component, load its `components-*.md` cluster, which carries the per-platform deltas inline.

## Reference Files

Load only the rows the question touches — usually a single file. Each reference is a distilled cluster of related HIG pages with per-platform deltas inline.

| Asking about… | Read |
|---|---|
| Color, Dark Mode, materials / Liquid Glass, typography, icons, images, SF Symbols, branding | `references/foundations-visual.md` |
| Accessibility, inclusion, layout / margins / safe areas, motion, writing style, pointing devices | `references/foundations-ux.md` |
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
| Siri, App Shortcuts, CarPlay, HomeKit, Maps, SharePlay, Live Photos, machine-learning / generative-AI surfaces | `references/technologies-system-services.md` |
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
