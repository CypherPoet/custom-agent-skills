---
name: app-store-connect-submission
description: >
  Step-by-step playbook for actually submitting an Apple-platform app (iOS/iPadOS,
  and the shared flow for macOS/tvOS/watchOS/visionOS) to the App Store through App
  Store Connect — the operational mechanics and console navigation, NOT review-guideline
  compliance. Use this whenever someone is taking an app from "built" to "Submitted for
  Review": creating the app record; the agreements/tax/banking + Small Business Program
  prerequisites; registering an explicit App ID; filling App Information vs the version
  ("1.0 Prepare for Submission") page; App Privacy / "Data Not Collected" + where the
  Privacy Policy URL now lives; pricing & availability incl. the Apple-Silicon-Mac toggle;
  creating in-app purchases and ATTACHING them to the version; building and delivering the
  archive via Xcode (Organizer / Distribute / Transporter) OR Xcode Cloud; and setting up
  sandbox testing. ALSO use it to debug App Store Connect / submission errors and traps —
  "Invalid bundle … error 90474" / UIRequiresFullScreen, "Apple Account is incorrect" on a
  sandbox tester, "Manage Workflows is greyed out" in Xcode Cloud, an empty sandbox paywall,
  a build that archives but never reaches the App Store, the DEVELOPMENT_TEAM signing gap, or
  a missing Privacy Policy URL field. Trigger even when the user only says "how do I submit to
  the App Store", "ship my iOS app", "set up Xcode Cloud", "sandbox test my purchase", "attach
  my IAP", or names one of those errors — don't wait for them to say "App Store Connect".
  For App Review compliance / rejection-risk audits / keyword & metadata optimization, use
  apple-app-store-best-practices instead; for exact screenshot dimensions, apple-app-store-screenshots;
  for writing IAP/StoreKit code, the storekit skill.
---

# App Store Connect Submission

The operational playbook for getting an Apple-platform app from **built** to
**Submitted for Review**. It covers the console navigation, the order of operations,
build delivery, sandbox testing, and the UI traps that aren't in Apple's happy-path docs.

> ⚠️ **Apple's consoles drift.** Screen names, field locations, and option labels change
> without notice. Every screen-specific claim here is dated **(as of 2026-06)**. When the
> screen in front of you disagrees with this skill, **trust the screen** — and ideally
> update the skill. Treat the steps as a map, not a contract.

## What this skill owns — and what it hands off

This skill is the *mechanics* of submitting. It deliberately defers three adjacent concerns
to sibling skills so each stays sharp:

- **Will it pass review? Is the listing optimized?** → `apple-app-store-best-practices`
  (guideline §1–§5 risk audit, rejection patterns, ASO, keyword/metadata strategy).
- **Exact screenshot dimensions / app-preview specs?** → `apple-app-store-screenshots`.
- **Writing the in-app-purchase / restore *code*?** → `storekit` (StoreKit 2).

If a request is really about one of those, say so and point there instead of half-answering here.

## The two consoles (know which owns what)

You bounce between two web apps, and most "I can't find that setting" confusion comes from
being in the wrong one:

- **[Apple Developer portal](https://developer.apple.com/account)** — membership, **Identifiers**
  (App IDs), **Certificates**, and the **Small Business Program**.
- **[App Store Connect](https://appstoreconnect.apple.com)** — the **app record**, pricing,
  in-app purchases, builds, and the **submission** itself.

## Submission flow — the order to do it in

Work top to bottom. Each step has detail in a reference file (see the table at the bottom).

1. **Prerequisites** (Developer portal + ASC → Business). Sign the **Paid Apps Agreement**
   and finish **tax + banking** — *required even for a free app if it has a paid IAP, or the
   IAP won't load in sandbox or review*. Enroll in the **Small Business Program** if eligible.
   Register an **explicit App ID** (not a wildcard) under **Identifiers** — *not* Certificates.
2. **Create the app record** (ASC → Apps → ＋ → New App). SKU and Bundle ID choices here are
   permanent; the bundle ID locks after the first build.
3. **App Information** (app-level / "General"): name, subtitle, category, content rights, age rating, and the
   **EU Digital Services Act trader status** — any app earning money in the EU (paid app or paid IAP) must
   verify trader details or it's pulled from the EU App Store.
4. **App Privacy** (left sidebar → Trust & Safety): answer the data-collection question, set the
   **Privacy Policy URL** (Apple moved this field here from App Information), then **Publish** —
   it stays a draft until you do.
5. **Pricing & availability**: price + tax category + territories. Decide the **iPhone & iPad
   Apps on Apple-Silicon Macs** toggle (and Vision Pro) — it defaults *on*; uncheck for v1 if
   the app is untested there.
6. **Create each in-app purchase** → fill every field (incl. availability + the review
   screenshot) → status **Ready to Submit**.
7. **Build & deliver** the archive — local Xcode **or** Xcode Cloud. → `references/build-and-delivery.md`
8. **Version page** ("1.0 Prepare for Submission" — the *version-level* page, not App Information):
   description, keywords, promo text, support URL, screenshots, copyright; **select the build**
   once it finishes processing.
9. **App Review Information**: contact, sign-in details (or "not required"), and notes that tell
   the reviewer how to reach gated features / trigger purchases.
10. ⚠️ **Attach each first-time IAP to the version.** This is the #1 missed step — a brand-new
    app's first IAP can't be reviewed standalone; it must ride *with* the version, or you risk a
    Guideline 2.1 rejection.
11. *(Recommended, not required)* **Sandbox-test the purchase + restore** on a real device.
    → `references/testing-purchases.md`
12. Pick a **release option** (Manual gives you go-live control) → **Add for Review → Submit**.

Steps 1–6, 8–10, 12 are walked field-by-field in `references/walkthrough.md`.

## Glossary (the terms that trip people up)

- **The two consoles** — Developer portal vs App Store Connect (above).
- **App-level vs version-level** — *app-level* settings (the **App Information** page) are shared
  across every release (name, subtitle, category); *version-level* settings (the **"1.0 Prepare
  for Submission"** page) are per-release (description, screenshots, build, review info).
- **"Version page"** — shorthand for the **"1.0 Prepare for Submission"** page in the left sidebar
  under the app. If you can't find Description/Keywords/Screenshots, you're on App Information — go here.
- **Bundle ID vs App ID vs Apple ID** — the **Bundle ID** (`com.you.YourApp`) identifies the app in
  your Xcode target; the **App ID** is the matching entry you register in the portal's *Identifiers*
  tab; the **Apple ID** is a read-only number ASC assigns the app record. Three different things.
- **Identifiers vs Certificates** — both live under *Certificates, Identifiers & Profiles* in the
  portal. **Identifiers** is where you register the App ID. **Certificates** is signing — which
  Xcode's *Automatically manage signing* handles for you; don't hand-create a distribution cert.
- **Sandbox tester** — a fake Apple Account (ASC → Users and Access → Sandbox) for testing purchases
  against Apple's sandbox servers with no real charge. **Not** a real Apple ID; it can't be used in
  the normal Settings sign-in.
- **`.storekit` configuration** — a local file that **simulates** the store inside Xcode (no servers)
  — the *opposite* of Sandbox. Toggled in the Run scheme's *StoreKit Configuration*.
- **Ready to Submit** (IAP status) — the IAP has every required field (price, availability,
  localization, review screenshot) and can be attached to a version. Before that it reads
  *Missing Metadata*.
- **Distribution Preparation** (Xcode Cloud Archive action) — the setting that decides where a build
  can go; the value **"App Store Connect"** is the one that makes a build submittable (Apple's docs
  sometimes call the same option "TestFlight and App Store").

## Build & deliver: two paths

Both land the build in App Store Connect; steps 8–12 are identical afterward. Full setup for each is
in `references/build-and-delivery.md`.

- **Local archive (Xcode)** — Release config, *Any iOS Device (arm64)*, Product → Archive → in the
  Organizer **Distribute App → the App Store Connect tile (recommended settings) → Distribute**
  (Xcode 15+ one-click; the old Upload / options / signing wizard is under **Custom**). ⚠️ Requires a
  signing **Team** on every target; if `DEVELOPMENT_TEAM` isn't pinned, the archive won't sign.
- **Xcode Cloud** — a workflow builds and delivers in the cloud with **cloud-managed signing** (no
  local cert/Team setup). Two things must be right or no submittable build appears: the **Archive**
  action's **Distribution Preparation = "App Store Connect"**, and it must build your **release
  branch**. Xcode Cloud builds the **git remote**, not your local files — commit and push first.

Prefer to drive uploads and the rest of the flow from the CLI / CI (or an agent) **without fastlane**? An
App Store Connect **API key** does it: `xcrun altool` for uploads, and a small JWT + REST call for
build-status polling, metadata, and submission. → `references/api-automation.md`

## Testing purchases — with or without the real pipeline

Detail in `references/testing-purchases.md`. The key distinction:

- **Local `.storekit` config** (simulator, no device, no servers) verifies your *app's* purchase
  UX/logic. It always "works" regardless of your ASC setup, so it can't catch pipeline problems —
  but it's the fast, device-free way to see the flow, and automated StoreKit tests already cover it.
- **Sandbox** (real device, real Apple servers) is the *only* pre-submission check of the live
  pipeline: Paid Apps Agreement, product propagation, a real transaction, restore via `AppStore.sync()`.
  It's **recommended, not a submission gate** — if you skip it, at minimum confirm the **Paid Apps
  Agreement is Active**, which is the highest-probability failure.

## Troubleshooting — common App Store Connect / submission errors

Symptom → cause → fix. Section refs point at the fuller explanation.

| Symptom | Cause | Fix |
|---------|-------|-----|
| Upload fails — **"Invalid bundle… error 90474"** | A portrait-only **universal** (iPhone+iPad) app doesn't satisfy iPad multitasking (which needs all four orientations) | Set `INFOPLIST_KEY_UIRequiresFullScreen = YES` — opts out of iPad multitasking and keeps portrait. (Or genuinely support all four iPad orientations.) → walkthrough |
| Sandbox sign-in: **"Apple Account is incorrect"** | A sandbox tester is **not** a real Apple ID; entered in the wrong field | Sign in at the **purchase sheet** when you tap Buy, or only at Settings → Developer → Sandbox Apple Account — never the main App Store login. → testing-purchases |
| New sandbox-tester email **rejected (red)** | iCloud plus-aliases (`you+x@icloud.com`) resolve back to your real Apple ID | Use a **non-iCloud** address (e.g. a Gmail plus-alias) — Apple treats it as a new email. → testing-purchases |
| Sandbox paywall **empty / "product unavailable"** | Paid Apps Agreement inactive · ASC metadata still propagating · scheme still on the local `.storekit` file | Confirm **agreement Active**; wait (propagation can take hours after *Ready to Submit*); set the Run scheme's StoreKit Configuration → **None**. → testing-purchases |
| Xcode Cloud: **"Manage Workflows" greyed out** / no workflow appears | Source-access grant or Xcode Cloud terms not finished; Xcode's menu is stale | Finish the GitHub/source grant + accept Xcode Cloud terms (Account Holder); the workflow shows under **ASC → Xcode Cloud** even when Xcode's menu lags. → build-and-delivery |
| Xcode Cloud build **archives but never reaches the App Store** | Archive action set to *None* / "TestFlight (Internal Testing Only)" | Set the Archive action's **Distribution Preparation = "App Store Connect"**. → build-and-delivery |
| Local archive **won't sign** | `DEVELOPMENT_TEAM` not pinned on the targets | Select your **Team** per target in Signing & Capabilities; for Xcode Cloud, commit + **push** the team to the build branch. → build-and-delivery |
| Can't find the **Description / Keywords / Screenshots** box | They're *version-level*, not on App Information | Open **"1.0 Prepare for Submission"** in the left sidebar. → walkthrough |
| **Privacy Policy URL** field missing on App Information | Apple moved it | Set it under **Trust & Safety → App Privacy**, then **Publish**. → walkthrough |
| App **not available in the EU** after release | EU **DSA trader status** not declared/verified | App Information → complete **trader status** (Get Started); EU storefronts hide the app until verification clears. → walkthrough |
| IAP stuck at **"Missing Metadata"** | Price, availability, localization, or review screenshot not all set | Fill every field; availability defaults to all territories — just confirm it. → walkthrough |
| **"Add for Review" greyed out** on the version | A required field is still empty | Scroll the version page — ASC flags every incomplete field inline; usual culprits are screenshots, support URL, or the build not yet selected. → walkthrough |

## Reference files

Load the one you need; don't read all of them upfront.

| File | Load when |
|------|-----------|
| `references/walkthrough.md` | Doing the field-by-field ASC flow (prerequisites → app record → App Information → App Privacy → pricing → IAP → version page → review info → submit) |
| `references/build-and-delivery.md` | Building and delivering the archive — local Xcode archive **or** Xcode Cloud workflow setup, signing, and delivery |
| `references/testing-purchases.md` | Testing in-app purchases — the local `.storekit` simulator path and the real **Sandbox** path (testers, scheme config, purchase-time sign-in) |
| `references/api-automation.md` | Driving submission from the CLI / CI / an agent **without fastlane** — the App Store Connect **API key** + `.env` pattern, `xcrun altool` uploads, and JWT + REST for build status / metadata / submit |
