
"""JWT authentication and role checks for the PulseIQ KPI Builder."""

import csv
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_USERS_FILE = PROJECT_ROOT / "05_Starter" / "demo_users.csv"

ALGORITHM = "HS256"
TOKEN_TYPE = "access"
ADMIN_IDENTITY = "ADMIN"


class AuthenticationError(ValueError):
    """Raised when a JWT or user identity is invalid."""


class AuthorizationError(PermissionError):
    """Raised when a user lacks permission for an action."""


def _get_secret() -> str:
    """Load JWT secret from environment or Streamlit Cloud secrets."""
    secret = os.getenv("JWT_SECRET")

    if not secret:
        try:
            import streamlit as st
            secret = st.secrets.get("JWT_SECRET")
        except Exception:
            secret = None

    if not secret:
        raise AuthenticationError("JWT_SECRET is not configured.")

    return str(secret)


def load_demo_users() -> dict[str, str]:
    """Load the approved demo username-to-role allowlist."""
    if not DEMO_USERS_FILE.is_file():
        raise AuthenticationError(
            f"Demo user allowlist not found: {DEMO_USERS_FILE}"
        )

    with DEMO_USERS_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        rows = csv.DictReader(file)

        required = {"username", "role"}

        if not rows.fieldnames or not required.issubset(rows.fieldnames):
            raise AuthenticationError(
                "Demo user file has invalid headers."
            )

        users = {}

        for row in rows:
            username = (row.get("username") or "").strip()
            role = (row.get("role") or "").strip().upper()

            if username and role:
                users[username] = role

    return users


def issue_access_token(
    username: str,
    employee_id: str = "",
    expires_minutes: int = 60,
) -> str:
    """
    Issue a signed access token for an approved demo user.

    ADMIN uses a fixed demo-only identity claim.
    Non-admin users require a verified employee ID.
    """
    if not isinstance(username, str) or not username.strip():
        raise AuthenticationError("A valid username is required.")

    if (
        not isinstance(expires_minutes, int)
        or isinstance(expires_minutes, bool)
        or not 1 <= expires_minutes <= 1440
    ):
        raise AuthenticationError(
            "Token lifetime must be 1 to 1440 minutes."
        )

    username = username.strip()
    users = load_demo_users()

    if username not in users:
        raise AuthenticationError(
            "User is not in the demo allowlist."
        )

    role = users[username]

    if role == "ADMIN":
        token_employee_id = ADMIN_IDENTITY
    else:
        if (
            not isinstance(employee_id, str)
            or not employee_id.strip()
        ):
            raise AuthenticationError(
                "A verified employee_id is required."
            )

        token_employee_id = employee_id.strip()

    now = datetime.now(timezone.utc)

    claims = {
        "sub": username,
        "employee_id": token_employee_id,
        "role": role,
        "type": TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid.uuid4()),
    }

    return jwt.encode(
        claims,
        _get_secret(),
        algorithm=ALGORITHM,
    )


def verify_access_token(token: str) -> dict:
    """Verify JWT signature, expiry, required claims and demo role."""
    if not isinstance(token, str) or not token.strip():
        raise AuthenticationError(
            "A bearer access token is required."
        )

    try:
        claims = jwt.decode(
            token,
            _get_secret(),
            algorithms=[ALGORITHM],
            options={
                "require": [
                    "sub",
                    "employee_id",
                    "role",
                    "type",
                    "iat",
                    "exp",
                    "jti",
                ]
            },
        )

    except jwt.PyJWTError as exc:
        raise AuthenticationError(
            "Invalid or expired access token."
        ) from exc

    username = claims.get("sub")
    employee_id = claims.get("employee_id")
    role = claims.get("role")

    users = load_demo_users()

    if not isinstance(username, str) or username not in users:
        raise AuthenticationError(
            "Token subject is not an approved demo user."
        )

    if role != users[username]:
        raise AuthenticationError(
            "Token role does not match the demo allowlist."
        )

    if not isinstance(employee_id, str) or not employee_id.strip():
        raise AuthenticationError(
            "Token has an invalid employee_id."
        )

    if role == "ADMIN" and employee_id != ADMIN_IDENTITY:
        raise AuthenticationError(
            "Invalid ADMIN identity claim."
        )

    if role != "ADMIN" and employee_id == ADMIN_IDENTITY:
        raise AuthenticationError(
            "Non-admin users require a verified employee ID."
        )

    if claims.get("type") != TOKEN_TYPE:
        raise AuthenticationError(
            "Token is not an access token."
        )

    return claims


def require_admin(claims: dict) -> None:
    """Allow only authenticated ADMIN users to manage custom KPIs."""
    if not isinstance(claims, dict):
        raise AuthenticationError(
            "Verified token claims are required."
        )

    if claims.get("role") != "ADMIN":
        raise AuthorizationError(
            "Only ADMIN users can manage custom KPIs."
        )
