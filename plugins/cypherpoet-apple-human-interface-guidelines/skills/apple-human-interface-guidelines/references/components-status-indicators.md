# Components — Status & Indicators

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Components pages: Progress indicators, Gauges, Activity rings, Rating indicators, Labels.

## Contents
- [Progress indicators](#progress-indicators)
- [Gauges](#gauges)
- [Activity rings](#activity-rings)
- [Rating indicators](#rating-indicators)
- [Labels](#labels)

### Progress indicators
*Last changed: 2023-09*

**Purpose:** Show that the app isn't stalled while loading content or running lengthy operations; some also let people estimate wait time. All are transient — visible only while the operation runs.

**Use it when / not when:**
- Use a determinate indicator when: the task has a well-defined duration (e.g. file conversion) — it fills a linear or circular track as the task completes.
- Use an indeterminate indicator (activity indicator / spinner) when: the task is unquantifiable (e.g. loading or syncing complex data) — it uses an animated image; all platforms support a spinning circular image, and macOS also supports an indeterminate bar.
- Prefer a determinate indicator whenever possible — it helps people decide whether to wait, restart, or abandon.

**Best practices:**
- Be accurate when reporting advancement; even out the pace so people trust the estimate. Showing 90% in five seconds and the last 10% in 5 minutes feels deceptive.
- Keep indicators moving — a stationary indicator reads as a stalled or frozen app. If a process stalls, give feedback on the problem and what to do.
- When an indeterminate process becomes measurable, switch the progress bar from indeterminate to determinate.
- Don't switch from the circular style to the bar style — different shapes/sizes disrupt the interface and confuse people.
- Display a short, accurate, succinct description for context if helpful; avoid vague terms like "loading" or "authenticating."
- Place progress indicators in a consistent location across platforms and apps.
- When feasible, let people halt processing: include a Cancel button; add a Pause button too if interrupting causes negative side effects (e.g. losing a partial download).
- When canceling loses progress, show an alert to confirm the cancellation or resume.
- Progress bar: track fills leading→trailing. Circular indicator: track fills clockwise.

Canonical implementations: SwiftUI `ProgressView`, UIKit `UIProgressView` / `UIActivityIndicatorView` / `UIRefreshControl`, AppKit `NSProgressIndicator`.

**Platform deltas:**
- iOS/iPadOS: Refresh content controls — a specialized activity indicator, hidden by default, revealed by dragging the view (e.g. Mail Inbox) to reload immediately. Still perform periodic automatic updates; don't make people initiate every refresh. Add a title only if it adds value (e.g. last-updated time), never to explain how to refresh. See `UIRefreshControl`.
- macOS: Indeterminate indicators can be bar or circular. Prefer a spinner for background-operation status or constrained space (e.g. inside a text field or next to a button). Avoid labeling a spinner.
- watchOS: System shows indicators in white over the scene's background color by default; change via tint color. Supports progress bar, circular indicator, and activity indicator.
- tvOS: No additional considerations.
- visionOS: No additional considerations.

### Gauges
*Last changed: 2022-09*

**Purpose:** Display a specific numerical value within a range of values, optionally giving context about the range itself (e.g. labeling endpoints and using a color spectrum).

**Best practices:**
- Write succinct labels describing the current value and both endpoints of the range. Even when a style doesn't show all labels, VoiceOver reads the visible ones.
- Consider filling the path with a gradient to communicate purpose (e.g. red→blue for hot→cold temperature).
- Standard style: shows an indicator at the current value's location. Capacity style: shows a fill that stops at the value's location. Paths can be circular or linear.
- Accessory variant: circular and linear, standard and capacity styles, visually similar to watchOS complications; works well in iOS Lock Screen widgets and anywhere echoing complications.

Canonical implementations: SwiftUI `Gauge`, AppKit `NSLevelIndicator`.

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS: Also defines a level indicator (`NSLevelIndicator`) for a value within a range, configurable for capacity, rating, or (rarely) relevance. Capacity style is continuous (translucent track filled by a solid bar) or discrete (a row of equally sized rectangular segments matching total capacity; segments fill completely, never partially). Prefer continuous for large ranges, where discrete segments get too small. Default fill is green; change fill at significant levels (very low/high, past the middle), or use the tiered state to show a sequence of colors in one indicator. Rating style → see Rating indicators. Relevance style (rare) shows relevancy as a shaded horizontal bar (e.g. ranking search results).
- visionOS: No additional considerations.
- watchOS: No additional considerations.
- tvOS: Not supported in tvOS.

### Activity rings
*Last changed: 2024-03*

**Purpose:** Show an individual's daily progress toward Move, Exercise, and Stand goals, matching the colors and meanings of the Activity app.

**Best practices:**
- Display Activity rings when relevant to your app's purpose — especially health/fitness apps and those contributing to HealthKit (e.g. on a workout metrics screen or a post-workout summary).
- Use Activity rings only to show Move, Exercise, and Stand information. Don't replicate or modify them for other purposes, never use them for other data, and never show Move/Exercise/Stand progress in another ring-like element.
- Show progress for a single person only; make it obvious whose progress it is via a label, photo, or avatar.
- Keep the visual appearance identical everywhere: never change ring colors (no filters or opacity changes); always display on a black background; prefer enclosing rings and background within a circle by adjusting the enclosing view's corner radius rather than a circular mask; keep the black background visible around the outermost ring (add a thin black stroke if needed; no gradient, shadow, or other effect); scale rings appropriately; design surrounding UI to blend with the rings, never the reverse.
- For labels/values tied to a ring, use its matching RGB color (see Specs).
- Maintain a minimum outer margin no less than the distance between rings; never crop, obstruct, or encroach on that margin or the rings.
- Differentiate other ring-like elements with padding, lines, labels, color, or scale.
- Don't send notifications repeating Move/Exercise/Stand info the Activity app already sends, and don't show an Activity ring element in notifications (referencing progress uniquely is fine).
- Don't use Activity rings for decoration (never in labels or background graphics) or for branding (never in the app icon or marketing materials).

Canonical implementations: HealthKit `HKActivityRingView` (iOS).

**Specs:**

Ring label/value colors (RGB):

| Ring | R | G | B |
| --- | --- | --- | --- |
| Move | 250 | 17 | 79 |
| Exercise | 166 | 255 | 0 |
| Stand | 0 | 255 | 246 |

**Platform deltas:**
- iOS: Available via `HKActivityRingView`. With an Apple Watch paired, shows all three rings; without one paired, shows only the Move ring (approximated from steps and other apps' workout info). Activity history can mix both styles.
- iPadOS: No additional considerations.
- watchOS: No additional considerations. Always contains three rings.
- macOS: Not supported in macOS.
- tvOS: Not supported in tvOS.
- visionOS: Not supported in visionOS.

### Rating indicators
*Last changed: 2022-09*

**Purpose:** Use a series of horizontally arranged graphical symbols — by default, stars — to communicate a ranking level.

**Best practices:**
- Doesn't display partial symbols; rounds the value to complete symbols only.
- Symbols are always the same distance apart and don't expand or shrink to fit the component's width.
- Make it easy to change rankings — let people adjust an item's rank inline without a separate editing screen.
- If you replace the star with a custom symbol, ensure its purpose is clear; the star is highly recognizable and other symbols may not read as a rating scale.

Canonical implementations: AppKit `NSLevelIndicator.Style.rating`.

**Platform deltas:**
- macOS: No additional considerations.
- iOS: Not supported in iOS.
- iPadOS: Not supported in iPadOS.
- tvOS: Not supported in tvOS.
- visionOS: Not supported in visionOS.
- watchOS: Not supported in watchOS.

### Labels
*Last changed: 2023-06*

**Purpose:** A static piece of text people can read and often copy, but not edit — appearing in buttons, menu items, lists, and views to convey context and available actions.

**Use it when / not when:**
- Use a label when: displaying a small amount of text people don't need to edit.
- Use a text field when: people need to edit a small amount of text.
- Use a text view when: displaying (and optionally editing) a large amount of text.

**Best practices:**
- Prefer system fonts; labels support Dynamic Type (where available) by default. If you restyle or use custom fonts, keep text legible.
- Use the four system label colors to convey relative importance (see Specs).
- Make useful label text selectable — let people copy error messages, locations, IP addresses, etc.

**Specs:**

System label colors:

| System color | Example usage | iOS/iPadOS/tvOS/visionOS | macOS |
| --- | --- | --- | --- |
| Label | Primary information | `label` | `labelColor` |
| Secondary label | Subheading or supplemental text | `secondaryLabel` | `secondaryLabelColor` |
| Tertiary label | Unavailable item or behavior | `tertiaryLabel` | `tertiaryLabelColor` |
| Quaternary label | Watermark text | `quaternaryLabel` | `quaternaryLabelColor` |

Canonical implementations: SwiftUI `Label` / `Text`, UIKit `UILabel`, AppKit `NSTextField`.

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- tvOS: No additional considerations.
- visionOS: No additional considerations.
- macOS: No additional considerations.
- watchOS: Date and time text components show the current date, time, or both (configurable formats, calendars, time zones); a countdown timer component shows a precise count down/up. System date/timer components auto-adjust presentation to fit available space and update content without further input. Consider using them in complications; for developer guidance see `Text`.
