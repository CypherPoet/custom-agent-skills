# Automate App Store Connect with an API key

Use the bundled Swift client for repeatable API operations and Apple's upload tools
for archive delivery. The client manages authentication, explicit targets, polling,
and media safety. It does not create credentials, submit apps, or release versions.

## Table of Contents

| Section | Covers |
|---|---|
| [Credentials and providers](#credentials-and-providers) | Team-key permissions, file and Keychain providers, storage, and authorization boundaries |
| [Uploads with Apple tools](#uploads-with-apple-tools) | File-based API-key authentication for altool and archive export |
| [Shared Swift client](#shared-swift-client) | Origin restrictions, redirects, target selection, polling, and exit codes |
| [Media replacement](#media-replacement) | Preflight validation, staging, capacity limits, cleanup, and recovery |
| [Useful endpoints](#useful-endpoints) | Discovery, metadata, review, and delivery-state APIs |
| [Verify submission and release](#verify-submission-and-release) | Checking the exact submission and attached purchases |
| [API drift and remaining scope](#api-drift-and-remaining-scope) | Current fields, unsupported automation, and console workflows |

## Credentials and providers

An App Store Connect team API key consists of a Key ID, Issuer ID, and a `.p8`
private key. The private key can be downloaded only once. Create keys only when
credential setup is authorized, through Users and Access → Integrations → App Store
Connect API. An Account Holder or Admin creates a team key and assigns its role.

App Manager is appropriate for workflows that include submission; use a narrower
role when the task only needs narrower access. A team key can reach all apps in the
account; its role limits operations, not app scope. Treat a leaked App Manager key
as a serious compromise of app metadata and distribution. Verify current permissions
in Apple's [API-key guidance](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api/).
The bundled signer supports team keys (`iss` authentication), not individual keys.

### File provider

Store the key outside repositories, named `AuthKey_<KEYID>.p8`. Configuration contains
IDs and paths, never private-key contents:

```sh
ASC_KEY_PROVIDER=file
ASC_KEY_ID=ABC123XYZ
ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
API_PRIVATE_KEYS_DIR="/Users/you/.appstoreconnect/private_keys" # absolute path
```

Use a private directory (0700) and private file (0600), protected by the user's
chosen disk encryption and backup policy. The tool does not create this directory,
change permissions, or verify the storage policy. Setting up storage or changing
permissions needs separate authorization. Keep `.env`, `*.p8`, and `private_keys/`
out of git; gitignore is not encryption. Save only a placeholder template in a repo.

The dotenv parser supports `export`, single/double quotes, trailing comments, and
common escapes in double quotes. A `#` inside quotes is literal; outside quotes it
starts a comment at the beginning of a value or after whitespace. Shell expansion,
command substitution, and multiline values are not supported. Process environment
values override the file, including empty values. Malformed lines fail without
printing their contents. App, version, platform, and locale targets are command flags.

### Keychain provider

The Swift client can read an **existing** generic-password item containing the `.p8`
PEM text. Select it explicitly:

```sh
ASC_KEY_PROVIDER=keychain
ASC_KEY_ID=ABC123XYZ
ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ASC_KEYCHAIN_SERVICE=your-existing-service
ASC_KEYCHAIN_ACCOUNT=your-existing-account
```

This performs a noninteractive Keychain lookup. A missing, locked, or inaccessible
item fails; the client does not prompt, import a key, create an item, change access
controls, or fall back to disk. Creating/importing the item and allowing a particular
compiled tool to read it are separate, user-authorized setup tasks. Compilation or
binary identity changes may require revisiting that access outside the script.

There is no general password-manager command hook. Do not place shell commands or
key contents in configuration. For CI, supply a separately authorized secret-store
integration; this package does not provision CI secrets. Revoke a compromised key
in App Store Connect and replace it through the same authorized setup process.

**Agent boundary:** operate through the selected provider; keep raw keys and JWTs
out of chat, source, logs, and command-line arguments. Configuration/support for a
provider does not authorize accessing real credentials during a code review or test.

## Uploads with Apple tools

For the file provider, export the IDs/key-directory variables into the shell before
using `altool`; it does not read this client's `.env` or Keychain provider:

```sh
xcrun altool --upload-app -f App.ipa -t ios \
  --apiKey "$ASC_KEY_ID" --apiIssuer "$ASC_ISSUER_ID"
```

Get the IPA from Organizer → Custom → Export or `xcodebuild -exportArchive`.
`altool` can discover `AuthKey_<KEYID>.p8` in `API_PRIVATE_KEYS_DIR` or its standard
private-key search directories. `--validate-app` contacts Apple for validation;
it is not an offline test. Keychain-provider selection does not automatically
export the key to disk for Apple tools. Use Xcode/Transporter or an independently
authorized integration for that delivery path.

## Shared Swift client

See the [script README](../scripts/README.md) for executable examples. The package
requires macOS 13+, Xcode/Swift 5.9+, and no external Swift dependencies.

- API requests and pagination links require `https://api.appstoreconnect.apple.com`
  with no credentials in the URL, fragments, or nonstandard port.
- Every redirect is rejected, including same-origin redirects and signed uploads.
- Signed-upload operations use their provided HTTPS URL and headers, never the ASC
  bearer token. Invalid ranges, non-HTTPS URLs, or credential-bearing headers fail.
- Each API request receives a fresh ES256 JWT with a ten-minute lifetime. Tokens
  stay in memory; the client does not print request headers or raw error bodies.
- Writes require explicit app ID, version resource ID, and platform. Media also
  requires locale and display type. The client verifies ownership and
  `appVersionState == PREPARE_FOR_SUBMISSION` before writing; it never falls back
  to the first app/version or the deprecated state field.
- Build polling requires an explicit build resource ID, app ID, and platform.
  Media polling uses the exact newly reserved resource IDs.
- Exit 0 means confirmed success; 1 means failure/unknown/unconfirmed result; 2
  means still processing. Poll limits are configurable. No automatic write retries.

## Media replacement

The command validates **all** local files before reading credentials or contacting
Apple. Screenshots must decode as PNG/JPEG without alpha. Previews need a readable
MP4/MOV/M4V container, 15–30 seconds of video, and stereo audio, including silent
previews. Apple performs the final device-size and encoding validation.

Each asset uses reserve → upload the specified byte ranges → commit with its whole
file MD5 → poll delivery state. Screenshots use `assetDeliveryState`; previews use
`videoDeliveryState`. A commit response alone is not validation success.

An existing nonempty set requires `--replace`. New assets are staged in that same
set and must all reach `COMPLETE` before the old assets can be deleted. The client
rechecks version state and set membership, orders new assets first, removes the
old IDs, and verifies final ordering. This also sets preview order explicitly.

Apple's set limits still apply: old plus new must fit within 10 screenshots or 3
previews. The client refuses replacements that exceed capacity; it never clears a
set to make space. Use the console for a full-capacity replacement.

There is no atomic multi-asset transaction. A failed/pending upload preserves the
original IDs but may leave new reservations. A cleanup failure after validation
may leave both old and new assets. Inspect the reported set/resource IDs before
retrying; there is no destructive automatic recovery. Avoid concurrent edits.

The 6.7/6.9-inch iPhone screenshot class uses `APP_IPHONE_67` (preview `IPHONE_67`).
Use the appropriate API display type for other devices; the scripts no longer
hardcode `en-US` or select an arbitrary prepared version.

If Apple returns `MOV_RESAVE_STEREO`, check the stereo audio track; for
`MOV_RESAVE_LONGER`, check the 15-second minimum. A checksum mismatch requires
rechecking the whole original file rather than individual chunks. Preview poster
frames can be set through `previewFrameTimeCode` (`HH:MM:SS:FF`) on the preview
resource; the upload helper does not set that optional field.

The listing's marketing icon comes from the uploaded build's asset catalog. The
media helper does not replace the icon or choose its appearance.

## Useful endpoints

| Goal | Endpoint |
|---|---|
| Discover versions for an app | `GET /v1/apps/<id>/appStoreVersions`; inspect resource IDs, platform, and `appVersionState` |
| Discover builds | `GET /v1/builds?filter[app]=<id>&sort=-uploadedDate` |
| Read a selected build | `GET /v1/builds/<id>?include=app,preReleaseVersion` |
| Read/write listing copy | `GET` / `PATCH /v1/appStoreVersionLocalizations/<id>` |
| Attach a build | `PATCH /v1/appStoreVersions/<id>/relationships/build` |
| Media | `appScreenshotSets`/`appPreviewSets` and `appScreenshots`/`appPreviews` |
| Order assets | `PATCH /v1/<set-type>/<id>/relationships/<asset-type>` with the ordered IDs |
| Review notes | `PATCH /v1/appStoreReviewDetails/<id>`; set the contact in the console first |
| Submit for review | `reviewSubmissions` and `reviewSubmissionItems`; consult the current schema for the intended item types |
| Read submission state | `GET /v1/reviewSubmissions?filter[app]=<id>&include=items` |

The bundled `get` command is read-only; the table is an API reference, not an
implemented general-purpose write client. Submission and release require their
own authorized workflow and checks.

## Verify submission and release

After an authorized submission, inspect the **exact submission ID** returned by
creation, rather than assuming a `limit=1` list response is the latest submission.
Confirm its state is `WAITING_FOR_REVIEW` and the intended version/items are present.
Read items via the submission's `items` relationship/include instead of assuming
that an individual `reviewSubmissionItems` GET is supported.

For first-of-type IAPs, verify the version's purchase selection in the console and
the purchase's state after submission. `READY_TO_SUBMIT` is not evidence of being
queued; inspect why it did not transition before attempting another submission.
Manual release remains a separate action after approval. The helpers do not carry
out submission, TestFlight tester management, or release.

## API drift and remaining scope

Apple's [API 3.7 release notes](https://developer.apple.com/documentation/appstoreconnectapi/app-store-connect-api-3-7-release-notes)
deprecate `appStoreState` in favor of `appVersionState`, and preview
`assetDeliveryState` in favor of `videoDeliveryState`. The shared client uses those
replacement fields and fails on missing/unknown states instead of guessing.
Build relationships and version fields were checked against Apple's public API
reference on 2026-09-30; offline tests do not establish live account compatibility.

Age ratings are not categorically console-only: Apple exposes
[Modify an age rating declaration](https://developer.apple.com/documentation/appstoreconnectapi/patch-v1-ageratingdeclarations-_id_).
These helpers do not implement that workflow. The walkthrough uses the console for
age ratings, App Privacy, DSA declarations, agreements, and banking. Verify current
schemas and account permissions before extending automation; questionnaires are
app/version-specific work, not necessarily one-time account setup.
