# Patterns — Search & Settings

> Source: https://developer.apple.com/design/human-interface-guidelines
> Last synced: 2026-06-16

Distilled from Apple's HIG Patterns pages: Searching, Search fields, Settings, Managing accounts.

## Contents
- [Searching](#searching)
- [Search fields](#search-fields)
- [Settings](#settings)
- [Managing accounts](#managing-accounts)

### Searching
*Last changed: 2026-06*

**Purpose:** Lets people find content on their device, within an app, and within a document or file, typically through a search field.

**Best practices:**
- If search is important, give it a primary position in your app or view (a bottom-toolbar field like Notes, or a dedicated tab like Photos and Apple TV).
- Aim to make content searchable through a single, clearly identified location; offer local search for clearly distinct sections (e.g. search filters the current view in the iOS Music app).
- Clearly display the current scope of a search using descriptive placeholder text, a scope bar, or a title.
- Provide suggestions: show recent searches before typing or predictive suggestions while typing. See SwiftUI `searchSuggestions(_:)`.
- Take privacy into account before displaying search history; if shown, give people a way to clear it.
- Systemwide: make content searchable in Spotlight by indexing it and supplying descriptive metadata.
- Define metadata for custom file types via a Spotlight File Importer plug-in (`CSImportExtension`).
- Use Spotlight to offer advanced in-app file search (e.g. a button that runs a Spotlight search on the current selection and shows results in a custom view).
- Prefer the system-provided open and save views, which include a built-in search field.
- Implement a Quick Look generator if your app produces custom file types, so Spotlight and other apps can preview documents.

Canonical implementations: SwiftUI `searchSuggestions(_:)`; Core Spotlight `CSImportExtension`; Quick Look.

**Platform deltas:**
- iOS/iPadOS/macOS/tvOS/visionOS/watchOS: No additional considerations.

### Search fields
*Last changed: 2026-06*

**Purpose:** An editable text field with a Search icon, Clear button, and placeholder text that lets people search a collection of content for specific terms.

**Best practices:**
- Use placeholder text to convey what people can search for and reinforce the search scope.
- If possible, start searching immediately as a person types, so results refine continuously.
- Consider showing suggested search terms: recent searches before search begins, predictive suggestions as a person types.
- Simplify results: surface the most relevant first to minimize scrolling, and consider categorizing them.
- Consider letting people filter results, e.g. a scope bar in the results content area.
- Use a scope bar to filter among clearly defined search categories (e.g. Mail moves from the entire mailbox to the current one). See SwiftUI Scoping a search operation.
- Default to a broader scope and let people refine it as needed.
- Use tokens to filter by common search terms or items; a token gets a visual treatment people can select and edit as a single item. For the macOS component, see Token fields.
- Consider pairing tokens with search suggestions, since people may not know which tokens are available.

Canonical implementations: SwiftUI `searchable(text:placement:prompt:)`, Adding a search interface to your app; UIKit `UISearchBar`, `UISearchTextField`, `UISearchController`; AppKit `NSSearchField`.

**Platform deltas:**
- iOS: Three entry-point placements for search — as a tab in a tab bar, in a bottom or top toolbar, or directly inline with content. Search-as-a-tab has two styles: **Standard tab** (uniform with the tab bar; tapping opens a search landing page with a field at the top — choose it to provide suggestions, promote discovery, and encourage exploration, as Apple TV does) and **Button appearance** (a separate button on the trailing edge; tapping focuses the field and shows the keyboard immediately — choose it for quick, transient searches that return people to their previous tab). For toolbars: place search at the bottom if there's room (expanded field or button; animates into a field above the keyboard), useful whenever search is a priority (Settings, Mail, Notes); place it at the top when you must defer to content at the bottom or there's no bottom toolbar (Wallet). For inline fields: use when position alongside the content it searches strengthens that relationship, or for filtering within a single view; when at the top, position it above the list it searches and consider pinning it to the top toolbar when scrolling.
- iPadOS, macOS: Placement and behavior are similar; keep the experience consistent across both. Put a search field at the trailing side of the toolbar for many common uses, especially split-view apps searching multiple columns (Mail, Notes, Voice Memos) or where results appear in the detail view (Freeform). Include search at the top of the sidebar when filtering content or navigation there (Settings). Include search as a sidebar or tab-bar item when you want a dedicated discovery area paired with rich suggestions (Music, TV). In a dedicated area, consider immediately focusing the field on navigation — except on iPad when only a virtual keyboard is available, where it's better to leave it unfocused so the keyboard doesn't cover the view. Account for window resizing: on iPad the field fluidly resizes like on Mac, and for compact views ensure search stays contextually useful (Notes and Mail move search above the content-list column when compact).
- tvOS: A search screen is a specialized keyboard screen that enters search text and shows results beneath the keyboard in a fully customizable view (`UISearchController`). People don't want to type much, so provide popular and context-specific suggestions, including recent searches.
- watchOS: Tapping the search field displays a full-screen text-input control; the app returns to the field only after the person taps Cancel or Search.
- visionOS: No additional considerations.

### Settings
*Last changed: 2024-06*

**Purpose:** Lets people customize an app or game experience, through a custom in-app settings area, in-context task options, or the system-provided Settings app.

**Use it when / not when:**
- Custom in-app settings area: for general, infrequently changed options that affect the overall experience (interface style, window configuration, game-saving behavior, account-related options).
- In-context (task-specific) options: prefer these for options that affect only a specific task (showing/hiding parts of a view, reordering items, filtering a list) — keep them in the screens they affect.
- System-provided Settings app: add only the most rarely changed options here; consider a button that opens it directly from your interface.

**Best practices:**
- Provide default settings that give the best experience to the largest number of people (e.g. auto-maximize game performance for the device).
- Minimize the number of settings; too many make the experience less approachable and harder to navigate.
- Make settings available in expected ways: Command-Comma (,) opens an app's settings when a physical keyboard is connected; Esc often opens a game's settings.
- Avoid using settings to ask for setup information you can get in other ways (detect a connected controller; detect Dark Mode).
- Respect systemwide settings and avoid redundant in-app versions of them (accessibility, scrolling behavior, authentication methods), which confuses people about scope.

Canonical implementations: SwiftUI `Settings`; Foundation `UserDefaults`; Preference Panes.

**Platform deltas:**
- iOS/iPadOS/tvOS/visionOS: No additional considerations.
- macOS: The Settings item in the App menu opens a custom settings window, typically with a toolbar of buttons that switch between panes of related settings. Include a Settings item in the App menu (avoid settings buttons in a window toolbar; put document-level options in the File menu). Dim the settings window's minimize and maximize buttons. Use a noncustomizable toolbar that stays visible and always indicates the active button. Update the window title to reflect the visible pane; if there's only one pane, title it _App Name_ Settings. Restore the most recently viewed pane on open.
- watchOS: Apps and games don't add custom settings to the system-provided Settings app. Instead, make a small number of essential options available at the bottom of the main view, or let people use a More menu to reconfigure objects.

### Managing accounts
*Last changed: 2025-06*

**Purpose:** Guidance for offering accounts as a convenient way to access content and personal details without creating an unnecessary barrier to the experience.

**Best practices:**
- Ask people to create an account only if your core functionality requires it; otherwise let them use the app without one.
- If you require an account, consider Sign in with Apple for a consistent, trusted sign-in experience.
- Explain the benefits of creating an account and how to sign up; display this message in your sign-in view.
- Delay sign-in for as long as possible (e.g. let a shopping app's users browse freely, requiring sign-in only at purchase).
- If you don't use Sign in with Apple on iOS, iPadOS, macOS, or visionOS, prefer a passkey (people provide only a user name); see Supporting passkeys. If you keep passwords, augment with two-factor authentication.
- Always identify the authentication method you offer (title a button "Sign In with Face ID," not a generic "Sign In").
- Refer only to authentication methods available in the current context (don't reference Face ID on a device without it); check capabilities via `LABiometryType`.
- In general, avoid an app-specific setting for opting in to biometric authentication — it's set at the system level and is redundant.
- Avoid using the term _passcode_ for account authentication; people associate it with unlocking their device or authenticating for Apple services.
- Deleting accounts: if you help people create an account, you must also help them delete (not just deactivate) it, and comply with your region's legal requirements and the right to be forgotten.
- Provide a clear way to initiate account deletion within the app; if it can't be done in-app, give a direct, easy-to-find link to the deletion webpage (don't bury it in Privacy Policy or Terms of Service).
- Keep the deletion experience consistent whether done in-app or on the website (don't make one version longer or more complicated).
- Consider letting people schedule deletion for the future, but also offer immediate deletion.
- Tell people when deletion will complete and notify them when it's finished.
- If you support in-app purchases, help people understand billing and cancellation at deletion: auto-renewable subscription billing continues through Apple until canceled (regardless of deletion), and after deletion people still need to cancel the subscription or request a refund. Provide guidance on canceling subscriptions and managing purchases.

Canonical implementations: Authentication Services Supporting passkeys; `LABiometryType`.

**Platform deltas:**
- iOS/iPadOS/macOS/visionOS: No additional considerations.
- tvOS: Most people use a remote, not a keyboard, so ask for the minimum information necessary. Prefer letting people use another device to sign up or authenticate (configure associated domains so Apple TV can suggest credentials, including Sign in with Apple). When people are signed in to a shared account, avoid asking them to choose their profile every time they become the current user — in tvOS 16 and later, share credentials with all users while storing each profile separately (`kSecUseUserIndependentKeychain`, `User Management Entitlement`). Minimize data entry; for more than a small amount of information, ask people to visit a website from another device, and show the email keyboard screen (with recent addresses) when you need an email. TV provider accounts: if your TV provider app requires sign-in, use TV Provider Authentication; avoid a sign-out option when people are signed in at the system level (if you must include one, prompt people to navigate to Settings > TV Provider to sign out); never instruct people to sign out by adjusting privacy controls (Settings > Privacy isn't a sign-out mechanism).
- watchOS: Use iCloud synchronization to provide access to the Keychain, letting people autofill user names and passwords and preserve app settings.
