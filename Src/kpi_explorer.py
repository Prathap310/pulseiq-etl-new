"""Privacy-governed self-service KPI Explorer for PulseIQ Task 18."""

from __future__ import annotations

from typing import Any


# Only metrics with explicit dictionary privacy thresholds are enabled.
METRICS = {
    **{
        f"M{i:02d}": {
            "minimum_group_size": 5,
            "privacy_unit": "employees",
            "dimension": "department",
        }
        for i in [1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    },
    **{
        f"M{i:02d}": {
            "minimum_group_size": 10,
            "privacy_unit": "employees",
            "dimension": "department",
        }
        for i in [4, 5, 6, 27]
    },
    **{
        f"M{i:02d}": {
            "minimum_group_size": 5,
            "privacy_unit": "tasks",
            "dimension": "team",
        }
        for i in [22, 23, 25]
    },
}

METRIC_NAMES = {
    "M01": "Headcount",
    "M02": "Hires",
    "M03": "Exits",
    "M04": "Monthly attrition rate",
    "M05": "Rolling 12-month attrition rate",
    "M06": "Voluntary attrition rate",
    "M07": "Gross pay",
    "M08": "Net pay",
    "M09": "Employer payroll cost",
    "M10": "Cost per head",
    "M11": "Overtime share",
    "M12": "Variable pay share",
    "M13": "Attendance rate",
    "M14": "Late arrival rate",
    "M15": "Leave without pay days",
    "M22": "Task completion rate",
    "M23": "On-time delivery rate",
    "M25": "Average cycle time",
    "M27": "High-risk share",
}

DISABLED_METRICS = {
    "M16", "M17", "M18", "M19", "M20", "M21",
    "M24", "M26", "M28",
}

VALID_ROLES = {"ADMIN", "HR", "MANAGER", "EXECUTIVE"}

ROLE_LEVELS = {
    "ADMIN": {"company", "department", "team"},
    "HR": {"company", "department"},
    "MANAGER": {"reporting_group", "team"},
    "EXECUTIVE": {"company"},
}


class ExplorerAuthorizationError(PermissionError):
    """Raised when a user cannot access an Explorer scope."""


class ExplorerPrivacyError(ValueError):
    """Raised when a metric or group fails privacy requirements."""


def get_metric(metric_id: str) -> dict[str, Any]:
    """Return an enabled metric or fail closed."""

    if metric_id in DISABLED_METRICS or metric_id not in METRICS:
        raise ExplorerPrivacyError(
            f"{metric_id} is unavailable because its privacy "
            "threshold or data requirements are not approved."
        )

    return {
        "metric_id": metric_id,
        "name": METRIC_NAMES[metric_id],
        **METRICS[metric_id],
    }


def validate_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise ExplorerAuthorizationError("Unrecognized user role.")


def validate_level(role: str, level: str) -> None:
    validate_role(role)

    if level not in ROLE_LEVELS[role]:
        raise ExplorerAuthorizationError(
            f"{role} users cannot access the {level} level."
        )


def verify_employee_identity(connection: Any, employee_id: str) -> dict:
    """Verify an identity against the current warehouse employee record."""

    if not isinstance(employee_id, str) or not employee_id.strip():
        raise ExplorerAuthorizationError("Employee identity is required.")

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT employee_id, department_id, manager_id, role_title
            FROM dw.dim_employee
            WHERE employee_id = %s
              AND UPPER(TRIM(is_current)) IN ('Y', 'YES', 'TRUE', '1')
            """,
            (employee_id.strip(),),
        )

        rows = cursor.fetchall()

        if len(rows) != 1:
            raise ExplorerAuthorizationError(
                "Employee identity is not uniquely verified as current."
            )

        return {
            "employee_id": rows[0][0],
            "department_id": rows[0][1],
            "manager_id": rows[0][2],
            "role_title": rows[0][3],
        }

    finally:
        cursor.close()


def get_manager_scope(connection: Any, manager_id: str) -> dict:
    """Return verified direct-report scope for a manager."""

    manager = verify_employee_identity(connection, manager_id)

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(DISTINCT employee_id)
            FROM dw.dim_employee
            WHERE manager_id = %s
              AND UPPER(TRIM(is_current)) IN ('Y', 'YES', 'TRUE', '1')
            """,
            (manager["employee_id"],),
        )

        direct_reports = int(cursor.fetchone()[0])

        return {
            "manager_id": manager["employee_id"],
            "department_id": manager["department_id"],
            "direct_reports": direct_reports,
            "scope_type": "direct_reports",
        }

    finally:
        cursor.close()


def get_manager_team_scope(connection: Any, manager_id: str) -> list[dict]:
    """Return teams for which the verified employee is the team lead."""

    manager = verify_employee_identity(connection, manager_id)

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT team_id, team_name, department_id
            FROM dw.dim_team
            WHERE team_lead_employee_id = %s
            ORDER BY team_id
            """,
            (manager["employee_id"],),
        )

        return [
            {
                "team_id": row[0],
                "team_name": row[1],
                "department_id": row[2],
            }
            for row in cursor.fetchall()
        ]

    finally:
        cursor.close()


def privacy_check(group_size: int, metric_id: str) -> bool:
    """Check a group's size against its metric-specific threshold."""

    metric = get_metric(metric_id)

    if not isinstance(group_size, int) or group_size < 0:
        raise ExplorerPrivacyError("Invalid privacy group size.")

    return group_size >= metric["minimum_group_size"]


def suppress_small_groups(
    rows: list[dict],
    metric_id: str,
) -> list[dict]:
    """Return only groups that satisfy their metric privacy threshold."""

    metric = get_metric(metric_id)
    threshold = metric["minimum_group_size"]

    safe_rows = []

    for row in rows:
        group_size = row.get("privacy_group_size")

        if (
            isinstance(group_size, int)
            and group_size >= threshold
            and row.get("privacy_threshold_met") is True
        ):
            safe_rows.append(row)

    return safe_rows
