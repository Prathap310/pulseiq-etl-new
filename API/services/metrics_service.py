from decimal import Decimal

from psycopg2.extras import RealDictCursor

from API.database import get_db_connection
from API.services.metric_config import METRICS
from API.services.freshness_service import get_freshness


def serialize_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def get_metric_data(metric_id):
    metric_id = metric_id.upper()

    if metric_id not in METRICS:
        raise ValueError(f"Unsupported metric ID: {metric_id}")

    config = METRICS[metric_id]

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    metric_id,
                    metric_name,
                    business_definition,
                    formula,
                    source_table,
                    grain,
                    time_period,
                    owner_team,
                    unit,
                    good_direction,
                    caveat,
                    minimum_group_size
                FROM dw.metric_catalog
                WHERE metric_id = %s
            """, (metric_id,))

            definition = cur.fetchone()

            if definition is None:
                raise LookupError(
                    f"Definition not found for metric {metric_id}"
                )

            view = config["view"]
            value_column = config["value_column"]
            date_column = config["date_column"]
            dimension_column = config["dimension_column"]

            if date_column and dimension_column:
                query = f"""
                    SELECT
                        {date_column} AS period,
                        {dimension_column} AS dimension,
                        {value_column} AS value,
                        privacy_threshold_met
                    FROM {view}
                    ORDER BY {date_column} DESC, {dimension_column}
                    LIMIT %s
                """
            elif date_column:
                query = f"""
                    SELECT
                        {date_column} AS period,
                        {value_column} AS value,
                        privacy_threshold_met
                    FROM {view}
                    ORDER BY {date_column} DESC
                    LIMIT %s
                """
            else:
                query = f"""
                    SELECT
                        {value_column} AS value,
                        privacy_threshold_met
                    FROM {view}
                    LIMIT %s
                """

            cur.execute(query, (100,))
            records = cur.fetchall()

    return {
        "metric": {
            key: serialize_value(value)
            for key, value in definition.items()
        },
        "metric_id": metric_id,
        "source_view": config["view"],
        "minimum_group_size": config["minimum_group_size"],
        "records": [
            {
                key: serialize_value(value)
                for key, value in record.items()
            }
            for record in records
        ],
        "freshness": get_freshness(),
    }
