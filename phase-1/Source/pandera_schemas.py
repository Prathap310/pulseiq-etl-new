import pandera.pandas as pa
from pandera import Check




def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False

FACT_ANOMALY_SCHEMA = pa.DataFrameSchema(
    {
        "result_id": pa.Column(
            str,
            checks=Check.str_matches(r"^AN-\d{4}$"),
            nullable=False,
            unique=True,
        ),
        "source_dataset": pa.Column(
            str,
            checks=Check.isin(
                ["attendance_monthly_features", "payroll_monthly_features"]
            ),
            nullable=False,
        ),
        "record_id": pa.Column(str, nullable=False),
        "employee_id": pa.Column(str, nullable=False),
        "period": pa.Column(str, nullable=False),
        "anomaly_score": pa.Column(
            float,
            checks=Check.in_range(0, 1),
            nullable=False,
            coerce=True,
        ),
        "flagged": pa.Column(
            str,
            checks=Check.isin(["Y", "N"]),
            nullable=False,
        ),
        "reason_code": pa.Column(str, nullable=False),
        "reason_text": pa.Column(str, nullable=False),
        "money_at_risk": pa.Column(
            str,
            checks=Check(
                lambda series: series.map(
                    lambda value: value is None
                    or str(value).strip() == ""
                    or _is_number(value)
                ).all()
            ),
            nullable=True,
        ),
        "model_version": pa.Column(str, nullable=False),
        "scored_at": pa.Column(str, nullable=False),
    },
    strict=False,
    coerce=False,
)
