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
    required = [
        "PGHOST", "PGPORT", "PGDATABASE",
        "PGUSER", "PGPASSWORD", "PGSCHEMA",
    ]
    missing = [key for key in required if not get_setting(key)]
    if missing:
        raise ValueError(
            "Missing database settings: " + ", ".join(missing)
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


st.subheader("Available KPI definitions")

names = [item["name"] for item in EXAMPLES]
selected_name = st.selectbox("Select a KPI", names)

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
    st.markdown("**Status**")
    st.info(definition["status"].upper())
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

            csv_data = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download preview CSV",
                data=csv_data,
                file_name="custom_kpi_preview.csv",
                mime="text/csv",
            )

except Exception as exc:
    st.error("Could not prepare the KPI preview.")
    st.exception(exc)

st.divider()
st.subheader("Governance")

st.warning(
    "This page currently supports read-only KPI previews. "
    "Admin authentication and persistent approval storage have not "
    "yet been configured. A KPI must not be treated as approved "
    "or published until those controls are implemented."
)
