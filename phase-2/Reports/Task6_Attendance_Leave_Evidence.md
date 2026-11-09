# Task 6 — Attendance and Leave Trends Dashboard

## 1. Objective

Build an interactive dashboard to analyze employee attendance, late arrivals, overtime, approved leave, and holidays using the PostgreSQL warehouse.

## 2. Implementation

- **Application:** Streamlit
- **Database:** PostgreSQL
- **Schema:** `dw`
- **Dashboard file:** `05_Starter/app_task6.py`
- **Attendance source:** `dw.fact_attendance_monthly`
- **Leave source:** `dw.fact_leave`
- **Calendar source:** `dw.dim_date`

## 3. Dashboard Features

- Monthly attendance rate by department
- Monthly late arrivals and overtime
- Approved leave days by leave type
- Holiday timeline
- Unusual-month analysis
- Department filter and detailed department table
- KPI cards for attendance, late arrivals, overtime, and approved leave

## 4. Validation Evidence

### 4.1 Python Syntax Validation

**Command:**

```powershell
python -m py_compile .\05_Starter\app_task6.py
```

**Result:** Passed with no syntax errors.

### 4.2 Attendance Validation

PostgreSQL weighted attendance rates were checked for 18 monthly periods from April 2025 through September 2026.

- **Lowest rate:** May 2026 — 92.87%
- **Highest rate:** July 2025 — 95.56%
- **Latest period:** September 2026 — 95.18%

Attendance rates were validated using aggregated attendance and scheduled-day totals rather than an unweighted average of department percentages.

### 4.3 Approved Leave Validation

PostgreSQL totals were checked for approved leave requests and leave days.

| Leave type | Approved requests | Approved leave days |
|---|---:|---:|
| EL | 1,130 | 2,336 |
| CL | 977 | 1,995 |
| SL | 836 | 1,769 |
| ML | 7 | 910 |
| BL | 80 | 137 |
| LOP | 58 | 129 |

**Finding:** ML has 910 approved leave days across seven requests and requires business-rule review. The finding is documented in Section 8.

### 4.4 Holiday Validation

- Calendar dates: 2,647
- Dates flagged as holidays: 19

### 4.5 Overtime Validation

The highest monthly overtime totals were:

1. December 2025 — 787.0 hours
2. March 2026 — 610.5 hours
3. September 2026 — 599.5 hours

### 4.6 Interactive Validation

- The dashboard loaded successfully.
- Dashboard charts and KPI cards were displayed.
- The department filter was tested.
- Selecting Engineering updated the displayed metrics.

The validation recorded above covers the checks performed to date; it does not establish that every possible filter combination or acceptance criterion has been tested.

## 5. Git Evidence

- **Dashboard file:** `05_Starter/app_task6.py`
- **Commit:** `c721031`
- **Commit message:** `Add Task 6 attendance and leave dashboard`
- **Branch:** `master`
- **Push to `origin/master`:** Successful

The dashboard implementation was committed and pushed. The evidence report and screenshots should be checked separately for their latest Git status.

## 6. Screenshot Evidence

Dashboard screenshots have been captured and saved in the project's `Reports` folder.

Expected screenshot files:

1. `Reports/Task6_Dashboard_Overview.png`
2. `Reports/Task6_Attendance_Charts.png`
3. `Reports/Task6_Overtime_LateArrivals.png`
4. `Reports/Task6_Leave_Days_By_Type.png`
5. `Reports/Task6_Holiday_Timeline.png`
6. `Reports/Task6_Unusual_Months.png`
7. `Reports/Task6_Department_Details.png`

Additional screenshot copies may exist with numbered suffixes. They have not been removed.

## 7. Remaining Review

- Confirm the official Task 6 acceptance criteria, if a separate rubric is provided.
- Review the ML leave-day totals and date ranges against the intended business rules and source-data conventions.
- Complete a final visual review of the captured screenshots for readability and completeness.
- Verify Git status and commit the updated evidence report and intended screenshot files without staging unrelated project changes.

## 8. Leave Data Review — ML Records

The leave-type dictionary defines ML as Maternity Leave, paid, with an annual quota of 182 days.

Seven approved ML requests were found, each recording 130 leave days, for a total of 910 days.

A date-overlap query identified 14 overlapping pairs across different employees. Follow-up checks in both PostgreSQL and the source CSV found no overlapping approved ML requests for the same employee.

### Assessment

The current checks do not establish a duplicate-request issue. The recorded leave-day totals and date ranges should be reviewed against the intended leave policy and source-data conventions before any correction is considered.

### Action Taken

No warehouse records were modified. The finding is documented for business-rule review.

## 9. Conclusion

The Task 6 Attendance and Leave Trends Dashboard has been implemented using Streamlit and PostgreSQL. Python syntax validation passed, selected warehouse aggregates were checked, and the department filter was tested successfully. Dashboard screenshots have been captured for visual evidence, and the ML leave-data finding is documented for further business-rule review.

**Status:** Implementation and initial validation completed. Final completion remains subject to confirming any additional official acceptance criteria and completing the remaining review items.
