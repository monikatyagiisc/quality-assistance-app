---
name: stlc-quality-report
description: 'Create a complete STLC quality report with prioritized test cases, test data, automation, run analysis, locator recovery, change impact, bug reports, stakeholder summary, and release verdict. Use when asked for STLC coverage, end-to-end testing analysis, test-run review, or release readiness.'
---

# STLC Quality Report

Produce a structured report covering the relevant Software Testing Life Cycle areas. Use this format when the user requests full STLC coverage or a report like the nine-section checkout example. Keep the sections in the order below and name the responsible specialist using the exact label shown.

## Required sections

1. **Prioritized Test Cases** — `test_case_generation`
2. **Suggested Test Data** — `test_data_generation`
3. **Automation Notes / Approach** — `test_script_automation`
4. **Analysis of the Latest Test Run** — `test_execution`
5. **Self-Healing for Broken Locators** — `self_healing_test_scripts`
6. **Impact of the Code Diff** — `change_impact_analysis`
7. **Bug Reports for Each Failed Test** — `bug_report_generation`
8. **Short Test Summary for Stakeholders** — `test_summary_reporting`
9. **Release-Readiness Verdict** — `release_readiness_evaluation`

Use a numbered heading for each section, with the specialist label in the heading or immediately below it. Prefer concise tables for cases, data, execution results, automation layers, and readiness criteria. Include actionable recommendations where appropriate.

## Evidence and accuracy

- Ground analysis in the supplied requirements, test output, screenshots, and actual code diff. Inspect repository files when available and relevant.
- Separate observed facts from hypotheses and recommendations. Label uncertain root causes as hypotheses; do not present them as confirmed.
- Never invent test outcomes, environment/build details, bug IDs, attachments, implemented fixes, or automation capabilities. Mark unavailable information as **Not provided** or **Not verified**.
- If no code diff or repository is available, state that change impact cannot be confirmed from the provided evidence; do not fabricate changed files or behavior.
- Do not claim a locator is healed, a test is fixed, or a pipeline is integrated unless that work is verified. Distinguish recommended selector strategies from implemented automation.
- Treat skipped tests separately from passes and failures. Do not file a defect for an environmental skip unless there is evidence of a product defect.
- Recalculate totals and pass rates from individual test outcomes; state the denominator and whether skips are excluded.
- Make the release verdict follow the evidence and clearly state blockers, assumptions, and required follow-up. Do not approve a release when a stated release gate fails.

## Section guidance

### 1. Prioritized Test Cases
Provide priority, test ID (if supplied or useful), title, and expected behavior. Cover the principal user and business risks before edge and non-functional cases. Do not invent unsupported product requirements.

### 2. Suggested Test Data
List representative valid, invalid, boundary, and time-dependent data as relevant. Mark examples as proposed fixtures, not existing application data.

### 3. Automation Notes / Approach
Map test layers to suitable tools and assertions. Tie each recommendation to the supplied system and avoid presenting illustrative commands or selectors as verified production code.

### 4. Analysis of the Latest Test Run
Summarize each supplied test's expected and actual result. Identify confirmed observations separately from possible causes. Include accurately calculated totals and pass rate.

### 5. Self-Healing for Broken Locators
Recommend robust, accessible selectors first (for example, role/name or stable test IDs), and explain how to validate them. Avoid brittle selector fallbacks or retries that can hide real failures. Treat iframe selectors according to the actual provider and available DOM details.

### 6. Impact of the Code Diff
For each relevant change, describe affected behavior and focused regression coverage. If the diff is absent, say so and provide only a conditional checklist.

### 7. Bug Reports for Each Failed Test
Create one report per confirmed failed test, with title, severity and rationale, reproduction steps, expected/actual results, environment, and evidence. Mark missing fields rather than guessing. Do not turn skipped tests into bugs without supporting evidence.

### 8. Short Test Summary for Stakeholders
Report scope, results, material risks, skips/dependencies, and next actions in plain language. Ensure numbers match section 4.

### 9. Release-Readiness Verdict
Use a readiness table with criterion, status, and rationale, followed by a clear **SHIP**, **DO NOT SHIP**, or **CONDITIONAL** decision. Explain unmet gates and what evidence would change the verdict.
