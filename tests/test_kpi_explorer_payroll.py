import pytest

from Src.kpi_explorer import (
    ExplorerAuthorizationError,
    ExplorerPrivacyError,
)
from Src.kpi_explorer_sql import build_payroll_attendance_query


@pytest.mark.parametrize(
    "metric_id, source_table, formula",
    [
        ("M07", "dw.fact_payroll", "SUM(gross_pay)"),
        ("M08", "dw.fact_payroll", "SUM(net_pay)"),
        ("M09", "dw.fact_payroll", "SUM(employer_cost)"),
        ("M10", "dw.fact_payroll", "COUNT(DISTINCT employee_id)"),
        ("M11", "dw.fact_payroll", "SUM(overtime_pay)"),
        ("M12", "dw.fact_payroll", "SUM(variable_pay)"),
        ("M13", "dw.fact_attendance_monthly", "SUM(half_days_unpaid)"),
        ("M14", "dw.fact_attendance_monthly", "SUM(late_arrivals)"),
        ("M15", "dw.fact_payroll", "SUM(lop_days)"),
    ],
)
def test_metric_query_uses_correct_source_and_formula(
    metric_id, source_table, formula
):
    sql, params = build_payroll_attendance_query(
        metric_id, "company", "2026-09-01", "ADMIN"
    )

    assert source_table in sql
    assert formula in sql
    assert "COUNT(DISTINCT employee_id) AS privacy_group_size" in sql
    assert "HAVING COUNT(DISTINCT employee_id) >= %s" in sql
    assert params == ["2026-09-01", "2026-09-01", 5]


def test_department_query_excludes_executive_office():
    sql, params = build_payroll_attendance_query(
        "M07", "department", "2026-09-01", "ADMIN"
    )

    assert "department_id <> 'D00'" in sql
    assert params == ["2026-09-01", "2026-09-01", 5]


def test_department_filter_is_parameterized():
    sql, params = build_payroll_attendance_query(
        "M09", "department", "2026-09-01", "ADMIN", "D01"
    )

    assert "department_id = %s" in sql
    assert "D01" not in sql
    assert params == ["2026-09-01", "2026-09-01", "D01", 5]


def test_manager_cannot_query_department_level():
    with pytest.raises(ExplorerAuthorizationError):
        build_payroll_attendance_query(
            "M07", "department", "2026-09-01", "MANAGER"
        )


def test_company_query_rejects_department_filter():
    with pytest.raises(ValueError):
        build_payroll_attendance_query(
            "M07", "company", "2026-09-01", "ADMIN", "D01"
        )


def test_invalid_month_is_rejected():
    with pytest.raises(ValueError):
        build_payroll_attendance_query(
            "M07", "company", "2026-09-15", "ADMIN"
        )


def test_headcount_metric_is_not_supported_by_this_builder():
    with pytest.raises(ExplorerPrivacyError):
        build_payroll_attendance_query(
            "M01", "company", "2026-09-01", "ADMIN"
        )
