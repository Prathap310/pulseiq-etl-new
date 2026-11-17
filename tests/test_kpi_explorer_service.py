import pytest

from Src import kpi_explorer_service as service
from Src.kpi_explorer import ExplorerAuthorizationError


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.description = [
            ("group_id",),
            ("sprint_id",),
            ("metric_value",),
            ("privacy_group_size",),
            ("privacy_threshold_met",),
        ]

    def execute(self, sql, params):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.fake_cursor = FakeCursor(rows)

    def cursor(self):
        return self.fake_cursor


def test_manager_can_query_only_a_team_they_lead(monkeypatch):
    monkeypatch.setattr(
        service, "verify_access_token",
        lambda token: {
            "role": "MANAGER",
            "employee_id": "EMP-001",
        },
    )
    monkeypatch.setattr(
        service, "verify_employee_identity",
        lambda connection, employee_id: {
            "employee_id": employee_id,
        },
    )
    monkeypatch.setattr(
        service, "get_manager_team_scope",
        lambda connection, manager_id: [
            {"team_id": "T01"},
        ],
    )
    monkeypatch.setattr(
        service, "build_task_query",
        lambda **kwargs: ("SELECT test", []),
    )

    connection = FakeConnection([
        ("T01", "SP-01", 90.0, 8, True),
    ])

    result = service.execute_kpi_query(
        connection,
        "valid-token",
        "M22",
        "team",
        team_id="T01",
    )

    assert result == [
        {
            "group_id": "T01",
            "metric_value": 90.0,
            "sprint_id": "SP-01",
        }
    ]


def test_manager_cannot_query_another_managers_team(monkeypatch):
    monkeypatch.setattr(
        service, "verify_access_token",
        lambda token: {
            "role": "MANAGER",
            "employee_id": "EMP-001",
        },
    )
    monkeypatch.setattr(
        service, "verify_employee_identity",
        lambda connection, employee_id: {
            "employee_id": employee_id,
        },
    )
    monkeypatch.setattr(
        service, "get_manager_team_scope",
        lambda connection, manager_id: [
            {"team_id": "T01"},
        ],
    )

    connection = FakeConnection([])

    with pytest.raises(ExplorerAuthorizationError):
        service.execute_kpi_query(
            connection,
            "valid-token",
            "M22",
            "team",
            team_id="T02",
        )


def test_manager_cannot_access_department_metrics(monkeypatch):
    monkeypatch.setattr(
        service, "verify_access_token",
        lambda token: {
            "role": "MANAGER",
            "employee_id": "EMP-001",
        },
    )

    connection = FakeConnection([])

    with pytest.raises(ExplorerAuthorizationError):
        service.execute_kpi_query(
            connection,
            "valid-token",
            "M27",
            "department",
        )


def test_small_groups_are_not_returned(monkeypatch):
    monkeypatch.setattr(
        service, "verify_access_token",
        lambda token: {
            "role": "HR",
            "employee_id": "HR-001",
        },
    )
    monkeypatch.setattr(
        service, "build_risk_query",
        lambda *args: ("SELECT test", []),
    )

    connection = FakeConnection([
        ("D01", 20.0, 3, True),
    ])

    result = service.execute_kpi_query(
        connection,
        "valid-token",
        "M27",
        "department",
    )

    assert result == []


def test_invalid_token_is_rejected_before_query(monkeypatch):
    def reject_token(token):
        raise ValueError("Invalid or expired access token.")

    monkeypatch.setattr(
        service, "verify_access_token", reject_token
    )

    connection = FakeConnection([])

    with pytest.raises(ValueError):
        service.execute_kpi_query(
            connection,
            "invalid-token",
            "M27",
            "company",
        )
