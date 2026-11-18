# Task 19 – Metrics API and Data Lineage

## 1. Objective
Develop and deploy a FastAPI-based Metrics API that provides governed business metrics, metric definitions, source information, data lineage, and data freshness.

## 2. Selected Metrics

| Metric ID | Metric Name | Warehouse Metric View |
|---|---|---|
| M01 | Headcount | dw.m01_headcount |
| M07 | Gross Pay | dw.m07_gross_pay |
| M13 | Attendance Rate | dw.m13_attendance_rate |
| M22 | Task Completion Rate | dw.m22_task_completion_rate |
| M27 | High-Risk Share | dw.m27_high_risk_share |

## 3. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/v1/metrics | List available metrics |
| GET | /api/v1/metrics/{metric_id} | Retrieve metric details and values |
| GET | /api/v1/metrics/{metric_id}/lineage | Retrieve metric data lineage |
| GET | /api/v1/freshness | Retrieve pipeline freshness information |
| GET | /health | Check API health |
| GET | /docs | Interactive Swagger API documentation |

## 4. Data Lineage

The API provides the following lineage stages:

1. Raw Data
2. ETL
3. Warehouse
4. Metric View
5. Dashboard

Dashboard integration is documented as planned where a live connection has not been verified.

## 5. Data Freshness

The API reads pipeline execution history from Logs/pipeline_runs.csv.

Freshness statuses:

- FRESH: Latest pipeline run succeeded and the last successful refresh was within 24 hours.
- STALE: Latest pipeline run succeeded, but the last successful refresh was more than 24 hours ago.
- WARNING: Latest pipeline run failed.
- UNKNOWN: Pipeline refresh history is unavailable.

The deployed API returned STALE because its latest successful refresh in the available pipeline history was 2026-10-19 11:25:11 UTC.

## 6. Local Testing

- FastAPI application started successfully using Uvicorn.
- Swagger documentation opened successfully.
- Health endpoint returned a healthy response.
- Metrics list returned five metric IDs.
- Individual metric endpoints were tested successfully.
- Metric lineage endpoint was tested successfully.
- Freshness endpoint returned pipeline status and refresh information.

## 7. Deployment

Hosting platform: Render

GitHub repository:
https://github.com/Prathap310/pulseiq-etl-new

Branch: master

Deployed API:
https://pulseiq-etl-new.onrender.com

Swagger documentation:
https://pulseiq-etl-new.onrender.com/docs

Health endpoint:
https://pulseiq-etl-new.onrender.com/health

Metrics endpoint:
https://pulseiq-etl-new.onrender.com/api/v1/metrics

Freshness endpoint:
https://pulseiq-etl-new.onrender.com/api/v1/freshness

Deployment status: Successful

## 8. Deployment Verification

The following deployed endpoints were verified in the browser:

- Swagger documentation loaded successfully.
- Health endpoint returned HTTP 200.
- Metrics endpoint returned five metrics: M01, M07, M13, M22 and M27.
- Freshness endpoint returned a valid response.
- Individual metric details endpoint returned data.
- M01 lineage endpoint returned lineage information.

## 9. Project Files

- API/main.py
- API/database.py
- API/routers/metrics.py
- API/services/metric_config.py
- API/services/metrics_service.py
- API/services/freshness_service.py
- API/services/lineage_config.py
- API/services/lineage_service.py
- API/README.md
- Procfile
- requirements.txt

## 10. Conclusion

The Task 19 Metrics API has been implemented, tested locally, and deployed successfully on Render. The API exposes five governed metrics, metric details, data lineage, health information, and data freshness information.
