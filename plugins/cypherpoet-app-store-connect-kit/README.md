# cypherpoet-app-store-connect-kit

The **operational** half of App Store publishing: how to actually get an
Apple-platform app from *built* to **Submitted for Review** in App Store Connect —
the console navigation, the order of operations, build delivery, sandbox testing,
and the UI traps that aren't in Apple's happy-path docs.

It is deliberately scoped to *mechanics*, and hands off the rest to siblings:

| For… | Use |
|------|-----|
| Submission workflow, ASC navigation, build delivery, Xcode Cloud, sandbox setup, submission errors | **this plugin** (`app-store-connect-submission`) |
| Review-guideline compliance, rejection-risk audits, ASO / keyword & metadata optimization | `cypherpoet-mobile-dev` → `apple-app-store-best-practices` |
| Exact screenshot dimensions / app-preview specs | `cypherpoet-apple-app-store-screenshots` |
| Writing IAP / StoreKit purchase & restore code | `storekit` |

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [app-store-connect-submission](skills/app-store-connect-submission/SKILL.md) | Step-by-step submission playbook with a dated gotchas/troubleshooting table. | Yes |
