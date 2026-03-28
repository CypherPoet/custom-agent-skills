---
name: apple-appstore-reviewer
description: >
  Audit an iOS, macOS, tvOS, watchOS, or visionOS app for App Store rejection risks
  against the official Apple App Store Review Guidelines. Produces a prioritized risk
  register with specific guideline citations (e.g., violates §3.1.1), evidence from the
  codebase, and concrete remediation steps. Use this skill before submitting to App Review,
  after receiving a rejection, when adding IAP/subscriptions/auth/UGC/data collection to an
  app, or whenever someone asks about App Store compliance, review guidelines, or rejection
  risks. Also use when the user mentions "App Store", "App Review", "rejection", "submission",
  "guideline", or is working on an Apple platform app and wants a compliance check. Even for
  quick questions like "do I need Sign in with Apple?" or "will this pass review?", consult
  this skill.
  Last synced with Apple guidelines: 2026-03-27
---

# Apple App Store Reviewer

Systematically audit an app against all 5 sections of the [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), producing findings with exact section citations and actionable remediation.

## Reference Files

This skill includes reference files in `references/` containing the full guidelines organized by section. Load them selectively based on the app's features — don't load everything upfront.

| File | When to load |
|------|-------------|
| `common-rejection-patterns.md` | **Always load first** — triage checklist of top rejection reasons |
| `section-1-safety.md` | App has UGC, targets kids, has health/medical features, or handles sensitive content |
| `section-2-performance.md` | Always load for full audits — covers completeness, metadata, software requirements |
| `section-3-business.md` | App has any monetization: IAP, subscriptions, physical goods, ads, crypto |
| `section-4-design.md` | App has login/auth, extensions, push notifications, Apple Music, or mini-apps |
| `section-5-legal.md` | App collects any user data, uses location, has health features, or targets kids |
| `reviewer-notes-template.md` | When generating the Draft App Review Notes deliverable |

## Audit Workflow

### Phase 1: App Reconnaissance

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

### Phase 2: Technical Compliance

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

### Phase 3: Business Model Compliance

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

### Phase 4: Safety and Content

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

### Phase 5: Design and Metadata

Check against §4 (Design) and §2.3 (Metadata).

**App completeness (§2.1):**
- No placeholder text ("Lorem ipsum", "TODO", "Coming soon")
- All URLs functional and not pointing to localhost/staging
- Demo account credentials available for review team
- All backend services live and accessible

**Metadata accuracy (§2.3):**
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

### Phase 6: Legal Compliance

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

## Output Format

Produce these 6 deliverables:

### 1. Executive Summary

5-10 bullets covering: app purpose, top risks, submission verdict.

**Verdict:** `READY` / `CONDITIONAL` (minor fixes needed) / `NOT READY` (blockers exist)

### 2. Risk Register

| Priority | Guideline | Area | Finding | Evidence | Remediation | Effort | Confidence |
|----------|-----------|------|---------|----------|-------------|--------|------------|
| P0 | §3.1.1 | Payments | Digital content unlocked via external payment | `PurchaseManager.swift:47` — Stripe checkout for premium features | Migrate to StoreKit IAP | L | HIGH |

- **Priority:** P0 (blocker), P1 (high risk), P2 (medium), P3 (low/polish)
- **Guideline:** Exact section number from the Review Guidelines
- **Area:** Privacy, Payments, Content, Design, Metadata, Technical, Legal
- **Evidence:** File path, function name, configuration entry, or metadata field
- **Confidence:** HIGH (clear violation), MEDIUM (likely violation, interpretation-dependent), LOW (possible issue, reviewer-dependent)

### 3. Detailed Findings

Group findings by area. For each finding:
- The specific guideline section and what it requires
- What the app currently does that may violate it
- Exact evidence (file paths, code snippets, config entries)
- Recommended fix with implementation guidance

### 4. Reviewer Experience Checklist

Walk through the app as a reviewer would:
- [ ] Install and launch — does it load without crashes?
- [ ] First permission prompt — is the purpose string clear?
- [ ] Account creation/login — is Sign in with Apple offered?
- [ ] Core feature walkthrough — do all features work?
- [ ] IAP flows — can purchases be completed in sandbox?
- [ ] External links — do they open correctly?
- [ ] Edge cases — what happens with no network, denied permissions, empty states?

### 5. Draft App Review Notes

Use the template from `references/reviewer-notes-template.md`. Fill in based on what was found during the audit: demo credentials, feature access steps, permission explanations, IAP testing instructions.

### 6. Guideline Coverage Summary

| Section | Applicable | Evaluated | Findings |
|---------|-----------|-----------|----------|
| §1 Safety | Yes/No | Yes/No | Count |
| §2 Performance | Yes/No | Yes/No | Count |
| §3 Business | Yes/No | Yes/No | Count |
| §4 Design | Yes/No | Yes/No | Count |
| §5 Legal | Yes/No | Yes/No | Count |

## Severity Definitions

**P0 — Blocker** (almost certain rejection):
- Missing privacy policy (§5.1.1(i))
- Digital content without IAP (§3.1.1)
- No account deletion when account creation exists (§5.1.1(v))
- App crashes or has placeholder content (§2.1)
- Private API usage (§2.5.1)

**P1 — High Risk** (likely rejection):
- Third-party login without Sign in with Apple (§4.8)
- UGC without all 4 moderation requirements (§1.2)
- Vague permission purpose strings (§5.1.1(ii))
- Unclear subscription pricing (§3.1.2(c))
- Missing ATT prompt when tracking (§5.1.2(i))

**P2 — Medium Risk** (may cause rejection depending on reviewer):
- Screenshots don't reflect current app (§2.3.3)
- Over-requesting permissions (§5.1.1(iii))
- Questionable age rating (§2.3.6)
- Unused background modes declared (§2.5.4)

**P3 — Low Risk / Polish** (unlikely to block but worth fixing):
- Generic "What's New" text (§2.3.12)
- Reviewer notes could be more helpful (§2.1)
- Metadata could be improved (§2.3)

## Adaptive Depth

Scale the audit based on app complexity:

**Quick audit** (simple utility, no accounts/payments):
Phase 1 + Phase 2 + Phase 6, plus metadata spot-check. Load only `common-rejection-patterns.md`.

**Standard audit** (app with accounts, payments, or data collection):
All 6 phases. Load relevant section references based on Phase 1 findings.

**Deep audit** (UGC, kids, health data, complex subscriptions, multiple platforms):
All 6 phases with full reference loading. Flag ambiguous cases for human review. Cross-reference between sections for compound risks (e.g., kids + UGC triggers both §1.2 and §5.1.4).

## Development-Time Reference

For targeted questions during development (not full audits), map the task to guideline sections:

| Task | Load | Check |
|------|------|-------|
| Adding IAP/subscriptions | `section-3-business.md` | §3.1.1, §3.1.2 |
| Adding user authentication | `section-4-design.md`, `section-5-legal.md` | §4.8, §5.1.1(v) |
| Adding data collection | `section-5-legal.md` | §5.1.1, §5.1.2 |
| Adding UGC features | `section-1-safety.md` | §1.2 (all 4 requirements) |
| Targeting Kids Category | `section-1-safety.md`, `section-5-legal.md` | §1.3, §5.1.4 |
| Adding push notifications | `section-4-design.md` | §4.5.4 |
| Adding health features | `section-5-legal.md` | §5.1.3 |
| Adding crypto features | `section-3-business.md` | §3.1.5 |
| Adding extensions | `section-4-design.md` | §4.4 |
| Adding Apple Music | `section-4-design.md` | §4.5.2 |

## Post-Rejection Workflow

When an app has been rejected:

1. **Parse the rejection message** — Extract the cited guideline section(s) and the reviewer's description
2. **Load the corresponding reference file** — Look up the exact requirement for the cited section
3. **Scan the codebase** for the specific issue the reviewer flagged
4. **Check for related issues** — Reviewers often flag one thing but the same root cause may trigger additional violations on resubmission (e.g., fixing one privacy issue but missing another)
5. **Produce a targeted remediation plan** with the same Risk Register format, focused on the rejection reason plus any related risks

The goal is to fix the rejection AND prevent a follow-up rejection for something the reviewer will notice next.
