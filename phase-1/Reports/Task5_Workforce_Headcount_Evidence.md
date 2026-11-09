# Task 5 — Workforce & Headcount Dashboard Evidence

## Objective
Deliver an interactive workforce dashboard using governed headcount, hires, and exits metrics.

## Dashboard features
- Latest headcount, hires, exits, and selected-department KPI cards.
- Monthly headcount trend.
- Average monthly headcount by department.
- Current employee records by location tier.
- Current employee records by work mode.
- Department and reporting-date filters.
- Numerical insights for the charts.
- Five CEO workforce-planning questions.

## Data governance
- Headcount uses `dw.m01_headcount`.
- Hires use `dw.m02_hires`.
- Exits use `dw.m03_exits`.
- The metric queries retain rows where `privacy_threshold_met = TRUE`.
- Workforce breakdowns use employee and location dimensions.

## Validation results
- Python syntax check passed.
- Dashboard launched successfully in Streamlit.
- Department and date filters were tested successfully.
- KPI results matched the read-only database validation for the full reporting period:
  - Latest headcount: 440 (September 2026)
  - Hires in period: 81
  - Exits in period: 5
- Department averages matched the governed-view query.
- Current employee dimension breakdowns reconciled to 745 records:
  - Location tier: Tier 1 = 679, Tier 2 = 50, Tier 3 = 16.
  - Work mode: Hybrid = 339, Onsite = 263, Remote = 143.
- The department filter excludes the aggregate label `All Departments`; the expected selectable department count is 11.
- The Executive Office has a current employee record but no privacy-approved headcount rows in the queried period. Its headcount must not be inferred from the employee dimension.

## Evidence files
Screenshots are stored in `Reports/Task5_Evidence/`:
- `dashboard_overview.png`
- `ceo_questions.png`
- `Headcount by Department.png`
- `Monthly headcount Trend.png`
- `Workforce by Location Tier.png`
- `Workforce by Work Mode.png`

## Completion status
Dashboard launch, KPI comparison, chart-query comparison, and filter testing were reported as passed. This evidence records the checks performed; it does not imply independent verification of every possible edge case.
