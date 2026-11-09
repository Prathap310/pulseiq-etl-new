# PulseIQ Metric Dictionary

**Total metrics:** 28

This document is generated from `03_Data/csv/metric_dictionary.csv`.
Metric definitions and formulas are preserved from the supplied dataset.

## M01 ? Headcount

- **Business definition:** Active employees on the last day of the month (permanent and contract).
- **Formula:** `COUNT(DISTINCT employee_id) with hire_date <= month_end AND (exit_date IS NULL OR exit_date > month_end)`
- **Source table:** fact_headcount_monthly / dim_employee
- **Grain:** Department x month
- **Time period:** Month end
- **Owner team:** HR Analytics
- **Unit:** count
- **Good direction:** Context dependent
- **Caveat:** Excludes CEO if you compare departments only
- **Minimum group size:** 5

## M02 ? Hires

- **Business definition:** Employees whose hire_date falls in the month.
- **Formula:** `COUNT(employee_id) where hire_date in month`
- **Source table:** fact_headcount_monthly
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** HR Analytics
- **Unit:** count
- **Good direction:** Context dependent
- **Caveat:** Transfers are not hires
- **Minimum group size:** 5

## M03 ? Exits

- **Business definition:** Employees whose exit_date falls in the month (resigned, terminated or contract ended).
- **Formula:** `COUNT(employee_id) where exit_date in month`
- **Source table:** fact_headcount_monthly
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** HR Analytics
- **Unit:** count
- **Good direction:** Lower is better
- **Caveat:** None specified
- **Minimum group size:** 5

## M04 ? Attrition rate (monthly)

- **Business definition:** Share of people who left in the month.
- **Formula:** `Exits / headcount_start x 100`
- **Source table:** fact_headcount_monthly
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** HR Analytics
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** Very noisy for small departments
- **Minimum group size:** 10

## M05 ? Attrition rate (rolling 12 months)

- **Business definition:** Leavers in the last 12 months divided by average headcount over the same months.
- **Formula:** `SUM(exits, 12m) / AVG(headcount_end, 12m) x 100`
- **Source table:** fact_headcount_monthly
- **Grain:** Department x month
- **Time period:** 12 months
- **Owner team:** HR Analytics
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** Use for headline reporting; monthly is too noisy
- **Minimum group size:** 10

## M06 ? Voluntary attrition rate

- **Business definition:** Same as M05 but only resignations (voluntary_exits).
- **Formula:** `SUM(voluntary_exits, 12m) / AVG(headcount_end, 12m) x 100`
- **Source table:** fact_headcount_monthly
- **Grain:** Department x month
- **Time period:** 12 months
- **Owner team:** HR Analytics
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** None specified
- **Minimum group size:** 10

## M07 ? Gross pay

- **Business definition:** Total earnings before deductions for the month.
- **Formula:** `SUM(gross_pay)`
- **Source table:** fact_payroll
- **Grain:** Employee x month
- **Time period:** Month
- **Owner team:** Payroll
- **Unit:** INR
- **Good direction:** Context dependent
- **Caveat:** Includes overtime and variable pay
- **Minimum group size:** 5

## M08 ? Net pay

- **Business definition:** Take-home pay after employee deductions.
- **Formula:** `SUM(net_pay)`
- **Source table:** fact_payroll
- **Grain:** Employee x month
- **Time period:** Month
- **Owner team:** Payroll
- **Unit:** INR
- **Good direction:** Context dependent
- **Caveat:** None specified
- **Minimum group size:** 5

## M09 ? Payroll cost (employer cost)

- **Business definition:** Full cost of employees to the company: gross pay plus employer PF and ESI.
- **Formula:** `SUM(employer_cost)`
- **Source table:** fact_payroll
- **Grain:** Employee x month
- **Time period:** Month
- **Owner team:** Finance
- **Unit:** INR
- **Good direction:** Lower is better when output is equal
- **Caveat:** Must reconcile with ledger accounts 5001-5005
- **Minimum group size:** 5

## M10 ? Cost per head

- **Business definition:** Average employer cost per paid employee.
- **Formula:** `SUM(employer_cost) / COUNT(DISTINCT employee_id)`
- **Source table:** fact_payroll
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** Finance
- **Unit:** INR
- **Good direction:** Context dependent
- **Caveat:** Part-month joiners lower the average
- **Minimum group size:** 5

## M11 ? Overtime share

- **Business definition:** How much of payroll cost is overtime pay.
- **Formula:** `SUM(overtime_pay) / SUM(employer_cost) x 100`
- **Source table:** fact_payroll
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** Payroll
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** Only overtime-eligible roles earn overtime
- **Minimum group size:** 5

## M12 ? Variable pay share

- **Business definition:** Bonus, incentive and award pay as a share of gross pay.
- **Formula:** `SUM(variable_pay) / SUM(gross_pay) x 100`
- **Source table:** fact_payroll
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** Payroll
- **Unit:** percent
- **Good direction:** Context dependent
- **Caveat:** April bonus and quarter-end incentives create spikes
- **Minimum group size:** 5

## M13 ? Attendance rate

- **Business definition:** Days present (half day counts 0.5) divided by scheduled working days.
- **Formula:** `(SUM(present_days) + 0.5 x SUM(half_days_unpaid)) / SUM(scheduled_days)`
- **Source table:** fact_attendance_monthly
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** HR Analytics
- **Unit:** ratio
- **Good direction:** Higher is better
- **Caveat:** Paid leave counts as not present
- **Minimum group size:** 5

## M14 ? Late arrival rate

- **Business definition:** Late check-ins per present day.
- **Formula:** `SUM(late_arrivals) / SUM(present_days)`
- **Source table:** fact_attendance_monthly
- **Grain:** Department x month
- **Time period:** Month
- **Owner team:** HR Analytics
- **Unit:** ratio
- **Good direction:** Lower is better
- **Caveat:** Work-from-home days use web check-in time
- **Minimum group size:** 5

## M15 ? Leave without pay days

- **Business definition:** Unpaid absence and unpaid leave days.
- **Formula:** `SUM(lop_days) in fact_payroll`
- **Source table:** fact_payroll
- **Grain:** Employee x month
- **Time period:** Month
- **Owner team:** Payroll
- **Unit:** days
- **Good direction:** Lower is better
- **Caveat:** Half-day unpaid counts 0.5
- **Minimum group size:** 5

## M16 ? Revenue

- **Business definition:** Income booked in the ledger (accounts 4001-4004).
- **Formula:** `-SUM(signed_amount) for accounts 4001-4004`
- **Source table:** fact_ledger
- **Grain:** Account x month
- **Time period:** Month
- **Owner team:** Finance
- **Unit:** INR
- **Good direction:** Higher is better
- **Caveat:** Excludes GST (booked to 2200)
- **Minimum group size:** Not specified

## M17 ? Net profit

- **Business definition:** Revenue minus all expenses (4xxx less 5xxx).
- **Formula:** `-SUM(signed_amount) for accounts 4xxx and 5xxx`
- **Source table:** fact_ledger
- **Grain:** Month
- **Time period:** Month
- **Owner team:** Finance
- **Unit:** INR
- **Good direction:** Higher is better
- **Caveat:** Interest income (4900) is included
- **Minimum group size:** Not specified

## M18 ? Operating margin

- **Business definition:** Net profit as a share of revenue.
- **Formula:** `Net profit / Revenue x 100`
- **Source table:** fact_ledger
- **Grain:** Month
- **Time period:** Month
- **Owner team:** Finance
- **Unit:** percent
- **Good direction:** Higher is better
- **Caveat:** None specified
- **Minimum group size:** Not specified

## M19 ? Payroll as % of revenue

- **Business definition:** Share of revenue consumed by payroll cost.
- **Formula:** `Payroll cost / Revenue x 100`
- **Source table:** fact_payroll + fact_ledger
- **Grain:** Month
- **Time period:** Month
- **Owner team:** Finance
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** Use ledger payroll accounts to avoid mismatch
- **Minimum group size:** Not specified

## M20 ? Days sales outstanding (DSO)

- **Business definition:** Average days to collect: receivables divided by credit sales x days.
- **Formula:** `Closing receivables / revenue incl GST (last 90 days) x 90`
- **Source table:** fact_invoice, fact_ledger
- **Grain:** Month
- **Time period:** 90 days
- **Owner team:** Finance
- **Unit:** days
- **Good direction:** Lower is better
- **Caveat:** Carried-in invoices included
- **Minimum group size:** Not specified

## M21 ? Overdue receivables

- **Business definition:** Unpaid invoice balance past due date at the report date.
- **Formula:** `SUM(balance_due) where due_date < report date and status not DRAFT/CANCELLED`
- **Source table:** fact_invoice
- **Grain:** Client x date
- **Time period:** Point in time
- **Owner team:** Finance
- **Unit:** INR
- **Good direction:** Lower is better
- **Caveat:** None specified
- **Minimum group size:** Not specified

## M22 ? Task completion rate

- **Business definition:** Tasks done divided by tasks planned in the sprint (cancelled tasks excluded).
- **Formula:** `COUNT(status = Done) / COUNT(status != Cancelled)`
- **Source table:** fact_task
- **Grain:** Team x sprint
- **Time period:** Sprint
- **Owner team:** Engineering Ops
- **Unit:** percent
- **Good direction:** Higher is better
- **Caveat:** Sample feed until the live board is ready
- **Minimum group size:** 5 tasks

## M23 ? On-time delivery rate

- **Business definition:** Done tasks completed on or before the sprint end date.
- **Formula:** `COUNT(completed_on_time = Y) / COUNT(status = Done)`
- **Source table:** fact_task
- **Grain:** Team x sprint
- **Time period:** Sprint
- **Owner team:** Engineering Ops
- **Unit:** percent
- **Good direction:** Higher is better
- **Caveat:** None specified
- **Minimum group size:** 5 tasks

## M24 ? Velocity

- **Business definition:** Story points completed in the sprint.
- **Formula:** `SUM(story_points) where status = Done`
- **Source table:** fact_task
- **Grain:** Team x sprint
- **Time period:** Sprint
- **Owner team:** Engineering Ops
- **Unit:** points
- **Good direction:** Context dependent
- **Caveat:** Do not compare across teams
- **Minimum group size:** Not specified

## M25 ? Average cycle time

- **Business definition:** Days from start to completion for done tasks.
- **Formula:** `AVG(completed_date - started_date)`
- **Source table:** fact_task
- **Grain:** Team x sprint
- **Time period:** Sprint
- **Owner team:** Engineering Ops
- **Unit:** days
- **Good direction:** Lower is better
- **Caveat:** Negative values are data errors
- **Minimum group size:** 5 tasks

## M26 ? Anomaly flag rate

- **Business definition:** Share of scored records flagged by the AI anomaly service.
- **Formula:** `COUNT(flagged = Y) / COUNT(*)`
- **Source table:** fact_anomaly
- **Grain:** Source x month
- **Time period:** Month
- **Owner team:** AI/ML
- **Unit:** percent
- **Good direction:** Context dependent
- **Caveat:** Flags are leads, not proof
- **Minimum group size:** Not specified

## M27 ? High-risk share

- **Business definition:** Share of employees in the High attrition-risk band.
- **Formula:** `COUNT(risk_band = High) / COUNT(*)`
- **Source table:** fact_attrition_risk
- **Grain:** Department
- **Time period:** Point in time
- **Owner team:** AI/ML
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** Show by group only; never rank named people
- **Minimum group size:** 10

## M28 ? Forecast error (MAPE)

- **Business definition:** Average absolute percentage error of headcount forecasts versus actuals.
- **Formula:** `AVG(ABS(actual - forecast) / actual) x 100`
- **Source table:** fact_forecast vs fact_headcount
- **Grain:** Department x month
- **Time period:** Rolling
- **Owner team:** AI/ML
- **Unit:** percent
- **Good direction:** Lower is better
- **Caveat:** Needs actuals for the forecast months
- **Minimum group size:** Not specified
