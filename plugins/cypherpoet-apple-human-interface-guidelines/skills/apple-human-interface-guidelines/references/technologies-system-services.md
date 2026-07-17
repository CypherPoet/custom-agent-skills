# Technologies — System Services

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Technologies pages: Siri, App Shortcuts, Snippets, Generative AI, Machine learning, Maps, Nearby interactions, NFC, CarPlay, Game Center, Designing for games, iCloud, Printing, VoiceOver.

**Contents:** [Siri](#siri) · [App Shortcuts](#app-shortcuts) · [Snippets](#snippets) · [Generative AI](#generative-ai) · [Machine learning](#machine-learning) · [Maps](#maps) · [Nearby interactions](#nearby-interactions) · [NFC](#nfc) · [CarPlay](#carplay) · [Game Center](#game-center) · [Designing for games](#designing-for-games) · [iCloud](#icloud) · [Printing](#printing) · [VoiceOver](#voiceover)

### Siri
*Last changed: 2026-06*

**Purpose:** Lets people find information and perform quick actions throughout the system and your app by voice, the Dynamic Island, or the Siri app — powered by Apple Intelligence on supported devices.

**Best practices:**
- Expose your app's features (intents) and content (entities) to Apple Intelligence via the App Intents framework — by default the system has no awareness of what your app can do.
- Adopt app schemas (preset templates for known domains like email, music, photos) to get built-in handling and deeper contextual understanding without extra work; fall back to App Shortcuts for custom actions outside those domains.
- Share contextual info: annotate onscreen views with app entities, donate entities to the on-device Spotlight index, and donate actions as intents so Siri can anticipate future actions.
- Identify your app's most popular actions and where they occur to prioritize what to expose.
- Use familiar terms for content and actions (track vs. song vs. podcast).
- Offer relevant content (recent searches, favorites, wishlist) rather than the whole catalog — email/messaging may justify full-catalog access.
- Don't advertise: no marketing or in-app-purchase pitches in Siri-delivered content.
- Only provide a custom response if built-in responses don't meet your needs.
- Write clear, descriptive response dialogue; customize follow-up questions ("Which soup?" not "Which one?").
- Keep responses succinct; avoid unnecessary words and humor that grate on repetition.
- Provide responses Siri can deliver both audibly and visually, and keep the voice response self-sufficient (e.g., AirPods get spoken forecast, iPhone shows it onscreen).
- Design inclusive interactions — avoid unnecessary pronouns ("Who should I send it to?" not "What's his or her name?").
- Ask an open-ended question when the option list is too long to read aloud.
- Keep responses device-independent; a request can start on one device and take effect on another.
- Omit your app name from responses — the system attributes your app.
- Use appropriate language and respect parental controls; others nearby may hear the response.
- Enhance default error descriptions to be situation-specific ("Sorry, we're out of chicken noodle soup").
- Editorial: refer to Siri by name, never pronouns; never impersonate Siri or reproduce its functionality; don't use reserved phrases like "Call 911" or "Hey Siri." In localization, translate only the word "Hey" — "Siri" is a trademark, never translated.

Canonical implementations: App Intents framework (intents + entities), app schema domains; SiriKit (legacy).

**Platform deltas:**
- No platform-specific section beyond the cross-device behavior noted above.

### App Shortcuts
*Last changed: 2026-06*

**Purpose:** Gives people access to your app's key functions or content throughout the system (Siri, Spotlight, Shortcuts app, Action button, Apple Pencil squeeze), available immediately on install.

**Use it when / not when:**
- Use when: exposing unique features or custom content in areas not covered by app schemas.
- Prefer app schemas when: surfacing common domain functionality (email, music, photos) — schemas let Siri surface features contextually without adopting individual App Shortcuts.

**Best practices:**
- Each app can include up to 10 App Shortcuts; each uses App Intents and bundles one or more actions.
- Offer App Shortcuts for your most common and important tasks; prefer tasks people can complete without leaving context, but you can open the app for multistep tasks.
- Add a single optional value (parameter) when it helps ("Start [morning, daily, sleep] meditation"); use predictable, familiar values since people won't see the list.
- Ask for clarification when a request omits optional info; suggest a sensible default plus a short alternatives list.
- Keep voice interactions simple — one parameter per phrase; ask for additional required info in a later step.
- Make App Shortcuts discoverable in-app with occasional tips (`SiriTipUIView`).
- Respond with dialogue Siri speaks, plus snippets (static info / confirmations) or Live Activities (timers, countdowns).
- Provide enough detail for audio-only devices (AirPods, HomePod) — put all critical info in the full dialogue text.
- Editorial: provide brief, memorable activation phrases and natural variants; you must include your app name but can be creative ("Create a Keynote" and "Add a new presentation in Keynote").
- Editorial: "App Shortcuts" / "Shortcuts" (the app) always title case and plural; individual "shortcuts" lowercase.

Canonical implementations: App Intents (`AppShortcutPhrase`, `LiveActivityIntent`), `SiriTipUIView`.

**Platform deltas:**
- iOS/iPadOS: App Shortcuts appear in Spotlight's Top Hit area or the Shortcuts area below, each with an SF Symbol or preview image. Order shortcuts by importance; the system later reprioritizes by usage frequency.
- macOS: App Shortcuts aren't supported, but App Intents actions are — people build custom shortcuts in the Shortcuts app on Mac.
- visionOS/watchOS: No additional considerations. Not supported in tvOS.

### Snippets
*Last changed: 2026-06*

**Purpose:** Compact views that appear in response to a Siri, Spotlight, or Shortcuts action to show a result or ask for confirmation.

**Use it when / not when:**
- Use a result snippet when: providing information that needs no further action (always shown by a snippet-displaying intent).
- Use a confirmation snippet when: people need to confirm/cancel, possibly with options that affect the result (the confirmation step is optional).

**Best practices:**
- Anatomy: spoken dialogue (system places it above the view), a custom view, and system buttons. Confirmation = secondary Cancel + a primary button with a customizable label; result = single Done button.
- Keep the custom view no taller than the 400-pt maximum height so all content is visible.
- Ensure sufficient contrast against the system background in light and dark, with consistent margins.
- Keep content concise; for more detail in a result snippet, deep-link into your app rather than expanding the view.
- Choose a descriptive primary-button label from `ConfirmationActionName` or a custom one ("Order" not "OK"); default is Continue.
- Communicate purpose visually — don't rely on the dialogue text; prefer omitting dialogue from the visual representation and convey info in the custom view.
- Be mindful that fonts draw at various sizes based on the person's preferred text size.

Canonical implementations: App Intents (`ConfirmationActionName`, displaying static and interactive snippets).

**Platform deltas:**
- No additional considerations for iOS, iPadOS, or macOS. Not supported in tvOS, visionOS, or watchOS.

### Generative AI
*Last changed: 2026-06*

**Purpose:** Uses machine learning models to create and transform text, images, and other content, enabling features for creative expression, communication, and productivity.

**Best practices:**
- Design responsibly: account for direct and indirect impacts; small input changes (or the same input) can produce very different outcomes, so build for all real-world situations, inclusively and privately.
- Keep people in control: honor in-scope requests, handle sensitive content carefully, let people dismiss/revert/retry generated content, and clearly identify when and where you use AI.
- Ensure an inclusive experience: models favor common data and can encode bias; ask for needed info rather than inferring personal/cultural traits, seek clarity before assuming, and test across a diverse set of people.
- Offer generative features only where they give clear, specific value (time savings, better communication, enhanced creativity).
- Provide a non-AI fallback when possible — ensure a great experience even when generative features are unavailable or people opt out (Genmoji vs. regular emoji; notification summaries vs. reading directly).
- Transparency: communicate where your app uses AI; never trick someone into thinking AI content is human-authored; align disclosure with regional regulations.
- Transparency: set clear expectations about what the feature can and can't do — offer a brief tutorial, curated suggestions for open-ended prompts, and up-front notice of known limitations.
- Privacy: choose a model type that fits the need and protects privacy — on-device models keep data local, respond quickly, work offline; server-based models suit larger context/processing but require minimizing and disclosing what's shared.
- Privacy: ask permission before using personal info and usage data, use the minimum needed, offer an opt-out, get explicit permission for storage/training use, and note stricter rules for kids' apps.
- Privacy: clearly disclose how the app and model use and store personal info, including whether it's used for training.
- Models/datasets: evaluate model capabilities early (Foundation Models requires a compatible device with Apple Intelligence on); be intentional about datasets, ensure licenses, include diverse representation, and test to mitigate bias and misinformation.
- Inputs: guide people with diverse predefined example inputs.
- Inputs: minimize hallucinations by scoping requests tightly; avoid requesting factual info unless the model has verified, up-to-date access; never use AI content where a hallucination could harm someone.
- Inputs: get permission before irreversible or problematic tasks; avoid automating destructive actions (deleting photos) or hard-to-undo ones (purchases); ask confirmation before significant actions; follow model usage policies and regional AI law.
- Outputs: make it easy to refine or revert results (Edit, Undo, Retry, Adjust near content) and acknowledge when corrections take effect.
- Outputs: help people improve blocked/undesirable requests by coaching them ("Unable to use that description") and offering example requests.
- Outputs: reduce harmful outcomes via thoughtful design and thorough testing of out-of-scope, vague, sensitive, and adversarial requests.
- Outputs: avoid replicating copyrighted content — build on protective base models, curate inputs, offer pre-approved prompts, and instruct the model to avoid mimicking specific content/styles.
- Outputs: factor in latency — generative models are slower than real-time models (ARKit body tracking, Vision); design a loading experience or generate in the background.
- Outputs: give specific, reassuring progress feedback ("Finding substitutions for ingredients" not "Processing…").
- Outputs: consider offering alternate versions so people can pick (Image Playground).
- Continuous improvement: update the model over time (frequent updates like blocked-word lists, larger changes around app releases); plan fine-tuning and retesting when moving to a newer base model.
- Continuous improvement: let people give voluntary, unobtrusive feedback (thumbs-up/down plus detailed option) and act on it.
- Continuous improvement: design flexible features (separate the model from the UX) so you can swap models as capabilities improve.

Canonical implementations: Foundation Models framework, Core AI.

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, visionOS, or watchOS.

### Machine learning
*Last changed: 2026-06*

**Purpose:** Lets apps and games learn from data and usage patterns to improve existing experiences and create new ones (recommendations, recognition, personalization).

**Best practices:**
- Classify your feature's role to guide design decisions:
  - Critical or complementary — the more central the feature, the more people expect accuracy; people forgive secondary-feature mistakes more.
  - Private or public — the more sensitive the data, the worse an inaccurate result; always protect privacy.
  - Proactive or reactive — proactive features (unrequested) get less tolerance for low quality.
  - Visible or invisible — invisible features struggle to communicate reliability or gather feedback.
  - Dynamic or static — dynamic models improve as people interact (often with calibration and feedback); static improve only on app update.
- Explicit feedback (info people provide on request): request only when necessary, always make it voluntary, use simple direct language ("Suggest less pop music" — avoid vague terms like "dislike"), add icons only as a supplement, offer multiple progressively specific options, act immediately and persist changes. Favoriting and social feedback are actually implicit feedback.
- Implicit feedback (info from interactions): always secure it, tell people how info is gotten/shared and let them restrict it, don't let it shrink exploration, combine multiple signals to infer intent, withhold private/sensitive suggestions on shared devices, prioritize recent feedback, update predictions at a cadence matching the mental model, account for UI changes shifting feedback, and beware confirmation bias.
- Calibration (info a feature needs to function, e.g., Face ID face scan): only use when the feature can't work without it; secure the info; be clear why you need it (emphasize what it does, not how); collect only essentials; avoid repeating it and do it early; make it quick with clear goals and progress; assist immediately if progress stalls (never imply fault); confirm success; allow cancel anytime; let people update or remove the info.
- Mistakes are inevitable: anticipate and mitigate them, help people handle them, and learn from them when it improves the app. Match corrective tools to the seriousness of the consequence, make frequent/predictable mistakes easy to correct, address mistakes without complicating the UI when possible, and be especially careful with proactive features.
- Corrections (people fixing app mistakes): give familiar easy ways to correct (Photos auto-crop reuses the same crop controls), provide immediate value and persist, let people correct their corrections, balance feature benefit vs. correction effort, never rely on corrections to mask low quality, learn from corrections only when quality improves, and prefer guided corrections (suggested alternatives) over freeform.
- Multiple options: can give a greater sense of control; prefer diverse options (Maps routes — no tolls, scenic, highways), avoid too many (increases cognitive load; keep on one screen), list the most likely first (optionally selected by default), make options easy to distinguish, and learn from selections.
- Confidence: verify confidence correlates with quality before showing it; translate values into concepts people understand; prefer ranking/ordering or semantic categories ("high chance"/"low chance") over raw numbers, except where statistical/numerical info is expected (weather, sports, polling); convey confidence as actionable suggestions ("This is a good time to buy"); adapt presentation across thresholds (Photos asks to confirm faces at lower confidence); generally avoid showing low-confidence results, especially for proactive features (set a threshold).
- Attribution (the rationale for a result, "Because you've read mysteries"): use to aid transparency and distinguish results; avoid being too specific or too general; keep it factual and objective ("Because you've read nonfiction" not "Because you love nonfiction"); avoid technical/statistical jargon except for statistical results.
- Limitations (what a feature can't do well or at all): set expectations before use, demonstrate how to get the best results (placeholder text, real-time feedback like Memoji's "Low light," alternative suggestions over no results), explain why inferior results occur, and consider telling people when a limitation is resolved.

Canonical implementations: Core ML, Create ML.

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, visionOS, or watchOS.

### Maps
*Last changed: 2024-12*

**Purpose:** Displays outdoor or indoor geographical data in your app or website, supporting zoom, pan, rotation, annotations, overlays, routing, and standard/satellite/hybrid views.

**Best practices:**
- In general, make your map interactive — people expect to zoom, pan, and interact; noninteractive elements that obscure the map break expectations.
- Pick an emphasis style: default (fully saturated, good for standard maps and visual alignment with the Maps app) or muted (desaturated, good when information-rich content must stand out). See `MKStandardMapConfiguration.EmphasisStyle`.
- Help people find places — offer search plus category filters.
- Clearly identify selected elements with distinct styling (outline, color variation).
- Cluster overlapping points of interest into a single pin; expand progressively on zoom.
- Keep the Apple logo and legal link visible: don't cover them permanently; use ~7 pt side padding and 10 pt above/below; keep them fixed to the map (not moving with your UI); if your UI moves, place them 10 pt above the lowest resting position of the moving element.
- Custom info: use annotations matching your app's visual style — default marker is red tint with white pin; you can change tint and use an icon string (keep to 2–3 characters) or image (`MKAnnotationView`).
- Make Apple-provided map features (points of interest, territories, physical features) independently selectable when displaying related custom info (`MKMapFeatureOptions`).
- Use overlays at a level matching their relationship: "above roads" (default; above roads, below buildings/trees) or "above labels" (above roads and labels, hiding everything beneath) (`MKOverlayLevel`).
- Ensure enough contrast between custom controls and the map (thin stroke, light drop shadow, or blend modes).
- Place cards (rich place info — hours, phone, address): choose a style — automatic, callout (full or compact), caption ("Open in Apple Maps" link), or sheet. Full callout shows as a popover in iPadOS/macOS and a sheet in iOS.
- Choose a place-card style that fits the context (compact callout for small maps with many annotations), keep content viewable across devices/window sizes (set a minimum width for full callout), avoid duplicating info your app already shows, and keep the selected location visible (set an offset).
- Indoor maps: adjust detail by zoom level (large areas always, finer features on zoom-in); use distinctive color + icons; offer a floor picker with concise numbers; include surrounding areas for context (dim noninteractive ones); limit scrolling outside the venue; support routing to nearby transit; and design the map as a natural extension of your app rather than replicating Apple Maps (see Indoor Mapping Data Format).

Canonical implementations: MapKit, MapKit JS; Indoor Mapping Data Format (IMDF).

**Specs:**

| Element | Spec |
| --- | --- |
| Logo/link side padding | ~7 pt |
| Logo/link top/bottom padding | 10 pt |
| Icon-string annotation length | 2–3 characters |

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, or visionOS.
- watchOS: Maps are static, non-interactive snapshots; tapping opens the Maps app. Add up to 5 annotations. Fit the entire map element onscreen without scrolling and show the smallest region encompassing all points of interest (`WKInterfaceMap`).

### Nearby interactions
*Last changed: 2023-06*

**Purpose:** Supports on-device experiences that integrate the presence of nearby people and objects using Ultra Wideband (UWB), via the Nearby Interaction framework.

**Best practices:**
- People grant permission before participating; the APIs preserve privacy with randomly generated device identifiers that last only as long as the session.
- Find inspiration by thinking about a task from the physical-world perspective (transfer a song by bringing iPhone and HomePod mini close).
- Use distance, direction, and context to inform interactions; prioritize nearby, contextually relevant info (share sheet suggesting the closest contact the person faces via U1 chip).
- Mirror physical perception — feedback should sharpen as objects get closer (AirTag: directional arrow transitions to a pulsing circle).
- Provide continuous, uninterrupted feedback that responds to movement (Find My direction and proximity updates).
- Use multiple feedback types (visual, audible, haptic) and transition fluidly to match task and context.
- Never make a nearby interaction the only way to perform a task — provide alternatives.
- Device usage: encourage portrait orientation (landscape lowers accuracy); prefer implicit visual cues over explicitly telling people to hold portrait; design for the directional field of view (similar to the iPhone 11+ Ultra Wide camera — outside it you may get distance but not direction); help people understand that intervening objects/people/animals reduce accuracy.

Canonical implementations: Nearby Interaction framework.

**Platform deltas:**
- iOS: APIs provide a peer device's distance and direction.
- watchOS: APIs provide a peer device's distance only; all participating watchOS apps must be in the foreground.
- No additional considerations for iPadOS. Not supported in macOS, tvOS, or visionOS.

### NFC

**Purpose:** Lets iOS apps on supported devices read data from electronic tags attached to real-world objects via near-field communication scanning.

**Use it when / not when:**
- Use in-app tag reading when: the app is active — display a scanning sheet for single- or multiple-object scans.
- Use background tag reading when: people should scan quickly without opening the app first — the system looks for tags whenever the screen is illuminated and shows a tappable notification. Unavailable when an NFC scanning sheet is visible, Wallet/Apple Pay are in use, cameras are in use, Airplane Mode is on, or the device is locked after a restart.

**Best practices:**
- Don't encourage physical contact — the device only needs to be in close proximity; use "scan" and "hold near," not "tap" and "touch."
- Use approachable terminology — avoid technical terms (NFC, Core NFC, near-field communication, tag); use friendly, conversational words.
- Provide succinct instructional text for the scanning sheet — a complete sentence in sentence case with ending punctuation, identifying the object, kept short to avoid truncation, and revised for subsequent scans ("Now hold your iPhone near another [object]").
- Support both background and in-app tag reading — always provide an in-app path for devices that don't support background reading.

Canonical implementations: Core NFC.

**Platform deltas:**
- No additional considerations for iOS or iPadOS. Not supported in macOS, tvOS, visionOS, or watchOS.

### CarPlay
*Last changed: 2023-05*

**Purpose:** Shows compatible iPhone apps on the car's built-in display so drivers can get directions, call, message, and listen to audio while staying focused on the road.

**Best practices:**
- Build the interface from system-defined templates for your app type (audio, communication, navigation, fueling); your app supplies content and iOS renders it — no custom UI, no adjusting for screen resolution or hardware input.
- Design for the driving context — features should let people complete tasks quickly with minimal interaction.
- iPhone interactions: eliminate app interactions on iPhone when CarPlay is active (use the car's controls/display); require any iPhone setup before the vehicle moves; never lock people out of CarPlay because iPhone needs input; make sure the app works without unlocking iPhone (most people use CarPlay while iPhone is locked).
- Audio: let people choose when to start playback (avoid auto-play unless single-source or resuming); don't start an audio session until ready to play (it silences the car radio); start playback as soon as audio sufficiently loads (system shows a spinner until ready); show the Now Playing screen when audio is ready, loading descriptive info in the background; resume after temporary interruptions (phone call) but not permanent ones (a Siri playlist); adjust relative audio levels but never the overall volume.
- Layout: provide high-value info in a clean, scannable layout; keep a consistent appearance (similar functions look similar); make primary content stand out and feel actionable; place the most important content/controls in the upper half of the screen.
- Color: prefer a limited palette coordinated with your app logo; don't use the same color for interactive and noninteractive elements; test under varied real-car lighting (day/night, weather, tinting); ensure it looks great in both dark and light appearances (CarPlay may auto-switch).
- Icons/images: supply @2x and @3x artwork; mirror your iPhone app icon; don't use black for the icon background (lighten it or add a border).
- Error handling: report errors in CarPlay, never directing people to their iPhone.

Canonical implementations: CarPlay templates (see CarPlay App Programming Guide).

**Specs:**

| Common screen size (pixels) | Aspect ratio |
| --- | --- |
| 800x480 | 5:3 |
| 960x540 | 16:9 |
| 1280x720 | 16:9 |
| 1920x720 | 8:3 |

| App icon | Size (pixels) |
| --- | --- |
| @2x | 120x120 |
| @3x | 180x180 |

**Platform deltas:**
- No additional considerations for iOS. Not supported in iPadOS, macOS, tvOS, visionOS, or watchOS.

### Game Center
*Last changed: 2025-06*

**Purpose:** Apple's social gaming network — lets players track progress, connect with friends across Apple platforms, and boosts discovery of your game, via the GameKit framework.

**Best practices:**
- On launch, check whether the player is signed in to Game Center; if not, initialize them then — this gives the most seamless experience and maximizes discovery (Top Played chart, social recommendations).
- Access point (Apple-designed UI element to view profile/info without leaving the game): display it on menu screens (main menu or settings), not during gameplay, splash, cinematics, or tutorials; present it at one of the four corners in a fixed position, avoiding overlap with controls (it has collapsed and expanded states); consider pausing the game while the Game Overlay (iOS/iPadOS/macOS) or dashboard (visionOS/tvOS) is present.
- Custom UI: you can deep-link into the Game Overlay or dashboard; use official Game Center artwork from Apple Design Resources without altering dimensions/effects; use correct terminology ("Game Center," "Game Center Profile," "Achievements," "Leaderboards," "Challenges," "Add Friends" — not GameKit, Profile, Trophies, Rankings, etc.).
- Achievements: align with the four states (locked, in-progress, hidden, completed — grouped into Completed and Locked); upload order = display order; be succinct (title and description limited to 2 lines each, title case / sentence case); use progressive achievements for progress messages; design rich high-quality images (don't reuse one asset for multiple achievements; circular mask, keep content centered).
- Leaderboards: choose classic (best all-time score, always active) or recurring (resets on an interval — daily/weekly, boosts engagement); use leaderboard sets to organize multiple boards by theme; add a unique image per leaderboard (single image for iOS/iPadOS/macOS, an animating set for tvOS focus effects).
- Challenges (multiplayer competitions built on leaderboards, with time limits): create short skill-based activities of 1–5 minutes that players complete individually; avoid tracking overall progress or personal-best scores (unfair to regulars) — track the most recent score per attempt; make it easy to jump in (deep-link to the exact mode/level, complete onboarding first); create high-quality artwork (keep primary content clear of title/description; provide localized text versions).
- Multiplayer activities (real-time and turn-based): use party codes (alpha-numeric, typically 8 characters like "2MP4-9CMF") — allow late join/early leave/return, show the current code, and allow manual entry; support multiplayer through in-game UI (invite nearby/recent players, friends, contacts) or custom UI; provide engaging activity artwork.

Canonical implementations: GameKit.

**Specs:**

Achievement image (iOS, iPadOS, macOS, visionOS):

| Attribute | Value |
| --- | --- |
| Format | PNG, TIF, or JPG |
| Color space | sRGB or P3 |
| Resolution | 72 DPI (minimum) |
| Image size | 512x512 pt (1024x1024 px @2x) |
| Mask diameter | 512 pt (1024 px @2x) |

Achievement image (tvOS):

| Attribute | Value |
| --- | --- |
| Image size | 320x320 pt (640x640 px @2x) |
| Mask diameter | 200 pt (400 px @2x) |

Leaderboard image (iOS, iPadOS, macOS):

| Attribute | Value |
| --- | --- |
| Format | JPEG, JPG, or PNG |
| Image size | 512x512 pt (1024x1024 px @2x) |
| Cropped area | 512x312 pt (1024x624 px @2x) |

Leaderboard image (tvOS, multi-layered):

| Attribute | Value |
| --- | --- |
| Image size | 659x371 pt (1318x742 px @2x) |
| Focused size | 618x348 pt (1236x696 px @2x) |
| Unfocused size | 548x309 pt (1096x618 px @2x) |

Challenge / multiplayer activity image:

| Attribute | Value |
| --- | --- |
| Format | JPEG, JPG, or PNG |
| Image size | 1920x1080 pt (3840x2160 px @2x) |
| Cropped area | 1465x767 pt (2930x1534 px @2x) |

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, or visionOS.
- tvOS: optionally add a dashboard image (600x180 pt / 1200x360 px @2x; PNG/TIF/JPG, sRGB or P3, 72 DPI min) — simple and recognizable; use a logo or word mark, not the app icon.
- watchOS: GameKit features and API are available, but there's no system Game Center UI to invoke — content appears on a connected iPhone.

### Designing for games
*Last changed: 2025-06*

**Purpose:** Platform-wide guidance for integrating Apple platform characteristics and patterns so a game feels at home across Apple devices.

**Best practices:**
- Jump into gameplay: let people play as soon as installation completes — include as much playable content as possible in the initial install while keeping download time to 30 minutes or less, and download more in the background.
- Provide great default settings using device info (resolution, paired accessories/controllers, accessibility settings); support the platform's most common interaction methods.
- Teach through play — integrate onboarding into a playable tutorial; offer any written tutorial as a reference, not a prerequisite.
- Defer permission and rating requests until the right time — tie a sensor/data request to the scenario that needs it; let people spend quality time before asking for a rating or review.
- Look stunning: keep text legible (good contrast, at least the minimum text size per platform); keep buttons easy to use (at least the minimum button size; iOS touch buttons must be 44x44 pt); prefer resolution-independent textures (vector art in visionOS); accommodate device features (rounded corners, camera housing) using safe areas; make in-game menus adapt to aspect ratios (16:10, 19.5:9, 4:3) and both iPhone/iPad orientations with dynamic relative layouts; design for full-screen (macOS/iOS/iPadOS full-screen mode, visionOS Full Space).
- Enable intuitive interactions: support each platform's default interaction method; support physical game controllers but always give alternatives (not everyone can use one); offer touch-based controls that embrace the touchscreen on iPhone/iPad.
- Welcome everyone: prioritize perceivability (don't rely solely on color; provide subtitles for cutscenes); help players personalize (type size, control mapping, motion intensity, sound balance) using Apple accessibility technologies; let players represent themselves across the spectrum of self-identity; avoid stereotypes in stories and characters.
- Adopt Apple technologies: integrate Game Center (GameKit) for discovery, leaderboards, challenges, multiplayer; support GameSave so players resume on any device via their iCloud account; support haptics (Core Haptics — iOS, iPadOS, tvOS, visionOS, and many controllers); use Spatial Audio (multichannel) to immerse players; use AR, machine learning, HealthKit, camera/microphone/location for unique mechanics.

Canonical implementations: GameKit, GameSave, Core Haptics; Unity plug-ins for non-native games.

**Specs:**

Text size by platform:

| Platform | Default | Minimum |
| --- | --- | --- |
| iOS, iPadOS | 17 pt | 11 pt |
| macOS | 13 pt | 10 pt |
| tvOS | 29 pt | 23 pt |
| visionOS | 17 pt | 12 pt |
| watchOS | 16 pt | 12 pt |

Button size by platform:

| Platform | Default | Minimum |
| --- | --- | --- |
| iOS, iPadOS | 44x44 pt | 28x28 pt |
| macOS | 28x28 pt | 20x20 pt |
| tvOS | 66x66 pt | 56x56 pt |
| visionOS | 60x60 pt | 28x28 pt |
| watchOS | 44x44 pt | 28x28 pt |

Interaction methods by platform:

| Platform | Default | Additional |
| --- | --- | --- |
| iOS | Touch | Game controller |
| iPadOS | Touch | Game controller, keyboard, mouse, trackpad, Apple Pencil |
| macOS | Keyboard, mouse, trackpad | Game controller |
| tvOS | Remote | Game controller, keyboard, mouse, trackpad |
| visionOS | Touch | Game controller, keyboard, mouse, trackpad, spatial game controller |
| watchOS | Touch | – |

**Platform deltas:**
- Every platform except watchOS supports physical game controllers. See per-platform interaction-method table above.

### iCloud
*Last changed: 2025-06*

**Purpose:** A service that lets people seamlessly access their content (photos, videos, documents, and more) from any device without explicit synchronization — built on transparency, so people always assume they're accessing the latest version.

**Best practices:**
- Make it easy to use your app with iCloud — people turn it on in Settings and expect apps to work with it automatically; if a choice is warranted, show a simple "all data or not at all" option on first launch.
- Avoid asking which documents to keep in iCloud — most people expect everything available and don't want per-document management; automate file management.
- Keep content up to date, balanced against storage and bandwidth; for very large documents, let people control downloads and indicate when a newer version is available; show subtle feedback if a download takes more than a few seconds.
- Respect iCloud storage (a finite, paid resource) — store content people create, not regenerable resources; note that iCloud backups include every app's Documents folder, so be picky about what goes there.
- Behave appropriately when iCloud is unavailable — no alert needed when someone turns it off or enables Airplane Mode, but unobtrusively note that changes won't reach other devices until access is restored.
- Keep app-state info in iCloud (last page read) when those settings should apply across all devices — some settings are more device- or context-specific.
- Warn about deletion consequences — deleting a document removes it from iCloud and all devices; show a warning and ask for confirmation.
- Make conflict resolution prompt and easy — resolve automatically when possible; otherwise show an unobtrusive notification to differentiate and choose between versions, as early as possible.
- Include iCloud content in search results.
- For games, consider saving player progress in iCloud — the GameSave framework syncs save data across devices and offers built-in alerts (or custom UI) for offline/conflict situations.

Canonical implementations: CloudKit, GameSave.

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, visionOS, or watchOS.

### Printing

**Purpose:** Lets an iOS, iPadOS, macOS, or visionOS app integrate system-provided print functionality, with custom printer- and document-specific options when needed.

**Best practices:**
- Make printing discoverable in standard locations — a Print item in a macOS File menu; a toolbar button opening an action sheet in iOS/iPadOS; optionally a customizable Print button in a macOS toolbar.
- Present a printing option only when it's possible — dim the macOS File-menu Print item and remove the iOS/iPadOS Print action when there's nothing to print or no printers; dim or hide a custom print button accordingly.
- Present relevant printing options (page range, copies, double-sided) using the system-provided view when the printer supports them.

Canonical implementations: `UIPrintInteractionController` (UIKit), `NSDocument` (AppKit).

**Platform deltas:**
- No additional considerations for iOS, iPadOS, or visionOS. Not supported in tvOS or watchOS.
- macOS: for app-specific options, create a custom print-panel category with a unique name (e.g., your app name) — Keynote adds presenter notes, slide backgrounds, skipped slides; for document page settings, consider a page setup dialog but don't reimplement what the system provides (orientation, reverse order); make option interdependencies clear; separate advanced features behind a disclosure control labeled "Advanced Options"; consider letting people preview a setting's effect; consider storing modified settings with the document (at least until it's closed).

### VoiceOver
*Last changed: 2025-03*

**Purpose:** A screen reader that lets people who are blind or have low vision experience your app's interface and content without seeing the display.

**Best practices:**
- Supported across Apple platforms and in Unity via Apple's Unity plug-ins.
- Descriptions: provide alternative labels for all key interface elements — system controls have generic labels by default, so supply descriptive ones and label custom elements; keep them current as the UI changes (Accessibility modifiers / View-Accessibility).
- Describe meaningful images, conveying only what the image itself shows (VoiceOver already handles surrounding captions).
- Make charts and infographics fully accessible — give a concise description and expose interactions to VoiceOver too.
- Exclude purely decorative images from VoiceOver to reduce cognitive load (`accessibilityHidden(_:)`, `isAccessibilityElement`).
- Navigation: use unique titles and accurate section headings — the title is the first thing an assistive technology announces on a screen.
- Specify how elements are grouped, ordered, or linked when relationships are visual only; group related elements so VoiceOver reads each image with its caption rather than all images then all captions (`shouldGroupAccessibilityChildren`). VoiceOver reads in the reading order of the active language/locale.
- Inform VoiceOver when visible content or layout changes occur, so people can update their mental map (`AccessibilityNotification`).
- Support the VoiceOver rotor — identify headings, links, and other content types so people can navigate by them (and bring up the braille keyboard) (`AccessibilityRotorEntry`, `UIAccessibilityCustomRotor`, `NSAccessibilityCustomRotor`).

Canonical implementations: SwiftUI accessibility modifiers, UIKit (`isAccessibilityElement`, `UIAccessibilityCustomRotor`), AppKit (`NSAccessibilityCustomRotor`).

**Platform deltas:**
- No additional considerations for iOS, iPadOS, macOS, tvOS, or watchOS.
- visionOS: with VoiceOver on, apps/games with custom gestures don't receive hand input by default (so people can explore by voice); people can opt out via Direct Gesture mode, which disables standard VoiceOver gestures and lets the app process hand input directly.
