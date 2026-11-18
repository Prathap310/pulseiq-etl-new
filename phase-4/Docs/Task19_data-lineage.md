# PulseIQ - Data Lineage

## 1. Purpose

This document traces selected governed metrics from their source data through
ETL processing, warehouse storage, metric views, dashboard configuration and
the Metrics API.

Primary implementation references:
- `API/services/lineage_config.py`
- `API/services/lineage_service.py`
- `API/routers/metrics.py`
- `Warehouse/production_loader.py`
- `Warehouse/metric_views.sql`
- `docs/metric-dictionary.md`

## 2. End-to-End Metric Lineage

### M01 - Headcount

- Source: `03_Data/csv/fact_headcount_monthly.csv`
- Supporting dimension: `dim_employee`
- ETL: `Warehouse/production_loader.py`
- Warehouse table: `dw.fact_headcount_monthly`
- Metric view: `dw.m01_headcount`
- Definition: Active permanent and contract employees on the last day
  of the month.
- Dictionary formula: Count distinct employees hired on or before month-end
  and not exited before or on month-end.
- Implemented view: Uses `headcount_end`; publishes the value only when
  `headcount_end >= 5`.
- Grain: Department x month.
- Privacy threshold: 5.
- Dashboard configured in API lineage: PulseIQ KPI Dashboard.
- API: `GET /api/v1/metrics/M01`
- Lineage API: `GET /api/v1/metrics/M01/lineage`

### M07 - Gross Pay

- Source: `03_Data/csv/fact_payroll.csv`
- ETL: `Warehouse/production_loader.py`
- Warehouse table: `dw.fact_payroll`
- Metric view: `dw.m07_gross_pay`
- Definition: Total earnings before deductions for the month.
- Formula: `SUM(gross_pay)`.
- Implemented view: Sums gross pay by period and department, rounded to
  two decimal places. The result is published only when at least five
  distinct employees are present.
- Implemented grain: Department x month.
- Privacy threshold: 5 employees.
- Dictionary grain: Employee x month.
- Grain discrepancy: The metric dictionary specifies Employee x month,
  while the implemented view and metric catalog use Department x month.
  Business-owner review is required.
- Caveat: Includes overtime and variable pay.
- Dashboard configured in API lineage: PulseIQ KPI Dashboard.
- API: `GET /api/v1/metrics/M07`
- Lineage API: `GET /api/v1/metrics/M07/lineage`

### M13 - Attendance Rate

- Source: `03_Data/csv/fact_attendance_monthly.csv`
- ETL: `Warehouse/production_loader.py`
- Warehouse table: `dw.fact_attendance_monthly`
- Metric view: `dw.m13_attendance_rate`
- Definition: Days present, with an unpaid half-day counted as 0.5,
  divided by scheduled working days.
- Formula:
  `(SUM(present_days) + 0.5 * SUM(half_days_unpaid)) /
  SUM(scheduled_days)`
- Implemented view: Calculates the ratio by period and department,
  rounded to two decimal places. The value is NULL when fewer than
  five distinct employees are present or scheduled days total zero.
- Grain: Department x month.
- Privacy threshold: 5 employees.
- Caveat: Paid leave counts as not present.
- Dashboard configured in API lineage: PulseIQ KPI Dashboard.
- API: `GET /api/v1/metrics/M13`
- Lineage API: `GET /api/v1/metrics/M13/lineage`

### M22 - Task Completion Rate

- Source: `Data/Clean/fact_task.csv`
- ETL: `Warehouse/production_loader.py`
- Warehouse table: `dw.fact_task`
- Metric view: `dw.m22_task_completion_rate`
- Definition: Tasks completed divided by planned tasks, excluding cancelled
  tasks.
- Formula:
  `100 * COUNT(status = Done) / COUNT(status <> Cancelled)`
- Implemented view: Groups by team and sprint. It excludes rows without
  team or sprint identifiers and publishes the percentage only when at
  least five non-cancelled tasks are present.
- Grain: Team x sprint.
- Privacy threshold: 5 non-cancelled tasks.
- Caveat: The metric dictionary identifies the task feed as a sample feed
  until the live board is ready.
- Dashboard configured in API lineage: PulseIQ KPI Dashboard.
- API: `GET /api/v1/metrics/M22`
- Lineage API: `GET /api/v1/metrics/M22/lineage`

### M27 - High-Risk Share

- Source: `03_Data/csv/fact_attrition_risk.csv`
- ETL: `Warehouse/production_loader.py`
- Warehouse table: `dw.fact_attrition_risk`
- Metric view: `dw.m27_high_risk_share`
- Definition: Share of employees in the High attrition-risk band.
- Formula:
  `100 * COUNT(risk_band = High) / COUNT(*)`
- Implemented view: Uses the latest available `as_of_date`, groups by
  department, and publishes the percentage only when the group contains
  at least ten records.
- Grain: Department at the latest available snapshot date.
- Privacy threshold: 10 employees.
- Privacy caveat: Show by group only; never rank named people.
- Dashboard configured in API lineage: PulseIQ KPI Dashboard.
- API: `GET /api/v1/metrics/M27`
- Lineage API: `GET /api/v1/metrics/M27/lineage`

## 3. API and Reporting Flow

The configured API lineage follows this sequence:

Source data
-> ETL process
-> Warehouse fact table
-> Governed metric view
-> Dashboard configuration
-> Metrics API

Available API endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/metrics` | List configured metrics |
| `GET /api/v1/metrics/{metric_id}` | Retrieve a metric |
| `GET /api/v1/metrics/{metric_id}/lineage` | Retrieve metric lineage |
| `GET /api/v1/freshness` | Retrieve data freshness |
| `GET /health` | API health check |

The API lineage configuration identifies the dashboard as
PulseIQ KPI Dashboard. This configuration alone does not prove that
each metric is displayed as a live dashboard tile.

## 4. Privacy and Data Quality Controls

- M01, M07 and M13 use a minimum group size of five in their implemented
  metric views.
- M22 requires at least five non-cancelled tasks.
- M27 requires at least ten records in a department.
- Values below the applicable threshold are returned as NULL by the
  implemented views.
- M27 is reported by department and snapshot date, not by named employee.

Latest recorded Task 17 DQ evidence:

- Total checks: 14
- PASS: 12
- FAIL: 2
- ERROR: 0

Outstanding findings:

1. DQ-C01: June 2026 D01 payroll-to-ledger difference of INR 18,450.
2. DQ-C11: 405 anomaly records have unverified timezone information.

These findings must remain visible until the responsible owners resolve
them. They must not be represented as successful validation.

## 5. Verification Status and Outstanding Work

| Lineage component | Evidence | Status |
|---|---|---|
| Source files | API lineage configuration | Configured |
| ETL process | `Warehouse/production_loader.py` reference | Configured |
| Warehouse tables | `Warehouse/metric_views.sql` | Verified in SQL |
| Metric definitions | `docs/metric-dictionary.md` | Documented |
| Metric views | `Warehouse/metric_views.sql` | Verified in SQL |
| API lineage | API lineage configuration | Configured |
| Dashboard name | API lineage configuration | Configured |
| Individual live dashboard tiles | Not established by configuration alone | Verification pending |
| Report integration for each metric | Not established by current lineage configuration | Verification pending |

## 6. Known Issues

- M07 has a documented grain discrepancy between the metric dictionary
  and implemented SQL.
- The dashboard configuration does not independently prove live tile
  integration.
- Report-level integration for each selected metric requires verification.
- DQ-C01 and DQ-C11 remain unresolved in the latest recorded DQ evidence.

## 7. Source Files

- `API/services/lineage_config.py`
- `API/services/lineage_service.py`
- `API/routers/metrics.py`
- `Warehouse/production_loader.py`
- `Warehouse/metric_views.sql`
- `docs/metric-dictionary.md`
- `reports/Task17_DQ_final_evidence.md`
