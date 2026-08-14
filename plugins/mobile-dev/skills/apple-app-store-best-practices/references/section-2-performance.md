# Section 2: Performance

> Source: https://developer.apple.com/app-store/review/guidelines/
> Last synced: 2026-07-17

## Table of Contents

| Section | Covers |
|---|---|
| [§2.1 App Completeness](#21-app-completeness) | §2.1(a) Final Versions Only and §2.1(b) In-App Purchases Complete |
| [§2.2 Beta Testing](#22-beta-testing) | Requirement: Betas, demos, trial versions, and pre-release builds must be distributed through TestFlight, not the App Store |
| [§2.3 Accurate Metadata](#23-accurate-metadata) | §2.3.1 Hidden or Undocumented Features, §2.3.2 In-App Purchase Metadata, §2.3.3 Screenshots, and related topics |
| [§2.4 Hardware Compatibility](#24-hardware-compatibility) | §2.4.1 iPhone Apps on iPad, §2.4.2 Power Efficiency, §2.4.3 Apple TV Remote Compatibility, and related topics |
| [§2.5 Software Requirements](#25-software-requirements) | §2.5.1 Public APIs Only, §2.5.2 Self-Contained Bundles, §2.5.3 No Malicious Code, and related topics |

---

## §2.1 App Completeness

### §2.1(a) Final Versions Only

**Requirement:** Apps submitted for review must be final, fully functional versions. No beta, demo, trial, or test builds.

**Triggers rejection if:**
- Placeholder or "lorem ipsum" text appears anywhere in the app
- Broken links, empty sections, or incomplete UI flows exist
- The app crashes or exhibits obvious bugs during review
- Backend services or APIs the app depends on are offline or returning errors
- No demo account is provided when login is required (include credentials in App Review Notes)
- App content is not fully loaded or populated

**What to check:**
- Search all `.strings`, `.stringsdict`, and `.xcstrings` files for placeholder patterns (`lorem`, `TODO`, `placeholder`, `test`, `sample`, `FIXME`, `TBD`, `CHANGEME`)
- Search storyboard/XIB files and SwiftUI views for hardcoded placeholder text
- Grep source files for `#warning`, `// TODO`, `// FIXME`, `// HACK` that indicate unfinished work
- Verify `Info.plist` URLs (support URL, privacy policy URL, marketing URL) resolve to live pages
- Check for test/staging API base URLs in source or config files (e.g., `staging.`, `dev.`, `localhost`, `127.0.0.1`, `0.0.0.0`)
- Verify App Review Notes field in App Store Connect metadata includes demo credentials if the app has login
- Look for debug/test flags that gate features (`isDebug`, `isTestFlight`, `#if DEBUG` guarding user-facing features)

**Key details:**
- Apple will test on actual devices running the latest OS
- If the app requires specific hardware or real-world conditions (e.g., location-based features), explain in review notes how to test
- Apps that are "shells" for a website with minimal native functionality will also be rejected under completeness

---

### §2.1(b) In-App Purchases Complete

**Requirement:** All in-app purchase products must be complete and functional at the time of review submission.

**Triggers rejection if:**
- IAP products are listed in App Store Connect but not yet implemented in the app
- Purchasing an IAP leads to an error, empty content, or a "coming soon" state
- IAP content or features are not accessible after purchase during review

**What to check:**
- Cross-reference IAP product identifiers in source code (search for `SKProduct`, `Product`, `StoreKit`, product ID strings) against what is registered in App Store Connect
- Verify StoreKit configuration files (`.storekit`) if present in the Xcode project
- Check that purchase completion handlers deliver content or unlock features (not just log success)
- Search for "coming soon" or "under construction" strings gated behind IAP product IDs

**Key details:**
- If the app uses a server to deliver IAP content, that server must be live and serving content during review
- Subscription IAPs must clearly show what the user gets at each tier

---

## §2.2 Beta Testing

**Requirement:** Betas, demos, trial versions, and pre-release builds must be distributed through TestFlight, not the App Store. Apps on the App Store must be intended for public distribution.

**Triggers rejection if:**
- App name, metadata, or UI contains "beta", "demo", "trial", "preview", "early access", or "pre-release"
- App is clearly a test or evaluation build not intended for end users
- Users are offered compensation (monetary or otherwise) to use the app as testers

**What to check:**
- Search `Info.plist` `CFBundleDisplayName` and `CFBundleName` for beta/test/demo keywords
- Search App Store Connect metadata (app name, subtitle, description, keywords) for these terms
- Grep source code and UI strings for "beta", "demo", "trial", "preview", "early access", "pre-release"
- Check for TestFlight-specific code paths that should not ship to production (e.g., `Bundle.main.appStoreReceiptURL?.lastPathComponent == "sandboxReceipt"` used to toggle beta features)

**Key details:**
- TestFlight beta apps can remain in beta for up to 90 days per build
- An app that is functionally complete but marketed as "beta" will still be rejected from the App Store

---

## §2.3 Accurate Metadata

### §2.3.1 Hidden or Undocumented Features

#### §2.3.1(a) No Hidden Features or Misleading Marketing (ASR & NR)

**Requirement:** Apps must not contain hidden, dormant, or undocumented features. All new features and functionality changes must be disclosed in the App Review Notes. Marketing text must accurately represent what the app does and not include false claims (e.g., promoting unavailable content, false pricing, fake malware scanners).

**Triggers rejection if:**
- Features exist in the binary that are not described in metadata or review notes
- Remote config or feature flags enable functionality post-review that was not present during review
- Marketing screenshots or descriptions promise features the app does not actually deliver
- App behavior changes based on geographic region, date, or A/B test group in ways not disclosed
- Marketing makes false claims (e.g., misleading pricing, "iOS malware scanner" features)

**What to check:**
- Search for remote config / feature flag SDKs (`FirebaseRemoteConfig`, `LaunchDarkly`, `Optimizely`, `Unleash`, custom feature flag implementations)
- Identify features gated behind flags and verify they are documented in review notes
- Look for date-based or region-based conditional logic that enables hidden features (`Date()`, `Locale.current`, `TimeZone.current` used in feature gating)
- Compare marketing description claims against actual implemented features in the codebase
- Check for URL scheme handlers or deep links that expose undocumented functionality

**Key details:**
- If using feature flags, clearly document all possible states in review notes
- "Easter eggs" and hidden gestures that unlock features count as undocumented functionality
- Server-driven UI that can change the app's behavior post-review is scrutinized heavily

#### §2.3.1(b) Dishonest Behavior

**Requirement:** Egregious or repeated dishonest behavior is grounds for removal from the Apple Developer Program.

**Triggers rejection if:**
- Repeated violations of §2.3.1(a) (hidden features, false marketing) across submissions
- Pattern of misrepresentation in metadata, review notes, or marketing
- Attempts to mislead App Review about app functionality, content, or business model

**What to check:**
- Account-level history of prior rejections related to honesty/transparency
- Whether prior reviewer feedback about misleading content has been addressed
- Consistency between what the app does, what metadata says, and what review notes claim

**Key details:**
- Consequences extend beyond app rejection to full Developer Program removal
- "Egregious" includes attempts to actively deceive App Review (e.g., behavior that changes after approval)

---

### §2.3.2 In-App Purchase Metadata

**Requirement:** App metadata must clearly indicate that in-app purchases are available, including what they are and how much they cost.

**Triggers rejection if:**
- App uses IAP but the description does not mention it
- IAP pricing or content descriptions are misleading or missing from metadata

**What to check:**
- Verify the App Store Connect description mentions in-app purchases if the source code imports `StoreKit` or `StoreKit2`
- Check that IAP product display names and descriptions in App Store Connect are accurate and non-misleading
- Confirm the app's screenshots or previews don't show premium content as if it were free

**Key details:**
- Apple displays an "In-App Purchases" badge automatically, but the description should still explain what is purchasable
- Subscription apps must clearly communicate pricing, billing frequency, and cancellation terms

---

### §2.3.3 Screenshots

**Requirement:** Screenshots must show the app in use. They should accurately represent the app experience on the device.

**Triggers rejection if:**
- Screenshots are purely marketing graphics with no actual app UI
- Screenshots show UI or features that do not exist in the current version
- Screenshots show content from a different app or platform
- Screenshots include device frames that do not match the target device

**What to check:**
- Review screenshot assets in the App Store Connect metadata or fastlane `screenshots/` directory
- Verify screenshots correspond to actual screens in the app's view hierarchy
- Check that screenshot dimensions match required sizes for each device class
- Flag screenshots that appear to be generic stock images or purely illustrative marketing art with no app UI

**Key details:**
- Screenshots can include text overlays and marketing callouts as long as the actual app UI is prominently shown
- Each device size requires appropriately sized screenshots (iPhone 6.7", 6.5", 5.5"; iPad Pro 12.9", etc.)

---

### §2.3.4 App Previews

**Requirement:** App previews (video) must use only captured footage of the app itself. Previews should show the app experience accurately.

**Triggers rejection if:**
- Preview video contains footage not captured from within the app
- Preview includes misleading visual effects or content not in the app
- Preview shows a different app or non-app content

**What to check:**
- Review app preview video files in App Store Connect metadata
- Verify video content corresponds to actual app screens and workflows
- Flag any live-action footage, stock video, or non-app UI content in previews

**Key details:**
- App previews auto-play on the product page, so first few seconds matter
- Audio in previews should come from the app itself
- Previews may include text overlays explaining what is shown

---

### §2.3.5 App Category

**Requirement:** Apps must be assigned to the most appropriate category and subcategory for their functionality.

**Triggers rejection if:**
- Selected category does not match the app's primary purpose (e.g., a game categorized as "Education" to avoid competition)
- App is placed in a less competitive category to gain visibility

**What to check:**
- Review the primary and secondary category in App Store Connect metadata
- Compare against the app's core functionality as described in its source code and UI
- Flag mismatches (e.g., an app with `GameKit` imports categorized as "Utilities")

**Key details:**
- Apple may recategorize apps that are clearly in the wrong category
- Games must be in the Games category or a Games subcategory

---

### §2.3.6 Age Rating

**Requirement:** Answer the age rating questionnaire honestly so that parental controls and the store's age tiers work correctly. You answer the questions; Apple derives the tier from your answers (you may set a *higher* tier than Apple assigns, never a lower one).

**The current system (since 2025-07-24):** Apple replaced the old 4+/9+/12+/17+ scheme with five tiers (4+, 9+, 13+, 16+, 18+) for more granular ratings, and added required questionnaire sections for *every* app: **In-App Controls, Capabilities, Medical/Wellness topics, and Violent Themes**. Completing the updated questionnaire is mandatory; an app that never re-answers it can be held. See Apple's [age-rating values and definitions](https://developer.apple.com/help/app-store-connect/reference/age-ratings-values-and-definitions/) and the [2025-07-24 update notice](https://developer.apple.com/news/upcoming-requirements/?id=07242025a).

**Triggers rejection (or a forced re-rate) if:**
- The app contains mature content (violence, gambling, profanity, sexual content, drugs/alcohol references) but the rating is set too low
- It provides unrestricted web access but the matching answer isn't selected (that alone pushes the rating to 16+)
- User-generated content exists without the matching content answers and moderation
- The rating contradicts what reviewers observe in the app

**What to check:**
- Search source code for content that implies mature themes: gambling mechanics, alcohol/drug references, violence, profanity filters (a filter's presence implies the content exists)
- Check for `WKWebView` or `SFSafariViewController` usage that provides unrestricted web access (→ 16+)
- Look for user-generated content features (chat, forums, photo sharing) that require the UGC content answers
- Confirm the four sections added in 2025 (In-App Controls, Capabilities, Medical/Wellness, Violent Themes) are answered, not left at defaults
- **Export compliance:** set `ITSAppUsesNonExemptEncryption` in `Info.plist` so uploads skip the per-build encryption prompt. Use `NO` (`false`) when the app uses only *exempt* cryptography — HTTPS/TLS and Apple's standard OS crypto (Keychain, CryptoKit defaults) — which covers most apps; use `YES` only if you ship non-exempt/proprietary encryption (then export documentation may apply). Verify the value matches the binary's actual crypto.

**Key details:**
- Unrestricted web browsing maps to **16+** under the current scale (the old "17+" tier no longer exists)
- User-generated content typically requires higher ratings and content moderation
- A fixed-price in-app purchase is **not** gambling (no loot boxes or randomized rewards), so it does not by itself raise the rating

---

### §2.3.7 App Name and Keywords

**Requirement:** App names must be unique to the app and not infringe on trademarks. Keywords must be accurate and relevant. Keyword stuffing and gaming search rankings are prohibited.

**Triggers rejection if:**
- App name includes generic terms that are not the actual app name (e.g., "Best Photo Editor - Camera Filter")
- Keywords include competitor names, irrelevant popular terms, or trademarked terms the developer does not own
- App name exceeds 30 characters
- App subtitle exceeds 30 characters
- Keywords include terms duplicated from the app name or category

**What to check:**
- Review `CFBundleDisplayName` and `CFBundleName` in `Info.plist` for length and content
- Check App Store Connect metadata: app name, subtitle, keywords field
- Flag competitor brand names in keywords
- Flag keyword duplication between name, subtitle, and keyword fields (wasted space and policy risk)
- Check for special characters or emoji in the app name that might violate naming rules

**Key details:**
- Apple strictly enforces the 30-character limit for app names and subtitles
- Keyword field has a 100-character limit; use commas to separate, no spaces after commas
- Names cannot include pricing information ("Free", "$0.99")

---

### §2.3.8 Metadata Appropriate for All Ages

**Requirement:** All metadata (name, description, screenshots, previews, keywords) must be appropriate for an all-ages audience, regardless of the app's age rating. Metadata is rated 4+.

**Triggers rejection if:**
- App description, screenshots, or previews contain mature language, images, or themes
- Keywords include vulgar or adult terms
- App icon contains inappropriate imagery

**What to check:**
- Scan App Store Connect metadata text fields for profanity, sexual terms, violent language, or drug references
- Review app icon asset (`AppIcon` in asset catalog) for inappropriate imagery
- Review screenshot and preview assets for age-inappropriate content

**Key details:**
- Even if the app itself carries a high age rating (16+/18+), the metadata shown on the store page must be suitable for all audiences
- This is because children browsing the App Store can see metadata before any parental gate applies

---

### §2.3.9 Intellectual Property Rights

**Requirement:** Developers must have secured all necessary rights for content, materials, and IP used in the app and its metadata.

**Triggers rejection if:**
- App uses copyrighted images, music, video, or text without rights
- App icon or screenshots use trademarked logos without authorization
- Third-party content (fonts, sounds, images) is used without proper licensing

**What to check:**
- Review asset catalogs and resource bundles for third-party content
- Check for embedded fonts and verify license files exist (look in `Fonts/`, resource bundles, or license files)
- Search for stock image watermarks in bundled assets
- Verify audio files have appropriate licensing documentation

**Key details:**
- Apple may request proof of licensing during review
- Using Apple trademarks (Apple logo, product names) requires compliance with Apple's trademark guidelines

---

### §2.3.10 Apple Platform Focus

**Requirement:** App metadata and experience should focus on the Apple platform. Apps should not primarily promote or direct users to other platforms.

**Triggers rejection if:**
- App description primarily promotes the Android, Windows, or web version
- App UI prominently features non-Apple platform branding or directs users elsewhere
- App feels like a wrapper or advertisement for a non-Apple experience

**What to check:**
- Search App Store Connect description for mentions of "Android", "Google Play", "Windows", "download on our website", or alternative app marketplace names
- Grep source code and UI strings for cross-platform promotional messaging
- Check for deep links or CTAs directing users to non-Apple platforms or alternative marketplaces

**Key details:**
- Cross-platform apps are fine; the issue is when metadata or the app itself is primarily an advertisement for another platform
- You can mention other platforms exist, but the focus should be on the Apple experience
- Names, icons, or imagery of alternative app marketplaces must not appear unless the feature specifically and with Apple approval enables interactive functionality there

---

### §2.3.11 Pre-Order Apps

**Requirement:** Pre-order apps must be complete and deliverable by the stated release date. The final version must match what was promised in pre-order metadata.

**Triggers rejection if:**
- App is not ready by the release date
- Released app significantly differs from pre-order description or screenshots
- Pre-order metadata is misleading about features or content

**What to check:**
- Compare pre-order metadata (description, screenshots) against the app's current implementation
- Verify the app's release date in App Store Connect is realistic given the current state of the codebase
- Check that all features promised in pre-order marketing exist in the current build

**Key details:**
- Pre-orders can be set up to 180 days before release
- If the app is not ready, the pre-order will be removed and users will be notified

---

### §2.3.12 What's New Text

**Requirement:** The "What's New" section for updates must clearly describe what changed in the new version.

**Triggers rejection if:**
- "What's New" is empty, generic ("Bug fixes"), or does not reflect actual changes
- "What's New" text is misleading or describes features not in the update
- Text is used for promotional messages unrelated to the update

**What to check:**
- Review the release notes / "What's New" field in App Store Connect metadata
- Cross-reference against actual code changes (git diff between versions, CHANGELOG if present)
- Flag generic or boilerplate text like "Bug fixes and performance improvements" without specifics

**Key details:**
- Apple increasingly expects meaningful release notes, especially for major updates
- Release notes should not be used for promotional copy or advertising

---

### §2.3.13 In-App Events

**Requirement:** In-app events displayed on the App Store must have accurate metadata, including event name, description, media, and timing.

**Triggers rejection if:**
- Event metadata does not match the actual in-app event
- Event dates or details are inaccurate
- Event media (images/video) is misleading or unrelated to the event
- Event is used solely for advertising or promotion unrelated to the app

**What to check:**
- Review in-app event configuration in App Store Connect
- Verify event dates align with server-side event scheduling in the codebase
- Check that event-related UI and content exist in the app for the described event

**Key details:**
- In-app events appear on the App Store product page and in search/browse
- Events must be timely and relevant; stale events should be removed

---

## §2.4 Hardware Compatibility

### §2.4.1 iPhone Apps on iPad

**Requirement:** iPhone apps should also run on iPad. Universal app support is expected unless there is a compelling technical reason not to.

**Triggers rejection if:**
- iPhone-only app does not function on iPad at all
- App unnecessarily restricts itself to iPhone when it could reasonably run on iPad
- iPad experience is broken or severely degraded

**What to check:**
- Check `Info.plist` `UIDeviceFamily` key: `1` = iPhone, `2` = iPad, `[1, 2]` = Universal
- Review Xcode project settings for Targeted Device Family (TARGETED_DEVICE_FAMILY build setting)
- If iPhone-only, check whether the app uses iPad-incompatible hardware (e.g., specific iPhone sensors) that would justify the restriction
- Check for iPad-specific layouts in storyboards, XIBs, or SwiftUI views (`horizontalSizeClass`, `verticalSizeClass`)
- Verify `UISupportedInterfaceOrientations~ipad` exists if universal

**Key details:**
- Apps that are iPhone-only will still run on iPad in compatibility mode, but Apple prefers native iPad support
- If the app uses features only available on iPhone (e.g., certain telephony features), document this in review notes

---

### §2.4.2 Power Efficiency

**Requirement:** Apps must be designed to use energy efficiently. Apps that drain battery excessively or generate excessive heat will be rejected. *(ASR & NR)*

**Triggers rejection if:**
- App rapidly drains battery during normal use
- App uses excessive CPU, GPU, or network resources when idle or in the background
- App prevents the device from sleeping unnecessarily
- App encourages placing the device under a mattress or pillow while charging
- App performs excessive write cycles to the device's solid-state drive
- Third-party advertisements within the app run unrelated background processes

**What to check:**
- Search for `UIApplication.shared.isIdleTimerDisabled = true` (prevents screen sleep)
- Check background mode declarations in `Info.plist` `UIBackgroundModes` — each declared mode should be justified
- Look for continuous location tracking (`CLLocationManager` with `startUpdatingLocation` vs `startMonitoringSignificantLocationChanges`)
- Search for high-frequency timers (`Timer.scheduledTimer` or `DispatchSource.makeTimerSource` with very short intervals)
- Check for unnecessary continuous animation loops or rendering when the view is not visible
- Review `BGTaskScheduler` usage for background processing
- Search for UI text or instructional content suggesting charging with device covered or placed under objects
- Audit third-party ad SDK initialization to confirm SDKs do not spin up unrelated background processes

**Key details:**
- Background audio, location, VoIP, and fetch modes are closely scrutinized
- Apps that declare background modes but do not use them appropriately will be rejected
- The prohibition on third-party ads running background processes applies even if the app itself is not responsible for initiating them

---

### §2.4.3 Apple TV Remote Compatibility

**Requirement:** Apple TV apps must be fully functional using only the Siri Remote (or Apple TV Remote). Game controllers and other input methods can be supported as optional enhancements.

**Triggers rejection if:**
- App requires a game controller or other hardware to function
- Navigation or core features are inaccessible via the Siri Remote
- Focus-based navigation is broken or missing

**What to check:**
- Check for `GCController` usage and verify it is optional, not required
- Review `Info.plist` for `GCSupportedGameControllers` — if present, confirm `GCMicroGamepad` (Siri Remote) is listed
- Verify focus engine implementation (`UIFocusEnvironment`, `canBecomeFocused`, `didUpdateFocus`)
- Check `tvOS` target in project settings to confirm the app targets Apple TV
- Ensure `pressesBegan`/`pressesEnded` or gesture recognizers handle Siri Remote input

**Key details:**
- The Siri Remote has a touch surface, menu button, play/pause button, and Siri button
- All tvOS apps must support the basic Siri Remote even if they also support game controllers

---

### §2.4.4 Device Restart and Settings (ASR & NR)

**Requirement:** Apps must not require the user to restart their device. Apps must not require modifications to system settings unrelated to core app functionality.

**Triggers rejection if:**
- App instructs users to restart their device at any point
- App behavior depends on a device restart to function correctly
- App requires users to disable Wi-Fi, turn off security features, or change unrelated system settings to function
- App actively encourages disabling security or privacy features of the OS

**What to check:**
- Search UI strings, alerts, and documentation for "restart", "reboot", "power cycle" instructions
- Verify the app does not depend on system-level changes that require a restart
- Search for instructions to disable Wi-Fi, VPN, firewall, or security settings
- Check onboarding or setup flows for any steps requiring unrelated system configuration changes

**Key details:**
- This applies to both setup flows and ongoing usage instructions
- Apps should handle all necessary initialization within their own lifecycle without relying on user-facing system modifications

---

### §2.4.5 Mac App Store Requirements

**Requirement:** Mac App Store apps must comply with additional packaging and behavior requirements specific to macOS.

#### §2.4.5(i) App Sandboxing

**Triggers rejection if:**
- App does not use App Sandbox on macOS when it should
- Entitlements request capabilities beyond what the app needs

**What to check:**
- Check entitlements file (`.entitlements`) for `com.apple.security.app-sandbox` set to `true`
- Review all sandbox entitlements (`com.apple.security.files.*`, `com.apple.security.network.*`, etc.) and verify each is justified by app functionality
- Check `Info.plist` for `NSAppTransportSecurity` exceptions

#### §2.4.5(ii) Xcode Packaging

**Triggers rejection if:**
- App is not built with Xcode or does not ship as a single `.app` bundle

**What to check:**
- Verify the project uses an `.xcodeproj` or `.xcworkspace`
- Check that the build product is a single `.app` bundle (not multiple binaries or installer packages)

#### §2.4.5(iii) No Auto-Launch

**Triggers rejection if:**
- App registers itself to launch at login or system startup without user consent

**What to check:**
- Search for `SMLoginItemSetEnabled`, `LSSharedFileList`, `SMAppService`, or `ServiceManagement` imports
- Check for launch agent or launch daemon plists bundled in the app
- Verify any auto-launch is opt-in via a user-facing preference

#### §2.4.5(iv) No Standalone Downloads

**Triggers rejection if:**
- App downloads additional standalone executables or app bundles from the internet

**What to check:**
- Search for `URLSession` download tasks targeting `.app`, `.dmg`, `.pkg`, `.zip` containing executables
- Check for code that writes to `/Applications` or moves downloaded bundles into place
- Look for update frameworks (`Sparkle`) — Mac App Store apps must update through the store

#### §2.4.5(v) No Root Escalation

**Triggers rejection if:**
- App requests root or admin privileges via `AuthorizationExecuteWithPrivileges` or similar

**What to check:**
- Search for `AuthorizationCreate`, `AuthorizationExecuteWithPrivileges`, `STPrivilegedTask`, or `sudo` invocations
- Check for `SMJobBless` usage (privileged helper tools)
- Look for `NSAppleScript` calls that execute shell commands with elevated privileges

#### §2.4.5(vi) No License Screens

**Triggers rejection if:**
- App displays a license agreement or EULA screen at launch that must be accepted before use

**What to check:**
- Search for modal alerts or sheets at launch containing "license", "EULA", "terms", "agree", "accept" in button titles
- Check `applicationDidFinishLaunching` or initial view controller for agreement flows

#### §2.4.5(vii) Mac App Store Updates Only

**Triggers rejection if:**
- App includes its own update mechanism rather than relying on Mac App Store updates

**What to check:**
- Search for `Sparkle.framework`, `SUUpdater`, `SUAppcastURL`, or any third-party update framework imports
- Check for custom update-checking code that polls a server for new versions
- Look for `UserDefaults` keys related to update checks

#### §2.4.5(viii) Run on Current macOS

**Triggers rejection if:**
- App cannot run on the current shipping version of macOS

**What to check:**
- Check `LSMinimumSystemVersion` in `Info.plist` or `MACOSX_DEPLOYMENT_TARGET` build setting
- Verify the deployment target is not more than a couple of major versions behind current macOS
- Check for deprecated API usage that would fail on current macOS

#### §2.4.5(ix) Single Language Bundle

**Triggers rejection if:**
- App ships separate binaries or bundles per language instead of a single localized bundle

**What to check:**
- Verify localization uses `.lproj` folders within the single `.app` bundle
- Check for multiple `.app` bundles targeting different languages

**Key details:**
- All Mac App Store rules (i–ix) must be met simultaneously
- Apps that also sell outside the Mac App Store may have different behavior in the non-store version, but the Mac App Store version must comply

---

## §2.5 Software Requirements

### §2.5.1 Public APIs Only

**Requirement:** Apps must use only public, documented Apple APIs. Apps must be built with the current version of Xcode and target the current OS. *(ASR & NR)*

**Triggers rejection if:**
- App uses private/undocumented Apple APIs
- App is built with an outdated Xcode or targets an unsupported iOS/macOS version
- App uses deprecated APIs that have been removed

**What to check:**
- Search for known private API patterns: selectors starting with `_` on system classes, direct calls to `objc_msgSend` with private selectors, `dlopen`/`dlsym` loading private frameworks
- Check `IPHONEOS_DEPLOYMENT_TARGET` or `MACOSX_DEPLOYMENT_TARGET` build settings for outdated targets
- Search for `@objc` methods that might be calling private APIs via string selectors (`perform(Selector("_privateMethod"))`)
- Look for imports of private frameworks (e.g., `UIKit` internal headers, `GraphicsServices`, `BackBoardServices`)
- Check `Podfile`, `Package.swift`, or `Cartfile` for dependencies known to use private APIs

**Key details:**
- Apple runs automated scans for private API usage during review
- Apps using private APIs may work during testing but be rejected upon submission
- The "current OS" requirement typically means within the last two major versions

---

### §2.5.2 Self-Contained Bundles

**Requirement:** Apps must be self-contained in their bundles. They must not install or download code that changes the app's primary purpose or functionality after review. *(ASR & NR)*

**Triggers rejection if:**
- App downloads and executes code (other than JavaScript in a web view)
- App uses `dlopen`, `NSBundle.load()`, or similar to dynamically load code not in the original bundle
- App changes its core functionality via remotely downloaded scripts or plugins post-review

**What to check:**
- Search for `dlopen`, `dlsym`, `NSBundle(path:)?.load()`, `Bundle.load()`
- Look for code downloading `.dylib`, `.framework`, or executable files
- Check for JavaScript execution outside of `WKWebView` (e.g., `JavaScriptCore` framework used to run downloaded scripts that alter app behavior)
- Search for hot-code-push frameworks or mechanisms (`CodePush` for React Native, custom OTA update systems)
- Review `NSAppTransportSecurity` exceptions for domains that might serve executable code

**Key details:**
- Educational apps teaching coding can run student-written code in a sandboxed environment
- JavaScript within web views is allowed
- The prohibition is on changing the app's reviewed behavior via downloaded code

---

### §2.5.3 No Malicious Code

**Requirement:** Apps must not contain viruses, malware, or any code designed to harm the user, their data, or their device. *(ASR & NR)*

**Triggers rejection if:**
- App contains known malware signatures or behaviors
- App exfiltrates user data without consent
- App performs cryptocurrency mining on the device
- App deliberately degrades device performance

**What to check:**
- Search for cryptocurrency mining code or libraries (`CryptoNight`, `Coinhive`, mining pool connections)
- Check for data exfiltration patterns: bulk contact, photo, or file uploads without clear user-facing justification
- Look for obfuscated code that hides its purpose
- Verify all network requests go to documented, expected endpoints

**Key details:**
- Apple scans binaries for known malicious patterns
- Apps that collect data must have appropriate privacy disclosures (covered in Section 5)

---

### §2.5.4 Background Services

**Requirement:** Background execution must only be used for its intended purpose. Apps must not abuse background modes. *(ASR & NR)*

**Triggers rejection if:**
- App declares background modes it does not actually use
- Background execution is used for purposes other than the declared mode (e.g., `audio` background mode used to keep the app alive when it does not play audio)
- App performs extensive work in the background beyond what the declared mode permits

**What to check:**
- Check `Info.plist` `UIBackgroundModes` array — common values: `audio`, `location`, `voip`, `fetch`, `remote-notification`, `processing`, `bluetooth-central`, `bluetooth-peripheral`, `external-accessory`
- For each declared mode, verify the app actually uses the corresponding API:
  - `audio` → `AVAudioSession`, `AVPlayer`, or audio recording
  - `location` → `CLLocationManager` with continuous tracking
  - `voip` → `PKPushRegistry` with VoIP push type
  - `fetch` → `BGAppRefreshTaskRequest` or legacy `setMinimumBackgroundFetchInterval`
  - `remote-notification` → silent push handling in `didReceiveRemoteNotification`
  - `bluetooth-central` → `CBCentralManager`
  - `bluetooth-peripheral` → `CBPeripheralManager`
- Flag any declared background mode that has no corresponding API usage in the source

**Key details:**
- Declaring unused background modes is a common rejection reason
- Background audio mode solely for playing silence to keep the app alive is explicitly prohibited
- Location background mode requires `NSLocationAlwaysAndWhenInUseUsageDescription` in `Info.plist`

---

### §2.5.5 IPv6 Compatibility

**Requirement:** Apps must support IPv6-only networking environments (NAT64/DNS64).

**Triggers rejection if:**
- App fails on IPv6-only networks
- App hardcodes IPv4 addresses instead of using hostnames
- Networking code uses IPv4-only APIs

**What to check:**
- Search for hardcoded IPv4 addresses (`\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b` regex pattern)
- Check for usage of IPv4-only APIs: `inet_addr`, `inet_aton`, `getaddrinfo` with `AF_INET` instead of `AF_UNSPEC`
- Look for low-level socket code using `sockaddr_in` instead of `sockaddr_in6` or dual-stack approaches
- Verify `SCNetworkReachability` is not configured with IPv4-only addresses
- Check third-party networking libraries for IPv6 compatibility

**Key details:**
- Apple tests apps on IPv6-only networks during review
- Using high-level Apple networking APIs (`URLSession`, `Network.framework`) generally ensures IPv6 compatibility
- The most common cause of failure is hardcoded IP addresses in configuration

---

### §2.5.6 WebKit for Web Browsing (ASR & NR)

**Requirement:** Apps that browse the web must use the WebKit framework (`WKWebView` or `SFSafariViewController`). Developers may apply for an entitlement to use an alternative web browser engine.

**Triggers rejection if:**
- App uses a non-WebKit rendering engine for web browsing without an Apple-approved entitlement
- App uses deprecated `UIWebView` instead of `WKWebView`

**What to check:**
- Search for `UIWebView` usage (deprecated since iOS 12, rejected since late 2020)
- Verify web browsing uses `WKWebView` or `SFSafariViewController` (search for imports of `WebKit` or `SafariServices`)
- Check third-party dependencies for bundled browser engines
- Search for `Chromium`, `GeckoView`, `CEF` (Chromium Embedded Framework) imports or embedded frameworks
- Check `Podfile` / `Package.swift` for known custom browser engine dependencies
- If using an alternative browser engine, verify the corresponding entitlement is present in the `.entitlements` file

**Key details:**
- This applies only to web browsing functionality; apps can use other engines for non-browsing purposes (e.g., game engines rendering HTML for UI)
- `UIWebView` references anywhere in the binary (including third-party SDKs) cause rejection — check all dependencies
- Apple now offers an entitlement process for alternative browser engines (in the European Union); see https://developer.apple.com/support/alternative-browser-engines/ for eligibility and requirements

---

### §2.5.8 No Alternate Desktop/Home Screen Environments

**Requirement:** Apps must not create alternate desktop or home screen experiences, or simulate multi-app widget-like interfaces.

**Triggers rejection if:**
- App replicates the iOS home screen or Springboard experience
- App creates a launcher-style UI for other apps
- App simulates a multi-window or multi-app desktop environment

**What to check:**
- Review the app's main UI for launcher-like patterns: grids of app icons, dock-like interfaces
- Search for `UIApplication.shared.open(url)` used to launch many other apps in a launcher pattern
- Check for URL schemes used to open other apps in aggregate

**Key details:**
- Widget-like functionality within a single app's context is fine
- The prohibition is on creating an alternative to the system home screen

---

### §2.5.9 Standard UI Switches and Native UI (ASR & NR)

**Requirement:** Apps must not alter or disable standard system hardware switches (Volume Up/Down, Ring/Silent) or alter other native UI elements and behaviors in misleading ways. Apps must not block links to other apps or features users expect to work in a standard way.

**Triggers rejection if:**
- App alters or disables the function of Volume Up, Volume Down, or Ring/Silent hardware switches
- Standard iOS toggle switches are used but behave opposite to convention (e.g., "on" position means "off")
- System-standard controls are visually altered to confuse users
- Standard gestures are overridden in misleading ways
- App blocks tappable links (universal links, deep links, system links) that users expect to open normally

**What to check:**
- Search for `UISwitch` customization that inverts behavior (`.setOn(!isEnabled)` patterns, `.isOn` with inverted logic)
- Check for overriding `AVAudioSession` volume or remapping hardware button behavior
- Check for custom controls mimicking system controls with different behavior
- Review gesture recognizer usage that overrides standard system gestures
- Search for `UIApplication.shared.open` interception patterns or blocked link schemes
- Verify tappable links in `WKWebView` and `SFSafariViewController` behave as users expect

**Key details:**
- Custom-designed controls are fine as long as their behavior is intuitive and not misleading
- Do not override system swipe-to-go-back or other standard navigation gestures
- Blocking universal links or preventing users from navigating to expected destinations is a rejection trigger

---

### §2.5.11 SiriKit and Shortcuts

**Requirement:** Apps using SiriKit and Shortcuts must handle only relevant intents, use appropriate vocabulary, and resolve intents directly without showing ads. *(ASR & NR)*

#### §2.5.11(i) Relevant Intents Only

**Triggers rejection if:**
- App handles Siri intents unrelated to its core functionality
- App registers for intents it does not meaningfully support

**What to check:**
- Check `Info.plist` `NSExtension` → `NSExtensionAttributes` → `IntentsSupported` and `IntentsRestrictedWhileLocked`
- Verify each declared intent has a corresponding handler in the Intents extension source code
- Cross-reference supported intents with the app's actual functionality

#### §2.5.11(ii) Appropriate Vocabulary

**Triggers rejection if:**
- Custom Siri vocabulary includes inappropriate, misleading, or competitor brand names

**What to check:**
- Check `AppIntentVocabulary.plist` for custom vocabulary entries
- Review `INVocabulary` API usage and the terms being registered
- Search for `AppShortcutsProvider` and review suggested phrases

#### §2.5.11(iii) Direct Resolution Without Ads

**Triggers rejection if:**
- Siri intent resolution shows ads or requires extra taps beyond what is necessary
- Intent handling redirects users to the app unnecessarily instead of resolving inline

**What to check:**
- Review intent handler `handle()` methods for ad insertion or unnecessary `continueInApp` responses
- Verify intents resolve with `INIntentResponse` success codes rather than always opening the app
- Check for analytics or ad SDK calls within intent handler code paths

**Key details:**
- Shortcuts and Siri integrations should feel like natural extensions of the app
- Intents should complete as quickly and directly as possible

---

### §2.5.12 CallKit and SMS Blocking

**Requirement:** Apps using CallKit or SMS/MMS message filtering must follow specific rules about functionality and data handling. *(ASR & NR)*

**Triggers rejection if:**
- Call blocking/identification app sends call data off-device without user consent
- SMS filter extension sends message content to a remote server (only on-device filtering for SMS)
- App misuses CallKit to block emergency numbers or legitimate callers without user knowledge

**What to check:**
- Check for `CallKit` framework import and `CXCallDirectoryProvider` usage
- Verify `CXCallDirectoryExtensionContext` entries are populated from local data, not remote-only sources
- For SMS filtering: check `ILMessageFilterExtension` — verify filtering logic runs on-device
- Look at the `ILMessageFilterQueryHandling` implementation — `ILNetworkResponse` usage means server-side filtering, which has restrictions
- Check `Info.plist` for `com.apple.developer.networking.networkextension` entitlements

**Key details:**
- On-device SMS filtering is preferred; network-based filtering requires additional review
- Call identification data must not be used for tracking or advertising
- Emergency numbers must never be blocked

---

### §2.5.13 Facial Recognition

**Requirement:** Apps using facial recognition for authentication must use the `LocalAuthentication` framework (Face ID). *(ASR & NR)*

**Triggers rejection if:**
- App implements custom facial recognition for device authentication instead of using Face ID
- App uses camera-based face matching as an authentication mechanism outside of `LocalAuthentication`
- App stores facial data insecurely or sends it off-device without consent

**What to check:**
- Search for `LocalAuthentication` import and `LAContext` usage (correct approach)
- Check for third-party face recognition SDKs (`OpenCV` face detection, `Vision` framework `VNDetectFaceRectanglesRequest` used for authentication purposes)
- Verify `NSFaceIDUsageDescription` exists in `Info.plist` if Face ID is used
- Look for `AVCaptureDevice` camera usage combined with face detection that might be used as an authentication mechanism

**Key details:**
- Using the `Vision` framework for face detection in non-authentication contexts (e.g., photo filters, AR) is fine
- The restriction is specifically on using facial recognition as an authentication substitute for `LocalAuthentication`

---

### §2.5.14 Recording Consent

**Requirement:** Apps must obtain explicit user consent before recording or transmitting user activity, screen content, or audio/video. *(ASR & NR)*

**Triggers rejection if:**
- App records screen, microphone, or camera without clear user consent
- App transmits user activity data (keystrokes, screen content, usage patterns) without disclosure
- Recording starts automatically without a clear user-facing indication

**What to check:**
- Check `Info.plist` for usage description keys: `NSMicrophoneUsageDescription`, `NSCameraUsageDescription`
- Search for `ReplayKit` (`RPScreenRecorder`) usage — screen recording
- Look for `AVCaptureSession` setup without corresponding user-facing recording indicators
- Search for analytics SDKs that record session replays (`FullStory`, `LogRocket`, `UXCam`, `Smartlook`, `Hotjar`)
- Check for `UIScreen.main.snapshotView` or screenshot capture code running on timers

**Key details:**
- Session replay SDKs are common sources of violations — they must have clear user consent
- The microphone and camera usage description strings must clearly explain why recording is needed

---

### §2.5.15 Files App and iCloud Document Support

**Requirement:** Apps that create or manage documents should support the Files app and iCloud document storage where appropriate.

**Triggers rejection if:**
- Document-based app provides no way to access files through the Files app
- App stores user documents in a way that is inaccessible outside the app without justification

**What to check:**
- Check `Info.plist` for `UISupportsDocumentBrowser` key
- Look for `UIDocumentBrowserViewController` or `UIDocumentPickerViewController` usage
- Check for `LSSupportsOpeningDocumentsInPlace` in `Info.plist`
- Verify `iCloud` entitlements if the app claims iCloud support: `com.apple.developer.icloud-container-identifiers`
- Check for `NSUbiquitousContainerIsDocumentScopePublic` in `Info.plist`
- Review `CFBundleDocumentTypes` and `UTExportedTypeDeclarations` / `UTImportedTypeDeclarations` for proper document type registration

**Key details:**
- Not all apps need Files app integration — this primarily applies to document-creation and document-management apps
- Apps that do support documents should use system document pickers rather than custom file browsers where possible

---

### §2.5.16 Widgets, Extensions, and Notifications

**Requirement:** Widgets, app extensions, and notifications must be related to the main app's functionality. App Clips must be included in the main app binary and must not contain ads. *(ASR & NR)*

**Triggers rejection if:**
- Widget or extension provides functionality completely unrelated to the main app
- Notifications are used for advertising, spam, or content unrelated to the app
- App Clip is a standalone binary separate from the main app
- App Clip displays ads

#### §2.5.16(a) App Clips

**What to check:**
- Verify App Clip target exists within the main Xcode project (not a separate project)
- Check App Clip binary is included in the main app's archive
- Search App Clip source code for ad SDKs (`GoogleMobileAds`, `AdMob`, `FBAudienceNetwork`, `AdColony`, `AppLovin`, `UnityAds`, `IronSource`)
- Check `_XCAppClipURL` associated domains in entitlements
- Verify App Clip size is within the tiered limits — 10 MB (iOS 15), 15 MB (iOS 16), 50 MB (iOS 16.4+ digital invocations only) (check build product size)

**What to check (widgets/extensions generally):**
- Review all extension targets in the Xcode project (`*.appex` bundles)
- Verify each widget/extension's functionality relates to the main app's purpose
- Check `NSExtensionPointIdentifier` in each extension's `Info.plist` to understand its type
- For widgets: review `WidgetKit` timeline providers and verify content relates to the main app
- For notification content extensions: verify they display relevant app content, not ads

**Key details:**
- Each extension/widget should enhance the main app's user experience
- Widgets should display timely, relevant, personalized information from the app
- Push notifications must be opt-in and related to the app's functionality

---

### §2.5.17 Matter Support (ASR & NR)

**Requirement:** Apps supporting Matter must use Apple's Matter SDK for device pairing/commissioning. If the app uses any Matter software component other than Apple's Matter SDK, that component must be certified by the Connectivity Standards Alliance (CSA) for the platform.

**Triggers rejection if:**
- App uses a custom or uncertified Matter stack for pairing/commissioning instead of Apple's SDK
- Third-party Matter SDK used by the app lacks valid CSA certification for the target platform
- App claims Matter support but does not use Apple-provided or CSA-certified APIs

**What to check:**
- Search for `import MatterSupport` or `import Matter` framework usage
- Check for third-party Matter SDKs (e.g., `connectedhomeip`, `chip-tool`, custom CHIP implementations) and verify CSA certification status
- Verify `com.apple.developer.matter.allow-setup-payload` entitlement if the app does Matter device setup
- Check `Info.plist` for `MatterSupport` usage descriptions

**Key details:**
- Apple's Matter framework handles commissioning, device control, and ecosystem integration and is always acceptable
- Third-party CSA-certified Matter components are now permitted as an alternative to Apple's SDK — obtain CSA certification documentation before submission
- Non-certified third-party Matter stacks remain prohibited

---

### §2.5.18 Display Advertising Limits

**Requirement:** Display advertising must be limited to the main app binary and must not appear in extensions, App Clips, widgets, notifications, keyboards, watchOS apps, or similar surfaces. Ads must be appropriate for the app's age rating, must let users see all targeting information without leaving the app, and must not target based on sensitive data (health/medical, school/classroom, kids). Interstitial ads must be clearly marked as ads, must not trick users into tapping, and must offer easily accessible close/skip buttons. Apps with ads must also let users report inappropriate or age-inappropriate ads. *(ASR & NR)*

**Triggers rejection if:**
- Ads appear in any surface other than the main app binary (extensions, App Clips, widgets, notifications, keyboards, watchOS apps)
- Ads target users based on sensitive data: HealthKit / health/medical data, ClassKit / school and classroom data, or data from Kids Category apps
- Ads are not appropriate for the app's declared age rating
- Users cannot view the targeting information used for an ad without leaving the app
- Interstitial or full-screen ads do not clearly indicate they are ads
- Interstitial ads manipulate or trick users into tapping them (e.g., fake close buttons, deceptive UI)
- Close/skip buttons on interstitial ads are too small, hidden, or otherwise not easily accessible
- App does not provide a way for users to report inappropriate or age-inappropriate ads
- Full-screen interstitial ads appear immediately at launch or without any user interaction
- Ads cannot be dismissed or block core functionality
- Ad frequency is excessive and degrades the user experience
- Ads are deceptive or disguised as app content

**What to check:**
- Search for ad SDK imports: `GoogleMobileAds`, `AdMob`, `FBAudienceNetwork`, `AdColony`, `AppLovin`, `UnityAds`, `IronSource`, `Vungle`, `Chartboost`, `InMobi`
- Check whether ad SDKs are linked into any extension, App Clip, widget, notification, keyboard, or watchOS target — all prohibited
- Verify ad targeting pipelines do not consume HealthKit, ClassKit, or kids-app data
- Confirm an in-app "Why this ad?" / targeting-info disclosure path exists without sending the user out of the app
- Inspect interstitial ad UI for clear "Ad" labeling, large/visible close/skip controls, and absence of misleading tap targets
- Verify a UI affordance exists for users to report inappropriate ads (often surfaced from a long-press, info button, or feedback link near the ad)
- Search for interstitial ad presentation in `viewDidAppear` of the initial view controller (immediate launch ads)
- Look for ad presentation without user interaction triggers
- Review ad placement frequency — timers or counters that show ads at very short intervals
- Check for `SKOverlay` or `SKStoreProductViewController` used aggressively for cross-promotion

**Key details:**
- Marked ASR and NR — applies to both distribution channels
- The list of ad-prohibited surfaces explicitly includes **keyboards and watchOS apps** in addition to widgets, App Clips, notifications, and extensions
- Sensitive-data targeting prohibitions cover HealthKit-derived data, ClassKit-derived school/classroom data, and any data sourced from Kids Category apps — these cannot feed behavioral or targeted advertising
- The "show all targeting info" requirement must be satisfied without making the user leave the app — an in-app disclosure surface is required
- Ad-reporting must be reachable from the ad itself, not buried in app settings
- Interstitial ads should appear at natural transition points, not immediately upon launch
- Users must always be able to dismiss ads and return to the app's content
- The App Tracking Transparency framework (`ATTrackingManager`) must be used before tracking for ad purposes
