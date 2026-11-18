"""SQL query builder for Task 18 headcount and attrition metrics."""

from __future__ import annotations

import re

from Source.kpi_explorer import (
    ExplorerAuthorizationError,
    ExplorerPrivacyError,
    get_metric,
    validate_level,
)


HEADCOUNT_METRICS = {"M01", "M02", "M03", "M04", "M05", "M06"}


def build_headcount_query(
    metric_id: str,
    level: str,
    report_month: str,
    role: str,
    department_id: str | None = None,
) -> tuple[str, list]:
    """Build a privacy-protected company or department query."""

    if metric_id not in HEADCOUNT_METRICS:
        raise ExplorerPrivacyError(
            "This query builder supports M01-M06 only."
        )

    validate_level(role, level)

    if level not in {"company", "department"}:
        raise ExplorerAuthorizationError(
            "Headcount metrics support company or department level only."
        )

    if not isinstance(report_month, str) or not re.fullmatch(
        r"\d{4}-\d{2}-01", report_month
    ):
        raise ValueError("report_month must use YYYY-MM-01 format.")

    if level == "company" and department_id is not None:
        raise ValueError(
            "A company-level query cannot accept a department filter."
        )

    metric = get_metric(metric_id)
    threshold = metric["minimum_group_size"]

    if level == "company":
        group_expression = "'COMPANY'::text"
        department_filter = ""
        params = [report_month]
    else:
        group_expression = "department_id"
        department_filter = "AND department_id <> 'D00'"
        params = [report_month]

        if department_id is not None:
            department_filter += " AND department_id = %s"
            params.append(department_id)

    if metric_id in {"M05", "M06"}:
        value_expression = (
            "exits::numeric / NULLIF(average_headcount, 0) * 100"
            if metric_id == "M05"
            else
            "voluntary_exits::numeric "
            "/ NULLIF(average_headcount, 0) * 100"
        )

        sql = f"""
            WITH monthly AS (
                SELECT
                    month_start_date,
                    {group_expression} AS group_id,
                    SUM(headcount_end) AS group_headcount,
                    SUM(exits) AS exits,
                    SUM(voluntary_exits) AS voluntary_exits
                FROM dw.fact_headcount_monthly
                WHERE month_start_date BETWEEN
                    (%s::date - INTERVAL '11 months')::date
                    AND %s::date
                {department_filter}
                GROUP BY month_start_date, {group_expression}
            ),
            aggregated AS (
                SELECT
                    group_id,
                    SUM(exits) AS exits,
                    SUM(voluntary_exits) AS voluntary_exits,
                    AVG(group_headcount) AS average_headcount,
                    MAX(group_headcount) FILTER (WHERE month_start_date = %s) AS privacy_group_size
                FROM monthly
                GROUP BY group_id
            )
            SELECT
                group_id,
                ROUND(({value_expression})::numeric, 2) AS metric_value,
                privacy_group_size,
                TRUE AS privacy_threshold_met
            FROM aggregated
            WHERE privacy_group_size >= %s
            ORDER BY group_id
        """

        # Two date parameters are used by the rolling date range.
        params = [report_month, report_month]

        if level == "department" and department_id is not None:
            params.append(department_id)

        params.append(report_month)
        params.append(threshold)

        return sql, params

    value_expressions = {
        "M01": "SUM(headcount_end)",
        "M02": "SUM(hires)",
        "M03": "SUM(exits)",
        "M04": (
            "SUM(exits)::numeric "
            "/ NULLIF(SUM(headcount_start), 0) * 100"
        ),
    }

    sql = f"""
        SELECT
            {group_expression} AS group_id,
            ROUND(({value_expressions[metric_id]})::numeric, 2)
                AS metric_value,
            SUM(headcount_end) AS privacy_group_size,
            TRUE AS privacy_threshold_met
        FROM dw.fact_headcount_monthly
        WHERE month_start_date = %s::date
        {department_filter}
        GROUP BY {group_expression}
        HAVING SUM(headcount_end) >= %s
        ORDER BY group_id
    """

    params.append(threshold)

    return sql, params




PAYROLL_ATTENDANCE_METRICS = {
    "M07", "M08", "M09", "M10", "M11",
    "M12", "M13", "M14", "M15",
}


def build_payroll_attendance_query(
    metric_id: str,
    level: str,
    report_month: str,
    role: str,
    department_id: str | None = None,
) -> tuple[str, list]:
    """Build privacy-protected payroll and attendance queries."""

    if metric_id not in PAYROLL_ATTENDANCE_METRICS:
        raise ExplorerPrivacyError(
            "This query builder supports M07-M15 only."
        )

    validate_level(role, level)

    if level not in {"company", "department"}:
        raise ExplorerAuthorizationError(
            "Payroll and attendance metrics support company "
            "or department level only."
        )

    if not isinstance(report_month, str) or not re.fullmatch(
        r"\d{4}-\d{2}-01", report_month
    ):
        raise ValueError("report_month must use YYYY-MM-01 format.")

    if level == "company" and department_id is not None:
        raise ValueError(
            "A company-level query cannot accept a department filter."
        )

    metric = get_metric(metric_id)
    threshold = metric["minimum_group_size"]

    if level == "company":
        group_expression = "'COMPANY'::text"
        department_filter = ""
    else:
        group_expression = "department_id"
        department_filter = "AND department_id <> 'D00'"

        if department_id is not None:
            department_filter += " AND department_id = %s"

    payroll_expressions = {
        "M07": "SUM(gross_pay)",
        "M08": "SUM(net_pay)",
        "M09": "SUM(employer_cost)",
        "M10": (
            "SUM(employer_cost)::numeric "
            "/ NULLIF(COUNT(DISTINCT employee_id), 0)"
        ),
        "M11": (
            "SUM(overtime_pay)::numeric "
            "/ NULLIF(SUM(employer_cost), 0) * 100"
        ),
        "M12": (
            "SUM(variable_pay)::numeric "
            "/ NULLIF(SUM(gross_pay), 0) * 100"
        ),
        "M15": "SUM(lop_days)",
    }

    attendance_expressions = {
        "M13": (
            "(SUM(present_days) + 0.5 * SUM(half_days_unpaid)) "
            "/ NULLIF(SUM(scheduled_days), 0)"
        ),
        "M14": (
            "SUM(late_arrivals)::numeric "
            "/ NULLIF(SUM(present_days), 0)"
        ),
    }

    if metric_id in payroll_expressions:
        source_table = "dw.fact_payroll"
        value_expression = payroll_expressions[metric_id]
    else:
        source_table = "dw.fact_attendance_monthly"
        value_expression = attendance_expressions[metric_id]

    sql = f"""
        SELECT
            {group_expression} AS group_id,
            ROUND(({value_expression})::numeric, 2)
                AS metric_value,
            COUNT(DISTINCT employee_id) AS privacy_group_size,
            TRUE AS privacy_threshold_met
        FROM {source_table}
        WHERE period_end_date >= %s::date
          AND period_end_date < (%s::date + INTERVAL '1 month')
        {department_filter}
        GROUP BY {group_expression}
        HAVING COUNT(DISTINCT employee_id) >= %s
        ORDER BY group_id
    """

    params = [report_month, report_month]

    if level == "department" and department_id is not None:
        params.append(department_id)

    params.append(threshold)

    return sql, params

TASK_METRICS = {"M22", "M23", "M25"}


def build_task_query(
    metric_id: str,
    level: str,
    role: str,
    team_id: str | None = None,
    sprint_id: str | None = None,
    manager_id: str | None = None,
) -> tuple[str, list]:
    """Build privacy-protected team-sprint task metric queries."""

    if metric_id not in TASK_METRICS:
        raise ExplorerPrivacyError(
            "This query builder supports M22, M23 and M25 only."
        )

    validate_level(role, level)

    if level != "team":
        raise ExplorerAuthorizationError(
            "Task metrics support team level only."
        )

    if role == "MANAGER" and not manager_id:
        raise ExplorerAuthorizationError(
            "A verified manager identity is required for team access."
        )

    if role != "MANAGER" and manager_id is not None:
        raise ValueError(
            "manager_id is only valid for manager queries."
        )

    metric = get_metric(metric_id)
    threshold = metric["minimum_group_size"]

    value_expressions = {
        "M22": (
            "COUNT(*) FILTER (WHERE status = 'Done')::numeric "
            "/ NULLIF(COUNT(*) FILTER "
            "(WHERE status <> 'Cancelled'), 0) * 100"
        ),
        "M23": (
            "COUNT(*) FILTER "
            "(WHERE status = 'Done' AND completed_on_time = 'Y')::numeric "
            "/ NULLIF(COUNT(*) FILTER (WHERE status = 'Done'), 0) * 100"
        ),
        "M25": "AVG(cycle_time_days)",
    }

    privacy_count_expressions = {
        "M22": "COUNT(*) FILTER (WHERE status <> 'Cancelled')",
        "M23": "COUNT(*) FILTER (WHERE status = 'Done')",
        "M25": "COUNT(cycle_time_days)",
    }
    privacy_count_expression = privacy_count_expressions[metric_id]

    filters = []
    params = []

    if team_id is not None:
        filters.append("team_id = %s")
        params.append(team_id)

    if sprint_id is not None:
        filters.append("sprint_id = %s")
        params.append(sprint_id)

    if role == "MANAGER":
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM dw.dim_team dt
                WHERE dt.team_id = ft.team_id
                  AND dt.team_lead_employee_id = %s
            )
            """
        )
        params.append(manager_id)

    where_clause = (
        "WHERE " + " AND ".join(filters)
        if filters
        else ""
    )

    sql = f"""
        SELECT
            ft.team_id AS group_id,
            ft.sprint_id,
            ROUND(
                ({value_expressions[metric_id]})::numeric,
                2
            ) AS metric_value,
            {privacy_count_expression} AS privacy_group_size,
            TRUE AS privacy_threshold_met
        FROM dw.fact_task ft
        {where_clause}
        GROUP BY ft.team_id, ft.sprint_id
        HAVING {privacy_count_expression} >= %s
        ORDER BY ft.team_id, ft.sprint_id
    """

    params.append(threshold)

    return sql, params

RISK_METRICS = {"M27"}


def build_risk_query(
    metric_id: str,
    level: str,
    role: str,
    department_id: str | None = None,
) -> tuple[str, list]:
    """Build privacy-protected high-risk share queries."""

    if metric_id not in RISK_METRICS:
        raise ExplorerPrivacyError(
            "This query builder supports M27 only."
        )

    validate_level(role, level)

    if level not in {"company", "department"}:
        raise ExplorerAuthorizationError(
            "High-risk share supports company or department level only."
        )

    if level == "company" and department_id is not None:
        raise ValueError(
            "A company-level query cannot accept a department filter."
        )

    threshold = get_metric(metric_id)["minimum_group_size"]

    if level == "company":
        group_expression = "'COMPANY'::text"
        department_filter = ""
        params = []
    else:
        group_expression = "department_id"
        department_filter = "AND department_id <> 'D00'"
        params = []

        if department_id is not None:
            department_filter += " AND department_id = %s"
            params.append(department_id)

    sql = f"""
        WITH latest_snapshot AS (
            SELECT MAX(as_of_date) AS snapshot_date
            FROM dw.fact_attrition_risk
        ),
        snapshot_data AS (
            SELECT
                fr.employee_id,
                fr.department_id,
                fr.risk_band
            FROM dw.fact_attrition_risk fr
            CROSS JOIN latest_snapshot ls
            WHERE fr.as_of_date = ls.snapshot_date
            {department_filter}
        )
        SELECT
            {group_expression} AS group_id,
            ROUND(
                (
                    COUNT(DISTINCT employee_id)
                    FILTER (WHERE risk_band = 'High')
                )::numeric
                / NULLIF(COUNT(DISTINCT employee_id), 0) * 100,
                2
            ) AS metric_value,
            COUNT(DISTINCT employee_id) AS privacy_group_size,
            TRUE AS privacy_threshold_met
        FROM snapshot_data
        GROUP BY {group_expression}
        HAVING COUNT(DISTINCT employee_id) >= %s
        ORDER BY group_id
    """

    params.append(threshold)
    return sql, params

