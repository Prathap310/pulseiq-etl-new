
"""Governed, parameterized custom KPI query builder for PulseIQ.

- SQL identifiers are restricted to TABLES and MEASURES.
- User filter values are always passed as bound parameters.
- Ratio denominators use NULLIF to prevent division by zero.
- Privacy thresholds can be configured per KPI.
- Draft and approved KPI definitions are validated separately.
"""

from __future__ import annotations

import copy
import re
from typing import Any


# ---------------------------------------------------------------------
# 1. WHITELISTED WAREHOUSE TABLES AND COLUMNS
# ---------------------------------------------------------------------

TABLES = {
    "fact_payroll": {
        "sql": "dw.fact_payroll",
        "columns": {
            "employee_id": "employee_id",
            "department_id": "department_id",
            "role_id": "role_id",
            "period_end_date": "period_end_date",
            "overtime_hours_paid": "overtime_hours_paid",
            "lop_days": "lop_days",
            "employer_cost": "employer_cost",
            "gross_pay": "gross_pay",
            "net_pay": "net_pay",
            "headcount_flag": "headcount_flag",
        },
        "privacy_column": "employee_id",
        "privacy_unit": "employees",
    },
    "fact_attendance_monthly": {
        "sql": "dw.fact_attendance_monthly",
        "columns": {
            "employee_id": "employee_id",
            "department_id": "department_id",
            "period_end_date": "period_end_date",
            "late_arrivals": "late_arrivals",
            "present_days": "present_days",
            "scheduled_days": "scheduled_days",
            "half_days_unpaid": "half_days_unpaid",
            "attendance_rate": "attendance_rate",
        },
        "privacy_column": "employee_id",
        "privacy_unit": "employees",
    },
    "fact_invoice": {
        "sql": "dw.fact_invoice",
        "columns": {
            "invoice_id": "invoice_id",
            "client_id": "client_id",
            "due_date": "due_date",
            "invoice_date": "invoice_date",
            "status": "status",
            "balance_due": "balance_due",
            "total_amount": "total_amount",
        },
        "privacy_column": "invoice_id",
        "privacy_unit": "invoices",
    },
    "fact_ledger": {
        "sql": "dw.fact_ledger",
        "columns": {
            "line_id": "line_id",
            "entry_id": "entry_id",
            "entry_date": "entry_date",
            "posting_period": "posting_period",
            "account_code": "account_code",
            "signed_amount_debit_positive":
                "signed_amount_debit_positive",
            "cost_center_department_id":
                "cost_center_department_id",
        },
        "privacy_column": None,
        "privacy_unit": None,
    },
    "fact_task": {
        "sql": "dw.fact_task",
        "columns": {
            "task_id": "task_id",
            "team_id": "team_id",
            "sprint_id": "sprint_id",
            "assignee_employee_id": "assignee_employee_id",
            "story_points": "story_points",
            "created_date": "created_date",
            "started_date": "started_date",
            "due_date": "due_date",
            "completed_date": "completed_date",
            "status": "status",
            "cycle_time_days": "cycle_time_days",
            "completed_on_time": "completed_on_time",
            "is_overdue_at_cutoff": "is_overdue_at_cutoff",
        },
        "privacy_column": "task_id",
        "privacy_unit": "tasks",
    },
}


# ---------------------------------------------------------------------
# 2. ALLOWED AGGREGATIONS AND FILTER OPERATORS
# ---------------------------------------------------------------------

MEASURES = {
    "sum": "SUM",
    "count": "COUNT",
    "count_distinct": "COUNT(DISTINCT",
    "avg": "AVG",
}

OPERATORS = {"=", "in", "between"}

DEFAULT_MINIMUM_GROUP_SIZE = 5

# Dictionary-backed thresholds.
# Task thresholds are measured in tasks, not employees.
METRIC_MINIMUM_GROUP_SIZES = {
    "M01": 5,
    "M02": 5,
    "M03": 5,
    "M04": 10,
    "M05": 10,
    "M06": 10,
    "M07": 5,
    "M08": 5,
    "M09": 5,
    "M10": 5,
    "M11": 5,
    "M12": 5,
    "M13": 5,
    "M14": 5,
    "M15": 5,
    "M22": 5,
    "M23": 5,
    "M25": 5,
    "M27": 10,
}


# ---------------------------------------------------------------------
# 3. FIVE REQUIRED WORKING KPI EXAMPLES
# ---------------------------------------------------------------------

EXAMPLES = [
    {
        "name": "Overtime hours per head",
        "description": (
            "Paid overtime hours divided by distinct employees."
        ),
        "source_table": "fact_payroll",
        "measure": {
            "type": "ratio",
            "numerator": {
                "aggregation": "sum",
                "column": "overtime_hours_paid",
            },
            "denominator": {
                "aggregation": "count_distinct",
                "column": "employee_id",
            },
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "HR Analytics",
        "status": "draft",
        "version": 1,
        "minimum_group_size": 5,
        "privacy_unit": "employees",
    },
    {
        "name": "Unpaid leave days by month",
        "description": (
            "Sum of unpaid leave days by department and month."
        ),
        "source_table": "fact_payroll",
        "measure": {
            "aggregation": "sum",
            "column": "lop_days",
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "Payroll",
        "status": "draft",
        "version": 1,
        "minimum_group_size": 5,
        "privacy_unit": "employees",
    },
    {
        "name": "Employer cost per head",
        "description": (
            "Employer cost divided by distinct paid employees."
        ),
        "source_table": "fact_payroll",
        "measure": {
            "type": "ratio",
            "numerator": {
                "aggregation": "sum",
                "column": "employer_cost",
            },
            "denominator": {
                "aggregation": "count_distinct",
                "column": "employee_id",
            },
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "Finance",
        "status": "draft",
        "version": 1,
        "minimum_group_size": 5,
        "privacy_unit": "employees",
    },
    {
        "name": "Late arrivals per present day",
        "description": (
            "Late check-ins divided by present days."
        ),
        "source_table": "fact_attendance_monthly",
        "measure": {
            "type": "ratio",
            "numerator": {
                "aggregation": "sum",
                "column": "late_arrivals",
            },
            "denominator": {
                "aggregation": "sum",
                "column": "present_days",
            },
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "HR Analytics",
        "status": "draft",
        "version": 1,
        "minimum_group_size": 5,
        "privacy_unit": "employees",
    },
    {
        "name": "Overdue receivables by client",
        "description": (
            "Outstanding invoice balance past its due date."
        ),
        "source_table": "fact_invoice",
        "measure": {
            "aggregation": "sum",
            "column": "balance_due",
        },
        "filters": [
            {
                "column": "status",
                "operator": "in",
                "value": ["DRAFT", "CANCELLED"],
                "exclude": True,
            }
        ],
        "group_by": ["client_id"],
        "time_grain": "month",
        "owner": "Finance",
        "status": "draft",
        "version": 1,
        "minimum_group_size": 5,
        "privacy_unit": "invoices",
    },
]


# ---------------------------------------------------------------------
# 4. COLUMN AND FILTER VALIDATION
# ---------------------------------------------------------------------

def _column(
    definition: dict[str, Any],
    column: str,
) -> str:
    """Return a SQL column only when it is whitelisted."""

    table = TABLES.get(definition.get("source_table"))

    if not table or not isinstance(column, str):
        raise ValueError("Source table or column is not allowed.")

    if column not in table["columns"]:
        raise ValueError(f"Unknown or disallowed column: {column}")

    return table["columns"][column]


def _validate_filter(
    definition: dict[str, Any],
    item: dict[str, Any],
) -> None:
    if not isinstance(item, dict):
        raise ValueError("Each filter must be an object.")

    _column(definition, item.get("column"))

    operator = item.get("operator")

    if operator not in OPERATORS:
        raise ValueError("Filter operator is not allowed.")

    value = item.get("value")

    if operator == "=" and value is None:
        raise ValueError("'=' filter requires a value.")

    if operator == "in":
        if not isinstance(value, list) or not value:
            raise ValueError("'in' requires a non-empty list.")

        if any(v is None for v in value):
            raise ValueError("'in' values cannot contain null.")

    if operator == "between":
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(
                "'between' requires exactly two values."
            )

        if any(v is None for v in value):
            raise ValueError("'between' values cannot contain null.")

    if "exclude" in item and not isinstance(item["exclude"], bool):
        raise ValueError("exclude must be boolean.")


# ---------------------------------------------------------------------
# 5. KPI DEFINITION VALIDATION
# ---------------------------------------------------------------------

def validate_definition(
    definition: dict[str, Any],
) -> None:
    """Validate a KPI definition before query generation or storage."""

    required = {
        "name",
        "description",
        "source_table",
        "measure",
        "filters",
        "group_by",
        "time_grain",
        "owner",
        "status",
        "version",
    }

    if not isinstance(definition, dict):
        raise ValueError("Definition must be an object.")

    if not required.issubset(definition):
        raise ValueError("Definition is missing required fields.")

    if not isinstance(definition["name"], str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9 _-]{1,79}",
        definition["name"],
    ):
        raise ValueError("Invalid KPI name.")

    if not isinstance(definition["description"], str):
        raise ValueError("Description must be text.")

    if not definition["description"].strip():
        raise ValueError("Description is required.")

    if definition["source_table"] not in TABLES:
        raise ValueError("Source table is not allowed.")

    if definition["status"] not in {"draft", "approved"}:
        raise ValueError("Status must be draft or approved.")

    if definition["time_grain"] != "month":
        raise ValueError("Only monthly time grain is supported.")

    if (
        not isinstance(definition["version"], int)
        or isinstance(definition["version"], bool)
        or definition["version"] < 1
    ):
        raise ValueError("Version must be a positive integer.")

    if (
        not isinstance(definition["owner"], str)
        or not definition["owner"].strip()
    ):
        raise ValueError("Owner is required.")

    if not isinstance(definition["group_by"], list):
        raise ValueError("group_by must be a list.")

    if len(set(definition["group_by"])) != len(
        definition["group_by"]
    ):
        raise ValueError("Duplicate group_by columns are not allowed.")

    for column in definition["group_by"]:
        _column(definition, column)

    if not isinstance(definition["filters"], list):
        raise ValueError("filters must be a list.")

    for item in definition["filters"]:
        _validate_filter(definition, item)

    measure = definition["measure"]

    if not isinstance(measure, dict):
        raise ValueError("Measure must be an object.")

    if measure.get("type") == "ratio":
        for side in ("numerator", "denominator"):
            part = measure.get(side)

            if not isinstance(part, dict):
                raise ValueError(f"Ratio requires {side}.")

            aggregation = part.get("aggregation")

            if aggregation not in MEASURES:
                raise ValueError("Unsupported ratio aggregation.")

            _column(definition, part.get("column"))

    else:
        aggregation = measure.get("aggregation")

        if aggregation not in MEASURES:
            raise ValueError("Unsupported aggregation.")

        _column(definition, measure.get("column"))

    minimum = definition.get("minimum_group_size")

    if minimum is not None:
        if (
            not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or minimum < 1
        ):
            raise ValueError(
                "minimum_group_size must be a positive integer."
            )

    if "privacy_unit" in definition:
        if definition["privacy_unit"] not in {
            "employees",
            "invoices",
            "tasks",
            "records",
        }:
            raise ValueError("Unsupported privacy unit.")


# ---------------------------------------------------------------------
# 6. AGGREGATION BUILDER
# ---------------------------------------------------------------------

def _aggregate(
    definition: dict[str, Any],
    part: dict[str, str],
) -> str:
    aggregation = part["aggregation"]
    column = _column(definition, part["column"])

    if aggregation == "count_distinct":
        return f"COUNT(DISTINCT {column})"

    return f"{MEASURES[aggregation]}({column})"


# ---------------------------------------------------------------------
# 7. FILTER SQL BUILDER
# ---------------------------------------------------------------------

def _build_filter_sql(
    definition: dict[str, Any],
    filters: list[dict[str, Any]],
) -> tuple[list[str], list[Any]]:
    where_parts: list[str] = []
    params: list[Any] = []

    for item in filters:
        _validate_filter(definition, item)

        column = _column(definition, item["column"])
        operator = item["operator"]
        value = item["value"]
        exclude = item.get("exclude", False)

        if operator == "=":
            sql_operator = "<>" if exclude else "="
            where_parts.append(f"{column} {sql_operator} %s")
            params.append(value)

        elif operator == "in":
            placeholders = ", ".join(["%s"] * len(value))
            sql_operator = "NOT IN" if exclude else "IN"

            where_parts.append(
                f"{column} {sql_operator} ({placeholders})"
            )

            params.extend(value)

        elif operator == "between":
            sql_operator = "NOT BETWEEN" if exclude else "BETWEEN"

            where_parts.append(
                f"{column} {sql_operator} %s AND %s"
            )

            params.extend(value)

    return where_parts, params


# ---------------------------------------------------------------------
# 8. PRIVACY THRESHOLD RESOLUTION
# ---------------------------------------------------------------------

def resolve_minimum_group_size(
    definition: dict[str, Any],
    minimum_group_size: int | None = None,
) -> int | None:
    """Resolve an explicit or dictionary-backed privacy threshold."""

    if minimum_group_size is not None:
        if (
            not isinstance(minimum_group_size, int)
            or isinstance(minimum_group_size, bool)
            or minimum_group_size < 1
        ):
            raise ValueError(
                "Minimum group size must be a positive integer."
            )

        return minimum_group_size

    if definition.get("minimum_group_size") is not None:
        return definition["minimum_group_size"]

    return DEFAULT_MINIMUM_GROUP_SIZE


# ---------------------------------------------------------------------
# 9. SQL QUERY BUILDER
# ---------------------------------------------------------------------

def build_query(
    definition: dict[str, Any],
    minimum_group_size: int | None = None,
) -> tuple[str, list[Any]]:
    """Build a safe, parameterized SQL query."""

    validate_definition(definition)

    table = TABLES[definition["source_table"]]

    group_columns = [
        _column(definition, column)
        for column in definition["group_by"]
    ]

    measure = definition["measure"]

    if measure.get("type") == "ratio":
        numerator = _aggregate(
            definition,
            measure["numerator"],
        )

        denominator = _aggregate(
            definition,
            measure["denominator"],
        )

        expression = (
            f"({numerator})::numeric / "
            f"NULLIF(({denominator})::numeric, 0)"
        )

    else:
        expression = _aggregate(
            definition,
            {
                "aggregation": measure["aggregation"],
                "column": measure["column"],
            },
        )

    where_parts, params = _build_filter_sql(
        definition,
        definition["filters"],
    )

    if definition["source_table"] == "fact_invoice":
        where_parts.extend([
            "due_date < CURRENT_DATE",
            "status NOT IN ('DRAFT', 'CANCELLED')",
        ])

    select_parts = list(group_columns)

    select_parts.append(f"{expression} AS kpi_value")

    privacy_column = table["privacy_column"]

    threshold = resolve_minimum_group_size(
        definition,
        minimum_group_size,
    )

    if privacy_column:
        select_parts.append(
            f"COUNT(DISTINCT {privacy_column}) "
            "AS privacy_group_size"
        )

        select_parts.append(
            f"'{table['privacy_unit']}' AS privacy_unit"
        )

        select_parts.append(
            f"COUNT(DISTINCT {privacy_column}) >= "
            f"{threshold} AS privacy_threshold_met"
        )

    else:
        select_parts.append(
            "NULL::bigint AS privacy_group_size"
        )

        select_parts.append(
            "'not_configured' AS privacy_unit"
        )

        select_parts.append(
            "TRUE AS privacy_threshold_met"
        )

    sql = (
        f"SELECT {', '.join(select_parts)} "
        f"FROM {table['sql']} "
    )

    if where_parts:
        sql += "WHERE " + " AND ".join(where_parts) + " "

    if group_columns:
        sql += "GROUP BY " + ", ".join(group_columns) + " "

    if privacy_column:
        sql += (
            "HAVING COUNT(DISTINCT "
            f"{privacy_column}) >= {threshold} "
        )

    if group_columns:
        sql += "ORDER BY " + ", ".join(group_columns)

    return sql, params


# ---------------------------------------------------------------------
# 10. KPI PREVIEW
# ---------------------------------------------------------------------

def preview_metric(
    connection: Any,
    definition: dict[str, Any],
    minimum_group_size: int | None = None,
) -> list[dict[str, Any]]:
    """Execute a KPI preview using an existing database connection."""

    sql, params = build_query(
        definition,
        minimum_group_size,
    )

    cursor = connection.cursor()

    try:
        cursor.execute(sql, params)

        columns = [
            item[0]
            for item in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    finally:
        cursor.close()


# ---------------------------------------------------------------------
# 11. APPROVAL WORKFLOW
# ---------------------------------------------------------------------

def approve_metric(
    definition: dict[str, Any],
    approver: str,
    role: str = "ADMIN",
) -> dict[str, Any]:
    """Return an approved KPI copy.

    The caller must authenticate the user and persist the result.
    """

    validate_definition(definition)

    if role != "ADMIN":
        raise PermissionError(
            "Only ADMIN users can approve custom KPIs."
        )

    if not isinstance(approver, str) or not approver.strip():
        raise ValueError("An approver identity is required.")

    approved = copy.deepcopy(definition)

    approved["status"] = "approved"
    approved["approved_by"] = approver.strip()

    return approved


# ---------------------------------------------------------------------
# 12. APPROVED KPI FILTER
# ---------------------------------------------------------------------

def approved_metrics(
    definitions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return only valid approved KPI definitions."""

    result = []

    for definition in definitions:
        validate_definition(definition)

        if definition["status"] == "approved":
            result.append(definition)

    return result
