
import os
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

st.set_page_config(
    page_title="PulseIQ | Attendance & Leave Dashboard",
    page_icon="📊",
    layout="wide",
)
st.title("PulseIQ Attendance & Leave Trends Dashboard")
st.caption("Task 6 | Attendance, leave, overtime and holiday trends")


def get_connection():
    required = [
        "PGHOST", "PGPORT", "PGDATABASE",
        "PGUSER", "PGPASSWORD", "PGSCHEMA",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(
            "Missing database settings in .env: " + ", ".join(missing)
        )
    if os.getenv("PGSCHEMA") != "dw":
        raise ValueError("PGSCHEMA must be dw.")

    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
    )


def read_sql(query, params=None):
    with get_connection() as conn:
        conn.set_session(readonly=True, autocommit=False)
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=300)
def load_departments():
    return read_sql("""
        SELECT department_id, department_name
        FROM dw.dim_department
        WHERE department_id NOT IN ('ALL', 'D00')
        ORDER BY department_name
    """)


@st.cache_data(ttl=300)
def load_attendance():
    return read_sql("""
        SELECT
            a.period_end_date,
            a.department_id,
            d.department_name,
            COUNT(DISTINCT a.employee_id) AS employees,
            SUM(a.scheduled_days) AS scheduled_days,
            SUM(a.present_days) AS present_days,
            SUM(a.half_days_unpaid) AS half_days_unpaid,
            SUM(a.late_arrivals) AS late_arrivals,
            SUM(a.overtime_hours) AS overtime_hours,
            100.0 * SUM(
                a.present_days + 0.5 * a.half_days_unpaid
            ) / NULLIF(SUM(a.scheduled_days), 0)
                AS attendance_rate_pct
        FROM dw.fact_attendance_monthly a
        JOIN dw.dim_department d
          ON a.department_id = d.department_id
        WHERE a.department_id NOT IN ('ALL', 'D00')
        GROUP BY
            a.period_end_date,
            a.department_id,
            d.department_name
        HAVING COUNT(DISTINCT a.employee_id) >= 5
        ORDER BY a.period_end_date, d.department_name
    """)


@st.cache_data(ttl=300)
def load_leave():
    return read_sql("""
        SELECT start_date, end_date, leave_type_code, status, days
        FROM dw.fact_leave
        WHERE status = 'Approved'
          AND start_date IS NOT NULL
    """)


@st.cache_data(ttl=300)
def load_calendar():
    return read_sql("""
        SELECT
            "date" AS calendar_date,
            year_month,
            is_holiday,
            is_working_day,
            is_weekend
        FROM dw.dim_date
        WHERE "date" IS NOT NULL
        ORDER BY "date"
    """)


try:
    departments = load_departments()
    attendance = load_attendance()
    leave = load_leave()
    calendar = load_calendar()
except Exception as exc:
    st.error(
        "Could not load Task 6 data. Check PostgreSQL, .env settings, "
        "and table permissions."
    )
    st.exception(exc)
    st.stop()


if attendance.empty:
    st.warning(
        "No attendance data is available after applying "
        "the minimum group-size threshold."
    )
    st.stop()


attendance["period_end_date"] = pd.to_datetime(
    attendance["period_end_date"]
)
for col in ["attendance_rate_pct", "overtime_hours", "late_arrivals"]:
    attendance[col] = pd.to_numeric(attendance[col], errors="coerce")

leave["start_date"] = pd.to_datetime(leave["start_date"])
leave["end_date"] = pd.to_datetime(leave["end_date"])
leave["days"] = pd.to_numeric(
    leave["days"], errors="coerce"
).fillna(0)
calendar["calendar_date"] = pd.to_datetime(calendar["calendar_date"])


# Sidebar filters
min_date = attendance["period_end_date"].min().date()
max_date = attendance["period_end_date"].max().date()

st.sidebar.header("Dashboard Filters")
selected_dates = st.sidebar.date_input(
    "Reporting date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
elif isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 1:
    start_date = end_date = selected_dates[0]
else:
    start_date, end_date = min_date, max_date

department_options = sorted(
    departments["department_name"].dropna().unique().tolist()
)
selected_departments = st.sidebar.multiselect(
    "Department",
    options=department_options,
    default=department_options,
    key="task6_department_filter",
)

filtered = attendance[
    attendance["period_end_date"].dt.date.between(start_date, end_date)
    & attendance["department_name"].isin(selected_departments)
].copy()

if filtered.empty:
    st.warning(
        "No data matches these filters. Select a wider date range "
        "or more departments."
    )
    st.stop()


# Monthly totals and correctly weighted attendance rate
monthly = (
    filtered.groupby("period_end_date", as_index=False)
    .agg(
        scheduled_days=("scheduled_days", "sum"),
        present_days=("present_days", "sum"),
        half_days_unpaid=("half_days_unpaid", "sum"),
        late_arrivals=("late_arrivals", "sum"),
        overtime_hours=("overtime_hours", "sum"),
    )
    .sort_values("period_end_date")
)

monthly["attendance_rate_pct"] = (
    100.0
    * (
        monthly["present_days"]
        + 0.5 * monthly["half_days_unpaid"]
    )
    / monthly["scheduled_days"].replace(0, float("nan"))
)

approved_leave = leave[
    leave["start_date"].dt.date.between(start_date, end_date)
].copy()

leave_summary = (
    approved_leave.groupby("leave_type_code", as_index=False)
    .agg(
        approved_leave_days=("days", "sum"),
        approved_requests=("days", "size"),
    )
    .sort_values("approved_leave_days", ascending=False)
)


# KPI cards
latest = monthly.iloc[-1]
previous = monthly.iloc[-2] if len(monthly) > 1 else None

attendance_delta = (
    latest["attendance_rate_pct"] - previous["attendance_rate_pct"]
    if previous is not None else None
)
late_delta = (
    int(latest["late_arrivals"] - previous["late_arrivals"])
    if previous is not None else None
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Latest Attendance Rate",
    f"{latest['attendance_rate_pct']:.2f}%",
    delta=(
        f"{attendance_delta:+.2f} pp"
        if attendance_delta is not None else None
    ),
)
c2.metric(
    "Late Arrivals (Latest Month)",
    f"{int(latest['late_arrivals']):,}",
    delta=late_delta,
    delta_color="inverse",
)
c3.metric(
    "Overtime Hours (Latest Month)",
    f"{latest['overtime_hours']:,.1f}",
)
c4.metric(
    "Approved Leave Days (Selected Period)",
    f"{approved_leave['days'].sum():,.1f}",
)

st.caption(
    f"Attendance reporting period: {start_date:%d %b %Y} to "
    f"{end_date:%d %b %Y}. Department-level metrics require "
    "at least five distinct employees."
)


# 1. Attendance trend by department
st.subheader("1. Monthly Attendance Rate by Department")
fig_attendance = px.line(
    filtered,
    x="period_end_date",
    y="attendance_rate_pct",
    color="department_name",
    markers=True,
    labels={
        "period_end_date": "Month ending",
        "attendance_rate_pct": "Attendance rate (%)",
        "department_name": "Department",
    },
)
fig_attendance.update_yaxes(ticksuffix="%")
st.plotly_chart(fig_attendance, use_container_width=True)


# 2. Late arrivals or overtime
st.subheader("2. Late Arrivals and Overtime by Month")
metric_choice = st.radio(
    "Choose monthly metric",
    ["Late arrivals", "Overtime hours"],
    horizontal=True,
)
y_col = (
    "late_arrivals"
    if metric_choice == "Late arrivals"
    else "overtime_hours"
)
fig_workload = px.bar(
    monthly,
    x="period_end_date",
    y=y_col,
    labels={
        "period_end_date": "Month ending",
        y_col: metric_choice,
    },
    title=f"Monthly {metric_choice.lower()} across selected departments",
)
st.plotly_chart(fig_workload, use_container_width=True)


# 3. Approved leave
st.subheader("3. Approved Leave Days by Leave Type")
if not leave_summary.empty:
    fig_leave = px.bar(
        leave_summary,
        x="leave_type_code",
        y="approved_leave_days",
        text="approved_leave_days",
        labels={
            "leave_type_code": "Leave type code",
            "approved_leave_days": "Approved leave days",
        },
    )
    st.plotly_chart(fig_leave, use_container_width=True)
    st.dataframe(
        leave_summary.round({"approved_leave_days": 2}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Leave is grouped by the recorded leave_type_code. "
        "Only status='Approved' is included."
    )
else:
    st.info("No approved leave starts within the selected reporting date range.")


# 4. Holiday timeline
st.subheader("4. Holidays and Long-Weekend Timeline")
cal = calendar[
    calendar["calendar_date"].dt.date.between(start_date, end_date)
].copy()

for col in ["is_holiday", "is_working_day", "is_weekend"]:
    cal[col + "_flag"] = cal[col].astype(str).str.strip().str.upper()

holidays = cal[cal["is_holiday_flag"].eq("Y")].copy()

if not holidays.empty:
    holidays["event"] = holidays.apply(
        lambda r: (
            "Holiday on weekend"
            if r["is_weekend_flag"] in ("Y", "YES", "TRUE", "1")
            else "Holiday"
        ),
        axis=1,
    )
    fig_holidays = px.scatter(
        holidays,
        x="calendar_date",
        y="event",
        color="event",
        hover_data=["year_month", "is_working_day", "is_weekend"],
        labels={
            "calendar_date": "Date",
            "event": "Calendar event",
        },
        title="Recorded holidays in selected reporting period",
    )
    st.plotly_chart(fig_holidays, use_container_width=True)
    st.dataframe(
        holidays[
            [
                "calendar_date", "year_month", "is_holiday",
                "is_working_day", "is_weekend",
            ]
        ].sort_values("calendar_date"),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Use adjacent weekend dates to review potential long-weekend opportunities."
    )
else:
    st.info(
        "No dates flagged as holidays were found in the selected reporting period."
    )


# 5. Unusual months
st.subheader("5. Three Unusual Months to Investigate")
findings = []

low_att = monthly.loc[monthly["attendance_rate_pct"].idxmin()]
high_ot = monthly.loc[monthly["overtime_hours"].idxmax()]
high_late = monthly.loc[monthly["late_arrivals"].idxmax()]

findings.extend([
    {
        "Month": low_att["period_end_date"].strftime("%B %Y"),
        "Signal": "Lowest attendance rate",
        "Observed value": f"{low_att['attendance_rate_pct']:.2f}%",
        "Interpretation": (
            "Lowest rate in the selected period; investigate leave, "
            "absences and calendar effects."
        ),
    },
    {
        "Month": high_ot["period_end_date"].strftime("%B %Y"),
        "Signal": "Highest overtime",
        "Observed value": f"{high_ot['overtime_hours']:.1f} hours",
        "Interpretation": (
            "Highest overtime total; compare staffing and workload "
            "before assigning a cause."
        ),
    },
    {
        "Month": high_late["period_end_date"].strftime("%B %Y"),
        "Signal": "Highest late-arrival count",
        "Observed value": f"{int(high_late['late_arrivals']):,}",
        "Interpretation": (
            "Highest late-arrival count; consider employee count "
            "and department mix."
        ),
    },
])

st.dataframe(
    pd.DataFrame(findings),
    use_container_width=True,
    hide_index=True,
)
st.caption(
    "These are descriptive outliers, not proven causes. A month can appear "
    "more than once if it has multiple extreme metrics."
)


# 6. Department detail
st.subheader("6. Department Detail")
department_monthly = (
    filtered.groupby(
        ["period_end_date", "department_name"], as_index=False
    )
    .agg(
        employees=("employees", "max"),
        attendance_rate_pct=("attendance_rate_pct", "mean"),
        late_arrivals=("late_arrivals", "sum"),
        overtime_hours=("overtime_hours", "sum"),
    )
    .sort_values(["period_end_date", "department_name"])
)

st.dataframe(
    department_monthly.round({
        "attendance_rate_pct": 2,
        "overtime_hours": 1,
    }),
    use_container_width=True,
    hide_index=True,
)


# Review questions
st.subheader("Questions for Review")
st.markdown("""
1. What operational factors contributed to the month with the lowest attendance rate?
2. Which departments account for the highest late-arrival and overtime totals?
3. Are holiday timing and long weekends associated with changes in attendance?
4. Which approved leave types account for the largest number of leave days?
5. Do unusual months reflect operational pressure, calendar effects, or data-quality issues?
""")

st.caption(
    "Data note: attendance rate = (present_days + 0.5 × half_days_unpaid) "
    "/ scheduled_days. Leave includes approved requests only. Holiday flags "
    "are Y/N text values from dw.dim_date. This dashboard is read-only and "
    "does not modify warehouse data."
)
