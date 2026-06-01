# Section 1: Safety

> Source: https://developer.apple.com/app-store/review/guidelines/
> Last synced: 2026-06-01

---

## §1.1 Objectionable Content

Apps should not include content that is offensive, insensitive, upsetting, intended to disgust, in exceptionally poor taste, or just plain creepy.

### §1.1.1 Defamatory, Discriminatory, or Mean-Spirited Content

**Requirement:** No defamatory, discriminatory, or mean-spirited content, including references or commentary about religion, race, sexual orientation, gender, national/ethnic origin, or other targeted groups -- particularly if the app is likely to humiliate, intimidate, or harm a targeted individual or group.

**Triggers rejection if:**
- App contains slurs, hate speech, or derogatory language targeting protected groups
- Content mocks, demeans, or dehumanizes individuals based on identity characteristics
- User-facing text or imagery singles out a group for ridicule or hostility

**What to check:**
- All user-facing strings, localized string files (`Localizable.strings`, `.xcstrings`, `strings.xml`)
- App Store metadata: title, subtitle, description, keywords, screenshots
- Hardcoded content in storyboards, XIBs, SwiftUI views, or HTML assets
- Image assets and bundled media for offensive imagery
- In-app content databases or bundled JSON/plist data files

**Key details:**
- Professional political satirists and humorists are generally exempt from this rule
- The exemption is narrow -- it applies to recognized satire, not casual mockery framed as humor

---

### §1.1.2 Realistic Portrayals of Violence

**Requirement:** No realistic portrayals of people or animals being killed, maimed, tortured, or abused. No content that encourages violence.

**Triggers rejection if:**
- App contains realistic depictions of violence against people or animals
- Game enemies solely target a specific race, culture, real government, corporation, or any other real entity
- Content glorifies or encourages violence

**What to check:**
- Image and video assets for graphic or realistic violent imagery
- Game assets: character models, textures, animations depicting gore or torture
- Enemy/NPC definitions -- check if targets map to real-world groups, governments, or corporations
- Content rating declarations in App Store Connect metadata
- Bundled media files (`.mp4`, `.mov`, `.gif`, `.png`, `.jpg`) for violent scenes

**Key details:**
- Stylized or cartoon violence may be acceptable depending on context and age rating
- The "real entity" restriction on game enemies is strictly enforced -- fictional stand-ins with obvious parallels may also be flagged

---

### §1.1.3 Weapons and Dangerous Objects

**Requirement:** No depictions encouraging illegal or reckless use of weapons and dangerous objects. No facilitation of firearms or ammunition purchases.

**Triggers rejection if:**
- App depicts or instructs on illegal/reckless weapon use
- App facilitates purchasing firearms or ammunition
- App provides instructions for assembling weapons or explosives

**What to check:**
- In-app purchase catalogs and linked e-commerce URLs for firearm/ammunition sales
- Deep links or URL schemes pointing to external weapon retailers
- Instructional content (text, video, PDF) related to weapon modification or assembly
- Bundled databases or product catalogs referencing weapon sales

**Key details:**
- Informational/educational content about weapons may be acceptable if presented responsibly
- Apps for licensed firearms dealers must still comply -- the rule covers facilitation of purchases through the app

---

### §1.1.4 Sexual or Pornographic Material

**Requirement:** No overtly sexual or pornographic material. Defined by Apple as explicit descriptions or displays of sexual organs or activities intended to stimulate erotic rather than aesthetic or emotional feelings.

**Triggers rejection if:**
- App contains explicit sexual imagery or descriptions
- App functions as a "hookup" app facilitating sexual encounters
- App may be used to facilitate prostitution, human trafficking, or exploitation
- App includes pornographic content or links to pornographic material

**What to check:**
- All bundled image, video, and audio assets for explicit content
- App Store screenshots and preview videos
- WebView URLs and any hardcoded or dynamically loaded web content
- URL schemes, deep links, or redirects to adult content sites
- UGC features without content moderation (see also §1.2)
- App description and marketing copy for suggestive language
- Core app functionality and user flows for matchmaking/hookup mechanics

**Key details:**
- "Hookup" apps are explicitly called out as a category that violates this rule
- Apps that could be repurposed for exploitation even if not their primary function are at risk

---

### §1.1.5 Inflammatory Religious Content

**Requirement:** No inflammatory religious commentary. No inaccurate or misleading quotations of religious texts.

**Triggers rejection if:**
- App contains content that mocks, denigrates, or inflames religious beliefs
- App presents altered, fabricated, or misleading quotations attributed to religious texts
- App misrepresents the teachings of a religion in a way designed to provoke

**What to check:**
- Bundled text content referencing religious texts (Bible, Quran, Torah, Vedas, etc.)
- Quotation databases -- verify citations are accurate and properly attributed
- Commentary or editorial content for inflammatory tone
- User-facing text in any language for derogatory religious references

**Key details:**
- Scholarly or educational discussion of religion is acceptable
- The key distinction is between respectful discourse and content designed to provoke or mislead

---

### §1.1.6 False Information and Features (ASR & NR)

**Requirement:** No false information or features. No inaccurate device data or trick/joke functionality such as fake location trackers. Stating "for entertainment purposes" does not overcome this guideline.

**Triggers rejection if:**
- App provides deliberately inaccurate data (e.g., fake location, fake sensor readings)
- App includes trick or joke functionality that misleads users about real capabilities
- App enables anonymous or prank phone calls or SMS/MMS messaging
- App claims device capabilities it does not actually have

**What to check:**
- `CoreLocation` usage -- verify location data is real, not spoofed or fabricated
- `CallKit`, `MessageUI`, or telephony framework usage for anonymous/prank call features
- App Store description claims vs. actual implemented functionality
- Any "prank" or "joke" features in the UI or feature list
- Fake sensor data generation (accelerometer, gyroscope, health sensors)
- Privacy manifest (`PrivacyInfo.xcprivacy`) declared API reasons vs. actual usage

**Key details:**
- Marked ASR (App Store Review) and NR (Notarization Review) -- applies to both distribution channels
- The "entertainment purposes" disclaimer is explicitly rejected as a defense
- Anonymous calling/messaging apps are categorically rejected

---

### §1.1.7 Harmful Concepts Capitalizing on Events

**Requirement:** No harmful concepts that capitalize or seek to profit on recent or current events such as violent conflicts, terrorist attacks, and epidemics. No spam.

**Triggers rejection if:**
- App monetizes or trivializes tragedies, disasters, or crises
- App exploits current events for profit in a tasteless manner
- App is fundamentally spam with no meaningful functionality

**What to check:**
- App Store metadata and marketing copy for references to recent tragedies or crises
- In-app purchase structure -- check if monetization is tied to real-world events
- Core value proposition -- does the app provide genuine utility or is it exploitative?
- Submission timing relative to current events (e.g., apps rushed out during a disaster)

**Key details:**
- Legitimate news, charity, or relief apps related to current events are acceptable
- The line is between genuinely helpful apps and those seeking to profit from tragedy

---

## §1.2 User-Generated Content

**Requirement:** Apps with user-generated content (UGC) or social networking services must include ALL FOUR of the following mechanisms:

1. **Content filtering** -- a method for filtering objectionable material from being posted
2. **Reporting mechanism** -- a way to report offensive content, with timely responses to concerns
3. **User blocking** -- the ability to block abusive users from the service
4. **Published contact info** -- published developer contact information so users can easily reach you

**Triggers rejection if:**
- Any one of the four required mechanisms is missing
- App is used primarily for pornographic content, Chatroulette-style experiences, random/anonymous chat, objectification of real people (e.g., "hot-or-not" voting), physical threats, or bullying
- UGC moderation is clearly inadequate or non-functional

**What to check:**
- Content moderation implementation: look for profanity filters, image classification models, or third-party moderation SDKs (e.g., `AWS Rekognition`, `Google Cloud Vision`, `Hive Moderation`, `OpenAI Moderation API`, `Perspective API`)
- Report flow UI: search for "report", "flag", or "abuse" buttons/actions in view controllers and SwiftUI views
- Block user functionality: check user profile screens and chat interfaces for block/mute actions
- Contact information: verify a support URL, email, or contact form is accessible from within the app and on the App Store listing
- Server-side moderation endpoints (e.g., `/api/report`, `/api/block`, `/api/moderate`)
- Content filtering configuration files or moderation rule sets
- Response time SLAs or moderation queue infrastructure

**Key details:**
- All four mechanisms are mandatory -- missing even one is grounds for rejection
- Apps may be removed without notice if they become primarily used for prohibited content
- Web-based UGC may display incidental NSFW content only if hidden by default and toggled on via the website (not the app)

---

### §1.2.1 Creator Content (ASR & NR)

**Requirement:** Apps featuring content from a community of "creators" must be properly moderated. Creator content is treated as user-generated content and must follow Guideline 1.2 (filtering, reporting, blocking, contact info) and Guideline 3.1.1 (in-app purchase for digital goods).

**Triggers rejection if:**
- Creator content is unmoderated or lacks the §1.2 mechanisms (filtering, reporting, blocking, published contact info)
- Creator experiences change core app features/functionality rather than adding content
- Digital goods/services within creator content bypass §3.1.1 in-app purchase requirements

**What to check:**
- Content moderation pipeline for creator submissions (manual review queue, automated screening, or hybrid)
- Reporting and blocking mechanisms for creator content (per §1.2)
- Published developer contact information accessible from within the app
- IAP enforcement for any digital goods or services offered through creator content (per §3.1.1)
- Creator content boundaries -- verify creator experiences add content within the app's structure rather than altering core native functionality

**Key details:**
- "Creator content" includes video, articles, audio, and casual games
- Creator experiences are treated as UGC by App Review, so all §1.2 requirements also apply
- Creator experiences must not function as independent native apps -- they are content within the host app

---

#### §1.2.1(a) Age Identification and Restriction (ASR & NR)

**Requirement:** Creator apps must provide a way for users to identify content that exceeds the app's age rating and must use an age restriction mechanism based on verified or declared age to limit access by underage users.

**Triggers rejection if:**
- No age identification system for content that exceeds the app's age rating
- No age restriction mechanism (verified or declared) to gate underage access
- Age restriction can be trivially bypassed (e.g., simple yes/no toggle with no enforcement)

**What to check:**
- Age gate or age verification UI: look for date-of-birth entry, age confirmation dialogs, or identity verification SDKs
- Content rating/tagging system for creator-submitted content
- Age-gated content sections with access controls
- Persistent storage of age verification state
- `AppTrackingTransparency` framework usage and age-appropriate handling

**Key details:**
- Marked ASR and NR -- applies to both distribution channels
- The age mechanism must be meaningful -- a simple unchecked toggle is insufficient
- Content ratings for creator content should align with the host app's declared age rating in App Store Connect

---

## §1.3 Kids Category

**Requirement:** Apps in the Kids Category must not include links out of the app, purchasing opportunities, or other distractions to kids unless placed behind a parental gate. Must comply with all applicable children's privacy laws worldwide (COPPA, GDPR Article 8, AADC, etc.). Must not send personally identifiable information or device information to third parties.

**Triggers rejection if:**
- App contains external links accessible to children (not behind a parental gate)
- In-app purchases or purchasing prompts are accessible without a parental gate
- App collects or transmits PII or device identifiers from children to third parties
- Third-party analytics SDK collects IDFA or identifiable child information
- Behavioral or targeted advertising is present
- Third-party advertising lacks documented human review of ad creatives for age appropriateness
- App leaves the Kids Category in an update but was previously expected to follow these rules

**What to check:**
- All `UIApplication.shared.open` calls, `SFSafariViewController`, `WKWebView` loads, and `Link` views in SwiftUI -- each must be behind a parental gate if accessible by children
- Parental gate implementation: must require adult-level knowledge or action (e.g., math problem, text instruction, multi-step gesture) -- simple taps or swipes do not qualify
- `StoreKit` integration: verify all purchase flows are behind a parental gate
- Third-party SDK inventory: audit `Podfile`, `Package.swift`, `build.gradle` for analytics and advertising SDKs
- Privacy manifest (`PrivacyInfo.xcprivacy`): check declared data collection categories and purposes
- `AppTrackingTransparency` usage: Kids Category apps should not request tracking authorization
- `AdSupport` framework / IDFA access: must not be present or must be disabled
- Network traffic endpoints: look for calls to analytics services (Firebase Analytics, Mixpanel, Amplitude, etc.) and verify they are configured to not collect child data
- Ad SDKs: if present, verify they are configured for contextual-only (no behavioral/targeted) ads and have publicly documented Kids Category policies with human review of creatives
- `NSUserDefaults`, `Keychain`, or local storage for PII that might be synced externally
- Info.plist for `NSAppTransportSecurityException` domains -- flag any that point to ad networks or analytics

**Key details:**
- Privacy requirements are extremely strict -- this is one of the most common rejection reasons for Kids apps
- Contextual advertising is permitted in limited cases only if the ad service has documented Kids Category policies and human-reviews creatives
- Third-party analytics is only permitted if the service does not collect or transmit IDFA or identifiable child information (including name, DOB, email, location, device info)
- Once an app is in the Kids Category, subsequent updates must continue to meet these requirements even if the category is deselected
- Parental gates must be non-trivial -- Apple provides specific guidance on acceptable gate designs

---

## §1.4 Physical Harm (ASR & NR)

Apps that behave in a way that risks physical harm may be rejected.

### §1.4.1 Medical Apps (ASR & NR)

**Requirement:** Medical apps that could provide inaccurate data or that could be used for diagnosing or treating patients are subject to greater scrutiny. Apps must clearly disclose data and methodology to support accuracy claims for health measurements. Apps should remind users to consult a doctor.

**Triggers rejection if:**
- App claims health measurement capabilities using only device sensors that cannot support them (e.g., blood pressure, blood glucose, body temperature, blood oxygen, x-rays via phone sensors alone)
- Accuracy claims lack disclosed methodology or supporting data
- App does not remind users to consult a medical professional
- App has received regulatory clearance but does not submit documentation

**What to check:**
- `HealthKit` integration and data types being read/written
- Health-related claims in App Store description, screenshots, and in-app UI
- Sensor usage: `CoreMotion`, camera-based measurements, `AVCaptureSession` for health readings
- Disclaimers and doctor consultation reminders in the UI flow (especially before displaying results)
- Regulatory clearance documentation: FDA 510(k), CE marking, or equivalent
- Accuracy methodology disclosures in the app or supporting website
- Info.plist usage descriptions for health-related permissions (`NSHealthShareUsageDescription`, `NSHealthUpdateUsageDescription`)

**Key details:**
- Marked ASR and NR
- Claiming sensor-only measurement of blood pressure, blood glucose, body temperature, blood oxygen, or x-ray capability is explicitly prohibited
- Regulatory clearance documentation should be submitted with the app if applicable
- The "consult a doctor" reminder is expected in the user flow, not just buried in terms of service

---

### §1.4.2 Drug Dosage Calculators (ASR & NR)

**Requirement:** Drug dosage calculators must originate from an approved entity: drug manufacturer, hospital, university, health insurance company, pharmacy, or equivalent. Must be approved by FDA or an international counterpart.

**Triggers rejection if:**
- App calculates drug dosages and is not from an approved entity type
- No evidence of FDA or equivalent regulatory approval
- Developer account does not correspond to an approved entity

**What to check:**
- Developer account name and organization -- verify it maps to an approved entity type
- App Store description and "about" section for entity credentials
- Drug dosage calculation logic and data sources
- Regulatory approval documentation submitted with the app
- Links to institutional backing or accreditation

**Key details:**
- Marked ASR and NR
- Apple requires confidence the app will be maintained long-term given the patient safety implications
- Independent developers or generic companies cannot publish dosage calculators

---

### §1.4.3 Substance Encouragement

**Requirement:** Apps must not encourage consumption of tobacco, vape products, illegal drugs, or excessive amounts of alcohol. Must not facilitate sale of controlled substances (except licensed pharmacies and legal cannabis dispensaries) or tobacco.

**Triggers rejection if:**
- App glorifies, promotes, or encourages substance use
- App encourages minors to consume any restricted substance
- App facilitates sale of controlled substances from an unlicensed entity
- App facilitates sale of tobacco products

**What to check:**
- App content and imagery for glorification of substance use
- E-commerce or marketplace features: check product catalogs for controlled substances or tobacco
- Age verification gates for substance-related content or purchases
- Developer entity type for substance sales apps (must be licensed pharmacy or legal dispensary)
- Marketing copy and App Store metadata for promotional substance language

**Key details:**
- Licensed pharmacies and legally operating cannabis dispensaries are exempt from the sales prohibition
- The "encourages minors" threshold is lower -- any substance content accessible to minors without age gating is risky
- Tobacco sales facilitation is categorically prohibited regardless of entity type

---

### §1.4.4 DUI Checkpoints (ASR & NR)

**Requirement:** DUI checkpoint information may only be displayed if published by law enforcement agencies. App must never encourage drunk driving or reckless behavior such as excessive speed.

**Triggers rejection if:**
- App displays DUI checkpoint data from non-law-enforcement sources
- App encourages drunk driving or reckless driving behavior
- App helps users evade law enforcement checkpoints

**What to check:**
- Data sources for checkpoint information -- verify they are official law enforcement feeds
- App purpose and framing: is checkpoint data presented for safety or for evasion?
- Speed-related features: speedometers, speed alerts, or speed challenge mechanics
- Map annotations or location data related to checkpoints or speed traps

**Key details:**
- Marked ASR and NR
- The intent behind the feature matters -- safety-oriented framing is expected
- "Excessive speed" encouragement is also covered, not just DUI-specific content

---

### §1.4.5 Risky Physical Activities (ASR & NR)

**Requirement:** Apps should not urge customers to participate in activities (bets, challenges, etc.) or use their devices in a way that risks physical harm to themselves or others.

**Triggers rejection if:**
- App encourages dangerous physical challenges or stunts
- App gamifies risky real-world activities (e.g., dare-based challenges)
- App encourages using the device in physically dangerous ways (e.g., while driving, while running near traffic)

**What to check:**
- Challenge or dare mechanics in the app's feature set
- Gamification of real-world physical activities with risk elements
- Motion-based gameplay that requires movement in potentially unsafe environments
- Social sharing of dangerous challenge completions
- Betting mechanics tied to physical activities

**Key details:**
- Marked ASR and NR
- Covers both physical activities and dangerous device usage patterns
- The "challenges" reference specifically calls out viral social media-style challenge trends

---

## §1.5 Developer Information (ASR & NR)

**Requirement:** Apps and their Support URL must include an easy way to contact the developer. Contact information must be accurate and current. Wallet passes must include valid issuer contact information and be signed with a dedicated certificate assigned to the brand or trademark owner.

**Triggers rejection if:**
- No contact method is accessible from within the app or its Support URL
- Contact information is outdated, invalid, or unreachable
- Wallet passes lack valid issuer contact information
- Wallet passes are not signed with a certificate belonging to the brand/trademark owner

**What to check:**
- Support URL configured in App Store Connect -- verify it loads and contains contact info
- In-app settings or help/about screens for contact email, phone, or support form
- `PKPass` (Wallet pass) files: inspect `organizationName`, `teamIdentifier`, and contact fields in `pass.json`
- Wallet pass signing certificate -- verify it is assigned to the correct brand
- App Store Connect metadata: developer contact fields are filled and valid
- Test that contact email addresses are deliverable (valid format, real domain)

**Key details:**
- Marked ASR and NR
- Particularly important for education apps used in classrooms
- Failure to provide accurate contact info may violate laws in some jurisdictions beyond just the App Store rules
- Wallet pass requirements are specific: certificate must belong to the brand or trademark owner of the pass

---

## §1.6 Data Security (ASR & NR)

**Requirement:** Apps must implement appropriate security measures to ensure proper handling of user information. Must prevent unauthorized use, disclosure, or access to personal data.

**Triggers rejection if:**
- App transmits sensitive user data without encryption
- App stores personal data insecurely (plaintext passwords, unencrypted local storage)
- App lacks appropriate access controls for user data
- App has known security vulnerabilities in its data handling

**What to check:**
- Network layer: verify all API calls use HTTPS (`NSAppTransportSecurity` settings in Info.plist -- flag any `NSAllowsArbitraryLoads = YES`)
- Authentication implementation: check for secure token storage (Keychain vs. UserDefaults)
- Local data storage: look for sensitive data in plaintext in `NSUserDefaults`, plist files, SQLite databases, or Core Data stores
- Encryption usage: check for `CryptoKit`, `CommonCrypto`, or `Security.framework` usage for sensitive data
- Privacy manifest (`PrivacyInfo.xcprivacy`): verify declared data types and purposes
- Keychain usage for credentials and tokens (`SecItemAdd`, `SecItemCopyMatching`)
- SSL pinning implementation for sensitive API endpoints
- Third-party SDK data handling: audit dependencies for known data security issues
- Server-side: check for API keys, secrets, or credentials hardcoded in the app binary

**Key details:**
- Marked ASR and NR
- Cross-references Guideline 5.1 (Privacy) for detailed data handling requirements
- "Appropriate" is judged relative to the sensitivity of the data collected
- Hardcoded secrets in the binary are a common finding -- these are trivially extractable

---

## §1.7 Reporting Criminal Activity

**Requirement:** Apps for reporting alleged criminal activity must involve local law enforcement. Can only be offered in countries or regions where such law enforcement involvement is actively sought.

**Triggers rejection if:**
- App enables reporting criminal activity without involving local law enforcement
- App is available in countries/regions where law enforcement has not sought this involvement
- App enables vigilante-style crime reporting without official channels

**What to check:**
- App's core purpose: does it involve crime reporting or tip submission?
- Law enforcement partnerships or integrations documented in the app or its metadata
- Geographic availability settings in App Store Connect -- verify the app is only available in appropriate regions
- Data flow: verify reports are routed to official law enforcement channels, not just stored privately
- Terms of service and privacy policy for law enforcement data sharing disclosures

**Key details:**
- The "actively sought" requirement means the local law enforcement agency must have requested or endorsed citizen reporting in that jurisdiction
- This is a narrow category -- most apps will not trigger this guideline
- Apps that encourage citizens to act as vigilantes or bypass official channels will be rejected
