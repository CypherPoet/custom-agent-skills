# Section 3: Business

> Source: https://developer.apple.com/app-store/review/guidelines/
> Last synced: 2026-03-27

If the business model is not obvious, it must be explained in metadata and App Review notes. Expensive apps with irrationally high prices will be rejected. Manipulation of reviews, chart rankings, or use of paid/incentivized/fake feedback may result in expulsion from the Apple Developer Program.

---

## 3.1 Payments

---

### 3.1.1 In-App Purchase

**Requirement:** All unlocking of features, functionality, subscriptions, in-game currencies, game levels, premium content, or full-version upgrades must use In-App Purchase (IAP). Apps may not use alternative unlock mechanisms.

**Triggers rejection if:**
- App unlocks digital content or features via license keys, augmented reality markers, QR codes, cryptocurrencies, cryptocurrency wallets, or any non-IAP mechanism
- In-app purchase credits or currencies have an expiration date
- Restorable IAP items lack a restore mechanism
- Loot boxes or randomized item purchases do not disclose odds prior to purchase
- Digital gift cards/certificates/vouchers redeemable for digital goods are sold outside IAP
- Free trial periods do not use Non-Consumable IAP at Price Tier 0 or do not follow "XX-day Trial" naming convention
- NFT ownership unlocks features or functionality within the app
- Apps outside the US storefront include external purchase links/buttons for NFT collections without IAP

**What to check:**
- `StoreKit` / `StoreKit2` imports in source files
- Usage of `SKProduct`, `SKPaymentQueue`, `Product`, `Transaction` (StoreKit 2)
- `.storekit` StoreKit configuration files for product definitions
- Any use of `SKPaymentQueue.default().restoreCompletedTransactions()` or `AppStore.sync()` (restore mechanism)
- Strings or UI referencing "unlock", "premium", "pro", "full version" -- verify these route through IAP
- Code patterns for license key validation, QR code scanning, or crypto wallet integration that gate content
- Search for "loot box", "mystery", "random", "chance", "odds", "probability" in UI strings and verify disclosure exists
- Gift card or voucher flows -- digital must use IAP; physical gift cards mailed to customers may use other payment
- Trial period product names -- must match "XX-day Trial" format exactly
- NFT-related code -- verify NFT ownership does not gate features (viewing own NFTs is fine)

**Key details:**
- Tipping digital content providers via IAP currencies is explicitly allowed
- Gifting IAP-eligible items to others is allowed; refunds go to original purchaser only, no exchanges
- Mac App Store apps may host plug-ins/extensions enabled with non-App Store mechanisms
- Credits and in-game currencies purchased via IAP must never expire
- Non-subscription free trials: use Non-Consumable IAP at Price Tier 0, clearly identify trial duration, what becomes inaccessible after trial ends, and any downstream charges
- NFT minting, listing, and transferring via IAP is allowed; NFT browsing of others' collections is allowed; external purchase links for NFTs only permitted on US storefront

---

### 3.1.1(a) Link to Other Purchase Methods

**Requirement:** Developers may apply for specific entitlements to link to an external website for purchasing digital content. The US storefront has broader permissions and does not require entitlements for external links.

**Triggers rejection if:**
- App uses a StoreKit External Purchase Link Entitlement outside the entitled storefronts/regions
- App uses Music Streaming Services Entitlement outside the entitled storefronts/regions
- App engages in misleading marketing, scams, or fraud in connection with entitlements
- Non-US storefront app includes external purchase buttons/links without the required entitlement (except US storefront)

**What to check:**
- Entitlements file (`.entitlements`) for `com.apple.developer.storekit.external-purchase-link` or similar external purchase entitlements
- Entitlements for music streaming services
- UI strings, buttons, or links directing users to external purchase websites
- Marketing language around external purchase options -- verify it is informational, not misleading
- Check which storefronts the app targets and whether the entitlement is valid in those regions

**Key details:**
- **StoreKit External Purchase Link Entitlements:** Apps in specific regions may include a link to the developer's own website informing users of other purchase methods. The link may mention lower prices. Limited to iOS/iPadOS in specific storefronts.
- **Music Streaming Services Entitlements:** Music streaming apps in specific regions can link to their website for purchasing digital music. May also collect email addresses to send purchase links. Limited to iOS/iPadOS in specific storefronts.
- **US storefront exception:** Apps on the US storefront do not need entitlements for external purchase buttons, links, or calls to action. These restrictions do not apply to the US storefront.
- Misleading marketing related to entitlements results in removal from App Store and possible developer program expulsion.

---

### 3.1.2 Subscriptions

**Requirement:** Auto-renewable subscriptions must provide ongoing value, last at least 7 days, and work across all of the user's devices where the app is available.

**Triggers rejection if:**
- Subscription does not provide ongoing value to the customer
- Subscription period is shorter than 7 days
- Subscription is not available across all user devices
- App is a scam, uses bait-and-switch tactics, or tricks users into subscribing under false pretenses
- Existing users lose primary functionality they already paid for when the app switches to a subscription model
- Subscription information is unclear or does not comply with Schedule 2 of the Apple Developer Program License Agreement

**What to check:**
- `.storekit` configuration files for subscription product definitions and durations
- `SKProduct.subscriptionPeriod` or `Product.SubscriptionInfo` usage
- Subscription-related UI: paywall screens, trial offers, pricing display
- Clarity of subscription descriptions -- what user gets, cost, duration, renewal terms
- Upgrade/downgrade flows -- verify users cannot accidentally hold multiple active subscriptions for the same content
- Free trial configuration via App Store Connect
- Any pattern where subscription gates content that was previously purchased as a one-time unlock

**Key details:**
- Appropriate subscription examples: new game levels, episodic content, multiplayer support, apps with consistent substantive updates, large/continually updated media collections, SaaS, cloud support
- Subscriptions may be offered alongside a la carte purchases
- Subscriptions may include consumable credits, gems, currencies and may offer discounted consumable goods
- Streaming game service subscriptions may be shared across third-party apps but games must be downloaded directly from the App Store
- Users must not be required to perform additional tasks (posting on social media, uploading contacts, checking in) to access what they paid for
- When transitioning to subscription model, existing paid users must keep their previously-purchased functionality
- Free trial periods are allowed via App Store Connect subscription offers
- Cellular carrier apps may include auto-renewable subscriptions in bundles with cellular data plans, with prior Apple approval

#### 3.1.2(b) Upgrades and Downgrades

**Requirement:** Users must have a seamless upgrade/downgrade experience and must not inadvertently subscribe to multiple variations of the same thing.

**What to check:**
- Subscription group configuration -- all tiers of the same offering should be in the same subscription group
- UI flows for changing subscription tiers
- Logic that might allow a user to hold multiple active subscriptions for overlapping content

#### 3.1.2(c) Subscription Information

**Requirement:** Before asking a customer to subscribe, clearly describe what they get for the price: number of issues, amount of storage, type of access, etc. Must comply with Schedule 2 of the Apple Developer Program License Agreement.

**What to check:**
- Paywall/subscription screen UI text for completeness and clarity
- Whether pricing, renewal period, and cancellation terms are displayed before the purchase button
- Compliance with Schedule 2 requirements (linked terms)

---

### 3.1.3 Other Purchase Methods (IAP Exemptions)

**Requirement:** Specific categories of apps may use purchase methods other than IAP. However, these apps cannot encourage users to use non-IAP purchasing within the app (except on US storefront and as permitted by 3.1.1(a) and 3.1.3(a)). Developers may communicate about alternative purchase methods outside the app.

**Triggers rejection if:**
- App claims an exemption category but does not actually qualify
- App in an exempt category encourages in-app use of non-IAP purchasing (outside US storefront) without proper entitlements
- App relies on an exemption for content/services that do not fit the exemption criteria

**What to check:**
- App category and business model to determine if any exemption applies
- UI strings, buttons, or prompts that direct users to external payment within the app
- Whether the app's content/service genuinely fits one of the exemption categories below

#### 3.1.3(a) "Reader" Apps

**Requirement:** Apps that allow access to previously purchased content -- specifically magazines, newspapers, books, audio, music, and video -- may use external purchase methods. May offer free-tier account creation and account management for existing customers.

**What to check:**
- Content type -- must be one of: magazines, newspapers, books, audio, music, video
- Whether the app creates/sells new content within the app (not allowed under reader exemption) vs. accessing previously purchased content
- External Link Account Entitlement in entitlements file if linking to a website for account creation/management
- US storefront apps do not need the entitlement for external links

**Key details:**
- Reader app developers may apply for the External Link Account Entitlement for informational links to their website
- US storefront apps do not require this entitlement

#### 3.1.3(b) Multiplatform Services

**Requirement:** Apps operating across multiple platforms may allow users to access content, subscriptions, or features acquired on other platforms or the developer's website, including consumable items in multiplatform games, provided those items are also available as IAP within the app.

**What to check:**
- Whether the app offers IAP for the same items that can be acquired externally
- Cross-platform content syncing logic
- Consumable items in multiplatform games -- must also be available via IAP

#### 3.1.3(c) Enterprise Services

**Requirement:** Apps sold directly to organizations for their employees or students (e.g., professional databases, classroom management tools) may allow enterprise users to access previously purchased content or subscriptions. Consumer, single-user, or family sales must use IAP.

**What to check:**
- Distribution model -- is this genuinely enterprise-only (B2B)?
- Whether any consumer/individual purchase paths exist (those must use IAP)
- MDM or enterprise distribution configuration

#### 3.1.3(d) Person-to-Person Services

**Requirement:** Apps enabling purchase of real-time person-to-person services between two individuals (tutoring, medical consultations, real estate tours, fitness training) may use non-IAP payment methods. One-to-few and one-to-many real-time services must use IAP.

**What to check:**
- Whether the service is truly 1:1 real-time between two individuals
- Group sessions, classes, or one-to-many broadcasts -- these do NOT qualify and must use IAP
- Payment integration (Stripe, PayPal, Apple Pay, etc.) for person-to-person services

**Key details:**
- The exemption is specifically for real-time, 1:1 services
- One-to-few (small group) and one-to-many (broadcast/class) do NOT qualify

#### 3.1.3(e) Goods and Services Outside the App

**Requirement:** Apps enabling purchase of physical goods or services consumed outside the app must use payment methods other than IAP (e.g., Apple Pay, credit card entry).

**What to check:**
- Whether the goods/services are physical or consumed outside the app
- Payment integration for physical goods (should NOT use IAP)
- Any digital goods or services mixed in (those still require IAP)

#### 3.1.3(f) Free Stand-alone Apps

**Requirement:** Free apps acting as a stand-alone companion to a paid web-based tool (VoIP, cloud storage, email services, web hosting) do not need IAP, provided there is no purchasing inside the app and no calls to action for purchase outside the app.

**What to check:**
- That the app is completely free with no IAP
- No purchase prompts, upgrade buttons, or calls to action for external purchase exist within the app
- The app functions as a companion to a web-based tool

**Key details:**
- Must be truly free with zero purchasing inside the app
- Must not direct users to purchase outside the app either

#### 3.1.3(g) Advertising Management Apps

**Requirement:** Apps solely for managing advertising campaigns across media types (TV, outdoor, websites, apps) do not need IAP. These apps must not display the ads themselves. Purchases for content experienced within the app (like social media "boosts") must use IAP.

**What to check:**
- Whether the app is purely for campaign management, not ad display
- Any in-app content purchases (e.g., boosts, promoted posts) -- these require IAP
- Whether the app displays the advertisements (not allowed under this exemption)

---

### 3.1.4 Hardware-Specific Content

**Requirement:** In limited circumstances, apps may unlock functionality without IAP when features depend on specific hardware (e.g., astronomy app synced with a telescope). Optional hardware accessories may unlock functionality without IAP provided an IAP option is also available.

**Triggers rejection if:**
- App requires purchase of unrelated products to unlock functionality
- App requires advertising or marketing activities to unlock functionality
- Optional hardware unlock exists without a corresponding IAP alternative

**What to check:**
- Hardware detection code (Bluetooth, accessory frameworks, ExternalAccessory, CoreBluetooth)
- Whether features locked behind hardware also have an IAP unlock path
- Any requirement to purchase unrelated products for app functionality

**Key details:**
- Hardware-dependent features (e.g., telescope sync) may unlock without IAP
- Optional hardware (e.g., toys) may unlock features BUT an IAP alternative must also exist
- Must not require purchase of unrelated products or engagement in advertising/marketing to unlock functionality

---

### 3.1.5 Cryptocurrencies

**Requirement:** Cryptocurrency-related apps have specific restrictions based on their function.

**Triggers rejection if:**
- Wallet app is submitted by an individual developer account (must be organization)
- App mines cryptocurrency on-device
- Exchange app operates in jurisdictions where it lacks proper licensing
- ICO/crypto-securities app is not from an established financial institution
- App rewards users with cryptocurrency for completing tasks (downloading apps, posting on social media, etc.)

**What to check:**
- Developer account type (organization vs. individual) for wallet apps
- Any on-device mining code (CPU/GPU intensive operations, mining libraries)
- Licensing documentation for exchange functionality
- Developer credentials for ICO/futures trading apps
- Task-completion reward flows that pay out in cryptocurrency

#### 3.1.5(i) Wallets

**Requirement:** Apps may facilitate virtual currency storage, but must be offered by developers enrolled as an organization.

**What to check:**
- Developer enrollment type in the Apple Developer account -- must be organization, not individual
- Wallet functionality (key storage, balance display, send/receive)

#### 3.1.5(ii) Mining

**Requirement:** Apps may not mine cryptocurrency on-device. Cloud-based (off-device) mining is permitted.

**What to check:**
- CPU/GPU-intensive background processes
- Mining library imports or mining pool connections
- Whether any mining processing happens on the device vs. being delegated to cloud/servers

#### 3.1.5(iii) Exchanges

**Requirement:** Exchange apps must be offered only in countries/regions where the app has appropriate licensing and permissions.

**What to check:**
- Storefront/region availability settings
- Licensing documentation referenced in app metadata or review notes
- Regional compliance for each supported jurisdiction

#### 3.1.5(iv) Initial Coin Offerings

**Requirement:** ICO apps, crypto futures trading, and crypto-securities trading must come from established banks, securities firms, futures commission merchants (FCM), or other approved financial institutions and must comply with all applicable law.

**What to check:**
- Developer identity -- is it an established financial institution?
- Type of crypto trading offered (spot vs. futures/securities/ICOs)
- Compliance documentation

#### 3.1.5(v) No Rewards for Task Completion

**Requirement:** Cryptocurrency apps may not offer currency for completing tasks such as downloading other apps, encouraging other users to download, posting to social networks, watching ads, or mining.

**What to check:**
- Reward/incentive systems that pay out cryptocurrency
- "Earn crypto" flows tied to app actions, social sharing, ad viewing, or referrals
- Gamification mechanics that reward crypto for engagement tasks

---

## 3.2 Other Business Model Issues

---

### 3.2.1 Acceptable

#### 3.2.1(i) Display Own Apps

**Requirement:** Apps may display their own apps for purchase or promotion within the app, provided the app is not merely a catalog of the developer's apps.

**What to check:**
- Whether the app has substantial functionality beyond promoting the developer's other apps
- Cross-promotion sections or "More Apps" screens

#### 3.2.1(ii) Third-Party App Collections

**Requirement:** Apps may display or recommend collections of third-party apps designed for a specific approved need (health management, aviation, accessibility). Must provide robust editorial content so it does not appear to be a mere storefront.

**What to check:**
- Whether the app has substantial editorial content (reviews, guides, recommendations)
- Whether the collection serves a specific approved need vs. being a general app catalog
- Distinction from a storefront or app-store-like interface (see 3.2.2(i))

#### 3.2.1(iii) Rental Content

**Requirement:** Apps may disable access to specific approved rental content (films, TV, music, books) after the rental period expires. All other items and services may not expire.

**What to check:**
- Expiration logic for content -- only rental-category content (films, TV, music, books) may expire
- Any non-rental digital content with expiration dates (not allowed)

#### 3.2.1(iv) Wallet Passes

**Requirement:** Wallet passes can be used for payments, offers, or identification (movie tickets, coupons, VIP credentials). Other uses may result in rejection and revocation of Wallet credentials.

**What to check:**
- PassKit/Wallet integration and pass types
- Whether pass usage fits approved categories (payment, offers, identification)

#### 3.2.1(v) Insurance Apps

**Requirement:** Insurance apps must be free, legally compliant in distributed regions, and cannot use in-app purchase.

**What to check:**
- App price (must be free)
- Absence of IAP
- Regional legal compliance for insurance products

#### 3.2.1(vi) Nonprofit Fundraising

**Requirement:** Approved nonprofits may fundraise directly within their own apps or third-party apps. Must adhere to all App Review Guidelines, offer Apple Pay support, disclose fund usage, comply with local/federal laws, and ensure tax receipts are available. Nonprofit platforms connecting donors to other nonprofits must ensure every listed nonprofit has gone through the approval process.

**What to check:**
- Apple's approved nonprofit status
- Apple Pay integration for donations
- Fund usage disclosure in the app
- Tax receipt availability
- If a platform: verification that all listed nonprofits are Apple-approved

#### 3.2.1(vii) Person-to-Person Monetary Gifts

**Requirement:** Apps may enable individual users to give monetary gifts to other individuals without IAP, provided the gift is completely optional and 100% of funds go to the receiver. Gifts connected to receiving digital content or services must use IAP.

**What to check:**
- Whether gifts are truly optional (no pressure or gating)
- Whether 100% of the gift amount goes to the receiver (no platform cut)
- Whether any digital content or services are tied to the gift (must use IAP if so)

**Key details:**
- The platform must not take a cut of person-to-person gifts
- If the gift unlocks or is associated with digital content/services at any point, IAP is required

#### 3.2.1(viii) Financial Trading/Investing

**Requirement:** Financial trading, investing, or money management apps must be submitted by the financial institution performing such services and must have necessary licensing and permissions in all locations where available.

**What to check:**
- Developer identity -- is it the financial institution itself?
- Licensing and regulatory compliance documentation
- Regional availability vs. licensing coverage

---

### 3.2.2 Unacceptable

#### 3.2.2(i) Third-Party App Store Interfaces

**Requirement:** Apps must not create an interface for displaying third-party apps, extensions, or plug-ins similar to the App Store or as a general-interest collection.

**Triggers rejection if:**
- App presents a browsable catalog of third-party apps resembling an app store
- App functions as a general-interest app discovery platform
- App displays third-party extensions or plug-ins in a storefront-like manner

**What to check:**
- UI patterns that resemble app store browsing (search, categories, install buttons for third-party apps)
- Lists of third-party apps without specific editorial focus
- Any "install" or "get" buttons for third-party content

#### 3.2.2(iii) Ad Impression/Click Inflation

**Requirement:** Apps must not artificially increase ad impressions or click-throughs. Apps designed predominantly for ad display are not allowed.

**Triggers rejection if:**
- App inflates ad impressions or click-throughs artificially
- App is designed predominantly to display advertisements with minimal other functionality

**What to check:**
- Ad SDK integration and ad placement density
- Whether the app has substantial functionality beyond displaying ads
- Auto-clicking or impression inflation logic
- Ad-to-content ratio

#### 3.2.2(iv) Unauthorized Charity Fund Collection

**Requirement:** Apps may not collect funds for charities or fundraisers within the app unless they are an approved nonprofit (per 3.2.1(vi)). Non-approved fundraising apps must be free and may only collect funds outside the app (e.g., via Safari or SMS).

**Triggers rejection if:**
- App collects charitable donations in-app without approved nonprofit status
- Fundraising app is not free on the App Store

**What to check:**
- In-app donation/fundraising flows
- Approved nonprofit status
- App pricing (fundraising apps must be free)

#### 3.2.2(v) Arbitrary Location/Carrier Restrictions

**Requirement:** Apps must not arbitrarily restrict who may use the app by location or carrier.

**Triggers rejection if:**
- App restricts access based on geographic location without a legitimate business reason
- App restricts access based on cellular carrier

**What to check:**
- Location-based gating logic
- Carrier detection and restriction code
- Whether restrictions have legitimate regulatory or business justification

#### 3.2.2(vii) Manipulating User Visibility/Status

**Requirement:** Apps must not artificially manipulate a user's visibility, status, or rank on other services unless permitted by that service's Terms and Conditions.

**Triggers rejection if:**
- App manipulates followers, likes, rankings, or visibility on third-party platforms
- App offers services to artificially boost social media metrics

**What to check:**
- Features that interact with third-party platform APIs to modify user metrics
- "Boost followers", "get likes", "increase rank" functionality

#### 3.2.2(viii) Binary Options, CFDs, FOREX

**Requirement:** Binary options trading apps are not permitted on the App Store. CFD and FOREX trading apps must be properly licensed in all jurisdictions where available.

**Triggers rejection if:**
- App facilitates binary options trading (outright ban)
- CFD or FOREX app operates without proper licensing in served jurisdictions

**What to check:**
- Trading instrument types offered (binary options are banned entirely)
- CFD/FOREX/derivatives trading features
- Licensing documentation for each jurisdiction
- App Store storefront availability vs. licensing coverage

#### 3.2.2(ix) Personal Loan APR Requirements

**Requirement:** Personal loan apps must clearly and conspicuously disclose all loan terms including maximum APR and payment due date. Maximum APR must not exceed 36% (including costs and fees). Repayment period must be greater than 60 days.

**Triggers rejection if:**
- Loan terms are not clearly disclosed
- APR exceeds 36% (including all costs and fees)
- Loan requires full repayment in 60 days or less
- APR or payment due date is not prominently displayed

**What to check:**
- Loan term disclosure UI -- APR, fees, repayment schedule must be clear and conspicuous
- Maximum APR calculations (must include all costs and fees, capped at 36%)
- Minimum repayment period (must exceed 60 days)
- Loan application flows and terms presentation

#### 3.2.2(x) Forced Ratings, Reviews, or Downloads

**Requirement:** Apps must not force users to rate the app, review the app, download other apps, or perform other store-related actions as a condition for accessing functionality, content, or use of the app.

**Triggers rejection if:**
- App gates features behind app rating or review requirements
- App requires downloading other apps to access content
- Access to functionality is conditional on store-related actions

**What to check:**
- Rating/review prompts that block functionality until completed
- Mandatory app downloads as prerequisite for features
- Any UI flow where content or features are locked behind store-related actions
- `SKStoreReviewController` usage -- verify it is not used as a gate
- Distinction: apps may incentivize in-app actions (completing a level, watching an ad) -- just not store-related actions
