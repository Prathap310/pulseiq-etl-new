# PulseIQ ETL — Task 20 Final Handover Report

## 1. Project overview
- Project: PulseIQ ETL
- Task: 20 — Board Pack and Final Handover
- Reporting data cut-off: 30 September 2026
- Handover evidence date: 18 November 2026
- Release: 1.0.0 proposed; approval and tag pending

This report consolidates evidence supplied during the Task 20 review. The figures below are reported from the reviewed handover evidence and have not been independently re-queried from the warehouse in this session.

## 2. Five key board findings

### Finding 1 — Workforce forecast
- September 2026 actual headcount: 441.
- October 2026 forecast: 426.3.
- March 2027 forecast: 439.8.
- October forecast is 14.7 below September actual.
- Forecast accuracy remains unverified because actuals for the forecast period were unavailable in the reviewed evidence.
**Management action:** Review assumptions with HR and department leaders.

### Finding 2 — Employee attrition risk
- Snapshot date: 30 September 2026.
- High-risk employees: 43.
- Eligible employees: 425.
- High-risk share: 10.12%.
**Management action:** Review the governed risk cohort and validate underlying signals before retention decisions.

### Finding 3 — Department attendance
- Finance & Accounts attendance: 88.87%.
- Customer Support attendance: 92.43%.
- Finance & Accounts had the lowest attendance among ten eligible departments in the September evidence.
**Management action:** Ask department leaders to investigate patterns; the evidence does not establish causes.

### Finding 4 — AI anomaly exposure
- Total anomaly records: 405.
- Quantified financial impact: 184 records.
- Unquantified financial impact: 221 records.
- Total quantified exposure: INR 31,421,239.07.
- Statistical outlier category: INR 19,432,986.26.
**Management action:** Prioritise investigation of quantified anomalies and track unquantified anomalies separately. Model-identified exposure is not confirmed realised loss.

### Finding 5 — September net profit
- September 2026 governed net profit: INR 14,985,979.13.
- The reviewed report does not contain cash-flow or cash-balance measures.
**Management action:** Use as a profitability baseline only; obtain cash evidence before making liquidity conclusions.

## 3. Data quality and reconciliation

### Latest detailed evidence reviewed
Task 17 final evidence timestamp: 17 November 2026, 03:50:02 UTC.
- Total checks: 14.
- PASS: 12.
- FAIL: 2.
- ERROR: 0.

This is the latest detailed DQ evidence provided in the review. It is not represented as a newly executed Task 20 validation run.

### DQ-C01 — Payroll equals ledger
- Status: FAIL; 1 bad row.
- June 2026, department D01.
- Payroll earned fixed pay: INR 19,873,074.18.
- Ledger account 5001: INR 19,891,524.18.
- Difference: INR 18,450.00, ledger higher.
- Journal: JE-002094; source: PR-2026-06.
- All 159 D01 payroll rows pass fixed-pay component reconciliation; journal balances overall.
**Treatment:** Preserve original source data. No unsupported adjustment. Finance/Payroll investigation remains open.

### DQ-C11 — AI feed freshness
- Status: FAIL; 405 anomaly records.
- All 405 anomaly records have `scored_at` value 2026-10-01 02:00:00 without explicit timezone.
- Data contract requires UTC; data owner has not confirmed timezone interpretation.
- All 405 were rejected from the clean dataset due to missing valid timezone information.
- Historical attrition predictions are not treated as stale solely by comparing historical `as_of_date` to the current date.
**Treatment:** Do not fabricate timestamps or prediction results. Keep failure visible until verified fresh scores and timezone confirmation exist.

### DQ-C14 — Minimum group size
- Status: PASS for metrics included in current exposure checks.
- Published-view exposures detected: 0 in the reviewed evidence.
- M07, M08, M09 and M15 remain excluded pending a separate employee-level exposure-policy decision.
**Treatment:** A passing check does not constitute approval of the excluded metrics.

### Other checks
DQ-C02 through DQ-C10 and DQ-C12 through DQ-C13 passed in the 17 November evidence.

## 4. Deployment and regression evidence
- Task 17: evidence reports 12 tests passed and 10 subtests passed.
- Task 18: evidence reports 72 regression tests passed.
- Task 19: Metrics API deployment and endpoint checks completed; freshness endpoint reported STALE in reviewed deployment evidence.
- Task 16: automated PDF and Excel management reporting; August and September 2026 reports available. October output was a no-data test because warehouse reporting cut-off was September 2026.

## 5. Known limitations and open decisions
1. INR 18,450 June 2026 D01 payroll-to-ledger difference unresolved.
2. 405 anomaly records stale; source timestamp timezone confirmation pending.
3. Forecast accuracy for October 2026–March 2027 is unverified.
4. Employee-level exposure-policy decision pending for M07, M08, M09 and M15.
5. Official PQ-13 reference comparison and sign-off pending.
6. Metrics API freshness endpoint was STALE in reviewed Task 19 evidence.
7. September report has no cash-flow statement or cash-balance measure.
8. Suppressed values must not be interpreted as zero.

## 6. Task 20 deliverables and status
- Board Pack: 9-slide draft included; management approval pending.
- Release Notes: included; release approval pending.
- Handover report: included.
- Demo script: included.
- Demo recording: the original local MP4 was previously opened successfully, but it is now missing from the working tree after `git clean -fd`. It must be recovered or recreated and revalidated.
- Improvement guide: committed at `3164d54` on `task20/final-release-readiness`.
- Final release tag `v1.0.0`: not created.

## 7. Recommended management actions
1. Finance and Payroll owners investigate DQ-C01 and attach supporting reconciliation evidence.
2. Data/AI owner confirms source timestamp timezone and supplies fresh anomaly scoring.
3. Privacy/governance owner decides employee-level exposure policy for M07, M08, M09 and M15.
4. Complete PQ-13 reference comparison and sign-off.
5. Review workforce forecast assumptions and attendance patterns.
6. Approve the Board Pack and consolidated handover.
7. Re-run release-candidate validation and archive its evidence.
8. Approve release before creating `v1.0.0`.

## 8. Final handover status
Task 20 deliverables are being consolidated. The reviewed evidence identifies two unresolved DQ failures and additional governance/sign-off items. Version 1.0.0 remains pending; this report does not claim final release approval.
