# Evaluation Methodology -- Detailed Calculation Guide

This guide explains the calculations and reported results in the final
project report for the AI-Driven Quality Assistance Application for STLC
Automation.


## 1. Evaluation dataset and protocol

The evaluation compared manual testing, a single-LLM workflow, and the
proposed multi-agent application.

  Benchmark category                Scenarios
  ------------------------------- -----------
  Requirements and user stories            10
  Code changes                             10
  Execution logs                           10
  Defect scenarios                         10
  Release scenarios                        10
  Test-data scenarios                      10
  **Total**                            **60**

Reference information was prepared in advance: expected
requirement-to-test links, expert-reviewed test cases, impacted test
cases, known execution root causes, expected defect classifications,
release/no-release decisions, and test-data constraints.

Three experienced testers reviewed generated artefacts using a
five-point scale: 1 = very poor, 2 = poor, 3 = average, 4 = good, and 5
= excellent. Criteria included correctness, completeness, relevance,
clarity, and practical usability. AI-assisted workflows were repeated
three times to examine variation and consistency.

## 2. End-to-end time and human effort

### 2.1 Cycle-time reduction

Reported values:

  Workflow                             Time
  ---------------------- ------------------
  Manual                   40 working hours
  Multi-agent assisted               1 hour

The workflow starts when requirements are received and ends when the
required testing artefacts are accepted. It includes test-case
preparation, test-data generation, automation recommendations, change
analysis, defect documentation, test summaries, release-readiness
assessment, review, and refinement.

Formula:



**Time Reduction (%) = (T_manual-T_assisted) / (T_manual) × 100**



Calculation:



**(40-1) / (40) × 100=97.5%**



**Meaning:** End-to-end cycle time decreased by 97.5%. The assisted
measurement includes review and refinement, not just the first model
response.

### 2.2 Active human-effort reduction

Reported values: manual = 30 hours; assisted = 35 minutes.

Convert 35 minutes to hours:



**35/60=0.5833hours**



Formula:



**Effort Reduction (%) = (E_manual-E_assisted) / (E_manual) × 100**



Calculation:




**(30-0.5833) / (30) × 100=98.06%approximately**



Active effort includes preparing inputs, reviewing outputs, providing
instructions, and correcting/refining outputs. It is different from
total elapsed cycle time.

### 2.3 Review rounds

  Workflow                 Review rounds
  ---------------------- ---------------
  Manual                            2--3
  Multi-agent assisted                 2

This is a direct count of review-and-refinement cycles before
acceptance, not a percentage.

### 2.4 First-draft latency

  Workflow                 First complete response
  ---------------------- -------------------------
  Manual                         1--2 working days
  Multi-agent assisted                  10 minutes

This is the time from submitting a request to receiving the first
complete response. It is not the end-to-end cycle time because review
and refinement may still be required.

### 2.5 Acceptance rate

  Workflow                 Acceptance rate
  ---------------------- -----------------
  Manual                               90%
  Multi-agent assisted                 80%

Formula:



**Acceptance Rate = (Artefacts accepted unchanged or with minor edits) / (Total artefacts assessed) × 100**



Illustrative example only: if 80 of 100 artefacts are accepted unchanged
or with minor edits, the rate is 80%. The report does not provide the
actual raw counts.

**Interpretation:** The assisted workflow had a lower reported
acceptance rate than the manual workflow. Human review therefore
remained important.

## 3. Specialist-level evaluation

Each specialist performs a different task, so each is assessed with
task-appropriate measures.

### S01 -- Test-case generation

**Reported:** 94.0% requirement coverage; 92.5% validity.

Requirement coverage:




**(Requirements covered by reviewer-accepted test cases) / (Total in-scope requirements) × 100**



Illustration: 94 of 100 requirements covered = 94%.

Test-case validity:




**(Valid generated test cases) / (Total generated test cases) × 100**



Illustration: 185 of 200 valid test cases = 92.5%.

Coverage measures whether requirements are represented; validity
measures whether the generated test cases are correct and usable.

### S02 -- Test-data generation

**Reported:** 97.2% data validity; 93.0% scenario coverage.

Data validity:




**(Valid generated records) / (Total generated records) × 100**



Illustration: 243 of 250 valid records = 97.2%. Validity can be checked
against data types, mandatory fields, business rules, boundaries, and
constraints.

Scenario coverage:




**(Required scenarios supported) / (Total required scenarios) × 100**



Illustration: 93 of 100 supported scenarios = 93%.

### S03 -- Test-script automation assistance

**Reported:** 89.0% recommendation precision.




**(Appropriate recommendations) / (Total recommendations) × 100**



Illustration: 89 of 100 appropriate recommendations = 89%. This measures
recommendation quality; the agent does not directly execute or modify
scripts.

### S04 -- Test execution analysis

**Reported:** 91.0% root-cause accuracy.




**(Correctly classified failures) / (Total failures with known causes) × 100**



Illustration: 91 of 100 correctly classified failures = 91%. Reference
categories include application defects, environment issues, test-script
failures, test-data issues, and configuration problems. The agent
analyses supplied execution information; it does not independently
execute external test suites.

### S05 -- Self-healing recommendations

**Reported:** 86.0% repair-suggestion accuracy.




**(Technically correct repair suggestions) / (Total suggestions) × 100**



Illustration: 86 of 100 technically correct suggestions = 86%. This is
recommendation quality, not an automatic script-repair success rate.

### S06 -- Change-impact analysis

**Reported:** 91.0% precision; 88.0% impact coverage.

Precision:




**(Correctly identified impacted test cases) / (Total test cases identified as impacted) × 100**



Illustration: 91 correct out of 100 identified = 91%.

Impact coverage:




**(Correctly identified impacted test cases) / (Total expert-identified impacted test cases) × 100**



Illustration: 88 found out of 100 expert-identified impacted cases =
88%.

Precision asks, "Of the cases predicted as impacted, how many were
correct?" Coverage asks, "Of all actually impacted cases, how many did
the agent find?"

### S07 -- Bug-report generation

**Reported:** 96.0% completeness; 90.0% acceptance; 92.0% classification
accuracy.

Completeness:




**(Complete bug reports) / (Total generated bug reports) × 100**



Illustration: 96 complete reports out of 100 = 96%. Required fields may
include title, description, reproduction steps, expected result, actual
result, severity, and priority.

Acceptance:




**(Accepted bug reports) / (Total generated bug reports) × 100**



Illustration: 90 accepted out of 100 = 90%.

Classification accuracy:




**(Correctly classified defects) / (Total classified defects) × 100**



Illustration: 92 correctly classified out of 100 = 92%.

### S08 -- Test-summary reporting

**Reported:** 97.0% factual accuracy.




**(Statements matching execution data) / (Total verifiable statements) × 100**



Illustration: 97 matching statements out of 100 = 97%. A summary's pass,
fail, and skip counts must match the underlying execution data.

### S09 -- Release-readiness assessment

**Reported:** 90.0% decision agreement.




**(Recommendations matching expert decisions) / (Total release scenarios) × 100**



Illustration: 9 matching recommendations out of 10 scenarios = 90%. This
measures agreement with experts; it does not mean the agent
independently approves releases.

## 4. Orchestration and operational metrics

The root agent interprets requests, selects specialists, passes context,
and aggregates responses.

### 4.1 Specialist-selection accuracy

**Reported:** 96.0%.




**(Requests where expected specialists are invoked) / (Total evaluated requests) × 100**



Illustration: expected specialists invoked for 96 of 100 requests = 96%.

### 4.2 Unnecessary specialist calls

**Reported:** 7.5%.




**(Unnecessary specialist invocations) / (Total specialist invocations) × 100**



Illustration: 15 unnecessary calls out of 200 total specialist
invocations = 7.5%. The denominator is invocations, not user requests.

### 4.3 Workflow completion rate

**Reported:** 94.0%.




**(Requests resulting in a usable response) / (Total requests initiated) × 100**



Illustration: 94 usable responses out of 100 initiated requests = 94%.
Merely generating a response is not enough; it must be usable.

### 4.4 Human correction rate

**Reported:** 14.0%.




**(Artefacts requiring major corrections) / (Total artefacts produced) × 100**



Illustration: 14 artefacts requiring major correction out of 100 = 14%.
This differs from acceptance rate: minor edits may still count as
acceptance.

### 4.5 Repeat consistency

**Reported:** 92.0%.




**(Repeated runs producing the same decision or classification) / (Total repeated-run comparisons) × 100**



Illustration: 92 consistent comparisons out of 100 = 92%. The report
says AI-assisted workflows were repeated three times. This measures
decision/classification consistency, not identical wording.

### 4.6 Agent orchestration latency

**Reported:** 4.2 seconds.

The report defines this as root-agent time spent on routing, delegation,
and result aggregation, excluding specialist execution.




**T_orchestration=T_routing+T_delegation+T_aggregation**



Illustrative breakdown only:

  Activity                                     Illustrative time
  ------------------------------------------ -------------------
  Interpret request and select specialists               1.0 sec
  Prepare and delegate tasks                             1.2 sec
  Aggregate specialist responses                         2.0 sec
  **Total**                                          **4.2 sec**

The report gives the overall measured result, not these component times.
This is not total end-to-end AI response time because specialist
execution is excluded.

### 4.7 Average cost per completed workflow

**Reported:** \$0.18.




**Average Cost=(Total LLM/API expenditure) / (Number of completed workflows)**



Illustration: \$18 total expenditure across 100 completed workflows =
\$0.18 per workflow.

The report says the cost includes refinement rounds. It does not provide
actual token counts, provider-wise prices, or a component-level cost
ledger.

## 5. Consolidated results

  Category        Metric                                                 Reported result
  --------------- ------------------------------------- --------------------------------
  End-to-end      Cycle-time reduction                                             97.5%
  End-to-end      Active human effort                              30 hours → 35 minutes
  End-to-end      Review rounds                                                 2--3 → 2
  End-to-end      First-draft latency                     1--2 working days → 10 minutes
  End-to-end      Acceptance rate                                              90% → 80%
  S01             Test-case requirement coverage                                   94.0%
  S01             Test-case validity                                               92.5%
  S02             Test-data validity                                               97.2%
  S02             Scenario coverage                                                93.0%
  S03             Automation recommendation precision                              89.0%
  S04             Root-cause accuracy                                              91.0%
  S05             Repair-suggestion accuracy                                       86.0%
  S06             Change-impact precision                                          91.0%
  S06             Change-impact coverage                                           88.0%
  S07             Bug-report completeness                                          96.0%
  S07             Bug-report acceptance                                            90.0%
  S07             Defect classification accuracy                                   92.0%
  S08             Test-summary factual accuracy                                    97.0%
  S09             Release decision agreement                                       90.0%
  Orchestration   Specialist-selection accuracy                                    96.0%
  Orchestration   Unnecessary calls                                                 7.5%
  Orchestration   Workflow completion                                              94.0%
  Orchestration   Human correction rate                                            14.0%
  Orchestration   Repeat consistency                                               92.0%
  Operational     Orchestration latency                                      4.2 seconds
  Operational     Average cost per workflow                                       \$0.18

## 6. Likely viva questions

**Q: How did you calculate 97.5% cycle-time reduction?**\
A: Manual workflow took approximately 40 working hours and the
multi-agent workflow took one hour. Applying (40 − 1) / 40 × 100 gives
97.5%. The assisted measurement includes review and refinement.

**Q: Why is human effort different from cycle time?**\
A: Cycle time is total elapsed time from receiving requirements to
accepting artefacts. Active effort counts only the engineer's
preparation, review, instruction, and refinement time. The report
records 30 hours manually and 35 minutes with assistance.

**Q: How did you validate requirement coverage?**\
A: Generated test cases were compared with expected requirement-to-test
links prepared for the benchmark. Coverage is the number of in-scope
requirements with at least one reviewer-accepted test case divided by
all in-scope requirements.

**Q: Who assessed whether an artefact was valid?**\
A: The evaluation used reference information prepared in advance and
review by three experienced testers. Review criteria included
correctness, completeness, relevance, clarity, and practical usability.

**Q: How was specialist-selection accuracy calculated?**\
A: Expected specialists were identified for each request, and the root
agent's actual selection was compared with that expected selection. The
result is the proportion of evaluated requests where expected
specialists were invoked.

**Q: How was repeat consistency calculated?**\
A: AI-assisted workflows were repeated three times. Decisions or
classifications from repeated runs were compared. The reported 92%
represents the proportion of comparisons that produced the same decision
or classification.

**Q: How was the \$0.18 cost calculated?**\
A: Total LLM/API expenditure was divided by completed workflows,
including refinement rounds. The report does not provide the raw token
or provider-wise cost breakdown.

**Q: Did the application execute test suites or repair scripts
automatically?**\
A: No. The execution-analysis agent analysed supplied test execution
information. The self-healing agent provided repair recommendations
rather than directly modifying repository files. Release-readiness
output was decision support; final approval remained with the
engineering team.

## 7. Methodological caveats

1.  **Raw calculation evidence:** The report provides metric definitions
    and final values, but not every raw numerator and denominator. Do
    not present illustrative examples as actual experimental counts.
2.  **Single-LLM baseline:** The methodology describes manual,
    single-LLM, and multi-agent comparison conditions. However, the
    report does not provide a complete numerical results table for all
    three. Do not claim a measured numerical advantage over the
    single-LLM baseline unless additional results are available.
3.  **Benchmark size:** The evaluation used 60 scenarios and three
    experienced reviewers. Results should be interpreted within this
    benchmark and application configuration, not as universal
    performance guarantees.
4.  **Human judgement:** Relevance, usability, and technical correctness
    of recommendations involve reviewer judgement.
5.  **Operational cost detail:** The report gives \$0.18 per completed
    workflow but not underlying token counts, provider-wise rates, or
    component-level cost ledger.
6.  **Latency detail:** The 4.2-second result is root-agent
    orchestration time, excluding specialist execution. It is not full
    workflow response time.

## 8. Five calculations to remember

1.  **Cycle-time reduction:** 40 hours to 1 hour = 97.5%.
2.  **Human-effort reduction:** 30 hours to 35 minutes = approximately
    98.06%.
3.  **Workflow completion:** usable responses divided by total initiated
    requests = 94%.
4.  **Specialist selection:** requests with expected specialists invoked
    divided by evaluated requests = 96%.
5.  **Repeat consistency:** repeated-run comparisons with the same
    decision/classification divided by all comparisons = 92%.


