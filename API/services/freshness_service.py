import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_LOG = ROOT / "Logs" / "pipeline_runs.csv"


def get_freshness():
    if not PIPELINE_LOG.exists():
        return {
            "latest_pipeline_status": "UNKNOWN",
            "latest_pipeline_run": None,
            "last_successful_refresh": None,
            "freshness_status": "UNKNOWN",
            "freshness_statement": "Pipeline refresh history is unavailable.",
        }

    with PIPELINE_LOG.open("r", newline="", encoding="utf-8") as file:
        runs = list(csv.DictReader(file))

    if not runs:
        return {
            "latest_pipeline_status": "UNKNOWN",
            "latest_pipeline_run": None,
            "last_successful_refresh": None,
            "freshness_status": "UNKNOWN",
            "freshness_statement": "No pipeline runs are recorded.",
        }

    latest_run = max(
        runs,
        key=lambda row: row["finished_at_utc"],
    )

    successful_runs = [
        row for row in runs
        if row["status"].upper() == "SUCCESS"
    ]

    latest_success = (
        max(successful_runs, key=lambda row: row["finished_at_utc"])
        if successful_runs else None
    )

    last_successful_refresh = (
        latest_success["finished_at_utc"] if latest_success else None
    )

    if latest_run["status"].upper() != "SUCCESS":
        freshness_status = "WARNING"
        statement = (
            "The latest pipeline run failed. "
            "Data reflects the last successful refresh."
        )
    elif last_successful_refresh:
        refreshed_at = datetime.fromisoformat(
            last_successful_refresh.replace("Z", "+00:00")
        )
        age_hours = (
            datetime.now(timezone.utc) - refreshed_at
        ).total_seconds() / 3600

        freshness_status = "FRESH" if age_hours <= 24 else "STALE"
        statement = (
            "Data was refreshed successfully within the last 24 hours."
            if freshness_status == "FRESH"
            else "The last successful refresh was more than 24 hours ago."
        )
    else:
        freshness_status = "UNKNOWN"
        statement = "No successful pipeline refresh is recorded."

    return {
        "latest_pipeline_status": latest_run["status"],
        "latest_pipeline_run": latest_run["finished_at_utc"],
        "last_successful_refresh": last_successful_refresh,
        "freshness_status": freshness_status,
        "freshness_statement": statement,
    }
