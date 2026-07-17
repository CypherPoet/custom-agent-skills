# Components — Content Views

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Components pages: Lists and tables, Collections, Split views, Scroll views, Outline views, Column views, Boxes, Image views, Web views, Lockups, Charts, Charting data.

**Contents:** [Lists and tables](#lists-and-tables) · [Collections](#collections) · [Split views](#split-views) · [Scroll views](#scroll-views) · [Outline views](#outline-views) · [Column views](#column-views) · [Boxes](#boxes) · [Image views](#image-views) · [Web views](#web-views) · [Lockups](#lockups) · [Charts](#charts) · [Charting data](#charting-data)

### Lists and tables
*Last changed: 2023-06*

**Purpose:** Present data in one or more columns of rows, supporting grouped/hierarchical content and interactions like selecting, adding, deleting, and reordering.

**Use it when / not when:**
- Use when: presenting text — the row format makes text easy to scan and read; expressing information hierarchy for navigation.
- Prefer a collection when: items vary widely in size, or you need to display a large number of images.
- Prefer an outline view (macOS) when: presenting hierarchical data (it adds disclosure triangles for nested levels).

**Best practices:**
- Keep item text succinct to minimize truncation/wrapping; for large per-item text, list titles only and reveal content in a detail view.
- Preserve readability when narrow — a centered ellipsis preserves both start and end of clipped content.
- Use descriptive column headings in multicolumn tables: nouns or short noun phrases, title-style capitalization, no ending punctuation. For a single-column table with no heading, supply a label or header for context.
- Provide selection feedback: persistently highlight the selected row for hierarchy navigation; briefly highlight then add a checkmark for option selection.
- Let people edit (reorder at minimum) when it makes sense; in iOS/iPadOS, people must enter edit mode before selecting items.
- Choose a list/table style coordinating with data and platform: iOS/iPadOS grouped style uses headers, footers, and space to separate groups; watchOS elliptical style makes items roll off a rounded surface; macOS bordered style uses alternating row backgrounds for large tables.
- Use a row style fitting the content (e.g., leading image + label).

Canonical implementations: SwiftUI `List`, `Tables`, `ListStyle`; UIKit `UITableView`, `UIListContentConfiguration` (iOS/iPadOS/tvOS); AppKit `NSTableView`.

**Platform deltas:**
- iOS/iPadOS/visionOS: Use an info button (detail disclosure button) only to reveal more info about a row — it doesn't support navigation; use a disclosure indicator (`UITableViewCell.AccessoryType.disclosureIndicator`) to drill into subviews. Avoid adding an index to a table whose rows show trailing controls like disclosure indicators — index and controls both sit on the trailing side and interfere.
- macOS: Let people click a column heading to sort (re-click reverses direction); let people resize columns; consider alternating row colors in multicolumn tables; use an outline view, not a table, for hierarchical data.
- tvOS: Confirm images near a table still look good as each focused row highlights and slightly increases in size with rounded corners; don't add your own corner masks.
- watchOS: When possible, limit the number of rows (list most relevant + a way to see more). Constrain detail-view length to support vertical page-based navigation (it works only when detail views don't scroll).

### Collections

**Purpose:** Manage an ordered set of content in a customizable, highly visual layout (default horizontal row or grid).

**Use it when / not when:**
- Use when: showing image-based content.
- Prefer a table when: displaying text — it's simpler and more efficient to view and digest in a scrollable list.

**Best practices:**
- Use the standard row or grid layout whenever possible; avoid custom layouts that confuse or draw undue attention.
- Make it easy to choose an item; use adequate padding around images to keep focus/hover effects visible and prevent overlap.
- Add custom interactions only when necessary; by default people tap to select, touch and hold to edit, and swipe to scroll.
- Consider standard or custom animations as feedback when inserting, deleting, or reordering items.

Canonical implementations: UIKit `UICollectionView`; AppKit `NSCollectionView`.

**Platform deltas:**
- iOS/iPadOS: Use caution with dynamic layout changes; avoid changing layout while people view/interact unless it's a response to an explicit action.
- macOS/tvOS/visionOS: No additional considerations.
- watchOS: Not supported.

### Split views
*Last changed: 2025-06*

**Purpose:** Manage multiple adjacent panes of content (tables, collections, images, custom views), typically showing multiple hierarchy levels at once with navigation between them.

**Best practices:**
- Persistently highlight the current selection in each pane that leads to the detail view, to clarify pane relationships and keep people oriented.
- Consider letting people drag and drop content between panes.

Canonical implementations: SwiftUI `NavigationSplitView`, `VSplitView`, `HSplitView`; UIKit `UISplitViewController`; AppKit `NSSplitViewController`, `NSSplitView.DividerStyle`.

**Platform deltas:**
- iOS: Prefer a split view in a regular — not compact — environment; a compact environment (iPhone portrait) lacks horizontal space for multiple panes without wrapping/truncating.
- iPadOS: Can include two vertical panes (like Mail) or three (like Keynote). Account for narrow, compact, and intermediate window widths since iPad windows resize fluidly; ensure logical navigation between panes at all widths.
- macOS: Arrange panes vertically, horizontally, or both; dividers can drag to resize. Set reasonable min/max pane sizes so the divider stays visible. Consider letting people hide a pane (e.g., to expand an editing area) and provide multiple ways to reveal hidden panes (toolbar button, menu command, keyboard shortcut). Prefer the thin divider style (1 point wide); use thicker styles only for a specific need.
- tvOS: Default layout devotes a third of screen width to the primary pane and two-thirds to the secondary; a half-and-half layout is also available. Display a single title above the split view. Center the title when the secondary pane holds a content collection; place it above the primary pane when the secondary holds a single main content view.
- visionOS: Prefer a split view over a new window to display supplementary information; use a sheet for a small request or a simple blocking task.
- watchOS: Displays either the list view or a detail view as a full-screen view. Automatically display the most relevant detail view at launch. For multiple detail pages, place detail views in a vertical tab view so people scroll between tabs with the Digital Crown (a page indicator appears next to the Crown).

### Scroll views
*Last changed: 2026-06*

**Purpose:** Let people view content larger than the view's boundaries by moving it vertically or horizontally; the view itself has no appearance but can show a translucent scroll indicator.

**Best practices:**
- Support default scrolling gestures and keyboard shortcuts; custom scroll indicators must use the expected elastic behavior.
- Make it apparent when content is scrollable (e.g., show partial content at the view's edge).
- Avoid nesting scroll views of the same orientation; a horizontal scroll view inside a vertical one (or vice versa) is fine.
- Consider page-by-page scrolling when it fits the content; define page size (typically the view's current height/width) and optionally subtract a unit of overlap (a line of text, a row of glyphs, part of a picture) for context.
- Scroll automatically only as much as needed to retain context when: an operation selects/places the insertion point off-screen; people start entering info off-screen; the pointer moves past the view edge during selection; or people scroll away before acting on a selection.
- If you support zoom, set appropriate max/min scale values.

**Scroll edge effects** (iOS, iPadOS, macOS) — visual separation between floating elements like toolbars and the scrolling content behind them:
- Prefer the automatic style (more opaque separation for top toolbars with many controls, text outside Liquid Glass controls, and pinned table headers); thoroughly test legibility if using the soft style.
- Use a scroll edge effect only when a scroll view is behind floating interface elements — they aren't decorative and don't block or darken like overlays.
- Apply one scroll edge effect per view; in iPad/Mac split-view layouts each pane can have its own — keep them consistent in height to maintain alignment.

Canonical implementations: SwiftUI `ScrollView`, `PagingScrollTargetBehavior`, `ScrollEdgeEffectStyle`, `ScrollInputKind`/`look`; UIKit `UIScrollView`, `UIScrollEdgeEffect.Style`; AppKit `NSScrollView`, `NSScrollEdgeEffectStyle`; WatchKit `WKPageOrientation`.

**Platform deltas:**
- iOS/iPadOS: Consider a page control in page-by-page mode (e.g., Weather); if shown, don't also show the scrolling indicator on the same axis.
- macOS: A scroll indicator is called a scroll bar. Use small or mini scroll bars in space-tight panels, using the same size for all controls in the panel.
- tvOS: Views scroll but aren't distinct objects with scroll indicators; the system auto-scrolls to keep focused items visible.
- visionOS: The scroll indicator has a small fixed size, appearing vertically centered at the trailing edge during vertical scrolling and horizontally centered at the bottom edge during horizontal scrolling; it's slightly thicker than in iOS, so increase tight margins to avoid overlap. Looking at the indicator and dragging enables a jog-bar experience controlling scroll speed via tick marks. **Look to Scroll:** off by default — add support per scroll view. Support it for reading/browsing views; avoid it for secondary content with UI controls or dense info needing precise scrolling. Maintain consistency across similar views. Prefer making the view full-width or full-height with clear edges. Remove custom scroll effects/animations (parallax, etc.) before supporting it. Developer guidance: `look`, `ScrollInputKind`.
- watchOS: Prefer vertically scrolling content navigated with the Digital Crown. Use tab views for page-by-page scrolling (displayed as pages); a vertical stack of tab views lets the Crown move through full-screen pages with a page indicator. Consider limiting an individual page to a single screen height; use variable-height pages judiciously and place them after fixed-height pages.

### Outline views

**Purpose:** Present hierarchical data in a scrolling list of cells organized into columns and rows, with at least one column of primary hierarchical data and disclosure triangles that expand parents to reveal children (e.g., Finder).

**Use it when / not when:**
- Use when: displaying text-based hierarchical content, often on the leading side of a split view.
- Prefer a table when: data isn't hierarchical.

**Best practices:**
- Expose data hierarchy in the first column only; other columns display attributes of the primary data.
- Use descriptive column headings: nouns or short noun phrases, title-style capitalization, no punctuation (avoid a trailing colon). Always provide headings in multi-column outline views; supply a label or other context for a single-column outline view with no heading.
- Consider letting people click column headings to sort (ascending/descending); clicking the primary column heading sorts at each hierarchy level; re-clicking a sorted column reverses direction.
- Let people resize columns.
- Make it easy to expand/collapse nested containers — clicking a disclosure triangle expands one folder; Option-clicking expands all subfolders.
- Retain people's expansion choices and restore them next time.
- Consider alternating row colors in multi-column outline views.
- Let people edit when it makes sense — single-click a cell to edit; a double-click can do something different (e.g., open the file).
- Consider a centered ellipsis to truncate cell text instead of clipping.
- Consider offering a search field (often in the toolbar) for lengthy outline views.

Canonical implementations: SwiftUI `OutlineGroup`; AppKit `NSOutlineView`.

**Platform deltas:**
- Not supported in iOS, iPadOS, tvOS, visionOS, or watchOS.

### Column views

**Purpose:** Also called a browser — view and navigate a data hierarchy using a series of vertical columns, where each column is one hierarchy level and selecting a parent shows its children in the next column (e.g., Finder column view).

**Use it when / not when:**
- Use when: you have a deep data hierarchy where people navigate back and forth frequently between levels and you don't need the sorting a list or table provides.

**Best practices:**
- Show the root level of the hierarchy in the first column so people can quickly scroll back to start over.
- Consider showing info about the selected item when it has no nested items (Finder shows a preview plus creation date, modification date, file type, and size).
- Let people resize columns (especially important when item names exceed the default column width).

Canonical implementations: AppKit `NSBrowser`.

**Platform deltas:**
- Not supported in iOS, iPadOS, tvOS, visionOS, or watchOS.

### Boxes

**Purpose:** Create a visually distinct group of logically related information and components, using a visible border or background color (and optionally a title) to separate contents from the rest of the interface.

**Best practices:**
- Prefer keeping a box relatively small versus its containing view; as it approaches the window/screen size it stops communicating separation and crowds other content.
- Use padding and alignment, not nested boxes, to communicate subgroups within a box.
- Provide a succinct introductory title if it clarifies contents (also helps VoiceOver users predict content).
- If you need a title, write a brief descriptive phrase with sentence-style capitalization and no ending punctuation — except in a settings pane, where you append a colon.

Canonical implementations: SwiftUI `GroupBox`; AppKit `NSBox`.

**Platform deltas:**
- iOS/iPadOS: Default to the secondary and tertiary background colors.
- macOS: Displays a box's title above it by default.
- visionOS: No additional considerations.
- tvOS/watchOS: Not supported.

### Image views
*Last changed: 2023-06*

**Purpose:** Display a single image — or an animated sequence of images — on a transparent or opaque background; typically not interactive.

**Use it when / not when:**
- Use when: the view's primary purpose is simply to display an image.
- Prefer a system button when: you want an interactive image — configure the button to display the image rather than adding button behaviors to an image view.
- Prefer SF Symbols or an interface icon when: displaying an icon — symbols are vector-based and renderable in various colors/opacities; interface icons (glyph/template images) are typically bitmaps whose nontransparent pixels receive color. Both can use people's accent colors.

**Best practices:**
- Take care overlaying text on images: ensure good contrast and consider a text shadow or background layer.
- Use a consistent size for all images in an animated sequence; prescale images to fit the view so the system doesn't scale. Performance is generally better when all images are the same size and shape.
- An image view can hold rich image data in formats like PNG, JPEG, and PDF.

Canonical implementations: SwiftUI `Image`; UIKit `UIImageView`; AppKit `NSImageView`; WatchKit `WKImageAnimatable`.

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS: Use an image well for an editable image view (supports copy, paste, drag, Delete key to clear). Use an image button, not an image view, for a clickable image.
- tvOS: Many images combine multiple layers with transparency for depth (see Layered images).
- visionOS: Windows can use image views for 2D, stereoscopic, and spatial photos; with RealityKit, display images of any type outside image views next to 3D content or generate a spatial scene from a 2D image (`ImagePresentationComponent`).
- watchOS: Use SwiftUI for animations when possible; alternatively use WatchKit (`WKImageAnimatable`).

### Web views

**Purpose:** Load and display rich web content (embedded HTML, websites) directly within your app (e.g., Mail showing HTML messages).

**Use it when / not when:**
- Use when: letting people briefly access a website without leaving your app's context.
- Don't: build a web browser — Safari is the primary way people browse; replicating its functionality is unnecessary and discouraged.

**Best practices:**
- Support forward and back navigation when appropriate (not available by default); provide corresponding controls if people are likely to visit multiple pages.

Canonical implementations: WebKit `WKWebView`.

**Platform deltas:**
- iOS/iPadOS/macOS/visionOS: No additional considerations.
- tvOS/watchOS: Not supported.

### Lockups

**Purpose:** Combine multiple separate views (content view, header, footer) into a single interactive unit that expands and contracts together as the lockup gets focus; four types — cards, caption buttons, monograms, and posters.

**Best practices:**
- Allow adequate space between lockups since a focused lockup expands in size, to avoid overlapping or displacing others.
- Use consistent lockup sizes (matching widths and heights) within a row or group.
- **Cards:** combine header, footer, and content view to present ratings and reviews for media items (`TVCardView`).
- **Caption buttons:** can include a title and subtitle beneath the button and contain either an image or text. On focus, they tilt with the swipe motion — up/down when aligned vertically, left/right when aligned horizontally, both in a grid (`TVCaptionButtonView`).
- **Monograms:** identify people (usually cast and crew) with a circular picture and name; show initials if no image is available. Prefer images over initials (`TVMonogramContentView`).
- **Posters:** an image plus optional title and subtitle hidden until focus; any size, appropriate to the content (`TVPosterView`).

Canonical implementations: TVUIKit `TVLockupView`, `TVLockupHeaderFooterView`.

**Platform deltas:**
- Not supported in iOS, iPadOS, macOS, visionOS, or watchOS. (tvOS component.)

### Charts
*Last changed: 2022-09*

**Purpose:** Organize data in a chart to communicate information with clarity and visual appeal, highlighting a few key pieces of a dataset to help people gain insights and make decisions.

**Anatomy:** A *mark* is the visual representation of a data value (choose a mark type — bar, line, point — to set the chart style). *Plotting* is depicting individual values; the *plot area* contains the marks. *Axes* define a frame of reference; *ticks* are reference points along an axis; *grid lines* extend from a tick across the plot area. *Labels* name axes/grid lines/ticks/marks; *accessibility labels* describe elements for assistive tech; titles, subtitles, annotations, and a *legend* add context.

**Marks — choose by the information you want to communicate:**
- Bar marks: compare values across categories or view proportions of a whole; for change over time they work best when each value is a sum (e.g., total steps per day).
- Line marks: show how values change over time; slope reveals magnitude of change and overall trends.
- Point marks: depict individual values as distinct marks; show how two properties relate and reveal outliers and clusters.
- Consider combining mark types for clarity (e.g., points on top of a line to highlight individual values).

**Axes:**
- Use a fixed axis range when specific min/max values are meaningful for all data (e.g., battery 0%–100%); use a dynamic range when values vary widely and you want marks to fill the plot area.
- Define the lower bound by mark type and usage: zero works well for bar charts (lets people compare relative heights), but a zero lower bound can obscure meaningful differences far from zero (e.g., a heart-rate chart hiding resting-vs-active differences).
- Prefer familiar value sequences in tick/grid-line labels (e.g., 0, 5, 10 rather than 1, 6, 11).
- Tailor grid-line and label density/weight to the chart's use cases — too many overwhelm, too few make estimation hard; use fewer grid lines and light labels when people can inspect individual points.

**Best practices:**
- Establish a consistent visual hierarchy — typically the data is most prominent, with descriptions and axes providing context without competing.
- In a compact environment, maximize the plot area width; keep vertical-axis labels as short as possible; consider putting units in a title and a longer axis label (e.g., a category name) inside the plot area.
- Make every chart accessible — support VoiceOver and enhance it with Audio Graphs.
- Let people interact with data when it makes sense, but don't require interaction to reveal critical information.
- Expand the hit target to the entire plot area (scrubbing) when marks are too small to target with a finger or pointer.
- Make interactive charts navigable via keyboard (including full keyboard access) and Switch Control; use accessibility APIs (e.g., `accessibilityRespondsToUserInteraction(_:)`) for a logical path, or let people move focus among subsets of values for very large datasets.
- Help people notice important changes (animate them) but also convey changes in other ways for VoiceOver users and people who turn off animations (`UIAccessibility.Notification` / `NSAccessibility.Notification`).
- Align a chart with surrounding interface elements; display each vertical grid line's label on its trailing side or shift the Y axis to the trailing side to keep a clean leading edge; anchor a stray label to a grid line with a tick.

**Descriptive content:**
- Write descriptions that help people understand what a chart does before they view it (especially important for VoiceOver users and people with certain cognitive disabilities).
- Summarize the chart's main message so people grasp it quickly (e.g., Weather's title/subtitle for next-hour precipitation).

**Color:**
- Avoid relying solely on color to differentiate data; supplement with different shapes or patterns (e.g., Health uses a red circle for systolic and a black/white diamond for diastolic).
- Add visual separation between contiguous areas of color (e.g., separators between stacked bar-mark segments, as in iPhone Storage Settings).

**Enhancing accessibility:** Swift Charts provides a default Audio Graphs implementation plus a default accessibility element per mark (or group).
- Consider Audio Graphs to give VoiceOver users more information; customize with a chart title and descriptive summary. Without Audio Graphs, provide an overview of structure and purpose — identify the chart type (bar, line), explain each axis, and describe upper/lower axis bounds.
- Write accessibility labels that support the chart's purpose (Maps summarizes elevation over a route portion; Health labels each Steps bar with its actual count).
- Prioritize clarity and comprehensiveness — include context (date/location), avoid repeating info available elsewhere (like an axis name).
- Avoid subjective terms (rapidly, gradually, almost); use actual values.
- Avoid ambiguous formats/abbreviations — "June 6" over "6/6"; "60 minutes"/"60 meters" over "60m."
- Describe what details represent, not what they look like (identify what each color series represents, don't name the colors).
- Be consistent about axis order (e.g., always mention the X axis first).
- Hide visible axis/tick text labels from assistive technologies — VoiceOver users get values via accessibility labels and Audio Graphs.

Canonical implementations: SwiftUI Swift Charts.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS: No additional considerations.
- watchOS: Avoid requiring complex chart interactions; prefer glanceable info and simple interactions; defer detailed/interactive versions to another platform (e.g., Heart Rate on watchOS shows the current day; Health on iPhone shows multiple periods and individual marks).

### Charting data
*Last changed: 2022-09*

**Purpose:** Design-guidance page for presenting data in a chart to communicate complex information with clarity and appeal (the companion to the Charts component page).

**Use it when / not when:**
- Use when: highlighting important information about a dataset; analyzing trends, visualizing a changing state over time, or comparing data across categories.
- Prefer a list or table when: you simply need to provide data — scrollable, searchable, sortable — without conveying information about it or helping people analyze it.

**Best practices:**
- Keep a chart simple; let people reveal additional details gradually (different detail levels or data subsets); consider offering several chart versions, each with more functionality.
- Make every chart accessible — provide accessibility labels that describe values/components and accessibility elements for interaction.
- Prefer common chart types (bar, line) so people already know how to read them.
- If presenting data in a novel way, help people learn to interpret it (e.g., Activity animates each ring to show how it maps to move/exercise/stand).
- Examine data from multiple levels (macro totals/averages, mid-level subsets, individual points) to find details worth surfacing.
- Add descriptive text — titles, subtitles, annotations, and a brief headline/summary (e.g., Weather's "Chance of light rain in the next hour"); descriptive text doesn't replace accessibility labels.
- Match the chart's size to its functionality, topic, and level of detail.
- Prefer consistency across multiple charts, deviating only to highlight meaningful differences.
- Maintain continuity among multiple charts using the same data — one chart type and consistent colors, annotations, layouts, and descriptive text (e.g., Health Trends small charts and their expanded versions).

Canonical implementations: SwiftUI Swift Charts.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: No additional considerations.
