# Automate App Store Connect with an API key (no fastlane)

The App Store Connect **API** is a REST API over almost everything in the console — builds, app
metadata, screenshots, pricing, in-app purchases, TestFlight, and **submitting a version for review**.
You can drive it from the CLI (or an agent / CI) without fastlane. *As of 2026-06; trust the current docs.*

## The key, and the `.env` pattern

Generate the key once: **App Store Connect → Users and Access → Integrations → App Store Connect API**.
Create a **Team key** and **assign it the App Manager role** (*Which role*, below). Download
`AuthKey_<KEYID>.p8` **once** — Apple won't let you re-download it. You get three things:

- **Key ID** — short, e.g. `ABC123XYZ`. The `.p8` must be named `AuthKey_<KEYID>.p8`.
- **Issuer ID** — a UUID at the top of the Integrations page.
- the **`.p8`** private key file — the only real secret.

### Which role: a Team key, assigned App Manager

Two things are easy to conflate — *who may generate the key* vs *what the key may do*:

- **Who generates it.** A **Team key** (the kind you want — it authenticates for the whole account, ideal
  for CI or an agent) can only be created by an **Account Holder or Admin**. An App Manager can't mint a Team
  key; they can only generate a personal **Individual key** that inherits their own permissions. This is
  about who clicks *Generate*, not what the key can do.
- **What it may do.** At creation you **assign the key a role**, and that role bounds which API calls
  succeed. Assign **App Manager** — the least-privilege role that still covers the whole ship pipeline: read
  build processing state, edit listing metadata, select the build, and **submit for review** (Apple's
  *Submit an app* page: "Required role: Account Holder, Admin, or App Manager" — Developer can't submit).
  App Manager and Admin are **identical for everything app-delivery**; Admin only adds powers a submission
  key should never hold (manage users, generate more keys, banking/tax + financial reports, sign
  certificates). So a leaked App Manager key can't drain payouts, add collaborators, or mint certs.

Caveat: the role bounds the key's *permissions*, not its *app reach* — a Team key can touch **every** app in
the account regardless of role (Apple won't scope a Team key to one app). Moot for a single-app account.

Keep secrets out of git: the `.p8` stays a gitignored file; an env file holds the IDs and the key-dir
*path* (never the key contents). Commit a `.env.template`, not `.env`:

```sh
# .env  (gitignored)
ASC_KEY_ID=ABC123XYZ
ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
API_PRIVATE_KEYS_DIR=/Users/you/.appstoreconnect/private_keys   # holds AuthKey_ABC123XYZ.p8
ASC_APP_ID=1234567890                                           # the app's numeric Apple ID
```

Gitignore `.env`, `*.p8`, `private_keys/`.

> **Credential boundary (for agents):** drive the tooling via env; never read, print, or store the raw
> `.p8`. Same posture as a `gh` token.

## Uploads — Apple-native `altool` (no JWT, no fastlane)

`xcrun altool` reads the API key straight from env + the key dir — no JWT plumbing:

```sh
xcrun altool --upload-app -f App.ipa -t ios \
  --apiKey "$ASC_KEY_ID" --apiIssuer "$ASC_ISSUER_ID"
```

altool searches `./private_keys`, `~/private_keys`, `~/.private_keys`, `~/.appstoreconnect/private_keys`,
or `$API_PRIVATE_KEYS_DIR` for `AuthKey_<KEYID>.p8`. (`--validate-app` dry-runs it.) Get the `.ipa` from
Organizer → **Custom → Export**, or `xcodebuild -exportArchive`.

## Everything else — a JWT + REST call

Build-status polling, metadata, screenshots, and **submitting for review** hit the REST API directly.
Auth is a short-lived **ES256 JWT** signed with the `.p8`:

- Header: `{ "alg": "ES256", "kid": "<KEY_ID>", "typ": "JWT" }`
- Payload: `{ "iss": "<ISSUER_ID>", "iat": <now>, "exp": <now+1200>, "aud": "appstoreconnect-v1" }`
- `Authorization: Bearer <jwt>` against `https://api.appstoreconnect.apple.com`.

Sign it with one import — Node `jsonwebtoken`, Python `PyJWT[crypto]`, or Swift CryptoKit. Minimal Node
poll for "is my latest build processed?":

```js
// node --env-file=.env check-build.mjs   (Node 20.6+ reads .env from the flag; or add: import "dotenv/config")
import { readFileSync } from "node:fs";
import jwt from "jsonwebtoken";        // npm i jsonwebtoken
const { ASC_KEY_ID, ASC_ISSUER_ID, API_PRIVATE_KEYS_DIR, ASC_APP_ID } = process.env;
const key = readFileSync(`${API_PRIVATE_KEYS_DIR}/AuthKey_${ASC_KEY_ID}.p8`);
const token = jwt.sign({ aud: "appstoreconnect-v1" }, key, {
  algorithm: "ES256", keyid: ASC_KEY_ID, issuer: ASC_ISSUER_ID, expiresIn: "20m",
});
const r = await fetch(
  `https://api.appstoreconnect.apple.com/v1/builds?filter[app]=${ASC_APP_ID}` +
  `&sort=-uploadedDate&limit=1&fields[builds]=version,processingState,uploadedDate`,
  { headers: { Authorization: `Bearer ${token}` } });
const b = (await r.json()).data?.[0]?.attributes;
console.log(b ? `build ${b.version}: ${b.processingState}` : "no builds");
```

`processingState` is `PROCESSING` → `VALID` (then selectable on the version page) or `FAILED` / `INVALID`.

> **Bundled scripts.** This skill ships ready-to-run, zero-dependency Swift versions of all of this in
> [`scripts/`](../scripts/) (Swift + CryptoKit ship with Xcode, so there's nothing to install):
> `asc-get` (inspect any endpoint), `asc-build-status` (poll the build), `asc-upload-screenshots` /
> `asc-upload-previews` (the media flow below), and `asc-set-review-notes`. They read the same `.env`
> and discover the in-prep version themselves. Reach for them before hand-rolling a request.

## Uploading screenshots & previews (reserve → upload → commit)

Media uploads are a 3-phase flow (plus an ordering step), same shape for both (only the asset endpoint
differs). First create the set: `POST /v1/appScreenshotSets` (attribute `screenshotDisplayType`, e.g.
`APP_IPHONE_67`) / `appPreviewSets` (attribute `previewType`, e.g. `IPHONE_67`), related to an
`appStoreVersionLocalization`. Then per asset:

1. **Reserve** — `POST /v1/appScreenshots` (or `/v1/appPreviews`) with `{fileName, fileSize}` + a
   relationship to the set. The response returns the asset id and an `uploadOperations` array.
2. **Upload** — for each operation, `PUT` the byte range `[offset, offset+length)` of the file to its
   pre-signed `url`, applying every `requestHeaders` entry.
3. **Commit** — `PATCH …/<id>` with `{uploaded: true, sourceFileChecksum: <md5-hex-of-the-whole-file>}`,
   then poll `assetDeliveryState` (→ `COMPLETE`, or `FAILED` with a `code`).
4. **Order** — assets display in insertion order; to set it explicitly (or reorder later), `PATCH
   /v1/appScreenshotSets/<id>/relationships/appScreenshots` (or `appPreviewSets/<id>/relationships/appPreviews`)
   with the ordered id list as the `data` array. Returns `204 No Content` (no JSON body).

**Gotchas that fail validation:**

- **No `APP_IPHONE_69`.** 6.9" assets (1320×2868) upload under **`APP_IPHONE_67`** — Apple's 6.7"/6.9"
  class shares one display type (preview `previewType` is `IPHONE_67`, sans `APP_`). Upload the largest
  class; the smaller iPhone classes auto-scale.
- **App previews need a stereo audio track even when silent** — no audio fails with `MOV_RESAVE_STEREO`.
  Mux a silent stereo AAC track.
- **App previews must be ≥ 15 s** — shorter fails with `MOV_RESAVE_LONGER` (Apple's range is 15–30 s).
- **`sourceFileChecksum` is the MD5 of the whole original file**, not per-chunk; commit fails on a mismatch.
- Set a preview poster with `PATCH /v1/appPreviews/<id>` `previewFrameTimeCode` (`"HH:MM:SS:FF"`, e.g.
  `"00:00:02:00"`); it otherwise defaults to the 5 s mark.

The **marketing app icon is NOT settable via the API** — it's extracted from the uploaded build's asset
catalog (default appearance); there's no `AppStoreVersion` icon relationship. (Showing a *dark* icon on the
listing isn't possible either without making the dark art the build's default appearance.)

## Useful endpoints

| Goal | Endpoint |
|------|----------|
| Latest build + processing state | `GET /v1/builds?filter[app]=<id>&sort=-uploadedDate&limit=1` (build `version` is a string — sort by date, not `-version`) |
| The version being prepared | `GET /v1/apps/<id>/appStoreVersions?filter[appVersionState]=PREPARE_FOR_SUBMISSION` (`appStoreState` is deprecated) |
| Read / write listing copy | `GET` / `PATCH /v1/appStoreVersionLocalizations/<id>` (description, keywords, promo, URLs) |
| Attach the selected build | `PATCH /v1/appStoreVersions/<id>/relationships/build` |
| Upload screenshots / previews | `appScreenshotSets`/`appPreviewSets` + `appScreenshots`/`appPreviews` (reserve → `PUT` → commit; see above) |
| Order a media set | `PATCH /v1/appScreenshotSets/<id>/relationships/appScreenshots` (or `appPreviewSets/.../appPreviews`) with the ordered id list |
| Submit for review | `POST /v1/reviewSubmissions` + `reviewSubmissionItems` (a new app's first IAP rides along as its own item), then mark it submitted |
| Read a submission's state | `GET /v1/reviewSubmissions?filter[app]=<id>&include=items` — `reviewSubmissionItems` blocks `GET_INSTANCE`, so read items via the `include`, not by id |
| Set App Review notes | `PATCH /v1/appStoreReviewDetails/<id>` `{attributes:{notes}}` — the record pre-exists once the review contact is set (`asc-set-review-notes.swift`) |

Full schema: Apple's [App Store Connect API reference](https://developer.apple.com/documentation/appstoreconnectapi).

## Verify the submission landed

After `POST /v1/reviewSubmissions` (+ items) and marking it submitted, confirm it actually queued — the
console can lag, and a first IAP can silently fail to attach:

- **Submission state** — `GET /v1/reviewSubmissions?filter[app]=<id>&include=items&limit=1`. A queued
  submission reads `state: WAITING_FOR_REVIEW` with its item(s) `READY_FOR_REVIEW`. Gotcha:
  `reviewSubmissionItems` does **not** allow `GET_INSTANCE` — fetching one by id returns
  `403 FORBIDDEN_ERROR` ("Allowed operations are: CREATE, DELETE, UPDATE"), so read items through the
  submission's `items` relationship / `include`, never by id.
- **Confirm the IAP rode along** — a new app's first in-app purchase reviews *with* the app, but the
  version↔IAP selection isn't exposed by the API and only materializes in the submission. The reliable
  signal is the IAP's own state: `GET /v2/inAppPurchases/<id>` flips `READY_TO_SUBMIT` →
  `WAITING_FOR_REVIEW` (→ `APPROVED`) once it's attached. If it's still `READY_TO_SUBMIT` after you
  submit, it did **not** ride along — re-check the version's *In-App Purchases* selection and resubmit.

## Scope — what stays console-bound

The API covers builds, metadata, screenshots, pricing, IAP, TestFlight, and version submission. A few
one-time, account-level steps stay in the web console: the **age-rating questionnaire**, **EU DSA trader
status**, the **App Privacy** questionnaire, and agreements / banking. Do those once in the console;
script the rest.
