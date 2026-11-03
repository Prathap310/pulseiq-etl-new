
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "Reports" / "Task13" / "task13_department_month.csv"

st.set_page_config(
    page_title="Task 13 - Cross-Department Impact",
    page_icon="📊",
    layout="wide"
)

st.title("Task 13: Cross-Department Impact View")
st.caption("Department-level monthly comparison of payroll cost and attrition")


@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE, parse_dates=["month_start_date"])


df = load_data()

if df.empty:
    st.error("Task 13 dataset is empty.")
    st.stop()

departments = sorted(df["department_name"].dropna().unique())

selected_departments = st.multiselect(
    "Select departments",
    departments,
    default=departments
)

filtered = df[df["department_name"].isin(selected_departments)].copy()

if filtered.empty:
    st.warning("Select at least one department.")
    st.stop()

summary = (
    filtered.groupby(
        ["department_id", "department_name"],
        as_index=False
    )
    .agg(
        total_employer_cost=(
            "employer_cost",
            lambda values: values.sum(min_count=1)
        ),
        average_monthly_attrition=(
            "attrition_rate_monthly_pct",
            "mean"
        ),
        attrition_months_available=(
            "attrition_rate_monthly_pct",
            "count"
        ),
        months_available=("month_start_date", "nunique"),
        suppressed_months=("is_suppressed", "sum")
    )
)

st.subheader("Department comparison")

# Exclude departments whose employer cost is fully suppressed.
chart_summary = summary[
    summary["total_employer_cost"].notna()
].copy()

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=chart_summary["department_name"],
        y=chart_summary["total_employer_cost"],
        name="Total employer cost (INR)",
        yaxis="y"
    )
)

fig.add_trace(
    go.Scatter(
        x=chart_summary["department_name"],
        y=chart_summary["average_monthly_attrition"],
        name="Average monthly attrition (%)",
        mode="lines+markers",
        yaxis="y2"
    )
)

fig.update_layout(
    xaxis_title="Department",
    yaxis=dict(
        title="Total employer cost (INR)",
        tickformat=",.0f"
    ),
    yaxis2=dict(
        title="Average monthly attrition (%)",
        overlaying="y",
        side="right"
    ),
    legend=dict(orientation="h", y=1.12),
    height=550,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Department summary")

display_summary = summary.copy()

display_summary["total_employer_cost"] = (
    display_summary["total_employer_cost"].round(2)
)

display_summary["average_monthly_attrition"] = (
    display_summary["average_monthly_attrition"].round(2)
)

st.dataframe(display_summary, use_container_width=True)

st.subheader("Monthly department data")
st.dataframe(filtered, use_container_width=True)

st.download_button(
    "Download department comparison CSV",
    data=summary.to_csv(index=False).encode("utf-8"),
    file_name="task13_department_comparison.csv",
    mime="text/csv"
)

st.info(
    "Suppressed department metrics are retained as missing values, "
    "not displayed as zero. D00 has fewer than five employees. "
    "Attrition follows the M04 minimum group size of 10. "
    "D10 has fewer eligible months."
)
