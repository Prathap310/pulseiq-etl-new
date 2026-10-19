# Task 1 — Data Contract Notes

Source: 03_Data/csv/data_contracts.csv

## 1. fact_task — Task Board

- task_id: Required string; unique; format TASK-nnnnn.
- team_id: Required string; must exist in dim_team.
- sprint_id: Required string; must exist in dim_sprint.
- assignee_employee_id: Required string; must exist in dim_employee.
- task_type: Required string; Feature, Bug, Chore, or Spike.
- priority: Required string; P1 through P4.
- story_points: Required integer; 1, 2, 3, 5, 8, or 13.
- created_date: Required date; must be on or before started_date.
- started_date: Nullable date; blank only when status is To Do.
- due_date: Required date; must equal the sprint end date.
- completed_date: Nullable date; required when status is Done and must be on or after started_date.
- status: Required string; Done, In Progress, Blocked, To Do, or Cancelled.
- reopened_count: Required integer; must be at least zero.

## 2. fact_anomaly — AI Anomaly Results

- result_id: Required string; unique; format AN-nnnn.
- source_dataset: Required string; attendance_monthly_features or payroll_monthly_features.
- record_id: Required string; must exist in the source dataset.
- employee_id: Required string; must exist in dim_employee.
- period: Required date; month-end or month-start date.
- anomaly_score: Required decimal; between 0 and 1.
- flagged: Required character; Y or N.
- reason_code: Required string; must be a published code.
- reason_text: Required string; plain English.
- money_at_risk: Nullable decimal(14,2); blank for attendance rows.
- model_version: Required string; semantic version text.
- scored_at: Required timestamp; UTC.

## 3. fact_forecast — AI Forecast

- forecast_id: Required string; unique; format FC-nnnn.
- metric: Required string; headcount_end or attrition_rate_monthly_pct.
- department_id: Required string; department ID or ALL.
- forecast_month: Required date; first day of the month.
- forecast_value: Required decimal; must be at least zero.
- lower_80: Required decimal; must be less than or equal to forecast_value.
- upper_80: Required decimal; must be greater than or equal to forecast_value.
- method: Required string; text describing the forecasting method.
- trained_through: Required string; format YYYY-MM.

## Validation policy

- Validate required and nullable fields.
- Validate data types, allowed values, uniqueness, and applicable relationships.
- Validate cross-column rules and date constraints.
- Preserve every rejected row with a written reason.
- Never silently discard invalid rows.
- Reconcile counts so rows in = rows passed + rows quarantined.


## Open issue ? fact_anomaly scored_at timezone

- Contract requirement: `scored_at` is a required timestamp in UTC.
- Source value observed: `2026-10-01 02:00:00` in all 405 rows.
- Source values contain no explicit timezone or UTC offset.
- Current validator quarantines all 405 rows with `scored_at: invalid timestamp or missing timezone`.
- Decision required: confirm with the data owner whether these timestamps are UTC. Do not append a timezone or convert the values until that interpretation is approved.
- Until resolved, preserve the strict UTC validation rule and report the affected row count.

## Open issue — fact_attrition_risk batch date
- Contract requirement: `as_of_date` must be the same for the entire batch.
- Source values observed: 425 rows use `2026-09-30`; 5 rows use `2026-03-31`.
- Current validator uses the majority date (`2026-09-30`) as the batch date.
- The 5 rows with `2026-03-31` are quarantined with a reason explaining the mismatch.
- Confirm the intended batch date with the data owner before production sign-off.

## Verified checks — fact_anomaly
- All 405 `period` values are valid month-start or month-end dates.
- All 184 payroll anomaly `record_id` values match records in `fact_payroll`.
- All 184 payroll anomaly employee IDs match the employee IDs on their source payroll records.
- All 405 rows share the `scored_at` value `2026-10-01 02:00:00`.
- The source timestamp has no explicit timezone. UTC interpretation remains unconfirmed, so the strict UTC validation and quarantine remain in place.
- The separate `attendance_monthly_features` source is not supplied, so its 221 record references cannot be verified against that source.
