"""Governed, parameterized custom KPI query builder for PulseIQ."""

from __future__ import annotations

import re
from typing import Any

# Every SQL identifier and expression is controlled by this whitelist.
TABLES = {
    "fact_payroll": {
        "sql": "dw.fact_payroll",
        "columns": {
            "employee_id": "employee_id",
            "department_id": "department_id",
            "period_end_date": "period_end_date",
            "overtime_hours_paid": "overtime_hours_paid",
            "lop_days": "lop_days",
            "employer_cost": "employer_cost",
        },
        "privacy_column": "employee_id",
    },
    "fact_attendance_monthly": {
        "sql": "dw.fact_attendance_monthly",
        "columns": {
            "employee_id": "employee_id",
            "department_id": "department_id",
            "period_end_date": "period_end_date",
            "late_arrivals": "late_arrivals",
            "present_days": "present_days",
        },
        "privacy_column": "employee_id",
    },
    "fact_invoice": {
        "sql": "dw.fact_invoice",
        "columns": {
            "invoice_id": "invoice_id",
            "client_id": "client_id",
            "due_date": "due_date",
            "status": "status",
            "balance_due": "balance_due",
        },
        "privacy_column": "invoice_id",
    },
}

MEASURES = {
    "sum": "SUM",
    "count": "COUNT",
    "count_distinct": "COUNT(DISTINCT",
    "avg": "AVG",
}

OPERATORS = {"=", "in", "between"}

# Explicit privacy policy: invoice groups require at least five invoices.
DEFAULT_MINIMUM_GROUP_SIZE = 5

EXAMPLES = [
    {
        "name": "Overtime hours per head",
        "description": "Paid overtime hours divided by distinct employees.",
        "source_table": "fact_payroll",
        "measure": {
            "type": "ratio",
            "numerator": {"aggregation": "sum", "column": "overtime_hours_paid"},
            "denominator": {"aggregation": "count_distinct", "column": "employee_id"},
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "HR Analytics",
        "status": "draft",
        "version": 1,
    },
    {
        "name": "Unpaid leave days by month",
        "description": "Sum of unpaid leave days by department and month.",
        "source_table": "fact_payroll",
        "measure": {"aggregation": "sum", "column": "lop_days"},
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "Payroll",
        "status": "draft",
        "version": 1,
    },
    {
        "name": "Employer cost per head",
        "description": "Employer cost divided by distinct paid employees.",
        "source_table": "fact_payroll",
        "measure": {
            "type": "ratio",
            "numerator": {"aggregation": "sum", "column": "employer_cost"},
            "denominator": {"aggregation": "count_distinct", "column": "employee_id"},
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "Finance",
        "status": "draft",
        "version": 1,
    },
    {
        "name": "Late arrivals per present day",
        "description": "Late check-ins divided by present days.",
        "source_table": "fact_attendance_monthly",
        "measure": {
            "type": "ratio",
            "numerator": {"aggregation": "sum", "column": "late_arrivals"},
            "denominator": {"aggregation": "sum", "column": "present_days"},
        },
        "filters": [],
        "group_by": ["department_id", "period_end_date"],
        "time_grain": "month",
        "owner": "HR Analytics",
        "status": "draft",
        "version": 1,
    },
    {
        "name": "Overdue receivables by client",
        "description": "Outstanding invoice balance past its due date.",
        "source_table": "fact_invoice",
        "measure": {"aggregation": "sum", "column": "balance_due"},
        "filters": [
            {"column": "status", "operator": "in", "value": ["DRAFT", "CANCELLED"], "exclude": True}
        ],
        "group_by": ["client_id"],
        "time_grain": "month",
        "owner": "Finance",
        "status": "draft",
        "version": 1,
    },
]


def _column(definition: dict[str, Any], column: str) -> str:
    table = TABLES.get(definition.get("source_table"))
    if not table or column not in table["columns"]:
        raise ValueError(f"Unknown or disallowed column: {column}")
    return table["columns"][column]


def validate_definition(definition: dict[str, Any]) -> None:
    required = {
        "name", "description", "source_table", "measure", "filters",
        "group_by", "time_grain", "owner", "status", "version",
    }
    if not isinstance(definition, dict) or not required.issubset(definition):
        raise ValueError("Definition is missing required fields.")

    if not isinstance(definition["name"], str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9 _-]{1,79}", definition["name"]
    ):
        raise ValueError("Invalid KPI name.")

    if definition["source_table"] not in TABLES:
        raise ValueError("Source table is not allowed.")

    if definition["status"] not in {"draft", "approved"}:
        raise ValueError("Status must be draft or approved.")

    if definition["time_grain"] != "month":
        raise ValueError("Only monthly time grain is supported.")

    if not isinstance(definition["version"], int) or definition["version"] < 1:
        raise ValueError("Version must be a positive integer.")

    if not isinstance(definition["owner"], str) or not definition["owner"].strip():
        raise ValueError("Owner is required.")

    if not isinstance(definition["group_by"], list):
        raise ValueError("group_by must be a list.")

    for column in definition["group_by"]:
        _column(definition, column)

    if not isinstance(definition["filters"], list):
        raise ValueError("filters must be a list.")

    for item in definition["filters"]:
        if not isinstance(item, dict):
            raise ValueError("Each filter must be an object.")
        _column(definition, item.get("column"))
        operator = item.get("operator")
        if operator not in OPERATORS:
            raise ValueError("Filter operator is not allowed.")
        value = item.get("value")
        if operator == "in" and (
            not isinstance(value, list) or not value
        ):
            raise ValueError("'in' requires a non-empty list.")
        if operator == "between" and (
            not isinstance(value, list) or len(value) != 2
        ):
            raise ValueError("'between' requires exactly two values.")
        if "exclude" in item and not isinstance(item["exclude"], bool):
            raise ValueError("exclude must be boolean.")

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


def _aggregate(definition: dict[str, Any], part: dict[str, str]) -> str:
    aggregation = part["aggregation"]
    column = _column(definition, part["column"])
    if aggregation == "count_distinct":
        return f"COUNT(DISTINCT {column})"
    return f"{MEASURES[aggregation]}({column})"


def build_query(
    definition: dict[str, Any],
    minimum_group_size: int = DEFAULT_MINIMUM_GROUP_SIZE,
) -> tuple[str, list[Any]]:
    """Return SQL and bound parameters. Never accepts user-supplied SQL."""
    validate_definition(definition)

    if not isinstance(minimum_group_size, int) or minimum_group_size < 1:
        raise ValueError("Minimum group size must be a positive integer.")

    table = TABLES[definition["source_table"]]
    group_columns = [_column(definition, c) for c in definition["group_by"]]
    privacy_column = table["privacy_column"]

    measure = definition["measure"]
    if measure.get("type") == "ratio":
        numerator = _aggregate(definition, measure["numerator"])
        denominator = _aggregate(definition, measure["denominator"])
        expression = f"({numerator})::numeric / NULLIF(({denominator})::numeric, 0)"
    else:
        part = {
            "aggregation": measure["aggregation"],
            "column": measure["column"],
        }
        expression = _aggregate(definition, part)

    params: list[Any] = []
    where_parts = []

    for item in definition["filters"]:
        column = _column(definition, item["column"])
        operator = item["operator"]
        value = item["value"]
        exclude = item.get("exclude", False)

        if operator == "=":
            where_parts.append(f"{column} {'<>' if exclude else '='} %s")
            params.append(value)
        elif operator == "in":
            placeholders = ", ".join(["%s"] * len(value))
            where_parts.append(
                f"{column} {'NOT IN' if exclude else 'IN'} ({placeholders})"
            )
            params.extend(value)
        elif operator == "between":
            where_parts.append(f"{column} BETWEEN %s AND %s")
            params.extend(value)

    if definition["source_table"] == "fact_invoice":
        where_parts.extend([
            "due_date < CURRENT_DATE",
            "status NOT IN ('DRAFT', 'CANCELLED')",
        ])

    select_parts = list(group_columns)
    select_parts.extend([
        f"{expression} AS kpi_value",
        f"COUNT(DISTINCT {privacy_column}) AS privacy_group_size",
        f"(COUNT(DISTINCT {privacy_column}) >= {minimum_group_size}) AS privacy_threshold_met",
    ])

    sql = (
        f"SELECT {', '.join(select_parts)} "
        f"FROM {table['sql']} "
    )
    if where_parts:
        sql += "WHERE " + " AND ".join(where_parts) + " "
    if group_columns:
        sql += "GROUP BY " + ", ".join(group_columns) + " "
    sql += "HAVING COUNT(DISTINCT " + privacy_column + f") >= {minimum_group_size} "
    if group_columns:
        sql += "ORDER BY " + ", ".join(group_columns)

    return sql, params


def preview_metric(
    connection: Any,
    definition: dict[str, Any],
    minimum_group_size: int = DEFAULT_MINIMUM_GROUP_SIZE,
) -> list[dict[str, Any]]:
    """Execute a draft or approved definition and return preview rows."""
    sql, params = build_query(definition, minimum_group_size)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        columns = [item[0] for item in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        cursor.close()


def approve_metric(definition: dict[str, Any], approver: str) -> dict[str, Any]:
    """Return an approved copy after validation; caller must persist governance."""
    validate_definition(definition)
    if not isinstance(approver, str) or not approver.strip():
        raise ValueError("An approver identity is required.")
    approved = dict(definition)
    approved["status"] = "approved"
    approved["approved_by"] = approver.strip()
    return approved


def approved_metrics(definitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only validated approved metrics are returned for dashboard/API use."""
    result = []
    for definition in definitions:
        validate_definition(definition)
        if definition["status"] == "approved":
            result.append(definition)
    return result
