# Platform — macOS

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG platform pages: Designing for macOS, The menu bar, Dock menus, Mac Catalyst.

## Contents
- [Designing for macOS](#designing-for-macos)
- [The menu bar](#the-menu-bar)
- [Dock menus](#dock-menus)
- [Mac Catalyst](#mac-catalyst)

### Designing for macOS

**Purpose:** Design for a large-display, pointer-and-keyboard, multi-window environment where people run several apps at once for tasks ranging from quick edits to hours of deep concentration.

**Best practices:**
- **Display.** Assume a large, high-resolution display; people extend their workspace across additional displays (including iPad). Leverage the space to present more content in fewer nested levels and with less modality, while keeping a comfortable information density.
- **Ergonomics.** Typical viewing distance is roughly 1–3 feet, with the device stationary on a desk or table.
- **Windows.** Let people resize, hide, show, and move windows to fit their work style and device configuration. Support full-screen mode for a distraction-free context.
- **Inputs.** Support any combination of input modes — keyboards, pointing devices, game controls, Siri. Help people use high-precision input for pixel-perfect selections and edits, and handle keyboard shortcuts to accelerate keyboard-only work styles.
- **Menu bar.** Give people easy access to all of your app's commands through the menu bar.
- **Customization.** Support personalization — let people customize toolbars, configure windows to show the views they use most, and choose interface colors and fonts.
- **App switching.** People frequently keep multiple apps open; support smooth transitions between active and inactive states.

### The menu bar
*Last changed: 2025-06*

**Purpose:** The bar at the top of the screen displaying an app's top-level menus; Mac users rely on it to learn what an app does and find commands, so a consistent menu bar experience is essential.

**Best practices:**
- **Ordering.** Support the default system-defined menus and their ordering; people expect a familiar order. App-specific menus appear between View and Window. List app-specific menus from most to least general/commonly used, and reflect your app's hierarchy.
- **Visibility.** Always show the same set of menu items so people learn what the app supports. If an item isn't actionable, disable it — never hide it.
- **Icons + shortcuts.** Represent actions with the same standard icons the system uses (Copy, Share, Delete). Support the standard keyboard shortcuts for the standard items you include (Copy, Cut, Paste, Save, Print); define custom shortcuts only when necessary.
- **Titles.** Prefer short, one-word menu titles — they scan easily and take little space. If more than one word is needed, use title-style capitalization.
- **App menu.** Holds app-wide items (not task/document/window-specific). The app name appears in bold to identify the active app. Show About first, in its own group (separator after it). Use a short app name of 16 characters or fewer for About / Hide / Quit. Settings is for app-level settings only.
- **File menu.** Manages files/documents; rename or remove it if the app handles no file types. Prefer Duplicate over Save As / Export / Copy To. Autosave periodically. Determine whether Find items belong here instead of Edit (e.g. searching for files).
- **View menu.** Customizes window appearance regardless of window type. Provide it even for a subset of functions — at minimum the Enter/Exit Full Screen item. Each show/hide title must reflect the current view state (Show Toolbar vs Hide Toolbar).
- **Window menu.** Provide it even with a single window so Full Keyboard Access users can reach Minimize and Zoom. Don't use Zoom to enter/exit full screen — that's the View menu's job. List open windows in alphabetical order; avoid listing panels.
- **Help menu.** At the trailing end. Using the Help Book format auto-adds a search field. Keep the item count small; separate primary help from additional items (registration, release notes).
- **Dynamic menu items.** A modifier key (Control/Option/Shift/Command) changes an item's behavior (e.g. Minimize → Minimize All). Never make a dynamic item the only way to do something — they're hidden by default. Use them primarily in menu-bar menus; require only a single modifier key.
- **macOS specifics.** The Apple menu is always first on the leading side and can't be modified or removed. Menu bar extras sit on the trailing side; the system hides/shows them to make room for app menus, so don't rely on their presence or location. A menu bar extra should display a menu (not a popover) on click, and people — not the app — decide whether it appears. Also expose functionality via a Dock menu, which is always available while the app runs.

**Specs:**

| Item | Value |
| --- | --- |
| Menu bar height | 24 pt |
| About / Hide / Quit app name length | 16 characters or fewer |

Standard top-level menu order (when present): _YourAppName_ → File → Edit → Format → View → app-specific menus → Window → Help. The Apple menu is always leftmost; menu bar extras sit on the trailing side.

### Dock menus

**Purpose:** The menu revealed by secondary-clicking an app's Dock icon; presents both system-provided and custom items, and is always available while the app runs (unlike menu bar extras).

**Best practices:**
- **Standard items.** System-provided items vary by whether the app is open (e.g. Safari shows items like viewing a current window or creating a new window).
- **Custom items.** Prefer high-value custom items — list currently/recently open windows for quick jumps, plus a few actions most useful when the app isn't frontmost or has no open windows (e.g. Mail's get-new-mail and compose).
- **Redundancy.** Not everyone uses the Dock menu, so offer the same commands elsewhere (menu bar menus or the app's UI).
- **Labeling.** Label items succinctly and organize them logically, as with all menus.

### Mac Catalyst
*Last changed: 2023-05*

**Purpose:** Bring an iPad app to the Mac. Good candidates already support drag and drop, keyboard navigation and shortcuts, multitasking (Split View, Slide Over, Picture in Picture), and multiple scenes/windows. Apps whose essential features need gyroscope, accelerometer, rear camera, HealthKit, ARKit, or whose primary function is marking/handwriting/navigation may not suit the Mac.

**Best practices:**
- **Choose an idiom.** Xcode defaults to the iPad idiom ("Scale Interface to Match iPad") — consistent with minimal layout change, but iPadOS views and text scale down to 77% (17 pt iPad text → 13 pt). Switch to the Mac idiom for sharper text/artwork, more Mac-like elements, and better performance in graphics-intensive apps — most beneficial when the app shows lots of text, detailed artwork, or animation. The Mac idiom renders text and views at 100%, so audit the layout, adjust font sizes (prefer text styles over fixed sizes), and consider a separate asset catalog for Mac assets.
- **Don't just reskin.** Go beyond displaying the iPadOS layout in a macOS window; adopt Mac patterns and conventions regardless of idiom.
- **Navigation.** Replace an iPad tab bar with a split view + sidebar (preferred, and consistent across iPad and Mac) or a segmented control (works for flat hierarchies). Keep important tab-bar items reachable by listing them in the macOS View menu. Offer Next/Previous buttons in addition to swipe gestures.
- **Layout.** Adopt a top-down flow — put the most important actions and content near the top. Move iPad toolbar controls into the macOS window toolbar (and list their commands in the menu bar). Split a single column into multiple columns; use regular-width/regular-height size classes and reflow side-by-side as the window resizes. Present an inspector next to content instead of a popover. Relocate buttons from screen side/bottom edges (the iPad reachability rationale doesn't apply on Mac).
- **Menus.** Mac users expect every command in the persistent menu bar and a context menu on every object. Pop-up/pull-down button menus and context menus convert automatically to a macOS appearance; look for additional places to add context menus (called _contextual_ menus on Mac).
- **App icons.** Create a macOS version of the app icon with the lifelike rendering style macOS expects.
- **Appearance.** Limit customizations to standard macOS ones similar to those in iPadOS — not all iPadOS control customizations exist on macOS.

**Specs:**

Free macOS features gained via Mac Catalyst: pointer interactions, keyboard focus/navigation, window management, toolbars, rich text interaction (copy/paste, editing context menus), file management, menu bar menus, app settings in the system Settings app. System UI takes a Mac appearance (split view, file browser, activity view, form sheet, contextual actions, color picker).

| Idiom | Text/view render scale | Notes |
| --- | --- | --- |
| iPad ("Scale Interface to Match iPad", default) | 77% (17 pt → 13 pt) | Minimal layout change; slightly less detail |
| Mac | 100% | Sharper; audit layout and font sizes |

Automatic gesture conversion:

| iPadOS gesture | Mouse | Trackpad |
| --- | --- | --- |
| Tap | Left or right click | Click |
| Touch and hold | Click and hold | Click and hold |
| Pan | Left click and drag | Click and drag |
| Pinch | — | Pinch |
| Rotate | — | Rotate |
