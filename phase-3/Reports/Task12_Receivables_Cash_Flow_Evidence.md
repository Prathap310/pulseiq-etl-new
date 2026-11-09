\# Task 12 – Invoices, Receivables and Cash Flow Analytics



\## 1. Objective



The objective of Task 12 was to develop an analytics dashboard to monitor open invoices, receivables ageing, client payment performance, overdue balances, and monthly cash inflows and outflows.



The dashboard was developed using the provided invoice, invoice payment, client, and expense datasets.



\## 2. Source Datasets



The following CSV files were used:



1\. `fact\_invoice.csv` – Invoice details, invoice status, total amount, paid amount, outstanding balance, due date and ageing information.

2\. `fact\_invoice\_payment.csv` – Invoice payment transactions, payment dates and received amounts.

3\. `dim\_client.csv` – Client information and payment details.

4\. `fact\_expense.csv` – Expense records, payment status, paid dates and expense amounts.



\## 3. Implementation



The Streamlit dashboard was developed in:



`05\_Starter/app\_task12.py`



The dashboard includes the following sections:



\- Receivables overview and key performance indicators.

\- Open invoice identification.

\- Receivables ageing analysis.

\- Clients with the highest overdue balances.

\- Average days to pay by client.

\- Monthly cash inflow versus cash outflow.

\- Receivables reconciliation.

\- Data quality validation checks.

\- CSV report download options.



\## 4. Invoice and Receivables Analysis



A total of 743 invoice records were analyzed.



Invoice status distribution:



| Invoice Status | Records |

|---|---:|

| PAID | 676 |

| SENT | 49 |

| OVERDUE | 12 |

| PARTIALLY\_PAID | 1 |

| CANCELLED | 4 |

| DRAFT | 1 |

| \*\*Total\*\* | \*\*743\*\* |



Open receivables were calculated using the SENT, OVERDUE and PARTIALLY\_PAID statuses.



\- Total open invoices: 62

\- Total open receivables: ₹139,394,278

\- Overdue receivables: ₹27,110,866

\- Not-yet-due receivables: ₹112,283,412



\## 5. Receivables Ageing Analysis



Open receivables were classified into ageing buckets based on the reporting cutoff date of 30 September 2026.



| Ageing Bucket | Invoice Count | Outstanding Amount |

|---|---:|---:|

| Not yet due | 49 | ₹112,283,412 |

| 1–30 days | 10 | ₹22,133,626 |

| 31–60 days | 0 | ₹0 |

| 61–90 days | 1 | ₹1,940,982 |

| 90+ days | 2 | ₹3,036,258 |

| \*\*Total\*\* | \*\*62\*\* | \*\*₹139,394,278\*\* |



The ageing buckets were checked against the total open receivables.



\*\*Reconciliation result: PASSED\*\*



The total of all ageing buckets matches the open receivables balance. The reconciliation difference is ₹0.



\## 6. Highest Overdue Clients



The dashboard identifies clients with the highest overdue balances and displays their outstanding amounts.



This analysis helps identify clients requiring payment follow-up and supports receivables collection activities.



The overdue analysis includes partially paid invoices where an outstanding balance remains overdue.



\## 7. Average Days to Pay by Client



Average days to pay were calculated for each client using the `days\_to\_pay` field from fully paid invoices.



The dashboard displays the average payment duration by client to help understand payment behaviour and identify clients who generally take longer to settle invoices.



This calculation is based on fully paid invoices only.



\## 8. Monthly Cash Inflow and Cash Outflow



Monthly cash inflow was calculated using payment transactions from `fact\_invoice\_payment.csv`, grouped by `payment\_date`.



Monthly cash outflow was calculated using PAID expense records from `fact\_expense.csv`, grouped by `paid\_date`.



Dataset summary:



\- Total recorded invoice payment transactions: ₹1,419,349,558

\- Total expense amount: ₹197,477,337.90

\- Total paid expenses: ₹185,831,316.70

\- Total unpaid expenses: ₹11,646,021.20



The dashboard compares monthly cash inflows and outflows to provide visibility into cash movement.



\*\*Note:\*\* Expense records are not linked to individual clients. Therefore, the client filter does not filter cash-out amounts.



\## 9. Data Quality and Reconciliation Checks



The following validations were performed:



1\. Verified invoice status categories.

2\. Verified open invoice selection.

3\. Checked outstanding balances for open invoices.

4\. Validated ageing bucket classification.

5\. Checked whether ageing buckets reconcile to total open receivables.

6\. Checked invoice and payment record identifiers for duplicates.

7\. Checked payment records for unknown invoice IDs.

8\. Checked invoice records for unknown client IDs.

9\. Checked paid expense records for missing paid dates.

10\. Compared invoice payment totals with payment transaction totals.



\### Reconciliation observations



Two differences were identified during validation:



\*\*Observation 1 – Invoice balance difference\*\*



The difference between invoice total less amount paid and the recorded balance due is ₹5,540,218. This relates to cancelled and draft invoice records in the source data.



\*\*Observation 2 – Payment transaction difference\*\*



The total amount recorded in invoice payment transactions differs from the invoice-level amount paid by ₹100.



These differences were retained as data quality observations rather than silently adjusted.



\## 10. Testing Performed



The following dashboard testing activities were completed:



\- Verified that the Streamlit application launches successfully.

\- Verified that the source CSV datasets load.

\- Checked the invoice status distribution.

\- Checked open receivables calculations.

\- Verified ageing bucket calculations.

\- Verified that ageing totals match open receivables.

\- Reviewed the highest overdue clients.

\- Reviewed average days to pay by client.

\- Checked monthly cash inflow and outflow calculations.

\- Reviewed data quality and reconciliation results.

\- Verified that CSV download options are displayed.



Python syntax validation was also completed successfully using:



`python -m py\_compile .\\05\_Starter\\app\_task12.py`



No syntax errors were reported.



\## 11. Evidence Screenshots



Screenshots of the working Task 12 dashboard were saved in:



`Reports/Task12\_Screenshots/`



The evidence includes:



1\. Dashboard overview.

2\. Receivables ageing analysis.

3\. Highest overdue clients.

4\. Average days to pay.

5\. Monthly cash flow.

6\. Receivables reconciliation.

7\. Data quality checks.

8\. Report download section.



Additional screenshot captures were retained where sections were captured more than once.



\## 12. Conclusion



Task 12 – Invoices, Receivables and Cash Flow Analytics has been implemented as a Streamlit dashboard.



The dashboard provides visibility into outstanding invoices, receivables ageing, overdue clients, client payment performance, and monthly cash inflows and outflows.



The ageing reconciliation was successfully validated with a difference of ₹0. Additional source-data discrepancies were identified and documented for review.



The dashboard implementation, testing and screenshot evidence are complete. Git staging, commit and push are pending.

