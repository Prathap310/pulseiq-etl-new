# Task 3 - Data Quality Gatekeeper Evidence

- Evidence refreshed (UTC): 2026-10-21T13:44:26+00:00
- Latest recorded check run (UTC): 2026-10-21 13:21:52.836926+00:00
- Checks reported: 14
- PASS: 3
- FAIL: 11
- ERROR: 0

| Check | Name | Status | Bad rows | Details |
|---|---|---|---:|---|
| DQ-C01 | Payroll equals ledger | FAIL | 5 | severity=critical; bad_rows=5 |
| DQ-C02 | Ledger balanced | PASS | 0 | severity=critical; bad_rows=0 |
| DQ-C03 | Unique payroll rows | FAIL | 2 | severity=critical; bad_rows=2 |
| DQ-C04 | No orphan employees | FAIL | 2 | severity=critical; bad_rows=2 |
| DQ-C05 | No attendance after exit month | FAIL | 4 | severity=warning; bad_rows=4 |
| DQ-C06 | Unpaid leave deducted | FAIL | 41 | severity=warning; bad_rows=41 |
| DQ-C07 | Invoice arithmetic | FAIL | 1 | severity=warning; bad_rows=1 |
| DQ-C08 | Expense arithmetic | FAIL | 1 | severity=warning; bad_rows=1 |
| DQ-C09 | Task dates sensible | FAIL | 20 | severity=warning; bad_rows=20 |
| DQ-C10 | Leave dates sensible | FAIL | 2 | severity=warning; bad_rows=2 |
| DQ-C11 | AI feeds fresh | FAIL | 835 | severity=warning; bad_rows=835 |
| DQ-C12 | Dimension history does not overlap | PASS | 0 | severity=critical; bad_rows=0 |
| DQ-C13 | Pipeline freshness | PASS | 0 | severity=critical; bad_rows=0 |
| DQ-C14 | Minimum group size | FAIL | 1419 | severity=critical; metric_group_violations=1419; by_metric=[M01=81, M02=314, M03=227, M04=245, M05=231, M06=231, M10=18, M11=18, M12=18, M13=18, M14=18, M22=0, M23=0, M25=0, M27=0]; M07/M08/M09/M15 excluded: employee-level grain requires a separate exposure-policy decision. |

## Interpretation

- Failed checks remain visible and are not treated as successful.
- Critical checks should block acceptance of a load when they fail; warning checks should be reviewed and documented according to the agreed policy.
- This report reflects the latest stored result for each check. It does not prove every check has been tested with a deliberately bad row.
- The official `unlock_PQ-03` planted-issues comparison is pending because that file was not found in the project.
- Do not mark Task 3 fully verified until the planted-issues comparison and negative tests are completed.

## Additional Verification Evidence

### Automated unit tests
- Full test suite: 16 tests passed, 0 failures.
- Evidence file: `Reports/Task3_unit_test_results.txt`.
- Existing ETL validation and pipeline output tests passed.
- Six additional isolated DQ runner tests passed, covering the 14-check definition, severity definitions, C13 freshness behavior, and C14 mocked-result counting.
- Limitation: mocked C14 results do not prove SQL defect detection against deliberately planted database records.

### Read-only DQ verification
- Evidence file: `Reports/Task3_readonly_check_verification.csv`.
- All 14 check queries were independently executed in a read-only transaction and rolled back without database changes.
- Results matched the recorded summary: 3 PASS and 11 FAIL.
- C11 supporting evidence: `Reports/C11_freshness_evidence.csv`.

### Negative-test status and limitations
- Checklist: `Reports/Task3_negative_test_checklist.csv`.
- The checklist records 14 of 14 checks as VERIFIED. See the final verification update below.
- C13 has isolated tests for missing, fresh, and stale pipeline summary files.
- C14 has a mocked-result unit test and an actual SQL negative test for metric M10. The test detected 4 employees against the configured minimum of 5 in the isolated test database; other metric-specific queries have not all been individually tested.
- The official `unlock_PQ-03` planted-issues fixture was not found in the project files searched, so comparison remains pending.
- C14 excludes M07, M08, M09, and M15 pending a separate exposure-policy decision.
- Current warehouse quality failures remain unresolved. Critical failures must not be treated as accepted loads.

### Completion decision
Negative-test verification and automated unit testing are complete. Final sign-off remains conditional on review of C14 exclusions, outstanding production DQ findings, and the official planted-issues comparison if required.

## Final Verification Update â€” 2026-10-21

### Negative-test checklist
- Verified checks: 14 of 14.
- DQ-C01 through DQ-C12 and DQ-C14 were tested using the actual SQL in the isolated pulseiq_dq_test database, with temporary test records rolled back after detection.
- DQ-C13 was verified through focused unit tests for missing, fresh, and stale pipeline summaries.
- Checklist: Reports/Task3_negative_test_checklist.csv.

### Full automated test suite
- Result: 16 tests passed; 0 failures.
- DQ runner tests: 6 passed.
- ETL validation tests: 6 passed.
- Pipeline output tests: 4 passed.

### Outstanding production and policy findings
- Passing negative tests proves detection behavior, not that existing production DQ failures are resolved.
- Review the C14 exclusions for M07, M08, M09, and M15 and document the exposure-policy decision.
- Existing warehouse quality failures remain subject to investigation; critical failures must not be accepted without resolution or an explicitly approved exception.
- The official unlock_PQ-03 planted-issues comparison remains pending if the supplied fixture is unavailable.

### Completion status
Negative-test verification and automated unit testing are complete. Final Task 3 sign-off remains conditional on the outstanding policy decisions, production DQ findings, and required planted-issues comparison.

