# Technologies — Health & Media

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Technologies pages: Playing audio, Playing video, AirPlay, SharePlay, Live Photos, Photo editing, ShazamKit, HealthKit, CareKit, ResearchKit, Workouts, HomeKit, Augmented reality.

## Contents
- [Playing audio](#playing-audio)
- [Playing video](#playing-video)
- [AirPlay](#airplay)
- [SharePlay](#shareplay)
- [Live Photos](#live-photos)
- [Photo editing](#photo-editing)
- [ShazamKit](#shazamkit)
- [HealthKit](#healthkit)
- [CareKit](#carekit)
- [ResearchKit](#researchkit)
- [Workouts](#workouts)
- [HomeKit](#homekit)
- [Augmented reality](#augmented-reality)

### Playing audio
*Last changed: 2023-06*

**Purpose:** Deliver rich audio that automatically adjusts as device context, volume, and output routes change.

**Best practices:**
- Adjust relative, independent volume levels for a good mix, but never override system volume — it governs final output.
- Permit rerouting of audio output (stereo, car, Apple TV) unless there's a compelling reason not to.
- Use the system-provided volume view (slider plus output-rerouting control); customize slider appearance only — see `MPVolumeView`.
- Choose the `AVAudioSession.Category` that fits your sound use (table below); don't silence another app's audio if you don't need to.
- Respond to external audio controls (Control Center, headphones) only when actively playing, in an audio context, or connected via Bluetooth/AirPlay; otherwise don't halt another app's audio.
- Don't repurpose or redefine audio controls; if you don't support a control, don't respond to it.
- Create custom audio player controls only for commands the system can't offer (e.g. custom skip increments, related content like a sports score).
- Flag your audio session with `notifyOthersOnDeactivation` so other apps know when they can resume after your temporary audio.
- Inspect audio-session interruptions to decide your response; for recording/VoIP, avoid auto-unmuting the mic — a VoIP app must end a call when the iPad Smart Folio closes (which mutes the built-in mic). See Handling audio interruptions.
- On interruption end, use the interruption type plus your app type to decide whether to auto-resume: check `shouldResume` for resumable types (incoming call) vs nonresumable (new playlist); a game can resume without checking since its audio isn't an explicit user choice.

Canonical implementations: AVFAudio `AVAudioSession`, MediaPlayer `MPVolumeView`, MusicKit; AudioToolbox Audio Services for short sounds; WatchKit background audio + Now Playing view.

**Specs:**

| Category | Meaning | Behavior |
| --- | --- | --- |
| Solo ambient | Sound isn't essential but silences other audio (e.g. game with a soundtrack). | Responds to silence switch. Doesn't mix. Doesn't play in background. |
| Ambient | Sound isn't essential and doesn't silence other audio (game allowing music from another app). | Responds to silence switch. Mixes. Doesn't play in background. |
| Playback | Sound is essential, might mix (audiobook, language app). | Doesn't respond to silence switch. May or may not mix. Plays in background. |
| Record | Sound is recorded (note-taking with audio mode). | Doesn't respond to silence switch. Doesn't mix. Records in background. |
| Play and record | Sound is recorded and played, possibly simultaneously (audio messaging, video calling). | Doesn't respond to silence switch. May or may not mix. Records and plays in background. |

**Platform deltas:**
- iOS/iPadOS: Use the system's sound services (Audio Services) to play short sounds and vibrations.
- macOS: Notification sounds mix with other audio by default.
- visionOS: Sound is pervasive; prefer playing sound and design custom sounds for custom UI. Use Spatial Audio (ambient audio + audio sources) for immersion; decide fixed (perceived as pointed at the wearer) vs tracked (perceived as coming from an object) sound; vary repetitive sounds by randomizing pitch/volume. Now Playing audio pauses when its window closes; non-Now-Playing audio can duck when the wearer looks away.
- watchOS: System manages playback. Play short clips while active, or longer audio that continues across wrist-lower/app-switch (Playing Background Audio). Encode media at 64 kbps HE-AAC. Consider a Now Playing view to control current/recent audio.
- tvOS: System plays audio only when people initiate it; no sounds accompany alerts or notifications.

### Playing video
*Last changed: 2023-09*

**Purpose:** Provide rich, consistent video playback by embedding the system player (and optionally integrating with the TV app) across iOS, iPadOS, macOS, tvOS, and visionOS.

**Use it when / not when:**
- Use when: the system video player meets your needs — it gives a familiar, consistent experience with PiP, aspect-ratio modes, and AirPlay.
- Build a custom player only when: the system player truly can't meet your needs; then mirror its behavior and interface closely so habitual interactions still work.

**Best practices:**
- Always display video at its original aspect ratio; never bake letterbox/pillarbox padding into the frame — embedded padding breaks scaling, shrinks the video in both modes, and breaks edge-to-edge contexts like PiP on iPad.
- Default playback mode follows aspect ratio: aspect-fill (full-screen, some edge cropping) is default for wide video 2:1 through 2.40:1 (`resizeAspectFill`); aspect (fit-to-screen, letterbox/pillarbox as needed) is default for standard 4:3/16:9/up-to-2:1 and ultrawide above 2.40:1 (`resizeAspect`).
- Add a title/image/description via `externalMetadata` when it adds value, but don't obscure playback.
- Support expected input interactions on every device — Space to play/pause on a connected keyboard (Vision Pro, Mac, iPhone, iPad, Apple TV); Siri Remote gestures on Apple TV.
- Avoid mixing audio across sources when viewers switch modes (e.g. unmuted PiP video over a game's background music) — handle secondary audio via `silenceSecondaryAudioHintNotification`.
- TV app integration: present your own black screen before playback for a seamless fade-to-black transition; start content immediately (no splash/detail/intro barriers); auto-resume without prompting; play/pause on Space from a Bluetooth keyboard; switch to the profile the TV app specifies (or ask before playback); resume long clips at the previous end time.
- Loading: avoid loading screens when possible; if loading exceeds two seconds, show a black screen with a centered spinner and no surrounding content; start playback as soon as enough content loads and keep loading in the background; keep any branding minimal on the black background.
- Exiting playback (TV app): show a contextually relevant screen (a detail view with a resume option, else a content menu or main menu) and prepare the exit view early for an immediate exit.

Canonical implementations: AVKit `AVPlayerViewController`, watchOS `VideoPlayer`; AVFoundation, HTTP Live Streaming; RealityKit video player on visionOS.

**Specs:**

watchOS media asset encoding:

| Attribute | Value |
| --- | --- |
| Video codec | H.264 High Profile |
| Video bit rate | 160 kbps at up to 30 fps |
| Resolution (full screen) | 208x260 px (portrait) |
| Resolution (16:9) | 320x180 px (landscape) |
| Audio | 64 kbps HE-AAC |

**Platform deltas:**
- iOS/iPadOS/macOS: No additional considerations.
- tvOS: Defer to content for overlays — small unobtrusive logos/timers only; prefer translucent SDR graphics and short overlays (some devices are prone to image retention). For interactive overlays (quizzes, surveys), pause with a minimum 0.5-second delay and give a clear way to dismiss and resume.
- visionOS: Help comfort — let people start video, use a small resizable window, keep surroundings visible. In a fully immersive experience the system places the player at a predictable spot; don't let virtual content occlude playback/transport controls, and don't auto-start fully immersive playback. For scrubbing, supply a thumbnail track with each thumbnail 160 px wide. Inline video must be 2D — don't expand an inline `AVPlayerViewController` to fill a window; keep window content visible. Use a RealityKit video player for splash/transitional views (no controls, auto aspect ratio for 2D/3D, closed captions).
- watchOS: System manages playback; play short clips while active and running in foreground (`VideoPlayer`). Keep clips no longer than 30 seconds. Use recommended sizes/encoding; don't scale clips. Don't make a poster image look like a system control; do make it represent the clip's contents.

### AirPlay
*Last changed: 2023-05*

**Purpose:** Let people stream media wirelessly from iOS, iPadOS, macOS, and tvOS devices to Apple TV, HomePod, and AirPlay-capable TVs and speakers.

**Best practices:**
- Prefer the system-provided media player (`AVPlayerViewController`) — it supports chapters, subtitles, closed captioning, and AirPlay streaming. Build a custom player only if it can't meet your needs.
- Provide content in the highest possible resolution; include the full range of resolutions in your HLS playlist so AVFoundation can pick the right one per device (720p content looks low quality streamed to a 4K TV).
- Stream only content people expect; don't stream background loops or short in-app-only video (`usesExternalPlaybackWhileExternalScreenIsActive`).
- Support both AirPlay streaming and mirroring for maximum flexibility.
- Support remote control events so people can play/pause/fast-forward from the lock screen, Siri, or HomePod (Remote command center events).
- Don't stop playback when your app backgrounds or the device locks; avoid automatic mirroring so other content isn't streamed without explicit choice.
- Don't interrupt another app's playback unless starting immersive content; play launch/auto-play inline videos on the local device only (`ambient` category).
- Keep your app functional during playback; if people navigate away, don't let other in-app videos start and interrupt the stream.
- If you must build a custom player, match the system AirPlay button's appearance/behavior with distinct states (starting, occurring, unavailable), use only Apple-provided symbols, and place the AirPlay icon in the lower-right corner (iOS 16 / iPadOS 16 and later).
- Use only Apple-provided AirPlay icons (black on light, white on dark, or custom color to match other technology icons); position consistently with other technology icons; use the icon/name noninteractively only — never in custom buttons.
- Refer to _AirPlay_ as a noun only (one word, uppercase A and P); use terms like _works with_, _use_, _supports_, _compatible_; you may pair _Apple_ with _AirPlay_; keep AirPlay references less prominent than your app.

Canonical implementations: AVKit `AVPlayerViewController`, AVFoundation, HTTP Live Streaming.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS: No additional considerations.
- watchOS: Not supported.

### SharePlay
*Last changed: 2023-12*

**Purpose:** Let multiple people share a synchronized activity — watching, listening, gaming, sketching — during a FaceTime call or Messages conversation.

**Best practices:**
- Indicate SharePlay support in your interface — e.g. use the `shareplay` SF Symbol to mark sharable content.
- If part of your app needs a subscription, help nonsubscribers join fast: offer temporary/provisional access, a one-time pass, or Family Sharing; if they can subscribe during the activity, present a streamlined sign-up so others don't wait.
- Support Picture in Picture where possible (PiP window on iPhone/iPad; a movable background window on Mac).
- Define an _activity_ per shareable experience type; give each a short, meaningful description that avoids truncation (see Defining your app's SharePlay activities).
- Make it easy to start sharing: when no session exists, present UI to start a group activity, and the system asks whether to share or continue solo.
- Help people prepare before showing the activity — handle login, downloads, or payment up front and keep it effortless.
- Defer app tasks that might delay the shared activity (e.g. ask for a profile when playback pauses or finishes).
- Use _SharePlay_ as a noun ("Join SharePlay") or a verb for a direct action ("SharePlay Movie"); don't add adjectives (_virtual_, _spatial_) or inflect it (_SharePlayed_, _SharePlays_, _SharePlaying_).

Canonical implementations: GroupActivities (`SystemCoordinator`, `SpatialTemplatePreference`).

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS: No additional considerations.
- watchOS: Not supported.
- visionOS: Most apps are expected to support SharePlay; people choose the Spatial option in FaceTime. Spatial Personas appear in each wearer's space within a _shared context_ (single coordinate system; system synchronizes size, position, orientation). Pick a spatial Persona template — side-by-side (all face content, good for media, less nonverbal interaction), surround (around 3D content, faces each other), or conversational (around a center point with content on the circle, for being-together-while-app-works-in-background). Launch directly into the shared activity (present sign-in in an autodismissible window); help people join together without forcing a level-of-immersion change that would disrupt their task; integrate new participants smoothly and design for up to five. Keep everyone on the same app state; use Spatial Audio; prefer letting people resolve conflicts socially (e.g. last-change-wins); keep private vs shared windows distinguishable and allow dragging content from private to shared. Let people personalize without changing others' experience (volume, subtitles); give a unique per-person view only when content needs a specific angle (e.g. Spatial Capture); make it easy to exit and rejoin.

### Live Photos

**Purpose:** Present sound- and motion-rich Live Photos that spring to life on press, while keeping their content and interaction model consistent across apps.

**Best practices:**
- Apply any effects/adjustments to all frames of a Live Photo; if you can't, offer to convert it to a still photo.
- Keep Live Photo content intact — never disassemble it and present frames or audio separately.
- For sharing, let people preview the entire Live Photo before sharing, and always offer to share it as a traditional photo.
- Clearly indicate when a Live Photo is downloading (progress indicator) and when it's playable (completion indication).
- In environments that don't support Live Photos, display a traditional still — don't replicate the experience.
- Make Live Photos distinguishable from stills, ideally via a hint of movement (no built-in motion effects exist — design custom ones). Where movement isn't possible, show the system-provided badge (with or without text) and never a video-style playback button. Keep badge placement consistent, typically in a corner.

Canonical implementations: PhotoKit `PHLivePhoto`, LivePhotosKit JS.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS: No additional considerations.
- watchOS: Not supported.
- visionOS: People can view a Live Photo but can't capture one.

### Photo editing

**Purpose:** Let photo-editing extensions modify photos and videos inside the Photos app via filters or other changes, always saving edits as new files that preserve the originals.

**Best practices:**
- Confirm cancellation of edits — when someone taps Cancel after making edits, ask them to confirm and warn that edits will be lost; skip the confirmation if no edits were made.
- Don't provide a custom top toolbar; the modal view already includes one — a second is confusing and steals content space.
- Let people preview edits before closing the extension and returning to Photos.
- Use your app icon as the extension icon so people trust the extension comes from your app.

Canonical implementations: PhotoKit; App extensions.

**Platform deltas:**
- iOS/iPadOS/macOS: No additional considerations.
- tvOS/visionOS/watchOS: Not supported.

### ShazamKit

**Purpose:** Recognize audio by matching a sample against the ShazamKit catalog or a custom catalog (for genre-aware graphics, synced captions/sign language, or synchronized in-app experiences).

**Best practices:**
- Request microphone access only when you need samples, and explain why (see Privacy).
- Stop recording as soon as possible — record only as long as it takes to get the sample, to preserve privacy.
- Let people opt in before storing recognized songs to their iCloud library; even though the Music Recognition control and Shazam app attribute your app as the source, people want control over which apps add to their library.

Canonical implementations: ShazamKit.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: No additional considerations.

### HealthKit

**Purpose:** Read and write health and fitness data through the central HealthKit repository on iOS, iPadOS, and watchOS, with the user's permission.

**Best practices:**
- Request permission before accessing data and protect it; provide a coherent privacy policy via a URL given at app submission (see Protecting user privacy).
- Request access only when contextually needed (when people log weight, not at launch) — and request every time, since people can change permissions (`requestAuthorization(toShare:read:completion:)`).
- Clarify intent by adding a few succinct sentences to the standard permission screen explaining why you need the data and how people benefit; don't build custom screens that replicate it.
- Manage health-data sharing solely through Settings > Privacy; don't add in-app screens that affect health-data flow.
- Activity rings: use only for Move/Exercise/Stand progress, for a single identifiable person; never for ornamentation, branding, app icons, or marketing. Never alter ring/background colors, opacity, or filters — design the surrounding UI to blend (e.g. enclose in a circle by adjusting corner radius, not a circular mask). Keep a minimum outer margin no less than the distance between rings; never crop/obstruct the rings. Differentiate any other ring-like elements with padding, lines, labels, color, or scale. In notifications, reference Activity progress uniquely but never show a ring element or repeat the system's Move/Exercise/Stand updates.
- Apple Health icon: use only the Apple-provided icon (don't redesign or mimic); display the name _Apple Health_ near it; size it no smaller than other health-related icons; never use it as a button; never alter it (corner radius, circular shape, borders, overlays, gradients, shadows); keep minimum clear space of 1/10 its height and don't composite it onto other graphics; don't use it within text or as a substitute for _Health_, _Apple Health_, or _HealthKit_; don't display Health app screenshots.
- Editorial: refer to the app as _Apple Health_ or _the Apple Health app_; don't expose the developer-facing term _HealthKit_ to users; capitalize _Apple Health_ as two words (uppercase A and H); use the system-provided translation of _Health_.

Canonical implementations: HealthKit `HKHealthStore`, HealthKitUI `HKActivityRingView`.

**Platform deltas:**
- iOS/iPadOS/watchOS: No additional considerations.
- macOS/tvOS/visionOS: Not supported.

### CareKit
*Last changed: 2023-05*

**Purpose:** Build care-plan apps (chronic-illness management, recovery, wellness goals) using CareKit UI's prebuilt task, chart, and contact views backed by the on-device CareKit Store.

**Best practices:**
- Protect the sensitive data CareKit collects; provide a coherent privacy policy URL at submission and get permission before accessing device/system data (see Protecting user privacy).
- For HealthKit integration, request access only when needed and every time, clarify intent on the standard permission screen, and manage sharing solely via Settings > Privacy.
- With permission, use Core Motion for motion data (standing, walking, running, cycling, driving; step count, pace, flights), and `UIImagePickerController` for camera/photo sharing of treatment progress; use ResearchKit for surveys, tasks, charts, and the informed-consent module.
- Use each view category for its intended purpose (task, chart, contact); a view is a header plus an optional vertical stack of content subviews — CareKit UI manages layout constraints.
- Tasks: pick the style per use case — simple (one-step), instructions (simple plus informative text), log (timestamped event logging), checklist (multistep list), grid (compact multistep, exposes underlying collection view for custom UI). A task carries Title (required), Schedule (required), Instructions (optional), Group ID (optional). Use color to reinforce meaning but never as the only cue; combine accuracy with simplicity (medication marketing name, not chemical name); supplement complex tasks with videos or images.
- Charts: choose bar, scatter, or line; provide title/subtitle, axis markers, data set. Highlight narratives/trends; keep labels short and non-repetitive (e.g. _BPM_ in an axis label); use distinct, sufficiently contrasting colors and a legend if needed; denote units of time clearly; consolidate large data sets; offset data to keep charts proportional.
- Contacts: simple or detailed style; support phone/message/email and a map link; use color to categorize care-team members.
- Notifications: minimize them and coalesce multiple items into one; consider a detail view so people can act (e.g. mark tasks complete) without opening the app; Apple Watch can show them.
- Symbols/branding: prefer CareKit's built-in symbols (the grid view supports custom UI); design relevant care symbols (use SF Symbols), avoid purely decorative symbols or logos; keep branding refined and unobtrusive (no advertising).

Canonical implementations: CareKit (CareKit UI + CareKit Store); HealthKit `HKHealthStore`; Core Motion; UIKit `UIImagePickerController`.

**Specs:**

CareKit task information:

| Information | Required | Description | Example |
| --- | --- | --- | --- |
| Title | Yes | Word/short phrase introducing the task. | _Ibuprofen_ |
| Schedule | Yes | Schedule on which the task must be completed. | _Four times a day_ |
| Instructions | No | Detailed instructions, recommendations, warnings. | _Take 1 tablet every 4–6 hours (not to exceed 4 tablets daily)._ |
| Group ID | No | Identifier for grouping similar tasks. | _medication_, _exercise_ |

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS/tvOS/visionOS/watchOS: Not supported.

### ResearchKit
*Last changed: 2023-09*

**Purpose:** Build medical-research apps with predesigned onboarding, consent, survey, and active-task screens. (Informational only, not legal advice — consult an attorney.)

**Best practices:**
- Display onboarding screens in the correct order: Introduction → Eligibility → Informed consent → Permission to access data.
- Introduction: clearly describe the study's subject and purpose with a call to action; let existing participants log in and continue.
- Eligibility: determine it as soon as possible so ineligible people skip consent; present only necessary requirements in simple language with easy entry.
- Informed consent: ensure participants understand the study before consenting; comply with applicable App Store Guidelines and review-board requirements; break long forms into digestible sections (data gathering, use, benefits, risks, time commitment, withdrawal) with optional Learn More detail and the full form viewable before agreeing; optionally add a comprehension quiz; collect signature and contact info and typically email a PDF of the form.
- Permission: clearly explain why you need location, Health, or other data; don't request data that isn't critical; ask for notification permission if required.
- Surveys: tell participants how many questions and roughly how long; one screen per question; show progress; keep surveys short (several short beat one long); use the standard font for questions and a slightly smaller font for explanatory text; tell them when it's complete.
- Active tasks: describe how to perform the task in clear simple language; explain requirements (timing, circumstances); make completion obvious.
- Provide a profile screen to manage personal data, view consent/privacy docs, and leave the study; provide a dashboard for encouragement and progress (daily progress, weekly assessments, comparisons with aggregated results); keep both accessible at all times.

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS/tvOS/visionOS/watchOS: Not supported.

### Workouts

**Purpose:** Create workout/fitness experiences (primarily Apple Watch, also iPhone/iPad) that surface live activity data and familiar fitness-metric components.

**Best practices:**
- In a watchOS fitness app, use workout sessions to keep showing the app between wrist raises with the data people care about (elapsed/remaining time, calories, distance) and relevant controls (lap/interval markers). The common layout: large session controls (End, Resume, New, Segment) on the leftmost screen, glanceable metrics on a dedicated screen, media-playback controls on the rightmost screen.
- Avoid distracting people mid-workout with irrelevant info (don't make them browse your workout list or other app areas).
- Use a distinct visual appearance for an active workout — the real-time-updating metrics page, optionally with a unique layout.
- Provide easy-to-find, easy-to-tap pause/resume/stop controls with clear start/stop feedback.
- When sensor data is unavailable (e.g. water blocking heart rate), explain what is still recorded using language like the system Workout app (e.g. "water may prevent a heart-rate measurement, but Apple Watch will still track your calories, laps, and distance using the built-in accelerometer").
- Provide an end-of-session summary confirming completion and showing recorded data; consider including Activity rings.
- Discard extremely brief sessions automatically, or ask whether to record them.
- Keep text legible in motion — large font sizes, high-contrast colors, most important info easiest to read.
- Use Activity rings only for their documented purpose, matching the Activity app's colors and meanings.

Canonical implementations: WorkoutKit; HealthKit (workouts and activity rings).

**Platform deltas:**
- iOS/iPadOS/watchOS: No additional considerations.
- macOS/tvOS/visionOS: Not supported.

### HomeKit
*Last changed: 2023-05*

**Purpose:** Let people securely control connected home accessories via Siri or the Apple Home app on iPhone, iPad, Apple Watch, and Mac, with your app providing custom or accessory-specific experiences.

**Best practices:**
- Use HomeKit's object model and terminology so home automation feels approachable. Hierarchy: _home_ (root) → _rooms_, _accessories_, _zones_. An _accessory_ is a physical device; _category_ is its type (light, thermostat, fan); a _service_ is a controllable feature (named in UI, e.g. "garage door opener" — this is what people speak to Siri, not the accessory name); a _characteristic_ is a controllable attribute (speed, brightness); a _service group_ controls multiple services as a unit; an _action_ changes a characteristic; a _scene_ groups actions across services/accessories; _automations_ react to situations (location, time, accessory state, sensor); a _zone_ groups rooms (e.g. "upstairs").
- Reference the HomeKit hierarchy even if your UI doesn't organize by room/zone (so voice commands like "turn on the lights upstairs" work); surface an accessory's room/zone/home in its detail view; recognize people can have multiple homes; never present duplicate home settings — always defer to the Home app.
- Setup: use the system-provided setup flow (`performAccessorySetup(using:completionHandler:)`); provide a purpose string explaining why you need Home data; don't require an account or personal info (defer to HomeKit; make optional account setup post-setup); honor setup choices (don't force other-platform setup during HomeKit setup); present the system flow first, then offer a custom post-setup experience for unique features.
- Naming: suggest good service names (never company names or model numbers); enforce HomeKit naming rules — alphanumeric, space, apostrophe only; start and end with an alphabetic or numeric character; no emojis; help people avoid putting room/location info in a service name (assign to the room/zone instead).
- Siri: present example voice commands using the chosen service name during setup; later teach more complex commands; recommend zones and service groups when useful; offer shortcuts only for accessory-specific functionality HomeKit doesn't support (never duplicating HomeKit), and clarify the difference between shortcuts and HomeKit voice control.
- Custom functionality: be clear what's done in your app vs the Home app; defer to HomeKit when your database differs (reflect Home app changes; show conflicts visually); ask permission before writing to the HomeKit database — never overwrite settings without explicit direction.
- Cameras: don't block or cover camera images (supplements like activity alerts are fine); show a microphone button only if the camera supports bidirectional audio.
- Icons: use only Apple-provided HomeKit/Home app icons; position consistently with other technology icons; use noninteractively (don't put HomeKit icon/name in custom buttons — but the Apple Home app icon may open its App Store page); don't use the icon within text or as a replacement for the word HomeKit; pair icon and name correctly.
- Editorial: emphasize your app over HomeKit; follow Apple trademark guidelines (singular, non-possessive, untranslated; no category descriptors like "tablet"; refer to devices/OSes only in technical specs — "from your iPhone or iPad," not "from your iOS devices"); use _works with_/_supports_/_compatible_ rather than HomeKit as a descriptor; don't suggest HomeKit performs an action ("Back door is unlocked with HomeKit," not "HomeKit unlocked the back door"); capitalize _HomeKit_ (one word) and _Apple Home_ (two words); use the full name _Apple Home_ on first mention, then _the Home app_.

Canonical implementations: HomeKit `HMAccessorySetupManager`.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: No additional considerations.

### Augmented reality

**Purpose:** Blend virtual 3D objects with the live camera view of the real world using ARKit to create convincing, interactive immersive experiences.

**Best practices:**
- Offer AR features only on capable devices; if AR is your app's primary purpose, restrict availability to ARKit-supporting devices; if AR is optional, just omit the feature on unsupported devices rather than showing an error (Verifying Device Support and User Permission).
- Let people use the entire display for the physical world and virtual objects; avoid cluttering with controls.
- Strive for convincing illusions: detailed 3D assets with lifelike textures, correct scaling and placement on detected surfaces, environmental lighting and camera-grain simulation, top-down diffuse shadows; update scenes 60 times per second so objects don't jump or flicker.
- Prefer small or coarse reflective surfaces, since ARKit reflections are approximations.
- Use audio and haptics to confirm contact and enhance immersion; background music helps envelop people.
- Minimize text; show only what's needed.
- For persistent info/controls, prefer screen space and indirect controls (2D, in screen space), positioned so people needn't change their grip; use translucency to avoid blocking the scene.
- Anticipate varied real-world environments (limited room, no flat surfaces); communicate requirements up front; consider feature sets per environment.
- Mind comfort (avoid prolonged awkward device angles; keep game levels short with downtime) and safety (avoid encouraging rapid, sweeping, or large sudden motions; introduce motion gradually).
- Coaching: use the built-in coaching view (`ARCoachingOverlayView`) for initialization and relocalization; hide unrelated UI during coaching; build a custom coaching experience only with the system view for reference.
- Placing objects: use the coaching view to find a horizontal/vertical surface, then a custom indicator aligned to the surface plane; integrate a placed object immediately rather than waiting for refined data, then subtly nudge it onto the surface (`ARTrackedRaycast`); guide people to offscreen objects with visual/audible cues; don't try to align objects precisely to surface edges (boundaries are approximate); use plane classification (floor, table) to inform placement.
- Interactions: prefer direct manipulation when people aren't moving (indirect controls when they are); use standard gestures (single-finger drag to move, two-finger rotation to spin); keep interactions simple (limit movement to the 2D resting surface, limit rotation to a single axis); respond to gestures within reasonable proximity of small/thin/distant objects; allow scaling only when it helps (imaginary environments yes, real-world furniture-sizing no); watch for conflicting gestures (pinch vs two-finger rotation — test); keep object movement consistent with your AR physics and keep objects visible (no jumping/vanishing); explore motion and proximity as interaction inputs.
- Multiuser: each participant maps the environment independently and ARKit merges maps (`isCollaborationEnabled`); consider people occlusion for realism; let new participants join an ongoing experience via implicit map merging unless your app requires all up front.
- Reacting to real-world objects: supply 2D reference images / 3D reference objects for ARKit to detect (Detecting Images in an AR Experience). When a detected image disappears, wait up to one second before fading attached objects to prevent flicker; keep ARKit looking for 100 or fewer reference images at once (swap the active set by context if you need more); limit the number of reference images requiring an accurate position (use a tracked image when it may move or its attached content is small relative to the image).
- Communicating: use approachable, conversational terms — avoid "ARKit," "plane," "tracking," "insufficient features," "excessive motion." Prefer 3D hints in a 3D context (e.g. a rotation indicator around an object) over 2D text overlays; make important text readable in screen space (face the user; same type size regardless of distance); provide a clear way to tap for more info.
- Handling interruptions: ARKit can't track during an interruption (app switch, phone call), so objects may reappear in the wrong place — support relocalization (Managing Session Life Cycle and Tracking Quality). Use the coaching view to help people return the device to its prior position; hide previously placed objects during relocalization to avoid flicker; embed non-AR tasks within the AR experience to minimize interruptions; let people cancel relocalization (provide a reset button) since it continues indefinitely without success; indicate when the front-facing camera can't track a face for more than about half a second.
- Problem resolution: let people reset the experience rather than wait or struggle; suggest friendly fixes for failures (insufficient features → "Try turning on more lights and moving around"; excessive motion → "Try moving your phone slower"; slow surface detection → "Try moving around, turning on more lights, and making sure your phone is pointed at a sufficiently textured surface").
- Icons/badges: use the AR glyph only to launch an ARKit experience (adjust only size and color); maintain minimum clear space of 10% of the glyph's height. Use AR badges (collapsed/expanded) only to mark objects viewable in AR via ARKit, never altered; prefer the full AR badge over the glyph-only badge (use glyph-only for constrained spaces); badge only when the app mixes AR-viewable and non-AR objects; keep badge placement consistent in one corner, large enough to see but not occluding detail; maintain minimum clear space of 10% of the badge's height.

Canonical implementations: ARKit (`ARCoachingOverlayView`, `ARTrackedRaycast`, `ARWorldTrackingConfiguration.isCollaborationEnabled`); RealityKit.

**Specs:**

| Item | Value |
| --- | --- |
| Scene update rate | 60 times per second |
| Detected-image removal delay | up to 1 second before fading attached objects |
| Reference images in use | 100 or fewer at one time |
| Face-tracking loss indicator | when unable to track a face for more than ~0.5 second |
| Glyph/badge minimum clear space | 10% of glyph/badge height |

**Platform deltas:**
- iOS/iPadOS: No additional considerations.
- macOS/tvOS/watchOS: Not supported.
- visionOS: With the wearer's permission, use ARKit to detect surfaces, inform custom gestures from hand/finger positions, and incorporate nearby physical objects into immersive experiences.
