# App Store Listing Optimization

Beyond-compliance best practices for the App Store listing — metadata/ASO, screenshots, reviews, and localization. Referenced by the [apple-app-store-best-practices](../SKILL.md) skill.

## Metadata Optimization Best Practices

Beyond compliance, well-optimized metadata improves discoverability and conversion. Apply these when reviewing or drafting App Store listings.

**App Name & Subtitle:**
- Use the full 30 characters in both — every unused character is a missed keyword opportunity
- Front-load the most important keyword into the title; use the subtitle for a secondary keyword or value proposition
- Don't repeat words between title and subtitle — Apple indexes both together

**Keywords field (100 characters):**
- No spaces after commas — spaces count against the limit (use `photo,editor,filter` not `photo, editor, filter`)
- Don't duplicate words already in the title or subtitle — Apple indexes those automatically
- Use singular forms only — Apple indexes both singular and plural
- Don't include the word "app" or your category name — already indexed
- Don't include competitor names (also violates §2.3.7)
- Use all 100 characters — fill remaining space with related terms, synonyms, and common misspellings

**Description (4,000 characters):**
- Lead with a one-line value proposition — this is what users see before tapping "more"
- Follow with 3-5 bullet points highlighting key features
- Include social proof if available (awards, press mentions, user count)
- End with a call to action
- Note: the Description is NOT indexed for search — keywords here don't affect discoverability. Focus on conversion, not keyword stuffing.

**Promotional Text (170 characters):**
- Updated anytime without a new app version — use for timely messaging (seasonal events, new features, limited offers)
- Not indexed for search — purely a conversion tool

## Screenshot & App Preview Strategy

Screenshots and app preview videos are the primary conversion driver on the App Store listing page.

This section covers *strategy and compliance*. For the exact specifications — screenshot dimensions per device class, formats and counts, the upload-the-largest / auto-scale model, app preview video specs, and capture/`fastlane` automation — use the **`apple-app-store-screenshots`** skill, which ships with this plugin.

**Screenshot best practices:**
- Use all 10 available screenshot slots — more screenshots give users more reasons to download
- The first 3 screenshots are visible before scrolling in search results — put the strongest features there
- Show the app in actual use with real content, not empty states or placeholder data
- Each screenshot should communicate a distinct feature or benefit
- Add concise captions above or below the UI to explain what the user is seeing
- Provide screenshots for every supported device class — uploading the largest (the 6.9" iPhone, the 13" iPad) lets App Store Connect auto-scale the rest (exact sizes: the `apple-app-store-screenshots` skill)

**App preview video:**
- App previews auto-play in search results (muted) and significantly increase conversion
- Keep it under 30 seconds — focus on the core user journey
- Design for muted viewing — use text overlays to convey the narrative without audio
- Show real app footage, not animated mockups (also required by §2.3.3)

**Compliance note:** Screenshots and previews must accurately represent the current app experience (§2.3.3). Outdated or misleading visuals are a P2 rejection risk.

## Review & Rating Management

App Store ratings directly affect search ranking and conversion. Proactive management matters.

**Strategic review prompts:**
- Use `SKStoreReviewController.requestReview()` — Apple controls the display frequency (max 3 times per 365-day period per device)
- Prompt after positive moments: completing onboarding, achieving a milestone, finishing a successful transaction — not on first launch or during frustrating moments
- Never create custom review prompts that bypass `SKStoreReviewController` — this violates §3.2.2(x)
- Never gate features behind reviews or incentivize ratings — this is a P2 rejection risk (§3.2.2(x))

**Responding to reviews:**
- Respond to negative reviews via App Store Connect — this signals active maintenance and can prompt users to update their rating
- Address the specific issue raised, not a generic "thanks for your feedback"
- Use the App Store Connect API to monitor and respond to reviews programmatically at scale

**Feedback loop:**
- Monitor review sentiment for recurring complaints — these often surface the same issues that trigger App Review rejections
- Common review complaints about crashes, broken features, or permission requests map directly to §2.1, §2.3, and §5.1.1(ii)

## Localization Guidance

Localizing App Store metadata expands discoverability across markets. Each locale gets its own independent set of metadata fields.

**What to localize:**
- App Name, Subtitle, Keywords, Description, Promotional Text, What's New, and Screenshots
- Each locale gets a separate 100-character keyword field — this multiplies your total keyword coverage
- Keywords that don't fit in your primary market can go in secondary locale keyword fields

**Localization vs. translation:**
- Don't just translate keywords — research what users in each market actually search for
- Search behavior varies by culture: a direct translation of "photo editor" may not be the top search term in Japanese or Korean
- Use App Store Connect's App Analytics to see which search terms drive impressions in each locale

**Priority markets** (largest App Store revenue, in order):
- English (US, UK, Australia, Canada)
- Simplified Chinese
- Japanese
- Korean
- German
- French
- Spanish

**Tip:** Even if the app UI is English-only, localizing just the metadata (title, subtitle, keywords, description) still improves discoverability in non-English markets. This requires no code changes — it's configured entirely in App Store Connect.
