# Automate App Store Connect with an API key (no fastlane)

The App Store Connect **API** is a REST API over almost everything in the console — builds, app
metadata, screenshots, pricing, in-app purchases, TestFlight, and **submitting a version for review**.
You can drive it from the CLI (or an agent / CI) without fastlane. *As of 2026-06; trust the current docs.*

## The key, and the `.env` pattern

Generate the key once: **App Store Connect → Users and Access → Integrations → App Store Connect API**
(role **App Manager** for submission, or **Admin**). Download `AuthKey_<KEYID>.p8` **once** (it can't be
re-downloaded). You get three things:

- **Key ID** — short, e.g. `ABC123XYZ`. The `.p8` must be named `AuthKey_<KEYID>.p8`.
- **Issuer ID** — a UUID at the top of the Integrations page.
- the **`.p8`** private key file — the only real secret.

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
// node check-build.mjs   (env loaded from .env)
import { readFileSync } from "node:fs";
import jwt from "jsonwebtoken";        // npm i jsonwebtoken
const { ASC_KEY_ID, ASC_ISSUER_ID, API_PRIVATE_KEYS_DIR, ASC_APP_ID } = process.env;
const key = readFileSync(`${API_PRIVATE_KEYS_DIR}/AuthKey_${ASC_KEY_ID}.p8`);
const token = jwt.sign({ aud: "appstoreconnect-v1" }, key, {
  algorithm: "ES256", keyid: ASC_KEY_ID, issuer: ASC_ISSUER_ID, expiresIn: "20m",
});
const r = await fetch(
  `https://api.appstoreconnect.apple.com/v1/builds?filter[app]=${ASC_APP_ID}` +
  `&sort=-version&limit=1&fields[builds]=version,processingState,uploadedDate`,
  { headers: { Authorization: `Bearer ${token}` } });
const b = (await r.json()).data?.[0]?.attributes;
console.log(b ? `build ${b.version}: ${b.processingState}` : "no builds");
```

`processingState` is `PROCESSING` → `VALID` (then selectable on the version page) or `FAILED` / `INVALID`.

## Useful endpoints

| Goal | Endpoint |
|------|----------|
| Latest build + processing state | `GET /v1/builds?filter[app]=<id>&sort=-version&limit=1` |
| The version being prepared | `GET /v1/apps/<id>/appStoreVersions?filter[appStoreState]=PREPARE_FOR_SUBMISSION` |
| Read / write listing copy | `GET` / `PATCH /v1/appStoreVersionLocalizations/<id>` (description, keywords, promo, URLs) |
| Attach the selected build | `PATCH /v1/appStoreVersions/<id>/relationships/build` |
| Submit for review | `POST /v1/reviewSubmissions` + `reviewSubmissionItems`, then mark it submitted |

Full schema: Apple's [App Store Connect API reference](https://developer.apple.com/documentation/appstoreconnectapi).

## Scope — what stays console-bound

The API covers builds, metadata, screenshots, pricing, IAP, TestFlight, and version submission. A few
one-time, account-level steps stay in the web console: the **age-rating questionnaire**, **EU DSA trader
status**, the **App Privacy** questionnaire, and agreements / banking. Do those once in the console;
script the rest.
