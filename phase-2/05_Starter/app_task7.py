
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PulseIQ | Task 7 Attrition Analytics",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "03_Data" / "csv"

st.title("Task 7 — Attrition Analytics")
st.caption(
    "Historical exits describe recorded outcomes. Predicted attrition risk "
    "is a model estimate, not a certain future event."
)


@st.cache_data
def load_csv(filename):
    path = CSV_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    return pd.read_csv(path)


try:
    employees = load_csv("dim_employee.csv")
    headcount = load_csv("fact_headcount_monthly.csv")
    risk = load_csv("fact_attrition_risk.csv")
    departments = load_csv("dim_department.csv")
except Exception as exc:
    st.error(f"Could not load Task 7 data: {exc}")
    st.stop()


# Convert date columns safely.
employees["hire_date"] = pd.to_datetime(
    employees["hire_date"], errors="coerce"
)
employees["exit_date"] = pd.to_datetime(
    employees["exit_date"], errors="coerce"
)
headcount["month_start_date"] = pd.to_datetime(
    headcount["month_start_date"], errors="coerce"
)
risk["as_of_date"] = pd.to_datetime(risk["as_of_date"], errors="coerce")

# Use one current employee dimension row per employee for exit analysis.
if "is_current" in employees.columns:
    current_mask = (
        employees["is_current"].astype(str).str.upper().eq("Y")
    )
    current_employees = employees.loc[current_mask].copy()
else:
    current_employees = employees.copy()

current_employees = current_employees.drop_duplicates(
    subset=["employee_id"], keep="last"
)

department_map = departments.set_index("department_id")[
    "department_name"
].to_dict()

headcount["department_name"] = headcount["department_id"].map(
    department_map
).fillna(headcount["department_id"])

current_employees["department_name"] = (
    current_employees["department_id"].map(department_map)
    .fillna(current_employees["department_id"])
)

risk["department_name"] = risk["department_id"].map(
    department_map
).fillna(risk["department_id"])

# Exclude leadership department from group-level risk views.
# This dashboard does not show individual employee risk records.
eligible_departments = departments.loc[
    ~departments["is_leadership"].astype(str).str.upper().eq("Y"),
    "department_id",
].tolist()

headcount_view = headcount[
    headcount["department_id"].isin(eligible_departments)
].copy()

employee_view = current_employees[
    current_employees["department_id"].isin(eligible_departments)
].copy()

risk_view = risk[risk["department_id"].isin(eligible_departments)].copy()

st.sidebar.header("Filters")

if headcount_view["month_start_date"].notna().any():
    min_month = headcount_view["month_start_date"].min().date()
    max_month = headcount_view["month_start_date"].max().date()
    start_month, end_month = st.sidebar.date_input(
        "Reporting period",
        value=(min_month, max_month),
        min_value=min_month,
        max_value=max_month,
    )
    if not isinstance(start_month, type(end_month)):
        start_month, end_month = min_month, max_month
    headcount_view = headcount_view[
        headcount_view["month_start_date"].dt.date.between(
            start_month, end_month
        )
    ]

department_options = sorted(
    headcount_view["department_name"].dropna().unique().tolist()
)
selected_departments = st.sidebar.multiselect(
    "Departments",
    options=department_options,
    default=department_options,
)
if selected_departments:
    headcount_view = headcount_view[
        headcount_view["department_name"].isin(selected_departments)
    ]
    employee_view = employee_view[
        employee_view["department_name"].isin(selected_departments)
    ]
    risk_view = risk_view[
        risk_view["department_name"].isin(selected_departments)
    ]
else:
    headcount_view = headcount_view.iloc[0:0]
    employee_view = employee_view.iloc[0:0]
    risk_view = risk_view.iloc[0:0]

# Use the latest available prediction snapshot for risk summaries.
if not risk_view.empty and risk_view["as_of_date"].notna().any():
    latest_risk_date = risk_view["as_of_date"].max()
    latest_risk = risk_view[risk_view["as_of_date"].eq(latest_risk_date)].copy()
else:
    latest_risk_date = None
    latest_risk = risk_view.copy()

# Historical outcomes.
monthly = (
    headcount_view.groupby("month_start_date", as_index=False)
    .agg(
        exits=("exits", "sum"),
        voluntary_exits=("voluntary_exits", "sum"),
        headcount_start=("headcount_start", "sum"),
        headcount_end=("headcount_end", "sum"),
    )
    .sort_values("month_start_date")
)

total_exits = int(headcount_view["exits"].sum()) if not headcount_view.empty else 0
total_voluntary = (
    int(headcount_view["voluntary_exits"].sum())
    if not headcount_view.empty else 0
)
latest_headcount = (
    int(monthly.iloc[-1]["headcount_end"])
    if not monthly.empty else 0
)
voluntary_share = (
    total_voluntary / total_exits * 100 if total_exits else 0
)

# Tenure at recorded exit, using one current row per employee.
exited = employee_view[
    employee_view["exit_date"].notna()
    & employee_view["hire_date"].notna()
    & employee_view["exit_date"].ge(employee_view["hire_date"])
].copy()
exited["tenure_years"] = (
    (exited["exit_date"] - exited["hire_date"]).dt.days / 365.25
)

st.header("Historical attrition — recorded outcomes")
st.caption(
    "These figures describe recorded exits in the selected monthly headcount data."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Recorded exits", f"{total_exits:,}")
c2.metric("Voluntary exits", f"{total_voluntary:,}")
c3.metric("Voluntary share of exits", f"{voluntary_share:.1f}%")
c4.metric("Latest ending headcount", f"{latest_headcount:,}")

left, right = st.columns(2)

with left:
    st.subheader("Exits by month")
    if monthly.empty:
        st.info("No monthly records for the selected filters.")
    else:
        st.line_chart(
            monthly.set_index("month_start_date")[["exits"]]
        )

with right:
    st.subheader("Exits by department")
    if headcount_view.empty:
        st.info("No department records for the selected filters.")
    else:
        by_department = (
            headcount_view.groupby("department_name", as_index=False)
            .agg(
                exits=("exits", "sum"),
                voluntary_exits=("voluntary_exits", "sum"),
            )
            .sort_values("exits", ascending=False)
            .set_index("department_name")
        )
        st.bar_chart(by_department[["exits"]])

left, right = st.columns(2)

with left:
    st.subheader("Voluntary vs. other exits")
    if headcount_view.empty:
        st.info("No exit records available.")
    else:
        exit_mix = pd.DataFrame(
            {
                "Exit type": ["Voluntary exits", "Other exits"],
                "Count": [
                    total_voluntary,
                    max(total_exits - total_voluntary, 0),
                ],
            }
        ).set_index("Exit type")
        st.bar_chart(exit_mix)

with right:
    st.subheader("Tenure at exit")
    if exited.empty:
        st.info("No valid hire and exit dates are available.")
    else:
        tenure_bins = pd.cut(
            exited["tenure_years"],
            bins=[0, 1, 3, 5, 10, float("inf")],
            labels=["Under 1 year", "1–3 years", "3–5 years", "5–10 years", "10+ years"],
            include_lowest=True,
        )
        tenure_counts = (
            tenure_bins.value_counts(sort=False)
            .rename_axis("Tenure at exit")
            .to_frame("Employees")
        )
        st.bar_chart(tenure_counts)

st.subheader("Monthly exit detail")
if monthly.empty:
    st.info("No monthly exit data available.")
else:
    st.dataframe(monthly, use_container_width=True, hide_index=True)

st.divider()

# Predicted risk is intentionally separated from historical outcomes.
st.header("Predicted attrition risk — not certain")
st.warning(
    "Risk scores are estimates from a baseline model. They do not establish "
    "that an employee will leave, and must not be used alone for employment decisions."
)

if latest_risk_date is not None:
    st.caption(f"Prediction snapshot: {latest_risk_date.date()}")

if latest_risk.empty:
    st.info("No risk records available for the selected departments.")
else:
    # Minimum group size of 5 before showing group-level risk.
    MIN_GROUP_SIZE = 5
    risk_group = (
        latest_risk.groupby("department_name", as_index=False)
        .agg(
            group_size=("prediction_id", "count"),
            high_risk_count=("risk_band", lambda s: s.astype(str).str.lower().eq("high").sum()),
            medium_risk_count=("risk_band", lambda s: s.astype(str).str.lower().eq("medium").sum()),
            average_risk_score=("risk_score_12m", "mean"),
        )
    )
    risk_group["high_risk_pct"] = (
        risk_group["high_risk_count"] / risk_group["group_size"] * 100
    )
    risk_group["medium_risk_pct"] = (
        risk_group["medium_risk_count"] / risk_group["group_size"] * 100
    )
    suppressed = risk_group["group_size"] < MIN_GROUP_SIZE
    display_risk = risk_group.loc[~suppressed].copy()

    st.caption(
        f"Groups with fewer than {MIN_GROUP_SIZE} predictions are suppressed "
        "to reduce disclosure risk."
    )

    if display_risk.empty:
        st.info("No department groups meet the minimum group-size requirement.")
    else:
        risk_left, risk_right = st.columns(2)
        with risk_left:
            st.subheader("Average predicted risk by department")
            st.bar_chart(
                display_risk.set_index("department_name")[["average_risk_score"]]
            )
        with risk_right:
            st.subheader("Predicted risk bands by department")
            st.bar_chart(
                display_risk.set_index("department_name")[
                    ["high_risk_count", "medium_risk_count"]
                ]
            )

        st.subheader("Department-level risk summary")
        st.dataframe(
            display_risk[
                [
                    "department_name",
                    "group_size",
                    "high_risk_count",
                    "medium_risk_count",
                    "average_risk_score",
                    "high_risk_pct",
                    "medium_risk_pct",
                ]
            ].round(3),
            use_container_width=True,
            hide_index=True,
        )

# Three biggest findings based on the filtered data.
st.divider()
st.header("Three biggest findings")

findings = []

if not monthly.empty:
    highest_month = monthly.loc[monthly["exits"].idxmax()]
    findings.append(
        f"Highest recorded exits: {int(highest_month['exits'])} in "
        f"{highest_month['month_start_date'].strftime('%B %Y')}."
    )
    if monthly["exits"].sum() > 0:
        findings.append(
            f"Recorded exits in the selected period: {int(monthly['exits'].sum())}."
        )

if not headcount_view.empty:
    dept_totals = (
        headcount_view.groupby("department_name")["exits"]
        .sum()
        .sort_values(ascending=False)
    )
    if not dept_totals.empty:
        findings.append(
            f"Department with the most recorded exits: {dept_totals.index[0]} "
            f"({int(dept_totals.iloc[0])} exits)."
        )

if not exited.empty:
    median_tenure = exited["tenure_years"].median()
    findings.append(
        f"Median recorded tenure at exit: {median_tenure:.1f} years "
        f"across {len(exited):,} employee records with valid dates."
    )

if latest_risk_date is not None and not latest_risk.empty:
    findings.append(
        "Predicted risk is shown separately from actual exits and should be "
        "interpreted as a model estimate, not a confirmed outcome."
    )

if findings:
    for number, finding in enumerate(findings[:3], start=1):
        st.markdown(f"**{number}.** {finding}")
else:
    st.info("Not enough data is available to produce findings for these filters.")

st.caption(
    "Data sources: dim_employee.csv, fact_headcount_monthly.csv, "
    "fact_attrition_risk.csv, and dim_department.csv."
)
