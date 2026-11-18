# PulseIQ ETL — Release Notes

## Release
- Version: 1.0.0 (proposed; not approved or tagged)
- Project: PulseIQ ETL
- Release status: Pending final validation and approval
- Reporting data cut-off: 30 September 2026

## Included
- ETL processing for workforce, payroll, attendance, leave, expense, invoice and task data.
- PostgreSQL analytics warehouse with dimensional and fact tables.
- Data quality checks DQ-C01 through DQ-C14.
- Governed KPI views and minimum-group-size privacy controls.
- Department-level workforce and operational analysis.
- Attrition-risk and headcount forecasting.
- AI anomaly analysis and financial-impact reporting.
- Automated monthly PDF and Excel management reports.
- Custom KPI Builder and KPI Explorer.
- Metrics API with metric lineage and freshness endpoints.
- Streamlit dashboard and Render-hosted Metrics API.

## Validation evidence and known limitations
The latest detailed DQ evidence supplied for review is the Task 17 final run dated 17 November 2026, 03:50:02 UTC:
- 14 checks total: 12 PASS, 2 FAIL, 0 ERROR.
- DQ-C01 FAIL: June 2026 D01 payroll-to-ledger difference of INR 18,450 (ledger higher), journal JE-002094, source PR-2026-06. No unsupported adjustment has been made.
- DQ-C11 FAIL: 405 stale anomaly records. The source `scored_at` value is 2026-10-01 02:00:00 without an explicit timezone; data-owner confirmation that it represents UTC is pending. Do not fabricate timestamps or scores.
- DQ-C14 PASS for metrics included in the tested exposure checks. M07, M08, M09 and M15 remain excluded pending a separate employee-level exposure-policy decision.
- Forecast horizon: October 2026 through March 2027; forecast accuracy is unverified because actuals for that period were not available in the reviewed evidence.
- September 2026 governed net profit: INR 14,985,979.13. The reviewed report does not provide cash flow or cash balance; net profit is not cash.
- Official PQ-13 reference comparison and sign-off remain pending.
- Metrics API freshness endpoint was reported STALE in reviewed Task 19 deployment evidence.

## Task 20 deliverables
- Board Pack: 9-slide draft included in this package.
- Handover report and demo script included.
- Demo recording: previously created and opened successfully in the user's local environment, but the original MP4 is no longer present in the working tree after `git clean -fd`. It must be recovered or recreated and revalidated.
- Improvement guide: previously committed on branch `task20/final-release-readiness`, commit `3164d54`.
- Final approval and Git tag `v1.0.0`: pending.

## Release conditions
1. Resolve or formally accept DQ-C01 with Finance/Payroll evidence.
2. Assign an owner and remediation plan for DQ-C11; confirm source timestamp timezone.
3. Record the employee-level exposure-policy decision for M07, M08, M09 and M15.
4. Complete official PQ-13 reference comparison and sign-off.
5. Re-run final validation against the release candidate and archive console/CSV evidence.
6. Review and approve the Board Pack and handover.
7. Validate the demo recording and final repository contents.
8. Obtain release approval before creating tag `v1.0.0`.
