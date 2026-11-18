# Task 18 — Self-service KPI Explorer Evidence

## 1. Implementation
- Created Src/kpi_explorer.py for KPI definitions, role rules and privacy checks.
- Created Src/kpi_explorer_sql.py for governed KPI query builders.
- Created Src/kpi_explorer_service.py for authentication, authorization, query execution and privacy filtering.
- Created 05_Starter/pages/2_KPI_Explorer.py as a separate Streamlit page.
- Existing Task 17 page was preserved.

## 2. Enabled KPIs
M01-M15, M22, M23, M25 and M27.
Disabled metrics remain unavailable.

## 3. Authentication and roles
- ADMIN: company, department and team-level permissions as supported by the KPI.
- HR: company and department-level permissions.
- MANAGER: authorized team-level task metrics only, restricted to teams led by the verified employee.
- EXECUTIVE: company-level permissions.

Demo identities:
- admin.demo — ADMIN
- hr.demo — HR — EMP-0719
- manager.demo — MANAGER — EMP-0046
- exec.demo — EXECUTIVE — EMP-0006

## 4. KPI validation
- M01 company headcount: 441.
- M27 latest snapshot: 2026-09-30.
- M27 company high-risk share: 10.12% (43 of 425 employees).
- M27 department results: 10 eligible departments.
- Small groups are excluded by metric-specific privacy thresholds.

## 5. Privacy break test
Latest snapshot (2026-09-30):
- D01: 163 — ALLOW
- D02: 25 — ALLOW
- D03: 50 — ALLOW
- D04: 44 — ALLOW
- D05: 12 — ALLOW
- D06: 58 — ALLOW
- D07: 19 — ALLOW
- D08: 16 — ALLOW
- D09: 28 — ALLOW
- D10: 10 — ALLOW

Older snapshot (2026-03-31):
- D01: 3 — SUPPRESS
- D03: 1 — SUPPRESS
- D04: 1 — SUPPRESS

Snapshots are not combined. The latest snapshot is used for M27.

## 6. Automated tests
Task 18 regression suite: 72 passed.

## 7. Local application validation
- Streamlit application launched successfully.
- KPI Explorer page opened successfully.
- ADMIN authentication succeeded.
- M01 company query returned 441.
- HR authentication and KPI access tested.
- Manager and executive role access tested by user.

## 8. Remaining release checks
- Capture and retain role-view screenshots.
- Run final regression and syntax checks.
- Review Git changes and stage only Task 18 files.
- Commit, push and validate Streamlit Cloud deployment.
