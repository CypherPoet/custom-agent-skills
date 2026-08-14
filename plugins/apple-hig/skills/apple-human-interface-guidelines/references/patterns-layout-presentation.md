# Patterns — Layout & Presentation

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Patterns pages: Right to left, Drag and drop, Undo and redo, Loading, Offering help, Collaboration and sharing, File management.

## Table of Contents

| Section | Covers |
|---|---|
| [Right to left](#right-to-left) | Layout mirroring, directional assets, text alignment, and exceptions for right-to-left languages |
| [Drag and drop](#drag-and-drop) | Let people move or duplicate selected content by dragging a selection from a source location to a destination |
| [Undo and redo](#undo-and-redo) | Reversible actions, undo affordances, grouping, and confirmation boundaries |
| [Loading](#loading) | Design content loading so it doesn't disrupt or negatively impact the experience |
| [Offering help](#offering-help) | Provide contextual help when necessary, directly related to the precise action or task people are doing right now |
| [Collaboration and sharing](#collaboration-and-sharing) | Content sharing, participant roles, presence, permissions, and collaboration feedback |
| [File management](#file-management) | Let document-based apps support documents and files that people expect to create |

## Right to left

**Purpose:** Support right-to-left languages like Arabic and Hebrew by reversing your interface as needed to match the reading direction of the related scripts.

**Best practices:**
- System UI frameworks support RTL by default and flip system components automatically; if you use standard elements and layouts you may need no changes. Follow these rules only to fine-tune layout or adapt currencies, numerals, or math symbols per locale.
- Text alignment: adjust to match interface direction if the system doesn't (left-aligned LTR → right-aligned RTL).
- Align a paragraph (three or more lines) based on its language, not the current context; continue aligning one- and two-line blocks to the current context.
- Use consistent alignment for all items in a list, including items in a different script.
- Don't reverse the order of numerals within a specific number (e.g. "541", phone, credit card) — digits keep the same order regardless of language or surrounding content.
- Reverse the order of numerals that show progress or counting direction (progress bars, sliders, rating controls, ordered sequences); never flip the numerals themselves.
- Flip controls that show progress from one value to another (sliders, progress indicators); also reverse the positions of accompanying begin/end glyphs or images.
- Flip controls that navigate or access items in a fixed order (e.g. back button points right in RTL; next/previous flip).
- Preserve the direction of a control that refers to an actual direction or points to an onscreen area (a "to the right" control always points right).
- Visually balance adjacent Latin and RTL scripts: increase RTL (Arabic/Hebrew) font size by about 2 points when next to uppercased Latin text, since those scripts lack uppercase.
- Avoid flipping photographs, illustrations, and general artwork — flipping changes meaning and may violate copyright; create a new version if content is tied to reading direction.
- Reverse the positions of images when their order is meaningful (chronological, alphabetical, favorite).
- Flip interface icons that represent text or reading direction (left-aligned bars → right-aligned).
- Consider a localized version of an interface icon that displays actual text (SF Symbols ships Latin/Hebrew/Arabic variants of signature, rich-text, and I-beam pointer symbols); if letters communicate a non-reading concept, design a text-free alternative.
- Flip an interface icon that shows forward or backward motion (e.g. speaker sound waves emanate from the reading-start side).
- Don't flip logos or universal signs and marks (e.g. the checkmark) — confusing and possibly illegal.
- In general, avoid flipping interface icons that depict real-world objects (clocks, right-handed tools); flip only when the object indicates directionality.
- Before flipping a complex custom icon, weigh its components and overall balance: keep design-language pieces consistent (SF Symbols reuses the same backslash for prohibition in LTR and RTL); flip a component or its position only when needed to keep the icon sensible and balanced; preserve a tool's handedness while flipping the base image if necessary.

Canonical implementations: SF Symbols (RTL variants and localized symbols; specify directionality on custom symbols via `Creating custom symbol images for your app`). SwiftUI `Preparing views for localization`.

**Platform deltas:**
- iOS/iPadOS, macOS, tvOS, visionOS, watchOS: No additional considerations.

## Drag and drop

*Last changed: 2023-10*

**Purpose:** Let people move or duplicate selected content by dragging a selection from a source location to a destination, within or across containers and apps.

**Use it when / not when:**
- Move when: source and destination containers are the same (e.g. dragging text within a document).
- Copy when: source and destination differ (e.g. dragging an image between documents); dragging between apps always copies.

**Best practices:**
- Support drag and drop throughout your app as much as possible; system components (text fields, text views) give built-in support.
- Offer alternative ways to accomplish drag-and-drop actions (e.g. menu commands). On iOS/iPadOS, expose sources and destinations to assistive tech via `accessibilityDragSourceDescriptors` and `accessibilityDropPointDescriptors`.
- Decide move vs. copy deliberately; favor the behavior most people expect and the one least likely to cause frustration or data loss.
- Support multi-item drag and drop when it makes sense. iOS, iPadOS, macOS, visionOS support selecting multiple items and dragging as a group; macOS also allows items from several apps; iPadOS lets people add items mid-drag without stopping.
- Prefer letting people undo a drag-and-drop operation; ask for confirmation before a drop that can't be undone (Finder confirms drops into write-only folders); offer a way to reverse results when undo isn't possible (Photos lets people cancel sharing after dropping into a shared stream).
- Consider offering multiple versions of dragged content, ordered highest- to lowest-fidelity (e.g. PDF vector, lossless PNG, lossy JPEG) so the destination picks the best it accepts.
- Consider supporting spring loading: controls (buttons, segmented controls) activate when content is dragged over them. On Mac with Magic Trackpad, force-click while holding content; on iPad, hover while holding.
- Providing feedback: display a translucent drag image as soon as people drag a selection about three points; show it until they drop.
- Modify the drag image to help predict the result if it adds clarity (e.g. expand to default photo size); use drag flocking to group/ungroup multiple items; avoid constant, radical changes.
- Show whether a destination can accept dragged content (insertion point, highlight) or show no feedback / an explicit "not allowed" image like SF Symbols `circle.slash`; show cues only while content is over the destination; with multiple destinations, cue one at a time.
- On an invalid destination or failed drop, provide visual feedback (item returns to source, or scales up and fades out to evaporate).
- Accepting drops: scroll a destination's contents when an item is dragged over a scrolling container with lots of content; stop auto-scroll when the drag leaves the container (system text views/fields do this by default).
- When there's a choice, pick the richest version of dropped content your app can accept; fall back to a simpler version (e.g. image) if unsupported.
- Extract only the relevant portion of dropped content if necessary (Mail takes only name and email from a dropped contact).
- When a physical keyboard is attached, check for the Option key at drop time: holding Option forces a same-container drag to copy; releasing it before drop results in a move.
- Provide feedback when dropped content needs time to transfer (progress indicator; placeholder at the drop location in collections/lists/tables); the system can alert on time-consuming transfers between apps.
- Provide feedback when a drop initiates a task or action (e.g. printing) and keep people informed of progress.
- Apply appropriate styling to dropped text: preserve original attributes when both sides support the same styles; otherwise apply the destination's style.
- After a drop, maintain the content's selection state in the destination and update the source: a same-container move removes it from the original; a same-container copy removes the selection from the original; cross-container drags deselect the source.

Canonical implementations: UIKit `Drag and drop`, AppKit `Drag and Drop`, `File Provider`. visionOS: associate an `NSUserActivity` with draggable content to handle drops into empty space.

**Platform deltas:**
- iOS, iPadOS: Let people perform multiple simultaneous drag activities — in iPadOS, sequentially add items to an in-progress drag session, provide flocking feedback, and accept multiple simultaneous drops.
- macOS: Consider letting people drag content into the Finder in a format your app can reopen (Calendar exports an event as `.ics`); output to a *clipping* when needed (unrelated to the Clipboard). Let people drag a *background selection* from an inactive window without activating it, and drag individual items from an inactive window without affecting its existing selection. Consider displaying a badge (filled oval with a count) during multi-item drags and updating it when only a subset is accepted. Consider changing the pointer (copy, drag link, disappearing item, operation not allowed) to indicate the drop result. As much as possible, let people select and drag with a single motion.
- visionOS: When possible, launch your app to handle content dropped into empty space (dropping a URL launches Safari; Quick Look–supported content launches Quick Look).
- Not supported in tvOS or watchOS.

## Undo and redo

**Purpose:** Give people easy ways to reverse many types of actions, helping them explore and experiment safely while learning an interface or task.

**Best practices:**
- Help people predict the results of undo and redo: on iPhone, describe the result in the shake alert; in menu items, modify labels to identify the result (e.g. "Undo Typing", "Redo Bold").
- Show the results of an undo or redo — if the affected content is offscreen, scroll to reveal it so people don't think the action had no effect and repeat it.
- Let people undo multiple times; avoid arbitrary limits. People expect to undo every action since a logical step like opening or saving.
- Consider giving people the option to revert multiple changes at once (a batch of related adjustments, or all changes since opening/saving).
- Provide undo and redo buttons only when necessary; people expect system-supported ways (Edit menu, keyboard shortcuts, iPhone shake). If you add dedicated buttons, use standard system symbols and place them in a toolbar.

Canonical implementations: Foundation `UndoManager`.

**Platform deltas:**
- iOS, iPadOS: Avoid redefining standard gestures (three-finger swipe undo/redo, iPhone shake). The undo/redo alert title auto-prefixes "Undo " or "Redo " (with trailing space); supply an additional word or two (e.g. "Undo Name", "Redo Address Change").
- macOS: Place undo and redo in the Edit menu and support standard shortcuts — Command–Z for undo, Shift–Command–Z for redo.
- visionOS: No additional considerations.
- Not supported in tvOS or watchOS.

## Loading

*Last changed: 2025-06*

**Purpose:** Design content loading so it doesn't disrupt or negatively impact the experience — ideally finishing before people become aware of it.

**Best practices:**
- Show something as soon as possible; a blank wait reads as a problem. Show placeholder text, graphics, or animations and replace them as content arrives.
- Let people do other things while content loads (load in the background; a game can load the next level while players read about it or use an in-game menu).
- If loading is unavoidably long, give people something interesting to view (gameplay hints, tips, new features); gauge remaining time so the placeholder content is neither too brief nor repeated.
- Improve installation and launch time by downloading large assets in the background; consider the `Background Assets` framework to schedule downloads (level packs, 3D models, textures) right after install, during updates, or at nondisruptive times.
- Showing progress: clearly communicate that content is loading and roughly how long it will take. Use a *determinate* progress indicator when you know the duration, an *indeterminate* one when you don't.
- For games, consider a custom loading view with animations and elements matching the game's style.

**Platform deltas:**
- iOS, iPadOS, macOS, tvOS, visionOS: No additional considerations.
- watchOS: Avoid showing a loading indicator as much as possible — aim to display content immediately. When content needs a second or two, a loading indicator is better than a blank screen.

## Offering help

*Last changed: 2023-12*

**Purpose:** Provide contextual help when necessary, directly related to the precise action or task people are doing right now.

**Best practices:**
- Let your app's tasks inform the help type: an inline view for simple one- or two-step tasks; a tutorial for complex or multistep tasks. Make help easy to dismiss or avoid.
- Use relevant, consistent language and images appropriate to the platform and context (don't show a game controller for Siri Remote users; don't tell people to "click" on iPhone or "tap" a menu item on Mac).
- Make all help content inclusive.
- Don't bloat help by explaining how standard components or patterns work; describe the specific action a standard element performs in your app. For unique controls or nonstandard input use (e.g. holding the Siri Remote rotated 90 degrees), orient people quickly, preferring animation or graphics over lengthy text.
- Creating tips: a tip is a small, transient view briefly describing how to use a feature, best for new or less obvious features.
- Use the most appropriate tip type: a *popover* tip to preserve content flow; an *inline* tip to keep surrounding info visible; an *annotation*-style inline tip when pointing to a specific UI element; a *hint*-style tip when not tied to specific UI.
- Use tips for simple features people can complete in a few steps; a feature needing more than three actions is probably too complicated for a tip.
- Make tips short, actionable, and engaging — one or two sentences, action-oriented, no promotional or off-context content.
- Define eligibility rules (parameter-based or event-based) so tips reach only people who benefit; with more than one tip, set a reasonable display frequency (e.g. once every 24 hours).
- If an image or symbol is associated with the feature, consider including it and prefer the filled variant; if the tip already points directly to that image in the UI, don't repeat the same image in the tip.
- Use buttons to direct people to settings or more information (e.g. open the relevant settings, or a setup flow / additional resources).

Canonical implementations: `TipKit` (tips). macOS/visionOS tooltips: SwiftUI `help(_:)`, AppKit `NSHelpManager`.

**Platform deltas:**
- iOS, iPadOS, tvOS, watchOS: No additional considerations.
- macOS, visionOS: A *tooltip* (a *help tag* in user docs) is a small transient view describing how to use a component. On Mac (including iPhone/iPad apps) it appears on pointer hover; in visionOS it appears on look or hover. Describe only the control the person indicates interest in. Explain the action or task the control initiates, often beginning with a verb ("Restore default settings"). Avoid repeating the control's name. Be brief — limit to roughly 60–75 characters (localization changes length); use sentence fragments and omit articles. Use sentence case and omit ending punctuation unless your app's style requires it. Consider context-sensitive tooltips (different text per control state).

## Collaboration and sharing

*Last changed: 2023-12*

**Purpose:** Provide simple, responsive collaboration and sharing that lets people engage with content while communicating effectively with others, using system sharing interfaces and Messages integration.

**Best practices:**
- Works whether you implement collaboration via CloudKit, iCloud Drive, or a custom solution; a custom infrastructure must support universal links to offer these features.
- Place the Share button in a convenient location like a toolbar. The system share sheet (iOS 16) and sharing popover (iPadOS 16, macOS 13) let people choose a file-sharing method and set permissions for a new collaboration. In SwiftUI, present a `ShareLink` that opens the system share sheet.
- Customize the share sheet or sharing popover to offer the file-sharing types you support. CloudKit "send copy": pass both the file and your collaboration object. iCloud Drive supports "send copy" by default. Custom collaboration: include a file (or a plain-text representation) in your collaboration object.
- Write succinct phrases summarizing supported sharing permissions (e.g. "Only invited people can edit", "Everyone can make changes"); the system uses your summary in a button that reveals the sharing options.
- Provide a minimal set of simple sharing options that streamline setup (who can access, edit vs. read, whether collaborators can add participants); keep custom choices few and grouped for at-a-glance understanding.
- Prominently display the system-provided Collaboration button as soon as collaboration starts — it reminds people the content is shared and identifies who's sharing; place it next to the Share button.
- Provide custom actions in the collaboration popover only if needed. The popover has three sections: top lists collaborators with Messages/FaceTime buttons, middle holds your custom items, bottom holds the manage-shared-file button. Offer only essentials.
- Customize the title of the modal's collaboration-management button if it makes sense ("Manage Shared File" by default). CloudKit sharing provides a management view; otherwise create your own.
- Consider posting collaboration event notifications in Messages (content change, membership change, participant mention) with a universal link to the relevant view, via `SWHighlightEvent`.

Canonical implementations: SwiftUI `ShareLink`, `Shared with You` / `SWHighlightEvent`. visionOS also supports immersive sharing through SharePlay.

**Platform deltas:**
- iOS, iPadOS, macOS: No additional considerations.
- visionOS: By default the system supports screen sharing for an app in the Shared Space by streaming the current window; if anyone transitions to a Full Space while sharing, the system pauses the stream until the app returns to the Shared Space.
- watchOS: In a SwiftUI app, use `ShareLink` to present the system share sheet.
- Not available in tvOS.

## File management

*Last changed: 2024-06*

**Purpose:** Let document-based apps support documents and files that people expect to create, edit, save, browse, and manage throughout the system.

**Best practices:**
- People browse files outside apps too: Finder on Mac; Files app on iPhone, iPad, and Apple Vision Pro. watchOS and tvOS don't provide a document-browsing interface, since people don't typically create or manage documents there.
- Creating and opening files: use app menus and keyboard shortcuts for creating and opening documents. iPadOS shows New/Open in the Command-key shortcuts interface; macOS shows them in the File menu. Regardless, include an Add (+) button to create a new document; in macOS put the add action in the File menu.
- If you require a custom file browser, support understanding of the platform's file system: open to the most relevant location (Documents, iCloud, or most recent) but let people view the rest of the file system.
- Saving work: help people be confident work is always preserved unless they cancel or delete it. Avoid requiring an explicit save — autosave periodically while editing and when closing a file or switching apps.
- Hide file extensions by default but let people view them; reflect the current choice in all save/open interfaces.
- Quick Look previews: use a Quick Look viewer to let people preview a file even when your app can't open it. Consider implementing a Quick Look generator if your app produces custom file types so the Finder, Files, and Spotlight can show previews.

Canonical implementations: SwiftUI `Documents`, `DocumentGroupLaunchScene` (iOS/iPadOS document launcher), `File Provider`, `Finder Sync`.

**Platform deltas:**
- iOS, iPadOS: Starting in iOS 18 / iPadOS 18, document-based apps can use the system *document launcher* — a full-screen browse/open/create experience — via `DocumentGroupLaunchScene`. It has three parts: a *title card* (app title plus two app-specific buttons), a background image with surrounding *accessory* images, and a sheet with a file browser and optional controls. Assign the title card's buttons to your most important functions (primary typically creates a new document; e.g. Numbers uses "Start Writing" and "Choose a Template"). Provide a background clearly distinct from accessories and title card (solid color, gradient, or pattern; avoid complex images). Be mindful of accessory placement (front/back for depth) while keeping the app name and both buttons visible; avoid clutter; test across screen sizes and orientations. Use animation sparingly (gentle, repeating "breathe" or "sway"). A *file provider app extension* can present a custom interface for importing, exporting, opening, and moving documents: display only context-appropriate documents (a PDF editor lists only PDFs) and optionally show modification dates, sizes, and local/remote status; let people select a destination when exporting/moving and optionally add subdirectories; avoid a custom top toolbar since the extension's modal view already has one.
- macOS: People have strong associations with the Finder's familiar browsing experience — use the default file browser unless you have an important reason for a custom one. Make a custom file-opening interface convenient ("open recent", filtering criteria, multi-select); in an open panel you can retitle the Open button (e.g. "Insert"). Provide a save interface to change a file's name, format, or location (new documents are "Untitled" until named; default to a logical save location; offer a format choice when you support multiple). Consider extending the Save dialog with a custom accessory view (e.g. Mail's option to include attachments). A *Finder Sync app extension* expresses sync status and control in the Finder: display badges for sync status, provide custom contextual menu items (favoriting, password-protection), and custom toolbar buttons (initiate a sync). Help people avoid losing work if they turn off autosaving (via "Ask to keep changes when closing documents" in Desktop & Dock settings): show unsaved changes and present a save dialog on close/quit/log-out/restart. When autosaving is off, show a dot on the window's close button and next to the document name in the Window menu (don't show the dot when autosave is on); you can append "Edited" to the title-bar title, removing it as soon as autosave occurs or the user saves.
- tvOS, visionOS, watchOS: No additional considerations.
