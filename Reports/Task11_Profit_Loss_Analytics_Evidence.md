# Task 11 — Profit & Loss and Expense Analytics

## 1. Objective
Develop a Streamlit dashboard to analyse monthly revenue, expenses, profit, profit margin, expense categories, and vendor spending.

## 2. Data Sources
- 03_Data/csv/dim_account.csv
- 03_Data/csv/fact_ledger.csv
- 03_Data/csv/fact_expense.csv
- 03_Data/csv/dim_vendor.csv

## 3. Account Hierarchy
Group accounts are excluded from calculations. Only active account detail-level classification is used through the account hierarchy, with P&L calculations restricted to detail accounts classified as INCOME or EXPENSE.

## 4. Dashboard Implementation
Created `05_Starter/app_task11.py` with:
- Monthly revenue, expenses, profit, and profit margin KPIs.
- Monthly financial performance trend.
- Month selector and P&L table.
- Expense analysis by category.
- Top 10 vendors by expense.
- Expense-to-ledger reconciliation.
- Three automatically generated key findings.
- CSV export for monthly P&L and vendor analysis.

## 5. Validation Results

### Ledger Date Coverage
- Valid ledger dates: 6,784
- Invalid ledger dates: 0
- Monthly periods: 18
- First period: April 2025
- Last period: September 2026

### Independent P&L Validation
| Metric | Calculated Result |
|---|---:|
| Revenue | ₹1,260,930,052.00 |
| Expenses | ₹1,036,264,914.42 |
| Profit | ₹224,665,137.58 |
| Profit Margin | 17.82% |

Independent calculations matched the dashboard totals.

### Expense-to-Ledger Reconciliation
- Expense records with ledger references: 501
- Matched references: 501
- Unmatched references: 0
- Difference: ₹0.00

### Dashboard Testing
- Python syntax validation passed.
- Dashboard launched successfully.
- Monthly filter tested successfully.
- KPI values changed according to the selected month.
- Expense category and vendor visualizations displayed.
- P&L table and CSV export controls implemented.

## 6. Key Financial Findings
1. August 2026 recorded the highest monthly profit margin at 27.16%.
2. July 2025 recorded the lowest monthly profit margin at 8.27%.
3. Skyline Realty Holdings was the largest vendor by expense, with ₹16,879,440 across 22 transactions in the full dataset.

## 7. README Reference Comparison
The current README does not contain P&L headline figures. Therefore, comparison against README reference totals remains pending until the expected figures are provided.

## 8. Deliverable
Dashboard: `05_Starter/app_task11.py`

Evidence report: `Reports/Task11_Profit_Loss_Analytics_Evidence.md`

## 9. Overall Status
Dashboard implementation and the listed technical validations are complete. README reference comparison and final Git submission remain pending.
