# PulseIQ Custom KPI Builder

## 1. Purpose

The Custom KPI Builder currently supports governed KPI definition validation,
SQL generation, and read-only preview using warehouse tables. Approval helpers
are implemented, but persistent approval and administrator authentication are
not yet integrated into the Streamlit page.

Implementation:
- `Src/kpi_builder.py`
- `tests/test_kpi_builder.py`

## 2. Metric definition format

Each KPI definition uses the following fields:

| Field | Description |
|---|---|
| name | Unique, readable KPI name |
| description | Business definition |
| source_table | Whitelisted warehouse source |
| measure | Aggregation or ratio definition |
| filters | Optional validated filters |
| group_by | Allowed grouping columns |
| time_grain | Supported reporting grain |
| owner | Responsible team |
| status | draft or approved |
| version | Positive integer version |

Example:

```json
{
  "name": "Unpaid leave days by month",
  "description": "Sum of unpaid leave days by department and month.",
  "source_table": "fact_payroll",
  "measure": {
    "aggregation": "sum",
    "column": "lop_days"
  },
  "filters": [],
  "group_by": ["department_id", "period_end_date"],
  "time_grain": "month",
  "owner": "Payroll",
  "status": "draft",
  "version": 1
}
```

## 3. Supported aggregations

- sum
- count
- count_distinct
- avg
- ratio using a numerator and denominator

Ratio calculations use NULLIF to prevent division-by-zero errors.

## 4. Supported filters

Allowed operators:

- `=`
- `in`
- `between`

Filter values are passed as database parameters. User-supplied SQL,
unknown tables, and unknown columns are not accepted.

## 5. Five example KPIs

1. Overtime hours per head
   - Source: fact_payroll
   - Calculation: SUM(overtime_hours_paid) / COUNT(DISTINCT employee_id)
   - Grouping: department and month

2. Unpaid leave days by month
   - Source: fact_payroll
   - Calculation: SUM(lop_days)
   - Grouping: department and month

3. Employer cost per head
   - Source: fact_payroll
   - Calculation: SUM(employer_cost) / COUNT(DISTINCT employee_id)
   - Grouping: department and month

4. Late arrivals per present day
   - Source: fact_attendance_monthly
   - Calculation: SUM(late_arrivals) / SUM(present_days)
   - Grouping: department and month

5. Overdue receivables by client
   - Source: fact_invoice
   - Calculation: SUM(balance_due)
   - Conditions: due_date before the latest invoice date in the source data;
     exclude DRAFT and CANCELLED
   - Grouping: client

## 6. Privacy and validation

- Payroll and attendance groups require at least five distinct employees.
- Invoice groups use an explicit configurable minimum of five distinct invoices.
- Groups below the threshold are excluded.
- The query also returns privacy_group_size and privacy_threshold_met.
- The invoice threshold is an implementation policy, not a value supplied by metric_dictionary.csv.
- Source tables and columns are restricted to the code whitelist.

## 7. Admin workflow

1. Create a KPI definition with status draft.
2. Validate the definition.
3. Preview the generated query results.
4. Review the calculation and privacy threshold.
5. Approve the definition with an approver identity.
6. Expose only approved definitions to dashboard/API consumers.

The current implementation provides validation, query preview,
and approval helpers. The Streamlit page is read-only. Persistent KPI
definition storage, authenticated administrator approval, and dashboard/API
publication remain pending.

## 8. Security test coverage

`tests/test_kpi_builder.py` checks:

- Five example definitions.
- SQL generation for all examples.
- Parameterized filter values.
- SQL injection attempts.
- Unknown tables and columns.
- Invalid operators and aggregations.
- Division-by-zero protection.
- Invoice overdue conditions and privacy threshold.
- Approval identity and approved-only filtering.

## 9. Test command

```powershell
python -m pytest .\tests\test_kpi_builder.py -v
```

Latest recorded result: 12 passed, 10 subtests passed.
