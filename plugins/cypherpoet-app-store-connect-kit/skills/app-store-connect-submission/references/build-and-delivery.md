# Build & deliver the archive

Two ways to get a build into App Store Connect. *As of 2026-06; trust the screen.* Both land the build in
ASC → TestFlight → Builds; the version-page steps afterward are identical. Pick one.

After either path, the build shows as **Processing** for a while; it isn't selectable on the version page
until processing finishes.

---

## Path A — Local archive (Xcode)

1. **Scheme**: select the app scheme (not a test scheme).
2. **Destination**: **Any iOS Device (arm64)**. (Archive is greyed out if a simulator is selected.)
3. **Signing**: select the app target → **Signing & Capabilities** → **Automatically manage signing** on,
   and a **Team** selected. ⚠️ **The most common local-archive failure is an unsigned archive because
   `DEVELOPMENT_TEAM` isn't pinned.** If the project was created "without a team," set the Team on **every**
   target here.
4. **Product → Archive.** On success the **Organizer** opens to the new archive.
5. **Distribute App → App Store Connect → Upload.** Accept automatic signing — Xcode mints the Apple
   Distribution cert + App Store provisioning profile (cloud-managed). Wait for **"Upload Complete."**
   - Alternative: **Distribute → Export** the `.ipa`, then upload with the **Transporter** app.
6. No export-compliance prompt appears if `ITSAppUsesNonExemptEncryption = NO` is set.

---

## Path B — Xcode Cloud

Xcode Cloud is Apple's CI. A **workflow** defines *when* it runs (start condition), *what* it does
(actions: build / test / **archive**), and post-actions. Builds run on Apple's servers with
**cloud-managed signing** — no local certificate or Team setup. You reach it all from Xcode's **Integrate**
menu, and from **ASC → your app → Xcode Cloud**.

### One-time setup (and the traps)

- **Accept Xcode Cloud terms** (first use) — the **Account Holder** must agree, in App Store Connect. Until
  then, no workflow can be created.
- **Grant source access.** Xcode Cloud clones your repo, so it needs access to it (e.g. installing the
  Xcode Cloud GitHub App on the repository — explicitly granting a **private** repo). The Save step in the
  workflow editor walks you through a browser grant; complete it and you'll see green checkmarks.
- ⚠️ **"Manage Workflows" greyed out / no workflow appears** almost always means one of the two grants above
  isn't finished — *not* that your workflow is wrong. Xcode's menu also caches: even after a workflow exists
  server-side, the menu can lag. **ASC → your app → Xcode Cloud** is the source of truth; quit/reopen Xcode
  if the menu is stale. Use `Integrate → Create Workflow…` to (re)launch setup; `Start Build` lives inside
  Manage Workflows / the Report navigator's **Cloud** tab, not as a top-level menu item.

### Configure the workflow

In the workflow editor the app is already scoped by the **Primary Repository** + **Project** — there's no
"product" field. The thing that matters:

- ⚠️ **Add an Archive action.** A fresh workflow's **Actions** list is often empty (build/test only), which
  delivers nothing. **＋ → Archive**, set the **scheme**, and set:
- ⚠️ **Distribution Preparation = "App Store Connect."** This is the value that makes the build submittable.
  ("None" delivers nothing; "TestFlight (Internal Testing Only)" can't reach the App Store. Apple's docs
  sometimes call the App Store option "TestFlight and App Store" — same thing; the current Xcode UI labels
  it "App Store Connect.")
- **Start Conditions** default to **Branch Changes** (every push). Restrict to your **release branch** (or a
  `release/*` tag), or rely on manual **Start Build** — otherwise feature branches trigger release builds.
- **Post-Actions** (TestFlight distribution) are optional; the Archive action with "App Store Connect"
  already delivers the build to ASC.

### Signing & the git-remote gotcha

Cloud signing manages the distribution certificate for you (you need an **Admin / Account Holder** role, or
a granted distribution-cert permission). But Xcode Cloud builds the **git remote**, not your working copy:

- ⚠️ If the project needs a `DEVELOPMENT_TEAM` set (the same gap as Path A), set the Team on every target,
  then **commit and push** that change to the branch the workflow builds. A local-only edit does nothing.
- Always build the **release branch**, not a feature/worktree branch, or you'll submit the wrong code.

### Where builds land, and cost

A successful Archive-with-"App Store Connect" workflow delivers to **ASC → TestFlight → Builds**
(Processing → ready), exactly like a local upload. Watch progress in Xcode's **Report navigator → Cloud**
tab (⌘9) or in ASC. The Developer Program includes **25 compute hours/month** free (test actions count too).
