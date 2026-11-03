
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="PulseIQ | Task 12 Receivables & Cash Flow",
    page_icon="💰",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "03_Data" / "csv"
CUTOFF_DATE = pd.Timestamp("2026-09-30")

st.title("Task 12 — Invoices, Receivables and Cash Flow")
st.caption(
    "Receivables ageing, client payment behaviour, overdue balances, "
    "and monthly cash movement."
)


@st.cache_data
def load_csv(filename):
    path = CSV_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def money(value):
    return f"₹{value:,.2f}"


try:
    invoices = load_csv("fact_invoice.csv")
    payments = load_csv("fact_invoice_payment.csv")
    clients = load_csv("dim_client.csv")
    expenses = load_csv("fact_expense.csv")
except Exception as exc:
    st.error(f"Could not load source data: {exc}")
    st.stop()


# ---------------------------------------------------------------------
# Validate required columns
# ---------------------------------------------------------------------
required = {
    "fact_invoice.csv": (
        invoices,
        {
            "invoice_id", "client_id", "invoice_date", "due_date",
            "total_amount", "amount_paid", "balance_due", "status",
            "days_to_pay",
        },
    ),
    "fact_invoice_payment.csv": (
        payments,
        {"payment_id", "invoice_id", "payment_date", "amount"},
    ),
    "dim_client.csv": (
        clients,
        {"client_id", "client_name", "payment_behaviour"},
    ),
    "fact_expense.csv": (
        expenses,
        {"expense_id", "paid_date", "total_amount", "status"},
    ),
}

for filename, (frame, columns) in required.items():
    missing = columns - set(frame.columns)
    if missing:
        st.error(
            f"{filename} is missing columns: "
            f"{', '.join(sorted(missing))}"
        )
        st.stop()


# ---------------------------------------------------------------------
# Clean data types
# ---------------------------------------------------------------------
for column in ["invoice_date", "due_date"]:
    invoices[column] = pd.to_datetime(
        invoices[column], errors="coerce"
    )

invoices["status"] = (
    invoices["status"].astype(str).str.strip().str.upper()
)

for column in ["total_amount", "amount_paid", "balance_due", "days_to_pay"]:
    invoices[column] = pd.to_numeric(
        invoices[column], errors="coerce"
    )

payments["payment_date"] = pd.to_datetime(
    payments["payment_date"], errors="coerce"
)
payments["amount"] = pd.to_numeric(
    payments["amount"], errors="coerce"
)

expenses["paid_date"] = pd.to_datetime(
    expenses["paid_date"], errors="coerce"
)
expenses["total_amount"] = pd.to_numeric(
    expenses["total_amount"], errors="coerce"
)
expenses["status"] = (
    expenses["status"].astype(str).str.strip().str.upper()
)

# ---------------------------------------------------------------------
# Open receivables and ageing
# ---------------------------------------------------------------------
open_statuses = ["SENT", "OVERDUE", "PARTIALLY_PAID"]

open_invoices = invoices[
    invoices["status"].isin(open_statuses)
].copy()

open_invoices = open_invoices[
    open_invoices["balance_due"] > 0
].copy()

open_invoices["days_past_due"] = (
    CUTOFF_DATE - open_invoices["due_date"]
).dt.days.clip(lower=0)

def ageing_bucket(days):
    if pd.isna(days) or days <= 0:
        return "Not yet due"
    if days <= 30:
        return "1-30 days"
    if days <= 60:
        return "31-60 days"
    if days <= 90:
        return "61-90 days"
    return "90+ days"

open_invoices["ageing_bucket"] = (
    open_invoices["days_past_due"].apply(ageing_bucket)
)

ageing_order = [
    "Not yet due",
    "1-30 days",
    "31-60 days",
    "61-90 days",
    "90+ days",
]

ageing = (
    open_invoices.groupby("ageing_bucket", as_index=False)
    .agg(
        invoice_count=("invoice_id", "count"),
        outstanding=("balance_due", "sum"),
    )
)

ageing["ageing_bucket"] = pd.Categorical(
    ageing["ageing_bucket"],
    categories=ageing_order,
    ordered=True,
)
ageing = ageing.sort_values("ageing_bucket")


# ---------------------------------------------------------------------
# Client receivables and average days to pay
# ---------------------------------------------------------------------
open_client = (
    open_invoices.groupby("client_id", as_index=False)
    .agg(
        open_invoice_count=("invoice_id", "count"),
        outstanding=("balance_due", "sum"),
        overdue_amount=(
            "balance_due",
            lambda values: values[
                open_invoices.loc[values.index, "days_past_due"] > 0
            ].sum(),
        ),
    )
)

paid_invoices = invoices[
    (invoices["status"] == "PAID")
    & invoices["days_to_pay"].notna()
].copy()

client_payment_days = (
    paid_invoices.groupby("client_id", as_index=False)
    .agg(
        average_days_to_pay=("days_to_pay", "mean"),
        paid_invoice_count=("invoice_id", "count"),
    )
)

client_analysis = clients.merge(
    open_client, on="client_id", how="left"
).merge(
    client_payment_days, on="client_id", how="left"
)

for column in [
    "open_invoice_count", "outstanding", "overdue_amount",
    "paid_invoice_count",
]:
    client_analysis[column] = (
        client_analysis[column].fillna(0)
    )

# ---------------------------------------------------------------------
# Monthly cash in and cash out
# ---------------------------------------------------------------------
cash_in = payments.dropna(
    subset=["payment_date", "amount"]
).copy()

cash_in["month"] = (
    cash_in["payment_date"].dt.to_period("M").astype(str)
)

cash_in_monthly = (
    cash_in.groupby("month", as_index=False)
    .agg(cash_in=("amount", "sum"))
)

cash_out = expenses[
    (expenses["status"] == "PAID")
    & expenses["paid_date"].notna()
].copy()

cash_out["month"] = (
    cash_out["paid_date"].dt.to_period("M").astype(str)
)

cash_out_monthly = (
    cash_out.groupby("month", as_index=False)
    .agg(cash_out=("total_amount", "sum"))
)

cash_flow = pd.merge(
    cash_in_monthly, cash_out_monthly,
    on="month", how="outer"
).fillna(0)

cash_flow = cash_flow.sort_values("month")
cash_flow["net_cash_flow"] = (
    cash_flow["cash_in"] - cash_flow["cash_out"]
)

# ---------------------------------------------------------------------
# Dashboard filters
# ---------------------------------------------------------------------
st.sidebar.header("Dashboard Filters")

client_options = sorted(clients["client_name"].dropna().unique())

selected_clients = st.sidebar.multiselect(
    "Select clients",
    options=client_options,
    default=client_options,
)

filtered_clients = clients[
    clients["client_name"].isin(selected_clients)
]

filtered_ids = filtered_clients["client_id"]

filtered_open = open_invoices[
    open_invoices["client_id"].isin(filtered_ids)
].copy()

filtered_cash_in = cash_in[
    cash_in["invoice_id"].isin(
        invoices[
            invoices["client_id"].isin(filtered_ids)
        ]["invoice_id"]
    )
].copy()

st.sidebar.caption(
    f"Receivables cutoff: {CUTOFF_DATE.strftime('%d %b %Y')}"
)

# ---------------------------------------------------------------------
# KPI section
# ---------------------------------------------------------------------
total_open = filtered_open["balance_due"].sum()

total_overdue = filtered_open.loc[
    filtered_open["days_past_due"] > 0,
    "balance_due",
].sum()

not_yet_due = filtered_open.loc[
    filtered_open["days_past_due"] == 0,
    "balance_due",
].sum()

overdue_count = (
    filtered_open["days_past_due"] > 0
).sum()

st.subheader("Receivables Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open Receivables", money(total_open))
c2.metric("Overdue Receivables", money(total_overdue))
c3.metric("Not Yet Due", money(not_yet_due))
c4.metric("Overdue Invoices", f"{overdue_count:,}")

# ---------------------------------------------------------------------
# Ageing analysis
# ---------------------------------------------------------------------
st.divider()
st.subheader("1. Receivables Ageing Analysis")

filtered_ageing = (
    filtered_open.groupby("ageing_bucket", as_index=False)
    .agg(
        invoice_count=("invoice_id", "count"),
        outstanding=("balance_due", "sum"),
    )
)

filtered_ageing["ageing_bucket"] = pd.Categorical(
    filtered_ageing["ageing_bucket"],
    categories=ageing_order,
    ordered=True,
)

filtered_ageing = filtered_ageing.sort_values(
    "ageing_bucket"
)

fig_ageing = px.bar(
    filtered_ageing,
    x="ageing_bucket",
    y="outstanding",
    color="ageing_bucket",
    text_auto=".2s",
    title="Outstanding Receivables by Ageing Bucket",
)
st.plotly_chart(fig_ageing, use_container_width=True)

st.dataframe(
    filtered_ageing,
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------
# Top overdue clients
# ---------------------------------------------------------------------
st.divider()
st.subheader("2. Clients with the Highest Overdue Amount")

top_clients = (
    filtered_open[
        filtered_open["days_past_due"] > 0
    ].merge(
        clients[["client_id", "client_name"]],
        on="client_id",
        how="left",
    )
    .groupby("client_name", as_index=False)
    .agg(
        overdue_amount=("balance_due", "sum"),
        overdue_invoices=("invoice_id", "count"),
        maximum_days_overdue=("days_past_due", "max"),
    )
    .sort_values("overdue_amount", ascending=False)
    .head(10)
)

if not top_clients.empty:
    fig_clients = px.bar(
        top_clients.sort_values("overdue_amount"),
        x="overdue_amount",
        y="client_name",
        orientation="h",
        text_auto=".2s",
        title="Top 10 Clients by Overdue Receivables",
    )
    st.plotly_chart(fig_clients, use_container_width=True)
    st.dataframe(
        top_clients,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No overdue balances for the selected clients.")

# ---------------------------------------------------------------------
# Average days to pay
# ---------------------------------------------------------------------
st.divider()
st.subheader("3. Average Days to Pay by Client")

payment_analysis = client_analysis[
    client_analysis["client_id"].isin(filtered_ids)
].copy()

payment_analysis = payment_analysis.sort_values(
    "average_days_to_pay", ascending=False, na_position="last"
)

fig_payment_days = px.bar(
    payment_analysis.dropna(
        subset=["average_days_to_pay"]
    ),
    x="client_name",
    y="average_days_to_pay",
    color="payment_behaviour",
    title="Average Days to Pay by Client (Fully Paid Invoices)",
)
fig_payment_days.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_payment_days, use_container_width=True)

st.dataframe(
    payment_analysis[
        [
            "client_name",
            "payment_behaviour",
            "average_days_to_pay",
            "paid_invoice_count",
            "outstanding",
            "overdue_amount",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------
# Monthly cash flow
# ---------------------------------------------------------------------
st.divider()
st.subheader("4. Monthly Cash In versus Cash Out")

selected_invoice_ids = invoices[
    invoices["client_id"].isin(filtered_ids)
]["invoice_id"]

filtered_cash_in = cash_in[
    cash_in["invoice_id"].isin(selected_invoice_ids)
].copy()

filtered_cash_in["month"] = (
    filtered_cash_in["payment_date"].dt.to_period("M").astype(str)
)

filtered_cash_out = cash_out.copy()

filtered_cash_in_monthly = (
    filtered_cash_in.groupby("month", as_index=False)
    .agg(cash_in=("amount", "sum"))
)

filtered_cash_out_monthly = (
    filtered_cash_out.groupby("month", as_index=False)
    .agg(cash_out=("total_amount", "sum"))
)

filtered_cash_flow = pd.merge(
    filtered_cash_in_monthly,
    filtered_cash_out_monthly,
    on="month",
    how="outer",
).fillna(0)

filtered_cash_flow = filtered_cash_flow.sort_values("month")
filtered_cash_flow["net_cash_flow"] = (
    filtered_cash_flow["cash_in"]
    - filtered_cash_flow["cash_out"]
)

if not filtered_cash_flow.empty:
    cash_chart = filtered_cash_flow.melt(
        id_vars="month",
        value_vars=["cash_in", "cash_out"],
        var_name="cash_type",
        value_name="amount",
    )

    fig_cash = px.bar(
        cash_chart,
        x="month",
        y="amount",
        color="cash_type",
        barmode="group",
        title="Monthly Cash In and Cash Out",
    )
    st.plotly_chart(fig_cash, use_container_width=True)

    st.dataframe(
        filtered_cash_flow,
        use_container_width=True,
        hide_index=True,
    )

# ---------------------------------------------------------------------
# Receivables reconciliation
# ---------------------------------------------------------------------
st.divider()
st.subheader("5. Receivables Reconciliation")

ageing_total = filtered_ageing["outstanding"].sum()
reconciliation_difference = total_open - ageing_total

r1, r2, r3 = st.columns(3)
r1.metric("Open Invoice Balance", money(total_open))
r2.metric("Ageing Bucket Total", money(ageing_total))
r3.metric("Difference", money(reconciliation_difference))

if abs(reconciliation_difference) < 0.01:
    st.success("Receivables ageing reconciles with total open receivables.")
else:
    st.error(
        "Receivables ageing does not reconcile. "
        "Investigate the underlying invoice records."
    )

# ---------------------------------------------------------------------
# Additional data-quality observations
# ---------------------------------------------------------------------
st.divider()
st.subheader("6. Data Quality and Reconciliation Checks")

invoice_total = invoices["total_amount"].sum()
invoice_paid_total = invoices["amount_paid"].sum()
invoice_balance_total = invoices["balance_due"].sum()
payment_total = payments["amount"].sum()

checks = pd.DataFrame([
    {
        "Check": "Invoice total less amount paid versus balance due",
        "Value": invoice_total - invoice_paid_total - invoice_balance_total,
    },
    {
        "Check": "Invoice amount paid versus payment records",
        "Value": invoice_paid_total - payment_total,
    },
    {
        "Check": "Unpaid expenses excluded from cash out",
        "Value": expenses.loc[
            expenses["status"] != "PAID", "total_amount"
        ].sum(),
    },
])

st.dataframe(checks, use_container_width=True, hide_index=True)

st.caption(
    "Cash in uses customer payment records by payment date. "
    "Cash out uses PAID expense records by paid date. "
    "Cash out is not filtered by client because expense records "
    "are not linked to clients."
)

# ---------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------
st.divider()
st.subheader("7. Download Reports")

d1, d2, d3 = st.columns(3)

with d1:
    st.download_button(
        "Download Open Receivables",
        filtered_open.to_csv(index=False).encode("utf-8"),
        "Task12_Open_Receivables.csv",
        "text/csv",
    )

with d2:
    st.download_button(
        "Download Ageing Summary",
        filtered_ageing.to_csv(index=False).encode("utf-8"),
        "Task12_Ageing_Summary.csv",
        "text/csv",
    )

with d3:
    st.download_button(
        "Download Cash Flow",
        filtered_cash_flow.to_csv(index=False).encode("utf-8"),
        "Task12_Cash_Flow.csv",
        "text/csv",
    )

st.caption(
    "PulseIQ ETL | Task 12 | Receivables and Cash Flow Analytics"
)
