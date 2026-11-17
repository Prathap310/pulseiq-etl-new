METRICS = {
    "M01": {
        "view": "dw.m01_headcount",
        "value_column": "headcount",
        "date_column": "month_start_date",
        "dimension_column": "department_id",
        "minimum_group_size": 5,
    },
    "M07": {
        "view": "dw.m07_gross_pay",
        "value_column": "gross_pay",
        "date_column": "period_end_date",
        "dimension_column": "department_id",
        "minimum_group_size": 5,
    },
    "M13": {
        "view": "dw.m13_attendance_rate",
        "value_column": "attendance_rate",
        "date_column": "period_end_date",
        "dimension_column": "department_id",
        "minimum_group_size": 5,
    },
    "M22": {
        "view": "dw.m22_task_completion_rate",
        "value_column": "task_completion_rate_pct",
        "date_column": None,
        "dimension_column": None,
        "minimum_group_size": 5,
    },
    "M27": {
        "view": "dw.m27_high_risk_share",
        "value_column": "high_risk_share_pct",
        "date_column": "as_of_date",
        "dimension_column": "department_id",
        "minimum_group_size": 10,
    },
}
