# Section 5: Legal

> Source: https://developer.apple.com/app-store/review/guidelines/
> Last synced: 2026-04-27

---

## 5.1 Privacy

### 5.1.1 Data Collection and Storage

#### 5.1.1(i) Privacy Policies

**Requirement:** Every app must have an accessible privacy policy that clearly explains what data is collected, how it is used, who it is shared with, and how long it is retained.

**Triggers rejection if:**
- No privacy policy URL set in App Store Connect
- No privacy policy link accessible within the app itself
- Privacy policy does not identify all types of data collected and their purposes
- Privacy policy omits data retention and deletion policies
- Privacy policy fails to disclose third-party data access or sharing

**What to check:**
- App Store Connect metadata for privacy policy URL field
- In-app Settings or onboarding screens for a tappable privacy policy link
- Privacy policy text: does it enumerate all collected data types, usage purposes, third-party sharing, retention periods, and deletion procedures?
- App Privacy nutrition labels in App Store Connect match what the privacy policy describes
- `PrivacyInfo.xcprivacy` file: `NSPrivacyCollectedDataTypes` array matches declared collection

**Key details:**
- The privacy policy must be available both externally (App Store Connect URL) and inside the app
- Policy must be written in clear language, not just legal boilerplate that obscures actual practices
- If the app collects data from children, the policy must address COPPA/GDPR-K requirements

---

#### 5.1.1(ii) Permission

**Requirement:** Apps must obtain user consent before collecting personal data. Users must be able to withdraw consent easily. Paid functionality must not be gated on consent to unrelated data sharing. All system permission dialogs must include clear, accurate purpose strings.

**Triggers rejection if:**
- Data collection occurs before or without user consent
- App functionality is locked behind consent to unrelated data sharing (e.g., "share contacts to unlock premium features")
- No mechanism to withdraw consent after granting it
- System permission dialogs use vague, misleading, or missing purpose strings
- App requests permissions at launch without context for why they are needed

**What to check:**
- All `NS*UsageDescription` keys in `Info.plist` (e.g., `NSCameraUsageDescription`, `NSPhotoLibraryUsageDescription`, `NSLocationWhenInUseUsageDescription`, `NSMicrophoneUsageDescription`, `NSContactsUsageDescription`, etc.)
- Purpose strings: are they specific and honest about why the permission is needed?
- Consent flows in onboarding or first-use screens
- Settings screen or account page for a consent withdrawal mechanism
- Whether paid features or subscriptions require unrelated data sharing as a prerequisite

**Key details:**
- Purpose strings must explain the specific feature that uses the permission, not generic statements like "to improve your experience"
- Consent withdrawal must be straightforward -- not buried behind multiple screens or requiring account deletion
- Pre-checked consent toggles are discouraged; opt-in should be affirmative

---

#### 5.1.1(iii) Data Minimization

**Requirement:** Apps must request only the data relevant to the app's core functionality. Where possible, use out-of-process pickers or share sheets instead of requesting broad access to user data stores.

**Triggers rejection if:**
- App requests access to entire photo library when only a single image selection is needed
- App requests full Contacts access when only a single contact lookup is needed
- App collects data types unrelated to its stated functionality
- App does not use `PHPickerViewController`, `UIDocumentPickerViewController`, or share sheets where appropriate

**What to check:**
- Use of `PHPickerViewController` (out-of-process photo picker) vs. `PHPhotoLibrary` (full access)
- Use of `CNContactPickerViewController` (limited picker) vs. `CNContactStore` (full access)
- Use of `UIDocumentPickerViewController` or share sheets for file access
- `NSPhotoLibraryUsageDescription` vs. `NSPhotoLibraryAddUsageDescription` (write-only is more minimal)
- Data types declared in `PrivacyInfo.xcprivacy` `NSPrivacyCollectedDataTypes` -- are all of them justified by app functionality?

**Key details:**
- Apple strongly prefers out-of-process pickers that do not grant the app persistent access to the data store
- If the app only needs to save photos (not read the library), request add-only access
- Collecting device identifiers, location, or contacts without a clear feature justification is a red flag

---

#### 5.1.1(iv) Access

**Requirement:** Apps must respect user permission decisions. If a user denies a permission, the app must provide reasonable alternative functionality or degrade gracefully.

**Triggers rejection if:**
- App crashes or becomes unusable when a permission is denied
- App repeatedly prompts the user to grant a denied permission
- App does not check authorization status before attempting to use a protected resource
- No fallback UX when a permission is denied (e.g., blank screen with no explanation)

**What to check:**
- Authorization status checks before accessing Camera, Photos, Contacts, Location, Microphone, etc.
- Fallback UI or messaging when permission is denied (e.g., explaining how to enable in Settings)
- Whether the app naggingly re-requests denied permissions on every launch or interaction
- Crash logs or error handling around permission-gated features

**Key details:**
- Apps may explain why a permission is needed and link to Settings, but must not block all functionality solely because one permission is denied (unless the permission is fundamental to the app's entire purpose, e.g., a camera app)
- Repeated permission prompts after denial are considered harassment

---

#### 5.1.1(v) Account Sign-In

**Requirement:** Apps must not require account creation or sign-in unless the app's core features are account-based. If the app offers account creation, it must also offer account deletion. Apps must not collect unnecessary personal information during sign-up. Social network apps must provide a mechanism for credential revocation.

**Triggers rejection if:**
- App requires sign-in but core features do not need an account (e.g., a flashlight app requiring login)
- App offers account creation but no in-app account deletion flow
- Sign-up collects unnecessary personal information (e.g., date of birth for a notes app)
- Social network app provides no way to revoke credentials or disconnect the account
- Account deletion flow is excessively difficult, buried, or non-functional
- Sign in with Apple not offered when third-party sign-in is available (see guideline 4.8)

**What to check:**
- Whether the app requires sign-in before any functionality is accessible
- Account creation flow: what personal data fields are required vs. optional?
- In-app account deletion: is there a working path from Settings/Profile to delete the account and associated data?
- For social networks: credential revocation mechanism (e.g., revoke OAuth tokens, disconnect account)
- App Store Connect: is account deletion URL provided where required?
- If third-party sign-in (Google, Facebook, etc.) is offered, Sign in with Apple must also be offered

**Key details:**
- Account deletion must actually delete server-side data, not just deactivate the account
- Apple may require the account deletion URL to be submitted in App Store Connect
- Apps in regulated industries (e.g., banking) may have legitimate reasons to require sign-in, but must still offer deletion

---

#### 5.1.1(vi) Surreptitious Discovery of Private Data

**Requirement:** Developers must not use their apps to surreptitiously discover passwords or any other private user data. Egregious violation results in removal from the Apple Developer Program.

**Triggers rejection if:**
- App intercepts, logs, or keyloggs password fields or other secure inputs
- App attempts to access Keychain items belonging to other apps
- App uses accessibility features, input monitoring, or screen scraping to capture credentials or other private data
- App covertly extracts private data (messages, financial info, health info, contacts) from device-level sources without user consent
- App probes for private data outside the scope of its declared purpose strings and entitlements

**What to check:**
- Keychain access patterns: is the app reading items it did not create?
- Custom keyboard extensions: do they log or transmit keystrokes from secure fields?
- Any network requests that transmit password fields, message contents, or other private data to external servers
- Use of `UITextField.isSecureTextEntry` -- is it respected or circumvented?
- Accessibility API usage (UIAccessibility, AX protocols) used to read text from other apps' secure fields
- Background-running processes scraping pasteboard, clipboard, or notification content for private data
- Data collected vs. declared purpose strings — flag any extraction beyond the declared scope

**Key details:**
- The guideline now explicitly covers ALL private data, not just passwords — credentials, messages, health/financial data, etc.
- Consequence is explicit: removal from the Apple Developer Program
- Password autofill via standard system mechanisms (ASWebAuthenticationSession, AutoFill) is fine
- The violation is the surreptitious nature — covert collection without user awareness, not all data collection

---

#### 5.1.1(vii) SafariViewController Visibility

**Requirement:** `SFSafariViewController` must be visible and not hidden from the user. It must not be used for invisible tracking or data collection.

**Triggers rejection if:**
- `SFSafariViewController` is presented with zero-size frame, off-screen, or behind other views
- `SFSafariViewController` is used for cookie syncing or tracking without user visibility
- Hidden web views are used to silently authenticate or track users

**What to check:**
- All instantiations of `SFSafariViewController` -- are they presented modally or pushed onto a visible navigation stack?
- Frame/bounds of the presented view controller -- not zero-sized or off-screen
- Whether `SFSafariViewController` is dismissed immediately after loading (sign of invisible tracking)
- Use of `WKWebView` with `isHidden = true` or zero-frame for tracking purposes
- `SFAuthenticationSession` / `ASWebAuthenticationSession` usage (these are the correct APIs for auth flows)

**Key details:**
- The intent of this rule is to prevent apps from exploiting Safari's cookie jar for cross-app tracking
- Legitimate OAuth flows should use `ASWebAuthenticationSession`, not hidden `SFSafariViewController`

---

#### 5.1.1(viii) Personal Information Compilation

**Requirement:** Apps must not compile personal information databases from device data without explicit user consent.

**Triggers rejection if:**
- App scrapes contacts, photos, messages, or other personal data to build profiles or databases
- App aggregates user data across devices or accounts without disclosure and consent
- App harvests device data (calendar, reminders, call logs) for purposes beyond stated app functionality

**What to check:**
- Contacts framework usage: does the app upload or sync the full contact list to a server?
- Photos framework usage: does the app scan or upload photos beyond what the user explicitly selects?
- Any bulk data extraction patterns from system frameworks (EventKit, CallKit, etc.)
- Network traffic: are large payloads of personal data being sent to external servers?

**Key details:**
- Even with consent, the data usage must be proportionate to the app's purpose
- Building advertising profiles or social graphs from contact lists is a common violation

---

#### 5.1.1(ix) Regulated Fields

**Requirement:** Apps operating in regulated industries (health, finance, legal, etc.) must be submitted by the legal entity that provides the regulated service.

**Triggers rejection if:**
- Health, fintech, or legal app is submitted by an individual developer account rather than the regulated entity
- App provides regulated services (insurance, banking, clinical diagnostics) without the submitting entity holding appropriate licenses
- Developer account name does not match the entity providing the regulated service

**What to check:**
- Developer account type: Organization vs. Individual
- Developer account name alignment with the entity providing regulated services
- HealthKit entitlements: if present, verify the submitting entity is a legitimate health organization
- Financial transaction features: verify the submitting entity is a licensed financial institution
- App Store Connect: organization name and D-U-N-S number

**Key details:**
- This is about who submits the app, not the app's content alone
- Third-party developers building apps for regulated entities must have the entity submit under their own account
- Includes health, finance, insurance, legal, real estate, and other government-regulated fields

---

#### 5.1.1(x) Basic Contact Info

**Requirement:** Requests for basic contact information (name, email) to use the app must be optional, not mandatory, unless the information is essential to the app's core function.

**Triggers rejection if:**
- App requires name and email before any functionality is available, and the features do not need that information
- Mandatory profile completion with personal details for apps where identity is not core (e.g., utility apps, calculators)

**What to check:**
- Onboarding flow: can the user skip or dismiss contact info requests?
- Required vs. optional form field validation
- Whether the app's core function genuinely needs the user's name or email

**Key details:**
- Apps with account-based features (social, messaging, etc.) have legitimate reasons to require contact info
- The test is whether the app's primary value proposition requires the data

---

### 5.1.2 Data Use and Sharing

#### 5.1.2(i) Permission and Third-Party Sharing

**Requirement:** Collected data must not be shared with third parties — including third-party AI services — without user consent. Sharing with third-party AI must be explicitly disclosed and require explicit permission. Tracking requires App Tracking Transparency (ATT) authorization. System functionality (e.g., app features, content access) must not be gated on granting tracking permission.

**Triggers rejection if:**
- App tracks users without presenting the ATT prompt
- App shares user data with third-party ad networks, analytics, data brokers, or AI services without disclosure and explicit permission
- App functionality is locked or degraded when the user declines ATT tracking
- App uses fingerprinting as a substitute for tracking when ATT consent is denied
- Third-party SDKs perform tracking without ATT consent

**What to check:**
- `PrivacyInfo.xcprivacy`: `NSPrivacyTracking` key (boolean -- is tracking declared?)
- `PrivacyInfo.xcprivacy`: `NSPrivacyTrackingDomains` array (list of tracking domains)
- `ATTrackingManager.requestTrackingAuthorization` usage in code
- Import of `AppTrackingTransparency` framework
- Third-party SDK privacy manifests (each SDK should have its own `PrivacyInfo.xcprivacy`)
- Whether app features are conditionally disabled based on `ATTrackingManager.AuthorizationStatus`
- Data collection declarations in App Store Connect privacy nutrition labels
- Network traffic to known ad/analytics domains (e.g., `graph.facebook.com`, `analytics.google.com`, `adjust.com`)
- `SKAdNetwork` usage (permitted alternative to user-level tracking)

**Key details:**
- "Tracking" means linking user or device data with third-party data for advertising, or sharing user data with a data broker
- Device fingerprinting (using device characteristics as a substitute for IDFA) is explicitly prohibited
- ATT must be presented before any tracking occurs, not retroactively
- Each third-party SDK must include its own privacy manifest; the app is responsible for all embedded SDKs
- This is both an App Store Review (ASR) and Notarization Requirement (NR)

---

#### 5.1.2(ii) No Data Repurposing

**Requirement:** Data collected for one stated purpose must not be repurposed for a different purpose without obtaining new consent.

**Triggers rejection if:**
- Data collected for app functionality is later used for advertising without additional consent
- User-provided content (e.g., photos for editing) is used to train ML models without disclosure
- Contact information collected for account creation is used for marketing emails without opt-in

**What to check:**
- Privacy policy: does it cover all actual uses of collected data?
- Marketing or analytics code paths that use data originally collected for core features
- ML training pipelines that ingest user-provided content
- Email or push notification marketing sent without separate opt-in

**Key details:**
- The principle is purpose limitation: data use must match the purpose stated at collection time
- New purposes require new, specific consent

---

#### 5.1.2(iii) No Surreptitious User Profiling

**Requirement:** Apps must not secretly build user profiles based on collected data.

**Triggers rejection if:**
- App collects behavioral data (usage patterns, preferences, browsing) to build advertising or behavioral profiles without disclosure
- Hidden analytics that profile users beyond what is disclosed in the privacy policy
- Shadow profiles built from data the user did not knowingly provide

**What to check:**
- Analytics SDK integrations: what user properties and events are being tracked?
- Custom user profiling or segmentation code
- Data sent to external analytics or advertising services
- Whether profiling activities are disclosed in the privacy policy

**Key details:**
- Profiling for personalization within the app may be acceptable if disclosed
- The violation is secrecy -- profiling the user without their knowledge

---

#### 5.1.2(iv) No Contacts or Photos Database Building

**Requirement:** Apps must not build private databases from users' Contacts or Photos data.

**Triggers rejection if:**
- App uploads the user's entire contact list to external servers
- App scrapes or indexes the user's photo library to build a facial recognition or image database
- Contact or photo data is stored server-side beyond what is needed for the user-initiated feature

**What to check:**
- `CNContactStore` usage: is the full contact list fetched and transmitted?
- `PHAsset` / `PHFetchResult` usage: is the full photo library enumerated and uploaded?
- Server-side storage of contacts or photos data
- Network requests containing bulk personal data from these frameworks

**Key details:**
- Apps may access individual contacts or photos the user explicitly selects
- The violation is bulk extraction and external storage of these data stores

---

#### 5.1.2(v) Contact Users at Their Initiative

**Requirement:** Apps must only contact users (via email, push, SMS, etc.) when the user has explicitly initiated or opted into communication.

**Triggers rejection if:**
- App sends unsolicited marketing emails or push notifications without opt-in
- App shares user contact info with third parties who then contact the user
- Push notifications are used for advertising without user consent

**What to check:**
- Push notification registration flow: is there an opt-in before requesting push permission?
- Email collection: is there a separate marketing opt-in checkbox (not pre-checked)?
- Third-party communication services that might contact users independently

**Key details:**
- Transactional communications (order confirmations, security alerts) are generally permitted
- Marketing communications always require explicit opt-in

---

#### 5.1.2(vi) HomeKit, HealthKit, ClassKit, and Motion & Fitness Data Restrictions

**Requirement:** Data from HomeKit, HealthKit, ClassKit, and CoreMotion must be used only for their intended health, home automation, or education purposes. This data must not be shared with third parties for advertising, sold, or used for purposes unrelated to improving the user's health, home, or education experience.

**Triggers rejection if:**
- HealthKit data is shared with advertisers or data brokers
- HomeKit data is used for purposes beyond home automation
- ClassKit data is used for advertising or non-educational profiling
- Motion and fitness data is sold or shared for advertising

**What to check:**
- `HealthKit` entitlement in the app's entitlements file and capability configuration
- `HKHealthStore` usage: what data types are read/written?
- `HomeKit` entitlement and `HMHomeManager` usage
- `ClassKit` imports and `CLSContext` / `CLSDataStore` usage
- `CoreMotion` framework imports: `CMMotionManager`, `CMPedometer`, `CMMotionActivityManager`
- Whether any of this data flows to analytics, advertising, or third-party SDKs
- Privacy policy: does it specifically address health/home/education data handling?

**Key details:**
- HealthKit data must not be stored in iCloud (see 5.1.3)
- These restrictions are stricter than general data rules -- even with consent, certain uses are prohibited
- Apps using HealthKit must have a clear health or fitness purpose

---

#### 5.1.2(vii) Apple Pay Data

**Requirement:** Apps using Apple Pay may share user data acquired via Apple Pay with third parties only to facilitate or improve delivery of goods and services. No other use of Apple Pay data with third parties is permitted.

**Triggers rejection if:**
- Apple Pay transaction or user data is shared with analytics platforms, ad networks, or data brokers
- Apple Pay data is used for advertising, marketing, profiling, or any purpose not tied to fulfilling/improving the actual goods or services purchased
- Apple Pay data is sold or licensed to third parties

**What to check:**
- `PassKit` framework usage and `PKPaymentAuthorizationController` / `PKPaymentAuthorizationViewController` flows
- Network calls following Apple Pay completion: where does payment data flow? Each downstream recipient must be a fulfillment/delivery counterparty (carrier, processor, vendor) — not an ad or analytics platform
- Analytics SDK events that capture Apple Pay transaction details
- Server-side storage and onward sharing of Apple Pay-derived data
- Privacy policy: does it limit Apple Pay data use to delivery/fulfillment?

**Key details:**
- This is a narrow, purpose-bound permission: Apple Pay data may flow to third parties only to deliver or improve the purchased goods/services
- Even with user consent, advertising or marketing uses of Apple Pay data are prohibited
- Standard payment processor and carrier integrations are fine; downstream marketing pipelines are not

---

### 5.1.3 Health and Health Research

#### 5.1.3(i) No Health Data for Advertising

**Requirement:** Health data collected through HealthKit, CareKit, or similar health frameworks must not be used for advertising or marketing purposes.

**Triggers rejection if:**
- Health data is sent to advertising SDKs or ad networks
- Health metrics are used to target or personalize advertisements
- Health data is included in analytics events sent to advertising platforms

**What to check:**
- Data flow from `HKHealthStore` reads -- does any of this data reach ad SDKs?
- Ad SDK initialization: are health-related user properties being set?
- Analytics events that include health metrics
- Network requests that combine health data with advertising identifiers

**Key details:**
- This is an absolute prohibition -- no amount of consent makes it acceptable
- Includes indirect use such as using health conditions to select ad categories

---

#### 5.1.3(ii) No False Health Data; No iCloud Storage

**Requirement:** Apps must not write false or fabricated data to HealthKit. Health data must not be stored in iCloud.

**Triggers rejection if:**
- App writes synthetic, test, or fabricated data to HealthKit in production
- App stores health data in iCloud (CloudKit, iCloud Drive, or iCloud Key-Value Store)
- App allows users to manually enter health data that could be misleading to other health apps

**What to check:**
- `HKHealthStore.save()` calls: what data is being written and is it legitimate?
- CloudKit or iCloud entitlements combined with health data storage
- `NSUbiquitousKeyValueStore` usage for health-related data
- `CKContainer` usage that stores health records
- Core Data with iCloud sync enabled for health data models

**Key details:**
- Health data should be stored locally or on the developer's own secure servers, never in iCloud
- Test or demo data must not be written to the real HealthKit store

---

#### 5.1.3(iii) Informed Consent for Research

**Requirement:** Apps conducting health research involving human subjects must obtain informed consent from participants.

**Triggers rejection if:**
- Research data is collected without presenting an informed consent form
- Consent form is missing required elements (purpose, procedures, risks, benefits, voluntary participation, withdrawal rights)
- Participants cannot withdraw from the study

**What to check:**
- `ResearchKit` imports and usage (`ORKConsentDocument`, `ORKConsentReviewStep`)
- Consent flow implementation: does it present a full consent document with signature?
- Withdrawal mechanism: can participants leave the study and request data deletion?
- Study protocol documentation (may be referenced in the app or app review notes)

**Key details:**
- Informed consent is a legal and ethical requirement, not just an Apple policy
- The consent process must be meaningful, not a quick checkbox

---

#### 5.1.3(iv) Ethics Board Approval

**Requirement:** Health research apps must have approval from an independent ethics review board (IRB or equivalent).

**Triggers rejection if:**
- App conducts human subjects research without IRB approval
- IRB approval documentation is not available upon request
- Research protocol has not been reviewed by a qualified ethics board

**What to check:**
- App review notes: is IRB approval referenced?
- ResearchKit study configuration: does it reference an approved protocol?
- Developer documentation or website: is ethics board approval disclosed?

**Key details:**
- Apple may request proof of IRB approval during review
- This applies to any app that collects data for research purposes involving human subjects, not just clinical trials

---

### 5.1.4 Kids

#### 5.1.4(a) COPPA and GDPR Compliance

**Requirement:** Apps in the Kids Category or apps that target children must comply with COPPA (Children's Online Privacy Protection Act), GDPR Article 8, and equivalent local regulations. Apps must collect only necessary data, provide useful functionality regardless of age, and must not include third-party analytics or advertising.

**Triggers rejection if:**
- Kids app includes third-party advertising SDKs
- Kids app includes third-party analytics SDKs (except limited Apple-approved services)
- App collects personal data from children without verifiable parental consent
- App collects birthdate or parental contact information beyond what is required for regulatory compliance
- App fails to provide useful functionality if the user declines to share age or personal information
- Kids app does not comply with COPPA or GDPR-K requirements

**What to check:**
- App Store Connect: age rating and Kids Category designation
- Third-party SDK inventory: are any ad SDKs present (AdMob, Meta Audience Network, Unity Ads, etc.)?
- Third-party analytics SDKs: are any present (Firebase Analytics, Amplitude, Mixpanel, etc.)?
- Data collection during onboarding: what is collected from child users?
- Age gate implementation: does it comply with COPPA (date entry, not just "Are you 13+")?
- Parental consent mechanisms (verifiable parental consent for children under 13/16)
- `PrivacyInfo.xcprivacy`: what data types are declared for collection?

**Key details:**
- COPPA applies to children under 13; GDPR Article 8 applies to children under 16 (varies by EU member state, minimum 13)
- "No third-party analytics" is strict -- even analytics SDKs that claim to be privacy-safe are generally prohibited
- Apple-provided analytics (App Analytics in App Store Connect) is acceptable
- The app must still be useful and functional even if minimal data is collected

---

#### 5.1.4(b) Limited Third-Party Services

**Requirement:** Kids Category apps may use limited third-party services subject to the same restrictions as guideline 1.3 (kids category content). Apps in the Kids Category must include a privacy policy. The term "For Kids" is reserved exclusively for apps in the Kids Category.

**Triggers rejection if:**
- Kids app uses third-party services that do not comply with kids privacy restrictions
- Kids Category app lacks a privacy policy
- App not in the Kids Category uses "For Kids" in its name, subtitle, or description
- Third-party services in kids apps collect data independently or for their own purposes

**What to check:**
- App Store Connect: Kids Category designation and privacy policy URL
- Third-party service integrations: do they have their own kids-compliant privacy policies?
- App metadata (name, subtitle, description, keywords): unauthorized use of "For Kids"
- Third-party SDK data flows: do any SDKs independently collect or transmit data?

**Key details:**
- "For Kids" is a regulated term in the App Store -- using it outside the Kids Category is a rejection
- Third-party services in kids apps must operate as data processors only, not independent controllers
- Privacy policy must specifically address children's data practices

---

### 5.1.5 Location Services

**Requirement:** Location data must only be used when directly relevant to the app's features and services. Apps must notify users and obtain consent before collecting location data. Location APIs must not be used for emergency services dispatching or autonomous device control — except for small devices such as drones, toys, and remote car alarms where location is core to device operation.

**Triggers rejection if:**
- App requests location access for features that do not require it
- App uses location data without notifying the user of the purpose
- Location access is requested without a clear, specific purpose string
- App uses "Always" location when "When In Use" would suffice
- App uses location for emergency services dispatch or autonomous control of full-size vehicles (small devices like drones, toys, and remote car alarms are exempt)
- App collects location data in the background without justification

**What to check:**
- `CoreLocation` imports and `CLLocationManager` usage
- `Info.plist` location usage description keys:
  - `NSLocationWhenInUseUsageDescription`
  - `NSLocationAlwaysAndWhenInUseUsageDescription`
  - `NSLocationAlwaysUsageDescription` (deprecated but may still be present)
- Background modes: `location` in `UIBackgroundModes` array in `Info.plist`
- Location accuracy requested: `kCLLocationAccuracyBest` vs. `kCLLocationAccuracyReduced`
- Geofencing / region monitoring usage (`CLCircularRegion`, `startMonitoring(for:)`)
- Whether the app's stated purpose justifies the level of location access requested
- Significant location change monitoring (`startMonitoringSignificantLocationChanges`)

**Key details:**
- "Always" location access has a much higher bar for justification than "When In Use"
- Background location usage requires a visible indicator and clear user benefit
- Apple may reject apps that request precise location when approximate would suffice
- Location data is considered sensitive and is subject to all data minimization requirements

---

## 5.2 Intellectual Property

### 5.2.1 Licensed or Owned Content Only

**Requirement:** Apps must only use content (images, audio, video, text, code, fonts, etc.) that the developer owns or has properly licensed.

**Triggers rejection if:**
- App contains copyrighted content without proper licensing
- App uses stock assets, fonts, or media without valid licenses
- User-generated content features do not include DMCA/takedown mechanisms
- App bundles third-party code or libraries without complying with their licenses

**What to check:**
- Bundled assets: images, audio files, video files, fonts -- are licenses documented?
- Third-party library licenses (check `Pods/`, `Carthage/`, `Package.swift` dependencies)
- Open-source license compliance (MIT, Apache, GPL attribution requirements)
- User-generated content: is there a reporting/takedown mechanism?
- App Store Connect: are content rights declarations accurate?

**Key details:**
- Using placeholder images from the web (Unsplash, etc.) still requires compliance with their license terms
- GPL-licensed code has specific obligations that may conflict with App Store distribution
- Apple may request proof of licensing for recognizable content

---

### 5.2.2 Third-Party Service Authorization

**Requirement:** Apps that interface with third-party services must have proper authorization to use those services' APIs and data.

**Triggers rejection if:**
- App uses a third-party API without proper API keys or authorization
- App scrapes or reverse-engineers third-party services instead of using official APIs
- App violates the terms of service of third-party platforms it integrates with
- App impersonates or misrepresents its relationship with a third-party service

**What to check:**
- Third-party API integrations: are official SDKs or documented APIs being used?
- API key management: are keys properly secured (not hardcoded in client code)?
- Web scraping code: is the app scraping content instead of using an API?
- Terms of service compliance for integrated services (social platforms, payment processors, etc.)

**Key details:**
- Using unofficial or undocumented APIs of third-party services is a violation
- Even if a third-party API is technically accessible, using it without authorization violates this guideline
- This includes unauthorized use of Apple's own internal APIs

---

### 5.2.3 No Illegal File Sharing

**Requirement:** Apps must not facilitate unauthorized copying, downloading, or sharing of copyrighted content.

**Triggers rejection if:**
- App enables downloading of copyrighted music, movies, or books without authorization
- App provides torrent, P2P, or file-sharing functionality for pirated content
- App circumvents DRM (Digital Rights Management) protections
- App facilitates unauthorized redistribution of copyrighted material

**What to check:**
- Download functionality: what content can users download, and is it authorized?
- File sharing features: are there safeguards against piracy?
- DRM handling: does the app respect content protection?
- Media playback: does the app play content from unauthorized sources?

**Key details:**
- Apps that allow saving content from other services (e.g., social media downloaders) are frequently rejected
- Even if the app itself does not host content, facilitating access to pirated content is a violation
- Legal file sharing (user's own files, properly licensed content) is acceptable

---

### 5.2.4 Apple Endorsements

#### 5.2.4(a) No Implied Apple Endorsement

**Requirement:** Apps must not suggest or imply that Apple endorses, sponsors, or is affiliated with the app or its developer.

**Triggers rejection if:**
- App marketing materials suggest Apple endorsement or partnership
- App UI or description implies Apple recommendation or certification
- App name, icon, or description creates confusion about Apple affiliation

**What to check:**
- App Store Connect metadata: name, subtitle, description, promotional text
- In-app copy and marketing screens: references to Apple endorsement
- App icon and screenshots: Apple logo usage or Apple product imagery implying endorsement
- Website and external marketing materials linked from the app

**Key details:**
- Stating compatibility with Apple products ("Works with iPhone") is acceptable
- Claiming Apple recommends or endorses the app is not
- This is both an App Store Review (ASR) and Notarization Requirement (NR)

---

#### 5.2.4(b) Editor's Choice

**Requirement:** The "Editor's Choice" badge is applied solely by Apple's editorial team. Apps must not self-apply or claim Editor's Choice status.

**Triggers rejection if:**
- App displays an "Editor's Choice" badge it was not awarded
- App metadata references "Editor's Choice" without having received the designation
- App creates its own badges or labels that mimic Apple's Editor's Choice

**What to check:**
- App Store Connect metadata: references to "Editor's Choice"
- In-app assets: any badges or labels resembling Apple's Editor's Choice
- Marketing materials: claims of Editor's Choice status

**Key details:**
- This is a strict prohibition -- only Apple can apply this designation
- This is both an App Store Review (ASR) and Notarization Requirement (NR)

---

### 5.2.5 No Confusion with Apple Products

**Requirement:** Apps must not be designed in a way that could be confused with existing Apple hardware or software products.

**Triggers rejection if:**
- App name is confusingly similar to an Apple product (e.g., "iMessage Pro", "AirDrop Plus")
- App icon mimics the design of a built-in Apple app
- App UI deliberately imitates a system app to deceive users
- App functionality description suggests it replaces or extends a built-in Apple feature in a misleading way

**What to check:**
- App name: does it use Apple product names or naming conventions (i-prefix, Apple prefix)?
- App icon: does it resemble any built-in iOS/macOS app icon?
- UI design: does it mimic system apps (Messages, Phone, Settings, etc.) in a deceptive way?
- App description: does it claim to be a replacement for or extension of Apple's own apps?

**Key details:**
- Using "i" prefix alone is not necessarily a violation, but combined with Apple-like branding it can be
- Apps that extend Apple functionality (e.g., widgets for Apple Health) are fine as long as they do not create identity confusion
- This is both an App Store Review (ASR) and Notarization Requirement (NR)

---

## §5.3 Gaming, Gambling, and Lotteries

Gaming and gambling are highly regulated industries. Verify legal obligations in every location where the app is available before including gambling features.

### §5.3.1 Sweepstakes and Contests Sponsorship

**Requirement:** Sweepstakes and contests must be sponsored by the app developer.

**Triggers rejection if:**
- Sweepstakes or contest is sponsored by an entity other than the app developer

**What to check:**
- Official rules for any sweepstakes or contest — sponsor identification must match the developer
- Marketing copy and promotional materials for sponsor attribution

**Key details:**
- The developer submitting the app must be the sponsoring entity; third-party-sponsored promotions are not permitted

---

### §5.3.2 Official Rules Must Disclaim Apple

**Requirement:** Official rules for sweepstakes, contests, and raffles must be presented in the app and must make clear that Apple is not a sponsor or involved in any way.

**Triggers rejection if:**
- Sweepstakes or contest rules are not displayed within the app
- Rules do not explicitly state Apple has no involvement
- Rules suggest Apple endorses or participates in the promotion

**What to check:**
- In-app display of official rules for any sweepstakes, contest, or raffle
- Rules text for an explicit Apple disclaimer (e.g., "This promotion is in no way sponsored, endorsed, or administered by Apple Inc.")
- App Store Connect metadata for accurate sweepstakes descriptions

**Key details:**
- Rules must be accessible within the app, not just on an external website
- The disclaimer must be explicit — a generic "Apple is not responsible" notice is insufficient

---

### §5.3.3 No IAP for Real Money Gaming Credits

**Requirement:** Apps may not use in-app purchase to purchase credits or currency for use in real money gaming.

**Triggers rejection if:**
- IAP is used to purchase chips, coins, or credits that fund real money gambling balances
- The app mixes IAP purchase flows with real money wagering mechanics

**What to check:**
- IAP product definitions (`StoreKit` / `.storekit` config) for gambling-related credits or currencies
- Code paths connecting IAP completion to real money gaming balances
- Distinction between virtual-only gaming (no cash value, no cash out) and real money gambling

**Key details:**
- Virtual currency used exclusively within a free-to-play game (no real-money redemption) may use IAP
- The prohibition is specifically on IAP as a funding mechanism for real money wagering

---

### §5.3.4 Real Money Gaming and Lottery Requirements

**Requirement:** Apps offering real money gaming (sports betting, poker, casino games, horse racing) or lotteries must have the necessary licensing in all applicable locations, must be geo-restricted to legal jurisdictions, and must be free on the App Store. Lottery apps must involve consideration, chance, and a prize.

**Triggers rejection if:**
- App offers real money wagering without proper licensing in each jurisdiction where it operates
- App is not geo-restricted to jurisdictions where it is licensed
- Real money gaming or lottery app has a paid price on the App Store
- Lottery app does not contain all three elements: consideration, chance, and prize

**What to check:**
- Licensing documentation for each jurisdiction — submit in App Review Notes
- Geo-restriction implementation (`CoreLocation` or server-side IP/region detection blocking non-licensed regions)
- App Store Connect availability settings vs. licensing coverage
- App Store price — must be free (no upfront cost)
- Lottery mechanics for all three required components: consideration (entry fee or required purchase), chance (random outcome), and prize

**Key details:**
- Licensing is per-jurisdiction; a license in one country does not authorize operation in others
- Geo-restriction must actively block access in unlicensed regions, not just display a warning
- The free-on-App-Store requirement applies even if the game involves real money wagers inside the app

---

## §5.4 VPN Apps (ASR & NR)

**Requirement:** Apps offering VPN services must use the `NEVPNManager` API, must be offered only by developers enrolled as an organization, must clearly disclose user data collection and usage before any purchase or service activation, and must not sell, use, or disclose user data to third parties. VPN apps must not violate local laws; where licensing is required, license information must be provided in App Review Notes.

**Triggers rejection if:**
- VPN app does not use the `NEVPNManager` API
- VPN app is submitted by an individual developer account (not an organization)
- App does not clearly disclose what user data is collected and how it is used before purchase or sign-up
- App sells, uses, or discloses user data to third parties for any purpose
- Privacy policy does not explicitly commit to no third-party data sharing or data selling
- App operates in a jurisdiction requiring a VPN license without disclosing that license in App Review Notes
- Non-compliant VPN apps risk removal from the App Store and developer program expulsion

**What to check:**
- `NetworkExtension` framework import and `NEVPNManager` / `NETunnelProviderManager` usage
- Developer account enrollment type — must be Organization, not Individual
- Pre-purchase or pre-signup disclosure UI: clearly state what data is collected and how it is used
- Privacy policy: explicit commitment to not selling, using, or disclosing user data to third parties
- App Review Notes: licensing information if operating in jurisdictions with VPN licensing requirements
- App entitlements file for `com.apple.developer.networking.networkextension` with VPN-related entitlement values
- Whether the app also serves as a parental control, content blocker, or security tool (these may also use `NEVPNManager`)

**Key details:**
- Marked ASR and NR — applies to both distribution channels
- Parental control apps, content blockers, and security apps from Apple-approved providers may also use `NEVPNManager`
- Data disclosure must occur before any purchase or service use — not buried in settings post-signup
- VPN apps that violate these terms face removal from the App Store and developer program expulsion

---

## §5.5 Mobile Device Management (ASR & NR)

**Requirement:** Apps offering Mobile Device Management (MDM) services must request the MDM capability from Apple and may only be offered by commercial enterprises, educational institutions, or government agencies.

**Triggers rejection if:**
- MDM app does not have Apple-approved MDM capability
- App is submitted by an individual developer rather than a qualifying organization
- App is broadly available to general consumers (MDM must be restricted to enterprise, education, or government)

**What to check:**
- Apple MDM capability approval — confirm this has been requested and granted before submission
- Developer account type and organizational identity in App Store Connect
- App availability settings — MDM apps should not be distributed broadly via the general consumer App Store; Apple Business Manager or Apple School Manager is the expected distribution path
- MDM enrollment configuration and device management profile handling
- Entitlements for MDM-related capabilities (e.g., `com.apple.developer.device-information.user-assigned-device-name`)

**Key details:**
- Marked ASR and NR — applies to both distribution channels
- MDM apps manage devices on behalf of organizations; individual consumer use is not a valid use case
- The MDM capability must be requested from Apple and approved prior to App Review submission
- Distribution is typically via Apple Business Manager (enterprises) or Apple School Manager (education), not the general App Store
