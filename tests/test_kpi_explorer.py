import pytest

from Src.kpi_explorer import (
    DISABLED_METRICS,
    ExplorerAuthorizationError,
    ExplorerPrivacyError,
    get_metric,
    privacy_check,
    suppress_small_groups,
    validate_level,
)


def test_metric_thresholds_match_dictionary():
    assert get_metric("M01")["minimum_group_size"] == 5
    assert get_metric("M04")["minimum_group_size"] == 10
    assert get_metric("M22")["minimum_group_size"] == 5
    assert get_metric("M27")["minimum_group_size"] == 10


@pytest.mark.parametrize("metric_id", sorted(DISABLED_METRICS))
def test_metrics_without_approved_threshold_are_disabled(metric_id):
    with pytest.raises(ExplorerPrivacyError):
        get_metric(metric_id)


def test_five_employee_group_passes_five_person_threshold():
    assert privacy_check(5, "M01") is True


def test_four_employee_group_fails_five_person_threshold():
    assert privacy_check(4, "M01") is False


def test_nine_employee_group_fails_ten_person_threshold():
    assert privacy_check(9, "M04") is False


def test_ten_employee_group_passes_ten_person_threshold():
    assert privacy_check(10, "M27") is True


def test_negative_group_size_is_rejected():
    with pytest.raises(ExplorerPrivacyError):
        privacy_check(-1, "M01")


def test_small_groups_are_suppressed():
    rows = [
        {"department": "D01", "privacy_group_size": 20,
         "privacy_threshold_met": True},
        {"department": "D02", "privacy_group_size": 2,
         "privacy_threshold_met": False},
        {"department": "D03", "privacy_group_size": 4,
         "privacy_threshold_met": True},
    ]

    result = suppress_small_groups(rows, "M01")

    assert len(result) == 1
    assert result[0]["department"] == "D01"


def test_manager_cannot_access_company_level():
    with pytest.raises(ExplorerAuthorizationError):
        validate_level("MANAGER", "company")


def test_executive_cannot_access_department_level():
    with pytest.raises(ExplorerAuthorizationError):
        validate_level("EXECUTIVE", "department")


def test_hr_can_access_department_level():
    validate_level("HR", "department")


def test_admin_can_access_team_level():
    validate_level("ADMIN", "team")


def test_unknown_role_is_rejected():
    with pytest.raises(ExplorerAuthorizationError):
        validate_level("UNKNOWN", "company")
