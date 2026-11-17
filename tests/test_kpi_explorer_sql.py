import pytest

from Src.kpi_explorer import (
    ExplorerAuthorizationError,
    ExplorerPrivacyError,
)
from Src.kpi_explorer_sql import build_headcount_query


@pytest.mark.parametrize("metric_id", ["M01", "M02", "M03", "M04"])
def test_monthly_metrics_generate_privacy_protected_sql(metric_id):
    sql, params = build_headcount_query(
        metric_id, "company", "2026-09-01", "ADMIN"
    )
    expected_threshold = 10 if metric_id == "M04" else 5

    assert "dw.fact_headcount_monthly" in sql
    assert "HAVING SUM(headcount_end) >= %s" in sql
    assert params == ["2026-09-01", expected_threshold]


@pytest.mark.parametrize("metric_id", ["M05", "M06"])
def test_rolling_metrics_use_selected_month_privacy_size(metric_id):
    sql, params = build_headcount_query(
        metric_id, "company", "2026-09-01", "ADMIN"
    )

    assert "INTERVAL '11 months'" in sql
    assert "AVG(group_headcount) AS average_headcount" in sql
    assert "FILTER (WHERE month_start_date = %s)" in sql
    assert "WHERE privacy_group_size >= %s" in sql
    assert "average_headcount" in sql
    assert "AVG(headcount_end)" not in sql
    assert params == [
        "2026-09-01",
        "2026-09-01",
        "2026-09-01",
        10,
    ]


def test_department_query_excludes_executive_office():
    sql, params = build_headcount_query(
        "M01", "department", "2026-09-01", "ADMIN"
    )

    assert "department_id <> 'D00'" in sql
    assert params == ["2026-09-01", 5]


def test_department_filter_is_parameterized():
    sql, params = build_headcount_query(
        "M01", "department", "2026-09-01", "ADMIN", "D01"
    )

    assert "department_id = %s" in sql
    assert "D01" not in sql
    assert params == ["2026-09-01", "D01", 5]


def test_rolling_department_filter_parameters_are_ordered():
    sql, params = build_headcount_query(
        "M05", "department", "2026-09-01", "ADMIN", "D01"
    )

    assert "department_id = %s" in sql
    assert params == [
        "2026-09-01",
        "2026-09-01",
        "D01",
        "2026-09-01",
        10,
    ]


def test_manager_cannot_query_department_level():
    with pytest.raises(ExplorerAuthorizationError):
        build_headcount_query(
            "M01", "department", "2026-09-01", "MANAGER"
        )


def test_company_query_rejects_department_filter():
    with pytest.raises(ValueError):
        build_headcount_query(
            "M01", "company", "2026-09-01", "ADMIN", "D01"
        )


def test_invalid_month_is_rejected():
    with pytest.raises(ValueError):
        build_headcount_query(
            "M01", "company", "2026-09-15", "ADMIN"
        )


def test_unsupported_metric_is_rejected():
    with pytest.raises(ExplorerPrivacyError):
        build_headcount_query(
            "M07", "company", "2026-09-01", "ADMIN"
        )
