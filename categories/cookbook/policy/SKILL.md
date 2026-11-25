---
name: policy
description: >
  Run a pre-launch legal and policy audit over an app or website codebase:
  privacy/terms/cookie/refund policies matched against what the code
  actually does, consent and data discipline, honesty in marketing and
  pricing, accessibility basics, and asset rights — audit first, then fix
  one item at a time. Use before first public launch, before adding
  payments or marketing campaigns, or when inheriting a codebase whose
  policy pages were never checked against reality.
license: MIT
---

# Policy — pre-launch legal & policy audit

A structured audit an agent runs over an app or website codebase before
launch (or before a major release) to find the policy, consent, honesty,
and accessibility gaps that most often create legal exposure for small
products. It produces a fix list with evidence, then applies fixes one at
a time.

This skill is **not legal advice**. It is an educational checklist. Which
laws apply depends on where the operator and the users are, and laws
change. Anything the audit flags as uncertain goes on a "take to a lawyer"
list instead of being guessed at.

## When to use it

- Before first public launch of an app, SaaS, or marketing site.
- Before adding payments, subscriptions, marketing email/SMS, or user accounts.
- When inheriting a vibe-coded codebase whose policy pages were never checked against what the code actually does.

## Workflow

### 1. Audit first, change nothing

Read the codebase and the live pages. For every checklist item below, record one of: **done**, **needs work**, or **doesn't apply**, with the file and line (or URL) that proves it. Do not edit anything during the audit pass.

### 2. Policies that match reality

- A privacy policy exists and matches what the product actually collects, why, and who receives it (analytics, AI APIs, email, payments, crash reporting). Name every third party that receives user data.
- Terms of service exist and describe the real offer: what is sold, limits, refunds, termination.
- Refund and cookie policies exist where money or cookies are involved.
- Every policy page is reachable from the product (footer, settings, signup), not orphaned.

### 3. Consent and data discipline

- Forms ask only for data the feature needs; optional fields are marked optional.
- Marketing email has a working unsubscribe link, and opt-outs are honoured.
- Marketing texts or push campaigns are sent only with recorded consent.
- Cookie consent is obtained before non-essential cookies or trackers fire.
- Third-party SDKs are inventoried: what each collects, where it sends it, and whether the privacy policy says so.
- Users can delete their account and their data from inside the product, and deletion actually removes stored files, not just the database row.
- Children: if the product can attract under-age users, there is an age gate and a parental-consent path, or the terms exclude them and the product enforces it.

### 4. Honesty in marketing and pricing

- No fake or AI-generated reviews, testimonials, ratings, or user counts.
- Every public claim (performance, savings, "AI-powered", comparisons) can be backed by evidence the operator holds.
- Prices show the full amount; no hidden fees appear late in checkout.
- Subscriptions are as easy to cancel as to start; free trials that convert to paid say so before signup and remind before charging.
- No dark patterns: no pre-ticked boxes, disguised ads, forced continuity, or confirm-shaming.

### 5. Accessibility basics

- Images carry meaningful alt text; decorative images are marked decorative.
- Text contrast meets WCAG AA (4.5:1 for body text).
- Every interactive element is reachable and operable by keyboard, with a visible focus state.
- Forms have real labels, not placeholder-only labels.

### 6. Business identity and asset rights

- The site names the real operator: business name, contact route, and jurisdiction where required.
- Every image, font, icon, and audio asset is licensed for this use, and the licence is recorded somewhere retrievable.
- The product name and logo have at least a basic trademark sanity check (search the name in the target market before launch).

### 7. Report, then fix in small commits

Present the audit as a table: item, status, evidence, suggested fix. Then fix one item per commit so each change is reviewable and revertible. Re-run the audit after fixes and report what remains open, including the "take to a lawyer" list.

## Output rules

- Never invent a penalty figure, a statute, or a deadline. If a number is cited, it must come from a source read during the audit; otherwise describe the risk qualitatively.
- Never write policy text that contradicts the code. If the code collects something the policy omits, fix the policy or the code — and say which.
- Flag jurisdiction explicitly: "this item matters under GDPR / CCPA / CAN-SPAM / app-store rules" only when that regime plausibly applies to the operator's users; otherwise mark it doesn't apply and say why.
- Keep the final report short enough to act on: blockers first, polish last.
