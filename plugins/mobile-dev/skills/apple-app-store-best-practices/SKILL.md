---
name: apple-app-store-best-practices
description: >
  Audit Apple-platform apps against the official App Store Review Guidelines — a
  prioritized risk register with section citations, code evidence, and
  remediation — plus metadata/ASO, screenshot strategy, and review management.
  Use before submitting, after a rejection, when adding IAP, subscriptions,
  auth, UGC, or data collection, or when optimizing a listing. Triggers on "App
  Review", "rejection", "guideline", "ASO", and quick questions like "do I need
  Sign in with Apple?" or "will this pass review?".
---

# Apple App Store Best Practices

*Last synced with Apple guidelines: 2026-07-17*

Comprehensive guide for Apple App Store success: compliance auditing against all 5 sections of the [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) with exact section citations and actionable remediation, plus metadata optimization, screenshot strategy, review management, and localization best practices.

This file routes; the depth lives in `references/`. Load files selectively based on the app's features — don't load everything upfront.

## Reference Files

| File | When to load |
|------|-------------|
| `common-rejection-patterns.md` | **Always load first** — triage checklist of top rejection reasons |
| `audit-workflow.md` | Running an audit — the full Phase 1–6 process + post-rejection workflow |
| `output-format.md` | Producing the deliverables — the 6-part report + severity scale |
| `section-1-safety.md` | App has UGC, targets kids, has health/medical features, or handles sensitive content |
| `section-2-performance.md` | Always load for full audits — covers completeness, metadata, software requirements |
| `section-3-business.md` | App has any monetization: IAP, subscriptions, physical goods, ads, crypto |
| `section-4-design.md` | App has login/auth, extensions, push notifications, Apple Music, or mini-apps |
| `section-5-legal.md` | App collects any user data, uses location, has health features, or targets kids |
| `listing-optimization.md` | Optimizing the listing — metadata/ASO, screenshots, reviews, localization |
| `app-accessibility.md` | Setting the App Store Connect **App Accessibility** declarations (Accessibility Nutrition Labels) — what to declare vs. skip, and the verify-before-declare rule |
| `reviewer-notes-template.md` | When generating the Draft App Review Notes deliverable |

## Audit Workflow

A full audit runs six phases — reconnaissance → technical → business → safety → design/metadata → legal — detailed in [references/audit-workflow.md](references/audit-workflow.md). **Phase 1 (reconnaissance)** scans the app's features and decides which `section-*.md` references to load; the later phases check the codebase and metadata against each guideline section. Produce the results with the 6-part report and severity scale in [references/output-format.md](references/output-format.md). For a rejected app, jump to the Post-Rejection Workflow in the workflow file.

## Adaptive Depth

Scale the audit based on app complexity:

**Quick audit** (simple utility, no accounts/payments):
Phase 1 + Phase 2 + Phase 6, plus metadata spot-check. Load only `common-rejection-patterns.md`.

**Standard audit** (app with accounts, payments, or data collection):
All 6 phases. Load relevant section references based on Phase 1 findings.

**Deep audit** (UGC, kids, health data, complex subscriptions, multiple platforms):
All 6 phases with full reference loading. Flag ambiguous cases for human review. Cross-reference between sections for compound risks (e.g., kids + UGC triggers both §1.2 and §5.1.4).

## Development-Time Reference

For targeted questions during development (not full audits), map the task to guideline sections:

| Task | Load | Check |
|------|------|-------|
| Adding IAP/subscriptions | `section-3-business.md` | §3.1.1, §3.1.2 |
| Adding user authentication | `section-4-design.md`, `section-5-legal.md` | §4.8, §5.1.1(v) |
| Adding data collection | `section-5-legal.md` | §5.1.1, §5.1.2 |
| Adding UGC features | `section-1-safety.md` | §1.2 (all 4 requirements) |
| Targeting Kids Category | `section-1-safety.md`, `section-5-legal.md` | §1.3, §5.1.4 |
| Adding push notifications | `section-4-design.md` | §4.5.4 |
| Adding health features | `section-5-legal.md` | §5.1.3 |
| Adding crypto features | `section-3-business.md` | §3.1.5 |
| Adding extensions | `section-4-design.md` | §4.4 |
| Adding Apple Music | `section-4-design.md` | §4.5.2 |

## Listing Optimization (Beyond Compliance)

Metadata/ASO, screenshot & app-preview strategy, review/rating management, and localization — the discoverability and conversion side of the listing — live in [references/listing-optimization.md](references/listing-optimization.md). For exact screenshot specs and capture automation, the **`apple-app-store-screenshots`** skill ships with this plugin.
