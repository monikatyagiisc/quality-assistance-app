# Checkout Smoke Test PR Fixture

Use this scenario to test the Quality Assistance GitHub pull-request and diff-import workflow. It is test input, not a description of checkout code implemented in this repository.

## Requirements

E-commerce checkout service (REST API + React UI).

- Cart supports coupons (percentage and fixed amount).
- Payment via card only; 3-D Secure for orders over ₹5000.
- Order confirmation email within 60 seconds.
- Inventory reserved for 15 minutes during checkout.

## Latest test run

Suite: `checkout-smoke` (staging-v2.4.1, build 1842)

- TC-101 Apply valid coupon — PASS (2.1s)
- TC-102 Apply expired coupon — FAIL: expected 400, got 200
- TC-103 Payment 3DS challenge — SKIP: sandbox certificate expired
- TC-104 Order confirmation email — FAIL: timeout after 90s
- TC-105 Inventory release job — PASS (0.8s)

## UI and code-change context

- The Playwright coupon-field locator changed from `#coupon-input` to `[data-testid="coupon-code"]`.
- The payment iframe selector is flaky.

## Quality-assistance request

Cover every STLC area and name the responsible specialist for each section:

1. Test cases
2. Test data
3. Test automation approach
4. Analysis of the test run above
5. Self-healing for the broken locators
6. Impact of the code difference
7. A bug report for each failed test
8. A short test summary for stakeholders
9. A release-readiness verdict
