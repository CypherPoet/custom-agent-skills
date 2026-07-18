# Inputs

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Inputs pages: Gestures, Focus and selection, Keyboards, Virtual keyboards, Playing haptics, Digital Crown, Apple Pencil and Scribble, Camera Control, Action button, Game controls, Remotes, Eyes, Gyroscope and accelerometer.

**Contents:** [Gestures](#gestures) · [Focus and selection](#focus-and-selection) · [Keyboards](#keyboards) · [Virtual keyboards](#virtual-keyboards) · [Playing haptics](#playing-haptics) · [Digital Crown](#digital-crown) · [Apple Pencil and Scribble](#apple-pencil-and-scribble) · [Camera Control](#camera-control) · [Action button](#action-button) · [Game controls](#game-controls) · [Remotes](#remotes) · [Eyes](#eyes) · [Gyroscope and accelerometer](#gyroscope-and-accelerometer)

### Gestures
*Last changed: 2024-09*

**Purpose:** A gesture is a physical motion a person uses to directly affect an object in an app or game, made on a touchscreen, in the air, or on a trackpad, mouse, remote, or game controller.

**Best practices:**
- Give people more than one way to interact; don't assume a specific gesture is available (voice, keyboard, Switch Control).
- Respond to gestures consistent with expectations; don't repurpose familiar gestures (tap, swipe) for app-unique actions, or invent gestures for standard actions (button activation, scrolling).
- Handle gestures responsively and provide immediate feedback.
- Indicate when a gesture isn't available so people don't think the app froze.
- Add custom gestures only when necessary; keep them discoverable, easy to perform, distinct, and never the only way to do something important.
- Use shortcut gestures to supplement, not replace, standard gestures (still provide a Back button alongside an edge-swipe).
- Avoid conflicting with system-UI gestures (edge swipe in watchOS, hand-roll for system overlays in visionOS); defer system gestures only within games/immersive experiences.

Canonical implementations: SwiftUI `Gestures`, UIKit `UITouch`; visionOS double-tap primary action via `handGestureShortcut(_:isEnabled:)` / `HandGestureShortcut.primaryAction`; visionOS system-overlay deferral via `persistentSystemOverlays(_:)`.

**Specs:**

Standard gestures (system APIs):

| Gesture | Supported in | Common action |
| --- | --- | --- |
| Tap | iOS, iPadOS, macOS, tvOS, visionOS, watchOS | Activate a control; select an item. |
| Swipe | iOS, iPadOS, macOS, tvOS, visionOS, watchOS | Reveal actions/controls; dismiss views; scroll. |
| Drag | iOS, iPadOS, macOS, tvOS, visionOS, watchOS | Move a UI element. |
| Touch (or pinch) and hold | iOS, iPadOS, tvOS, visionOS, watchOS | Reveal additional controls or functionality. |
| Double tap | iOS, iPadOS, macOS, tvOS, visionOS, watchOS | Zoom in/out; primary action on Apple Watch Series 9 and Ultra 2. |
| Zoom | iOS, iPadOS, macOS, tvOS, visionOS | Zoom a view; magnify content. |
| Rotate | iOS, iPadOS, macOS, tvOS, visionOS | Rotate a selected item. |

**Platform deltas:**
- iOS/iPadOS: Extra expected gestures — three-finger swipe (left = undo, right = redo); three-finger pinch (in = copy, out = paste); four-finger swipe switches apps (iPadOS only); shake = undo/redo. Consider simultaneous gesture recognition for games (e.g., joystick + fire buttons).
- macOS: Primary interaction is keyboard and mouse; standard gestures available on Magic Trackpad, Magic Mouse, or a game controller with a touch surface.
- tvOS: Standard gestures via compatible remote, Siri Remote, or game controller with a touch surface.
- visionOS: Two categories — *indirect* (look to target, then pinch fingers from a distance; comfortable at any distance, best for UI/buttons) and *direct* (physically touch an object; best for infrequent close-up use to avoid arm fatigue). Direct gestures: Touch (select/activate), Touch and hold (contextual menu), Touch and drag (move), Double touch (preview/select word), Swipe (reveal/dismiss/scroll), two-hand pinch-drag together/apart (zoom), two-hand pinch-drag circular (rotate). Reserve the area around a person's hand for system overlays (Home indicator, Control Center via hand-roll); don't anchor content to hands. Avoid custom gestures requiring a specific hand or specific body movements/positions. Custom gestures require a Full Space and permission to access hand data (ARKit).

### Focus and selection
*Last changed: 2023-10*

**Purpose:** Focus visually confirms which object an interaction targets, supporting component-based navigation via remote, game controller, or keyboard.

**Use it when / not when:**
- Focus often also selects the item. Separate selection from focus when auto-selecting would cause a distracting context shift (e.g., opening a new view) — as in tvOS, where selecting a focused item activates it.
- Use a focus ring for a text or search field; use a highlight in a list or collection (easier to read a whole highlighted row).

**Best practices:**
- Rely on system-provided focus effects; create custom effects only if absolutely necessary.
- Avoid changing focus without the person's interaction. Exception: when they move focus with a discrete directional device (keyboard, remote, game controller) and the focused item disappears — move focus to a nearby remaining item. Otherwise hide the focus indicator when the focused object disappears.
- Be consistent with the platform: iPadOS/macOS full keyboard access reaches every control, so support focus only for content (list items, text fields, search fields), not buttons/sliders/toggles. tvOS requires bringing focus to every onscreen element.

Canonical implementations: UIKit `UICollectionView`, `UICollectionViewCell`, `UIFocusHaloEffect`, `UIFocusGroupPriority`, `UIFocusEnvironment.focusGroupIdentifier`; AppKit `NSTableView`.

**Platform deltas:**
- iOS: *Not supported.*
- watchOS: *Not supported.*
- iPadOS: Focus system (iPadOS 15+) supports keyboard navigation of text fields, text views, sidebars, collection views, and custom views. Uses *focus groups*: Tab moves focus among groups (reading order, leading→trailing, top→bottom); arrow keys move within a group. Indicate focus via the halo effect (focus ring, customizable to contours/Bézier shapes, repositionable) or the highlighted appearance (text in app accent color, automatic on selected collection-view cells). Make an item primary by raising its priority so it auto-focuses when its group gains focus.
- tvOS: Uses *directional focus* (swipe Siri Remote or arrow keys reach every element). Avoid displaying a pointer; use the focus model for menus/interface. In a full-screen experience, let gestures affect content, not focus. Focusable items have five visually distinct states: unfocused, focused (scales up, elevates, illuminates, animates — supply larger assets), highlighted (instant feedback on choosing), selected (chosen/activated), unavailable (inactive, can't focus).
- visionOS: Same focus system as iPadOS/tvOS for connected input devices (keyboard, game controller). Focus effects are distinct from the hover (eye) effect.

### Keyboards
*Last changed: 2025-06*

**Purpose:** A physical keyboard is an essential input device for text entry, games, and app control; keyboard shortcuts (a primary key plus Control/Option/Shift/Command modifiers) speed up interactions.

**Best practices:**
- Support Full Keyboard Access where possible (iOS, iPadOS, macOS, visionOS) — navigate and activate windows, menus, controls, and system features by keyboard alone.
- Respect standard keyboard shortcuts; don't repurpose them for custom actions (people may rely on Command-Q to quit a game). Only redefine a standard shortcut if its action makes no sense in your app.
- Define custom shortcuts only for the most frequently used app-specific commands.
- Use modifier keys as expected: Command (main modifier), Shift (secondary complement to a related shortcut), Option (sparingly, for less-common/power features), Control (avoid — system uses it widely).
- List multiple modifiers in order: Control, Option, Shift, Command.
- Don't add Shift to a shortcut that uses the upper character of a two-character key (Command-Question mark, not Shift-Command-Slash).
- Don't create a new shortcut by adding a modifier to an unrelated command's shortcut (avoid Shift-Command-Z for something unrelated to undo/redo).
- Let the system localize and mirror shortcuts (auto-mirrors for right-to-left).

Canonical implementations: SwiftUI `KeyboardShortcut`, `Input events`; UIKit `handling key presses` / `UIKeyCommand.discoverabilityTitle`; AppKit `NSApplication.isFullKeyboardAccessEnabled`.

**Specs:**

Modifier keys and symbols:

| Modifier | Symbol | Usage |
| --- | --- | --- |
| Command | ⌘ | Main modifier in a custom shortcut. |
| Shift | ⇧ | Secondary modifier complementing a related shortcut. |
| Option | ⌥ | Sparingly, for less-common commands or power features. |
| Control | ⌃ | Avoid — reserved by many systemwide features. |

(For the full standard-shortcut table — Command-C copy, Command-V paste, Command-Z undo, Shift-Command-3 screenshot, etc. — see Apple's source page; standard shortcuts are too numerous to tabulate here.)

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS: *No additional considerations.*
- watchOS: *Not supported.*
- visionOS: App shortcuts appear in a shortcut interface shown when holding Command on a connected keyboard — a flat list per system category (File, Edit, View), showing only available commands that have shortcuts. Write descriptive shortcut titles (no submenu context). A virtual keyboard overlay appears above the physical keyboard with typing completion.

### Virtual keyboards
*Last changed: 2025-06*

**Purpose:** On devices without physical keyboards, the system offers virtual keyboards with task-optimized key sets (e.g., an email keyboard with "@" and ".com"); virtual keyboards don't support keyboard shortcuts.

**Use it when / not when:**
- Use a custom *input view* for app-specific entry available only inside your app (replaces the system keyboard while in your app).
- Use a *custom keyboard* (app extension) to expose keyboard functionality systemwide (a novel input method or an unsupported language). Works in any app except secure text and phone-number fields.

**Best practices:**
- Choose a keyboard type matching the content; specify semantic meaning so the system refines corrections.
- Consider customizing the Return key type to clarify the action (e.g., a search Return key).
- Custom input view: make its benefit obvious, and play the standard keyboard sound on key taps (people can disable in Settings > Sounds).
- Custom keyboard: provide an obvious way to switch keyboards (people expect the Globe key); don't duplicate system features (Emoji/Globe, Dictation keys appear automatically); consider an in-app tutorial but don't put help content inside the keyboard itself.

Canonical implementations: SwiftUI `keyboardType(_:)`, `textContentType(_:)`, `submitLabel(_:)`, `ToolbarItemPlacement`; UIKit `UIKeyboardType`, `UITextContentType`, `UIReturnKeyType`, `UIResponder.inputViewController`, `inputAccessoryView`, `UIKeyboardLayoutGuide`, `UIDevice.playInputClick()`.

**Platform deltas:**
- macOS: *Not supported.*
- iOS/iPadOS: Use the keyboard layout guide so UI and keyboard work together and important elements stay visible. Place custom controls above the keyboard only when relevant; apply Liquid Glass to a custom control view (standard toolbars adopt it automatically) and use the layout guide plus standard padding.
- tvOS: Shows a linear virtual keyboard when a text field is selected with the Siri Remote; shows a digit-specific keyboard for digit entry views.
- visionOS: System virtual keyboard supports direct and indirect gestures, appears in a separate movable window — don't account for its location in your layout.
- watchOS: A keyboard shows if the screen is large enough; otherwise people use Dictation or Scribble. You can't change keyboard type but can set the text field's content type (via `textContentType(_:)`). People can also enter text via a paired iPhone.

### Playing haptics
*Last changed: 2024-05*

**Purpose:** Haptics engage the sense of touch to complement visual and auditory feedback, played by built-in engines (iPhone Taptic Engine, Apple Watch, Force Touch trackpad) or external devices (game controllers, Apple Pencil Pro, some trackpads).

**Best practices:**
- Use system-provided haptic patterns per their documented meanings; don't repurpose a pattern — use a generic or custom pattern instead.
- Use haptics consistently to build a clear cause-and-effect association.
- Prefer haptics that complement other feedback; match intensity/sharpness of a haptic to the animation it accompanies.
- Avoid overusing haptics; prefer short haptics for discrete events over long-running haptics (continuous/long haptics on Apple Pencil Pro don't help and make holding it less pleasant).
- Make haptics optional (people can turn off/mute) and ensure the app works without them.
- Ensure haptic vibration doesn't disrupt camera, gyroscope, or microphone features.
- Custom haptics build from *transient* events (brief taps/impulses) and *continuous* events (sustained vibrations), each with controllable *sharpness* and *intensity*; combine with optional audio.

Canonical implementations: Core Haptics; UIKit `UIFeedbackGenerator`; AppKit `NSHapticFeedbackPerformer`; WatchKit `WKHapticType`; game controllers via `Playing Haptics on Game Controllers`.

**Specs:**

iOS feedback-generator patterns:

| Category | Pattern | Meaning |
| --- | --- | --- |
| Notification | Success | A task/action completed. |
| Notification | Warning | A task/action produced a warning. |
| Notification | Error | An error occurred. |
| Impact | Light | Collision of small/lightweight objects. |
| Impact | Medium | Collision of medium objects. |
| Impact | Heavy | Collision of large/heavyweight objects. |
| Impact | Rigid | Collision of hard/inflexible objects. |
| Impact | Soft | Collision of soft/flexible objects. |
| Selection | Selection | A UI element's values are changing. |

watchOS haptics: Notification, Up (value rose above a threshold), Down (value dropped below a threshold), Success, Failure, Retry, Start (activity began), Stop (activity ended), Click (dial-click sensation for progress increments — overusing dilutes/confuses).

macOS Magic Trackpad patterns (on drag or force click): Alignment (item snaps into alignment, reaches min/max/start/end), Level change (movement between discrete pressure levels), Generic (general fallback).

**Platform deltas:**
- iOS: Standard components (toggles, sliders, pickers) play Apple-designed system haptics by default; otherwise use a feedback generator for notification/impact/selection patterns.
- macOS: On a Magic Trackpad, an app can play alignment/level-change/generic haptics during drag or force click.
- watchOS: Apple Watch Series 4+ provides Digital Crown haptics; default linear detents as the Crown turns; defines the named haptic set above.

### Digital Crown
*Last changed: 2023-12*

**Purpose:** The Digital Crown is a key hardware input for Apple Vision Pro and Apple Watch, used for navigation, scrolling, and operating controls.

**Best practices (Apple Watch):**
- Anchor your app's navigation to the Digital Crown (watchOS 10+); orient list, tab, and scroll views vertically, and back Crown interactions with corresponding touchscreen interactions.
- Consider using the Crown to inspect data where navigation isn't needed (e.g., World Clock scrubbing time of day).
- Provide visual feedback for Crown interactions; without it people assume the Crown does nothing.
- Match interface update speed to the speed the person turns the Crown; avoid updating so fast it's hard to select values.
- Use default haptic detents when they fit; turn off detents or switch tables to linear detents (instead of row-based) when they don't match your animation or row heights.

Canonical implementations: WatchKit `WKCrownDelegate`.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS: *Not supported.*
- Apple Vision Pro: Use the Crown to adjust volume, adjust immersion level (portal/Environment/Full Space), recenter content, open Accessibility settings, and exit to the Home View. visionOS apps don't receive direct Digital Crown information.
- Apple Watch: Turning generates data for scrolling and controls. watchOS 10+ makes it the primary navigation input — widgets in the Smart Stack on the watch face, vertical movement through apps on the Home Screen, switching paginated tabs and scrolling within apps. Most models provide linear haptic detents as the Crown turns a set distance.

### Apple Pencil and Scribble
*Last changed: 2024-05*

**Purpose:** Apple Pencil enables precise drawing, handwriting, and markup on iPad and works as a pointer; Scribble converts Apple Pencil handwriting to text in any text field via on-device recognition.

**Best practices:**
- Support behaviors people expect from real marking tools (e.g., writing in margins).
- Let people choose when to switch between Apple Pencil and finger; make all controls respond to Apple Pencil so it never seems unresponsive. (Scribble supports Apple Pencil only.)
- Let people make a mark the instant Apple Pencil touches the screen — no button or mode first.
- Respond to Apple Pencil sensing: tilt (altitude), force (pressure), orientation (azimuth), and barrel roll; affect continuous properties like ink opacity or brush size via pressure.
- Provide visual feedback showing a direct connection with the touched content; don't affect distant content.
- Design for both left- and right-handed use; avoid placing controls a hand may obscure, or let people reposition them.
- Hover: use it to preview the mark the current tool will make; avoid continuously changing the preview by height; avoid using hover to initiate actions (especially destructive); prefer previewing a mid-range value (extremes like max pressure occlude, min pressure is invisible); show squeeze/modifier-revealed menus near the marking point; prefer restricting hover previews to Apple Pencil, not a pointing device.
- Double tap (supported models): default toggles current tool/eraser; people can set it to toggle current/previous tool, show/hide the color picker, or nothing — respect their setting; offer custom double-tap behavior with a control to enter it, off by default; avoid using double tap for content-modifying or destructive actions (it can fire accidentally).
- Squeeze (Apple Pencil Pro): treat as a single quick gesture performing a discrete (not continuous) action; show revealed UI near the tip; keep actions nondestructive and easy to undo; note people may map squeeze to an App Shortcut.
- Barrel roll (Apple Pencil Pro): use only to modify marking behavior (e.g., rotate a highlighter mark), never for navigation or controls.
- Scribble: works by default in standard text components (text fields, text views, search fields, editable web fields) except password fields; don't require tapping a custom field first; avoid autocompletion text and hide placeholder text while writing; keep the text field stationary and prevent autoscroll while writing/editing; give enough space to write (enlarge the field before/after writing, not during).
- Custom drawing (PencilKit): prevent dynamic Dark Mode color adjustment when drawing over existing content (PDF/photo) so markup stays sharp; in a compact environment show custom undo/redo buttons (the tool picker omits them) and consider supporting the 3-finger undo/redo gesture.

Canonical implementations: PencilKit, PaperKit; UIKit `UIScribbleInteraction`, `UIIndirectScribbleInteraction`; hover via `Adopting hover support for Apple Pencil`.

**Platform deltas:**
- iOS/macOS/tvOS/visionOS/watchOS: *Not supported.*

### Camera Control
*Last changed: 2024-09*

**Purpose:** The Camera Control (iPhone 16 and iPhone 16 Pro) gives direct hardware access to an app's camera experience and shows an overlay for adjusting camera controls.

**Best practices:**
- Use SF Symbols (no custom symbols) to represent control functionality; symbols don't reflect current state — see the Camera & Photos section of the SF Symbols app.
- Keep control names short (labels follow Dynamic Type; long names obscure the viewfinder).
- Include units/symbols with slider values for context (EV, %, custom string) via `localizedValueFormat`.
- Define prominent values for sliders (frequently chosen or evenly spaced, like zoom increments) via `prominentValues` so sliding lands on them.
- Make space for the overlay; it occupies screen area adjacent to the Camera Control in portrait and landscape — keep UI outside those areas and maximize the viewfinder.
- Minimize viewfinder distractions; don't duplicate controls in both your UI and the overlay.
- Enable/disable controls per camera mode (e.g., disable video controls when taking photos); you can't add/remove controls at runtime.
- Arrange controls with common ones toward the middle, lesser-used ones on the sides; the system remembers the last control used.
- Allow launching your experience from anywhere via a locked camera capture extension (locked device, Home Screen, or other apps).

**Interaction model:** Light press opens the overlay; light double-press views available controls; after selecting a control, slide a finger on the Camera Control to adjust its value. Two control types — *slider* (range of values) and *picker* (discrete options). System-provided standard controls include zoom factor and exposure bias.

Canonical implementations: AVFoundation `AVCaptureControl`, `AVCaptureSlider` (`localizedValueFormat`, `prominentValues`); LockedCameraCapture.

**Platform deltas:**
- iPadOS/macOS/watchOS/tvOS/visionOS: *Not supported.*

### Action button
*Last changed: 2023-09*

**Purpose:** The Action button (supported iPhone and Apple Watch models) gives quick access to a favorite feature — running an App Shortcut or system function the person assigns in setup or Settings.

**Best practices:**
- Support the Action button with your app's essential functions (e.g., "Start Egg Timer"); don't offer an App Shortcut that just opens your app — the system already provides that.
- Write a short label per action: title-style capitalization, begins with a verb, present tense, no articles/prepositions, max three words ("Start Race", not "Start the Race").
- Let the system show people how to configure it; don't repeat the guidance Settings already provides.

**Platform deltas:**
- iPadOS/macOS/tvOS/visionOS: *Not supported.*
- iOS: Let people use actions without leaving their context via Live Activities and custom snippets (e.g., "Set Timer" prompts for duration then shows a Live Activity countdown rather than opening Clock).
- watchOS: First press can drop a waypoint, start a dive, or begin a specific workout; the button also supports secondary actions (mark a segment, advance a multi-part workout). Offer a secondary function that supports/advances the primary action (people often act without looking); limit secondary functions to avoid cognitive load. Prefer subsequent presses for additional functionality, not stopping a function (offer stop within your UI). Pause the current function when people press the Action button and side button together — except in diving apps, where pausing a dive may be dangerous.

### Game controls
*Last changed: 2025-06*

**Purpose:** Game controls cover input from physical game controllers and platform default interactions (touch, remote, keyboard, mouse); support both to reach the widest audience.

**Best practices:**
- Support the platform's default interaction method as a fallback even when supporting game controllers (every iPhone/iPad has touch, Mac has keyboard+pointer, Apple TV has a remote, Vision Pro has eyes+hands).
- Touch controls: show virtual controls only when they help (games with many actions or movement); place buttons within thumb reach, clear of the Home indicator and Dynamic Island, secondary controls (menus) at the top; always include visible and tactile press states (glow plus sound/haptics); use action-representing symbols, not abstract shapes or controller labels (A/X/R1); show/hide controls per context; combine actions into single controls using double tap / touch and hold; map movement to the left side (dynamic thumbstick where the thumb lands) and camera to the right side (direct touch to pan).
- Physical controllers: tell people about controller requirements (tvOS/visionOS can require one — App Store shows a "Game Controller Required" badge; check for presence and prompt gracefully); auto-detect a paired controller and its profile; customize onscreen content to match the connected controller's labels/colors/symbols; prefer SF Symbols over text for controller elements (Gaming category).
- Keyboards: prioritize single-key commands (first letter of a menu item, Space for the main action); test binding comfort on an Apple keyboard (remap a non-Apple Control binding to Command, next to Space and the WASD keys); account for key proximity; let players customize key bindings.

**Specs:**

Minimum touch-control sizes:

| Control | Minimum size |
| --- | --- |
| Frequently used controls | 44×44 pt |
| Less important controls (e.g., menus) | 28×28 pt |

Controller button → UI behavior (outside gameplay, all platforms):

| Button | Expected UI behavior |
| --- | --- |
| A | Activates a control |
| B | Cancels an action / returns to previous screen |
| Left shoulder | Navigates left to a different screen/section |
| Right shoulder | Navigates right to a different screen/section |
| Left/right thumbstick | Moves selection |
| Directional pad | Moves selection |
| Home/logo | Reserved for system controls |
| Menu | Opens game settings or pauses gameplay |

Canonical implementations: Touch Controller framework; Game Controller framework (`GCControllerElement`, `GCRequiresControllerUserInteraction`); virtual controls via `Adding virtual controls to games that support game controllers in iOS`.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS: *No additional considerations.*
- watchOS: *Not supported* (physical game controllers).
- visionOS: Match spatial game controller behavior (e.g., PlayStation VR2 Sense) to hand input — look at an object and press a trigger to interact indirectly, or reach out and press a trigger to interact directly.

### Remotes

**Purpose:** The Siri Remote is the primary input for Apple TV, combining a clickpad and touch surface with dedicated buttons to navigate, browse, play/pause, and select from across the room.

**Best practices:**
- Prefer standard gestures for standard actions; don't redefine remote behaviors outside gameplay.
- Be consistent with the tvOS focus experience — move focus in the same direction as the gesture.
- Provide clear feedback for gestures (e.g., resting a thumb hints where to swipe down to reveal an info area).
- Define new gestures only when it makes sense (mostly within games).
- Differentiate press (intentional — choose, confirm, initiate) from tap (navigation, more info); avoid responding to inadvertent taps, especially during live video playback.
- Use tap position (up/down/left/right) for navigation/gameplay only when intuitive and discoverable.
- On Back, open the parent of the current screen (the Home Screen at the top level; otherwise per app hierarchy, not necessarily the previous screen). During active gameplay, open an in-game pause menu instead (Back again closes it and resumes); press-and-hold Back always goes to the Home Screen.
- Respond to Play/Pause to play, pause, or resume media.
- If a live-viewing app provides an EPG, respond to guide/browse buttons by opening it and to page up/down by paging through it; while content plays, respond to page up/down by changing channels. If no EPG, the system routes these to the default guide app.

**Specs:**

Button behaviors (app vs. game):

| Button/area | App | Game |
| --- | --- | --- |
| Touch surface (swipe) | Navigates; changes focus. | Directional-pad behavior. |
| Touch surface (press) | Activates a control/item; navigates deeper. | Primary button behavior. |
| Back | Returns to previous screen; exits to Home Screen. | Pauses/resumes gameplay; returns to previous screen / main game menu / Home Screen. |
| Play/Pause | Activates / pauses / resumes media playback. | Secondary button behavior; skips intro video. |

Canonical implementations: TVServices `Providing Channel Navigation`.

**Platform deltas:**
- iOS/iPadOS/macOS/visionOS/watchOS: *Not supported.*

### Eyes
*Last changed: 2024-06*

**Purpose:** In visionOS, people look at a virtual object to target it; the system shows a *hover effect* confirming the element is interactive and ready for an indirect gesture like tap.

**Best practices:**
- Always give people multiple ways to interact; support accessibility features.
- Design for visual comfort: keep needed objects within the field of view; avoid requiring multiple quick eye adjustments across a large area or multiple depth levels.
- Place content at a comfortable viewing distance — at least one meter away for content viewed over time; avoid very close placement unless interaction is brief.
- Prefer standard UI components, which respond consistently to looking.
- Minimize visual distractions and movement, especially in peripheral vision (revealing content near a looked-at button can pull the eye away).
- Give enough space around items: at least a 16-point margin around each item, or place items so their centers are at least 60 points apart.
- Avoid a repeating pattern/texture filling the field of view (eyes lock onto elements at apparent different depths); use it in a smaller area.
- Use subtle cues (centering, gentle motion, increased contrast, color/scale variation) to encourage looking at the likely target — noticeable but not flashy.
- Prefer rounded shapes for interactive items (eyes drift toward corners); give a multi-element interactive component one overall containing shape visionOS can highlight.
- Custom hover effects run out of process: define two states (effect / no effect); the system can't tell you when someone is looking, so the effect can't run gaze-dependent code or perform the action. Use them to emphasize special moments, not to replace sufficient standard effects. Choose a delay — no delay (default; for subtle/inviting effects like a slider knob), short delay (look then quickly interact, like tab-bar expansion), long delay (additional info like a tooltip). Keep one or more primary views unchanged across both states for stability; test while wearing Apple Vision Pro.

Canonical implementations: visionOS `Adopting best practices for privacy and user preferences`; supports RealityKit entities for custom hover effects.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/watchOS: *Not supported.*

### Gyroscope and accelerometer

**Purpose:** On-device gyroscopes and accelerometers supply real-time data about a device's physical movement for motion-based app and game experiences.

**Best practices:**
- Use motion data only to offer a tangible benefit (fitness feedback, enhanced gameplay); don't gather data just to have it.
- Outside active gameplay, avoid using accelerometers/gyroscopes for direct manipulation of the interface — motion gestures can be hard to replicate precisely, physically challenging, and battery-intensive.

Canonical implementations: Core Motion (`Getting processed device-motion data`).

**Availability:** Accelerometer and gyroscope data in iOS, iPadOS, and watchOS; tvOS apps can use gyroscope data from the Siri Remote.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: *No additional considerations.*
