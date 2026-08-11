# Technologies — Commerce & Identity

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Technologies pages: Apple Pay, In-app purchase, Wallet, Sign in with Apple, Tap to Pay on iPhone, ID Verifier.

**Contents:** [Apple Pay](#apple-pay) · [In-app purchase](#in-app-purchase) · [Wallet](#wallet) · [Sign in with Apple](#sign-in-with-apple) · [Tap to Pay on iPhone](#tap-to-pay-on-iphone) · [ID Verifier](#id-verifier)

### Apple Pay
*Last changed: 2026-06*

**Purpose:** A secure, easy way to pay for physical goods and services, donations, and subscriptions in apps and any browser, bringing up a payment sheet authorized with Face ID, Touch ID, Optic ID, or Apple Watch.

**Use it when / not when:**
- Use when: the device/browser supports Apple Pay — offer it everywhere it's supported.
- Don't present Apple Pay when: the device doesn't support it.
- Use the Apple Pay mark (not a button) when: showing Apple Pay alongside other payment options as a selected/available method; it doesn't facilitate payment, so never use it as or position it like a button.

**Best practices:**
- Offer Apple Pay on all devices/browsers that support it; hide it where unsupported.
- When you use the APIs to detect an active card in Wallet, you MUST make Apple Pay the primary (not necessarily sole) payment option everywhere you use those APIs. Don't split it into a separate step/flow; consider pre-selecting it.
- Use Apple Pay buttons ONLY to initiate payment or (when appropriate) the Apple Pay setup process — nothing else.
- If you use a custom button to start payment, it must NOT display "Apple Pay" or the Apple Pay logo; instead show the Apple Pay mark graphic or reference Apple Pay in text on the same page.
- Don't hide an Apple Pay button or make it appear unavailable; if it can't be used yet (e.g., size/color unselected), surface the problem gracefully after tap/click.
- Provide a cohesive, branded checkout; avoid opening new pages/windows.
- Present the Apple Pay button first/larger/visually separated when available.
- Accelerate single-item buys with Apple Pay buttons on product detail pages (individual item only, excluding cart contents); accelerate multi-item buys with express checkout (single shipping method + destination).
- Support coupon/promo code entry directly on the payment sheet, especially for express checkout.
- Collect required options (color/size) and optional info (gift messages, delivery instructions) and multiple shipping methods/destinations BEFORE showing the payment sheet — the sheet allows only a single shipping method/destination and no optional-data input.
- Prefer fetching latest contact/shipping/payment info from Apple Pay during checkout.
- Avoid requiring account creation before purchase; offer it on the confirmation page and prepopulate fields.
- Provide a business name after the word *Pay* on the total line, matching the bank-statement name: `Pay [Business_Name]`. If you're an intermediary, identify both: `Pay [End_Merchant_Business_Name (via Your_Business_Name)]`.
- Use line items for additional charges, discounts, pending costs, add-on donations, recurring/future payments (label + cost; recurring may include frequency). Don't itemize products. Keep line items short, ideally one line.
- Disclose possible post-authorization costs with an explanation and a subtotal marked *Amount Pending* (where regulations allow).
- Defer to the payment sheet for progress/loading state; don't add extra spinners.
- Report transaction results in the payment sheet; show an order confirmation / thank-you page. If listing Apple Pay there, show it after the last four digits or as a note (e.g., "1234 (Apple Pay)" or "Paid with Apple Pay").
- Report data-validation problems with custom messages + correct status codes; design validation to ignore irrelevant/infer missing data (e.g., ignore Zip+4 extra digits, accept varied phone formats). Use noun phrases, sentence-style capitalization, no ending punctuation; keep messages ≤128 characters to avoid truncation.
- On interruption (cancellation/timeout), cancel any in-progress payment; people restart via the Apple Pay button.
- Subscriptions: clarify billing frequency/terms before the sheet; use line items to reiterate frequency, discounts, upfront fees, trial amount (including $0), regular amount, and the date regular billing begins; clarify current amount in the total. Only show the sheet on a subscription change when it adds fees (not needed if cost stays same or decreases).
- Donations (approved nonprofits only): use a line item like `Donation $50.00`; offer predefined amounts (e.g., $25, $50, $100) plus an Other Amount option.
- Always use the Apple-provided API to render buttons — never create custom Apple Pay button designs or replicate Apple's. Choose the button type matching your flow.
- Make the Apple Pay button no smaller than other payment buttons; don't make people scroll to it. Side-by-side, place it to the RIGHT of an Add to Cart button; stacked, place it ABOVE.
- Apple Pay mark: use only Apple-provided artwork, adjusting only height (≥ other payment marks); don't change width/corner radius/aspect ratio, add trademark symbols, remove the border, add effects, or flip/rotate/animate; maintain clear space of 1/10 its height.
- Referring to Apple Pay in text: use "Apple Pay" exactly (two words, uppercase A/P, never plural/possessive, never translated, never the Apple logo for "Apple"). Use ® on first body-text mention in the US; omit ® when it's a checkout selection option. Text-only description is allowed only when ALL payment options are text-only; otherwise use the mark graphic.

Canonical implementations: PassKit `PKPaymentAuthorizationController` (iOS, watchOS), `PKPaymentRequest.paymentSummaryItems`, `PKPaymentButtonType` / `PKPaymentButtonStyle` (`.automatic`), `PKPaymentButton.cornerRadius`, `PKDateComponentsRange`, `PKPaymentError`, `PKPaymentAuthorizationViewControllerDelegate`; WatchKit `WKInterfacePaymentButton` (watchOS); web `ApplePaySession.applePayCapabilities`, `ApplePayButtonStyle`.

**Specs:**

Website icon (for payment authorization / Handoff / Wallet subscription flows):

| @2x | @3x |
| --- | --- |
| 60x60 pt (120x120 px @2x) | 60x60 pt (180x180 px @3x) |

Button minimum sizes and margins:

| Button | Minimum width | Minimum height | Minimum margins |
| --- | --- | --- | --- |
| Apple Pay (and Buy / Check Out / Set Up / Subscribe with Apple Pay) | 100pt (100px @1x, 200px @2x) | 30pt (30px @1x, 60px @2x) | 1/10 of the button's height |
| Book with Apple Pay (and Donate with Apple Pay) | 140pt (140px @1x, 280px @2x) | 30pt (30px @1x, 60px @2x) | 1/10 of the button's height |

Button types: Buy, Pay, Check Out, Continue, Book, Donate, Subscribe, Reload, Add Money, Top Up, Order, Rent, Support, Contribute, Tip, plain "Apple Pay" (no call to action / smaller min width), plus a Set Up Apple Pay button (shown in Settings, profile, or interstitial when the device supports Apple Pay but it isn't set up).

Button styles: *automatic* (matches system appearance); *Black* (light backgrounds with sufficient contrast); *White with outline* (light backgrounds lacking contrast); *White* (dark backgrounds with sufficient contrast). Corner radius is adjustable from square to capsule.

**Platform deltas:**
- iOS/iPadOS/macOS/visionOS/watchOS: No additional considerations.
- tvOS: Not supported.

### In-app purchase
*Last changed: 2023-09*

**Purpose:** Lets people securely pay within your app for virtual goods — premium content, digital goods, and subscriptions — via StoreKit.

**Use it when / not when:**
- Consumable: depletes with use and can be re-purchased (e.g., game lives/gems).
- Non-consumable: doesn't expire (e.g., premium features).
- Auto-renewable subscription: renews each period until canceled.
- Non-renewing subscription: time-limited access purchased each time (e.g., in-game battle pass).

**Best practices:**
- Let people experience your app before purchasing; for subscriptions, consider limited free access (freemium, metered paywall, or free trial).
- Design an integrated shopping experience that mirrors your app's style; don't let people feel they entered a different app.
- Use simple, succinct product names/descriptions that don't truncate or wrap.
- Display the TOTAL billing price for every in-app purchase you offer, regardless of type.
- Display your store only when people can make payments; if they can't (e.g., parental restrictions), hide the store or explain why it's unavailable.
- Use the default system confirmation sheet — don't modify or replicate it.
- Family Sharing: shareable content (auto-renewable subscriptions, non-consumables) reaches up to 5 additional family members. Mention "Family"/"Shareable" in names and on the sign-up screen; customize in-app messaging for both purchasers and family members.
- Refund help: provide a custom help screen before the refund request, but don't let it block the refund — avoid making people scroll or open another screen to reach the refund button. Use a simple action title ("Refund" / "Request a Refund"). Help people identify the purchase (image, name, description, original date). The system-provided refund flow makes it clear the refund comes from Apple. Don't characterize Apple's refund policies or speculate about outcomes.
- Subscription onboarding: show value, a strong call to action, and a clear summary of terms.
- Offer a range of content choices, service levels, and durations.
- Provide clear, distinguishable subscription options with self-explanatory names, price, and duration; list any introductory price, its duration, and the standard price after.
- Simplify initial signup — ask only for necessary info; defer the rest.
- The in-app sign-up screen MUST include: subscription name, duration, and content/services per period; the correctly localized billing amount for each territory/currency; and a way for existing subscribers to sign in or restore purchases.
- Clearly describe how a free trial works — that payment auto-starts for the next period when the trial ends, including the duration and the billed amount.
- Include a sign-up opportunity in app/account settings. Encourage a new subscription only when someone isn't already subscribed; offer sign-in across apps/website so people don't pay twice.
- Offer codes (iOS/iPadOS): *one-time use codes* (generated in App Store Connect; redeemable via redemption URL, in-app, or App Store; good for small/restricted distribution) and *custom codes* (e.g., NEWYEAR — alphanumeric ASCII only, no special/Chinese/Arabic characters; redeemable only via redemption URL or in-app, NOT App Store account settings — so tell people how to redeem). Consider in-app redemption (only custom UI needed is one that launches the system flow). Supply an optional promotional image (else app icon is used).
- Subscription management: let people upgrade/downgrade/cancel without leaving the app; consider the system-provided management UI. Show subscription summaries including the upcoming renewal date. Always make canceling easy — don't bury it. On cancellation, consider a personalized retention offer or exit survey.

Canonical implementations: StoreKit `AppStore.canMakePayments`, `Transaction.beginRefundRequest(for:in:)`, `Product.SubscriptionInfo`, `AppStore.showManageSubscriptions(in:)`, `AppStore.presentOfferCodeRedeemSheet(in:)`; SwiftUI `View.offerCodeRedemption(isPresented:onCompletion:)`.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS: No additional considerations.
- tvOS: Help people sign up / authenticate using another device — send a code to another device rather than asking for input on Apple TV.
- watchOS: The sign-up screen must display the same required subscription info as other versions. Clearly describe differences from other devices without implying parity. Consider a modal sheet (with its default Close button) to present all required items in one view. Make options easy to compare on a small screen — either one option per button (lock up each button with its description) or a list of options followed by a button whose title updates to the chosen option.

### Wallet
*Last changed: 2026-06*

**Purpose:** Securely stores credit/debit cards, IDs, transit cards, tickets, keys, and passes on iPhone and Apple Watch, and supports order tracking and identity verification.

**Best practices:**
- Offer to add new passes with one tap when an action creates one; for frequent predictable actions (e.g., flight check-in) add passes in the background after a one-time authorization. Show a custom Add to Apple Wallet button view if people want to review first.
- Help people add a pass created outside your app (suggest it next time they open the app); if they decline, don't ask again — but show an Add to Apple Wallet button wherever pass info appears so they can add it later.
- Add related passes as a group (e.g., multi-connection boarding passes, event-ticket sets).
- Let people jump from your app to the pass in Wallet via a "View in Wallet" link.
- Tell the system when passes expire (set expiration date, relevant date, voided properties) so Wallet can hide them.
- Always get permission before deleting passes; offer an in-app setting for manual vs. automatic removal.
- Help the system surface a pass when relevant (Lock Screen link, and Live Activity for types like event tickets) by supplying when/where it's relevant.
- Keep passes up to date (e.g., flight delays/gate changes). Use change messages ONLY for time-critical updates — never for marketing or noncritical info.
- Design a clean, simple pass that feels at home in Wallet rather than replicating its physical counterpart; use Pass Designer to design/preview.
- Keep the pass front uncluttered: put essential info (event date, balance) in the header so it shows when collapsed; put rarely needed details on the additional info sheet / back fields.
- Make passes instantly identifiable with brand colors/images/full-art backgrounds; ensure sufficient contrast between background and text/label colors.
- Design passes to work on all devices (Apple Watch shows less info / fewer images and crops white space from some images); don't put essential info in elements that may be unavailable; avoid padding on images; use device-neutral language (avoid "Slide to view").
- Pass fields, top to bottom: logo + logo text (visible when collapsed), header fields (critical, visible when collapsed), primary field (most important), secondary + auxiliary fields (useful but less critical), footer fields (e.g., category), back fields (rarely accessed, e.g., legal text). Layout varies by style.
- Semantic tags describe pass content to the system (enabling pass surfacing and featured actions); for poster event and semantic boarding passes they're REQUIRED and enable automatic layout — still include pass fields alongside them so older iOS versions display correctly.
- Pass images: PNG, @2x and @3x. Reserve images for visual content (embedded text isn't accessible and may not render everywhere); use text fields/semantic tags for text and Pass Designer/APIs for barcodes rather than embedding. Keep file sizes small for fast email/web downloads. Provide a pass icon (app icon or a separate one). Avoid inner drop shadows on logo artwork. Thumbnails are square with rounded corners exported as transparent PNG.
- Order tracking: make it easy to add an order to Wallet (auto-add after Apple Pay, or the system Track with Apple Wallet button in iOS 17+ on confirmation/status/tracking pages and emails). Make order info available immediately after placement even if details are pending. Provide fulfillment info as soon as available and keep status current (Order Placed, Processing, Ready for Pickup, Picked Up, Out for Delivery, Delivered, Issue, Canceled). Keep the fulfillment screen centered on tracking. Provide multiple contact methods (at minimum a website/landing-page link; optionally Messages for Business, phone, email, support page). Choose shipping status values matching the detail you have (`onTheWay`/`outForDelivery`/`delivered` when known, else `shipped`), and provide a tracking link. Be direct and thorough for Issue/Canceled statuses.
- Identity verification (iOS 16+): present Verify with Wallet only when the device supports it, with a fallback verification method otherwise. Ask for identity info only at the precise moment you need it. Write a clear purpose string (sentence case, active voice, period at end) explaining why you need the data; the system displays it in the verification sheet. Ask only for the data you need (e.g., use an age threshold rather than current age/birth date). Indicate whether/how long you'll keep the data via PassKit duration APIs. Choose the button label matching your case. The verification button is white-on-black; a light-outline variant exists for dark backgrounds, and corner radius is adjustable.

Canonical implementations: PassKit `PKPassLibrary.addPasses(_:withCompletionHandler:)`, `PKPassLibrary.Capability.backgroundAddPasses`, `PKAddPassesViewController`, `PKAddPassButton`, `VerifyIdentityWithWalletButton`, `PKIdentityButton.Label` / `.Style.blackOutline` / `.cornerRadius`, `PKIdentityElement.age(atLeast:)`, `PKIdentityIntentToStore`, `PKPaymentOrderDetails`; WalletPasses `Pass`, `LineItem`, `Order`, `Merchant`, `ShippingFulfillment`; FinanceKitUI `AddOrderToWalletButton`; web `ApplePayPaymentOrderDetails`.

**Specs:**

Pass styles: boarding passes (airline = semantic tags; other transit = pass fields); coupons; event tickets (poster event = full-art background + semantic tags; non-poster = standard fields + optional background/thumbnail); store cards (loyalty/discount/points/gift, often showing a balance); poster generic passes (full background image, flexible); generic passes (gym card, coat-check ticket).

Pass image dimensions (pt):

| Image | Filename | Supported styles | Width | Height |
| --- | --- | --- | --- | --- |
| Logo | logo.png | Non-semantic airline boarding, non-airline boarding styles, coupons, non-poster event tickets, generic, store cards | 50–160 (min–max) | 50 |
| Primary logo | primaryLogo.png | Airline boarding, poster event tickets, poster generic | 30–126 (min–max) | 30 |
| Secondary logo | secondaryLogo.png | Poster event ticket | 12–135 (min–max) | 12 |
| Icon | icon.png | All | 38 | 38 |
| Strip | strip.png | Coupon, store card | 375 | 144 |
| Thumbnail | thumbnail.png | Event ticket, generic | 60–90 (min–max) | 90 |
| Background (non-poster) | background.png | Event tickets | 343 | 503 |
| Background (poster) | artwork.png | Poster event tickets, poster generic | 358 | 448 |
| Footer | footer.png | Airline boarding passes | 268 | 15 |

Order-tracking images: logo and product images are PNG/JPEG, 300x300 px, nontransparent background.

**Platform deltas:**
- iOS/iPadOS/macOS/visionOS: No additional considerations.
- tvOS: Not supported.
- watchOS: Wallet shows passes in a scrolling carousel; tapping reveals a scrolling details screen. Each style maps fields/images into a logo + essential-field row, a primary-field row, and a secondary/auxiliary-field row; overflow goes to the details screen. People can add a pass to Apple Watch even without a watch-specific app.

### Sign in with Apple
*Last changed: 2022-09*

**Purpose:** A fast, private way to sign in or sign up using an existing Apple Account — with Face ID/Touch ID/Optic ID and built-in two-factor authentication — skipping forms, email verification, and passwords; available on every platform, including non-Apple ones.

**Use it when / not when:**
- Offer it in every version of your app or website across all platforms, including non-Apple platforms, when you offer sign-in.
- If you require an account, set it up first (explain why), then offer Sign in with Apple alongside other sign-in methods.
- In a commerce app, wait until after a purchase to ask people to create an account; if name/email were already provided during Apple Pay, don't ask again.

**Best practices:**
- Ask people to sign in only in exchange for value; describe the benefits.
- Delay sign-in as long as possible; let people explore first.
- Consider letting people link an existing account to Sign in with Apple (e.g., when a shared email matches an existing account, or from account settings after username/password sign-in).
- As soon as Sign in with Apple completes, welcome people to their account; don't delay with non-required info.
- Indicate the current sign-in method (e.g., "Using Sign in with Apple") in settings/account.
- Don't ask people to supply a password (a core benefit is no extra passwords).
- Clarify whether additional data is required (legal/contractual — e.g., terms agreement, region of residence, birth date, real-identity-law info) or optional (explain its benefits); never block account access/features when optional data is declined.
- Avoid asking for a personal email when people supply a private relay address; respect it — let people view their relay address, direct them to Settings > Apple Account > Password & Security > Apps using Apple Account, or identify them via order/phone number.
- Be transparent about collected data (e.g., welcome people by the name/email they shared); if you don't display data people provided, they'll wonder why you asked.
- Prominently display a Sign in with Apple button — no smaller than other sign-in buttons, and not requiring scrolling.
- Prefer the system-provided button APIs (Apple-approved appearance, ideal proportions, automatic title translation, configurable corner radius on iOS/macOS/web, VoiceOver label).
- Button titles (iOS/macOS/tvOS/web): "Sign in with Apple", "Sign up with Apple", "Continue with Apple" — pick one and use consistently. watchOS provides one title: "Sign in".
- Button appearances: White (all platforms + web; dark backgrounds with sufficient contrast); White with outline (iOS/macOS/web; light backgrounds lacking contrast — avoid on dark/saturated backgrounds); Black (all platforms + web; light backgrounds with sufficient contrast). The watchOS black button uses system dark gray (not pure black) to contrast Apple Watch's black background.
- Adjust corner radius (square to capsule on iOS/macOS/web) to match other buttons.
- Custom button: allowed on iOS/macOS/web; people must instantly recognize it as a Sign in with Apple button, and App Review evaluates all custom buttons. Use only Apple-provided logo artwork from Apple Design Resources (PNG/SVG/PDF, black and white) — never create a custom Apple logo, never use the logo as a button, never crop it, don't add vertical padding, and match logo height to button height. Don't change titles (only the three approved), general shape (logo+text always rectangular; logo-only can be circular or rectangular), or logo/title colors (both black or both white). You MAY change title font (weight/size), title case (all caps allowed), background appearance (must stay black or white; subtle texture/gradient allowed), corner radius, and bezel/shadow.
- Custom logo+text proportions must match the system: title font size = 43% of button height (button height = 233% of font size, rounded). Use PNG only at 44 pt tall (default/recommended iOS height); use SVG/PDF at any height. Vertically center the title, then add the logo at button height. Keep a margin of at least 8% of button width between title and right edge.
- Custom logo-only buttons always have a 1:1 aspect ratio with built-in padding — don't add horizontal padding or crop; use a mask (circular/rounded-rectangular) to change the square shape; use PNG only at 44x44 pt. Maintain a margin of at least 1/10 the button's height.

Canonical implementations: AuthenticationServices `ASAuthorizationAppleIDButton` (`cornerRadius`) (iOS, macOS, tvOS); WatchKit `WKInterfaceAuthorizationAppleIDButton` (watchOS); web "Displaying Sign in with Apple buttons on the web".

**Specs:**

System button (and custom logo+text button) minimum size and margin (iOS/macOS/web):

| Minimum width | Minimum height | Minimum margin |
| --- | --- | --- |
| 140pt (140px @1x, 280px @2x) | 30pt (30px @1x, 60px @2x) | 1/10 of the button's height |

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: No additional considerations.

### Tap to Pay on iPhone
*Last changed: 2024-05*

**Purpose:** Lets merchants accept contactless payments using an iOS app on iPhone — no external hardware — via a supported payment service provider (PSP) and ProximityReader APIs.

**Best practices:**
- Before integrating: work with a supported PSP, request the Tap to Pay on iPhone entitlement, and use ProximityReader (via the PSP's SDK or directly).
- Help merchants accept the terms and conditions before they start a customer-facing flow (e.g., in onboarding/in-app messaging), since acceptance is required before initial device configuration. Use the API to check status and present the acceptance flow only when needed.
- Present terms and conditions only to an administrative user; if a nonadministrator tries, explain that admin access is required (admins can accept via a web interface or another app, including on non-iPhone devices — contact your PSP).
- If your PSP requires specific iOS versions, present terms only after the merchant updates.
- Educate merchants with a tutorial covering each supported payment type — either built from Apple-approved marketing assets or via the prebuilt, localized `ProximityReaderDiscovery` experience. Make it available in help/settings, after terms acceptance, or for new users. A custom tutorial must show how to launch checkout per payment type, position a contactless card/digital wallet, and handle PIN entry including accessibility mode; end it with a chance to accept terms.
- Offer Tap to Pay on iPhone as a checkout option whether or not it's enabled; on tap, present terms if needed and auto-show the Tap to Pay screen when configuration completes.
- Avoid making merchants wait: configuration is needed initially AND each time the app becomes frontmost — prepare the feature at app start and after each foreground transition. Keep the checkout option always selectable even while configuration continues in the background; show an indeterminate progress indicator, or a determinate one if the API reports ongoing configuration.
- If you support multiple payment-acceptance methods, make the Tap to Pay button easy to find (no scrolling) and let merchants switch between it and hardware accessories during checkout without visiting settings. If it's your only method, open Tap to Pay automatically when checkout begins.
- Button label: use "Tap to Pay on iPhone" or, if space is constrained, "Tap to Pay". Exception: if it's your only payment-acceptance method, you may reuse existing Charge/Checkout buttons. If you use icons across methods, use the `wave.3.right.circle` or `wave.3.right.circle.fill` SF Symbols. NEVER include the Apple logo. Match the button's color/shape to your app.
- Determine the final amount (including tips and other pre-payment options) before opening the Tap to Pay screen; display pre-payment options in your checkout screen before the Tap to Pay screen; show the final amount on the Tap to Pay screen.
- Start processing as soon as possible (request the read result before the checkmark animation finishes). Display an authorization progress indicator after the Tap to Pay screen animation finishes and before your result screen.
- Clearly display the transaction result (declined or successful); offer a digital receipt (e.g., QR code or text message).
- On a failed tap (unreadable card, unsupported network, amount not allowed, no online PIN), help merchants finish checkout: accept an alternate form (cash), use a different method (hardware/payment link), or relaunch Tap to Pay for another card. Handle region-specific cases (Strong Customer Authentication PIN-after-tap; Offline PIN markets) per PSP guidance.
- If the system returns a merchant-addressable error (e.g., iOS version unsupported), show a clear description and recommended resolution (e.g., an alert to update iOS). Make it easy to get help (app/website help content, contact support).
- Additional interactions (reading a card with no transaction amount — look up a transaction, retain card info, refund, verify): use a GENERIC label like "Look Up", "Store Card", "Verify", or "Refund" — don't include "Tap to Pay on iPhone" / "Tap to Pay". For an independent loyalty/discount/points card transaction, give a separate, clearly labeled button (e.g., "Loyalty Card") that avoids "Tap to Pay" or payment-related terms.

Canonical implementations: ProximityReader `PaymentCardReader.prepare(using:)`, `ProximityReaderDiscovery`, `PaymentCardReader.Event.updateProgress(_:)` / `.readyForTap`, `PaymentCardReader.Options.returnReadResultImmediately`, `PaymentCardReaderSession.ReadError`.

**Platform deltas:**
- iOS: No additional considerations.
- iPadOS/macOS/tvOS/visionOS/watchOS: Not supported.

### ID Verifier
*Last changed: 2023-09*

**Purpose:** Lets an iPhone app read ISO18013-5 compliant mobile IDs in person (no external hardware) for in-person ID verification, beginning in iOS 17.

**Use it when / not when:**
- Display Only request: shows data (name/age + photo portrait) in system UI for visual confirmation; the customer's data stays in system UI and isn't transmitted to your app.
- Data Transfer request: use ONLY with a legal verification requirement when you must store/process info (e.g., address, date of birth); requires an additional entitlement.

**Best practices:**
- Ask only for the data you need (e.g., specify an age threshold rather than requesting current age or birth date).
- If your app qualifies for Apple Business Register, register for ID Verifier so the system can display your official organization name and logo during a request.
- Provide a button that initiates verification — use "Verify Age" for a simple age check or "Verify Identity" for a detailed identity data request. Avoid symbols implying a communication type (NFC, QR codes). Never include the Apple logo.
- In a Display Only request, let the app user give feedback on the visual confirmation (e.g., "Matches Person" / "Doesn't Match Person" buttons) so the app receives an approved/rejected value.

Canonical implementations: ProximityReader `MobileDriversLicenseDisplayRequest`, `MobileDriversLicenseDataRequest` (`Element.ageAtLeast(_:)`), `MobileDriversLicenseRawDataRequest`.

**Platform deltas:**
- iOS: No additional considerations.
- iPadOS/macOS/tvOS/visionOS/watchOS: Not supported.
