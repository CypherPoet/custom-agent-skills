# Patterns — Navigation

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Patterns pages: Launching, Onboarding, Modality, Multitasking, Going full screen.

## Contents
- [Launching](#launching)
- [Onboarding](#onboarding)
- [Modality](#modality)
- [Multitasking](#multitasking)
- [Going full screen](#going-full-screen)

### Launching
*Last changed: 2024-06*

**Purpose:** Deliver a streamlined launch — from app open through initial download to first screen ready — so people can start using the app immediately.

**Best practices:**
- Launch instantly; people don't want to wait more than a couple of seconds.
- If the platform requires it (iOS, iPadOS, tvOS), provide a launch screen. macOS, visionOS, and watchOS don't require launch screens.
- A splash screen is not a launch screen. If you need a splash screen, display it at the beginning of your onboarding flow — or as soon as launching completes if there's no onboarding.
- Restore the previous state on restart so people continue where they left off; restore granular details (scroll position, window state and location).

**Launch screens** (*Not applicable for macOS, visionOS, or watchOS*):
- A launch screen's sole function is to make the experience feel quick to launch and ready to use — it's not onboarding, a splash screen, or artistic expression.
- Design a launch screen nearly identical to the app's first screen to avoid an unpleasant flash. If the first screen is a solid color, make the launch screen only that solid color. Match the device's current orientation and appearance mode.
- Avoid text on the launch screen — its content can't be localized.
- Don't advertise: no logos or branding unless they're a fixed part of the first screen.

**Platform deltas:**
- iOS/iPadOS: Launch in the device's current orientation if both portrait and landscape are supported; otherwise launch in the supported orientation. A landscape-only interface must respond correctly whether the device is rotated left or right.
- macOS: No additional considerations.
- watchOS: No additional considerations.
- tvOS: In a live-viewing app, consider auto-starting playback of new or recently viewed live content after a few seconds of inactivity.
- visionOS: Consider launching in the Shared Space even if the app is fully immersive — open a window to provide context while loading and offer a control to enter the fully immersive experience. Let people choose when to transition to a Full Space.

### Onboarding
*Last changed: 2024-06*

**Purpose:** When onboarding is necessary, give people a fast, fun, optional flow that helps them get a quick start; it occurs after launching completes, not as part of it.

**Best practices:**
- Teach through interactivity — let people safely test an action, discover a feature, or try a game mechanic rather than just viewing instructional material.
- Consider context-specific tips instead of a single onboarding flow; display instructions near the relevant interface area. For developer guidance, see TipKit.
- If a prerequisite flow is required, keep it brief and enjoyable; don't make people memorize a lot.
- If you offer a separate tutorial, make it optional. If people skip it on first launch, don't present it again — keep it findable later (help, account, or settings).
- Keep onboarding focused on your app or game; don't teach the system or device.
- Briefly display a splash screen only if necessary — just long enough to absorb at a glance without feeling delayed.
- Don't let large downloads hinder onboarding; bundle enough media/content in the package so people can start immediately whether they onboard or skip.
- Avoid licensing details in the onboarding flow — let the App Store show agreements and disclaimers. If you must include them, integrate them without disrupting the experience.
- Postpone nonessential setup and customization; provide reasonable defaults so most people can start without configuration.
- If the app needs access to private data/resources to function, consider integrating the permission request into onboarding (to explain why and show the benefits). Otherwise, request permission when people first access the function that relies on it.
- Prefer letting people experience the app before prompting for ratings or purchases.

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, visionOS, or watchOS.

### Modality
*Last changed: 2023-12*

**Purpose:** Present content in a separate, dedicated mode that prevents interaction with the parent view and requires an explicit action to dismiss — to deliver critical info, confirm/modify an action, support a narrowly scoped task, or give an immersive/focused experience.

**Use it when / not when:**
- Use when: there's a clear benefit — helping people focus or make choices that affect their content or device.
- Use a full-screen modal style when: presenting in-depth content or a complex/multistep task (videos, photos, camera views, marking up a document, editing a photo).
- Prefer a nonmodal full-screen experience when: the experience doesn't need to block the parent view — see Going full screen.

**Best practices:**
- Present content modally only when there's a clear benefit — modality takes people out of context and requires an action to dismiss.
- Keep modal tasks simple, short, and streamlined so people don't lose track of the suspended task.
- Avoid an "app within your app." Don't present a deep hierarchy of views in a modal task; if subviews are needed, provide a single path and avoid buttons people might mistake for the dismiss button.
- Always give an obvious way to dismiss. Follow platform conventions: iOS, iPadOS, watchOS — a button in the top toolbar or swipe down; macOS, tvOS — a button in the main content view.
- Confirm before closing if dismissal could lose user-generated content (e.g., on iOS present an action sheet with a save option), whether dismissed by gesture or button.
- Make the modal view's task easy to identify with a title (and optional descriptive/guidance text).
- Let people dismiss one modal view before presenting another; don't show multiple modal views at once. An alert can appear on top of all content including other modals, but never display more than one alert at the same time.

Canonical implementations: SwiftUI presentation modifiers (`View-Presentation`), UIKit `UIModalPresentationStyle`, AppKit modal windows and panels.

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, visionOS, or watchOS.
- visionOS (noted in guidance): a full-screen modal fills a window in the Shared Space; transitioning the app to a Full Space can make it a more immersive experience.

### Multitasking
*Last changed: 2025-06*

**Purpose:** Let people switch quickly between apps and perform tasks in each; with rare exceptions (some games, Apple Vision Pro Full Space apps), every app needs to work well with multitasking and always be ready to save and restore context.

**Best practices:**
- Pause activities that require attention or active participation (games, media playback) when people switch away, and resume seamlessly when they switch back.
- Respond smoothly to audio interruptions: pause indefinitely for primary audio (music, podcasts, audiobooks); for shorter interruptions (GPS notifications) temporarily lower the volume or pause, then restore the original volume/playback when the interruption ends.
- Finish user-initiated tasks in the background (downloads, video processing) before suspending, when they need no further input.
- Use notifications sparingly: notify when an important or time-sensitive task completes; for routine or secondary tasks, let people check on return instead of sending an unnecessary notification.

**Platform deltas:**
- iOS: On iPhone, multitasking lets people use FaceTime or watch a video in Picture in Picture while using another app. The app switcher shows all open apps.
- iPadOS: People can view and interact with windows of several apps at once; a single app can also support multiple open windows. iPad supports full-screen or windowed apps; switch between full-screen app windows via the app switcher. Windowed apps are resizable and arrangeable (macOS-like), with system window controls for tiling, full screen, minimize, and close; the system colors the frontmost window's controls and casts a drop shadow on windows behind it. Videos and FaceTime calls can play in a Picture in Picture overlay whether apps are full screen or windowed. Adapt gracefully to different screen sizes.
- macOS: Multitasking is the default — people typically run more than one app at a time. macOS applies drop shadows and other visual effects to distinguish window states.
- tvOS: People can play or browse content while playing movies or TV shows in Picture in Picture (where supported).
- visionOS: People can run multiple apps in the Shared Space, switching between windows and volumes. Only one window is active at a time; looking from one window to another activates it while the previous recedes along the z-axis and becomes more translucent. Closing a window in the Shared Space backgrounds the app without quitting it. Avoid interfering with system multitasking behavior — don't change a window's edge appearance (the system applies a feathered mask to the window you look away from). Don't pause a window's video playback when people look away. Be prepared for audio to duck when people look away unless the app is the Now Playing app.
- watchOS: Not supported in watchOS.

### Going full screen
*Last changed: 2025-06*

**Purpose:** On iPhone, iPad, and Mac, let people expand a window to fill the screen, hiding system controls for a distraction-free environment. Apple TV, Apple Watch, and Apple Vision Pro don't offer full-screen modes (tvOS/watchOS already fill the screen; visionOS uses window expansion or the Digital Crown for immersion).

**Best practices:**
- Support full-screen mode when it fits the experience: playing a game, viewing media (videos, photo slideshows), or an in-depth task that benefits from a distraction-free environment.
- Adjust layout in full-screen mode if needed, but don't programmatically resize the window. Keep essential content prominent, use the extra space, and keep adjustments subtle to avoid jarring transitions.
- Keep essential features and controls accessible so people can finish a task without exiting (e.g., playback controls persistently available or easy to reveal).
- Except in games, let people reveal the Dock while in full-screen mode on iPadOS and macOS. To prevent accidental reveals in a full-screen game, ask iPadOS to ignore an initial swipe up from the bottom edge, or hide the Dock entirely in macOS. Developer guidance: `preferredScreenEdgesDeferringSystemGestures` (SwiftUI/UIKit), `hideDock` (AppKit).
- After switching away, help people resume where they left off (pause a game or slideshow automatically).
- Let people choose when to exit full-screen mode; don't end it automatically when they switch experiences or finish an activity.
- Prioritize content by temporarily hiding toolbars and navigation controls when content is the primary focus (full-screen photos, reading). Let people restore hidden elements with a familiar gesture/action (tap, swipe down, move the cursor to the top of the screen). Keep controls visible when essential for navigation or tasks.

Canonical implementations: SwiftUI `fullScreenCover(item:onDismiss:content:)`, AppKit `NSWindow.toggleFullScreen(_:)` / `NSScreen` / `NSWindow.CollectionBehavior`.

**Platform deltas:**
- iOS/iPadOS: Consider deferring system gestures to prevent accidental exits. By default the Home Screen indicator auto-hides shortly after switching to the app and reappears on interaction with the bottom of the screen, allowing a single swipe to exit; retain this familiar behavior when possible. If it causes unexpected exits, enable two swipes rather than one. Developer guidance: `preferredScreenEdgesDeferringSystemGestures` (SwiftUI).
- macOS: Use the system-provided full-screen experience (it accommodates things like the camera housing at top-center). Developer guidance: `toggleFullScreen(_:)`. In a game, don't change the display mode when players go full screen — people expect to control their display mode, and it doesn't improve performance. Always let people choose when to enter full-screen mode: prefer the window's Enter Full Screen button, the View menu item, or Control-Command-F; avoid a custom menu of window modes (a game may provide a custom toggle).
- tvOS: Not supported.
- visionOS: Not supported. (A visionOS window can hide toolbars or navigation controls, but people generally expect different immersive experiences — see Immersive experiences.)
- watchOS: Not supported.
