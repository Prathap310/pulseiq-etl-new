# Task 9 — Payroll Cost Dashboard and Reconciliation

## 1. Objective

Build a payroll analytics dashboard covering payroll costs, employee deductions, budget variance, payroll-to-ledger reconciliation, and payroll as a percentage of operating revenue.

The dashboard uses the existing PulseIQ project datasets and prepared report files. Original payroll source data is preserved.

## 2. Dashboard Features

The dashboard provides:

- Gross pay and net pay key performance indicators (KPIs).
- Employer cost and cost per employee-month.
- Overtime pay share and variable pay share.
- Leave without pay (LOP) days.
- Department and payroll-month filters.
- Department-month payroll metrics.
- Employer cost by department.
- Monthly employer cost trend.
- Payroll budget versus actual.
- M19 payroll as a percentage of operating revenue.
- Payroll-to-ledger reconciliation.
- Payroll exception evidence and CSV downloads.

The Streamlit application is located at `05_Starter/app_task9.py`.

## 3. Metric Definitions and Privacy Rules

| Metric | Calculation |
|---|---|
| M07 Gross pay | SUM(gross_pay) |
| M08 Net pay | SUM(net_pay) |
| M09 Employer cost | SUM(employer_cost) |
| M10 Cost per head | Employer cost / distinct employees |
| M11 Overtime share | SUM(overtime_pay) / SUM(employer_cost) × 100 |
| M12 Variable pay share | SUM(variable_pay) / SUM(gross_pay) × 100 |
| M15 LOP days | SUM(lop_days) |
| M19 Payroll as % of revenue | Monthly employer cost / operating revenue × 100 |

M19 uses operating revenue from ledger accounts 4001–4004. Account 4900 is excluded.

### Privacy rules

Department-month metrics and employee counts are suppressed when fewer than five distinct employees qualify.

### Reconciliation rule

Payroll employer cost is compared against ledger expense accounts 5001–5005. Differences are not silently adjusted.

### Budget variance rule

Budget variance is calculated as actual employer cost minus budget. Budget reconciliation is a separate control from payroll-to-ledger reconciliation.

## 4. Payroll Data Quality and Exception Treatment

Four payroll records are documented as exceptions:

- Two confirmed duplicate records.
- Two orphan foreign-key records whose employee IDs are absent from `dim_employee`.

All four records are excluded from analytical payroll totals. Original source payroll rows are preserved unchanged.

Excluding a row from analytical reporting does not delete the source record or constitute a financial adjustment to the ledger.

### 4.1 Confirmed duplicate records

| Payroll item ID | Matching payroll item ID | Employee ID | Period | Department | Classification |
|---|---|---|---|---|---|
| PI-X0001 | PI-004059 | EMP-0194 | 2026-02 | D02 | CONFIRMED_DUPLICATE |
| PI-X0002 | PI-000761 | EMP-0598 | 2025-05 | D08 | CONFIRMED_DUPLICATE |

These records are excluded from analytical payroll totals to prevent double-counting.

## 5. Payroll-to-Ledger Reconciliation

The reconciliation report compares payroll employer cost with ledger payroll expense at the department-month grain.

The report contains 198 department-month rows.

### 5.1 Corrected reconciliation exceptions

| Department | Month | Payroll employer cost (INR) | Ledger expense (INR) | Difference (INR) | Status |
|---|---|---:|---:|---:|---|
| D01 | 2026-06 | 20,143,232.18 | 20,161,682.18 | -18,450.00 | INVESTIGATE |

After the documented orphan-row exclusions, the April 2026 D01 and December 2025 D09 differences are zero.

### 5.2 April 2026 — Department D01

The original difference was INR 96,015.00, equal to the employer cost of exception PI-X0003.

After excluding PI-X0003 from analytical payroll totals:

- Corrected payroll employer cost: INR 26,135,951.92.
- Ledger expense: INR 26,135,951.92.
- Difference: INR 0.00.
- Status: `MATCHED`.

### 5.3 December 2025 — Department D09

The original difference was INR 98,327.42, equal to the employer cost of exception PI-X0004.

After excluding PI-X0004 from analytical payroll totals:

- Corrected payroll employer cost: INR 2,103,022.39.
- Ledger expense: INR 2,103,022.39.
- Difference: INR 0.00.
- Status: `MATCHED`.

### 5.4 June 2026 — Department D01

The June discrepancy remains unresolved:

- Payroll employer cost: INR 20,143,232.18.
- Payroll rows: 159.
- Ledger expense: INR 20,161,682.18.
- Difference (payroll minus ledger): INR -18,450.00.
- Status: `INVESTIGATE`.

The related journal entry is `JE-002094`, with source type `PAYROLL_RUN` and source ID `PR-2026-06`.

The journal entry balances overall, but the department-level difference has not been explained by the available evidence. No unsupported adjustment has been made.

## 6. Orphan Foreign-Key Exception Evidence

| Payroll item ID | Employee ID | Period | Department | Employer cost (INR) | Classification |
|---|---|---|---|---:|---|
| PI-X0003 | EMP-9001 | 2026-04 | D01 | 96,015.00 | ORPHAN_FOREIGN_KEY |
| PI-X0004 | EMP-9002 | 2025-12 | D09 | 98,327.42 | ORPHAN_FOREIGN_KEY |

The employee IDs are absent from `dim_employee`, leaving unresolved employee foreign-key references.

Treatment:

- Exclude these records from analytical payroll reporting pending validation.
- Preserve the original source rows.
- Retain the classifications and explanations in the exception evidence file.
- Do not treat analytical exclusion as a ledger adjustment.

The April and December reconciliation differences were eliminated after these exclusions were applied to the reconciliation report.

## 7. Payroll Budget Reconciliation

The project includes a separate payroll budget reconciliation report with:

- Budget cost.
- Corrected actual payroll cost.
- Variance.
- Variance percentage.
- Budget reconciliation status.

**Variance calculation:**

`Variance = Corrected actual cost − Budget cost`

A budget reconciliation status does not establish that payroll agrees with the ledger. These are separate controls.

The budget report contains 198 department-month rows.

Supporting files:

- `Reports/payroll_budget_reconciliation.csv`
- `Reports/Task9_Payroll_Budget_Reconciliation_Corrected.csv`

## 8. Evidence and Supporting Files

| File | Purpose |
|---|---|
| `05_Starter/app_task9.py` | Payroll dashboard application |
| `Reports/Task9_Payroll_Ledger_Reconciliation.csv` | Current department-month payroll-to-ledger reconciliation |
| `Reports/Task9_Payroll_Budget_Reconciliation_Corrected.csv` | Corrected payroll budget reconciliation |
| `Reports/Task9_Payroll_Excluded_Row_Evidence.csv` | Exception classifications and supporting evidence |
| `Reports/Task9_Payroll_Ledger_Reconciliation.backup.csv` | Earlier reconciliation backup |
| `Reports/Task9_Payroll_Ledger_Reconciliation.pre_orphan_fix.csv` | Backup created before the orphan-row correction |
| `Reports/Task9_Payroll_Findings.backup.md` | Earlier findings report backup |

Backup files are retained for traceability. The current reconciliation CSV is the working report.

## 9. Final Status and Limitations

### Completed

- Payroll dashboard and reporting features.
- Payroll-to-ledger reconciliation report.
- Payroll budget reconciliation report.
- Documentation of two confirmed duplicate records.
- Documentation of two orphan foreign-key records.
- Analytical exclusion of all four documented exception rows.
- Correction of the April 2026 D01 and December 2025 D09 differences.
- Preservation of the original payroll source data.

### Current reconciliation status

The corrected reconciliation report contains 198 department-month rows:

| Status | Count |
|---|---:|
| MATCHED | 197 |
| INVESTIGATE | 1 |
| Total | 198 |

The remaining exception is the June 2026 D01 difference of INR -18,450.00. Its cause has not been established, so it remains flagged `INVESTIGATE`.

The official PQ-09 validation answer key was not found in the project locations checked. Therefore, this report does not claim an official PQ-09 score or answer-key validation result.

### Conclusion

Task 9's payroll dashboard, reconciliation reports, and exception evidence have been prepared. Two reconciliation differences were eliminated through documented analytical exclusions of orphan payroll records. The June 2026 D01 discrepancy remains explicitly flagged for investigation.

The report distinguishes confirmed findings from unresolved issues and does not claim that every reconciliation exception has been resolved.