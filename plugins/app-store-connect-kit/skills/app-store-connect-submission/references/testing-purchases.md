# Testing in-app purchases

Two environments, for two different jobs. *As of 2026-06; trust the screen.*

> This is about **manually exercising the purchase flow** for submission confidence. Writing the StoreKit
> purchase/restore *code* is the `storekit` skill's job.

## Which one do you need?

| | **Local `.storekit` config** | **Sandbox** |
|---|---|---|
| Runs on | Simulator or device, **no Apple servers** | Real device (simulator is flaky), **real Apple servers** |
| Needs | Just the Xcode scheme | A sandbox tester + active Paid Apps Agreement |
| Proves | Your app's purchase **UX + logic** | The **live pipeline** end-to-end |
| Catches ASC misconfig? | **No** — it always "works" because you author it | **Yes** |

The local config is the fast, device-free way to *see* the flow; automated StoreKit unit tests
(`SKTestSession`) usually already cover the buy→entitlement logic. **Sandbox is the only pre-submission
check of the real pipeline** — but it's **recommended, not a submission gate.** If you skip it, at minimum
confirm **Business → Agreements → Paid Apps = Active** (the highest-probability pipeline failure).

---

## Local `.storekit` testing (no device, no sandbox account)

1. Xcode → **Product → Scheme → Edit Scheme → Run → Options → StoreKit Configuration** → select your
   `.storekit` file. *(This is the opposite of the Sandbox setup, where you set it to **None**.)*
2. Run on any simulator → open the paywall → the product + price load from the file → tap Buy → a simulated
   sheet (no real auth, no charge) → confirm → verify the unlock applies.
3. **Restore**: tap Restore → the unlock returns.
4. **Re-test / manage**: while running, open Xcode's **StoreKit Transaction Manager**
   (Debug → StoreKit → Manage Transactions…) to delete/refund a transaction so you can buy again, or to
   simulate failures and Ask to Buy.

Because you author the `.storekit` file, this passes regardless of your App Store Connect setup — great for
flow/UX, useless for verifying the live pipeline.

---

## Sandbox testing (real pipeline, real device)

### One-time setup — and the traps

1. **Paid Apps Agreement = Active.** If it isn't, products never load — the #1 cause of an empty paywall.
2. **Create a sandbox tester.** ASC → **Users and Access** (top-level, *not* inside the app — reach it via
   the App Store Connect logo / [direct link](https://appstoreconnect.apple.com/access/users)) → **Sandbox**
   tab → **＋**.
   - ⚠️ **Email trap:** the address must not already be an Apple ID — **and iCloud plus-aliases are
     rejected**, because Apple resolves `you+x@icloud.com` back to your real `you@icloud.com` Apple ID. Use a
     **non-iCloud** address, e.g. a **Gmail plus-alias** (`you+sbx1@gmail.com`) — Apple treats it as a brand
     new email and it still reaches your inbox.
3. **Point the app at real Sandbox, not the local file.** Edit Scheme → Run → Options → **StoreKit
   Configuration → None.** (Left on the `.storekit` file, you're testing a local simulation, never Sandbox.)
4. ⚠️ **Don't fight the Settings sign-in.** A sandbox tester is **not** a real Apple ID; entering it in
   Settings → [your name]/iCloud or the App Store gives *"Apple Account is incorrect."* Two correct options:
   - **Simplest — sign in at checkout:** leave your real Apple ID in iCloud, run the app, tap Buy, and enter
     the tester in the purchase sheet (marked **[Environment: Sandbox]**) right there.
   - **Pre-sign-in:** Settings → **Developer → Sandbox Apple Account** — the *only* Settings field that
     accepts a sandbox account. (No Developer menu? enable it via Settings → Privacy & Security → Developer
     Mode, or run a dev build on the device once.)

### The test

1. Build & run on the device → open the paywall → the product + price render.
2. Tap Buy → sandbox sheet → authenticate as the tester → confirm. No real charge.
3. Verify the unlock/entitlement applies.
4. **Restore**: delete + reinstall the app (locked again) → Restore Purchases → authenticate → the unlock
   returns. Test any in-Settings Restore button too.

### Troubleshooting

- **Empty paywall / "product unavailable"** (likeliest first): Paid Apps Agreement not Active → ASC IAP
  metadata still propagating to Sandbox (can take hours after *Ready to Submit*) → scheme still on the local
  `.storekit` file. Verify the **product ID in code matches ASC exactly** before suspecting anything exotic.
- **To buy again:** a non-consumable stays "owned" by the tester. Re-test via Users and Access → Sandbox →
  your tester → **Clear Purchase History**, or make a new tester.
- `AppStore.sync()` (the StoreKit 2 restore) prompts for sandbox auth — expected, not a bug.
