
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PulseIQ | Task 9 Payroll Cost",
    page_icon="💰",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "03_Data" / "csv"
REPORT_DIR = ROOT / "Reports"
MIN_GROUP_SIZE = 5

DUPLICATE_IDS = {"PI-X0001", "PI-X0002"}
REVENUE_ACCOUNTS = {"4001", "4002", "4003", "4004"}
PAYROLL_ACCOUNTS = {"5001", "5002", "5003", "5004", "5005"}

st.title("Task 9 — Payroll Cost & Reconciliation")
st.caption(
    "Payroll analytics, budget variance, and payroll-to-ledger reconciliation. "
    "Two confirmed duplicate rows are excluded from analytical totals. "
    "Unresolved exceptions remain visible."
)

with st.expander("Metric definitions and privacy rules", expanded=False):
    st.markdown(
        """
        - **M07 Gross pay:** sum of gross pay.
        - **M08 Net pay:** sum of take-home pay after employee deductions.
        - **M09 Employer cost:** sum of employer cost.
        - **M10 Cost per head:** employer cost divided by distinct employees
          within each department-month.
        - **M11 Overtime share:** overtime pay / employer cost × 100.
        - **M12 Variable pay share:** variable pay / gross pay × 100.
        - **M15 LOP days:** sum of leave-without-pay days.
        - **M19 Payroll as % of revenue:** monthly employer cost / operating
          revenue from ledger accounts 4001–4004 × 100.
        - **Privacy:** suppress department-month metrics and employee counts
          when fewer than 5 distinct employees qualify.
        - **Reconciliation:** compare payroll employer cost against ledger
          expense accounts 5001–5005. Differences are not silently adjusted.
        - **Budget variance:** actual employer cost minus budget. This is not
          the same as payroll-to-ledger reconciliation.
        """
    )


@st.cache_data
def load_csv(path_string):
    path = Path(path_string)
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def money(value):
    if pd.isna(value):
        return "Suppressed"
    return f"₹{value:,.2f}"


def number(value, decimals=2):
    if pd.isna(value):
        return "Suppressed"
    return f"{value:,.{decimals}f}"


def pct(value):
    if pd.isna(value):
        return "Suppressed"
    return f"{value:,.2f}%"


def format_columns(df, currency_columns=(), percentage_columns=(), number_columns=()):
    """Create display-only formatting without changing exported numeric data."""
    result = df.copy()

    for column in currency_columns:
        if column in result.columns:
            result[column] = result[column].map(money)

    for column in percentage_columns:
        if column in result.columns:
            result[column] = result[column].map(pct)

    for column in number_columns:
        if column in result.columns:
            result[column] = result[column].map(number)

    return result


def suppress_small_groups(df, count_column="employee_count"):
    """Suppress department-month metrics when fewer than five employees qualify."""
    result = df.copy()
    small = result[count_column].fillna(0).lt(MIN_GROUP_SIZE)

    metric_columns = [
        "gross_pay",
        "net_pay",
        "employer_cost",
        "cost_per_head",
        "overtime_share",
        "variable_pay_share",
        "lop_days",
    ]

    for column in metric_columns:
        if column in result.columns:
            result.loc[small, column] = float("nan")

    result["privacy_status"] = "Visible"
    result.loc[small, "privacy_status"] = "Suppressed (<5 employees)"
    return result


# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------
try:
    payroll = load_csv(str(CSV_DIR / "fact_payroll.csv"))
    departments = load_csv(str(CSV_DIR / "dim_department.csv"))
    ledger = load_csv(str(CSV_DIR / "fact_ledger.csv"))

    budget = load_csv(
        str(REPORT_DIR / "Task9_Payroll_Budget_Reconciliation_Corrected.csv")
    )
    reconciliation = load_csv(
        str(REPORT_DIR / "Task9_Payroll_Ledger_Reconciliation.csv")
    )
    excluded_evidence = load_csv(
        str(REPORT_DIR / "Task9_Payroll_Excluded_Row_Evidence.csv")
    )
except Exception as exc:
    st.error(f"Could not load Task 9 data: {exc}")
    st.stop()


# ---------------------------------------------------------------------
# Validate input columns
# ---------------------------------------------------------------------
required_payroll = {
    "payroll_item_id", "employee_id", "period_end_date", "department_id",
    "gross_pay", "net_pay", "employer_cost", "overtime_pay",
    "variable_pay", "lop_days",
}
missing = required_payroll - set(payroll.columns)
if missing:
    st.error(f"Missing payroll columns: {', '.join(sorted(missing))}")
    st.stop()

required_ledger = {
    "entry_date", "account_code", "debit", "credit",
    "source_type", "cost_center_department_id",
}
missing = required_ledger - set(ledger.columns)
if missing:
    st.error(f"Missing ledger columns: {', '.join(sorted(missing))}")
    st.stop()


# ---------------------------------------------------------------------
# Prepare payroll and exclude only confirmed duplicates
# ---------------------------------------------------------------------
payroll["period_end_date"] = pd.to_datetime(
    payroll["period_end_date"], errors="coerce"
)
payroll["month"] = (
    payroll["period_end_date"].dt.to_period("M").dt.to_timestamp()
)
payroll["department_id"] = payroll["department_id"].astype(str)

numeric_columns = [
    "gross_pay", "net_pay", "employer_cost", "overtime_pay",
    "variable_pay", "lop_days",
]
for column in numeric_columns:
    payroll[column] = pd.to_numeric(
        payroll[column], errors="coerce"
    ).fillna(0)

payroll["is_confirmed_duplicate"] = payroll["payroll_item_id"].isin(
    DUPLICATE_IDS
)

clean_payroll = payroll[
    ~payroll["is_confirmed_duplicate"]
].copy()

department_map = departments.set_index("department_id")[
    "department_name"
].to_dict()

clean_payroll["department_name"] = (
    clean_payroll["department_id"].map(department_map)
    .fillna(clean_payroll["department_id"])
)


# ---------------------------------------------------------------------
# Aggregate at department-month grain
# ---------------------------------------------------------------------
monthly = (
    clean_payroll.groupby(
        ["department_id", "department_name", "month"], as_index=False
    )
    .agg(
        gross_pay=("gross_pay", "sum"),
        net_pay=("net_pay", "sum"),
        employer_cost=("employer_cost", "sum"),
        overtime_pay=("overtime_pay", "sum"),
        variable_pay=("variable_pay", "sum"),
        lop_days=("lop_days", "sum"),
        employee_count=("employee_id", "nunique"),
        payroll_rows=("payroll_item_id", "count"),
    )
)

monthly["cost_per_head"] = (
    monthly["employer_cost"]
    / monthly["employee_count"].replace(0, float("nan"))
)

monthly["overtime_share"] = (
    monthly["overtime_pay"]
    / monthly["employer_cost"].replace(0, float("nan"))
    * 100
)

monthly["variable_pay_share"] = (
    monthly["variable_pay"]
    / monthly["gross_pay"].replace(0, float("nan"))
    * 100
)

monthly = suppress_small_groups(monthly)


# ---------------------------------------------------------------------
# Prepare ledger and operating revenue
# ---------------------------------------------------------------------
ledger["entry_date"] = pd.to_datetime(
    ledger["entry_date"], errors="coerce"
)
ledger["month"] = (
    ledger["entry_date"].dt.to_period("M").dt.to_timestamp()
)
ledger["account_code"] = ledger["account_code"].astype(str)

for column in ["debit", "credit"]:
    ledger[column] = pd.to_numeric(
        ledger[column], errors="coerce"
    ).fillna(0)

revenue_ledger = ledger[
    ledger["account_code"].isin(REVENUE_ACCOUNTS)
    & ledger["source_type"].eq("INVOICE")
].copy()

revenue_ledger["operating_revenue"] = (
    revenue_ledger["credit"] - revenue_ledger["debit"]
)

monthly_revenue = (
    revenue_ledger.groupby("month", as_index=False)["operating_revenue"]
    .sum()
)

monthly_payroll = (
    clean_payroll.groupby("month", as_index=False)["employer_cost"]
    .sum()
    .rename(columns={"employer_cost": "payroll_employer_cost"})
)

revenue_ratio = monthly_payroll.merge(
    monthly_revenue, on="month", how="outer"
).sort_values("month")

revenue_ratio["payroll_as_pct_revenue"] = (
    revenue_ratio["payroll_employer_cost"]
    / revenue_ratio["operating_revenue"].replace(0, float("nan"))
    * 100
)


# ---------------------------------------------------------------------
# Prepare reconciliation and budget
# ---------------------------------------------------------------------
reconciliation["department_id"] = reconciliation["department_id"].astype(str)
reconciliation["month"] = pd.to_datetime(
    reconciliation["month"], errors="coerce"
)
reconciliation["department_name"] = (
    reconciliation["department_id"].map(department_map)
    .fillna(reconciliation["department_id"])
)

budget["department_id"] = budget["department_id"].astype(str)
budget["month"] = pd.to_datetime(budget["month"], errors="coerce")
budget["department_name"] = (
    budget["department_id"].map(department_map)
    .fillna(budget["department_id"])
)


# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
st.sidebar.header("Filters")

department_options = sorted(
    monthly["department_name"].dropna().unique().tolist()
)

selected_departments = st.sidebar.multiselect(
    "Department",
    department_options,
    default=department_options,
)

month_values = sorted(monthly["month"].dropna().unique())
month_labels = [
    pd.Timestamp(value).strftime("%Y-%m")
    for value in month_values
]

selected_month_labels = st.sidebar.multiselect(
    "Payroll month",
    month_labels,
    default=month_labels,
)

selected_months = [
    pd.Timestamp(label + "-01")
    for label in selected_month_labels
]

filtered = monthly[
    monthly["department_name"].isin(selected_departments)
    & monthly["month"].isin(selected_months)
].copy()

filtered_reconciliation = reconciliation[
    reconciliation["department_name"].isin(selected_departments)
    & reconciliation["month"].isin(selected_months)
].copy()

filtered_budget = budget[
    budget["department_name"].isin(selected_departments)
    & budget["month"].isin(selected_months)
].copy()


# ---------------------------------------------------------------------
# KPI cards
# KPI sums only include groups meeting the privacy threshold.
# Cost per head is a weighted employee-month average across visible groups.
# ---------------------------------------------------------------------
st.header("Payroll overview")

visible = filtered[
    filtered["employee_count"].ge(MIN_GROUP_SIZE)
].copy()

if visible.empty:
    st.warning(
        "No department-month groups meet the minimum sample size of "
        f"{MIN_GROUP_SIZE} employees for the selected filters. "
        "Select additional departments or months."
    )
    st.stop()

total_gross = visible["gross_pay"].sum()
total_net = visible["net_pay"].sum()
total_employer_cost = visible["employer_cost"].sum()
total_employee_months = visible["employee_count"].sum()

cost_per_head = (
    total_employer_cost / total_employee_months
    if total_employee_months
    else float("nan")
)

overtime_share = (
    visible["overtime_pay"].sum() / total_employer_cost * 100
    if total_employer_cost
    else float("nan")
)

variable_share = (
    visible["variable_pay"].sum() / total_gross * 100
    if total_gross
    else float("nan")
)

total_lop_days = visible["lop_days"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross pay", money(total_gross))
c2.metric("Net pay", money(total_net))
c3.metric("Employer cost", money(total_employer_cost))
c4.metric("Cost per employee-month", money(cost_per_head))

c5, c6, c7 = st.columns(3)
c5.metric("Overtime share", pct(overtime_share))
c6.metric("Variable pay share", pct(variable_share))
c7.metric("LOP days", number(total_lop_days, 1))


# ---------------------------------------------------------------------
# Department-month metrics
# ---------------------------------------------------------------------
st.header("Payroll metrics by department and month")

metric_view = filtered[
    [
        "department_name", "month", "employee_count", "privacy_status",
        "gross_pay", "net_pay", "employer_cost", "cost_per_head",
        "overtime_share", "variable_pay_share", "lop_days",
    ]
].copy()

metric_view["month"] = metric_view["month"].dt.strftime("%Y-%m")

metric_display = format_columns(
    metric_view,
    currency_columns=[
        "gross_pay", "net_pay", "employer_cost", "cost_per_head"
    ],
    percentage_columns=["overtime_share", "variable_pay_share"],
    number_columns=["employee_count", "lop_days"],
)

st.dataframe(
    metric_display.sort_values(["month", "department_name"]),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Employer cost by department")
department_cost = visible.groupby("department_name")["employer_cost"].sum()
st.bar_chart(department_cost)

st.subheader("Employer cost trend")
trend = (
    visible.groupby("month", as_index=False)["employer_cost"]
    .sum()
    .sort_values("month")
)
trend["month"] = trend["month"].dt.strftime("%Y-%m")
st.line_chart(trend.set_index("month")["employer_cost"])


# ---------------------------------------------------------------------
# M19 — Company-wide monthly payroll as % of operating revenue
# This metric is monthly-grain and therefore not filtered by department.
# ---------------------------------------------------------------------
st.header("M19 — Payroll as a percentage of operating revenue")
st.caption(
    "Company-wide monthly metric for the selected months. "
    "Revenue is sourced from invoice ledger accounts 4001–4004; "
    "other income account 4900 is excluded. "
    "The department filter does not apply to this company-wide ratio."
)

ratio_view = revenue_ratio[
    revenue_ratio["month"].isin(selected_months)
].copy()

ratio_display = ratio_view.copy()
ratio_display["month"] = ratio_display["month"].dt.strftime("%Y-%m")
ratio_display = format_columns(
    ratio_display,
    currency_columns=["payroll_employer_cost", "operating_revenue"],
    percentage_columns=["payroll_as_pct_revenue"],
)

st.dataframe(
    ratio_display[
        [
            "month", "payroll_employer_cost",
            "operating_revenue", "payroll_as_pct_revenue",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

if not ratio_view.empty:
    ratio_chart = ratio_view.copy()
    ratio_chart["month"] = ratio_chart["month"].dt.strftime("%Y-%m")
    st.line_chart(
        ratio_chart.set_index("month")["payroll_as_pct_revenue"]
    )


# ---------------------------------------------------------------------
# Budget versus actual
# ---------------------------------------------------------------------
st.header("Payroll budget versus actual")
st.caption(
    "Variance = corrected actual employer cost minus budget. "
    "Budget variance is not the same as payroll-to-ledger reconciliation."
)

budget_view = filtered_budget[
    [
        "department_name", "month", "budget_cost",
        "corrected_actual_cost", "variance", "variance_percent", "status",
    ]
].copy()

budget_view["month"] = budget_view["month"].dt.strftime("%Y-%m")
budget_display = format_columns(
    budget_view,
    currency_columns=[
        "budget_cost", "corrected_actual_cost", "variance"
    ],
    percentage_columns=["variance_percent"],
)

st.dataframe(
    budget_display.sort_values(["month", "department_name"]),
    use_container_width=True,
    hide_index=True,
)

if not filtered_budget.empty:
    budget_chart = filtered_budget.pivot_table(
        index="month",
        columns="department_name",
        values="corrected_actual_cost",
        aggfunc="sum",
    ).sort_index()
    budget_chart.index = pd.to_datetime(budget_chart.index).strftime("%Y-%m")
    st.line_chart(budget_chart)


# ---------------------------------------------------------------------
# Payroll-to-ledger reconciliation with privacy suppression
# ---------------------------------------------------------------------
st.header("Payroll-to-ledger reconciliation")
st.caption(
    "Payroll employer cost is compared with ledger expense accounts 5001–5005. "
    "Differences remain visible for investigation. "
    "Counts and financial values are suppressed for groups with fewer than "
    f"{MIN_GROUP_SIZE} employees."
)

status_counts = (
    filtered_reconciliation["reconciliation_status"]
    .value_counts()
    .rename_axis("status")
    .reset_index(name="department_months")
)

st.dataframe(status_counts, use_container_width=True, hide_index=True)

recon_view = filtered_reconciliation[
    [
        "department_name", "month", "payroll_employer_cost",
        "ledger_expense", "difference_payroll_minus_ledger",
        "payroll_rows", "employee_count", "reconciliation_status",
    ]
].copy()

small_groups = recon_view["employee_count"].fillna(0).lt(MIN_GROUP_SIZE)

# Suppress sensitive counts and amounts for small groups.
sensitive_columns = [
    "payroll_employer_cost",
    "ledger_expense",
    "difference_payroll_minus_ledger",
    "payroll_rows",
    "employee_count",
]
recon_view.loc[small_groups, sensitive_columns] = float("nan")

recon_view["privacy_status"] = "Visible"
recon_view.loc[
    small_groups, "privacy_status"
] = "Suppressed (<5 employees)"

recon_view["month"] = recon_view["month"].dt.strftime("%Y-%m")

recon_display = format_columns(
    recon_view,
    currency_columns=[
        "payroll_employer_cost", "ledger_expense",
        "difference_payroll_minus_ledger",
    ],
    number_columns=["payroll_rows", "employee_count"],
)

recon_display = recon_display[
    [
        "department_name", "month", "payroll_employer_cost",
        "ledger_expense", "difference_payroll_minus_ledger",
        "payroll_rows", "employee_count", "privacy_status",
        "reconciliation_status",
    ]
]

st.dataframe(
    recon_display.sort_values(
        ["reconciliation_status", "month", "department_name"],
        ascending=[True, True, True],
    ),
    use_container_width=True,
    hide_index=True,
)

exceptions = filtered_reconciliation[
    filtered_reconciliation["reconciliation_status"] != "MATCHED"
].copy()

if exceptions.empty:
    st.success("No payroll-to-ledger exceptions in the selected filters.")
else:
    st.warning(
        f"{len(exceptions)} department-month reconciliation exception(s) "
        "are present in the selected filters."
    )

    exception_view = exceptions[
        [
            "department_name", "month", "payroll_employer_cost",
            "ledger_expense", "difference_payroll_minus_ledger",
            "employee_count", "reconciliation_status",
        ]
    ].copy()

    exception_small = exception_view["employee_count"].fillna(0).lt(
        MIN_GROUP_SIZE
    )
    exception_view.loc[
        exception_small,
        [
            "payroll_employer_cost", "ledger_expense",
            "difference_payroll_minus_ledger", "employee_count",
        ],
    ] = float("nan")

    exception_view["privacy_status"] = "Visible"
    exception_view.loc[
        exception_small, "privacy_status"
    ] = "Suppressed (<5 employees)"

    exception_view["month"] = exception_view["month"].dt.strftime("%Y-%m")

    exception_display = format_columns(
        exception_view,
        currency_columns=[
            "payroll_employer_cost", "ledger_expense",
            "difference_payroll_minus_ledger",
        ],
        number_columns=["employee_count"],
    )

    st.dataframe(
        exception_display,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Four suspicious payroll rows
# ---------------------------------------------------------------------
st.header("Payroll exception evidence")
st.caption(
    "PI-X0001 and PI-X0002 are confirmed duplicates. "
    "PI-X0003 and PI-X0004 are ledger-mismatch candidates pending validation."
)

evidence_view = excluded_evidence.copy()

evidence_view = evidence_view[
    evidence_view["department_id"].isin(
        reconciliation.loc[
            reconciliation["department_name"].isin(selected_departments),
            "department_id",
        ].unique()
    )
].copy()

evidence_view["employer_cost"] = evidence_view["employer_cost"].map(money)

st.dataframe(
    evidence_view,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------------------
# Download filtered results
# ---------------------------------------------------------------------
st.header("Export")

st.download_button(
    "Download filtered payroll metrics CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="Task9_Filtered_Payroll_Metrics.csv",
    mime="text/csv",
)

st.download_button(
    "Download filtered reconciliation CSV",
    data=filtered_reconciliation.to_csv(index=False).encode("utf-8"),
    file_name="Task9_Filtered_Payroll_Ledger_Reconciliation.csv",
    mime="text/csv",
)

st.caption(
    "The original source files remain unchanged. Two confirmed duplicates "
    "are excluded from analytical totals; two ledger-mismatch candidates "
    "remain included pending validation. The official PQ-09 answer key was "
    "not found in the project locations checked, so no official validation "
    "score is claimed."
)
