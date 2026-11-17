import pytest

from Src.kpi_explorer import (
    ExplorerAuthorizationError,
    ExplorerPrivacyError,
)
from Src.kpi_explorer_sql import build_task_query


@pytest.mark.parametrize(
    "metric_id, formula, privacy_expression",
    [
        (
            "M22",
            "COUNT(*) FILTER (WHERE status = 'Done')",
            "COUNT(*) FILTER (WHERE status <> 'Cancelled')",
        ),
        (
            "M23",
            "completed_on_time = 'Y'",
            "COUNT(*) FILTER (WHERE status = 'Done')",
        ),
        (
            "M25",
            "AVG(cycle_time_days)",
            "COUNT(cycle_time_days)",
        ),
    ],
)
def test_task_metric_uses_expected_formula_and_privacy_threshold(
    metric_id, formula, privacy_expression
):
    sql, params = build_task_query(metric_id, "team", "ADMIN")

    assert "dw.fact_task ft" in sql
    assert formula in sql
    assert "GROUP BY ft.team_id, ft.sprint_id" in sql
    assert f"HAVING {privacy_expression} >= %s" in sql
    assert f"{privacy_expression} AS privacy_group_size" in sql
    assert params == [5]


def test_task_query_supports_parameterized_team_and_sprint_filters():
    sql, params = build_task_query(
        "M22", "team", "ADMIN", team_id="T01", sprint_id="SP-01"
    )

    assert "team_id = %s" in sql
    assert "sprint_id = %s" in sql
    assert "T01" not in sql
    assert "SP-01" not in sql
    assert params == ["T01", "SP-01", 5]


def test_manager_query_is_limited_to_teams_they_lead():
    sql, params = build_task_query(
        "M23", "team", "MANAGER", manager_id="EMP-0001"
    )

    assert "dt.team_lead_employee_id = %s" in sql
    assert "dt.team_id = ft.team_id" in sql
    assert params == ["EMP-0001", 5]


def test_manager_must_supply_identity():
    with pytest.raises(ExplorerAuthorizationError):
        build_task_query("M22", "team", "MANAGER")


def test_non_manager_cannot_supply_manager_identity():
    with pytest.raises(ValueError):
        build_task_query(
            "M22", "team", "ADMIN", manager_id="EMP-0001"
        )


@pytest.mark.parametrize("role", ["HR", "EXECUTIVE"])
def test_roles_without_team_access_are_rejected(role):
    with pytest.raises(ExplorerAuthorizationError):
        build_task_query("M22", "team", role)


def test_task_builder_rejects_unsupported_metric():
    with pytest.raises(ExplorerPrivacyError):
        build_task_query("M01", "team", "ADMIN")


def test_task_builder_rejects_non_team_level():
    with pytest.raises(ExplorerAuthorizationError):
        build_task_query("M22", "company", "ADMIN")
