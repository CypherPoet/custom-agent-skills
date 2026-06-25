# Bundled App Store Connect API scripts

Ready-to-run, zero-dependency Swift scripts for driving App Store Connect from the CLI (or an agent).
Swift ships with the Command Line Tools / Xcode, so there's nothing to `npm install`; `CryptoKit`
signs the JWT. Run each from your project root with a filled `.env` beside it (see
[`../references/api-automation.md`](../references/api-automation.md) for the key + `.env` setup).

| Script | What it does | Usage |
|--------|--------------|-------|
| `asc-get.swift` | GET any API path, pretty-print the JSON. Read-only — your Swiss-army knife for inspecting live state. | `swift scripts/asc-get.swift "/v1/apps/<id>/appStoreVersions"` |
| `asc-build-status.swift` | Poll the latest build's `processingState` (`PROCESSING` → `VALID`). Sorts by `-uploadedDate` (build `version` is a string). | `swift scripts/asc-build-status.swift` |
| `asc-upload-screenshots.swift` | Upload screenshots to the `APP_IPHONE_67` set (reserve → PUT → commit → lock order). Re-runnable (clears the set first). | `swift scripts/asc-upload-screenshots.swift 01.png 02.png …` |
| `asc-upload-previews.swift` | Same flow for app preview videos into the `IPHONE_67` set. | `swift scripts/asc-upload-previews.swift 1.mp4 2.mp4 …` |
| `asc-set-review-notes.swift` | Set the App Review "Notes" on the in-prep version (from a file or stdin). | `swift scripts/asc-set-review-notes.swift notes.txt` |

All five read the same four `.env` vars (`ASC_KEY_ID`, `ASC_ISSUER_ID`, `API_PRIVATE_KEYS_DIR`,
`ASC_APP_ID`) and discover the in-prep version / en-US localization themselves, so they're app-agnostic.

> **Credential boundary:** the `.p8` is read only to sign the JWT; its contents are never printed.
> Keep `.env`, `*.p8`, and `private_keys/` gitignored. Same posture as a `gh` token.
