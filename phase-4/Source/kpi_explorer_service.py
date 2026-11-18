"""Secure execution service for the Task 18 KPI Explorer."""

from Source.kpi_auth import verify_access_token
from Source.kpi_explorer import (
    ExplorerAuthorizationError,
    get_manager_team_scope,
    suppress_small_groups,
    verify_employee_identity,
)
from Source.kpi_explorer_sql import (
    build_headcount_query,
    build_payroll_attendance_query,
    build_task_query,
    build_risk_query,
)


def execute_kpi_query(
    connection,
    token: str,
    metric_id: str,
    level: str,
    report_month: str | None = None,
    department_id: str | None = None,
    team_id: str | None = None,
    sprint_id: str | None = None,
) -> list[dict]:
    """Authenticate, authorize, execute and privacy-filter KPI results."""

    # Authenticate the user; never accept a role supplied by the UI.
    claims = verify_access_token(token)
    role = claims["role"]
    employee_id = claims["employee_id"]

    manager_id = None

    # Manager scope must come from a verified warehouse identity.
    if role == "MANAGER":
        manager = verify_employee_identity(connection, employee_id)
        manager_id = manager["employee_id"]

        if level == "team":
            allowed_teams = get_manager_team_scope(
                connection, manager_id
            )
            allowed_team_ids = {
                item["team_id"] for item in allowed_teams
            }

            if not allowed_team_ids:
                return []

            if team_id is not None and team_id not in allowed_team_ids:
                raise ExplorerAuthorizationError(
                    "Managers can access only teams they lead."
                )

    # Select only an approved query builder.
    if metric_id in {
        "M01", "M02", "M03", "M04", "M05", "M06"
    }:
        if report_month is None:
            raise ValueError("report_month is required for this metric.")

        sql, params = build_headcount_query(
            metric_id, level, report_month, role, department_id
        )

    elif metric_id in {
        "M07", "M08", "M09", "M10", "M11",
        "M12", "M13", "M14", "M15"
    }:
        if report_month is None:
            raise ValueError("report_month is required for this metric.")

        sql, params = build_payroll_attendance_query(
            metric_id, level, report_month, role, department_id
        )

    elif metric_id in {"M22", "M23", "M25"}:
        sql, params = build_task_query(
            metric_id=metric_id,
            level=level,
            role=role,
            team_id=team_id,
            sprint_id=sprint_id,
            manager_id=manager_id,
        )

    elif metric_id == "M27":
        sql, params = build_risk_query(
            metric_id, level, role, department_id
        )

    else:
        raise ValueError("Unsupported or disabled KPI metric.")

    # Execute parameterized SQL and convert results into dictionaries.
    cursor = connection.cursor()

    try:
        cursor.execute(sql, params)
        columns = [item[0] for item in cursor.description]
        raw_rows = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()

    # Apply a second privacy check before returning anything to the UI.
    safe_rows = suppress_small_groups(raw_rows, metric_id)

    # Do not expose privacy counts or internal threshold flags.
    output = []

    for row in safe_rows:
        clean_row = {
            "group_id": row["group_id"],
            "metric_value": row["metric_value"],
        }

        if "sprint_id" in row:
            clean_row["sprint_id"] = row["sprint_id"]

        output.append(clean_row)

    return output

