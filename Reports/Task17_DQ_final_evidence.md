# Task 17 - Final Data Quality Evidence

- Latest verification (UTC): 2026-11-16T18:33:30+00:00
- Total checks: 14
- PASS: 12
- FAIL: 2
- ERROR: 0
- Console evidence: `Reports/Task17_DQ_final_console.txt`

## 1. Final DQ Results

| Check | Name | Status | Bad rows |
|---|---|---|---:|
| DQ-C01 | Payroll equals ledger | FAIL | 1 |
| DQ-C02 | Ledger balanced | PASS | 0 |
| DQ-C03 | Unique payroll rows | PASS | 0 |
| DQ-C04 | No orphan employees | PASS | 0 |
| DQ-C05 | No attendance after exit month | PASS | 0 |
| DQ-C06 | Unpaid leave deducted | PASS | 0 |
| DQ-C07 | Invoice arithmetic | PASS | 0 |
| DQ-C08 | Expense arithmetic | PASS | 0 |
| DQ-C09 | Task dates sensible | PASS | 0 |
| DQ-C10 | Leave dates sensible | PASS | 0 |
| DQ-C11 | AI feeds fresh | FAIL | 835 |
| DQ-C12 | Dimension history does not overlap | PASS | 0 |
| DQ-C13 | Pipeline freshness | PASS | 0 |
| DQ-C14 | Minimum group size | PASS | 0 |

## 2. Outstanding Finding - DQ-C01

June 2026, department D01:

- Payroll earned fixed pay: INR 19,873,074.18
- Ledger account 5001: INR 19,891,524.18
- Difference: INR 18,450.00 (ledger higher)
- All other departments match for this comparison.
- All 159 D01 payroll rows pass fixed-pay component reconciliation.
- Journal entry: JE-002094.
- Source ID: PR-2026-06.
- The journal balances overall.
- The discrepancy was documented in the Task 9 payroll findings report as INVESTIGATE.

Treatment:
- Preserve the original ledger and payroll data.
- Do not create an unsupported adjustment.
- Keep DQ-C01 failed pending investigation and supporting evidence.

## 3. Outstanding Finding - DQ-C11

Total freshness findings: 835.

Breakdown:
- Attrition predictions: 430 stale records.
- Anomaly records: 405 records rejected from the clean dataset because their scored_at timestamps lack valid timezone information.

Additional findings:
- The 430 attrition records have as_of_date values from 2026-03-31 through 2026-09-30.
- The 405 anomaly records have timezone-naive scored_at values of 2026-10-01 02:00:00.
- Task 14 dashboard reads existing CSV files; it does not train models or generate fresh scores.
- No model-generation implementation was identified in the source files searched.

Treatment:
- Do not fabricate timestamps or prediction results.
- Implement and validate a genuine refresh/scoring process before treating these records as fresh.
- Keep DQ-C11 failed until the freshness requirements are satisfied.

## 4. Source History Verification

Git history confirms the three source files below were introduced in commit `443981e`:

- `03_Data/csv/fact_ledger.csv`
- `03_Data/csv/fact_anomaly.csv`
- `03_Data/csv/fact_attrition_risk.csv`

A comparison against commit `443981e` returned no differences for these files.

## 5. Completed Remediation

The following checks now pass:

- DQ-C03: Duplicate payroll rows.
- DQ-C04: Orphan employees.
- DQ-C05: Attendance after exit month.
- DQ-C06: Unpaid leave deduction.
- DQ-C07: Invoice arithmetic.
- DQ-C08: Expense arithmetic.
- DQ-C09: Task date validation.
- DQ-C10: Leave date validation.

DQ-C02, DQ-C12, DQ-C13 and DQ-C14 also pass in the latest run.

## 6. Final Assessment

Current result: 12 PASS, 2 FAIL, 0 ERROR.

Task 17 remediation has substantially improved data quality. However, full DQ acceptance is pending resolution of the June 2026 D01 payroll-ledger discrepancy and the AI feed freshness findings.

The two failures remain visible and are not overridden or treated as successful.
