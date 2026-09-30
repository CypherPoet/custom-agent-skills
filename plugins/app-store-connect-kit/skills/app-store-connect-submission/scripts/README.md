# App Store Connect command-line helpers

A dependency-free Swift package for macOS 13+ with Xcode/Swift 5.9+. The five
`asc-*.swift` files launch the shared package; keep the whole `scripts/` directory
together. The first run compiles the tool locally. No external Swift packages are fetched.
Launchers build in a temporary directory by default; set `ASC_BUILD_DIR` to an
absolute writable path for a stable build location. Installed plugin files stay read-only.

Run from the project containing your `.env`, or pass `--env-file /absolute/path`:

```sh
# SCRIPTS is the absolute path to this skill's scripts directory.
# BUILD_DIR is an absolute writable build directory outside the installed plugin.
swift run --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR" asc --help
swift run --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR" asc get '/v1/apps/APP_ID/appStoreVersions'
swift run --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR" asc build-status \
  --app-id APP_ID --build-id BUILD_RESOURCE_ID --platform IOS
swift run --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR" asc upload-screenshots \
  --app-id APP_ID --version-id VERSION_RESOURCE_ID --platform IOS \
  --locale en-US --display-type APP_IPHONE_67 shot1.png shot2.png
swift run --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR" asc upload-previews \
  --app-id APP_ID --version-id VERSION_RESOURCE_ID --platform IOS \
  --locale en-US --display-type IPHONE_67 preview.mp4
swift run --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR" asc set-review-notes \
  --app-id APP_ID --version-id VERSION_RESOURCE_ID --platform IOS notes.txt
```

Replace the uppercase placeholders with actual resource IDs. A version resource ID
is distinct from a marketing version such as `1.0`; a build resource ID is distinct
from a build number. The tool verifies ownership, platform, and editable version state.
It never chooses the first prepared version or localization. Read [credential and
API guidance](../references/api-automation.md) before an authorized live operation.

| Command | Behavior |
|---|---|
| `get` | Read one Apple API path; authenticated requests and pagination require Apple's HTTPS origin |
| `build-status` | Poll exactly the selected build; verify app and platform on every response |
| `upload-screenshots` | Validate all input files, stage PNG/JPEG assets, wait for validation, set order |
| `upload-previews` | Validate all input files, stage videos, wait for video validation, set order |
| `set-review-notes` | Update an existing review-detail record; requires the review contact to exist |

The compatibility invocation `swift "$SCRIPTS/asc-get.swift" /v1/apps` still works.
Version 0.8 requires explicit target flags for build/media/notes commands and a notes
file instead of stdin. `ASC_APP_ID` no longer selects a write target implicitly.

**Exit status:** `0` means confirmed success, `1` means a failure, invalid input,
unknown state, or unconfirmed write, and `2` means processing remained pending.
Polling defaults to 20 attempts, 3 seconds apart. Use `--attempts 1` for one check;
`--attempts` accepts 1–360 and `--interval` accepts 0–60 seconds. Each request has
its own network timeout; the polling limit is not a total wall-clock deadline.

**Replacement:** nonempty media sets require `--replace`. The tool stages the new
assets alongside the old ones, waits for every new asset to reach `COMPLETE`, checks
for concurrent edits, sets the order, then removes old assets. It never deletes a set.
The combined old/new count must fit Apple's limit (10 screenshots or 3 previews).
When it does not fit, the tool stops before writing; use the console for that case.

This is not an atomic transaction. A failed upload can leave reserved/new assets;
a failure during old-asset cleanup can leave a mix of validated new and old assets.
The tool reports IDs and exits unsuccessfully. Inspect that set before retrying;
there is no automatic rollback, cleanup, or retry of writes. Avoid editing the set
concurrently. A pending processing result never authorizes deletion of old assets.

Local media checks cover readability, uniqueness, count, format, screenshot alpha,
and preview duration/stereo audio. Apple still validates device-specific dimensions,
encoding, and other listing requirements. Use the exact display type for your target.

For offline tests, run `swift test --package-path "$SCRIPTS" --scratch-path "$BUILD_DIR"`. Tests use in-memory
HTTP and credential mocks plus synthetic local fixtures. They require no Apple account,
network requests, Keychain access, or real secrets. Repository `npm test` runs them
on macOS; the dedicated macOS CI job also runs them.
