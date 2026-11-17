import pytest

from Src.kpi_explorer import (
    ExplorerAuthorizationError,
    ExplorerPrivacyError,
)
from Src.kpi_explorer_sql import build_risk_query


def test_m27_company_query_uses_latest_snapshot_and_privacy():
    sql, params = build_risk_query("M27", "company", "ADMIN")

    assert "MAX(as_of_date)" in sql
    assert "risk_band = 'High'" in sql
    assert "COUNT(DISTINCT employee_id)" in sql
    assert "HAVING COUNT(DISTINCT employee_id) >= %s" in sql
    assert params == [10]


def test_m27_department_query_excludes_executive_office():
    sql, params = build_risk_query("M27", "department", "HR")

    assert "department_id <> 'D00'" in sql
    assert params == [10]


def test_m27_department_filter_is_parameterized():
    sql, params = build_risk_query(
        "M27", "department", "ADMIN", "D01"
    )

    assert "department_id = %s" in sql
    assert "D01" not in sql
    assert params == ["D01", 10]


def test_m27_company_rejects_department_filter():
    with pytest.raises(ValueError):
        build_risk_query("M27", "company", "ADMIN", "D01")


def test_m27_manager_cannot_access_department_level():
    with pytest.raises(ExplorerAuthorizationError):
        build_risk_query("M27", "department", "MANAGER")


def test_m27_rejects_unsupported_metric():
    with pytest.raises(ExplorerPrivacyError):
        build_risk_query("M01", "company", "ADMIN")


def test_m27_rejects_team_level():
    with pytest.raises(ExplorerAuthorizationError):
        build_risk_query("M27", "team", "ADMIN")
