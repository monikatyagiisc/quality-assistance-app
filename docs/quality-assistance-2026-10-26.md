**Prioritized Test Cases** *(High → Low)*  

| Priority | Test Case ID | Description | Acceptance Criteria |
|----------|--------------|-------------|----------------------|
| **P1** | TC‑PR‑001 | Verify password‑reset request email is sent to the registered address. | Email received within ≤ 5 s; contains a valid reset link. |
| **P1** | TC‑PR‑002 | Validate reset link expires after 24 hours. | Link returns “expired” error after 24 h; works before expiry. |
| **P1** | TC‑PR‑003 | Enforce new‑password rules (≥ 12 chars, ≥ 1 digit, ≥ 1 symbol). | System rejects passwords not meeting each rule with appropriate message. |
| **P2** | TC‑PR‑004 | Ensure account lock after 5 consecutive failed login attempts. | Account is locked on the 5th failure; unlocks only after admin action or defined policy. |
| **P2** | TC‑PR‑005 | Confirm that a locked account cannot use the reset flow to bypass lockout. | Reset link works, but after setting a new password the account remains locked until unlock procedure. |
| **P3** | TC‑PR‑006 | Verify that multiple reset requests within 24 h generate distinct, single‑use links. | Only the most recent link works; previous links are invalidated. |
| **P3** | TC‑PR‑007 | Test rate‑limiting on reset‑request endpoint (e.g., ≤ 5 requests/min per user). | Excess requests receive “too many requests” response. |
| **P4** | TC‑PR‑008 | Verify UI/UX: error messages are clear, accessible, and do not leak sensitive info. | Messages follow WCAG AA contrast; no email addresses disclosed in errors. |
| **P4** | TC‑PR‑009 | Validate that password reset works on all supported browsers/devices. | Successful flow on Chrome, Firefox, Safari, Edge, iOS, Android. |

---

**Suggested Test Data**  

| Data Type | Examples |
|-----------|----------|
| **Valid Emails** | `user@example.com`, `test.user+reset@domain.co.uk` |
| **Invalid Emails** | `user@`, `@example.com`, `user@@example.com` |
| **Reset Links** | `<BASE_URL>/reset?token=abc123` (valid, <24 h) ; same token after 24 h (expired) |
| **Passwords – Valid** | `StrongPass!1A`, `My$ecretPwd2023`, `A1b2c3d4e5!@` |
| **Passwords – Invalid** | `short1!` ( <12 ), `NoNumber!@#` , `NoSymbol12345` , `123456789012` (no symbol) |
| **Failed Login Attempts** | Correct password: `ValidPass!1`; Incorrect passwords: `Wrong1!`, `Wrong2!`, … (repeat 5 times) |
| **Rate‑Limit Tests** | 6 rapid reset requests from same IP/user within 60 s. |

---

**Automation Notes**  

- **Framework**: Use Selenium / Playwright for UI flows; Postman/Newman or REST‑Assured for API verification of reset‑link generation and expiry.  
- **Data‑Driven Tests**: Parameterize password inputs and email addresses from a CSV/JSON file (covers valid/invalid combos).  
- **Time‑Travel**: Mock server time or use a test‑environment clock‑offset to simulate 24‑hour expiry without waiting.  
- **Security**: Include OWASP ZAP scans on the reset endpoint to detect information leakage.  
- **CI Integration**: Run critical P1 cases on every PR; full suite (P1‑P4) on nightly builds.  
- **Self‑Healing**: Tag UI selectors with stable data‑attributes (`data-test-id`) to reduce flakiness when UI changes.  

---

**Release Risks**  

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Expired‑Link Handling** – Users may receive “link expired” after 24 h without clear guidance. | Customer support tickets, churn. | Provide friendly UI with “request new link” button; include expiry countdown in email. |
| **Password‑Policy Bypass** – Weak passwords accepted due to regex errors. | Security breach. | Enforce server‑side validation; add unit tests for regex edge cases. |
| **Account‑Lock Bypass via Reset** – Resetting password could unintentionally unlock the account. | Unauthorized access. | Ensure lock status persists post‑reset; add regression test (TC‑PR‑005). |
| **Email Delivery Failure** – Reset email not delivered (spam filters). | Users unable to recover access. | Use DKIM/SPF, monitor bounce rates, implement fallback SMS option. |
| **Rate‑Limit Bypass** – Attackers flood reset endpoint. | Denial‑of‑service, credential‑stuffing. | Implement CAPTCHA after N attempts; monitor throttling logs. |
| **Cross‑Browser Incompatibility** – UI elements misaligned on mobile. | Poor user experience. | Run automated visual regression on major browsers/devices before release. |

--- 

*All items are ready for hand‑off to test‑case generation, test‑data generation, automation scripting, and release‑readiness evaluation as needed.*