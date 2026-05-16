export type AssistanceSample = {
  id: string
  title: string
  description: string
  focus: string
  requirements: string
  userStories: string
  codeDiffs: string
  requiresSession?: boolean
}

export const ASSISTANCE_SAMPLES: AssistanceSample[] = [
  {
    id: 'smoke',
    title: 'Smoke test',
    description: 'Minimal input to verify planning agents and requirements summarization.',
    focus: 'S01, S02 · summarize_requirements',
    requirements: `Build a password reset flow for a web app.
- User requests reset via email
- Link expires after 24 hours
- New password must be at least 12 characters with one number and one symbol
- Account is locked after 5 failed login attempts`,
    userStories: '',
    codeDiffs: '',
  },
  {
    id: 'full-e2e',
    title: 'Full E2E demo',
    description: 'Requirements, user stories, and a code diff — best end-to-end showcase.',
    focus: 'S01–S03, S06, S09',
    requirements: `E-commerce checkout service (REST API + React UI).
- Cart supports coupons (percentage and fixed amount)
- Payment via card only; 3-D Secure for orders over ₹5000
- Order confirmation email within 60 seconds
- Inventory reserved for 15 minutes during checkout
- Audit log for every price change on a line item`,
    userStories: `As a shopper, I want to apply a coupon at checkout so that I get a discount on my order.
As a shopper, I want to see why my coupon was rejected so that I can fix the code or choose another.
As an admin, I want to void an order within 1 hour of placement so that mistaken orders can be cancelled before fulfillment.`,
    codeDiffs: `diff --git a/src/payment/coupon.py b/src/payment/coupon.py
--- a/src/payment/coupon.py
+++ b/src/payment/coupon.py
@@ -42,7 +42,12 @@ def apply_coupon(cart, code: str) -> Cart:
-    discount = coupon.percent_off * cart.subtotal
+    if coupon.max_discount and discount > coupon.max_discount:
+        discount = coupon.max_discount
+    if cart.subtotal - discount < 0:
+        raise CouponError("Discount exceeds subtotal")
     cart.total = cart.subtotal - discount
     return cart`,
  },
  {
    id: 'change-impact',
    title: 'Change impact',
    description: 'Diff-heavy input to stress regression and impact analysis.',
    focus: 'S06 · change impact',
    requirements: `Existing login API: POST /auth/login returns JWT. Rate limit: 10 req/min per IP.`,
    userStories: '',
    codeDiffs: `diff --git a/auth/login.py b/auth/login.py
-    if user.failed_attempts >= 5:
-        raise AccountLocked()
+    if user.failed_attempts >= 5 and not user.lock_expired():
+        raise AccountLocked(until=user.locked_until)
+    if verify_mfa(user, payload.totp):
+        return issue_token(user)`,
  },
  {
    id: 'execution-reporting',
    title: 'Execution & reporting',
    description: 'Paste-style test run log for execution, bugs, and release readiness.',
    focus: 'S04, S07, S08, S09',
    requirements: `Analyze this test run and suggest next steps:

Suite: checkout-smoke (staging)
- TC-101 Apply valid coupon ........ PASS (2.1s)
- TC-102 Apply expired coupon ...... FAIL — expected 400, got 200
- TC-103 Payment 3DS challenge ..... SKIP — sandbox cert expired
- TC-104 Order confirmation email .. FAIL — timeout after 90s
- TC-105 Inventory release job ..... PASS (0.8s)

Environment: staging-v2.4.1, build 1842, 2026-05-17`,
    userStories: '',
    codeDiffs: '',
  },
  {
    id: 'automation',
    title: 'Automation & self-healing',
    description: 'Playwright maintenance and CI smoke-test planning.',
    focus: 'S03, S05',
    requirements: `We automate checkout with Playwright (TypeScript). After UI refresh, the login button id changed from #btn-login to [data-testid="sign-in"]. Payment iframe selector is flaky. Need maintainable automation approach and healing strategy.`,
    userStories: `As a QA engineer, I want smoke tests to run in CI on every PR so regressions are caught early.`,
    codeDiffs: '',
  },
  {
    id: 'follow-up',
    title: 'Follow-up (same session)',
    description: 'Run after another sample succeeds — keeps session_id for multi-turn context.',
    focus: 'Multi-turn session',
    requiresSession: true,
    requirements: `Based on your previous answer, list only P1 test cases and one negative test per feature. Use a table with ID, title, priority.`,
    userStories: '',
    codeDiffs: '',
  },
]
