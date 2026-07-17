# Platform — iOS & iPadOS

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG platform pages: Designing for iOS, Designing for iPadOS, Status bars.

**Contents:** [Designing for iOS](#designing-for-ios) · [Designing for iPadOS](#designing-for-ipados) · [Status bars](#status-bars)

### Designing for iOS

**Purpose:** Conventions for iPhone — a medium-size, high-resolution display held in the hand and used on the go.

**Best practices:**
- **Display & ergonomics.** Medium-size, high-resolution display. People hold iPhone in one or both hands and switch freely between portrait and landscape; viewing distance is typically no more than a foot or two.
- **Inputs.** Support Multi-Touch gestures, virtual keyboards, and voice (Siri) so people can act while on the go. With permission, draw on personal data, gyroscope/accelerometer input, and spatial interactions; integrate platform data (payments, biometric auth, location) to enhance the experience without making people enter data.
- **Layout & reachability.** Place controls where they're easy to reach — the middle or bottom of the display is more comfortable than the top. Let people swipe to navigate back or trigger actions in a list row.
- **Focus.** Help people concentrate on primary tasks and content by limiting onscreen controls; keep secondary details and actions discoverable with minimal interaction.
- **Adaptivity.** Adapt seamlessly to appearance changes — device orientation, Dark Mode, and Dynamic Type — letting people choose the configuration that works for them.
- **System features.** Integrate the platform features people value: Widgets, Home Screen quick actions, Spotlight, Shortcuts, and Activity views.

### Designing for iPadOS

**Purpose:** Conventions for iPad — a large, high-resolution display valued for power, mobility, and flexibility across many input modes.

**Best practices:**
- **Display & ergonomics.** Large, high-resolution display. People may hold iPad, set it on a surface, or use a stand; viewing distance is typically within about 3 feet. Use viewing distance and input mode to determine the size and density of onscreen content.
- **Inputs.** Support Multi-Touch gestures and virtual keyboards, an attached keyboard or pointing device (trackpad/pointer), Apple Pencil, and voice — people often combine multiple input modes. Consider unique interactions that mix input modes.
- **Large-display layout.** Use the large display to elevate the content people care about; minimize modal interfaces and full-screen transitions. Position controls where they're easy to reach but not in the way.
- **Multitasking & inter-app.** People frequently keep multiple apps open and value viewing more than one app onscreen at once; support inter-app capabilities like drag and drop.
- **Adaptivity.** Adapt seamlessly to appearance changes — device orientation, multitasking modes, Dark Mode, and Dynamic Type — and transition effortlessly to running in macOS.
- **System features.** Integrate the platform features people value: Multitasking, Widgets, and Drag and drop.

### Status bars

**Purpose:** The bar along the upper screen edge showing device state (time, cellular carrier, Wi-Fi, battery). Supported on iOS and iPadOS only — not macOS, tvOS, visionOS, or watchOS.

**Best practices:**
- **Keep it readable over content.** The status bar background is transparent by default, letting content show through. Keep the bar readable and don't imply that content behind it is interactive (people may try to tap controls they can't reach). Prefer a scroll edge effect to place a blurred view behind it (`ScrollEdgeEffectStyle`, `UIScrollEdgeEffect`).
- **Hide temporarily for full-screen media.** A status bar can distract from media; temporarily hide it for a more immersive experience (e.g. full-screen photo browsing).
- **Never permanently hide it.** Without the status bar, people must leave the app to check the time or Wi-Fi. Let a simple, discoverable gesture redisplay a hidden status bar — for example, a single tap.
