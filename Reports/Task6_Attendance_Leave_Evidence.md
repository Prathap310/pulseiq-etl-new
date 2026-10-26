# Task 6 — Attendance and Leave Trends Dashboard

## 1. Objective
Build an interactive dashboard to analyze employee attendance, late arrivals, overtime, approved leave, and holidays using the PostgreSQL warehouse.

## 2. Implementation
- Application: Streamlit
- Database: PostgreSQL
- Schema: `dw`
- Dashboard file: `05_Starter/app_task6.py`
- Attendance source: `dw.fact_attendance_monthly`
- Leave source: `dw.fact_leave`
- Calendar source: `dw.dim_date`

## 3. Dashboard Features
- Monthly attendance rate by department
- Monthly late arrivals and overtime
- Approved leave days by leave type
- Holiday timeline
- Unusual-month analysis
- Department filter and detailed department table
- KPI cards for attendance, late arrivals, overtime, and approved leave

## 4. Validation Evidence

### Python syntax
Command: `python -m py_compile .\05_Starter\app_task6.py`

Result: Passed with no syntax errors.

### Attendance validation
PostgreSQL weighted attendance rates were checked for 18 monthly periods from April 2025 through September 2026.

- Lowest rate: May 2026 — 92.87%
- Highest rate: July 2025 — 95.56%
- Latest period: September 2026 — 95.18%

### Approved leave validation
PostgreSQL totals were checked against the dashboard data.

| Leave type | Approved requests | Approved leave days |
|---|---:|---:|
| EL | 1,130 | 2,336 |
| CL | 977 | 1,995 |
| SL | 836 | 1,769 |
| ML | 7 | 910 |
| BL | 80 | 137 |
| LOP | 58 | 129 |

Note: ML has 910 approved leave days across 7 requests and requires business-rule review.

### Holiday validation
- Calendar dates: 2,647
- Dates flagged as holidays: 19

### Overtime validation
Highest overtime totals:

1. December 2025 — 787.0 hours
2. March 2026 — 610.5 hours
3. September 2026 — 599.5 hours

### Interactive validation
The dashboard loaded successfully, displayed charts, and the department filter was tested. The displayed metrics updated when Engineering was selected.

## 5. Git Evidence
- File: `05_Starter/app_task6.py`
- Commit: `c721031`
- Commit message: `Add Task 6 attendance and leave dashboard`
- Branch: `master`
- Push to `origin/master`: Successful

## 6. Remaining Review
- Investigate the unusually high ML leave-day total.
- Capture screenshots of the dashboard for visual evidence.
- Confirm any additional Task 6 acceptance criteria before marking the task fully complete.

## 7. Conclusion
The Task 6 dashboard has been implemented, tested against selected PostgreSQL aggregates, committed, and pushed to GitHub. Further business-rule review and screenshot evidence remain.

## 8. Leave Data Quality Finding — ML Records

A read-only PostgreSQL review identified seven approved ML leave records, each containing 130 days, totaling 910 days.

A separate overlap query identified 14 overlapping pairs among these records.

**Assessment:** This pattern requires business-rule validation. It may represent synthetic test data, duplicate or overlapping requests, or a valid special leave arrangement. The records have not been modified.

**Recommended follow-up:** Confirm the intended ML leave policy and whether overlapping approved requests are permitted. If not, investigate the source records and add an appropriate data-quality check.

