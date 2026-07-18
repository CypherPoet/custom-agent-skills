# Components — Presentation

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Components pages: Sheets, Popovers, Alerts, Panels, Windows.

**Contents:** [Sheets](#sheets) · [Popovers](#popovers) · [Alerts](#alerts) · [Panels](#panels) · [Windows](#windows)

### Sheets
*Last changed: 2026-03*

**Purpose:** A sheet presents a scoped task closely related to the current context — requesting specific information or letting people complete a simple task before returning to the parent view.

**Use it when / not when:**
- Use when: the task is scoped, brief, and tied to the parent view (supply info to complete an action, attach a file, choose a save location).
- Use a nonmodal view (split view in visionOS, panel in macOS, nonmodal sheet in iOS/iPadOS) when: presenting supplementary items that affect the main task in the parent view.
- Prefer a full-screen modal (`UIModalPresentationStyle.fullScreen`) in iOS/iPadOS when: showing videos, photos, camera views, or multistep editing tasks.
- Prefer a new window or full-screen mode in macOS when: the task is self-contained (e.g. editing a document) or for viewing media.
- Prefer a Full Space in visionOS when: people dive into content or a task.
- Prefer a panel (macOS) when: people repeatedly provide input and observe results (e.g. find and replace).

**Best practices:**
- Display only one sheet at a time from the main interface; close the first before showing a second, and re-show it after the second is dismissed.
- Always pair a Done button with a Cancel button (or a Back button to move to a previous step) — never rely on Done alone.
- Avoid showing Cancel, Done, and Back together.
- Anatomy buttons: Cancel/Close dismisses without saving; Done dismisses after completing/saving; Back navigates to a previous step or parent (not for dismissing).
- A sheet is always modal in macOS, tvOS, visionOS, and watchOS. In iOS/iPadOS it can be modal or nonmodal.

Canonical implementations: SwiftUI `sheet(item:onDismiss:content:)`, UIKit `UISheetPresentationController`, AppKit `presentAsSheet(_:)`.

**Specs:**

| Detent | Height | Notes |
| --- | --- | --- |
| large | Fully expanded sheet height | Supported automatically by all sheets |
| medium | About half the fully expanded height | Designed for iPhone; opt-in |
| custom | One or more custom detent values | App-defined |

Adding `medium` lets the sheet rest at both heights; specifying only `medium` prevents expansion to full height. For developer guidance: `detents`, `prefersGrabberVisible`.

**Platform deltas:**
- iOS/iPadOS: For single-view sheets, Cancel goes on the leading edge of the top toolbar; Done on the trailing edge. In multi-step flows, the first step shows Cancel (leading) and an inactive Done (trailing); subsequent steps replace Cancel with Back; the final confirmation step activates Done. Resizable sheets use detents and a grabber (drag to resize, tap to cycle detents; works with VoiceOver). Support swiping vertically to dismiss; if unsaved changes exist, use an action sheet to confirm. Consider supporting the medium detent for progressive disclosure (e.g. share sheet); display only at full height when content needs the room (e.g. Messages/Mail compose). In iPadOS, prefer the page or form sheet presentation styles (default size, centered on a dimmed background); see `UIModalPresentationStyle`.
- macOS: A cardlike view with rounded corners floating on the dimmed parent window. Present in a reasonable default size; people don't expect to resize, but support resizing where useful. Let people interact with other app windows without dismissing the sheet; bring the parent window (and its modeless document-related panels) forward when the sheet opens.
- visionOS: Floats in front of and dims the parent window. Avoid emerging from the bottom edge — prefer centering in the field of view. Use a default size that helps people retain context; avoid covering most/all of the window; consider letting people resize.
- watchOS: A full-screen, semitransparent view that slides over current content (system blurs and desaturates the covered content). Use only when a modal task requires a custom title or custom content presentation; otherwise use an alert or action sheet. Keep interactions brief and occasional; don't use for navigation. If changing the default label, prefer SF Symbols and avoid labels that look like a page/app title (people won't know how to dismiss).
- tvOS: No additional considerations.

### Popovers

**Purpose:** A popover is a transient view that appears above other content when people click or tap a control or interactive area, exposing a small amount of related information or functionality.

**Use it when / not when:**
- Use when: exposing a small amount of information or a few related tasks temporarily; you want more room for content without a permanent sidebar or panel.
- Prefer an alert when: you need to show a warning — people can miss or accidentally close a popover.
- Prefer a full-screen modal (e.g. a sheet) in compact (iPhone) views; popovers adapt to a full-screen sheet in a compact environment.

**Best practices:**
- Position the popover so its arrow points as directly as possible to the element that revealed it; avoid covering that element or essential content.
- Use a Close button (Cancel/Done) only for confirmation or guidance; otherwise a popover closes when people click/tap outside it or select an item. If multiple selections are possible, keep it open until people explicitly dismiss it or tap outside.
- Always save work when automatically closing a nonmodal popover; discard work only on an explicit Cancel.
- Show one popover at a time — never cascade or nest popovers; close the open one before showing a new one.
- Don't show another view over a popover, except an alert.
- When possible, let people close one popover and open another with a single click/tap (useful when several bar buttons each open a popover).
- Avoid making a popover too big — only big enough to display its contents and point to its source; the system may resize it to fit.
- Animate size changes between condensed and expanded views so it doesn't look like a replacement popover.
- Avoid the word "popover" in help documentation; refer to the specific task or selection.

Canonical implementations: SwiftUI `popover(isPresented:attachmentAnchor:arrowEdge:content:)`, UIKit `UIPopoverPresentationController`, AppKit `NSPopover`.

**Platform deltas:**
- iOS/iPadOS: Avoid displaying popovers in compact views; reserve them for wide views. For compact views, use full screen via a full-screen modal (e.g. a sheet) instead.
- macOS: You can make a popover detachable — it becomes a separate panel when dragged, staying visible while people interact with other content. Make minimal appearance changes to a detached popover to preserve context.
- visionOS: No additional considerations.
- tvOS: Not supported.
- watchOS: Not supported.

### Alerts
*Last changed: 2024-02*

**Purpose:** An alert is a modal view that gives people critical information they need right away — reporting a problem, warning about destructive action, or confirming an important user-initiated action.

**Use it when / not when:**
- Use when: an uncommon, un-undoable destructive action needs confirmation, or critical actionable information must interrupt the task.
- Don't use merely to provide non-actionable information — find an in-context alternative (e.g. an indicator people can choose to learn more).
- Don't use for common, undoable destructive actions (e.g. deleting an email or file).
- Don't show an alert when your app starts; make important information discoverable another way (e.g. cached/placeholder data plus a nonintrusive label).
- Use an action sheet (not an alert) in iOS/iPadOS to offer choices related to an intentional action.

**Best practices:**
- Use alerts sparingly; each one should offer only essential information and useful actions.
- Write a title that clearly and succinctly describes the situation (what happened, the context, and why); avoid uninformative titles ("Error", "Error 329347 occurred") and titles longer than two lines. Complete-sentence title → sentence-style capitalization with ending punctuation; sentence-fragment title → title-style capitalization, no ending punctuation.
- Include informative text only if it adds value; keep it short, complete sentences, sentence-style capitalization, appropriate punctuation.
- Avoid explaining alert buttons; if guidance is unavoidable, use a term like "choose" and refer to the button by its exact title without quotes.
- Include a text field only if input is needed to resolve the situation (e.g. a secure field for a password).
- Be direct, neutral, and approachable in all alert copy.

**Buttons:**
- Aim for one- or two-word titles describing the result; prefer verbs/verb phrases tied to the alert text ("View All", "Reply", "Ignore"). Use title-style capitalization, no ending punctuation.
- Avoid "OK" as the default button title unless the alert is purely informational; prefer specific titles ("Erase", "Convert", "Clear", "Delete"). In informational alerts only, "OK" can mean acceptance — avoid "Yes"/"No".
- Always title a cancel button "Cancel".
- Place the most likely / default button on the trailing side of a row or at the top of a stack; Cancel goes on the leading side of a row or at the bottom of a stack.
- Use the destructive style only for a destructive button people didn't deliberately choose; don't apply it when the destructive action is the person's original intent (e.g. Empty Trash).
- If there's a destructive action, include a Cancel button; don't make Cancel the default. To force people to read an alert, make no button the default. For a single-button alert that's also the default, use a Done button, not Cancel.

**Specs:**

| Element | Availability |
| --- | --- |
| Title, optional informative text, up to 3 buttons | All platforms |
| Text field | iOS, iPadOS, macOS, visionOS |
| Icon + accessory view | macOS, visionOS |
| Suppression checkbox + Help button | macOS |

| Cancel shortcut | Platform |
| --- | --- |
| Exit to the Home Screen | iOS, iPadOS |
| Escape (Esc) or Command-Period (.) on an attached keyboard | iOS, iPadOS, macOS, visionOS |
| Pressing Menu on the remote | tvOS |

Canonical implementations: SwiftUI `alert(_:isPresented:actions:)`, UIKit `UIAlertController`, AppKit `NSAlert`.

**Platform deltas:**
- iOS/iPadOS: Use an action sheet — not an alert — to offer choices related to an intentional action. Avoid alerts that scroll; keep titles short and messages brief.
- macOS: Automatically displays your app icon (you can supply an alternative icon/symbol). Can configure repeating alerts with a suppression option, append a custom view (`accessoryView`), and include a Help button. Use a caution symbol (e.g. `exclamationmark.triangle`) sparingly — only when extra attention is needed (e.g. unexpected data loss), not for routine overwrite/remove tasks.
- visionOS: In the Shared Space, the alert appears in front of the app's window, slightly forward along the z-axis, and stays anchored to the window if moved. In a Full Space, it's centered in the wearer's field of view. An accessory view must have a maximum height of 154 pt and a 16-pt corner radius.
- tvOS: No additional considerations.
- watchOS: No additional considerations.

### Panels

**Purpose:** In a macOS app, a panel floats above other open windows providing supplementary controls, options, or information related to the active window or current selection.

**Use it when / not when:**
- Use when: giving quick access to controls or information related to the content people are working with (e.g. settings affecting the selected item).
- Use a panel for an inspector (shows details of the currently selected item, updating as the selection changes).
- Use a regular window, not a panel, for an Info window (always maintains the same contents regardless of selection).
- Consider a split view pane for an inspector depending on layout.
- In other platforms, use a modal view to present supplementary content relevant to the current task or selection.

**Best practices:**
- Prefer simple adjustment controls (sliders, steppers); avoid controls requiring text entry or multi-step selection.
- Write a brief title — a noun or noun phrase with title-style capitalization (e.g. "Fonts", "Colors", "Inspector").
- When your app becomes active, bring all open panels to the front regardless of which window was active when a panel opened; hide all panels when your app is inactive.
- Don't include panels in the Window menu's documents list (commands to show/hide are fine).
- In general, don't make a panel's minimize button available.
- Refer to panels by title in menus and help ("Show Fonts", "Show Inspector"); append "window" only when it adds clarity ("Fonts window").
- HUD-style panel (darker, translucent): prefer standard panels; use a HUD only in media-oriented apps (movies, photos, slides), when a standard panel would obscure essential content, or when you don't need controls (most system controls except the disclosure triangle don't match a HUD). Maintain one panel style across mode switches (e.g. keep the HUD when leaving full-screen). Use color sparingly; keep HUDs small and non-obscuring.

Canonical implementations: AppKit `NSPanel`; HUD style via `hudWindow`.

**Platform deltas:**
- macOS: Supported (panels are a macOS component).
- iOS/iPadOS, tvOS, visionOS, watchOS: Not supported.

### Windows
*Last changed: 2025-06*

**Purpose:** A window presents UI views and components in your app or game, defining the visual boundaries of app content and enabling multitasking within and between apps.

**Use it when / not when:**
- A primary window presents the main navigation, content, and associated actions of an app.
- An auxiliary window presents one specific task or area, doesn't allow navigation to other app areas, and typically includes a close button.
- visionOS — prefer a window for a familiar, UI-centric interface; prefer a volume for rich, bounded 3D content (e.g. a game board).

**Best practices:**
- Make windows adapt fluidly to different sizes to support multitasking and multiwindow workflows.
- Choose the right moment to open a new window; avoid opening new windows as default behavior unless it benefits the experience (excess windows create clutter).
- Consider offering "view in a new window" via a context menu or the File menu (`OpenWindowAction`).
- Avoid creating custom window UI — use system-provided windows, frames, and controls; don't replicate the system appearance.
- Use the term "window" in user-facing content (not "scene", which is an implementation term).

Canonical implementations: SwiftUI `Windows` / `WindowGroup`, UIKit `UIWindow`, AppKit `NSWindow`.

**Specs:**

| Property | Value | Platform |
| --- | --- | --- |
| Default window size | 1280×720 pt | visionOS |
| Initial placement | About 2 m in front of the wearer (~3 m apparent width) | visionOS |

**Platform deltas:**
- iPadOS: Windows present full screen (fill the screen, switch via the app switcher) or windowed (freely resizable, multiple onscreen, repositionable; the system remembers size and placement across closes) per Multitasking & Gestures settings. When windowed, window controls sit at the leading edge of the toolbar — move leading toolbar buttons inward so window controls don't hide them. Consider a gesture (e.g. pinch) to open content in a new window; see `collectionView(_:sceneActivationConfigurationForItemAt:point:)` and `UIWindowScene.ActivationInteraction`.
- macOS: Window = frame (above body, may include window controls, a toolbar, and rarely a bottom bar) + body area; drag the frame to move, drag edges to resize. Three states: Main (frontmost, one per app), Key/active (accepts input, one onscreen at a time — may be a panel rather than the main window), Inactive (not foreground; subdued, no vibrancy). Key window uses color in the close/minimize/zoom controls; inactive and non-key main windows use gray. Make custom windows use system-defined appearances. Avoid putting critical info/actions in a bottom bar (window relocation often hides the bottom edge); if used, keep it to a small amount of related info (e.g. Finder's status bar).
- visionOS: Two main window styles — default (a window) and volumetric (a volume); both display 2D and 3D content, and multiple can appear at once in the Shared Space and a Full Space. A window is an upright plane with an unmodifiable "glass" material, close button, window bar, and resize controls; may include a Share button, tab bar, toolbar, and ornaments; uses dynamic scale by default (`DefaultWindowStyle`). Retain the glass background. Default size 1280×720 pt, placed ~2 m in front (~3 m apparent width). Choose an initial shape suiting the content; set minimum and maximum sizes so layout doesn't break (`Positioning and sizing windows`). Minimize the depth of 3D content in a window — the system clips content that extends too far; use a volume for greater depth. A volume (`VolumetricWindowStyle`) displays 2D/3D content viewable from any angle; its close button and window bar shift to face the viewer as they move around it. Prefer a volume for rich 3D content. Place 2D content (via attachments) to look good from multiple angles. Generally use dynamic scaling; use fixed scaling (the default) to represent a real-world object. In visionOS 2+, the system shows a baseplate glow on look to mark a volume's edges; a volume can include one ornament (in addition to a toolbar and tab bar) via an attachment anchor (e.g. `topBack`, `bottomFront`) — avoid placing it on the same edge as a toolbar or tab bar, and prefer only one (`ornament(visibility:attachmentAnchor:contentAlignment:ornament:)`). Choose a baseplate alignment (parallel to floor vs. tilting to match gaze) that suits how people interact with the volume.
- iOS: Not supported.
- tvOS: Not supported.
- watchOS: Not supported.
