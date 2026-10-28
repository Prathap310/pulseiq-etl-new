# Task 9 — Payroll Cost Dashboard and Reconciliation

## 1. Objective

Build a payroll analytics dashboard covering payroll costs, employee deductions,
budget variance, payroll-to-ledger reconciliation, and payroll as a percentage
of operating revenue.

## 2. Dashboard features

- Gross pay and net pay KPIs
- Employer cost and cost per employee-month
- Overtime pay share and variable pay share
- Leave without pay (LOP) days
- Department and payroll-month filters
- Department-month payroll metrics
- Employer cost by department
- Monthly employer cost trend
- Payroll budget versus actual
- M19 payroll as a percentage of operating revenue
- Payroll-to-ledger reconciliation
- Payroll exception evidence and CSV downloads

## 3. Metric definitions

| Metric | Calculation |
|---|---|
| M07 Gross pay | SUM(gross_pay) |
| M08 Net pay | SUM(net_pay) |
| M09 Employer cost | SUM(employer_cost) |
| M10 Cost per head | Employer cost / distinct employees |
| M11 Overtime share | SUM(overtime_pay) / SUM(employer_cost) x 100 |
| M12 Variable pay share | SUM(variable_pay) / SUM(gross_pay) x 100 |
| M15 LOP days | SUM(lop_days) |
| M19 Payroll as % of revenue | Payroll employer cost / operating revenue x 100 |

Department-month metrics with fewer than five distinct employees are suppressed.
M19 is a company-wide monthly metric based on operating revenue ledger accounts
4001–4004. Other income account 4900 is excluded.

## 4. Confirmed duplicate records

Two payroll rows were identified as exact employee-period duplicates:

| Excluded payroll item | Matching record | Period | Department | Employer cost |
|---|---|---|---|---:|
| PI-X0001 | PI-004059 | 2026-02 | D02 | 154,811.89 |
| PI-X0002 | PI-000761 | 2025-05 | D08 | 61,813.15 |

These duplicate rows are excluded from analytical totals. The original source CSV
is preserved unchanged.

## 5. Payroll-to-ledger reconciliation

After excluding the two confirmed duplicate rows:

- Payroll employer cost: INR 861,780,734.84
- Ledger payroll expense: INR 861,604,842.42
- Net difference (payroll minus ledger): INR 175,892.42
- Matched department-months: 195
- Department-months requiring investigation: 3

### Unresolved exceptions

| Department | Month | Payroll employer cost | Ledger expense | Difference |
|---|---|---:|---:|---:|
| Operations & IT | 2025-12 | 2,201,349.81 | 2,103,022.39 | 98,327.42 |
| Engineering | 2026-04 | 26,231,966.92 | 26,135,951.92 | 96,015.00 |
| Engineering | 2026-06 | 20,143,232.18 | 20,161,682.18 | -18,450.00 |

The three exceptions remain flagged for investigation. They have not been silently
adjusted or marked as reconciled.

## 6. Additional exception candidates

| Payroll item | Classification | Period | Department | Employer cost |
|---|---|---|---|---:|
| PI-X0003 | Ledger mismatch candidate | 2026-04 | D01 | 96,015.00 |
| PI-X0004 | Ledger mismatch candidate | 2025-12 | D09 | 98,327.42 |

These records have no matching employee-period row in the checks performed.
They remain candidates pending further validation and are not classified as
confirmed duplicates.

## 7. Budget reconciliation

The corrected payroll budget reconciliation contains 198 department-month rows.
The report compares corrected actual employer cost with budget:

Variance = corrected actual employer cost - budget cost

A positive variance indicates actual cost above budget. A negative variance
indicates actual cost below budget. Budget variance is separate from payroll-to-
ledger reconciliation.

See `Task9_Payroll_Budget_Reconciliation_Corrected.csv` for the department-month
results.

## 8. Evidence files

- `Task9_Payroll_Budget_Reconciliation_Corrected.csv`
- `Task9_Payroll_Excluded_Row_Evidence.csv`
- `Task9_Payroll_Ledger_Reconciliation.csv`
- `Task9_Screenshots/Task9_Dashboard_Overview.png`
- `Task9_Screenshots/Task9_Payroll_Metrics.png`
- `Task9_Screenshots/Task9_Budget_vs_Actual.png`
- `Task9_Screenshots/Task9_Revenue_Ratio.png`
- `Task9_Screenshots/Task9_Ledger_Reconciliation.png`
- `Task9_Screenshots/Task9_Exception_Evidence.png`

## 9. Limitations and status

The official PQ-09 validation answer key was not found in the project locations
checked. Therefore, this report does not claim an official PQ-09 score or
official answer-key validation.

The two duplicate records are confirmed by exact employee-period matches.
The two other candidate records and three reconciliation exceptions require
further investigation.

The original payroll source data has been preserved.
