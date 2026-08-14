# Components — Menus & Actions

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-10

Distilled from Apple's HIG Components pages: Buttons, Menus, Context menus, Pull-down buttons, Pop-up buttons, Edit menus, Action sheets, Activity views.

## Table of Contents

| Section | Covers |
|---|---|
| [Buttons](#buttons) | A button initiates an instantaneous action, combining a style, content (symbol and/or text label), and a system-defined role |
| [Menus](#menus) | A menu reveals commands, options, or states on interaction — a space-efficient way to present commands |
| [Context menus](#context-menus) | A context menu provides hidden-by-default access to functionality directly related to an item |
| [Pull-down buttons](#pull-down-buttons) | A pull-down button displays a menu of items or actions directly related to the button's purpose |
| [Pop-up buttons](#pop-up-buttons) | A pop-up button displays a menu of mutually exclusive options |
| [Edit menus](#edit-menus) | Editing actions for selected text, images, files, charts, and other content |
| [Action sheets](#action-sheets) | An action sheet is a modal view presenting choices related to an action people intentionally initiate |
| [Activity views](#activity-views) | An activity view (share sheet) presents sharing activities, actions |

## Buttons
*Last changed: 2025-12*

**Purpose:** A button initiates an instantaneous action, combining a style, content (symbol and/or text label), and a system-defined role.

**Use it when / not when:**
- Use when: an instantaneous action is needed.
- Prefer purpose-built button-like components (toggles, pop-up buttons, segmented controls) when: their specific behavior fits the use case.

**Best practices:**
- Give every button a hit region of at least 44x44 pt — 60x60 pt in visionOS.
- Always include a press state for a custom button.
- Use a prominent (accent-colored) style for the most likely action; limit prominent buttons to one or two per view.
- Use style — not size — to distinguish the preferred choice in a set; keep option buttons the same size.
- Avoid button-label colors similar to colorful content-layer backgrounds; prefer the default monochromatic label appearance.
- Use familiar icons for familiar actions (e.g. `square.and.arrow.up` for sharing); use text when a short verb label is clearer, in title-style capitalization (e.g. "Add to Cart").
- Roles: Normal (no meaning), Primary (default; responds to Return; can auto-close sheets/alerts), Cancel, Destructive (system red).
- Assign the primary role to the most likely choice — but never to a destructive button, even if it's the most likely choice.

Canonical implementations: SwiftUI `Button`, UIKit `UIButton`, AppKit `NSButton`.

**Specs:**

visionOS button sizes by shape:

| Shape | Mini (28 pt) | Small (32 pt) | Regular (44 pt) | Large (52 pt) | Extra large (64 pt) |
|---|---|---|---|---|---|
| Circular | Yes | Yes | Yes | Yes | Yes |
| Capsule (text only) | — | Yes | Yes | Yes | — |
| Capsule (text and icon) | — | — | Yes | Yes | — |
| Rounded rectangle | — | Yes | Yes | Yes | — |

macOS help button locations:

| View style | Help button location |
|---|---|
| Dialog with dismissal buttons (OK/Cancel) | Lower corner opposite the dismissal buttons, vertically aligned with them |
| Dialog without dismissal buttons | Lower-left or lower-right corner |
| Settings window or pane | Lower-left or lower-right corner |

**Platform deltas:**
- iOS/iPadOS: Configure a button to show an inline activity indicator (optionally with an alternate label, e.g. "Checkout" → "Checking out…") for actions that don't complete instantly; the system hides the button image while the indicator shows.
- macOS: Four unique button types. *Push button* (standard): can be the default button and tinted; use flexible-height (`NSButton.BezelStyle.flexiblePush`) only for two-line text or tall icons; append a trailing ellipsis when it opens another window, view, or app; consider spring loading (drag items over + force click). *Square/gradient button* (`smallSquare`): symbols/icons only, no text; for view-related actions (e.g. add/remove table rows); place in the view, not toolbars or status bars; no introductory labels. *Help button*: system-provided circular question mark; open the context-relevant help topic when possible; at most one per window; no introductory text; within a view, not the window frame. *Image button*: in a view, not the window frame; include about 10 pixels of padding between image edges and button edges; avoid the system border (`isBordered`); place any label below the button.
- visionOS: Shapes — circle for icon-only, rounded rectangle or capsule for text-only, capsule for icon+text. Four states: idle, hover, selected, unavailable; tooltips appear on dwell (text buttons rarely need one). Prefer a visible background shape and fill except in toolbars, context menus, alerts, and ornaments; use `thin` material on glass windows, glass material when floating in space. Don't use white background + black content — the system reserves that style for the toggled state. Prefer circular or capsule shapes; keep button centers at least 60 pt apart; add 4 pt padding around buttons 60 pt or larger to keep hover effects from overlapping; avoid stacking small/mini buttons. In stacks/rows of text buttons: rounded rectangle for vertical stacks, capsule for horizontal rows. Use standard controls for audible feedback — visionOS plays no haptics.
- watchOS: All inline buttons use the capsule shape with a contrasting material effect. Use a toolbar to place buttons in corners (system moves time/title and applies Liquid Glass). Prefer full-width buttons for primary actions; two side-by-side buttons need equal heights and images or short titles. Use identical heights in vertical stacks of one- and two-line text buttons.
- tvOS: No additional considerations.

## Menus
*Last changed: 2026-06*

**Purpose:** A menu reveals commands, options, or states on interaction — a space-efficient way to present commands; its labeling and organization rules apply to all menu types.

**Best practices:**
- Label action items with a verb or verb phrase (View, Close, Select); use title-style capitalization; drop articles (a, an, the).
- Show unavailable items dimmed and non-interactive; keep the menu itself available even if every item is unavailable.
- Append an ellipsis (…) when an item needs more input before completing.
- Use standard system icons for common actions; use item icons sparingly and only when they clearly represent the item; within a group, give icons to all items or none.
- List important or frequently used items first; group related items with separators; keep all logically related commands in one group even if importance varies (e.g. Paste and Match Style with Paste).
- Keep menus short — split long menus or use a submenu; long scrolling menus are acceptable only for user-defined/dynamic content (e.g. History, Bookmarks).
- Submenus: use sparingly (consider one when a term repeats in more than two items in a group, e.g. "Sort by"); restrict to a single level; consider a new menu if a submenu exceeds about five items; keep a submenu available even when its nested items aren't; prefer a submenu over indenting items.
- Toggled items: prefer one changeable label (Show Map/Hide Map) over two items; add a verb if state vs. action is ambiguous (Turn HDR On); show both items when seeing both states helps; use checkmarks for attributes in effect; consider a reset item (e.g. Plain) to clear multiple toggled attributes.
- In games: support the platform's default interaction method; keep menus readable and tappable when content scales to smaller screens.

Canonical implementation: SwiftUI `Menu`.

**Platform deltas:**
- iOS/iPadOS: Three layouts (`preferredElementSize`) — Small: row of 4 icon-only items above the list; Medium: row of 3 items with icon + short label above the list; Large (default): all items in a list. Use medium for three important frequent actions; use small only for closely related grouped actions (e.g. Bold/Italic/Underline/Strikethrough) with recognizable symbols.
- visionOS: Supports the small and large layouts. Present near the content it controls; menus can extend beyond window bounds. Prefer the `subtle` breakthrough effect (default via `automatic` when overlapping 3D content); `prominent` can disrupt and cause discomfort; `none` may hide the menu behind 3D content.
- macOS/tvOS/watchOS: No additional considerations.

## Context menus
*Last changed: 2023-12*

**Purpose:** A context menu provides hidden-by-default access to functionality directly related to an item, revealed by touch-and-hold/pinch-and-hold (iOS, iPadOS, visionOS), Control-click, or secondary click (macOS, iPadOS).

**Use it when / not when:**
- Use when: people need quick access to the commands most likely needed for the selected item — not advanced or rarely used commands.
- Prefer an edit menu when: the item needs text/content-editing commands — on iOS/iPadOS provide one or the other for an item, never both.

**Best practices:**
- Keep the menu short; aim for no more than about three separator-delimited groups.
- Support context menus consistently throughout the app — partial support reads as a bug.
- Always expose every context-menu item in the main interface too.
- Keep submenus to one level, with intuitive titles that predict their contents.
- Hide unavailable items, don't dim them (macOS exception: Cut, Copy, and Paste may appear dimmed).
- Put the most frequently used items where people encounter them first; the menu may open above or below the selection, so item order may need to reverse.
- Show keyboard shortcuts in main menus only, never in context menus.
- In iOS, iPadOS, and visionOS, list destructive items last and mark them `destructive` (red text).
- Skip menu titles unless one clarifies the menu's effect (e.g. "3 Messages Selected" for a bulk action).
- Use the same standard icons as the system for common actions (Copy, Share, Delete).

Canonical implementations: SwiftUI `contextMenu(menuItems:)`, UIKit `UIContextMenuInteraction`, AppKit `popUpContextMenu(_:with:for:)`.

**Platform deltas:**
- iOS/iPadOS: Provide a context menu or an edit menu for an item, not both. iPadOS: consider a context menu in empty areas for object creation (e.g. New Folder in Files). The menu can show a graphical preview of the target content — make it a condensed version of the actual content, and match the preview's clipping path to its image shape so corners don't jump during the reveal animation (`UIContextMenuInteractionDelegate`).
- macOS: Sometimes called a *contextual* menu.
- visionOS: Consider a context menu instead of a panel or inspector window for frequent functionality. Avoid menu heights exceeding the window height — system controls sit above and below the window edges.
- tvOS: No additional considerations. Not supported in watchOS.

## Pull-down buttons
*Last changed: 2022-09*

**Purpose:** A pull-down button displays a menu of items or actions directly related to the button's purpose; choosing an item closes the menu and performs the action.

**Use it when / not when:**
- Use when: a menu can clarify a button's target or customize its behavior (e.g. Add → what to add; Sort → which attribute; Back → which location).
- Prefer a pop-up button when: presenting mutually exclusive choices that aren't commands.
- Prefer plain buttons/toggles/switches when: the menu would hold only one or two items.

**Best practices:**
- Don't hide all of a view's actions in one pull-down button — primary actions must stay discoverable.
- Aim for at least three menu items to make opening the menu worthwhile; avoid long menus that slow item-finding.
- Show a menu title only if it adds meaning; usually the button content plus item labels suffice.
- Mark destructive items (red text) and require confirmation — the system shows an action sheet (iOS) or popover (iPadOS) to confirm or cancel.
- Add an icon or image after an item label only when it clarifies meaning; prefer SF Symbols for alignment at every scale.

Canonical implementations: SwiftUI `MenuPickerStyle`, UIKit `showsMenuAsPrimaryAction`, AppKit `pullsDown`.

**Platform deltas:**
- iOS/iPadOS: A More (ellipsis) pull-down button can hold items that don't need prominent placement, but the ellipsis icon hurts predictability — weigh space savings against discoverability.
- macOS/visionOS: No additional considerations. Not supported in tvOS or watchOS.

## Pop-up buttons
*Last changed: 2023-10*

**Purpose:** A pop-up button displays a menu of mutually exclusive options; after a choice, the menu closes and the button can update to show the current selection.

**Use it when / not when:**
- Use when: presenting a flat list of mutually exclusive options or states, especially when space is limited and options needn't always be visible.
- Prefer a pull-down button when: offering a list of actions, letting people select multiple items, or including a submenu.

**Best practices:**
- Provide a useful default selection — the button shows the default until people choose.
- Let people predict the options without opening the menu, via an introductory label or a button label describing its effect.
- Include a Custom option if occasionally needed items would otherwise clutter the interface; explanatory text can appear below the list.

Canonical implementations: SwiftUI `MenuPickerStyle`, UIKit `changesSelectionAsPrimaryAction`, AppKit `NSPopUpButton`.

**Platform deltas:**
- iPadOS: In a popover or modal view, consider a pop-up button instead of a disclosure indicator for a list item with a small, well-defined set of options — avoids a detail-view round trip.
- iOS/macOS/visionOS: No additional considerations. Not supported in tvOS or watchOS.

## Edit menus
*Last changed: 2023-06*

**Purpose:** An edit menu lets people change selected content (text, images, files, contact cards, charts, map locations) in the current view, with related commands like Copy, Select, Translate, and Look Up; in iOS, iPadOS, and visionOS the system detects the selection's data type and may add related actions (e.g. Get Directions for an address).

**Use it when / not when:**
- Use when: people act on selected content with standard editing commands.
- Prefer the system-provided edit menu over a custom one — a custom menu with the same commands is redundant and confusing (standard commands: `UIResponderStandardEditActions`).

**Best practices:**
- Use the system-defined reveal interactions (touch and hold, double-tap, pinch and hold in visionOS, secondary click) — never a custom gesture for a standard task.
- Show only contextually relevant commands; remove or dim ones that don't apply (no Copy/Cut without a selection, no Paste with an empty pasteboard).
- List custom commands near related system commands (e.g. custom formatting after the system format section); avoid too many custom commands.
- Let people select and copy noneditable content text (captions, statuses), but not control labels.
- Support undo and redo — edit menus act without confirmation.
- Avoid other controls that duplicate edit-menu functions.
- Differentiate deletion commands when necessary: Delete behaves like the Delete key; Cut copies to the pasteboard first.
- Label custom commands with short verbs or verb phrases.

Canonical implementations: UIKit `UIEditMenuInteraction`, AppKit `NSMenu`.

**Platform deltas:**
- iOS: Compact horizontal bar on touch-and-hold or double-tap; a trailing chevron expands it into a context menu.
- iPadOS: Compact horizontal style for touch; opens directly as a context menu for keyboard/pointer. Ensure the menu works in both styles. Adjust placement if the default position (above/below the selection, with a system pointer indicator) covers important content — you can move the menu but not change its shape or pointer.
- macOS: Editing commands appear in a context menu during editing and in the menu bar's Edit menu (see The menu bar > Edit menu for ordering).
- visionOS: Opens via pinch and hold as a horizontal bar or as a context menu; no additional considerations. Not supported in tvOS or watchOS.

## Action sheets

**Purpose:** An action sheet is a modal view presenting choices related to an action people intentionally initiate.

**Use it when / not when:**
- Use when: offering choices related to an intentional action (e.g. canceling a draft → Delete Draft / Save Draft).
- Prefer an alert when: telling people about a problem or unexpected situation — alerts confirm or cancel but don't offer additional choices, and arrive unexpectedly.
- Prefer a menu when (iOS/iPadOS): people deliberately reveal options; an action sheet appears in response to an action that needs clarifying choices.

**Best practices:**
- Use sparingly — action sheets interrupt the current task.
- Keep titles to a single line; provide a message only if the title plus context isn't enough.
- Provide a Cancel button when an action might destroy data; place it at the bottom (watchOS: upper-left corner). SwiftUI confirmation dialogs include Cancel by default.
- Style destructive buttons as destructive and place them at the top, where they're most noticeable.

Canonical implementations: SwiftUI `confirmationDialog(_:isPresented:titleVisibility:actions:)`, UIKit `UIAlertController.Style.actionSheet`.

**Specs:**

watchOS button styles:

| Style | Meaning |
|---|---|
| Default | No special meaning |
| Destructive | Destroys user data or performs a destructive action |
| Cancel | Dismisses the view without acting |

| Attribute | Value |
|---|---|
| watchOS max buttons (incl. Cancel) | 4 |
| watchOS max non-Cancel choices | 3 |

**Platform deltas:**
- iOS/iPadOS: Avoid letting an action sheet scroll — more buttons mean slower choices, and scrolling risks accidental taps.
- watchOS: System style includes a title, optional message, Cancel button, and one or more additional buttons; appearance varies by device.
- macOS/tvOS: No additional considerations. Not supported in visionOS.

## Activity views

**Purpose:** An activity view (share sheet) presents sharing activities (e.g. messaging), actions (e.g. Copy, Print), and frequently used apps for the current context, appearing as a sheet or popover; the system lists app-specific actions before cross-app/system ones, and people can edit the action list.

**Use it when / not when:**
- Use when: people choose the Share button — the standard, expected entry point. Don't offer an alternative route to the same activities.

**Best practices:**
- Don't duplicate system-provided actions; if app-specific functionality is similar, give it a distinguishing title (e.g. "Print Transaction").
- Prefer SF Symbols for custom activity icons; center custom interface icons in an area of about 70x70 pixels.
- Title custom actions with a single verb or brief verb phrase; don't include the company or product name (a share activity's title — typically a company name — appears below its icon instead).
- Exclude system tasks that don't apply (e.g. Print in an app that can't print); show only contextually relevant custom tasks.
- Share/action extensions: prefer the system composition view for share extensions; include the app name and familiar interface elements for action extensions; keep interaction to a few steps; avoid stacking modal views above the extension (an alert may be necessary); a share extension automatically uses the app icon, while an action extension benefits from a symbol or task-identifying icon.
- The activity view dismisses as soon as the extension's task completes — continue lengthy work in the background and surface status in the main app; notify only about problems, never mere completion.

Canonical implementations: UIKit `UIActivityViewController`, `UIActivity`.

**Platform deltas:**
- iOS/iPadOS: Share and action extensions appear in the share sheet via the Action button.
- macOS: No activity view, but share extensions (Share toolbar button or Share in a context menu) and action extensions (pointer-over embedded content, toolbar button, or Finder quick actions) still work on a Mac.
- visionOS: No additional considerations. Not supported in tvOS or watchOS.
