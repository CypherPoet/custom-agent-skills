# Field-by-field submission walkthrough

The end-to-end App Store Connect flow, in order. *As of 2026-06; trust the screen when it
disagrees.* Examples use placeholders like `com.you.YourApp` — substitute the real values.

## Contents

- [0. Before you open App Store Connect](#0-before-you-open-app-store-connect)
- [1. Create the app record](#1-create-the-app-record)
- [2. App Information (app-level)](#2-app-information-app-level)
- [3. App Privacy](#3-app-privacy)
- [4. Pricing & availability](#4-pricing--availability)
- [5. In-app purchases](#5-in-app-purchases)
- [6. Version page metadata](#6-version-page-metadata)
- [7. App Review Information](#7-app-review-information)
- [8. Attach the IAP, pick a release option, submit](#8-attach-the-iap-pick-a-release-option-submit)

---

## 0. Before you open App Store Connect

These live in the **Developer portal** and ASC's **Business** module, and gate everything else.

| Task | Where | Why it matters |
|------|-------|----------------|
| Sign the **Paid Apps Agreement** + finish **tax forms** and **banking** | ASC → Business → Agreements, Tax, and Banking | **Mandatory even for a free app if it has any paid IAP.** Until the agreement is *Active*, the IAP won't load in Sandbox **or** review. This is the single most common pipeline failure. |
| Enroll in the **Small Business Program** (if eligible) | [developer.apple.com/app-store/small-business-program](https://developer.apple.com/app-store/small-business-program/) | 15% (vs 30%) commission while annual proceeds are under the threshold. Takes ~15 days to take effect; enroll early. |
| Register an **explicit App ID** | Developer portal → Certificates, Identifiers & Profiles → **Identifiers** | The New App dialog's Bundle ID dropdown reads from here. Use an **explicit** ID (`com.you.YourApp`), not a wildcard. ⚠️ It's the **Identifiers** sub-tab — *not* the Certificates landing page you may hit first. |

**On the "Register an App ID" page — enable nothing you don't need.** Leave capabilities unchecked
unless the app actually uses them (Push, iCloud, Game Center, Sign in with Apple, Associated Domains,
App Groups…). ⚠️ **In-App Purchase has no checkbox here** — it's auto-enabled on every explicit App ID,
so don't hunt for one. The page **does** require a **Description** (internal-only, never shown to users;
plain alphanumerics + spaces — punctuation or symbols reject it as *"Invalid description"*), and has
**no SKU field** (the SKU belongs to the app record, step 1 — a frequent mix-up). You don't hand-create a
distribution certificate either: Xcode's *Automatically
manage signing* generates the Apple Distribution cert + App Store profile during Archive.

**Project build settings worth verifying (not redoing) before you ship:**
- `ITSAppUsesNonExemptEncryption = NO` (in Info.plist) skips the export-compliance prompt for apps that
  use only OS-provided crypto and make no qualifying network calls.
- A `PrivacyInfo.xcprivacy` manifest with accurate `NSPrivacyTracking` and any required-reason API codes
  (e.g. UserDefaults `CA92.1`). This must **agree** with the App Privacy answers (step 3).
- For a **portrait-only universal (iPhone+iPad)** app: `INFOPLIST_KEY_UIRequiresFullScreen = YES`.
  Without it, upload validation rejects the build with **error 90474** ("must support all four iPad
  orientations for multitasking"). This setting opts out of multitasking and is the exemption.

---

## 1. Create the app record

**ASC → Apps → ＋ (top-left) → New App.** The dialog's fields:

| Field | Notes | Permanent? |
|-------|-------|------------|
| **Platforms** | A universal iPhone+iPad app is the single "iOS" platform. | — |
| **Name** | 2–30 chars. No trademarks you don't own. | Editable until first submit |
| **Primary Language** | — | Changeable later |
| **Bundle ID** | Pick the explicit App ID from the dropdown. | **Locks after the first build** |
| **SKU** | Your private ID, never shown to users (e.g. `MYAPP-IOS-001`). | **Permanent** |
| **User Access** | Full Access is fine for a solo dev. | Changeable |

After **Create**, Apple assigns a read-only numeric **Apple ID** (distinct from the Bundle ID).

> **App-level vs version-level.** *App Information* (left sidebar, "General") is shared across all
> versions. The *version page* ("1.0 Prepare for Submission") holds per-release fields. Knowing which
> is which prevents the most common "where is that field?" confusion.

---

## 2. App Information (app-level)

| Field | Action |
|-------|--------|
| **Subtitle** (≤30, optional) | A short value proposition. |
| **Primary Category** / Subcategories | Pick the best fit (up to two subcategories). |
| **Content Rights** | Declare whether it contains third-party content. |
| **License Agreement** | Leave default → Apple's Standard EULA is your Terms of Use, unless you have your own. |
| **Age Rating** | Run the questionnaire honestly. Apple replaced the old scheme on 2025-07-24 with **4+, 9+, 13+, 16+, 18+**. It now runs ~**7 steps**: In-App Controls + Capabilities (Yes/No: Parental Controls, Age Assurance, Unrestricted Web Access, User-Generated Content, Messaging, Advertising), then frequency-scaled theme sections (Mature Themes · Medical/Wellness · Sexuality · Violence · Chance-Based Activities), ending with the **calculated rating** to confirm. A fixed-price IAP is **not** gambling (no loot boxes / randomized rewards). |

> ⚠️ The **Privacy Policy URL is not on this page anymore** — Apple moved it to **App Privacy** (step 3).

> ⚠️ **EU Digital Services Act — trader status.** App Information includes a **trader status** declaration.
> Any app that earns money in the EU (a paid app **or** a paid IAP) must declare the developer a **trader**
> and complete verification — legal name, address, phone, email, shown **publicly** on the EU product page.
> Use **Get Started**; until it's verified the app is **unavailable across the EU App Store**. Apple's
> requirements here shift — confirm via the page's **Learn More**.

The page carries other sections most apps can skip: **App Encryption Documentation** (nothing to upload once
`ITSAppUsesNonExemptEncryption = NO` is set), plus situational declarations (regulated/medical, government,
and — for apps with a backend — **App Store Server Notifications** / **App-Specific Shared Secret**).

---

## 3. App Privacy

Left sidebar → **Trust & Safety → App Privacy**.

1. **Data collection.** Get Started → answer the "Do you (or partners) collect data?" question. If the
   app truly transmits nothing off-device, answer **"No, we do not collect data from this app"** → the
   **Data Not Collected** label. (Apple defines "collect" as *transmitting off-device*; an Apple-handled
   StoreKit purchase is not developer data collection.)
2. **Privacy Policy URL** (same page, **required even with no collection**): enter a live URL that
   returns 200. If you host it on GitHub Pages or similar, make sure the repo is **public** and Pages is
   **enabled**, or the URL 404s — and the same URL is usually hard-wired into the app's in-app legal link.
3. ⚠️ **Publish.** The answers and URL stay a **draft** until you click **Publish** (top-right). Skip it
   and the privacy details don't go live — submission is blocked.

The in-bundle `PrivacyInfo.xcprivacy` and this questionnaire must **agree**; the manifest does not
auto-fill the questionnaire.

---

## 4. Pricing & availability

Monetization → **Pricing and Availability**.

- **Price** — Add Pricing → choose the tier. A **free app with a paid IAP stays Free here** — the IAP carries
  its own price (step 5); don't price the app itself (a common mix-up). Let Apple **auto-generate** other
  storefronts from the base region; manual regional prices opt out of Apple's FX adjustments.
- **Tax Category** — a **separate taxonomy from the App Store discovery category**, not a mirror of it. Most
  apps take the default **App Store software** (it covers games, utilities, productivity… — there is **no**
  "Games" or "Utilities" tax category); only specific content types differ (e.g. *News publications*, *Books*,
  *Audio-visual streaming*). The IAP inherits it via "Match to parent app".
- **Availability** — all territories is the default; restrict only with reason.
- ⚠️ **iPhone & iPad Apps on Apple-Silicon Macs** — defaults **on**, so a universal iOS build is also
  offered on M-series Macs via the iOS-on-Mac layer. If the app's controls/haptics/purchases are untested
  on Mac, **uncheck it for v1** (App Review covers the Mac variant too, and a broken Mac experience invites
  1-star reviews). Fully reversible later. Same logic for the **Apple Vision Pro** availability toggle.

---

## 5. In-app purchases

Monetization → **In-App Purchases → ＋ → [type]** (Non-Consumable for a permanent unlock; the same field
discipline applies to Consumables and Subscriptions, though subscriptions add a Subscription Group + terms).

| Field | Notes |
|-------|-------|
| **Type** | Non-Consumable for a permanent, restorable one-time unlock. |
| **Reference Name** | Internal only, ≤64 chars. |
| **Product ID** | ≤100 chars, **permanent and never reusable** — type it *exactly*; it must match the string in your StoreKit code. |
| **Price** | Pick the **base** tier; Apple auto-generates **comparable** prices for the other ~175 storefronts (they vary with local currency, price points, and tax — leave the set, don't normalize per country). |
| **Availability** | Click **Set Up Availability** — defaults to all territories → Done. Keep it aligned with the app's availability, or buyers in some regions literally can't purchase. |
| **Family Sharing** | Optional. On lets **one purchase cover the buyer's Family Sharing group** — reasonable goodwill for a one-time unlock, but effectively **one-way** (hard to revoke once buyers rely on it), so decide deliberately. |
| **Display Name / Description** (localized) | Shown to customers. They live under **App Store Localization → Add Localization** (a subsection, *not* top-level fields — a common "where is this?" trap). Description ≤45 chars. |
| **Review Screenshot** | **One** capture of the in-app paywall as the user sees it (name, price, benefits, buy button). Required to review; any normal resolution. (This is *not* the marketing product-page screenshots, nor the optional 1024×1024 IAP promotional image.) |
| **Review Notes** | How to reach the paywall. |

Get the IAP to **Ready to Submit** (it sits at *Missing Metadata* until price + availability + localization
+ review screenshot are all present).

> 🔴 **First-launch trap:** a brand-new app's **first IAP must be submitted *with* the app version** — it
> can't be reviewed standalone. You attach it on the version page (step 8). Only after that first IAP is
> approved can later IAPs ship without a new app version.

---

## 6. Version page metadata

Open **"1.0 Prepare for Submission"** (left sidebar, under the app) — the *version-level* page.

| Field | Notes |
|-------|-------|
| **Description** | ≤4000 chars, plain text. Lead with a one-line value prop; this is what shows before "more". (Not indexed for search — for keyword strategy, defer to `apple-app-store-best-practices`.) |
| **Keywords** | ≤100 chars total, comma-separated, **no spaces after commas**. |
| **Promotional Text** | ≤170 chars, editable without a new version. |
| **Support URL** | Required — a contact/support page. |
| **Marketing URL** | Optional. |
| **Copyright** | Format `YYYY Owner` — **no © symbol** (Apple adds it). A handle/studio name is fine. |
| **Screenshots** | Upload the **largest** size per platform; Apple auto-scales down (one set covers all sizes + localizations; **only the first 3** appear on the install sheets). Required: **6.9″ iPhone (1320×2868)** + **13″ iPad (2064×2752)** for a universal app. ⚠️ The *Previews and Screenshots* block has iPhone / iPad / Watch tabs and may default to showing a smaller **6.5″** slot (1242×2688 / 1284×2778) — use **View All Sizes in Media Manager** to reach the 6.9″ slot. Must show real usage. (Exact specs for other device classes → `apple-app-store-screenshots`.) |
| **Build** | **Select** the processed build (see `build-and-delivery.md`). It won't be selectable until processing finishes. |

> ⚠️ If **"Add for Review" is greyed out**, a required field is still empty — scroll the page; ASC flags
> each incomplete field inline. Usual culprits: screenshots, support URL, or the build not yet selected.

---

## 7. App Review Information

- **Sign-in required:** ⚠️ ASC **defaults this checked** — for a no-login app you must actively **uncheck** it, or it demands a demo username/password the app doesn't have. Otherwise provide a working demo account.
- **Contact:** a real, reachable person — name, phone with country code, **monitored** email. This is
  private (reviewer-only), so it does not need to match any public-facing name.
- **Notes:** tell the reviewer exactly how to reach gated features and trigger purchases (e.g. "the paywall
  is on the main menu and when advancing past the free tier; Restore is on the paywall and in Settings").
- **Export Compliance:** auto-skipped when `ITSAppUsesNonExemptEncryption = NO`.

---

## 8. Attach the IAP, pick a release option, submit

On the version page:

1. **Select the build** (step 6) once it's done processing.
2. ⚠️ **Attach the IAP.** The *In-App Purchases and Subscriptions* section is labeled **"(Optional)"** —
   which it is *not* for a first IAP. Click **Select In-App Purchases or Subscriptions** and add each
   first-time IAP (status **Ready to Submit**). **This is the #1 missed step** — without it the IAP isn't
   reviewed and you risk a Guideline 2.1 rejection.
3. **Version Release** — ASC **defaults to *Automatically release*** (goes live as soon as approved).
   **Manually release** instead gives you go-live control (review timing is unaffected); the third option
   schedules an automatic release "no earlier than" a date you set. (Phased release is updates-only, not
   first launch.)
4. **Add for Review → Submit for Review.**

If ASC blocks the submit, it lists what's incomplete — usually a missing screenshot, the build still
processing, or the IAP not attached.
