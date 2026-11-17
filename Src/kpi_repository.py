
"""Persistent storage for governed PulseIQ custom KPIs."""

import copy
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from Src.kpi_builder import validate_definition


def save_draft(
    connection: Any,
    definition: dict,
    created_by: str,
) -> dict:
    """Save a new version of a KPI as a draft."""

    if not isinstance(created_by, str) or not created_by.strip():
        raise ValueError("Authenticated creator identity is required.")

    draft = copy.deepcopy(definition)
    draft["status"] = "draft"
    draft.pop("approved_by", None)
    draft.pop("approved_at", None)

    validate_definition(draft)

    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        # Prevent concurrent versions of the same KPI name.
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s))",
            (draft["name"].strip().lower(),),
        )

        cursor.execute(
            """
            SELECT COALESCE(MAX(version), 0) + 1 AS next_version
            FROM dw.custom_kpi_definitions
            WHERE LOWER(name) = LOWER(%s)
            """,
            (draft["name"],),
        )

        draft["version"] = cursor.fetchone()["next_version"]

        cursor.execute(
            """
            INSERT INTO dw.custom_kpi_definitions
                (name, description, definition, version,
                 status, created_by)
            VALUES (%s, %s, %s, %s, 'draft', %s)
            RETURNING kpi_id, name, version, status,
                      created_by, created_at
            """,
            (
                draft["name"],
                draft["description"],
                Json(draft),
                draft["version"],
                created_by.strip(),
            ),
        )

        result = dict(cursor.fetchone())

    connection.commit()
    return result


def load_kpis(
    connection: Any,
    status: str | None = None,
) -> list[dict]:
    """Load saved KPI definitions."""

    if status not in (None, "draft", "approved"):
        raise ValueError("Invalid KPI status.")

    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        if status:
            cursor.execute(
                """
                SELECT kpi_id, name, description, definition,
                       version, status, created_by, approved_by,
                       created_at, approved_at
                FROM dw.custom_kpi_definitions
                WHERE status = %s
                ORDER BY name, version DESC
                """,
                (status,),
            )
        else:
            cursor.execute(
                """
                SELECT kpi_id, name, description, definition,
                       version, status, created_by, approved_by,
                       created_at, approved_at
                FROM dw.custom_kpi_definitions
                ORDER BY name, version DESC
                """
            )

        return [dict(row) for row in cursor.fetchall()]


def approve_kpi(
    connection: Any,
    kpi_id: int,
    approver: str,
) -> dict:
    """Approve a saved draft using the database role permissions."""

    if not isinstance(kpi_id, int) or isinstance(kpi_id, bool) or kpi_id < 1:
        raise ValueError("Invalid KPI ID.")

    if not isinstance(approver, str) or not approver.strip():
        raise ValueError("Authenticated approver identity is required.")

    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            UPDATE dw.custom_kpi_definitions
            SET status = 'approved',
                approved_by = %s,
                approved_at = CURRENT_TIMESTAMP,
                definition = jsonb_set(
                    definition,
                    '{status}',
                    '"approved"'::jsonb,
                    true
                )
            WHERE kpi_id = %s
              AND status = 'draft'
            RETURNING kpi_id, name, version, status,
                      created_by, approved_by, approved_at
            """,
            (approver.strip(), kpi_id),
        )

        result = cursor.fetchone()

        if result is None:
            connection.rollback()
            raise ValueError(
                "Draft not found or KPI has already been approved."
            )

    connection.commit()
    return dict(result)
