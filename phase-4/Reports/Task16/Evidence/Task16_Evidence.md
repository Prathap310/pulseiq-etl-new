# Task 16 - Automated Report Builder & Release Candidate

## 1. Report Builder
- Script: Src/build_report.py
- Command: python Src/build_report.py --month YYYY-MM
- Output formats: PDF and Excel
- Sample reports generated for August 2026 and September 2026.

## 2. Management Report Contents
The report uses five warehouse metric views:
1. M01 - Headcount
2. M04 - Monthly Attrition
3. M09 - Employer Payroll Cost
4. M13 - Attendance Rate
5. M17 - Net Profit

The Excel report contains a Summary sheet, five metric sheets, and five charts.

## 3. Date Range and Data Cut-off
The report displays the selected reporting month and data cut-off date.

## 4. Monthly Scheduling
- Scheduler script: Src/run_monthly_report.py
- Scheduler: Windows Task Scheduler
- Task name: PulseIQ-Monthly-Report
- Schedule: First day of every month at 9:00 AM
- Next scheduled run: 1 December 2026, 9:00 AM

## 5. Scheduling Test
- Manual scheduled-task execution: Successful
- Last task result: 0
- Last run: 16 November 2026
- September 2026 PDF and Excel reports were regenerated successfully.

## 6. Sample Report Files
- management_report_2026_08.pdf
- management_report_2026_08.xlsx
- management_report_2026_09.pdf
- management_report_2026_09.xlsx

October 2026 files were also generated, but the warehouse data currently ends in September 2026. October output is therefore a no-data test, not a completed monthly management report.

## 7. Remaining Validation
- Clean-environment test: Passed (fresh virtual environment, dependencies installed, scripts compiled, September PDF and Excel generated)
- Final README setup and run instructions: Pending
- Release tag v1.0.0-rc1: Pending

