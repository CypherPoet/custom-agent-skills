# Components — Navigation & Bars

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Components pages: Tab bars, Sidebars, Tab views, Toolbars, Segmented controls, Path controls, Page controls.

## Table of Contents

| Section | Covers |
|---|---|
| [Tab bars](#tab-bars) | A tab bar lets people navigate between the top-level sections of an app while preserving each section's navigation state |
| [Sidebars](#sidebars) | Leading-edge navigation among app areas and top-level content collections |
| [Tab views](#tab-views) | A tab view presents multiple mutually exclusive panes of content in the same area, switched via a tabbed control on the top edge |
| [Toolbars](#toolbars) | A toolbar provides convenient access to frequently used commands |
| [Segmented controls](#segmented-controls) | A segmented control is a linear set of two or more equal-width segments |
| [Path controls](#path-controls) | A path control (macOS only) shows the file system path of a selected file or folder |
| [Page controls](#page-controls) | Indicator dots for navigating a flat, ordered set of pages and showing the current page |

## Tab bars
*Last changed: 2026-06*

**Purpose:** A tab bar lets people navigate between the top-level sections of an app while preserving each section's navigation state.

**Use it when / not when:**
- Use when: supporting navigation between top-level app sections.
- Prefer a toolbar when: you need controls that act on elements in the current view (tab bars are for navigation, not actions).
- Prefer a sidebar (or a sidebar-adaptable tab bar) when: the app has a complex information structure with many sections.

**Best practices:**
- Use the right number of tabs; fewer tabs are easier to navigate. Weigh added-tab complexity against access frequency.
- Keep the tab bar visible when people navigate to different sections; exception: a modal view may cover it.
- Avoid overflow tabs. When horizontal space limits visible tabs, the trailing tab becomes a More tab (iOS, iPadOS) revealing the rest in a separate list — limit scenarios that trigger this.
- Don't disable or hide tab bar buttons even when content is unavailable; if a section is empty, explain why.
- Include tab labels (beneath or beside the icon); use single words when possible.
- Use SF Symbols for tab icons; prefer filled symbols/icons. Icons appear above labels in compact views, side by side in regular views.
- Use a badge (red oval, white text, number or exclamation point) only for critical information.
- Avoid applying a similar color to tab labels and content-layer backgrounds; with bright colorful content, prefer a monochromatic tab bar or a sufficiently differentiated accent color.
- A tab bar can include a dedicated search tab at the trailing end.

Canonical implementations: SwiftUI `TabView`, `TabViewStyle.tabBarOnly`, `TabViewStyle.sidebarAdaptable`, `TabBarMinimizeBehavior`, `TabViewCustomization`, `TabViewBottomAccessoryPlacement`; UIKit `UITabBar`, `UITabBarController.MinimizeBehavior`, `UITab.Placement`.

**Platform deltas:**
- iOS: Tab bar floats above content at the bottom on a Liquid Glass background. With an attached accessory (e.g. MiniPlayer), you can minimize the tab bar and move the accessory inline on scroll-down; exit by tapping a tab or scrolling to top.
- iPadOS: Tab bar displays near the top. Can be a fixed element (`tabBarOnly`) or include a button converting it to a sidebar (`sidebarAdaptable`). Let people customize tabs; aim for a default of five or fewer to preserve continuity between compact and regular sizes.
- macOS: No additional considerations.
- visionOS: Tab bar is always vertical, fixed relative to the window's leading side; expands automatically on look, tap to open a tab (can temporarily obscure content behind it). Supply a symbol (always visible) and a short text label (revealed on look) per tab. Consider a sidebar within a tab for deep hierarchies, but don't let sidebar selections change the open tab.
- tvOS: Highly customizable (background tint/color/image, per-item fonts including selected, selected/unselected tints, button icons like settings and search). Translucent by default with only the selected tab opaque; focused selected tab gains a drop shadow. Height is 68 points; top edge is 46 points from the top of the screen — neither is changeable. Overflow items truncate with a fade from the right (and from the left when scrolling). Tab bar can scroll offscreen when a tab is a single main view, but stays pinned for split views; Menu returns focus to the tab bar. In live-viewing apps order tabs: live content, then DVR/recorded, then other.
- watchOS: Not supported.

## Sidebars
*Last changed: 2026-06*

**Purpose:** A sidebar appears on the leading side of a view and lets people navigate between app areas or top-level content collections like folders and playlists.

**Use it when / not when:**
- Use when: there's ample vertical and horizontal space and people benefit from many navigation options.
- Prefer a tab bar when: space is limited or you want more screen for content; for many apps a sidebar-adaptable tab bar provides both rather than forcing a choice.

**Best practices:**
- Extend visually rich content beneath the sidebar via horizontal scroll or a background extension effect (mirrors adjacent content under the sidebar).
- Let people customize the sidebar's contents when possible.
- Group hierarchy with disclosure controls if the app has a lot of content, to keep vertical space manageable.
- Use familiar SF Symbols for items; prefer a custom symbol over a bitmap image for custom icons.
- Let people hide the sidebar using platform-native interactions (iPadOS edge swipe; macOS show/hide button or View-menu Show/Hide Sidebar commands). Avoid hiding it by default so it stays discoverable.
- In general, show no more than two levels of hierarchy; for deeper data use a split view with a content list between sidebar items and the detail view.
- If using two hierarchy levels, title each group with succinct, descriptive labels.
- Sidebar icons use the app's accent color by default; on macOS honor the user's chosen system accent color. Use fixed colors sparingly and only with clear purpose (e.g. Mail's yellow VIP icon).

Canonical implementations: SwiftUI `TabViewStyle.sidebarAdaptable`, `NavigationSplitView`, `ListStyle.sidebar`, `backgroundExtensionEffect()`; UIKit `UICollectionLayoutListConfiguration`, `UICollectionLayoutListConfiguration.Appearance.sidebar`; AppKit `NSSplitViewController`.

**Platform deltas:**
- iOS, iPadOS: The `sidebarAdaptable` tab view style lets you choose sidebar or tab bar at launch, with a button to switch; it adapts to platform, rotation, and window resizing. Consider a tab bar first; use the convertible sidebar appearance for less-frequent content. If not using SwiftUI, apply `UICollectionLayoutListConfiguration.Appearance.sidebar`.
- macOS: Row height, text, and glyph size depend on overall sidebar size (small, medium, large), settable programmatically or via General settings. Consider auto-hiding/revealing the sidebar on window resize. Avoid critical info or actions at the bottom (people often hide the window's bottom edge).
- visionOS: For deep hierarchies, consider a sidebar within a tab for secondary navigation; don't let sidebar selections change the open tab. A window typically expands to fit a sidebar, so people rarely need to hide it.
- tvOS: No additional considerations.
- watchOS: Not supported.

## Tab views
*Last changed: 2023-06*

**Purpose:** A tab view presents multiple mutually exclusive panes of content in the same area, switched via a tabbed control on the top edge.

**Use it when / not when:**
- Use when: presenting closely related, mutually exclusive panes of content (macOS/AppKit).
- Prefer a segmented control when: on iOS/iPadOS (tab views aren't supported there).
- Prefer a pop-up button when: there are too many panes to display reasonably as tabs.

**Best practices:**
- Use a tab view for closely related areas of content; people expect tabs to hold similar/related content.
- Keep each pane self-contained — controls within a pane affect only that pane.
- Label every tab to describe its pane's contents; use nouns or short noun phrases (verbs occasionally), with title-style capitalization.
- Avoid a pop-up button to switch tabs (a tabbed control needs one click and shows all choices at once); a pop-up is acceptable only when there are too many panes for tabs.
- Avoid more than six tabs; for six or more, use another approach (e.g. a pop-up button menu).
- The tabbed control sits on the top edge; you can hide it for programmatic pane switching. When hidden, the content area can be borderless (solid or transparent), bezeled, or line-bordered.
- In general, inset the tab view by leaving a window-body margin on all sides; extending to the window edges is unusual.

Canonical implementations: SwiftUI `TabView`; AppKit `NSTabView`.

**Platform deltas:**
- iOS, iPadOS: Not supported — use a segmented control for similar functionality.
- watchOS: Displayed as page controls (`TabView`).
- tvOS, visionOS: Not supported.

## Toolbars
*Last changed: 2025-12*

**Purpose:** A toolbar provides convenient access to frequently used commands, controls, navigation, and search, arranged horizontally along the top or bottom edge of a view.

**Use it when / not when:**
- Use when: acting on content in the view, facilitating navigation, or orienting people.
- Prefer a tab bar when: navigating between top-level areas of an app (a tab bar is specifically for that).

**Best practices:**
- Choose items deliberately to avoid overcrowding; define which items move to the overflow menu as the toolbar narrows.
- Add a More menu only if needed for additional/less-important actions; try to fit all actions in the toolbar first.
- On iPadOS and macOS, consider letting people customize the toolbar.
- Reduce toolbar backgrounds and tinted controls; let the content layer inform color, and use a `ScrollEdgeEffectStyle` to distinguish the toolbar area when needed.
- Avoid a similar color on toolbar item labels and content-layer backgrounds; with bright colorful content prefer the default monochromatic appearance.
- Prefer standard components; standard buttons, text fields, headers, footers have corner radii concentric with bar corners — match that for custom components.
- Titles: provide a useful per-window title; you may leave the title area empty if redundant. Don't title windows with the app name. Keep titles under 15 characters.
- Navigation: use the standard Back and Close buttons and symbols; don't use text labels saying "Back" or "Close".
- Actions: prioritize main-task commands. Prefer simple recognizable symbols over text (except actions like "edit"). Prefer system-provided symbols without borders (no outlined-circle symbols). Use the `.prominent` style for one key action (Done/Submit) and place it on the trailing side.
- Item positions: leading edge (back, sidebar toggle, title, document menu — not customizable), center area (common controls, optional title; customizable on macOS/iPadOS, collapses into the overflow menu when the window shrinks), trailing edge (important always-available items, inspector buttons, optional search field, More menu, primary action like Done — visible at all window sizes).
- Group items logically by function and frequency; group navigation and critical actions (Done, Close, Save) in dedicated, distinct sections. Aim for a maximum of three groups. Keep groupings/placement consistent across platforms.
- Keep text-labeled actions separate from symbol actions by inserting fixed space (`UIBarButtonItem.SystemItem.fixedSpace`), so adjacent labels/symbols don't appear to merge.
- Consider temporarily hiding toolbars for a distraction-free experience, with a reliable way to restore them.

Canonical implementations: SwiftUI `Toolbars`, `ScrollEdgeEffectStyle`, `ToolbarItemPlacement.topBarLeading`/`.topBarTrailing`/`.bottomBar`/`.primaryAction`; UIKit `UIToolbar`, `UINavigationBar.prefersLargeTitles`, `UIBarButtonItem.SystemItem.fixedSpace`; AppKit `NSToolbar`.

**Platform deltas:**
- iOS: Prioritize only the most important items in the main toolbar area; use a More menu for the rest. Use a large title that transitions to standard on scroll and back to large at the top (`prefersLargeTitles`). A navigation-specific toolbar is sometimes called a navigation bar.
- iPadOS: A toolbar and a tab bar can coexist in the same horizontal space at the top of the view.
- macOS: Toolbar sits at the top of the window, below or integrated with the title bar; window titles can display inline with controls, and toolbar items don't include a bezel. Make every toolbar item also available as a menu bar command (people can customize or hide the toolbar).
- visionOS: System toolbar appears along the bottom edge, above the window-management controls, in a plane slightly in front of the window; uses a variable blur for legibility as content scrolls behind. Supply a symbol or text label per item (looking at a symbol reveals its label). Prefer the system-provided toolbar. Avoid a vertical toolbar (tab bars are vertical here). Prevent windows from resizing below the toolbar width (no menu bar exists). Offer contextual toolbar controls in modal states, restoring standard controls on exit. Avoid pull-down menus (they may obscure window controls below the bottom edge).
- watchOS: Place toolbar buttons in the top corners (`topBarLeading`, `topBarTrailing`) or along the bottom (`bottomBar`); they stay visible as content scrolls under them. A scrolling toolbar button (`primaryAction`) stays hidden until people scroll up — use it for an important action that isn't a primary app function.
- tvOS: No additional considerations.

## Segmented controls
*Last changed: 2023-06*

**Purpose:** A segmented control is a linear set of two or more equal-width segments, each functioning as a button, offering a single choice (or, in macOS, single or multiple choices) or acting as a set of momentary action buttons.

**Use it when / not when:**
- Use when: providing closely related choices that affect an object, state, or view, or grouping functions and showing selection state.
- Prefer a tab bar when: switching between completely separate sections of an app (iOS/iPadOS).
- Prefer a tab view when: switching views in the main window area on macOS (use a segmented control for view switching in a toolbar or inspector instead).
- Prefer a split view when: filtering content on tvOS, or for back-and-forth between content and filtering options.

**Best practices:**
- Keep control types consistent within one control: don't mix action segments with selection-state segments.
- Limit the number of segments: no more than about five to seven in a wide interface, no more than about five on iPhone.
- In general keep segment size consistent (equal width); keep icon and title widths consistent too.
- Prefer either text or images — not a mix — in a single control.
- Use content of similar size in each segment.
- Use nouns or noun phrases with title-style capitalization for segment labels; a text-label control needs no introductory text.

Canonical implementations: SwiftUI `PickerStyle.segmented`; UIKit `UISegmentedControl`, `UISegmentedControl.isMomentary`; AppKit `NSSegmentedControl`, `NSSegmentedControl.SwitchTracking.momentary`.

**Specs:**

| Context | Max segments |
| --- | --- |
| Wide interface | ~5–7 |
| iPhone | ~5 |

**Platform deltas:**
- iOS, iPadOS: Consider a segmented control to switch between closely related subviews; for separate app sections use a tab bar.
- macOS: Supports single or multiple choice. Consider introductory text and per-segment labels below symbol/icon segments; provide a tooltip per segment if the app uses tooltips. Use a tab view (not a segmented control) for main-window view switching. Consider supporting spring loading (Magic Trackpad).
- tvOS: Consider a split view instead for content filtering. Avoid placing other focusable elements close by — segments select on focus, not click, so nearby elements can be focused accidentally.
- visionOS: Looking at an icon segment shows a tooltip with the descriptive text you supply.
- watchOS: Not supported.

## Path controls

**Purpose:** A path control (macOS only) shows the file system path of a selected file or folder.

**Best practices:**
- Use a path control in the window body, not the window frame; it's not intended for toolbars or status bars (Finder's path bar sits at the bottom of the window body, not the status bar).
- Standard style: a linear list of root disk, parent folders, and selected item, each with icon and name; names between first and last are hidden if too long. If editable, people can drag an item onto the control to select it.
- Pop-up style: shows the selected item's icon and name; clicking opens a menu of root disk, parent folders, and selected item. If editable, the menu adds a Choose command and people can drag an item onto the control.

Canonical implementations: AppKit `NSPathControl`.

**Platform deltas:**
- Not supported in iOS, iPadOS, tvOS, visionOS, or watchOS.

## Page controls
*Last changed: 2023-06*

**Purpose:** A page control displays a row of indicator dots (a solid dot marks the current page) representing pages in a flat, ordered list, helping people navigate to a page.

**Use it when / not when:**
- Use when: representing movement between an ordered list of pages.
- Prefer a sidebar or split view when: relationships are hierarchical or nonsequential, or navigation is complex.
- Prefer a grid (or other arrangement) when: more than ~10 pages exist as peers, so people can navigate in any order.

**Best practices:**
- Use page controls for movement between an ordered list of pages, not hierarchical or nonsequential relationships.
- Center the control horizontally near the bottom of the view or window.
- Don't display too many dots; more than about 10 are hard to count at a glance.
- Indicators are equidistant and clipped if too many fit; a solid dot denotes the current page.
- Custom indicator images must be simple and clear — avoid complex shapes, negative space, text, or inner lines; prefer simple SF Symbols (e.g. `location.fill`, `bookmark.fill`).
- Customize the default indicator image only when it enhances overall meaning.
- Avoid more than two different indicator images in one control.
- Avoid coloring indicator images; let the system color them to preserve contrast.

Canonical implementations: SwiftUI `PageTabViewStyle`; UIKit `UIPageControl`, `UIPageControl.preferredIndicatorImage`, `setIndicatorImage(_:forPage:)`, `UIPageControl.backgroundStyle`.

**Platform deltas:**
- iOS, iPadOS: Indicators show the current page's relative position; when more indicators than fit, both sides shrink to suggest more pages. People tap (leading/trailing of the current dot for next/previous; iPadOS pointer can target a specific dot) or scrub (drag left/right; scrubbing past an edge jumps to first/last). Avoid animating page transitions during scrubbing (use animated scrolling only for tapping). Background styles via `backgroundStyle`: Automatic (background only during interaction; use when not the primary nav element), Prominent (always shown; use only when it's the primary nav control), Minimal (never shown; use to show only current-page position with no scrub feedback) — avoid supporting the scrubber with the minimal style.
- macOS: Not supported.
- tvOS: Use on collections of full-screen pages where pages are peers; avoid additional controls (they make focus hard to maintain between pages).
- visionOS: Page controls represent pages and indicate the current page, but people don't interact with them.
- watchOS: Displayed at the bottom for horizontal pagination, or next to the Digital Crown for a vertical tab view (indicator shows position within the current page and within the set of pages). Prefer vertical pagination to separate views into distinct pages scrolled via the Digital Crown; give each page a clear purpose. Consider limiting each page to a single screen height; use variable-height pages judiciously, ideally only after fixed-height pages.
