# Task 19 – Metrics API and Data Lineage

## 1. Overview

PulseIQ Metrics API provides access to five governed workforce and operational metrics through FastAPI.

API version: 1.0.0

Interactive API documentation:
`/docs`

OpenAPI specification:
`/openapi.json`

## 2. Selected Metrics

| Metric ID | Metric Name | Warehouse View | Privacy Threshold |
|---|---|---|---|
| M01 | Headcount | dw.m01_headcount | 5 employees |
| M07 | Gross Pay | dw.m07_gross_pay | 5 employees |
| M13 | Attendance Rate | dw.m13_attendance_rate | 5 employees |
| M22 | Task Completion Rate | dw.m22_task_completion_rate | 5 non-cancelled tasks |
| M27 | High-Risk Share | dw.m27_high_risk_share | 10 employees |

## 3. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | API information |
| GET | /health | API health check |
| GET | /api/v1/metrics | List available metrics |
| GET | /api/v1/metrics/{metric_id} | Metric definition and values |
| GET | /api/v1/metrics/{metric_id}/lineage | Metric lineage |
| GET | /api/v1/freshness | Pipeline freshness information |

## 4. Example Requests

### List Metrics

`GET /api/v1/metrics`

Example response:

    {
      "available_metrics": ["M01", "M07", "M13", "M22", "M27"],
      "count": 5
    }

### Retrieve a Metric

`GET /api/v1/metrics/M01`

The response includes:
- Metric definition
- Formula
- Source table
- Reporting grain
- Unit
- Metric values
- Privacy threshold status
- Data freshness information

### Retrieve Lineage

`GET /api/v1/metrics/M01/lineage`

The lineage stages are:
1. Raw Data
2. ETL
3. Warehouse
4. Metric View
5. Dashboard

The dashboard destination is currently documented as a planned integration.

### Retrieve Freshness

`GET /api/v1/freshness`

Example response:

    {
      "latest_pipeline_status": "FAILED",
      "latest_pipeline_run": "2026-11-16T18:06:00+00:00",
      "last_successful_refresh": "2026-11-09T06:08:08+00:00",
      "freshness_status": "WARNING",
      "freshness_statement": "The latest pipeline run failed. Data reflects the last successful refresh."
    }

## 5. Data Freshness Rules

- FRESH: Latest successful refresh is within 24 hours and the latest pipeline run succeeded.
- STALE: Latest successful refresh is older than 24 hours and the latest pipeline run succeeded.
- WARNING: Latest pipeline run failed.
- UNKNOWN: No usable pipeline history is available.

The API reads pipeline execution history from `Logs/pipeline_runs.csv`.

## 6. Data Lineage

Raw CSV source
    |
ETL / Production Loader
    |
PostgreSQL DW fact table
    |
Governed metric view
    |
Dashboard / API consumption

## 7. Privacy and Governance

- Existing warehouse privacy thresholds are preserved.
- Suppressed metric values remain NULL.
- The API returns the existing privacy threshold indicator.
- M27 uses a minimum group size of 10.
- M22 uses a minimum of 5 non-cancelled tasks.
- Only the five configured metric IDs are supported.

## 8. Run Locally

Install dependencies:

`pip install -r requirements.txt`

Start the API:

`python -m uvicorn API.main:app --host 127.0.0.1 --port 8000 --reload`

Open Swagger:

`http://127.0.0.1:8000/docs`

## 9. Deployment

The API entry point is:

`API.main:app`

Deployment requires:
- Python environment
- Dependencies from requirements.txt
- PostgreSQL connection settings
- Logs/pipeline_runs.csv
- Uvicorn application server

Database credentials must be supplied through deployment environment variables or secrets, never committed to Git.
