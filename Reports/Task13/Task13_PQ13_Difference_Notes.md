# Task 13 – PQ-13 Comparison and Difference Notes

## Comparison status
Status: Pending – official reference data not available.

The Task 13 department-month dataset has been generated for April 2025 to September 2026.

## Dataset validation
- Departments: 11
- Reporting months: 18
- Expected department-month rows: 198
- Actual rows: 198
- Duplicate department-month keys: 0
- General suppressed groups: 18
- Attrition suppressed groups: 30

## Comparison limitations
The official PQ-13 reference summary (reference_summary_dept_month) and unlock details have not yet been located.

Therefore, an official reference-to-output comparison and numerical difference calculation cannot yet be completed.

## Calculation and governance notes
- Fact tables were aggregated independently before joining at department-month grain.
- Approved leave records were used for leave aggregation.
- Cross-month leave allocation uses weekday proportions because an official allocation rule was not available.
- Attrition follows the M04 minimum group size of 10.
- General metric suppression follows a minimum group size of 5.

## Next action
Obtain the official PQ-13 unlock details and reference summary, then calculate and document differences.
