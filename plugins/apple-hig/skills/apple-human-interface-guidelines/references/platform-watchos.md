# Platform — watchOS

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG platform pages: Designing for watchOS, Always On.

**Contents:** [Designing for watchOS](#designing-for-watchos) · [Always On](#always-on)

### Designing for watchOS
*Last changed: 2023-06*

**Purpose:** Apple Watch delivers glanceable, essential information and simple, timely tasks for people on the move, where related experiences (complications, notifications, Siri) often matter more than the app itself.

**Best practices:**
- **Glanceability.** Support quick, single-screen interactions that deliver critical information succinctly and let people act with a gesture or two; concise app interactions can last under a minute. Personalize by anticipating needs and using on-device data for content that's relevant now or very soon.
- **Navigation.** Minimize navigation depth; use the Digital Crown for vertical navigation — scrolling or switching between screens.
- **Input.** People interact one foot from the display, using the opposite hand. Turn the Digital Crown to navigate vertically or inspect data (consistent on watch face, Home Screen, and within apps); use standard gestures (tap, swipe, drag) in motion; press the Action button to start an essential action without looking; use shortcuts for routine tasks. Device features include GPS, blood-oxygen and heart sensors, altimeter, accelerometer, gyroscope.
- **System features.** Lean on complications (dynamic data/graphics on the watch face; tap to open the app on every wrist raise), notifications (timely high-value info plus actions without opening the app), Always On, and watch faces. Use color for supporting info and materials for hierarchy and sense of place.
- **Independence.** Design the app to function on its own, complementing notifications and complications with additional detail and functionality.

### Always On
*Last changed: 2023-09*

**Purpose:** On Always On devices, the system keeps showing an app's interface in a low-power, privacy-preserving way when people suspend interaction — Apple Watch dims the watch face when the wrist drops, continuing to show the app while it's frontmost or running a background session.

**Best practices:**
- **Privacy.** Redact personal information casual observers shouldn't see (bank balances, health data), including anything that could surface in a notification. Keep glanceable info that people value (workout pace, heart rate); if they want nothing visible, they can turn Always On off.
- **Legibility/dimming.** Keep important content legible and dim nonessential content — increase dimming on secondary text, images, and color fills; consider removing rich images or large color areas and using dimmed colors.
- **Consistent layout.** Avoid distracting changes when Always On begins, ends, or runs. Transition interactive components to an unavailable appearance rather than removing them. Make infrequent, subtle updates (e.g., pause granular play-by-play, update only the score when it changes).
- **Motion.** Gracefully transition motion to a resting state — smoothly finish current motion rather than stopping instantly.
- **Behavior.** The system shows notifications during Always On; tapping the display exits Always On and resumes interaction. (Also supported on iPhone 14 Pro / Pro Max, which shows Lock Screen widgets and Live Activities. Not supported in iPadOS, macOS, tvOS, or visionOS.)
