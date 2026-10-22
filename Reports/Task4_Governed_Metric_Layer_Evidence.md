# Task 4 - Governed Metric Layer Evidence

## Scope
- SQL file: `Warehouse/metric_views.sql`
- Metric views: M01-M28
- Catalog view: `dw.metric_catalog`

## Implementation and deployment
- Local SQL validation: PASS
- PostgreSQL accepted the final SQL in a rollback-only transaction: PASS
- Deployment transaction committed: PASS
- Deployed metric views found: 28
- `dw.metric_catalog` present: YES
- Catalog rows: 28
- Queryability check for all discovered views: PASS
- Latest all-view query returned rows for all 28 views without SQL errors: PASS

## Representative metric validation
Five independent source-to-view checks completed with zero mismatches:

| Metric | Description | Rows checked | Mismatches | Result |
|---|---|---:|---:|---|
| M01 | Headcount | 891 | 0 | PASS |
| M04 | Monthly attrition | 891 | 0 | PASS |
| M13 | Attendance rate | 198 | 0 | PASS |
| M16 | Revenue | 18 | 0 | PASS |
| M20 | Days Sales Outstanding | 1 | 0 | PASS |

These checks validate the listed metric outputs against independently calculated source results for the tested rows. They do not establish formula correctness for every metric view.

## Financial reconciliation
M17 net profit reconciled against the underlying 4xxx and 5xxx ledger totals for five months:
- May 2026: difference 0.00
- June 2026: difference 0.00
- July 2026: difference 0.00
- August 2026: difference 0.00
- September 2026: difference 0.00

## Privacy validation
Seventeen applicable metric views were checked for values exposed when
`privacy_threshold_met = FALSE`.
- Views checked: 17
- Metric values exposed below threshold: 0
- Result: PASS for the tested condition

Caveat: M25 had no currently suppressed rows in production, so production data did not exercise an actual below-threshold M25 group.

Isolated M25 suppression-logic tests:
- Below-threshold case: four eligible completed tasks; average cycle time was NULL and `privacy_threshold_met` was FALSE. Result: PASS.
- At-threshold case: five eligible completed tasks; average cycle time was 3.20 days and `privacy_threshold_met` was TRUE. Result: PASS.
- Both-case assertion: TRUE.
- Test transaction: rolled back successfully; test data and temporary view were not persisted.
- Limitation: the test used a temporary view reproducing the M25 logic in `pulseiq_dq_test`. The deployed `dw.m25_average_cycle_time` view was absent from that database and was not directly tested by this procedure.

## Other reviewed results
- M22 task completion rate: 86.30%; threshold met.
- M23 on-time delivery rate: 92.83%; threshold met.
- M28 has six future forecast months (October 2026–March 2027) with NULL MAPE because actual headcount is not yet available. These are not measured forecast-accuracy results.

## Catalog metadata note
`minimum_group_size` is currently a text column. Values include `5`, `10`, `5 tasks`, and NULL. This preserves the mixed descriptions but means numeric threshold comparisons require explicit conversion or a separate numeric field.

## Grain discrepancy requiring review
The official metric dictionary specifies `Employee x month` for M07 (Gross pay), M08 (Net pay), M09 (Payroll cost), and M15 (Leave without pay days). Their implemented SQL views aggregate by `period_end_date` and `department_id`, applying a five-employee privacy threshold.

The catalog metadata has been updated to describe these four metrics as `Department x month`, with caveats documenting the discrepancy with the official dictionary. This aligns the catalog descriptions with the current view implementation but does not resolve the conflicting specification.

The starter SQL examples use department-month aggregation as a general pattern, but do not explicitly resolve the conflicting grain entries in the official metric dictionary. The intended reporting grain and business definitions still require confirmation from the appropriate metric owner. No formal owner approval is recorded.

## Remaining review / sign-off
- Confirm the intended reporting grain for M07, M08, M09, and M15 with the appropriate metric owner.
- Confirm final business definitions and reporting grains against the approved metric dictionary, especially financial and task metrics.
- Consider a dedicated numeric threshold field if downstream reporting needs numeric comparisons.
- Directly test the deployed M25 view with below-threshold data in an isolated test database, if practical.
- Formal business-owner approval is not recorded in this evidence report.

## Git safety
The repository contains other modified and untracked files. Do not use `git add .` or commit unrelated project work as part of Task 4.

This report records observed checks and known caveats; it is not a claim that all business definitions have received formal owner approval.
