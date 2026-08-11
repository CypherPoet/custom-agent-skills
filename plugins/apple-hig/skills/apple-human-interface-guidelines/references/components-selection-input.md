# Components — Selection & Input

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Components pages: Entering data, Text fields, Text views, Combo boxes, Token fields, Pickers, Digit entry views, Sliders, Steppers, Toggles, Disclosure controls, Color wells, Image wells.

**Contents:** [Entering data](#entering-data) · [Text fields](#text-fields) · [Text views](#text-views) · [Combo boxes](#combo-boxes) · [Token fields](#token-fields) · [Pickers](#pickers) · [Digit entry views](#digit-entry-views) · [Sliders](#sliders) · [Steppers](#steppers) · [Toggles](#toggles) · [Disclosure controls](#disclosure-controls) · [Color wells](#color-wells) · [Image wells](#image-wells)

### Entering data
*Last changed: 2023-06*

**Purpose:** Patterns for collecting information from people easily and without mistakes, across all input methods.

**Best practices:**
- Get information from the system whenever possible — don't ask for data you can gather automatically (settings) or by permission (location, calendar).
- Be clear about the data you need: show a placeholder prompt (e.g. "username@company.com") or an introductory label ("Email"); prefill reasonable default values.
- Use a secure text-entry field for sensitive data — obscures input, typically a small filled circle per character (`SecureField`). In tvOS, a digit entry view can obscure numerals (`isSecureDigitEntry`). In visionOS, the system shows entered data to the wearer only; secure fields auto-blur during AirPlay.
- Never prepopulate a password field; always require entry or biometric/keychain auth.
- When possible, offer choices (picker, menu, selection component) instead of requiring text entry.
- Let people provide data by dragging-and-dropping or pasting.
- Dynamically validate field values and give feedback as soon as a problem is detected. For numeric data, use a number formatter (restricts to numeric, can format decimals/percentage/currency).
- When data entry is required, gate the Next/Continue button until the required data is supplied.

Canonical implementations: SwiftUI `SecureField`.

**Platform deltas:**
- iOS/iPadOS, tvOS, visionOS, watchOS: No additional considerations.
- macOS: Consider an expansion tooltip to show the full version of clipped/truncated text in a field (appears on pointer hover); also applies to iOS/iPadOS apps running on a Mac.

### Text fields
*Last changed: 2023-06*

**Purpose:** A rectangular area for entering or editing small, specific pieces of text such as a name or email address.

**Use it when / not when:**
- Use when: requesting a small amount of text (name, email).
- Prefer a text view when: input is larger or multiline.
- Prefer a combo box (macOS) when: pairing text input with a list of choices.

**Best practices:**
- Show a hint via placeholder text ("Email", "Password") that disappears on typing; also include a separate label since the placeholder vanishes.
- Use secure text fields for sensitive data like passwords (`SecureField`).
- Match field size to the anticipated quantity of text.
- Evenly space multiple fields; stack vertically when possible; use consistent widths (e.g. first/last name one width, address/city another).
- Ensure tab order flows logically (system usually handles this automatically).
- Validate when it makes sense: email best validated on switching fields; username/password validated before switching fields.
- Use a number formatter for numeric data (restricts to numeric; can format decimals/percentage/currency) — don't assume presentation, it varies by locale.
- Adjust line breaks per need: default clips overflow; can wrap at character or word level, or truncate (ellipsis) at beginning, middle, or end.
- Consider an expansion tooltip to show full clipped/truncated text on pointer hover.
- In iOS, iPadOS, tvOS, visionOS, show the appropriate keyboard type for the content (numbers, URLs, etc.).
- Minimize text entry in tvOS and watchOS apps; prefer buttons/lists.

Canonical implementations: SwiftUI `TextField` / `SecureField`, UIKit `UITextField`, AppKit `NSTextField`.

**Platform deltas:**
- tvOS, visionOS: No additional considerations.
- iOS/iPadOS: Display a Clear button at the trailing end to erase input. Use images/buttons at field ends — leading end indicates purpose, trailing end offers features (e.g. Bookmarks button).
- macOS: Consider a combo box if pairing text input with a list of choices.
- watchOS: Present a text field only when necessary; prefer a list of options.

### Text views
*Last changed: 2023-06*

**Purpose:** Displays multiline, styled text content that can optionally be editable and can scroll when content overflows.

**Use it when / not when:**
- Use when: text is long, editable, or in a special format (most options for specialized display and text input).
- Prefer a label when: displaying a small amount of non-editable text.
- Prefer a text field when: the small text is editable.

**Best practices:**
- Default content aligns to the leading edge and uses the system label color. In iOS/iPadOS/visionOS, an editable text view shows a keyboard when selected.
- Keep text legible even when mixing fonts/colors/alignments; adopt Dynamic Type; test with accessibility options (e.g. bold text) on.
- Make useful text (error message, serial number, IP address) selectable so people can copy it.

Canonical implementations: SwiftUI `Text`, UIKit `UITextView`, AppKit `NSTextView`.

**Platform deltas:**
- macOS, visionOS, watchOS: No additional considerations.
- iOS/iPadOS: Show the appropriate keyboard type for the content.
- tvOS: Text can be displayed in a text view, but because text input is minimal by design, tvOS uses text fields for editable text instead.

### Combo boxes
**Purpose:** Combines a text field with a pull-down button in one control; people enter a custom value or pick from a predefined list.

**Best practices:**
- Custom values entered are not added to the list of choices.
- Populate the field with a meaningful default value that refers to the hidden choices (need not be the first list item); the field can be empty by default but a default is better.
- Use an introductory label (title-style capitalization, ending with a colon) so people know what items to expect.
- Provide relevant choices alongside the ability to enter a custom value.
- Make sure list items aren't wider than the text field, or they'll truncate.

Canonical implementations: AppKit `NSComboBox`.

**Platform deltas:**
- Not supported in iOS, iPadOS, tvOS, visionOS, or watchOS. (macOS only.)

### Token fields
**Purpose:** A text field that converts entered text into tokens that are easy to select and manipulate (e.g. Mail recipient fields).

**Best practices:**
- Tokens can be selected, dragged to reorder, or moved to another field; can show a suggestion list as people type.
- Add value with a context menu offering options/info about a token (e.g. edit recipient, mark as VIP, view contact card).
- Provide additional ways to convert text into tokens: by default text becomes a token on typing a comma; you can specify added shortcuts such as Return.
- Consider customizing the delay before showing suggested tokens — default is immediate, but too-fast suggestions can distract.

Canonical implementations: AppKit `NSTokenField`.

**Platform deltas:**
- Not supported in iOS, iPadOS, tvOS, visionOS, and watchOS. (macOS only.)

### Pickers
*Last changed: 2023-06*

**Purpose:** Displays one or more scrollable lists of distinct values to choose single or multipart values; values and order depend on device language.

**Use it when / not when:**
- Use when: offering medium-to-long lists of items.
- Prefer a pull-down button when: the list is fairly short (a picker adds too much visual weight).
- Prefer a list or table when: presenting a very large set (adjustable height; tables can include an index).

**Best practices:**
- Use predictable, logically ordered values (e.g. alphabetized country list) so people can move through hidden values quickly.
- Avoid switching views to show a picker; display it in context, below or near the field being edited — typically at the bottom of a window or in a popover.
- For date-picker minutes, default is 60 values (0–59); you can increase the minute interval as long as it divides evenly into 60 (e.g. quarter-hour: 0, 15, 30, 45).

Canonical implementations: SwiftUI `Picker` / `DatePicker`, UIKit `UIDatePicker` / `UIPickerView`, AppKit `NSDatePicker`.

**Specs:**

iOS/iPadOS date picker styles:

| Style | Behavior |
| --- | --- |
| Compact | Button showing editable date/time in a modal view; shows current value in the app's accent color; good when space is constrained |
| Inline | For time only, a button showing wheels of values; for dates and times, an inline calendar view |
| Wheels | Scrolling wheels; also supports data entry via built-in or external keyboard |
| Automatic | System-determined style based on platform and date picker mode |

iOS/iPadOS date picker modes:

| Mode | Shows |
| --- | --- |
| Date | Months, days of the month, years |
| Time | Hours, minutes, optional AM/PM |
| Date and time | Dates, hours, minutes, optional AM/PM |
| Countdown timer | Hours and minutes, max 23 hours 59 minutes; not available in inline or compact styles |

**Platform deltas:**
- visionOS: No additional considerations.
- iOS/iPadOS: Date picker supports four styles (compact, inline, wheels, automatic) and four modes (date, time, date and time, countdown timer); exact values/order depend on device location.
- macOS: Two date picker styles — textual (limited space, specific selections) and graphical (browse a calendar, select a date range, or a clock-face look). See `NSDatePicker`.
- tvOS: Pickers available with SwiftUI `Picker`.
- watchOS: Navigated with the Digital Crown; picker uses the wheels style, including date and time pickers. Configurable with outline, caption, and scrolling indicator. For longer lists, a navigation link displays the picker as a button (`navigationLink`); can scrub with the Digital Crown without tapping.

### Digit entry views
**Purpose:** A full-screen view that prompts for a series of digits (like a PIN) using a digit-specific keyboard, with optional title and prompt above the digit line.

**Best practices:**
- Use secure digit fields (display asterisks instead of entered digits) whenever asking for sensitive data.
- Clearly state the view's purpose with a title and prompt explaining why digits are needed.

Canonical implementations: TVUIKit `TVDigitEntryViewController`.

**Platform deltas:**
- Not supported in iOS, iPadOS, macOS, visionOS, or watchOS. (tvOS only.)

### Sliders
*Last changed: 2023-06*

**Purpose:** A horizontal track with an adjustable thumb that sets a value between a minimum and maximum; the track between minimum and thumb fills with color.

**Best practices:**
- Customize appearance (track color, thumb image/tint, left/right icons) only if it adds value — e.g. small-image icon on the left, large on the right for an image-size slider.
- Use familiar directions: minimum on the leading side, maximum on the trailing side (horizontal); minimum at bottom, maximum at top (vertical).
- Consider supplementing a slider with a text field and stepper so people can see and enter an exact value and increment in whole values.

Canonical implementations: SwiftUI `Slider`, UIKit `UISlider`, AppKit `NSSlider`.

**Platform deltas:**
- Not supported in tvOS.
- iOS/iPadOS: Don't use a slider to adjust audio volume — use a volume view (includes a volume-level slider plus output-device control).
- macOS: Can include tick marks. Linear slider thumb is a narrow lozenge; circular slider thumb is a small circle with tick marks as evenly spaced dots. Use horizontal sliders for a fixed start/end (e.g. opacity 0–100%); use circular sliders for repeating/indefinite values (e.g. rotation 0–360°, or 1440° for four spins). Consider live feedback as the value changes; use a label (sentence-style capitalization, ending with a colon) to introduce a slider. Use tick marks for clarity/accuracy; consider labeling tick marks (often just min and max suffice; periodic labels for nonlinear values); provide a tooltip showing the thumb value on hover.
- visionOS: Prefer horizontal sliders (side-to-side gesture is easier than up-and-down).
- watchOS: Track appears as discrete steps or a continuous bar over a finite range; side buttons increase/decrease by a predefined amount. System shows plus/minus signs by default; create custom glyphs if needed.

### Steppers
**Purpose:** A two-segment control to increase or decrease an incremental value; it doesn't display the value itself, so it sits next to a field showing the current value.

**Best practices:**
- Make the value the stepper affects obvious, since the stepper shows no value.
- Consider pairing a stepper with a text field when large value changes are likely (steppers suit small few-tap changes; a field suits widely varying specific values, e.g. number of copies on a printing screen).

Canonical implementations: UIKit `UIStepper`, AppKit `NSStepper`.

**Platform deltas:**
- iOS/iPadOS, visionOS: No additional considerations.
- Not supported in watchOS or tvOS.
- macOS: For large value ranges, consider supporting Shift-click to change the value by more than the default increment (e.g. 10× the default).

### Toggles
*Last changed: 2024-03*

**Purpose:** Lets people choose between a pair of opposing states (e.g. on/off), using a different appearance per state; styles include switch and checkbox, used differently per platform.

**Use it when / not when:**
- Use when: choosing between two opposing values that affect the state of content or a view.
- Prefer a pop-up button when: supporting other actions such as choosing from a list of items.

**Best practices:**
- All platforms also support buttons that behave like toggles via a different appearance per state (`ToggleStyle`).
- Clearly identify the setting/view/content the toggle affects; in macOS you can supply a label describing the controlled state. A toggle-style button typically uses an interface icon and changes its background per state.
- Make state differences obvious (add/remove a color fill, show/hide background shape, change inner detail like a checkmark or dot); don't rely solely on color.

Canonical implementations: SwiftUI `Toggle`, UIKit `UISwitch`, AppKit `NSButton.ButtonType.toggle` / `NSSwitch`.

**Platform deltas:**
- tvOS, visionOS, watchOS: No additional considerations.
- iOS/iPadOS: Use the switch toggle style only in a list row (no label needed; the row provides context). Change the default green switch color only if necessary (e.g. to the accent color) with enough contrast. Outside a list, use a button that behaves like a toggle, not a switch (e.g. Phone filter button shows a blue highlight when active); avoid a label explaining the button's purpose (`changesSelectionAsPrimaryAction`).
- macOS: Supports switch and checkbox styles plus radio buttons. Use switches, checkboxes, and radio buttons in the window body, not the window frame (avoid in a toolbar or status bar).
  - Switches: Prefer a switch for settings to emphasize (more visual weight; e.g. to control a group of settings) (`switch`). Within a grouped form, consider a mini switch to control a single row's setting for consistent row height; use a regular switch for the primary setting and mini switches for subordinate settings (`GroupedFormStyle`, `ControlSize`). In general, don't replace an existing checkbox with a switch.
  - Checkboxes: A small square button — empty when off, checkmark when on, dash when mixed; usually titled on the trailing side (no title in an editable checklist). Use a checkbox instead of a switch to present a hierarchy of settings (alignment + indentation show dependencies). Use radio buttons for more than two mutually exclusive options. Use a label to introduce a group if the relationship isn't clear (align label baseline with the first checkbox). Accurately reflect on/off/mixed state; show mixed when subordinate checkboxes differ (`allowsMixedState`).
  - Radio buttons: A small circular button followed by a label, typically in groups of 2–5, for mutually exclusive choices; state is selected (filled circle) or deselected (empty circle). Prefer radio buttons for mutually exclusive options; use checkboxes if multiple options can be chosen. Avoid more than about 5 in a set — use a pop-up button instead. To present a single on/off setting, prefer a checkbox. Use consistent spacing when displaying radio buttons horizontally (size to the longest label).

### Disclosure controls
**Purpose:** Reveal and hide information/functionality related to specific controls or views.

**Best practices:**
- Use to hide details until relevant; put the most-used controls at the top of the hierarchy (always visible), with advanced functionality hidden by default.
- Disclosure triangle: shows/hides info for a view or list; points inward from the leading edge when hidden, down when visible. Provide a descriptive label indicating what is disclosed/hidden (e.g. "Advanced Options"). See `NSButton.BezelStyle.disclosure`.
- Disclosure button: shows/hides functionality for a specific control (e.g. macOS Save sheet); points down when hidden, up when visible. Place it near the content it controls; use no more than one disclosure button per view. See `NSButton.BezelStyle.pushDisclosure`.

Canonical implementations: SwiftUI `DisclosureGroup`, AppKit `NSButton.BezelStyle.disclosure` / `NSButton.BezelStyle.pushDisclosure`.

**Platform deltas:**
- macOS: No additional considerations.
- iOS/iPadOS, visionOS: Available with the SwiftUI `DisclosureGroup` view.
- Not supported in tvOS or watchOS.

### Color wells
**Purpose:** Lets people adjust the color of text, shapes, guides, and other onscreen elements; tapping or clicking displays a color picker (system-provided or custom).

**Best practices:**
- Consider the system-provided color picker for a familiar, consistent experience that also lets people save a set of colors accessible from any app (and unifies the experience across iOS, iPadOS, macOS).

Canonical implementations: UIKit `UIColorWell` / `UIColorPickerViewController`, AppKit `NSColorWell`.

**Platform deltas:**
- iOS/iPadOS, visionOS: No additional considerations.
- Not supported in tvOS or watchOS.
- macOS: A clicked color well receives a highlight to confirm it's active, then opens a color picker; the well updates to the new color after selection. Supports drag and drop of colors between wells and from the color picker to a well.

### Image wells
**Purpose:** An editable version of an image view; people can copy/paste or delete its image, or drag a new image in without selecting first.

**Best practices:**
- Revert to a default image when needed — if the image well requires an image, redisplay the default if people clear its content.
- If the image well supports copy and paste, make sure the standard copy/paste menu items (and keyboard shortcuts) are available.

Canonical implementations: AppKit `NSImageView`.

**Platform deltas:**
- Not supported in iOS, iPadOS, tvOS, visionOS, or watchOS. (macOS only.)
