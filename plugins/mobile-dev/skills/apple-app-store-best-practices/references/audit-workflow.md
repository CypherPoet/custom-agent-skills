# App Store Audit Workflow

The phase-by-phase compliance audit for the [apple-app-store-best-practices](../SKILL.md) skill. Load this when running a standard or deep audit; Phase 1 (reconnaissance) decides which `section-*.md` references to pull in.

## Table of Contents

| Section | Covers |
|---|---|
| [Phase 1: App Reconnaissance](#phase-1-app-reconnaissance) | Platform targets, user flows, monetization, authentication, data, content, and audience |
| [Phase 2: Technical Compliance](#phase-2-technical-compliance) | Crashes, completeness, hardware use, software requirements, and beta or test behavior |
| [Phase 3: Business Model Compliance](#phase-3-business-model-compliance) | Payments, subscriptions, purchase methods, ads, and platform-specific monetization rules |
| [Phase 4: Safety and Content](#phase-4-safety-and-content) | Objectionable content, user-generated content, children, physical harm, and developer conduct |
| [Phase 5: Design and Metadata](#phase-5-design-and-metadata) | Minimum functionality, copied apps, login services, extensions, and truthful store metadata |
| [Phase 6: Legal Compliance](#phase-6-legal-compliance) | Privacy, intellectual property, gambling, financial services, VPN, and regulatory compliance |
| [Post-Rejection Workflow](#post-rejection-workflow) | Evidence collection, root-cause classification, remediation, and appeal decisions after rejection |

## Phase 1: App Reconnaissance

Before checking any guidelines, understand what the app does. Scan the project to identify:

- **Platform targets** — Check Xcode project for iOS, macOS, tvOS, watchOS, visionOS targets. This determines which platform-specific rules apply (e.g., §2.4.5 for Mac App Store, §2.4.3 for tvOS Siri Remote).
- **App purpose** — What does it do? What are the top 5 user flows?
- **Monetization model** — Free, freemium, subscription, paid, ads? Look for StoreKit imports, product configurations, ad SDKs.
- **Authentication** — Does it have sign-in? Third-party/social login? Look for ASAuthorizationAppleIDProvider, Firebase Auth, OAuth flows.
- **Data collection** — What data does it collect? Check NSUsageDescription strings, PrivacyInfo.xcprivacy, analytics SDKs, tracking frameworks.
- **User-generated content** — Can users post, share, or communicate? Look for text input with submission, image upload, chat features.
- **Target audience** — Is it for kids? Check age rating, Kids Category entitlements, educational frameworks.
- **Content type** — Does it display content that could be objectionable, medical, financial?

Based on what you find, load the relevant reference files. Use this decision tree:

- Any monetization → load `section-3-business.md`
- Any data collection → load `section-5-legal.md`
- Any UGC or sensitive content → load `section-1-safety.md`
- Any auth, extensions, or push → load `section-4-design.md`
- Full audit → load `section-2-performance.md` too

## Phase 2: Technical Compliance

Check the codebase against §2 (Performance) and §2.5 (Software Requirements).

**Info.plist audit:**
- All required keys present for declared capabilities
- Every `NS*UsageDescription` string is specific and meaningful (not generic like "This app needs access")
- Bundle identifier, version, and build number are set
- Required device capabilities match actual usage

**Entitlements audit:**
- Every declared entitlement is actually used in code
- No entitlements missing for features that need them (push notifications, HealthKit, HomeKit, etc.)
- App Groups configured if using shared data between app and extensions

**Privacy manifest (PrivacyInfo.xcprivacy):**
- File exists in the main app bundle
- NSPrivacyTracking accurately reflects tracking behavior
- NSPrivacyTrackingDomains lists all tracking domains
- NSPrivacyCollectedDataTypes matches actual collection
- NSPrivacyAccessedAPITypes declares all required-reason APIs (UserDefaults, file timestamp, disk space, etc.)
- Third-party SDK privacy manifests present

**API and framework checks:**
- No private API usage (§2.5.1) — grep for known private framework imports
- IPv6 compatibility (§2.5.5) — no hardcoded IPv4 addresses, uses high-level networking APIs
- WebKit for web browsing (§2.5.6) — any in-app browser uses WKWebView
- Background modes (§2.5.4) — each declared mode (`UIBackgroundModes`) has corresponding code that genuinely uses it
- No code downloading or dynamic execution of unsigned code (§2.5.2)

**Platform-specific:**
- macOS: Check sandboxing entitlements, no root escalation, no auto-launch (§2.4.5)
- tvOS: Verify UI works with Siri Remote (§2.4.3)
- iPhone: Should also run on iPad (§2.4.1)

## Phase 3: Business Model Compliance

Check monetization against §3 (Business). This is where most rejections happen for apps with payments.

**In-App Purchase enforcement (§3.1.1):**
- Digital content, features, or subscriptions MUST use Apple's IAP — look for alternative unlock mechanisms (license keys, QR codes, external payment URLs for digital goods, crypto payments)
- If IAP exists: verify restore mechanism, check that credits/currencies don't expire
- Loot boxes: odds must be disclosed before purchase
- Trial periods: Price Tier 0 with "XX-day Trial" naming

**Subscriptions (§3.1.2):**
- Provides ongoing value (not one-time content behind a subscription paywall)
- Minimum 7-day subscription period
- Available across all user devices
- Clear pricing and terms disclosed before purchase
- No manipulative subscription flows (dark patterns, unclear cancellation)

**Exemptions (§3.1.3):**
- Check if the app qualifies for any IAP exemption: Reader app, multiplatform service, enterprise, person-to-person real-time service, physical goods/services, free standalone
- If claiming an exemption, verify it actually applies

**External purchase links (§3.1.1(a)):**
- If using StoreKit External Purchase Link Entitlement, verify correct entitlement and region compliance

## Phase 4: Safety and Content

Check against §1 (Safety). Critical for apps with UGC, kids audience, or sensitive content.

**User-generated content (§1.2):**
If the app allows any form of user content (posts, comments, images, chat, profiles), ALL FOUR requirements must be met:
1. Content filtering for objectionable material
2. Mechanism to report offensive content (with timely response)
3. Ability to block abusive users
4. Published developer contact information

Missing even one is a rejection. Look for: content moderation SDKs, report buttons in UI, block user functionality, contact info in settings or about screens.

**Kids Category (§1.3):**
If targeting the Kids Category or children under 13:
- No links out of the app without a parental gate
- No purchasing without a parental gate
- No third-party analytics that collect device identifiers
- No behavioral/targeted advertising (only limited contextual ads)
- No personal information sent to third parties
- Must comply with COPPA and GDPR for children

**Content review:**
- Check for potentially objectionable content patterns (§1.1)
- Medical/health claims need validation from appropriate authorities (§1.4)
- Data security measures in place for user information (§1.6)

## Phase 5: Design and Metadata

Check against §4 (Design) and §2.3 (Metadata).

**App completeness (§2.1):**
- No placeholder text ("Lorem ipsum", "TODO", "Coming soon")
- All URLs functional and not pointing to localhost/staging
- Demo account credentials available for review team
- All backend services live and accessible

**Metadata accuracy (§2.3):**

Character limits (verify all fields are within bounds):

| Field | Max Length |
|-------|-----------|
| App Name (Title) | 30 characters |
| Subtitle | 30 characters |
| Promotional Text | 170 characters |
| Description | 4,000 characters |
| Keywords | 100 characters (comma-separated) |
| What's New | 4,000 characters |

- App description matches actual functionality
- Screenshots show the actual app in use (not marketing mockups)
- Age rating answers are accurate
- Keywords are relevant (no competitor names, no irrelevant terms)
- "What's New" describes actual changes

**Login services (§4.8):**
If the app has third-party or social login (Google, Facebook, X, etc.), it MUST also offer Sign in with Apple — unless it falls under an exception:
- App uses only its own first-party account system
- App is for a specific third-party service (e.g., Gmail app)
- Education, enterprise, or government ID requirement

Look for: ASAuthorizationAppleIDProvider, AuthenticationServices framework import. If third-party login exists without Sign in with Apple, flag as P1.

**Minimum functionality (§4.2):**
- App provides value beyond what a website could offer
- Not just a wrapper around a WebView loading a URL
- Not primarily marketing material

**Push notifications (§4.5.4):**
- Not required for core functionality
- No sensitive information in notification payloads
- Promotional notifications require opt-in
- Opt-out mechanism available

## Phase 6: Legal Compliance

Check against §5 (Legal). Privacy is the most scrutinized area.

**Privacy policy (§5.1.1(i)):**
- Linked in App Store Connect metadata
- Also accessible within the app (usually in Settings or About)
- Covers: what data is collected, how it's used, third-party sharing, retention, deletion

**Permissions and consent (§5.1.1(ii)):**
- Every permission request has a clear, specific purpose string
- App functions even if user denies optional permissions
- No gating paid features on data sharing consent
- Easy to withdraw consent

**Account deletion (§5.1.1(v)):**
If the app allows account creation, it MUST offer account deletion. Check for:
- Delete account option accessible from within the app
- Deletion process is clear and not buried
- If account management is web-based, deep link to deletion page

**App Tracking Transparency (§5.1.2(i)):**
If the app tracks users across apps/websites:
- ATTrackingManager prompt implemented
- Tracking only occurs after user grants permission
- NSPrivacyTracking set to true in privacy manifest
- All tracking domains listed

**Data minimization (§5.1.1(iii)):**
- Only requests data relevant to app functionality
- Uses system pickers (photo picker, contact picker) instead of requesting full library access where possible

**Health data (§5.1.3):**
- Never used for advertising or marketing
- Not stored in iCloud
- Research requires informed consent and ethics board approval

**Kids privacy (§5.1.4):**
- COPPA and GDPR compliance for children's data
- No third-party analytics or advertising in kids apps

## Post-Rejection Workflow

When an app has been rejected:

1. **Parse the rejection message** — Extract the cited guideline section(s) and the reviewer's description
2. **Load the corresponding reference file** — Look up the exact requirement for the cited section
3. **Scan the codebase** for the specific issue the reviewer flagged
4. **Check for related issues** — Reviewers often flag one thing but the same root cause may trigger additional violations on resubmission (e.g., fixing one privacy issue but missing another)
5. **Produce a targeted remediation plan** with the same Risk Register format, focused on the rejection reason plus any related risks

The goal is to fix the rejection AND prevent a follow-up rejection for something the reviewer will notice next.
