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

from Src.kpi_auth import AuthenticationError, verify_access_token
from Src.kpi_explorer import (
    METRIC_NAMES,
    ROLE_LEVELS,
    ExplorerAuthorizationError,
    get_manager_team_scope,
    verify_employee_identity,
)
from Src.kpi_explorer_service import execute_kpi_query


st.set_page_config(
    page_title="PulseIQ | KPI Explorer",
    page_icon="??",
    layout="wide",
)

st.title("Self-service KPI Explorer")
st.caption("Task 18 | Governed workforce, payroll, attendance, task and risk KPIs")


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


def read_options(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(sql, params or ())
            rows = cursor.fetchall()
        conn.rollback()
        return rows
    finally:
        conn.close()


def load_months():
    rows = read_options("""
        SELECT DISTINCT month_start_date
        FROM dw.fact_headcount_monthly
        ORDER BY month_start_date DESC
    """)
    return [row[0].strftime("%Y-%m-01") for row in rows]


def load_departments():
    rows = read_options("""
        SELECT DISTINCT department_id
        FROM dw.fact_headcount_monthly
        WHERE department_id <> 'D00'
        ORDER BY department_id
    """)
    return [row[0] for row in rows]


def load_teams():
    rows = read_options("""
        SELECT team_id, team_name
        FROM dw.dim_team
        ORDER BY team_id
    """)
    return rows


def load_sprints():
    rows = read_options("""
        SELECT DISTINCT sprint_id
        FROM dw.fact_task
        WHERE sprint_id IS NOT NULL
        ORDER BY sprint_id
    """)
    return [row[0] for row in rows]


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

st.subheader("Authentication")

token = st.text_input(
    "Paste your signed JWT access token",
    type="password",
    help="Use a token issued for an approved account in demo_users.csv.",
)

if not token:
    st.info("Authenticate with your approved demo account to continue.")
    st.stop()

try:
    claims = verify_access_token(token.strip())
except AuthenticationError:
    st.error("Authentication failed. Check the token and try again.")
    st.stop()

role = claims["role"]
employee_id = claims["employee_id"]

st.success(f"Authenticated: {claims['sub']} | Role: {role}")

st.divider()

# ---------------------------------------------------------
# Available metrics and authorized dimensions
# ---------------------------------------------------------

metric_ids = list(METRIC_NAMES.keys())
metric_id = st.selectbox(
    "Select KPI",
    metric_ids,
    format_func=lambda value: f"{value} — {METRIC_NAMES[value]}",
)

allowed_levels = sorted(ROLE_LEVELS[role])

# Task KPIs are team-level only.
if metric_id in {"M22", "M23", "M25"}:
    allowed_levels = [level for level in allowed_levels if level == "team"]
# Other currently enabled KPIs do not support team drill-down.
else:
    allowed_levels = [
        level for level in allowed_levels
        if level in {"company", "department"}
    ]

if not allowed_levels:
    st.warning("Your role has no approved access level for this KPI.")
    st.stop()

level = st.selectbox("Analysis level", allowed_levels)

report_month = None
department_id = None
team_id = None
sprint_id = None

# ---------------------------------------------------------
# Filters
# ---------------------------------------------------------

if level == "department":
    departments = load_departments()

    if not departments:
        st.warning("No department options are available.")
        st.stop()

    department_id = st.selectbox(
        "Department",
        departments,
    )

if metric_id not in {"M22", "M23", "M25", "M27"}:
    months = load_months()

    if not months:
        st.warning("No reporting months are available.")
        st.stop()

    report_month = st.selectbox(
        "Reporting month",
        months,
    )

if metric_id in {"M22", "M23", "M25"}:
    all_teams = load_teams()

    if role == "MANAGER":
        conn = get_connection()
        try:
            verified = verify_employee_identity(conn, employee_id)
            permitted_teams = get_manager_team_scope(
                conn, verified["employee_id"]
            )
        finally:
            conn.close()

        permitted_ids = {
            item["team_id"] for item in permitted_teams
        }
        all_teams = [
            item for item in all_teams
            if item[0] in permitted_ids
        ]

    if not all_teams:
        st.warning("No teams are available within your authorized scope.")
        st.stop()

    team_labels = {
        team[0]: f"{team[0]} — {team[1]}" for team in all_teams
    }

    team_choices = [None] + [team[0] for team in all_teams]
    selected_team = st.selectbox(
        "Team",
        team_choices,
        format_func=lambda value: (
            "All permitted teams" if value is None
            else team_labels[value]
        ),
    )
    team_id = selected_team

    sprints = load_sprints()
    sprint_choices = [None] + sprints
    sprint_id = st.selectbox(
        "Sprint",
        sprint_choices,
        format_func=lambda value: (
            "All sprints" if value is None else value
        ),
    )

st.divider()

# ---------------------------------------------------------
# Execute governed KPI
# ---------------------------------------------------------

if st.button("Run KPI Explorer", type="primary"):
    conn = None

    try:
        conn = get_connection()

        with st.spinner("Running privacy-governed KPI query..."):
            results = execute_kpi_query(
                connection=conn,
                token=token.strip(),
                metric_id=metric_id,
                level=level,
                report_month=report_month,
                department_id=department_id,
                team_id=team_id,
                sprint_id=sprint_id,
            )

        if not results:
            st.warning(
                "No results meet the access and minimum group-size rules."
            )
        else:
            frame = pd.DataFrame(results)

            st.subheader(METRIC_NAMES[metric_id])
            st.metric(
                "Groups returned",
                len(frame),
            )

            st.dataframe(
                frame,
                use_container_width=True,
                hide_index=True,
            )

            if "metric_value" in frame.columns:
                st.bar_chart(
                    frame.set_index("group_id")["metric_value"]
                )

            st.caption(
                "Results are filtered by your authenticated role "
                "and the KPI privacy thresholds."
            )

    except ExplorerAuthorizationError as exc:
        st.error(f"Access denied: {exc}")
    except Exception as exc:
        st.error(f"Unable to run the KPI query: {exc}")
    finally:
        if conn is not None:
            conn.close()
