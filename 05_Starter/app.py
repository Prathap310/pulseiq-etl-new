
import os
from datetime import date

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------
# PulseIQ Task 5 - Workforce and Headcount Dashboard
# Database access is read-only.
# Metrics come from governed dw.m01/m02/m03 views.
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

st.set_page_config(
    page_title="PulseIQ | Workforce Dashboard",
    page_icon="ðŸ“Š",
    layout="wide",
)

st.title("PulseIQ Workforce & Headcount Dashboard")
st.caption("Task 5 | Workforce analytics | Governed PostgreSQL metrics")

def get_setting(key, default=None):
    try:
        value = st.secrets.get(key)
        if value not in (None, ""):
            return str(value)
    except Exception:
        pass
    return os.getenv(key, default)


@st.cache_resource
def get_connection():
    required = [
        "PGHOST", "PGPORT", "PGDATABASE",
        "PGUSER", "PGPASSWORD", "PGSCHEMA",
    ]
    missing = [key for key in required if not get_setting(key)]

    if missing:
        raise ValueError(
            "Missing database settings in Streamlit Secrets or local .env: "
            + ", ".join(missing)
        )

    if get_setting("PGSCHEMA") != "dw":
        raise ValueError("PGSCHEMA must be dw.")

    return psycopg2.connect(
        host=get_setting("PGHOST"),
        port=get_setting("PGPORT"),
        dbname=get_setting("PGDATABASE"),
        user=get_setting("PGUSER"),
        password=get_setting("PGPASSWORD"),
        sslmode=get_setting("PGSSLMODE", "prefer"),
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
    )

def read_sql(query, params=None):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute(query, params or ())
        columns = [col[0] for col in cur.description]
        rows = cur.fetchall()
    conn.rollback()
    return pd.DataFrame(rows, columns=columns)

@st.cache_data(ttl=300)
def load_headcount():
    return read_sql("""
        SELECT month_start_date, department_id, headcount
        FROM dw.m01_headcount
        WHERE privacy_threshold_met = TRUE
        ORDER BY month_start_date, department_id
    """)

@st.cache_data(ttl=300)
def load_hires():
    return read_sql("""
        SELECT month_start_date, department_id, hires
        FROM dw.m02_hires
        WHERE privacy_threshold_met = TRUE
    """)

@st.cache_data(ttl=300)
def load_exits():
    return read_sql("""
        SELECT month_start_date, department_id, exits
        FROM dw.m03_exits
        WHERE privacy_threshold_met = TRUE
    """)

@st.cache_data(ttl=300)
def load_dimensions():
    departments = read_sql("""
        SELECT department_id, department_name
        FROM dw.dim_department
        ORDER BY department_name
    """)

    tier_counts = read_sql("""
        SELECT
            e.department_id,
            COALESCE(l.city_tier, 'Unknown') AS city_tier,
            COUNT(DISTINCT e.employee_id) AS employee_count
        FROM dw.dim_employee e
        LEFT JOIN dw.dim_location l
            ON e.work_location = l.work_location
        WHERE UPPER(TRIM(e.is_current)) IN ('Y', 'YES', 'TRUE', '1')
        GROUP BY e.department_id, COALESCE(l.city_tier, 'Unknown')
        HAVING COUNT(DISTINCT e.employee_id) >= 5
    """)

    mode_counts = read_sql("""
        SELECT
            department_id,
            COALESCE(work_mode, 'Unknown') AS work_mode,
            COUNT(DISTINCT employee_id) AS employee_count
        FROM dw.dim_employee
        WHERE UPPER(TRIM(is_current)) IN ('Y', 'YES', 'TRUE', '1')
        GROUP BY department_id, COALESCE(work_mode, 'Unknown')
        HAVING COUNT(DISTINCT employee_id) >= 5
    """)

    return departments, tier_counts, mode_counts

try:
    headcount = load_headcount()
    hires = load_hires()
    exits = load_exits()
    departments, tier_counts, mode_counts = load_dimensions()
except Exception as exc:
    st.error(
        "Could not load dashboard data. Check PostgreSQL availability, "
        "the .env settings, and database permissions."
    )
    st.exception(exc)
    st.stop()

if headcount.empty:
    st.warning(
        "No headcount rows are available after applying the metric's "
        "privacy threshold. Check the governed view and data."
    )
    st.stop()

for frame in (headcount, hires, exits):
    frame["month_start_date"] = pd.to_datetime(frame["month_start_date"])

headcount = headcount.merge(
    departments, on="department_id", how="left"
)
headcount["department_name"] = headcount["department_name"].fillna(
    headcount["department_id"]
)

hires = hires.merge(departments, on="department_id", how="left")
hires["department_name"] = hires["department_name"].fillna(
    hires["department_id"]
)

exits = exits.merge(departments, on="department_id", how="left")
exits["department_name"] = exits["department_name"].fillna(
    exits["department_id"]
)

# ---------------- Filters ----------------
min_date = headcount["month_start_date"].min().date()
max_date = headcount["month_start_date"].max().date()

st.sidebar.header("Dashboard Filters")
selected_dates = st.sidebar.date_input(
    "Reporting date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

department_options = sorted(
    departments["department_name"].dropna().unique().tolist()
)

selected_departments = st.sidebar.multiselect(
    "Department",
    options=department_options,
    default=department_options,
    key="department_filter",
)

filtered = headcount[
    headcount["month_start_date"].dt.date.between(start_date, end_date)
    & headcount["department_name"].isin(selected_departments)
].copy()

filtered_hires = hires[
    hires["month_start_date"].dt.date.between(start_date, end_date)
    & hires["department_name"].isin(selected_departments)
].copy()

filtered_exits = exits[
    exits["month_start_date"].dt.date.between(start_date, end_date)
    & exits["department_name"].isin(selected_departments)
].copy()

if filtered.empty:
    st.warning("No data matches these filters. Select a wider date range or more departments.")
    st.stop()

# ---------------- KPI cards ----------------
monthly = (
    filtered.groupby("month_start_date", as_index=False)["headcount"]
    .sum()
    .sort_values("month_start_date")
)
latest = monthly.iloc[-1]
previous = monthly.iloc[-2] if len(monthly) > 1 else None

current_headcount = int(latest["headcount"])
change = (
    current_headcount - int(previous["headcount"])
    if previous is not None else None
)
total_hires = int(filtered_hires["hires"].sum()) if not filtered_hires.empty else 0
total_exits = int(filtered_exits["exits"].sum()) if not filtered_exits.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest Headcount", f"{current_headcount:,}", delta=change)
c2.metric("Hires in Period", f"{total_hires:,}")
c3.metric("Exits in Period", f"{total_exits:,}")
c4.metric("Departments Selected", f"{len(selected_departments):,}")

st.caption(
    f"Latest visible reporting month: {latest['month_start_date']:%B %Y}. "
    "Headcount includes only groups passing the metric privacy threshold."
)

# ---------------- Chart 1: Headcount trend ----------------
st.subheader("1. Monthly Headcount Trend")
fig_trend = px.line(
    monthly,
    x="month_start_date",
    y="headcount",
    markers=True,
    labels={"month_start_date": "Month", "headcount": "Headcount"},
    title="Total headcount across selected departments",
)
st.plotly_chart(fig_trend, use_container_width=True)

if len(monthly) > 1:
    first = int(monthly.iloc[0]["headcount"])
    last = int(monthly.iloc[-1]["headcount"])
    delta = last - first
    pct = (delta / first * 100) if first else None
    pct_text = f" ({pct:+.1f}%)" if pct is not None else ""
    st.info(
        f"**Insight:** Headcount changed by {delta:+,} employees "
        f"from {monthly.iloc[0]['month_start_date']:%b %Y} "
        f"to {monthly.iloc[-1]['month_start_date']:%b %Y}{pct_text}."
    )
else:
    st.info("**Insight:** Only one month is available for the selected filters.")

# ---------------- Chart 2: Department breakdown ----------------
st.subheader("2. Headcount by Department")
department_summary = (
    filtered.groupby("department_name", as_index=False)["headcount"]
    .mean()
    .rename(columns={"headcount": "average_monthly_headcount"})
    .sort_values("average_monthly_headcount", ascending=False)
)
fig_dept = px.bar(
    department_summary,
    x="department_name",
    y="average_monthly_headcount",
    labels={
        "department_name": "Department",
        "average_monthly_headcount": "Average monthly headcount",
    },
    title="Average monthly headcount by department",
)
st.plotly_chart(fig_dept, use_container_width=True)

if not department_summary.empty:
    top = department_summary.iloc[0]
    st.info(
        f"**Insight:** {top['department_name']} has the highest average "
        f"monthly headcount ({top['average_monthly_headcount']:.1f}) "
        "among the selected departments."
    )

# ---------------- Chart 3: Location tier ----------------
st.subheader("3. Workforce by Location Tier")

tier_filtered = tier_counts.merge(
    departments, on="department_id", how="left"
)
tier_filtered = tier_filtered[
    tier_filtered["department_name"].isin(selected_departments)
]

tier_summary = (
    tier_filtered.groupby("city_tier", as_index=False)["employee_count"]
    .sum()
    .sort_values("employee_count", ascending=False)
)

if not tier_summary.empty:
    fig_tier = px.bar(
        tier_summary,
        x="city_tier",
        y="employee_count",
        labels={"city_tier": "Location tier", "employee_count": "Employees"},
        title="Current employees by location tier",
    )
    st.plotly_chart(fig_tier, use_container_width=True)
    top_tier = tier_summary.iloc[0]
    st.info(
        f"**Insight:** {top_tier['city_tier']} has the most current employees "
        f"({int(top_tier['employee_count']):,}) in the selected departments."
    )
else:
    st.warning("No location-tier groups meet the minimum group size for the selected departments.")

# ---------------- Chart 4: Work mode ----------------
st.subheader("4. Workforce by Work Mode")

mode_filtered = mode_counts.merge(
    departments, on="department_id", how="left"
)
mode_filtered = mode_filtered[
    mode_filtered["department_name"].isin(selected_departments)
]

mode_summary = (
    mode_filtered.groupby("work_mode", as_index=False)["employee_count"]
    .sum()
    .sort_values("employee_count", ascending=False)
)

if not mode_summary.empty:
    fig_mode = px.pie(
        mode_summary,
        names="work_mode",
        values="employee_count",
        hole=0.45,
        title="Current employees by work mode",
    )
    st.plotly_chart(fig_mode, use_container_width=True)
    top_mode = mode_summary.iloc[0]
    st.info(
        f"**Insight:** {top_mode['work_mode']} is the most common work mode, "
        f"with {int(top_mode['employee_count']):,} current employees "
        "in the selected departments."
    )
else:
    st.warning("No work-mode groups meet the minimum group size for the selected departments.")

# ---------------- CEO questions ----------------
st.subheader("Questions for the CEO")
st.markdown("""
1. What explains the largest month-to-month changes in headcount?
2. Which departments need hiring support based on their headcount trends?
3. Are location tiers aligned with our hiring and workforce strategy?
4. Does the current mix of work modes support productivity and retention?
5. What workforce capacity changes should we plan for over the next quarter?
""")

st.caption(
    "Data note: Headcount KPIs and trend charts use governed dw.m01_headcount. "
    "Hires and exits use dw.m02_hires and dw.m03_exits. Location-tier and "
    "work-mode breakdowns use current employee aggregates from PostgreSQL. "
    "Department/category groups with fewer than 5 employees are suppressed. "
    "No individual employee names or IDs are loaded into these charts."
)

