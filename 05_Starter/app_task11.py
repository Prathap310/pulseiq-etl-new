from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="PulseIQ | Task 11 P&L Analytics",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "03_Data" / "csv"

st.title("Task 11 — Profit & Loss and Expense Analytics")
st.caption("Monthly financial performance, expense categories, vendor spending, and reconciliation.")

@st.cache_data
def load_csv(filename):
    path = CSV_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)

def money(value):
    return f"₹{value:,.2f}"

try:
    accounts = load_csv("dim_account.csv")
    ledger = load_csv("fact_ledger.csv")
    expenses = load_csv("fact_expense.csv")
    vendors = load_csv("dim_vendor.csv")
except Exception as exc:
    st.error(f"Could not load source data: {exc}")
    st.stop()

required_accounts = {
    "account_code", "account_name", "account_type", "is_group", "statement"
}
required_ledger = {
    "entry_date", "account_code", "debit", "credit", "posting_period"
}
required_expenses = {
    "expense_date", "category_account", "vendor_id", "amount_excl_gst"
}
required_vendors = {"vendor_id", "vendor_name"}

for name, frame, required in [
    ("dim_account.csv", accounts, required_accounts),
    ("fact_ledger.csv", ledger, required_ledger),
    ("fact_expense.csv", expenses, required_expenses),
    ("dim_vendor.csv", vendors, required_vendors),
]:
    missing = required - set(frame.columns)
    if missing:
        st.error(f"{name} is missing columns: {', '.join(sorted(missing))}")
        st.stop()

# ---------------------------------------------------------------------
# Prepare account hierarchy and ledger
# ---------------------------------------------------------------------
for frame, column in [
    (accounts, "account_code"),
    (ledger, "account_code"),
    (expenses, "category_account"),
]:
    frame[column] = pd.to_numeric(frame[column], errors="coerce")

accounts["is_group"] = accounts["is_group"].astype(str).str.upper().str.strip()
accounts["account_type"] = accounts["account_type"].astype(str).str.upper().str.strip()

detail_accounts = accounts[accounts["is_group"].eq("N")].copy()
pl_accounts = detail_accounts[
    detail_accounts["account_type"].isin(["INCOME", "EXPENSE"])
].copy()

ledger["entry_date"] = pd.to_datetime(ledger["entry_date"], errors="coerce")
ledger["debit"] = pd.to_numeric(ledger["debit"], errors="coerce").fillna(0)
ledger["credit"] = pd.to_numeric(ledger["credit"], errors="coerce").fillna(0)

ledger = ledger.merge(
    pl_accounts[["account_code", "account_name", "account_type"]],
    on="account_code",
    how="inner",
)

ledger["month"] = ledger["entry_date"].dt.to_period("M").astype(str)
ledger = ledger[ledger["month"].notna() & ledger["entry_date"].notna()].copy()

# Revenue is credit less debit; expense is debit less credit.
ledger["revenue_amount"] = 0.0
ledger["expense_amount"] = 0.0

income_mask = ledger["account_type"].eq("INCOME")
expense_mask = ledger["account_type"].eq("EXPENSE")

ledger.loc[income_mask, "revenue_amount"] = (
    ledger.loc[income_mask, "credit"] - ledger.loc[income_mask, "debit"]
)
ledger.loc[expense_mask, "expense_amount"] = (
    ledger.loc[expense_mask, "debit"] - ledger.loc[expense_mask, "credit"]
)

monthly = (
    ledger.groupby("month", as_index=False)
    .agg(
        revenue=("revenue_amount", "sum"),
        expenses=("expense_amount", "sum"),
    )
    .sort_values("month")
)
monthly["profit"] = monthly["revenue"] - monthly["expenses"]
monthly["profit_margin_pct"] = (
    monthly["profit"].div(monthly["revenue"].replace(0, pd.NA)) * 100
)

if monthly.empty:
    st.error("No P&L ledger records were found.")
    st.stop()

# ---------------------------------------------------------------------
# Prepare expense fact for category and vendor analysis
# ---------------------------------------------------------------------
expenses["expense_date"] = pd.to_datetime(
    expenses["expense_date"], errors="coerce"
)
expenses["amount_excl_gst"] = pd.to_numeric(
    expenses["amount_excl_gst"], errors="coerce"
).fillna(0)
expenses["category_account"] = pd.to_numeric(
    expenses["category_account"], errors="coerce"
)

expenses = expenses.merge(
    detail_accounts[["account_code", "account_name", "account_type"]],
    left_on="category_account",
    right_on="account_code",
    how="left",
)

expenses = expenses.merge(
    vendors[["vendor_id", "vendor_name"]],
    on="vendor_id",
    how="left",
)
expenses["vendor_name"] = expenses["vendor_name"].fillna("Unknown vendor")
expenses["account_name"] = expenses["account_name"].fillna("Unmapped category")
expenses["month"] = expenses["expense_date"].dt.to_period("M").astype(str)

# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
st.sidebar.header("Filters")
available_months = monthly["month"].tolist()
selected_month = st.sidebar.selectbox(
    "Select month",
    ["All months"] + available_months,
    index=0,
)

if selected_month == "All months":
    selected_monthly = monthly.copy()
    selected_expenses = expenses.copy()
else:
    selected_monthly = monthly[monthly["month"].eq(selected_month)].copy()
    selected_expenses = expenses[expenses["month"].eq(selected_month)].copy()

# ---------------------------------------------------------------------
# KPI overview
# ---------------------------------------------------------------------
total_revenue = selected_monthly["revenue"].sum()
total_expenses = selected_monthly["expenses"].sum()
total_profit = total_revenue - total_expenses
overall_margin = (
    total_profit / total_revenue * 100 if total_revenue else 0
)

st.header("P&L overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", money(total_revenue))
c2.metric("Expenses", money(total_expenses))
c3.metric("Profit", money(total_profit))
c4.metric("Profit margin", f"{overall_margin:.2f}%")

# ---------------------------------------------------------------------
# Monthly trend
# ---------------------------------------------------------------------
st.header("Monthly revenue, expenses and profit")
trend = selected_monthly.melt(
    id_vars="month",
    value_vars=["revenue", "expenses", "profit"],
    var_name="metric",
    value_name="amount",
)
fig = px.line(
    trend,
    x="month",
    y="amount",
    color="metric",
    markers=True,
    title="Monthly financial performance",
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
# P&L table
# ---------------------------------------------------------------------
st.header("Profit & Loss statement")
pnl_table = selected_monthly.copy()
pnl_table["profit_margin_pct"] = pnl_table["profit_margin_pct"].round(2)
display_pnl = pnl_table.rename(
    columns={
        "month": "Month",
        "revenue": "Revenue (₹)",
        "expenses": "Expenses (₹)",
        "profit": "Profit (₹)",
        "profit_margin_pct": "Profit Margin (%)",
    }
)
st.dataframe(
    display_pnl.style.format({
        "Revenue (₹)": "₹{:,.2f}",
        "Expenses (₹)": "₹{:,.2f}",
        "Profit (₹)": "₹{:,.2f}",
        "Profit Margin (%)": "{:.2f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------
# Expense categories
# ---------------------------------------------------------------------
st.header("Expense analysis by category")
category_summary = (
    selected_expenses.groupby("account_name", as_index=False)
    .agg(expense_amount=("amount_excl_gst", "sum"))
    .sort_values("expense_amount", ascending=False)
)

if not category_summary.empty:
    category_fig = px.bar(
        category_summary,
        x="expense_amount",
        y="account_name",
        orientation="h",
        title="Expense by category (excluding GST)",
        labels={
            "expense_amount": "Expense amount (₹)",
            "account_name": "Category",
        },
    )
    category_fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(category_fig, use_container_width=True)
    st.dataframe(
        category_summary.rename(
            columns={
                "account_name": "Expense Category",
                "expense_amount": "Amount (₹)",
            }
        ).style.format({"Amount (₹)": "₹{:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No expense category records are available for this selection.")

# ---------------------------------------------------------------------
# Top 10 vendors
# ---------------------------------------------------------------------
st.header("Top 10 vendors by expense")
vendor_summary = (
    selected_expenses.groupby("vendor_name", as_index=False)
    .agg(
        expense_amount=("amount_excl_gst", "sum"),
        transaction_count=("vendor_id", "count"),
    )
    .sort_values("expense_amount", ascending=False)
    .head(10)
)

if not vendor_summary.empty:
    vendor_fig = px.bar(
        vendor_summary.sort_values("expense_amount"),
        x="expense_amount",
        y="vendor_name",
        orientation="h",
        title="Top 10 vendors by expense (excluding GST)",
        labels={
            "expense_amount": "Expense amount (₹)",
            "vendor_name": "Vendor",
        },
    )
    st.plotly_chart(vendor_fig, use_container_width=True)
    st.dataframe(
        vendor_summary.rename(
            columns={
                "vendor_name": "Vendor",
                "expense_amount": "Expense (₹)",
                "transaction_count": "Transactions",
            }
        ).style.format({"Expense (₹)": "₹{:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No vendor expense records are available for this selection.")

# ---------------------------------------------------------------------
# Expense-to-ledger reconciliation
# ---------------------------------------------------------------------
st.header("Expense-to-ledger reconciliation")
st.caption(
    "The ledger is the P&L source of truth. Expense records are used for "
    "category and vendor analysis and are not added again to P&L totals."
)

if {"ledger_entry_id", "category_account"}.issubset(expenses.columns):
    linked = expenses[
        expenses["ledger_entry_id"].notna()
        & expenses["ledger_entry_id"].astype(str).str.strip().ne("")
    ].copy()

    ledger_entries = load_csv("fact_ledger.csv")
    ledger_entries["account_code"] = pd.to_numeric(
        ledger_entries["account_code"], errors="coerce"
    )
    ledger_entries["debit"] = pd.to_numeric(
        ledger_entries["debit"], errors="coerce"
    ).fillna(0)
    ledger_entries["credit"] = pd.to_numeric(
        ledger_entries["credit"], errors="coerce"
    ).fillna(0)

    expense_ledger = ledger_entries[
        ledger_entries["account_code"].isin(
            detail_accounts.loc[
                detail_accounts["account_type"].eq("EXPENSE"), "account_code"
            ]
        )
    ].copy()

    ledger_net = (
        expense_ledger.groupby("entry_id", as_index=False)
        .apply(
            lambda group: pd.Series({
                "ledger_expense": (group["debit"] - group["credit"]).sum()
            }),
            include_groups=False,
        )
    )

    linked["ledger_entry_id"] = linked["ledger_entry_id"].astype(str)
    ledger_net["entry_id"] = ledger_net["entry_id"].astype(str)
    matched = linked.merge(
        ledger_net,
        left_on="ledger_entry_id",
        right_on="entry_id",
        how="left",
    )
    matched["ledger_expense"] = matched["ledger_expense"].fillna(0)
    matched["difference"] = (
        matched["amount_excl_gst"] - matched["ledger_expense"]
    )

    if selected_month != "All months":
        matched = matched[
            matched["expense_date"].dt.to_period("M").astype(str).eq(selected_month)
        ]

    reconciliation_summary = pd.DataFrame([{
        "Expense records with ledger reference": len(matched),
        "Matched references": int(matched["entry_id"].notna().sum()),
        "Unmatched references": int(matched["entry_id"].isna().sum()),
        "Expense amount (₹)": matched["amount_excl_gst"].sum(),
        "Matched ledger amount (₹)": matched.loc[
            matched["entry_id"].notna(), "ledger_expense"
        ].sum(),
        "Difference (₹)": matched["difference"].sum(),
    }])

    st.dataframe(
        reconciliation_summary.style.format({
            "Expense amount (₹)": "₹{:,.2f}",
            "Matched ledger amount (₹)": "₹{:,.2f}",
            "Difference (₹)": "₹{:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("Ledger reference column is unavailable; reconciliation cannot be calculated.")

# ---------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------
st.header("Key findings")

if len(monthly):
    highest_margin = monthly.loc[monthly["profit_margin_pct"].idxmax()]
    lowest_margin = monthly.loc[monthly["profit_margin_pct"].idxmin()]
    highest_revenue = monthly.loc[monthly["revenue"].idxmax()]

    st.markdown(
        f"1. **Highest margin:** {highest_margin['month']} recorded "
        f"{highest_margin['profit_margin_pct']:.2f}% profit margin."
    )
    st.markdown(
        f"2. **Lowest margin:** {lowest_margin['month']} recorded "
        f"{lowest_margin['profit_margin_pct']:.2f}% profit margin, "
        f"indicating the weakest monthly margin in the available period."
    )
    if not vendor_summary.empty:
        top_vendor = vendor_summary.iloc[0]
        st.markdown(
            f"3. **Vendor concentration:** {top_vendor['vendor_name']} was the "
            f"largest vendor in the selected period, with expenses of "
            f"{money(top_vendor['expense_amount'])}."
        )
    else:
        st.markdown(
            f"3. **Revenue peak:** {highest_revenue['month']} recorded the "
            f"highest monthly revenue at {money(highest_revenue['revenue'])}."
        )

# ---------------------------------------------------------------------
# Reference totals and export
# ---------------------------------------------------------------------
st.header("Reference totals and export")
st.info(
    "README headline P&L figures were not found in the current README. "
    "The dashboard therefore presents calculated ledger totals without "
    "claiming reconciliation to unavailable README figures."
)

st.download_button(
    "Download monthly P&L as CSV",
    data=monthly.to_csv(index=False).encode("utf-8"),
    file_name="Task11_Monthly_PL.csv",
    mime="text/csv",
)

st.download_button(
    "Download vendor analysis as CSV",
    data=vendor_summary.to_csv(index=False).encode("utf-8"),
    file_name="Task11_Top10_Vendors.csv",
    mime="text/csv",
)

st.caption(
    "P&L uses detail ledger accounts only. Expense category and vendor "
    "analysis uses fact_expense amounts excluding GST."
)
