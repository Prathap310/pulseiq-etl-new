from API.services.lineage_config import LINEAGE


def get_metric_lineage(metric_id):
    metric_id = metric_id.upper()

    if metric_id not in LINEAGE:
        raise ValueError(f"Unsupported metric ID: {metric_id}")

    lineage = LINEAGE[metric_id]

    return {
        "metric_id": metric_id,
        "metric_name": lineage["metric"],
        "lineage": [
            {
                "stage": "Raw Data",
                "details": lineage["raw_source"],
            },
            {
                "stage": "ETL",
                "details": lineage["etl_process"],
            },
            {
                "stage": "Warehouse",
                "details": lineage["warehouse_table"],
            },
            {
                "stage": "Metric View",
                "details": lineage["metric_view"],
            },
            {
                "stage": "Dashboard",
                "details": lineage["dashboard"],
                "status": "Planned integration",
            },
        ],
    }
