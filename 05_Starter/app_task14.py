
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------
# PATHS AND PAGE CONFIGURATION
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

ANOMALY_FILE = ROOT / "03_Data" / "csv" / "fact_anomaly.csv"
FORECAST_FILE = ROOT / "03_Data" / "csv" / "fact_forecast.csv"
ACTUAL_FILE = ROOT / "03_Data" / "csv" / "fact_headcount_monthly.csv"

st.set_page_config(
    page_title="Task 14 - AI Signals Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Task 14: AI Signals Dashboard")
st.caption(
    "Anomaly financial exposure, workforce forecasts, "
    "confidence intervals and forecast accuracy"
)

st.info("AI-generated, for human review")


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------

@st.cache_data
def load_data():
    anomalies = pd.read_csv(ANOMALY_FILE)
    forecasts = pd.read_csv(FORECAST_FILE)
    actuals = pd.read_csv(ACTUAL_FILE)

    anomalies["money_at_risk"] = pd.to_numeric(
        anomalies["money_at_risk"], errors="coerce"
    )

    anomalies["anomaly_score"] = pd.to_numeric(
        anomalies["anomaly_score"], errors="coerce"
    )

    forecasts["forecast_month"] = pd.to_datetime(
        forecasts["forecast_month"], errors="coerce"
    )

    actuals["month_start_date"] = pd.to_datetime(
        actuals["month_start_date"], errors="coerce"
    )

    for col in ["forecast_value", "lower_80", "upper_80"]:
        forecasts[col] = pd.to_numeric(
            forecasts[col], errors="coerce"
        )

    for col in ["headcount_start", "headcount_end", "exits"]:
        actuals[col] = pd.to_numeric(
            actuals[col], errors="coerce"
        )

    return anomalies, forecasts, actuals


try:
    anomalies, forecasts, actuals = load_data()
except Exception as exc:
    st.error(f"Unable to load Task 14 datasets: {exc}")
    st.stop()


# ---------------------------------------------------------
# BASIC DATA VALIDATION
# ---------------------------------------------------------

if anomalies.empty or forecasts.empty or actuals.empty:
    st.error("One or more Task 14 datasets are empty.")
    st.stop()

required_anomaly_columns = {
    "reason_code", "money_at_risk", "result_id"
}
required_forecast_columns = {
    "metric", "department_id", "forecast_month",
    "forecast_value", "lower_80", "upper_80"
}
required_actual_columns = {
    "month_start_date", "department_id",
    "headcount_end", "headcount_start", "exits"
}

if not required_anomaly_columns.issubset(anomalies.columns):
    st.error("The anomaly dataset is missing required columns.")
    st.stop()

if not required_forecast_columns.issubset(forecasts.columns):
    st.error("The forecast dataset is missing required columns.")
    st.stop()

if not required_actual_columns.issubset(actuals.columns):
    st.error("The actual dataset is missing required columns.")
    st.stop()


# ---------------------------------------------------------
# TOP-LEVEL METRICS
# ---------------------------------------------------------

total_anomalies = len(anomalies)
quantified_records = anomalies["money_at_risk"].notna().sum()
unquantified_records = anomalies["money_at_risk"].isna().sum()

total_money_at_risk = anomalies["money_at_risk"].sum(
    min_count=1
)

latest_actual_month = actuals["month_start_date"].max()
latest_actual_rows = actuals[
    actuals["month_start_date"] == latest_actual_month
]

latest_actual_headcount = latest_actual_rows[
    "headcount_end"
].sum(min_count=1)

m1, m2, m3, m4 = st.columns(4)

m1.metric("Anomaly records", f"{total_anomalies:,}")
m2.metric("Quantified records", f"{quantified_records:,}")
m3.metric(
    "Money at risk",
    f"{total_money_at_risk:,.2f}"
)
m4.metric(
    "Latest actual headcount",
    f"{latest_actual_headcount:,.0f}"
)

st.caption(
    f"Latest actual month: {latest_actual_month:%B %Y} | "
    f"{unquantified_records:,} anomaly records have no "
    "quantified financial impact."
)


# ---------------------------------------------------------
# SECTION 1: ANOMALY ANALYSIS
# ---------------------------------------------------------

st.divider()
st.header("1. Anomaly Analysis")
st.write(
    "This section ranks anomaly categories by their total "
    "quantified financial exposure. Categories without a "
    "financial impact value are shown as Not quantified."
)

anomaly_summary = (
    anomalies.groupby("reason_code", dropna=False)
    .agg(
        record_count=("result_id", "count"),
        quantified_count=("money_at_risk", "count"),
        money_at_risk=(
            "money_at_risk",
            lambda values: values.sum(min_count=1)
        )
    )
    .reset_index()
)

anomaly_summary["reason_code"] = (
    anomaly_summary["reason_code"]
    .fillna("Unknown")
)

anomaly_summary = anomaly_summary.sort_values(
    "money_at_risk",
    ascending=False,
    na_position="last"
)

quantified_summary = anomaly_summary[
    anomaly_summary["money_at_risk"].notna()
].copy()

unquantified_summary = anomaly_summary[
    anomaly_summary["money_at_risk"].isna()
].copy()

left, right = st.columns([1.5, 1])

with left:
    st.subheader("Money at risk by anomaly type")

    fig_anomaly = go.Figure()

    fig_anomaly.add_trace(
        go.Bar(
            x=quantified_summary["money_at_risk"],
            y=quantified_summary["reason_code"],
            orientation="h",
            text=quantified_summary["money_at_risk"].map(
                lambda value: f"{value:,.0f}"
            ),
            textposition="auto",
            name="Quantified money at risk"
        )
    )

    fig_anomaly.update_layout(
        height=480,
        xaxis_title="Money at risk",
        yaxis_title="Anomaly type",
        yaxis={"categoryorder": "total ascending"},
        showlegend=False
    )

    st.plotly_chart(fig_anomaly, use_container_width=True)

with right:
    st.subheader("Anomaly interpretation")

    st.write(
        f"**{total_anomalies:,}** anomaly records were identified."
    )

    st.write(
        f"**{total_money_at_risk:,.2f}** is the total "
        "financial exposure quantified in the source data."
    )

    st.write(
        f"**{unquantified_records:,}** records do not have "
        "a financial impact value."
    )

    st.write(
        "The highest quantified exposure category is "
        f"**{quantified_summary.iloc[0]['reason_code']}**."
        if not quantified_summary.empty
        else "No quantified anomaly exposure is available."
    )

st.subheader("Anomaly category details")

display_anomalies = anomaly_summary.copy()

display_anomalies["money_at_risk"] = (
    display_anomalies["money_at_risk"]
    .apply(
        lambda value: (
            f"{value:,.2f}"
            if pd.notna(value)
            else "Not quantified"
        )
    )
)

st.dataframe(
    display_anomalies,
    use_container_width=True,
    hide_index=True
)

st.caption("AI-generated, for human review")


# ---------------------------------------------------------
# SECTION 2: HEADCOUNT ACTUAL VS FORECAST
# ---------------------------------------------------------

st.divider()
st.header("2. Headcount: Actual vs Forecast")

st.write(
    "Historical actual headcount is compared with future "
    "forecast values. The shaded region represents the "
    "80% forecast confidence interval."
)

headcount_forecast = forecasts[
    forecasts["metric"] == "headcount_end"
].copy()

forecast_departments = sorted(
    headcount_forecast["department_id"].dropna().unique()
)

selected_department = st.selectbox(
    "Select department for headcount forecast",
    forecast_departments,
    index=forecast_departments.index("ALL")
    if "ALL" in forecast_departments else 0
)

selected_forecast = headcount_forecast[
    headcount_forecast["department_id"] == selected_department
].copy()

if selected_department == "ALL":
    actual_headcount = (
        actuals.groupby("month_start_date", as_index=False)
        .agg(
            actual_value=(
                "headcount_end",
                lambda values: values.sum(min_count=1)
            )
        )
    )
else:
    actual_headcount = (
        actuals[
            actuals["department_id"] == selected_department
        ][["month_start_date", "headcount_end"]]
        .rename(columns={"headcount_end": "actual_value"})
        .copy()
    )

actual_headcount = actual_headcount.dropna(
    subset=["month_start_date", "actual_value"]
).sort_values("month_start_date")

selected_forecast = selected_forecast.dropna(
    subset=["forecast_month", "forecast_value", "lower_80", "upper_80"]
).sort_values("forecast_month")

fig_headcount = go.Figure()

fig_headcount.add_trace(
    go.Scatter(
        x=actual_headcount["month_start_date"],
        y=actual_headcount["actual_value"],
        mode="lines",
        name="Actual headcount",
        line={"width": 2}
    )
)

fig_headcount.add_trace(
    go.Scatter(
        x=selected_forecast["forecast_month"],
        y=selected_forecast["upper_80"],
        mode="lines",
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip"
    )
)

fig_headcount.add_trace(
    go.Scatter(
        x=selected_forecast["forecast_month"],
        y=selected_forecast["lower_80"],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        name="80% confidence interval",
        hoverinfo="skip"
    )
)

fig_headcount.add_trace(
    go.Scatter(
        x=selected_forecast["forecast_month"],
        y=selected_forecast["forecast_value"],
        mode="lines+markers",
        name="Forecast headcount",
        line={"dash": "dash", "width": 2}
    )
)

fig_headcount.update_layout(
    height=480,
    xaxis_title="Month",
    yaxis_title="Headcount",
    hovermode="x unified"
)

st.plotly_chart(fig_headcount, use_container_width=True)

if selected_department == "ALL":
    latest_baseline = latest_actual_headcount
else:
    baseline_rows = actuals[
        (actuals["department_id"] == selected_department)
        & (actuals["month_start_date"] == latest_actual_month)
    ]
    latest_baseline = baseline_rows["headcount_end"].sum(
        min_count=1
    )

first_forecast = selected_forecast.iloc[0]

if pd.notna(latest_baseline):
    change = first_forecast["forecast_value"] - latest_baseline
    change_pct = (
        change / latest_baseline * 100
        if latest_baseline != 0 else float("nan")
    )

    st.write(
        f"**Plain-English explanation:** The latest available "
        f"actual headcount for {selected_department} is "
        f"{latest_baseline:,.1f}. The first forecast is "
        f"{first_forecast['forecast_value']:,.1f} for "
        f"{first_forecast['forecast_month']:%B %Y}, a change "
        f"of {change:,.1f} ({change_pct:.2f}%)."
    )

    if change < 0:
        st.warning(
            "The first forecast is below the latest actual "
            "headcount. Review the forecast baseline and "
            "assumptions before making workforce decisions."
        )
    elif change > 0:
        st.info(
            "The first forecast is above the latest actual "
            "headcount. Review expected hiring and workforce "
            "movement before making decisions."
        )
else:
    st.write(
        "A comparable latest actual headcount is unavailable "
        "for this department."
    )

st.caption("AI-generated, for human review")


# ---------------------------------------------------------
# SECTION 3: ATTRITION ACTUAL VS FORECAST
# ---------------------------------------------------------

st.divider()
st.header("3. Attrition: Actual vs Forecast")

st.write(
    "Historical organization-wide attrition is calculated "
    "using total exits divided by total starting headcount. "
    "Future values come from the supplied attrition forecast."
)

attrition_actual = (
    actuals.groupby("month_start_date", as_index=False)
    .agg(
        total_exits=("exits", "sum"),
        total_starting_headcount=(
            "headcount_start",
            "sum"
        )
    )
)

attrition_actual["actual_attrition_pct"] = (
    attrition_actual["total_exits"]
    / attrition_actual["total_starting_headcount"]
    * 100
)

attrition_actual.loc[
    attrition_actual["total_starting_headcount"] == 0,
    "actual_attrition_pct"
] = None

attrition_forecast = forecasts[
    (forecasts["metric"] == "attrition_rate_monthly_pct")
    & (forecasts["department_id"] == "ALL")
].copy()

attrition_forecast = attrition_forecast.dropna(
    subset=["forecast_month", "forecast_value", "lower_80", "upper_80"]
).sort_values("forecast_month")

fig_attrition = go.Figure()

fig_attrition.add_trace(
    go.Scatter(
        x=attrition_actual["month_start_date"],
        y=attrition_actual["actual_attrition_pct"],
        mode="lines",
        name="Actual attrition rate"
    )
)

fig_attrition.add_trace(
    go.Scatter(
        x=attrition_forecast["forecast_month"],
        y=attrition_forecast["upper_80"],
        mode="lines",
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip"
    )
)

fig_attrition.add_trace(
    go.Scatter(
        x=attrition_forecast["forecast_month"],
        y=attrition_forecast["lower_80"],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        name="80% confidence interval",
        hoverinfo="skip"
    )
)

fig_attrition.add_trace(
    go.Scatter(
        x=attrition_forecast["forecast_month"],
        y=attrition_forecast["forecast_value"],
        mode="lines+markers",
        name="Forecast attrition rate",
        line={"dash": "dash"}
    )
)

fig_attrition.update_layout(
    height=450,
    xaxis_title="Month",
    yaxis_title="Attrition rate (%)",
    hovermode="x unified"
)

st.plotly_chart(fig_attrition, use_container_width=True)

if not attrition_forecast.empty:
    first_attrition = attrition_forecast.iloc[0]

    st.write(
        f"**Plain-English explanation:** The first available "
        f"organization-wide attrition forecast is "
        f"{first_attrition['forecast_value']:.2f}% for "
        f"{first_attrition['forecast_month']:%B %Y}. "
        "The shaded area represents its 80% confidence interval."
    )

st.caption("AI-generated, for human review")


# ---------------------------------------------------------
# SECTION 4: FORECAST ACCURACY
# ---------------------------------------------------------

st.divider()
st.header("4. Forecast Accuracy")

st.write(
    "Forecast error is calculated only when an actual value "
    "exists for the same forecast month and metric. Future "
    "months without actual data are marked as Awaiting actuals."
)

accuracy_rows = []

for _, row in forecasts.iterrows():
    metric = row["metric"]
    forecast_month = row["forecast_month"]
    actual_value = None

    if pd.isna(forecast_month):
        continue

    if metric == "headcount_end":
        matching_actuals = actuals[
            actuals["month_start_date"] == forecast_month
        ]

        if row["department_id"] == "ALL":
            if not matching_actuals.empty:
                actual_value = matching_actuals[
                    "headcount_end"
                ].sum(min_count=1)
        else:
            matching_actuals = matching_actuals[
                matching_actuals["department_id"]
                == row["department_id"]
            ]

            if not matching_actuals.empty:
                actual_value = matching_actuals[
                    "headcount_end"
                ].sum(min_count=1)

    elif metric == "attrition_rate_monthly_pct":
        matching_actuals = attrition_actual[
            attrition_actual["month_start_date"] == forecast_month
        ]

        if not matching_actuals.empty:
            actual_value = matching_actuals[
                "actual_attrition_pct"
            ].iloc[0]

    forecast_value = row["forecast_value"]

    if pd.notna(actual_value) and pd.notna(forecast_value):
        error = actual_value - forecast_value
        absolute_error = abs(error)

        if forecast_value != 0:
            absolute_percentage_error = (
                absolute_error / abs(forecast_value) * 100
            )
        else:
            absolute_percentage_error = None

        status = "Actual available"
    else:
        error = None
        absolute_error = None
        absolute_percentage_error = None
        status = "Awaiting actuals"

    accuracy_rows.append({
        "Metric": metric,
        "Department": row["department_id"],
        "Forecast month": forecast_month.strftime("%Y-%m"),
        "Forecast value": forecast_value,
        "Actual value": actual_value,
        "Error (Actual - Forecast)": error,
        "Absolute error": absolute_error,
        "Absolute percentage error (%)": absolute_percentage_error,
        "Status": status
    })

accuracy_table = pd.DataFrame(accuracy_rows)

if not accuracy_table.empty:
    st.dataframe(
        accuracy_table,
        use_container_width=True,
        hide_index=True
    )

    available_count = (
        accuracy_table["Status"] == "Actual available"
    ).sum()

    awaiting_count = (
        accuracy_table["Status"] == "Awaiting actuals"
    ).sum()

    c1, c2 = st.columns(2)
    c1.metric("Forecasts with actuals", int(available_count))
    c2.metric("Forecasts awaiting actuals", int(awaiting_count))

    if available_count == 0:
        st.info(
            "No forecast months currently overlap with the "
            "available actual data. Forecast accuracy cannot "
            "yet be calculated without inventing actual values."
        )

    st.download_button(
        label="Download forecast accuracy table (CSV)",
        data=accuracy_table.to_csv(index=False).encode("utf-8"),
        file_name="Task14_Forecast_Accuracy.csv",
        mime="text/csv"
    )


# ---------------------------------------------------------
# SECTION 5: DATA NOTES AND TRANSPARENCY
# ---------------------------------------------------------

st.divider()
st.header("5. Data Notes and AI Transparency")

st.markdown(
    """
    - Anomaly financial exposure uses only populated
      `money_at_risk` values.
    - Missing financial impact is displayed as
      **Not quantified**, not zero.
    - Actual headcount data is available through September 2026.
    - Forecast data covers October 2026 through March 2027.
    - Forecast accuracy is calculated only when matching
      actual values are available.
    - The forecast confidence band represents the supplied
      lower and upper 80% bounds.
    - Forecast outputs and anomaly flags require human review
      before operational or financial decisions.
    """
)

st.info("AI-generated, for human review")

st.caption(
    "Task 14 - AI Signals Dashboard | "
    "Source: PulseIQ project CSV datasets"
)
