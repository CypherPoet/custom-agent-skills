# Decision Helpers — Choosing the Right Component

> Source: Apple Human Interface Guidelines (reorganized from this skill's distilled component references)
> Last synced: 2026-06-16

Quick "which one?" tables for confusable Apple components. Each row states when to reach for an option over its alternatives, drawn from the per-component HIG guidance. For full best practices and platform deltas, open the linked component reference.

## Tab Bar vs Sidebar vs Segmented Control
Top-level section navigation, many-section navigation, or switching closely-related subviews.

| Choose… | When… | Instead of… |
|---|---|---|
| Tab bar | Navigating between top-level app sections; space is limited or you want more screen for content | A sidebar (which suits many navigation options and ample space) |
| Sidebar | The app has a complex information structure with many sections, and there's ample vertical and horizontal space | A tab bar (for many apps a sidebar-adaptable tab bar provides both rather than forcing a choice) |
| Segmented control | Switching between closely related subviews, or offering closely related choices that affect an object, state, or view (iOS/iPadOS) | A tab bar (reserved for completely separate app sections) |

*See: `components-navigation-bars.md`.*

## Sheet vs Popover vs Alert vs Action Sheet
Which modal/transient presentation fits the task.

| Choose… | When… | Instead of… |
|---|---|---|
| Sheet | The task is scoped, brief, and tied to the parent view (supply info to complete an action, attach a file, choose a save location) | A popover (sheets handle a self-contained scoped task, not transient anchored content) |
| Popover | Exposing a small amount of related information or a few related tasks temporarily, anchored to the control that revealed it (reserve for wide views; in compact/iPhone views it adapts to a full-screen sheet) | An alert when you need to show a warning — people can miss or accidentally close a popover |
| Alert | Critical information is needed right away — confirming an uncommon, un-undoable destructive action, or interrupting with critical actionable info | An action sheet (alerts confirm or cancel but don't offer additional choices, and arrive unexpectedly) |
| Action sheet | Offering choices related to an action people intentionally initiate (e.g. canceling a draft → Delete Draft / Save Draft) | An alert (which reports a problem rather than offering choices) |

*See: `components-presentation.md`, `components-menus-actions.md`, `patterns-navigation.md`.*

## Pull-Down Button vs Pop-Up Button vs Menu vs Context Menu
Commands tied to a button, mutually-exclusive selection, or revealed commands for an item.

| Choose… | When… | Instead of… |
|---|---|---|
| Pull-down button | A menu can clarify a button's target or customize its behavior; offering a list of actions, selecting multiple items, or including a submenu (aim for at least three items) | A pop-up button (which is for mutually exclusive choices that aren't commands) |
| Pop-up button | Presenting a flat list of mutually exclusive options or states, especially when space is limited and options needn't always be visible | A pull-down button (used for actions, multi-select, or submenus) |
| Menu | Revealing commands, options, or states on interaction in a space-efficient way | — |
| Context menu | People need quick access to the commands most likely needed for a selected item, hidden by default until revealed | An edit menu when the item needs text/content-editing commands (on iOS/iPadOS provide one or the other, never both) |

*See: `components-menus-actions.md`.*

## Picker vs Pop-Up Button vs Stepper vs Segmented Control
Choosing among values by list length and entry style.

| Choose… | When… | Instead of… |
|---|---|---|
| Picker | Offering medium-to-long lists of items to choose single or multipart values | A pull-down button (a picker adds too much visual weight for a fairly short list) |
| Pop-up button | The list is a fairly short set of mutually exclusive options | A picker (too heavy for short lists) or a list/table (used for very large sets) |
| List or table | Presenting a very large set of values (adjustable height; tables can include an index) | A picker (which suits medium-to-long lists) |
| Stepper | Small, few-tap changes to an incremental value (pair it with a field showing the current value) | A text field when large or widely varying specific values are likely (e.g. number of copies) |
| Segmented control | Closely related choices that affect an object, state, or view, with no more than about five to seven segments | A pop-up button or picker when there are more options than fit as equal-width segments |

*See: `components-selection-input.md`, `components-navigation-bars.md`, `components-menus-actions.md`.*

## List/Table vs Collection vs Outline View vs Column View
Text rows, a visual grid, or hierarchical navigation (macOS).

| Choose… | When… | Instead of… |
|---|---|---|
| List or table | Presenting text — the row format makes text easy to scan and read; expressing information hierarchy for navigation | A collection (which suits images and widely varying item sizes) |
| Collection | Showing image-based content, items varying widely in size, or a large number of images | A table (simpler and more efficient for text in a scrollable list) |
| Outline view (macOS) | Displaying text-based hierarchical content, often on the leading side of a split view (adds disclosure triangles for nested levels) | A table (used when data isn't hierarchical) |
| Column view (macOS) | A deep data hierarchy where people navigate back and forth frequently between levels and you don't need the sorting a list or table provides | An outline view or table (when you need sorting, or fewer levels) |

*See: `components-content-views.md`.*

## Progress Indicator: Determinate vs Indeterminate; Gauge vs Progress
Known vs unknown duration, and ongoing measurement vs task progress.

| Choose… | When… | Instead of… |
|---|---|---|
| Determinate indicator | The task has a well-defined duration (e.g. file conversion) — prefer it whenever possible so people can decide whether to wait, restart, or abandon | An indeterminate indicator (reserved for unquantifiable tasks) |
| Indeterminate indicator (spinner) | The task is unquantifiable (e.g. loading or syncing complex data); switch to determinate once the process becomes measurable | A determinate indicator when there's no measurable progress to report |
| Gauge | Displaying a specific numerical value within a range, optionally giving context about the range itself | A progress indicator (which is transient and shows operation progress, not an ongoing measured value) |

*See: `components-status-indicators.md`.*

## Toggle: Switch vs Checkbox vs Radio Buttons (macOS placement)
Per-platform on/off and mutually-exclusive selection.

| Choose… | When… | Instead of… |
|---|---|---|
| Switch (iOS/iPadOS) | The control sits in a list row (no label needed; the row provides context) | A button-that-behaves-like-a-toggle, which is what to use outside a list |
| Switch (macOS) | Emphasizing a setting that deserves more visual weight (e.g. controlling a group of settings); place in the window body, not the window frame | A checkbox — and in general, don't replace an existing checkbox with a switch |
| Checkbox (macOS) | Presenting a hierarchy of settings (alignment + indentation show dependencies), or a single on/off setting | A switch (use a checkbox for hierarchies; prefer a checkbox for a single on/off setting) |
| Radio buttons (macOS) | More than two mutually exclusive options (typically groups of 2–5) | Checkboxes (which allow multiple selections); use a pop-up button instead of more than about five radio buttons |

*See: `components-selection-input.md`.*

## Activity View (Share Sheet) vs Custom Share UI
Sharing activities and actions for the current context.

| Choose… | When… | Instead of… |
|---|---|---|
| Activity view (share sheet) | People choose the Share button — the standard, expected entry point for sharing activities, actions, and frequently used apps | A custom alternative route to the same activities (don't offer one) |
| Custom activity / action | App-specific functionality the system doesn't provide — give it a distinguishing title (e.g. "Print Transaction") | Duplicating a system-provided action |

*See: `components-menus-actions.md`.*
