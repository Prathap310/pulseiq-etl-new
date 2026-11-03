# Task 13 – Cross-Department Impact View Evidence

## 1. Objective
Create a combined department-level monthly view using headcount, payroll, attendance and leave data.

## 2. Reporting period
April 2025 to September 2026.

## 3. Data processing
- Aggregated each source independently at department-month grain.
- Joined the aggregated datasets using department_id and month_start_date.
- Included employer cost, overtime cost, attendance rate, approved leave days and leave days per head.
- Applied minimum group-size suppression.

## 4. Validation results
- Expected rows: 198
- Actual rows: 198
- Departments: 11
- Months: 18
- Duplicate department-month keys: 0
- General suppressed groups: 18
- Attrition suppressed groups: 30

## 5. Dashboard testing
The Streamlit dashboard was launched successfully.
Verified:
- Department selection filter
- Employer cost comparison chart
- Average monthly attrition chart
- Department summary
- Monthly department data
- CSV download option

## 6. Metric governance
- General metric minimum group size: 5.
- M04 attrition minimum group size: 10.
- D00 metrics are suppressed because the group is below the minimum size.
- D10 has only 6 eligible months for attrition.

## 7. Assumptions and limitations
- Cross-month approved leave is allocated using weekday proportions.
- No official leave allocation rule was found in the available data contract.
- PQ-13 reference comparison remains pending because the official reference summary and unlock details have not been located.

## 8. Evidence status
Dataset generation and dashboard testing completed.
Official PQ-13 comparison and final sign-off remain pending.
