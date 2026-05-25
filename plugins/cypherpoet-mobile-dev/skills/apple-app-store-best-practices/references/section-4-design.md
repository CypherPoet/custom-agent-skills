# Section 4: Design

> Source: https://developer.apple.com/app-store/review/guidelines/
> Last synced: 2026-05-04

---

## 4.1 Copycats

### 4.1(a) Original Ideas Required

**Requirement:** Apps must offer a unique, original experience. Do not simply copy the UI, functionality, or concept of another popular app.

**Triggers rejection if:**
- The app closely replicates the look, feel, or core functionality of another well-known app
- The app copies distinctive UI elements, navigation patterns, or interaction models from another app without meaningful differentiation

**What to check:**
- Compare app screenshots, UI layout, and core feature set against top apps in the same category
- Review marketing text and metadata for references that mirror another app's positioning
- Check for near-identical icon design or color schemes matching a popular competitor

**Key details:**
- Having similar functionality to an existing app is acceptable if the implementation, design, and experience are meaningfully distinct
- "Inspired by" is fine; "cloned from" is not

---

### 4.1(b) No Impersonation (ASR & NR)

**Requirement:** Apps must not impersonate another app, developer, or service. The app's identity must be clearly its own.

**Triggers rejection if:**
- The app name, icon, or UI misleads users into believing it is made by or affiliated with another developer or company
- The app mimics another app's branding, trade dress, or identity elements in a way that causes confusion
- The developer account name is designed to impersonate another entity

**What to check:**
- App name in `Info.plist` (`CFBundleDisplayName`, `CFBundleName`) for similarity to well-known apps
- App icon assets for visual similarity to established brands
- Marketing text and App Store metadata for misleading claims of affiliation
- Developer name on the App Store Connect account

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Even unintentional similarity can trigger rejection if the result is user confusion

---

### 4.1(c) Unauthorized Use of Third-Party IP

**Requirement:** Do not use third-party icons, images, brand names, trademarks, or other intellectual property without authorization.

**Triggers rejection if:**
- The app uses another company's logo, icon, or brand imagery without a license
- The app name contains a trademarked term without authorization (e.g., "Facebook Companion", "Uber Helper")
- Third-party character designs, mascots, or branded visual elements appear in app assets

**What to check:**
- All image assets in `Assets.xcassets` for third-party logos or brand imagery
- App name and subtitle in App Store Connect metadata
- In-app strings and UI labels referencing third-party brands
- Marketing screenshots for unauthorized brand placements

**Key details:**
- Having a license or partnership agreement should be documented and available if Apple requests it
- Generic terms that happen to match a brand name (e.g., "Apple" for a fruit app) require extra care to avoid confusion

---

## 4.2 Minimum Functionality

**Requirement:** Apps must provide sufficient value and functionality to justify their presence on the App Store. An app that is merely a repackaged website, a thin wrapper around web content, or lacks meaningful features will be rejected.

**Triggers rejection if:**
- The app is essentially a `WKWebView` or `SFSafariViewController` loading a website with no native functionality
- The app offers no meaningful features beyond what a bookmark to a website would provide
- The app is a trivial utility with no real user value

**What to check:**
- `WKWebView` and `SFSafariViewController` usage -- determine whether the app is primarily web content vs. native UI
- Ratio of native UIKit/SwiftUI views to web views in the view hierarchy
- Whether the app uses device capabilities (camera, sensors, local storage, notifications) that go beyond a website
- Presence of offline functionality or native data persistence

**Key details:**
- Web-based apps can be acceptable if they provide significant native integration, offline capability, or platform-specific features
- Apps built with cross-platform frameworks (React Native, Flutter) are fine as long as they meet the functionality bar

---

### 4.2.1 ARKit Apps

**Requirement:** Apps that use ARKit must provide rich, integrated augmented reality experiences. AR must be core to the app's value, not a superficial feature.

**Triggers rejection if:**
- AR functionality is a gimmick or afterthought with no real utility
- The AR experience is minimal (e.g., placing a single static 3D object with no interaction)
- The app claims AR capability but delivers a trivially simple experience

**What to check:**
- `ARKit` / `RealityKit` / `ARSession` imports and usage depth
- Complexity of AR scene management (plane detection, object tracking, world mapping)
- Whether AR is central to the app's user journey or bolted on as a secondary feature
- `Info.plist` for `NSCameraUsageDescription` tied to AR functionality

**Key details:**
- The bar for AR apps is higher than a simple demo -- Apple expects production-quality AR experiences
- Consider whether the AR feature could be removed and the app would still function identically (if yes, it may not meet this requirement)

---

### 4.2.2 No Marketing-Only Apps

**Requirement:** Apps must not be primarily marketing materials, advertisements, or collections of web clippings.

**Triggers rejection if:**
- The app's primary content is promotional material for a business, product, or service with no interactive functionality
- The app is a digital brochure or catalog with no features beyond scrolling through marketing content
- The app aggregates web clippings, RSS feeds, or scraped content without adding value

**What to check:**
- Whether the app contains interactive features beyond passive content consumption
- Presence of user-facing functionality (search, filtering, personalization, transactions, user accounts)
- Whether content is static marketing copy vs. dynamic, user-relevant information
- Any in-app purchase or subscription that gates marketing content

**Key details:**
- A business app with ordering, booking, loyalty features, or other transactional functionality is acceptable even if it also contains marketing content
- Content-heavy apps are fine if they provide editorial value, curation, or utility beyond raw promotion

---

### 4.2.3 Standalone Functionality and Download Size Disclosure

**Requirement:** Apps must work as standalone products. If the app requires downloading additional content after initial launch, the download size must be disclosed before the user's first launch.

**Triggers rejection if:**
- The app is non-functional without downloading large additional resources after install, and the user is not informed of this before first launch
- The app is essentially a downloader/launcher for the "real" content without disclosing this upfront
- The App Store listing does not mention required post-install downloads

**What to check:**
- App launch flow for mandatory post-install downloads or resource fetches
- Size of additional downloads triggered on first launch
- App Store description and metadata for download size disclosures
- Whether the app provides any value before additional downloads complete

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- The disclosure must appear in the App Store metadata, not just in-app after purchase/download
- Games with large asset bundles are a common case -- the total download size must be clearly communicated

---

### 4.2.6 Template-Created Apps

**Requirement:** Apps generated from commercial templates, app builders, or cookie-cutter services will be rejected unless submitted by the template provider itself with unique content.

**Triggers rejection if:**
- The app was clearly generated by a template service (e.g., Appy Pie, BuildFire, GoodBarber) and submitted by an end customer rather than the template provider
- Multiple near-identical apps from the same template appear under different developer accounts
- The app has no meaningful customization beyond swapping text and images in a template

**What to check:**
- Binary analysis for known template framework signatures or embedded SDK identifiers
- Presence of template-provider branding in build artifacts, crash logs, or embedded metadata
- Whether the developer account appears to be submitting apps across many unrelated categories (common for template resellers)
- Code signing identity and provisioning profile origin

**Key details:**
- Template providers can submit apps on behalf of clients under a single developer account with unique content per app
- The restriction targets the template's customers submitting low-effort apps, not the template platform itself

---

### 4.2.7 Remote Desktop Clients

**Requirement:** Remote desktop mirroring apps must meet specific technical and UX requirements to ensure they provide genuine value and do not circumvent platform rules.

**Triggers rejection if:**
- The app connects to devices the user does not own or control
- Processing happens on the client device rather than being fully executed on the remote host
- The user must create an account with a service other than the host device's own system
- The app's UI mimics iOS, iPadOS, or the App Store interface
- The app acts as a thin client for cloud-based apps that should be distributed natively

**What to check:**
- Network connection targets -- verify the app connects to user-owned devices or local/LAN hosts
- Whether computation and rendering happen on the remote host (check for local processing of streamed content)
- Account creation flow -- should authenticate via the host machine's credentials, not a third-party service
- UI design for any elements that resemble iOS system UI, the App Store, or native iOS app layouts
- Whether the remote desktop functionality is being used to stream App Store-distributed apps from the cloud

**Key details:**
- Applies to all five sub-requirements: (a) user-owned/local/LAN devices, (b) fully executed on host, (c) host-native accounts, (d) non-iOS-mimicking UI, (e) no thin-client cloud app streaming
- VNC, RDP, and similar protocols are acceptable as long as all five conditions are met

---

## 4.3 Spam

### 4.3(a) Duplicate Apps (ASR & NR)

**Requirement:** Do not submit multiple apps with the same functionality under different Bundle IDs.

**Triggers rejection if:**
- The developer submits the same app (or nearly identical apps) under multiple Bundle IDs
- White-label apps with only cosmetic differences (logo, color scheme) are submitted as separate apps
- An app is resubmitted under a new Bundle ID to reset ratings or reviews

**What to check:**
- `CFBundleIdentifier` in `Info.plist` -- compare against other apps from the same developer account
- Binary similarity analysis between the submitted app and other apps from the same developer
- App Store Connect account for other apps with overlapping functionality
- Shared code signing certificates across near-identical apps

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- A single app with in-app configuration or theming is preferred over multiple near-identical apps
- Legitimate use cases for multiple Bundle IDs exist (e.g., free vs. pro versions with substantially different feature sets), but the apps must be meaningfully distinct

---

### 4.3(b) Category Saturation

**Requirement:** Do not flood a category with many similar apps. Apps should be meaningfully distinct from each other.

**Triggers rejection if:**
- A developer submits many apps to the same category that differ only in content (e.g., a separate app for each city, team, or topic)
- The developer's portfolio contains a high volume of low-effort, similar apps

**What to check:**
- Developer account's full app portfolio for patterns of similar submissions
- Whether the app's distinct content could be delivered as in-app content within a single app
- Category placement relative to the developer's other apps

**Key details:**
- A single app with content sections, filters, or regional settings is preferred over dozens of single-purpose apps
- This applies to the developer's overall portfolio, not just a single submission

---

## 4.4 Extensions (ASR & NR)

**Requirement:** App extensions must comply with the App Extension Programming Guide. They must include app functionality (not just help screens or settings), disclose extensions in marketing text, and must not contain marketing, advertising, or in-app purchases within the extension itself.

**Triggers rejection if:**
- An extension does not comply with the App Extension Programming Guide
- The extension contains no real functionality (only a help screen or settings page)
- Extensions are not disclosed in the App Store marketing text
- The extension displays advertising or offers in-app purchases
- The app is solely an extension with no containing app functionality

**What to check:**
- Xcode project for extension targets (`*.appex` bundles) -- verify each has meaningful functionality
- `NSExtension` dictionary in the extension's `Info.plist` for correct `NSExtensionPointIdentifier`
- App Store description for mentions of included extensions and their capabilities
- Extension code for any `SKPaymentQueue`, `SKProduct`, or ad SDK imports
- Containing app's functionality beyond hosting the extension

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- The containing app must provide value on its own; it cannot exist solely to deliver an extension
- Extensions must be functional within their declared extension point's constraints

---

### 4.4.1 Keyboard Extensions (ASR & NR)

**Requirement:** Keyboard extensions must provide keyboard input functionality. If they include images or emoji, they must also follow Sticker guidelines. They must provide a method to advance to the next keyboard, function without full network access, and cannot launch other apps (besides Settings) or repurpose keyboard UI buttons for unrelated actions.

**Triggers rejection if:**
- The keyboard extension does not provide actual keyboard text input
- No "next keyboard" button or globe key equivalent is implemented
- The keyboard requires network access to function at all (basic input must work offline)
- The extension launches apps other than Settings
- Standard keyboard buttons (e.g., return, space) are repurposed for non-keyboard actions
- Image/emoji keyboards do not follow Sticker guidelines from Section 10

**What to check:**
- `NSExtensionPointIdentifier` set to `com.apple.keyboard-service` in extension's `Info.plist`
- Implementation of `advanceToNextInputMode()` or equivalent next-keyboard mechanism
- `RequestsOpenAccess` key in `Info.plist` -- if `true`, verify the keyboard still functions with network disabled
- Code for `UIApplication.shared.open()` calls -- should only target Settings URLs
- UI layout for standard keyboard key behaviors (return key triggers return, not a custom action)
- If the keyboard provides stickers/images, cross-reference with Section 10 Sticker guidelines

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- "Full Access" (network) can be requested but must not be required for core keyboard functionality
- Emoji/sticker keyboards are acceptable but must still provide a path to text input or next keyboard

---

### 4.4.2 Safari Extensions (ASR & NR)

**Requirement:** Safari extensions must run on the current version of Safari, must not interfere with System Settings or Safari UI, must not contain malicious or misleading content, and should claim only the minimum necessary website access permissions.

**Triggers rejection if:**
- The extension does not function on the current Safari version
- The extension modifies or interferes with Safari's native UI or System Settings
- The extension injects malicious scripts, phishing content, or misleading elements into web pages
- The extension requests broad website access permissions (e.g., all websites) when it only needs access to specific domains

**What to check:**
- Safari extension target in Xcode project -- verify `SFSafariExtensionHandler` or `SFSafariWebExtensionHandler` implementation
- `manifest.json` (for Web Extensions) or `Info.plist` for declared permissions and host access patterns
- Content scripts for DOM manipulation that could interfere with Safari UI elements
- `permissions` and `host_permissions` arrays -- verify they follow least-privilege principle
- Minimum Safari/macOS version requirements in the extension's configuration

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Use `<all_urls>` or `*://*/*` host permissions only if the extension genuinely operates on all websites
- Content blockers have separate, more lenient rules under the Content Blocker extension point

---

## 4.5 Apple Sites and Services (ASR & NR)

### 4.5.1 Apple Data Sources

**Requirement:** Only use approved RSS feeds from Apple. Do not scrape Apple websites, services, or data.

**Triggers rejection if:**
- The app scrapes data from apple.com, the App Store, iTunes, or any other Apple web property
- The app uses unofficial or undocumented Apple APIs to extract data
- The app accesses Apple RSS feeds not listed in the approved feed directory

**What to check:**
- Network requests targeting `apple.com`, `itunes.apple.com`, `apps.apple.com`, or related Apple domains
- Web scraping libraries (e.g., SwiftSoup, Kanna) used against Apple URLs
- Hardcoded Apple URLs in source code or configuration files
- RSS feed URLs -- verify they match Apple's published approved feeds

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Apple's approved RSS feeds are documented at https://rss.applemarketingtools.com/
- Using the official App Store Connect API, iTunes Search API, or MusicKit is acceptable

---

### 4.5.2 Apple Music

**Requirement:** Apps integrating Apple Music must use MusicKit for native playback, follow Apple Music Identity Guidelines for branding, disclose what user data they access, and must not share Apple Music user data with third parties.

**Triggers rejection if:**
- The app plays Apple Music content without using MusicKit APIs
- Apple Music branding is used incorrectly (wrong logo, colors, or attribution)
- The app does not disclose to users what Apple Music data it accesses
- Apple Music listening data, playlists, or library information is shared with third parties

**What to check:**
- Imports: `MusicKit`, `StoreKit` (for subscription status), `MediaPlayer` framework usage
- `MusicAuthorization.request()` calls and handling of authorization status
- Privacy policy and in-app disclosures for Apple Music data access
- Network requests that transmit Apple Music user data to external servers
- Apple Music logo and branding usage against the Apple Music Identity Guidelines
- `NSAppleMusicUsageDescription` in `Info.plist`

**Key details:**
- Sub-requirements: (i) MusicKit for native playback (user-initiated), no payment required to monetize Apple Music; (ii) MusicKit is not a substitute for licensing deeper integration -- cover art and metadata may only accompany playback, not marketing/advertising; (iii) disclose data access, do not share Apple Music user data with third parties, and do not use it to identify users or target ads
- Apple Music API access requires a MusicKit developer token
- Streaming playback requires the user to have an active Apple Music subscription

---

### 4.5.3 No Spam via Apple Services

**Requirement:** Do not use Apple services (iMessage, Push Notifications, Game Center, etc.) to send spam or phishing content.

**Triggers rejection if:**
- The app sends unsolicited bulk messages via iMessage, AirDrop, or other Apple communication services
- Push notifications are used to deliver phishing links or deceptive content
- Game Center or other Apple social features are used to distribute spam

**What to check:**
- Push notification payload content and targeting logic
- `MessageUI` framework usage for automated or bulk message sending
- Game Center integration for any broadcast or mass-messaging patterns

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Legitimate transactional and user-requested notifications are acceptable
- User-initiated sharing via share sheets is fine

---

### 4.5.4 Push Notifications

**Requirement:** Push notifications must not be required for basic app functionality. They must not contain sensitive personal information. Promotional/marketing notifications require explicit user opt-in, and the app must provide a way to opt out.

**Triggers rejection if:**
- The app is non-functional without accepting push notifications
- Push notification payloads include sensitive data (health info, financial details, passwords)
- Marketing or promotional push notifications are sent without explicit user opt-in
- There is no way for the user to disable push notifications within the app (beyond system-level controls)

**What to check:**
- App launch flow -- verify the app works if the user declines notification permission
- `UNUserNotificationCenter` authorization request timing and handling of `.denied` status
- Push notification payload structure for sensitive data inclusion
- In-app notification preferences UI with granular opt-in/opt-out controls
- Server-side notification targeting logic for promotional vs. transactional distinction
- `Info.plist` for `UIBackgroundModes` containing `remote-notification` -- verify it is justified

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Silent push notifications for background content updates are acceptable
- The opt-out mechanism must be in-app, not just "go to Settings > Notifications"

---

### 4.5.5 Game Center

**Requirement:** Apps using Game Center must comply with Game Center terms of service. Player IDs must not be displayed to other users or shared with third parties.

**Triggers rejection if:**
- Game Center player IDs (`GKPlayer.gamePlayerID` or `GKPlayer.teamPlayerID`) are displayed in the UI or transmitted to external servers
- The app violates Game Center terms of service (e.g., fake leaderboard entries, achievement manipulation)
- Player identity information is shared with analytics or advertising services

**What to check:**
- `GameKit` imports and `GKPlayer` property access patterns
- Whether `gamePlayerID`, `teamPlayerID`, or `playerID` values are stored, displayed, or sent to external endpoints
- Leaderboard and achievement submission logic for manipulation vectors
- Network requests containing Game Center identifiers

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Use `displayName` and `alias` for user-visible player identification, not raw player IDs
- Scoped player IDs are acceptable for internal game logic but must not be exposed to users or third parties

---

### 4.5.6 Apple Emoji

**Requirement:** Apple emoji artwork must be used in accordance with Apple's emoji usage rules. Apps must not extract, repackage, or redistribute Apple's emoji designs.

**Triggers rejection if:**
- Apple emoji artwork is extracted and used as standalone image assets
- The app redistributes Apple emoji designs in sticker packs, keyboards, or other products
- Apple emoji are modified and presented as original artwork

**What to check:**
- Image assets for extracted Apple emoji artwork (PNG/SVG files of individual emoji)
- Sticker pack assets derived from Apple emoji designs
- Custom emoji keyboards that repackage Apple's emoji artwork
- Whether the app renders emoji through standard system text rendering (acceptable) vs. custom emoji image assets (potentially problematic)

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Displaying emoji through standard `UILabel`, `UITextView`, or SwiftUI `Text` is always fine
- The restriction is on extracting and repurposing the emoji artwork itself

---

## 4.7 Mini Apps, Mini Games, Streaming Games, Chatbots, Plug-ins, Game Emulators (ASR & NR)

**Requirement:** The developer of the host app is responsible for all software offered through the app, including mini apps, mini games, streaming games, chatbots, plug-ins, and game emulators. The host app and all contained software must comply with the full App Store Review Guidelines.

**Triggers rejection if:**
- The host app disclaims responsibility for third-party software offered within it
- Contained software violates any App Store guideline that the host app itself would be subject to

**What to check:**
- Whether the app hosts, distributes, or enables execution of third-party software
- Terms of service and developer agreements for the host platform
- Content moderation and review processes for hosted software
- Compliance of hosted software with the full guidelines (privacy, payments, content ratings)

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- The host developer bears full responsibility -- "we just provide the platform" is not a defense
- Game emulators specifically must comply with all sub-requirements below

---

### 4.7.1 Privacy, Content Filtering, and Digital Goods

**Requirement:** All software offered through the host app must follow the App Store privacy guidelines. The host app must include content filtering and a mechanism for users to report offensive content. Digital goods and services must follow Section 3.1 (in-app purchase requirements).

**Triggers rejection if:**
- Hosted software collects user data without proper privacy disclosures
- The host app lacks content filtering for user-generated or third-party content
- There is no mechanism for users to report inappropriate or offensive content
- Digital goods within hosted software bypass in-app purchase requirements

**What to check:**
- Privacy policy coverage for all hosted software and their data practices
- Content moderation UI: filtering controls, content rating systems, report/flag mechanisms
- In-app purchase implementation for any digital goods or services offered by hosted software
- `SKPaymentQueue` or StoreKit 2 integration for digital transactions within hosted content
- App Privacy Nutrition Labels in App Store Connect covering hosted software data collection

**Key details:**
- Content filtering must be proactive (not just reactive reporting)
- The IAP requirement from Section 3.1 applies to all digital goods regardless of whether they originate from the host or hosted software

---

### 4.7.2 No Unauthorized Native API Access

**Requirement:** Software offered through the host app must not use native platform APIs or technologies without explicit permission.

**Triggers rejection if:**
- Hosted mini apps, plug-ins, or games access native device APIs (camera, location, contacts, etc.) without the host app declaring and requesting those permissions
- Third-party code running within the host app uses private or undocumented APIs
- Hosted software bypasses the host app's permission boundaries

**What to check:**
- Permission declarations in the host app's `Info.plist` vs. what hosted software actually accesses
- JavaScript bridge or plugin interfaces that expose native APIs to hosted content
- `WKWebView` configuration for `allowsInlineMediaPlayback`, JavaScript-to-native bridges
- Dynamic code loading mechanisms that could introduce unauthorized API access

**Key details:**
- Every native API access by hosted software must be declared and authorized through the host app
- WebView-based mini apps must not use JavaScript bridges to access undeclared capabilities

---

### 4.7.3 No Unauthorized Data/Permission Sharing

**Requirement:** Hosted software must not share data or permissions with other hosted software without explicit user consent.

**Triggers rejection if:**
- One mini app/game can access data created by or collected by another mini app/game without user consent
- Shared storage or communication channels between hosted software leak user data across boundaries
- Permissions granted to one piece of hosted software are silently available to others

**What to check:**
- Data isolation between hosted software instances (sandboxing, separate storage containers)
- Shared `UserDefaults`, Keychain groups, or App Groups used across hosted software boundaries
- Cross-software communication mechanisms and whether they require user consent
- Permission inheritance patterns between the host app and hosted software

**Key details:**
- Each piece of hosted software should operate in its own data silo unless the user explicitly consents to sharing
- This is distinct from the host app's own data access -- the concern is cross-contamination between hosted software

---

### 4.7.4 Software Index with Universal Links

**Requirement:** The host app must provide a browsable index of all software it offers, and each entry must be accessible via a universal link.

**Triggers rejection if:**
- The host app does not maintain a discoverable catalog/index of available software
- Individual mini apps, games, or plug-ins are not addressable via universal links
- The index is hidden, incomplete, or not kept up to date

**What to check:**
- Presence of a catalog/directory/listing UI within the host app
- `apple-app-site-association` file on the associated domain for universal link configuration
- Universal link routing to individual pieces of hosted software
- Associated Domains entitlement (`com.apple.developer.associated-domains`) in the app's entitlements

**Key details:**
- Universal links allow Apple to index and verify the software offered through the host app
- The `apple-app-site-association` file must be served over HTTPS from the associated domain

---

### 4.7.5 Age Identification and Restriction

**Requirement:** The host app must implement an age identification mechanism and restrict access to software based on age appropriateness.

**Triggers rejection if:**
- The host app has no age verification or age gate mechanism
- Age-inappropriate content is accessible to users who have not confirmed their age
- The age restriction system is trivially bypassable (e.g., just a "Are you 18?" yes/no with no enforcement)

**What to check:**
- Age gate implementation at app launch or before accessing hosted content
- Content rating metadata for each piece of hosted software
- Whether age restrictions are enforced (not just advisory)
- Integration with device-level parental controls or Screen Time restrictions
- Persistent storage of age verification state

**Key details:**
- The age mechanism must be meaningful -- a simple unchecked toggle is insufficient
- Content ratings for hosted software should align with the host app's declared age rating in App Store Connect

---

## 4.8 Login Services (ASR & NR)

**Requirement:** Apps that offer third-party or social login (e.g., Facebook Login, Google Sign-In) must also offer Sign in with Apple as an equivalent option. Sign in with Apple must be presented with equal prominence.

**Triggers rejection if:**
- The app offers any third-party or social login option without also offering Sign in with Apple
- Sign in with Apple is present but given less prominence (smaller button, hidden behind a menu, listed last)
- The app collects more data through Sign in with Apple than name and email
- The app does not respect the user's choice of private email relay
- Sign in with Apple data is used to track users for advertising purposes

**What to check:**
- Login/signup UI for all authentication options -- verify Sign in with Apple is present and equally prominent
- `AuthenticationServices` framework import and `ASAuthorizationAppleIDProvider` usage
- `ASAuthorizationAppleIDButton` placement, size, and style relative to other login buttons
- Data collection scope after Apple ID authentication -- should be limited to `fullName` and `email`
- Handling of `privaterelay.appleid.com` email addresses -- must be supported, not blocked
- Whether the app forces users to create a secondary account after Sign in with Apple
- Network requests after Apple ID auth for any advertising/tracking payloads

**Exceptions (Sign in with Apple not required):**
- The app uses only the company's own proprietary account system (no third-party social login)
- The app is exclusively for an alternative app marketplace
- The app is an education, enterprise, or government app using institutional identity providers
- The app is a client for a specific third-party service where the account is with that service (e.g., a Gmail client requiring Google login)

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- The rule is triggered by the presence of ANY third-party/social login -- once one exists, Sign in with Apple must also exist
- "Equivalent option" means same prominence, same ease of access, same number of taps to complete
- Sign in with Apple button styling must follow Apple's Human Interface Guidelines (system-provided button styles preferred)

---

## 4.9 Apple Pay (ASR & NR)

**Requirement:** Apps using Apple Pay must display all material purchase information before the transaction is confirmed. Apple Pay branding and UI must follow Apple's guidelines. Recurring payments must be clearly disclosed.

**Triggers rejection if:**
- The final price, item details, or terms are not visible before the Apple Pay payment sheet appears
- Apple Pay branding (logo, button style, naming) deviates from Apple's guidelines
- Recurring or subscription payments via Apple Pay do not clearly disclose frequency, amount, and cancellation terms before purchase
- The Apple Pay button is used for non-payment actions

**What to check:**
- `PassKit` framework import and `PKPaymentAuthorizationViewController` / `PKPaymentAuthorizationController` usage
- `PKPaymentButton` styling and placement -- must follow Apple Pay Human Interface Guidelines
- Pre-payment summary screen: verify price, item description, shipping, and tax are displayed before the payment sheet
- `PKPaymentSummaryItem` configuration for recurring payments -- check `paymentType` is set to `.recurring` where applicable
- Recurring payment disclosures: frequency, amount, renewal terms, and cancellation instructions shown before payment
- `PKRecurringPaymentRequest` configuration for subscription details
- Marketing text and UI strings referencing "Apple Pay" -- must match official naming and trademark guidelines

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- Apple Pay is for physical goods, services, and donations -- digital content typically requires in-app purchase via StoreKit
- The Apple Pay mark and button assets must come from Apple's official resources, not custom recreations
- Recurring payment disclosure must appear BEFORE the user initiates the payment sheet

---

## 4.10 Monetizing Built-In Capabilities (ASR & NR)

**Requirement:** Apps must not charge users for accessing built-in hardware or OS features. Apps must not monetize Apple's own services or technologies in a way that implies the capability comes from the app rather than the platform.

**Triggers rejection if:**
- The app charges (via IAP, subscription, or otherwise) for access to device features like the flashlight, compass, level, calculator, or screen mirroring
- The app gates native OS capabilities behind a paywall (e.g., charging to use NFC, Bluetooth, or Wi-Fi scanning that the OS provides for free)
- The app monetizes Apple services (e.g., charging for Siri Shortcuts integration, iCloud sync, or HealthKit data display) in a way that misrepresents the value as coming from the app
- The app wraps a system utility in a minimal UI and charges for it

**What to check:**
- Core feature set vs. IAP/subscription gates -- identify whether any gated feature is a built-in device or OS capability
- `StoreKit` product definitions and what they unlock -- verify paid features provide genuine app-developed value, not repackaged system features
- Hardware API usage: `AVCaptureDevice` (torch), `CoreLocation` (compass), `CoreMotion` (level/pedometer), `CoreNFC`, `CoreBluetooth`
- Whether the app adds substantial value on top of the hardware/OS feature (e.g., a compass app with trip tracking and waypoints is acceptable; a compass app that just shows a compass behind a paywall is not)
- Marketing claims that imply the app provides capabilities that are actually built into the OS

**Key details:**
- Applies to both App Store Review (ASR) and Notarization Review (NR)
- The key distinction is whether the app adds meaningful value beyond the raw system capability
- A fitness app using HealthKit is fine if it provides analysis, coaching, or visualization -- charging for raw HealthKit data display is not
- Utility apps can charge for enhanced versions of system features if the enhancement is substantial and clearly communicated
