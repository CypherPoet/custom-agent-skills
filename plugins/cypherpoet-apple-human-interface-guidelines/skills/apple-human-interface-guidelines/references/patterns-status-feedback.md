# Patterns — Status & Feedback

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Patterns pages: Feedback, Notifications, Managing notifications, Live Activities, Privacy, Ratings and reviews.

## Contents
- [Feedback](#feedback)
- [Notifications](#notifications)
- [Managing notifications](#managing-notifications)
- [Live Activities](#live-activities)
- [Privacy](#privacy)
- [Ratings and reviews](#ratings-and-reviews)

### Feedback

**Purpose:** Feedback tells people what's happening, what they can do next, and the result of an action, matching the significance of the information to how it's delivered.

**Use it when / not when:**
- Display status passively when people can view it at their leisure.
- Use an interrupting alert when a warning could prevent data loss or another negative consequence.

**Best practices:**
- Make all feedback accessible by using multiple channels — color, text, sound, and haptics — so people get it whether they silence the device, look away, or use VoiceOver.
- Integrate status feedback into your interface near the items it describes so people get info without leaving their context.
- Use alerts only for critical, ideally actionable information; overuse drains their impact.
- Warn people before a task that causes unexpected and irreversible data loss; don't warn when data loss is the expected result (e.g. Finder deleting a file).
- Confirm a significant action or task completed only when it's important enough — people expect success, so usually just tell them when it fails.
- Show when a command can't be carried out and help people understand why.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS: No additional considerations.
- watchOS: Avoid an indeterminate progress indicator (like a loading spinner) — it makes people think they must keep watching. Instead reassure them they'll get a notification when the process completes.

### Notifications

*Last changed: 2023-10*

**Purpose:** A notification gives people timely, high-value information they can understand at a glance, delivered as a Lock Screen/Home Screen/desktop banner, an app-icon badge, or a Notification Center item.

**Use it when / not when:**
- Use a notification for timely, high-value updates.
- Use an alert — not a notification — to display an error message.

**Best practices:**
- Provide concise, informative notifications.
- Avoid sending multiple notifications for the same thing, even if someone hasn't responded — it fills Notification Center and makes people turn off all your notifications.
- Avoid telling people to perform specific tasks within your app; if simple tasks make sense, offer notification actions instead.
- Handle notifications gracefully in the foreground: your notifications don't appear, but you still get the data, so present it discreetly (increment a badge, subtly insert new data).
- Avoid including sensitive, personal, or confidential information — you can't predict who's nearby.
- Title: keep it short and use it for useful context (headline, event name, email subject). The system shows the sender's name for communication notifications and your app name if you omit a title. Use title-style capitalization, no ending punctuation.
- Body: write succinct content with complete sentences, sentence case, and proper punctuation; don't truncate (the system does it).
- Provide generically descriptive text for when previews are hidden (Settings shows only app icon + default title "Notification") — e.g. "Friend request," "New comment," "Reminder," "Shipment." Use sentence-style capitalization. See `hiddenPreviewsBodyPlaceholder`.
- Don't include your app name or icon in content — the system shows your icon automatically (and badges the sender's contact image in communication notifications).
- Consider a supplemental sound: short, distinctive, professionally produced, or a system alert sound. Don't rely on it for critical info; you can't trigger vibration programmatically. See `UNNotificationSound`.
- Notification actions: present up to four buttons for tasks done without opening the app. Use short title-case labels describing the result, no app name or extraneous text, mind localization.
- Avoid an action that merely opens your app — tapping the notification already does that.
- Prefer nondestructive actions; give enough context for any destructive one (the system styles destructive actions distinctly).
- Provide a simple SF Symbols interface icon per action; the system shows it on the trailing side of the action title.
- Badging: use a badge only to show the count of unread notifications, never for unrelated numeric data (weather, dates, stock prices, game scores).
- Don't make badging the only way you communicate essential info — people can turn it off.
- Keep badges current; update as soon as people open notifications. Reducing the count to zero removes all related notifications from Notification Center.
- Don't fake a badge with a custom image or component.

Canonical implementations: User Notifications (`UNNotificationCategory.hiddenPreviewsBodyPlaceholder`, `UNNotificationSound`), User Notifications UI.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS: No additional considerations.
- watchOS: Notifications occur in two stages — *short look* and *long look* — plus Notification Center; supported devices can double-tap to respond. A short look appears on wrist-raise and disappears on wrist-lower — don't use it as the only way to convey important info, and keep its title free of sensitive info. Long looks add detail (scrollable via swipe or Digital Crown); a custom long-look interface can be static or dynamic — at minimum ship a static interface (the system falls back to it with no network or unreachable iPhone companion), preferably a dynamic one too. The system-defined structure includes a sash at top (app icon + name; customize color or use a blurred appearance) and a Dismiss button at bottom below all custom buttons. Content-area background defaults to transparent; to match system notifications use white at 18% opacity. Provide up to four custom actions below the content area. Double-tap runs the first nondestructive action, so order most-used first.

### Managing notifications

**Purpose:** Lets people manage how they receive notifications through delivery scheduling, Focus, and per-notification interruption levels — built on permission you must get before sending anything.

**Best practices:**
- Build trust by accurately representing each notification's urgency; people can adjust or turn off all your notifications, so assigning the right interruption level is essential.
- Identify your notification types: use *communication* notifications for direct communications (phone calls, messages) and *noncommunication* notifications for everything else. To support communication notifications, adopt SiriKit intents (`INSendMessageIntent`, `UNNotificationContentProviding`) so people can customize behaviors via Siri.
- Specify a system-defined interruption level for every noncommunication notification; for communication notifications the system uses the sender to decide delivery timing.
- Use Time Sensitive only for info relevant in the moment — an event happening now or within an hour. The system explains Time Sensitive on first arrival and lets people turn it off, and revisits this periodically. See `UNNotificationInterruptionLevel`.
- Don't send marketing/promotional content without explicit opt-in; never use Time Sensitive for a marketing notification.
- Get explicit permission for marketing notifications via an alert, modal, or other interface with a clear opt-in/opt-out.
- Provide an in-app settings screen so people can change their notification choices.

Canonical implementations: User Notifications (`UNNotificationInterruptionLevel`), Intents (`INSendMessageIntent`, `UNNotificationContentProviding`).

**Specs:**

The four noncommunication interruption levels:

| Interruption level | Use for | Overrides scheduled delivery | Breaks through Focus | Overrides Ring/Silent switch (iPhone, iPad) |
| --- | --- | --- | --- | --- |
| Passive | Info to view at leisure (restaurant recommendation) | No | No | No |
| Active (default) | Info appreciated on arrival (sports score) | No | No | No |
| Time Sensitive | Directly impacts the person, needs immediate attention (security issue, package delivery) | Yes | Yes | No |
| Critical | Urgent health/safety info; extremely rare, typically governmental/public agencies or health/home apps | Yes | Yes | Yes |

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS: No additional considerations.
- watchOS: By default iPhone notification settings apply to the same apps on Apple Watch; people manage them in the Apple Watch app on iPhone, or access per-notification options (Mute 1 Hour, Turn off Time Sensitive) by swiping left on a notification.

### Live Activities

*Last changed: 2025-12*

**Purpose:** A Live Activity lets people track the progress of an activity, event, or task at a glance across system locations, delivering frequent content and status updates over a few hours with interaction.

**Use it when / not when:**
- Offer a Live Activity for tasks and events with a defined beginning and end (short-to-medium duration, not exceeding eight hours).
- Don't use it for ads or promotions — show only info related to the tracked event or task.

**Best practices:**
- Focus on important glanceable info; let people tap to open your app for more detail.
- Avoid displaying sensitive info (visible on the Lock Screen / Always-On display) — show an innocuous summary, or redact and let people opt to show sensitive data. See WidgetKit "Hide sensitive content."
- Match your app's visual aesthetic and personality in both dark and light appearances.
- Display any logo mark without a container; don't use the whole app icon.
- Don't add elements to your app that draw attention to the Dynamic Island.
- Keep text easy to read: large, medium-weight or heavier; use small text sparingly.
- Adapt layouts and assets to different screen sizes, presentations, and scale factors using the Specifications values.
- Use consistent, concentric margins so rounded shapes don't poke into the Live Activity's rounded shape; match corner radius by subtracting the margin (`ContainerRelativeShape`).
- Separate content blocks with an inset container shape or a thick line — don't draw content to the edge of the Dynamic Island.
- Dynamically change the height on the Lock Screen or expanded presentation, growing as more info becomes available.
- Colors: you can't customize background color for compact, minimal, or expanded presentations (Dynamic Island uses a black opaque background); you can set a custom Lock Screen background — ensure contrast, especially on Always-On displays. Tint the key line color (appears around the Dynamic Island on dark backgrounds) to match your content.
- Animations: system and custom animations have a maximum duration of two seconds; the system skips animations on Always-On displays with reduced luminance. Animate layout changes by moving existing elements rather than removing and re-adding; avoid overlapping elements.
- Interactivity: make tapping open your app at the right location (deep link). Keep interactive elements to essential, directly related functionality (music playback, workouts, live-audio recording); prefer limiting to a single interactive element.
- Start Live Activities at appropriate times and make it easy to turn them off in your app; offer an App Shortcut that starts one (e.g. via the Action button).
- Update only when new content is available; alert people only for essential updates (alerts light the screen, play the notification sound, and show the expanded/banner presentation). Don't pair push notifications with Live Activities for the same updates.
- Prefer one Live Activity that rotates through multiple events over several separate ones.
- Always end a Live Activity immediately when the task/event ends; consider a custom dismissal time proportional to its duration — usually 15 to 30 minutes is adequate. After ending, it's removed immediately from the Dynamic Island and CarPlay but remains up to four hours on the Lock Screen, the Mac menu bar, and the watchOS Smart Stack.
- Compact presentation: show the most essential dynamic info; design leading and trailing elements to read as one piece with consistent color and typography; keep content narrow and snug against the TrueDepth camera with no padding; link both elements to the same screen.
- Minimal presentation: stay recognizable — prefer updated info over a static logo (e.g. Timer shows remaining time).
- Expanded presentation: keep relative element placement coherent with compact/minimal; wrap content tightly around the TrueDepth camera.
- Lock Screen presentation: don't replicate notification layouts; use custom background/tint colors and opacity sparingly so it fits a personalized Lock Screen; verify contrast in Dark Mode and on Always-On displays; verify the system-generated dismiss button color (`activitySystemActionForegroundColor(_:)`); standard layout margin is 14 points.
- StandBy presentation: minimal presentation appears, transitioning to the Lock Screen presentation scaled up 2x on tap; update the layout and assets for the larger scale; consider the default background color so it blends with the bezel; use standard margins and avoid extending graphics to the edge; verify the design in Night Mode (system applies a red tint).

Canonical implementations: ActivityKit, SwiftUI (`ContainerRelativeShape`, `activitySystemActionForegroundColor(_:)`, `padding(_:_:)`), WidgetKit (`ActivityFamily.small`).

**Specs:**

Where Live Activities appear:

| Platform or system experience | Location |
| --- | --- |
| iPhone and iPad | Lock Screen, Home Screen, Dynamic Island and StandBy on iPhone |
| Mac | The menu bar |
| Apple Watch | Smart Stack |
| CarPlay | CarPlay Dashboard |

iOS dimensions (points):

| Screen (portrait) | Compact leading | Compact trailing | Minimal (width range) | Expanded (height range) | Lock Screen (height range) |
| --- | --- | --- | --- | --- | --- |
| 430x932 | 62.33x36.67 | 62.33x36.67 | 36.67–45x36.67 | 408x84–160 | 408x84–160 |
| 393x852 | 52.33x36.67 | 52.33x36.67 | 36.67–45x36.67 | 371x84–160 | 371x84–160 |

Dynamic Island corner radius: 44 points (matches the TrueDepth camera). Dynamic Island width: 250 pt on Max/Plus/Air models, 230 pt on base/Pro models (compact or minimal); expanded width 408 pt (Max/Plus/Air) or 371 pt (base/Pro), across iPhone 14 Pro through iPhone 17 Pro Max.

iPadOS Lock Screen dimensions (points): 1366x1024 → 500x84–160; 1194x834, 1012x834, 1080x810, 1024x768 → 425x84–160.

CarPlay Live Activity sizes (pt): 240x78, 240x100, 170x78. Smart Display Zoom test resolutions (pt): Widescreen 1920x720, Portrait 900x1200, Standard 800x480.

watchOS Smart Stack sizes (pt): 40mm 152x69.5, 41mm 165x72.5, 44mm 173x76.5, 45mm 184x80.5, 49mm 191x81.5.

**Platform deltas:**
- iOS/iPadOS: No additional considerations. Not supported in tvOS or visionOS.
- macOS: Active Live Activities appear automatically in the Mac menu bar using compact, minimal, and expanded presentations; clicking launches iPhone Mirroring. Use the iOS dimensions.
- watchOS: A Live Activity that begins on iPhone appears at the top of the paired Apple Watch's Smart Stack, combining the compact presentation's leading and trailing elements by default. With a watchOS app, tapping opens it; without one, tapping opens a full-screen view with a button to open the iPhone app. Consider a custom watchOS layout for more info and interactivity, but the custom layout also applies in CarPlay where interactive elements are deactivated — don't include buttons or toggles if people may start or observe it while driving.
- CarPlay: The system combines the compact presentation's leading and trailing elements into a single CarPlay Dashboard layout; interactive elements are deactivated. Consider a custom layout via the `ActivityFamily.small` supplemental activity family; prefer timely content over buttons and toggles.

### Privacy

*Last changed: 2023-06*

**Purpose:** Be transparent about the privacy-related data and resources you require, request only what you need, and protect the data people allow you to access.

**Best practices:**
- Request access only to data you actually need, and make permission requests as specific as possible.
- Be transparent about how you collect and use data; respect Hide My Email and Mail Privacy Protection, and understand your app-tracking obligations.
- Process data on device where possible (e.g. Apple Neural Engine, custom CreateML models) to avoid risky server round trips.
- Adopt system-defined privacy protections (e.g. CloudKit encryption and key management for strings, numbers, and dates in iOS 15+).
- Request permission only when your app clearly needs the data or resource; ideally wait until people use the feature that requires it.
- Avoid requesting permission at launch unless the data or resource is required for the app to function.
- Write a purpose string (usage description) that's a brief, complete, specific sentence: sentence case, active voice, period at the end. The system shows it after your app name and before the grant/deny buttons. See "Requesting access to protected resources" and App Tracking Transparency.
- Pre-alert screens (before a system permission alert): include only one button, titled "Continue" or "Next" — not "Allow" — making clear it opens the system alert. Don't include any additional action like Cancel or Close.
- Tracking requests: to track at launch, show the system alert before collecting any tracking data. Never precede it with a custom screen that could confuse or mislead. Prohibited (causes App Store rejection): offering incentives, mirroring the system alert's functionality, showing/modifying an image of the alert, and annotating the screen behind the alert. See App Review Guidelines 5.1.1 (iv).
- Location button (iOS, iPadOS, watchOS): Core Location provides a button granting temporary, one-time location authorization at the moment a task needs it. The first tap shows a standard alert; afterward a tap grants one-time access without reconfirmation. Customize only the system-provided title (e.g. "Current Location," "Share My Current Location"), filled or outlined glyph, background/title/glyph color, and corner radius — no other attributes; ensure text fits without truncation at all accessibility sizes and translations.
- Protecting data: prefer passkeys over passwords; augment retained passwords with two-factor authentication and biometric identification (Face ID, Optic ID, Touch ID). Store sensitive info in a keychain; never store passwords or secure content in plain-text files. Avoid inventing custom authentication schemes — prefer passkeys, Sign in with Apple, or Password AutoFill.

Canonical implementations: UIKit (Requesting access to protected resources), CoreLocation (location button, requesting authorization), AppTrackingTransparency, Security (Keychain services), LocalAuthentication, AuthenticationServices (passkeys).

**Specs:**

Purpose string examples:

| | Example purpose string | Notes |
| --- | --- | --- |
| Correct | The app records during the night to detect snoring sounds. | Active sentence that clearly describes how and why the app collects the data. |
| Incorrect | Microphone access is needed for a better experience. | Passive sentence giving vague, undefined justification. |
| Incorrect | Turn on microphone access. | Imperative sentence with no justification. |

**Platform deltas:**
- iOS/iPadOS/tvOS/watchOS: No additional considerations.
- macOS: Sign your app with a valid Developer ID if distributing outside the store. Protect data with app sandboxing (required for the Mac App Store). Avoid assuming who is signed in — fast user switching means multiple people may be active.
- visionOS: ARKit algorithms (persistence, world mapping, segmentation, matting, environment lighting) always run, but ARKit sends no data to apps in the Shared Space — accessing ARKit APIs requires a Full Space. Plane Estimation, Scene Reconstruction, Image Anchoring, and Hand Tracking require permission. User input is private by design: the system shows hover effects on SwiftUI/RealityKit interactive components without exposing where people look before they tap. The back camera provides blank input (compatibility only); the front camera provides input for spatial Personas only after permission — for an iOS/iPadOS app coming to visionOS, remove camera-dependent features or replace them with content import.

### Ratings and reviews

*Last changed: 2023-09*

**Purpose:** Choose the right moment to ask people for an App Store rating or review, using the system-provided prompt.

**Best practices:**
- Ask for a rating only after people demonstrate engagement (e.g. completing a level or significant task); avoid asking on first launch or during onboarding.
- Avoid interrupting people mid-task or mid-game; look for natural breaks or stopping points.
- Avoid pestering: allow at least a week or two between requests, and prompt again only after additional engagement.
- Prefer the system-provided prompt (iOS, iPadOS, macOS): people can rate, optionally review, or dismiss with a single tap/click, and can opt out for all apps. The system automatically limits display to three occurrences per app within a 365-day period. See `RequestReviewAction`.
- Weigh resetting your summary rating on a new release (ratings reflect the current version) against ending up with fewer ratings overall, which can discourage downloads.

Canonical implementations: StoreKit (`RequestReviewAction`).

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: No additional considerations.
