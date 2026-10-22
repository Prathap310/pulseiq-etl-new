
# Task 4 - Governed Metric Layer Evidence

## 1. Scope
- SQL implementation: `Warehouse/metric_views.sql`
- Governed metric views: M01-M28
- Metric catalog: `dw.metric_catalog`
- Production database: `pulseiq_wh`

## 2. Implementation and deployment
- Local SQL validation: PASS
- PostgreSQL SQL validation: PASS
- Deployment transaction committed: PASS
- Metric views deployed: 28
- Catalog entries: 28
- All 28 metric views queried successfully: PASS
- All 28 metric views returned rows: PASS

## 3. Latest metric-view queryability results

| Metric IDs | Rows returned by each view |
|---|---:|
| M01-M06 | 891 |
| M07-M15 | 198 |
| M16-M19 | 18 |
| M20-M23 | 1 |
| M24-M25 | 608 |
| M26 | 36 |
| M27 | 13 |
| M28 | 6 |

All 28 metric queries completed without SQL errors. These results establish queryability and nonempty output, not formula correctness for every metric.

The initial count of 29 objects matching the `m%` naming pattern included `metric_catalog`. The actual metric views are M01-M28, totaling 28.

## 4. Representative metric validation

Five independent source-to-view checks completed with zero mismatches.

| Metric | Description | Rows checked | Mismatches | Result |
|---|---|---:|---:|---|
| M01 | Headcount | 891 | 0 | PASS |
| M04 | Monthly attrition | 891 | 0 | PASS |
| M13 | Attendance rate | 198 | 0 | PASS |
| M16 | Revenue | 18 | 0 | PASS |
| M20 | Days Sales Outstanding | 1 | 0 | PASS |

These checks validate the listed outputs against independently calculated source results for the tested rows. They do not establish formula correctness for every metric view.

## 5. Financial reconciliation

M17 net profit reconciled against the underlying ledger totals for five months.

| Month | Difference | Result |
|---|---:|---|
| May 2026 | 0.00 | PASS |
| June 2026 | 0.00 | PASS |
| July 2026 | 0.00 | PASS |
| August 2026 | 0.00 | PASS |
| September 2026 | 0.00 | PASS |

## 6. Privacy validation

Seventeen applicable metric views were checked for values exposed when `privacy_threshold_met = FALSE`.

- Applicable views checked: 17
- Metric values exposed below threshold: 0
- Result for tested conditions: PASS

### M25 isolated threshold test

The repository's M25 view definition was tested in the isolated `pulseiq_dq_test` database. Test records and the view were created inside a transaction that was rolled back.

| Scenario | Eligible completed tasks | Average cycle time | Privacy threshold | Result |
|---|---:|---:|---|---|
| Below threshold | 4 | NULL | FALSE | PASS |
| At threshold | 5 | 2.20 days | TRUE | PASS |

The five-task scenario used durations of 1, 2, 3, 4, and 1 days. The average was 2.20 days. Both SQL assertions passed.

### M25 production privacy check

A read-only query against `dw.m25_average_cycle_time` in `pulseiq_wh` returned:

| Check | Result |
|---|---:|
| Total groups | 608 |
| Groups below threshold | 0 |
| Groups meeting threshold | 608 |
| Below-threshold groups exposing a non-NULL average | 0 |

Result: PASS for the current production results. Production currently contains no below-threshold M25 groups, so the isolated test provides the evidence for that scenario.

## 7. Other reviewed results

- M22 task completion rate: 86.30%; threshold met.
- M23 on-time delivery rate: 92.83%; threshold met.
- M28 has six future forecast months, October 2026 through March 2027, with NULL MAPE because actual headcount is not yet available. These are not measured forecast-accuracy results.

## 8. Catalog metadata note

`minimum_group_size` is currently a text column. Values include `5`, `10`, `5 tasks`, and NULL. Numeric threshold comparisons therefore require explicit conversion or a separate numeric field.

A dedicated numeric threshold field is an optional improvement unless a downstream consumer requires numeric comparisons.

## 9. Metric-grain alignment and approval status

The metric dictionary and SQL catalog now specify Department x month for the following metrics:

- M07 - Gross pay
- M08 - Net pay
- M09 - Payroll cost
- M15 - Leave without pay days

The current SQL views aggregate these metrics by period end date and department, applying a minimum group size of five employees. The catalog records the same reporting grain and minimum group size.

**Implementation status:** the dictionary and catalog are aligned with the existing department-month implementation.

**Governance status:** this alignment is a proposed reporting definition, not proof of business-owner approval. Written confirmation is still required from the responsible owners before the reporting grain can be marked formally approved.

## 10. Acceptance and outstanding governance

### Technical work completed
- 28 metric views deployed and queryable.
- 28 catalog entries present.
- Five representative source-to-view checks passed.
- M17 reconciled for May through September 2026.
- Applicable privacy checks returned zero exposed values below threshold.
- M25 isolated below-threshold and at-threshold tests passed.
- M25 production privacy check returned zero leaks.
- Evidence includes the latest row counts and validation results.

### Outstanding external decisions
1. Obtain written Payroll-owner confirmation of the Department x month reporting grain for M07, M08, and M15.
2. Obtain written Finance-owner confirmation of the Department x month reporting grain for M09.
3. Record formal business-owner sign-off for the final metric definitions and reporting grains.

No owner approval is claimed in this report. These governance items cannot be marked approved without an authorized decision.

## 11. Git safety
Other modified and untracked repository files are outside this Task 4 evidence update. Do not stage or commit unrelated project files as part of this work.

This report records observed technical results, implementation choices, limitations, and outstanding decisions. Successful SQL validation does not substitute for business-owner approval.
