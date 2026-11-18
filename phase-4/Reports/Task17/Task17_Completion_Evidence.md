# Task 17 – Custom KPI Builder Evidence

## 1. Implementation Files
- Src/kpi_builder.py
- 05_Starter/pages/1_Custom_KPI_Builder.py
- Docs/custom-kpi-builder.md
- tests/test_kpi_builder.py

## 2. KPI Preview Validation
The five sample KPI previews were tested in the Streamlit dashboard:
1. Overtime hours per head
2. Unpaid leave days by month
3. Employer cost per head
4. Late arrivals per present day
5. Overdue receivables by client

Preview testing was reported successful.

## 3. Automated Test Results
Evidence file: Reports/Task17/test_results.txt

- Tests passed: 12
- Subtests passed: 10
- Failures: 0

Security and validation coverage includes:
- SQL injection protection using bound parameters
- Unknown table rejection
- Unknown column rejection
- Invalid aggregation and operator rejection
- Division-by-zero protection
- Invoice status filtering
- Minimum group-size validation
- Approval validation
- Approved-metric visibility

## 4. Database Governance
The dw.custom_kpi_definitions table was created.
Reader and admin permission roles were created and their table permissions verified.

## 5. Outstanding Work
- Separate dashboard and admin login accounts are not yet configured.
- Persistent KPI creation and dashboard approval workflow still require implementation and verification.
- Final end-to-end authorization testing remains pending.

## 6. Evidence Location
Reports/Task17/test_results.txt

## 7. Current Status
Core KPI query generation, validation, and preview testing are successful.
Task 17 is partially completed; outstanding governance and authorization workflow items must be completed before final sign-off.
