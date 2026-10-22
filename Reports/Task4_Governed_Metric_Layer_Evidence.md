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
- Queryability check for discovered views: PASS

## Representative metric validation
Five source-to-view checks completed with zero mismatches:
- M01 - Headcount
- M04 - Monthly attrition
- M13 - Attendance rate
- M16 - Revenue
- M20 - Days Sales Outstanding

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

Caveat: M25 had no currently suppressed rows, so the check did not exercise
an actual below-threshold M25 group.

## Other reviewed results
- M22 task completion rate: 86.30%; threshold met.
- M23 on-time delivery rate: 92.83%; threshold met.
- M28 has six future forecast months (October 2026?March 2027) with NULL
  MAPE because actual headcount is not yet available. These are not
  measured forecast-accuracy results.

## Catalog metadata note
`minimum_group_size` is currently a text column. Values include `5`, `10`,
`5 tasks`, and NULL. This preserves the mixed descriptions but means numeric
threshold comparisons require explicit conversion or a separate numeric field.

## Remaining review / sign-off
- Confirm final business definitions and reporting grains against the approved
  metric dictionary, especially financial and task metrics.
- Consider a dedicated numeric threshold field if downstream reporting needs
  numeric comparisons.
- Exercise M25 with a below-threshold test case if practical.
- Review the report and SQL file before committing the intended Task 4 files.

## Git safety
The repository contains other modified and untracked files. Do not use
`git add .` or commit unrelated project work as part of Task 4.

This report records observed checks and known caveats; it is not a claim that
all business definitions have received formal owner approval.
