# PulseIQ - PQ-01 Task 1 Delivery Report

Generated (UTC): 2026-10-19

## Implementation

- ETL entry point: `Src/etl.py`
- Validation rules: `Src/validate_data.py`
- Pandera schema: `Src/pandera_schemas.py`
- Pipeline runner and run log: `Src/run_pipeline.py` and `Logs/pipeline_runs.csv`
- Docker image definition: `Dockerfile`
- Docker Compose configuration: `docker-compose.yml`
- Clean outputs: `Data/Clean/`
- Quarantined outputs: `Data/Rejected/`
- Contract notes: `Docs/data-contract-notes.md`
- Metric dictionary: `Docs/metric-dictionary.md`
- Automated tests: `tests/`
- Dependencies: `requirements.txt`

## Latest validation counts

| Feed | Input rows | Clean rows | Rejected rows | Counts reconcile |
|---|---:|---:|---:|---|
| fact_task | 28868 | 28848 | 20 | True |
| fact_anomaly | 405 | 0 | 405 | True |
| fact_attrition_risk | 430 | 425 | 5 | True |
| fact_forecast | 72 | 72 | 0 | True |
| **Total** | **29775** | **29345** | **430** | **True** |

## Verification status

- Docker image built successfully.
- `docker compose config` passed.
- ETL pipeline executed successfully using `docker compose run --rm etl`.
- Docker-generated clean files, rejected files, and logs were verified in the Windows project folders.
- All 10 automated tests passed after Docker execution.
- Python syntax compilation passed for the ETL entry point, validator, pipeline runner, Pandera schema, and test files.
- Repeated pipeline runs produced consistent feed counts.
- All four feeds reconcile: clean rows plus rejected rows equal input rows.

## Outstanding data-quality issues

- **fact_anomaly:** 405 rows quarantined because `scored_at` has no explicit timezone. Confirm UTC interpretation with the data owner before changing the data or relaxing validation.
- **fact_anomaly:** The separate `attendance_monthly_features` source is unavailable, so 221 attendance record references could not be verified.
- **fact_attrition_risk:** 5 rows with `as_of_date` of `2026-03-31` are quarantined against the majority batch date `2026-09-30`. Confirm the intended batch date with the data owner.
- **fact_task:** 20 rows quarantined: 12 have `completed_date` earlier than `started_date`, and 8 have missing completion dates despite status `Done`.
- **Git:** No Git repository was found in the checked project directory or nearby folders. No repository was initialized.

## Current status

The ETL pipeline, Pandera integration, automated tests, and Docker execution are working. Counts reconcile, and rejected rows retain rejection reasons.

**Final production sign-off is still pending** data-owner decisions on the outstanding data-quality issues and final contract review.
