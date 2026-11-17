from datetime import datetime, timedelta, timezone

import jwt
import pytest

from Src.kpi_auth import (
    AuthenticationError,
    AuthorizationError,
    require_admin,
    verify_access_token,
)


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-for-unit-tests-only-32bytes")


def make_token(username="admin.demo", role="ADMIN"):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": username,
        "employee_id": "TEST-EMPLOYEE",
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=10),
        "jti": "test-token-id",
    }
    return jwt.encode(claims, "test-secret-for-unit-tests-only-32bytes", algorithm="HS256")


def test_valid_admin_token():
    claims = verify_access_token(make_token())
    assert claims["sub"] == "admin.demo"
    assert claims["role"] == "ADMIN"


def test_non_admin_token_is_valid_but_cannot_manage_kpis():
    claims = verify_access_token(make_token("hr.demo", "HR"))
    with pytest.raises(AuthorizationError):
        require_admin(claims)


def test_admin_can_manage_kpis():
    require_admin(verify_access_token(make_token()))


def test_unknown_user_is_rejected():
    with pytest.raises(AuthenticationError):
        verify_access_token(make_token("unknown.demo", "ADMIN"))


def test_role_mismatch_is_rejected():
    with pytest.raises(AuthenticationError):
        verify_access_token(make_token("hr.demo", "ADMIN"))


def test_invalid_signature_is_rejected():
    token = jwt.encode(
        {
            "sub": "admin.demo",
            "employee_id": "TEST-EMPLOYEE",
            "role": "ADMIN",
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
            "jti": "test-token-id",
        },
        "wrong-secret-for-jwt-test-only-32bytes",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        verify_access_token(token)


def test_expired_token_is_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "admin.demo",
            "employee_id": "TEST-EMPLOYEE",
            "role": "ADMIN",
            "type": "access",
            "iat": now - timedelta(minutes=20),
            "exp": now - timedelta(minutes=10),
            "jti": "expired-token-id",
        },
        "test-secret-for-unit-tests-only-32bytes",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        verify_access_token(token)


def test_missing_token_is_rejected():
    with pytest.raises(AuthenticationError):
        verify_access_token("")


def test_missing_employee_id_is_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "admin.demo",
            "role": "ADMIN",
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=10),
            "jti": "missing-employee-id",
        },
        "test-secret-for-unit-tests-only-32bytes",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        verify_access_token(token)

