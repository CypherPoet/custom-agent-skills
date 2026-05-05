# Common App Store Rejection Patterns

> Source: https://developer.apple.com/app-store/review/guidelines/
> Last synced: 2026-05-04
>
> This checklist covers the most frequent rejection reasons. Load the corresponding
> section reference file for full details on any flagged item.

## P0 — Blockers (Almost Certain Rejection)

- [ ] **2.1 App Completeness** — App crashes, has placeholder text, broken links, or non-functional features
- [ ] **3.1.1 In-App Purchase Required** — Digital content/features unlocked without IAP (license keys, external payment for digital goods)
- [ ] **5.1.1(i) Privacy Policy Missing** — No privacy policy linked in App Store Connect AND in-app
- [ ] **5.1.1(v) Account Deletion Missing** — Account creation exists but no account deletion option
- [ ] **2.3.1 Hidden Features** — Undisclosed features, hidden switches, or dormant code paths
- [ ] **2.5.1 Private API Usage** — Using non-public Apple APIs

## P1 — High Risk (Frequent Rejections)

- [ ] **4.8 Sign in with Apple** — App offers third-party sign-in (Google, Facebook, etc.) but does not also offer Sign in with Apple
- [ ] **1.2 User Generated Content** — UGC exists without ALL four requirements: content reporting, blocking, hidden from flagged content, published contact info
- [ ] **3.1.2(c) Subscription Pricing/Terms** — Subscription price, duration, renewal terms, or cancellation instructions are unclear or missing from the purchase flow
- [ ] **5.1.2(i) App Tracking Transparency** — App collects data used for tracking across apps/websites but does not present the ATT prompt before tracking begins
- [ ] **2.5.4 Background Mode Misuse** — App declares background modes (audio, location, VoIP, etc.) it does not actively use, or uses them for unrelated purposes
- [ ] **1.3 Kids Category Violations** — App in the Kids Category collects data, includes ads not certified for children, or links out to external content without a gate
- [ ] **5.1.1(ii) Privacy Usage Descriptions** — Missing or vague NSUsageDescription strings for camera, microphone, location, photos, contacts, or other protected resources
- [ ] **2.5.2 Deprecated APIs/SDKs** — App built with deprecated or outdated SDK version that Apple has flagged for removal
- [ ] **3.1.1 External Purchase Links** — App links to external websites for purchasing digital content or subscriptions outside IAP without an approved entitlement

## P2 — Medium Risk (Common Delays)

- [ ] **2.3.3 Inaccurate Screenshots** — Screenshots or previews show features, UI, or devices that don't match the actual app experience
- [ ] **2.3.6 Incorrect Age Rating** — Age rating does not accurately reflect the app's content (violence, language, mature themes, gambling, etc.)
- [ ] **5.1.1(iii) Over-Requesting Permissions** — App requests access to data or capabilities it does not clearly need for its core functionality
- [ ] **4.2.6 Template/Cookie-Cutter Apps** — App is generated from a commercial template or app-builder with no meaningful unique functionality
- [ ] **4.2 Minimum Functionality** — App is too simple (single web view wrapper, basic timer, or trivial utility) with no compelling feature set
- [ ] **4.5.4 Push Notification Misuse** — Push notifications used for advertising, promotions, or spam rather than meaningful user-relevant content
- [ ] **3.1.1 Loot Box Odds** — App includes loot boxes or randomized virtual items for purchase but does not disclose the odds of receiving each item
- [ ] **2.5.5 IPv6 Compatibility** — App does not work on IPv6-only networks; hard-coded IPv4 addresses or IPv4-only APIs cause connectivity failures
- [ ] **2.3.10 Misleading Version Updates** — Repeatedly submitting updates with no meaningful changes to manipulate charts or search ranking

## P3 — Low Risk (Polish Issues / Soft Rejections)

- [ ] **2.3.12 Generic "What's New" Text** — Release notes say "Bug fixes and improvements" with no specifics; reviewers may request meaningful descriptions
- [ ] **2.1 Reviewer Notes Insufficient** — Demo credentials missing or broken, no instructions for features that require special setup or hardware
- [ ] **2.3 Metadata Quality** — App name, subtitle, or description contains inaccurate claims, excessive formatting, or irrelevant information
- [ ] **2.3.7 Keyword Stuffing** — Keywords field contains competitor names, irrelevant terms, or duplicates of the app name and category
- [ ] **2.3.13 In-App Event Metadata** — In-app event title, description, or media is misleading, too generic, or does not accurately represent the event content
- [ ] **4.0 Design — General Polish** — Minor UI issues like truncated text, misaligned elements, or non-Retina assets that don't rise to a hard rejection but trigger reviewer feedback
- [ ] **2.3.8 Pricing Mismatch** — App price tier or IAP pricing differs from what is described in metadata or marketing materials
