import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

from Src.kpi_builder import EXAMPLES, build_query
from Src.kpi_auth import AuthorizationError, require_admin
from Src.kpi_session import get_authenticated_session
from Src.kpi_repository import save_draft, load_kpis, approve_kpi


st.set_page_config(
    page_title="PulseIQ | Custom KPI Builder",
    page_icon="📊",
    layout="wide",
)

st.title("Custom KPI Builder")
st.caption("Task 17 | Governed KPI definitions and read-only previews")


def get_setting(key, default=None):
    try:
        value = st.secrets.get(key)
        if value not in (None, ""):
            return str(value)
    except Exception:
        pass
    return os.getenv(key, default)


def get_connection():
    """Read-only warehouse connection for KPI previews."""
    required = [
        "PGHOST", "PGPORT", "PGDATABASE",
        "PGUSER", "PGPASSWORD", "PGSCHEMA",
    ]
    missing = [key for key in required if not get_setting(key)]
    if missing:
        raise ValueError(
            "Missing reader database settings: " + ", ".join(missing)
        )

    if get_setting("PGSCHEMA") != "dw":
        raise ValueError("PGSCHEMA must be dw.")

    return psycopg2.connect(
        host=get_setting("PGHOST"),
        port=get_setting("PGPORT"),
        dbname=get_setting("PGDATABASE"),
        user=get_setting("PGUSER"),
        password=get_setting("PGPASSWORD"),
        sslmode=get_setting("PGSSLMODE", "require"),
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
    )


def get_admin_connection():
    """Separate write-enabled connection; never use the reader credentials."""
    required = [
        "KPI_ADMIN_PGHOST",
        "KPI_ADMIN_PGPORT",
        "KPI_ADMIN_PGDATABASE",
        "KPI_ADMIN_PGUSER",
        "KPI_ADMIN_PGPASSWORD",
    ]
    missing = [key for key in required if not get_setting(key)]
    if missing:
        raise ValueError(
            "Admin database credentials are not configured: "
            + ", ".join(missing)
        )

    return psycopg2.connect(
        host=get_setting("KPI_ADMIN_PGHOST"),
        port=get_setting("KPI_ADMIN_PGPORT"),
        dbname=get_setting("KPI_ADMIN_PGDATABASE"),
        user=get_setting("KPI_ADMIN_PGUSER"),
        password=get_setting("KPI_ADMIN_PGPASSWORD"),
        sslmode=get_setting("KPI_ADMIN_PGSSLMODE", "require"),
        connect_timeout=10,
        options="-c default_transaction_read_only=off",
    )


def preview_query(sql, params):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(sql, params)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
        conn.rollback()
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


def repository_action(action, *args):
    conn = get_admin_connection()
    try:
        return action(conn, *args)
    finally:
        conn.close()


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

claims, token = get_authenticated_session("custom_kpi_builder")

is_admin = claims["role"] == "ADMIN"

st.divider()

# ---------------------------------------------------------
# KPI examples and preview
# ---------------------------------------------------------

st.subheader("Available KPI definitions")

names = [item["name"] for item in EXAMPLES]
selected_name = st.selectbox("Select a KPI example", names)

definition = next(
    item for item in EXAMPLES if item["name"] == selected_name
)

left, right = st.columns(2)

with left:
    st.markdown("**Description**")
    st.write(definition["description"])
    st.markdown("**Source table**")
    st.code("dw." + definition["source_table"])

with right:
    st.markdown("**Owner**")
    st.write(definition["owner"])
    st.markdown("**Grouping**")
    st.write(", ".join(definition["group_by"]))

st.divider()
st.subheader("Query preview")

try:
    sql, params = build_query(definition)
    st.code(sql, language="sql")
    st.caption(f"Bound parameters: {len(params)}")

    if st.button("Run KPI Preview", type="primary"):
        with st.spinner("Querying the read-only warehouse..."):
            result = preview_query(sql, params)

        if result.empty:
            st.warning(
                "No rows returned. Check the data and privacy threshold."
            )
        else:
            st.success(f"Preview returned {len(result)} rows.")
            st.dataframe(result, use_container_width=True)

            st.download_button(
                "Download preview CSV",
                data=result.to_csv(index=False).encode("utf-8"),
                file_name="custom_kpi_preview.csv",
                mime="text/csv",
            )

except Exception:
    st.error("Could not prepare the KPI preview.")
    st.exception(Exception("Check the KPI definition and warehouse settings."))


# ---------------------------------------------------------
# Admin-only draft creation and approval
# ---------------------------------------------------------

st.divider()
st.subheader("KPI Governance")

if not is_admin:
    st.warning(
        "Your authenticated role is not ADMIN. "
        "You can preview KPIs but cannot create or approve definitions."
    )
else:
    try:
        require_admin(claims)
    except AuthorizationError:
        st.error("You are not authorized to manage KPIs.")
        st.stop()

    st.success("ADMIN permissions verified.")

    st.markdown("**Create a draft from the selected example**")

    if st.button("Save Selected KPI as Draft"):
        try:
            saved = repository_action(
                save_draft,
                definition,
                claims["sub"],
            )
            st.success(
                f"Draft saved: KPI #{saved['kpi_id']} "
                f"| Version {saved['version']}"
            )
        except Exception as exc:
            st.error("Could not save the KPI draft.")
            st.exception(exc)

    st.divider()
    st.markdown("**Saved draft definitions**")

    if st.button("Refresh Drafts"):
        st.session_state["refresh_kpi_drafts"] = True

    try:
        drafts = repository_action(load_kpis, "draft")

        if drafts:
            draft_labels = {
                f"#{row['kpi_id']} | {row['name']} | "
                f"v{row['version']}": row["kpi_id"]
                for row in drafts
            }

            selected_draft = st.selectbox(
                "Select a draft to approve",
                list(draft_labels.keys()),
            )

            selected_id = draft_labels[selected_draft]

            if st.button("Approve Selected Draft"):
                approved = repository_action(
                    approve_kpi,
                    selected_id,
                    claims["sub"],
                )
                st.success(
                    f"Approved KPI #{approved['kpi_id']}: "
                    f"{approved['name']} v{approved['version']}"
                )
                st.rerun()

            st.dataframe(
                pd.DataFrame([
                    {
                        "KPI ID": row["kpi_id"],
                        "Name": row["name"],
                        "Version": row["version"],
                        "Created By": row["created_by"],
                        "Created At": row["created_at"],
                    }
                    for row in drafts
                ]),
                use_container_width=True,
            )
        else:
            st.info("No saved drafts are available.")

    except Exception as exc:
        st.error("Could not load saved KPI drafts.")
        st.exception(exc)


# ---------------------------------------------------------
# Approved definitions
# ---------------------------------------------------------

st.divider()
st.subheader("Approved KPI Definitions")

try:
    approved = repository_action(load_kpis, "approved")

    if approved:
        st.dataframe(
            pd.DataFrame([
                {
                    "KPI ID": row["kpi_id"],
                    "Name": row["name"],
                    "Version": row["version"],
                    "Approved By": row["approved_by"],
                    "Approved At": row["approved_at"],
                }
                for row in approved
            ]),
            use_container_width=True,
        )
    else:
        st.info("No approved custom KPIs are published yet.")

except Exception as exc:
    st.error("Could not load approved KPI definitions.")
    st.exception(exc)


st.caption(
    "Task 17 | Drafts require ADMIN approval. "
    "Only approved definitions are listed in the publication section. "
    "SQL previews use a separate read-only warehouse connection."
)
