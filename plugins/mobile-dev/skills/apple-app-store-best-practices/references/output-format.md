# Audit Output Format

The deliverables and severity scale an [apple-app-store-best-practices](../SKILL.md) audit produces.

## Output Format

Produce these 6 deliverables:

### 1. Executive Summary

5-10 bullets covering: app purpose, top risks, submission verdict.

**Verdict:** `READY` / `CONDITIONAL` (minor fixes needed) / `NOT READY` (blockers exist)

### 2. Risk Register

| Priority | Guideline | Area | Finding | Evidence | Remediation | Effort | Confidence |
|----------|-----------|------|---------|----------|-------------|--------|------------|
| P0 | §3.1.1 | Payments | Digital content unlocked via external payment | `PurchaseManager.swift:47` — Stripe checkout for premium features | Migrate to StoreKit IAP | L | HIGH |

- **Priority:** P0 (blocker), P1 (high risk), P2 (medium), P3 (low/polish)
- **Guideline:** Exact section number from the Review Guidelines
- **Area:** Privacy, Payments, Content, Design, Metadata, Technical, Legal
- **Evidence:** File path, function name, configuration entry, or metadata field
- **Confidence:** HIGH (clear violation), MEDIUM (likely violation, interpretation-dependent), LOW (possible issue, reviewer-dependent)

### 3. Detailed Findings

Group findings by area. For each finding:
- The specific guideline section and what it requires
- What the app currently does that may violate it
- Exact evidence (file paths, code snippets, config entries)
- Recommended fix with implementation guidance

### 4. Reviewer Experience Checklist

Walk through the app as a reviewer would:
- [ ] Install and launch — does it load without crashes?
- [ ] First permission prompt — is the purpose string clear?
- [ ] Account creation/login — is Sign in with Apple offered?
- [ ] Core feature walkthrough — do all features work?
- [ ] IAP flows — can purchases be completed in sandbox?
- [ ] External links — do they open correctly?
- [ ] Edge cases — what happens with no network, denied permissions, empty states?

### 5. Draft App Review Notes

Use the template from `references/reviewer-notes-template.md`. Fill in based on what was found during the audit: demo credentials, feature access steps, permission explanations, IAP testing instructions.

### 6. Guideline Coverage Summary

| Section | Applicable | Evaluated | Findings |
|---------|-----------|-----------|----------|
| §1 Safety | Yes/No | Yes/No | Count |
| §2 Performance | Yes/No | Yes/No | Count |
| §3 Business | Yes/No | Yes/No | Count |
| §4 Design | Yes/No | Yes/No | Count |
| §5 Legal | Yes/No | Yes/No | Count |

## Severity Definitions

**P0 — Blocker** (almost certain rejection):
- Missing privacy policy (§5.1.1(i))
- Digital content without IAP (§3.1.1)
- No account deletion when account creation exists (§5.1.1(v))
- App crashes or has placeholder content (§2.1)
- Private API usage (§2.5.1)

**P1 — High Risk** (likely rejection):
- Third-party login without Sign in with Apple (§4.8)
- UGC without all 4 moderation requirements (§1.2)
- Vague permission purpose strings (§5.1.1(ii))
- Unclear subscription pricing (§3.1.2(c))
- Missing ATT prompt when tracking (§5.1.2(i))

**P2 — Medium Risk** (may cause rejection depending on reviewer):
- Screenshots don't reflect current app (§2.3.3)
- Over-requesting permissions (§5.1.1(iii))
- Questionable age rating (§2.3.6)
- Unused background modes declared (§2.5.4)

**P3 — Low Risk / Polish** (unlikely to block but worth fixing):
- Generic "What's New" text (§2.3.12)
- Reviewer notes could be more helpful (§2.1)
- Metadata could be improved (§2.3)
