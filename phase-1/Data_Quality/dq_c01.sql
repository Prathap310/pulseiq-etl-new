-- DQ-C01: Payroll employer cost must reconcile with ledger salary expenses.
-- Bad rows are periods whose totals differ by more than INR 0.01.
-- Payroll and ledger are aggregated separately to avoid join multiplication.

WITH payroll AS (
    SELECT
        TO_CHAR(period_end_date, 'YYYY-MM') AS period,
        SUM(employer_cost) AS payroll_cost
    FROM dw.fact_payroll
    GROUP BY TO_CHAR(period_end_date, 'YYYY-MM')
),
ledger AS (
    SELECT
        posting_period AS period,
        SUM(debit) AS ledger_cost
    FROM dw.fact_ledger
    WHERE account_code::text IN ('5001', '5002', '5003', '5004', '5005')
    GROUP BY posting_period
)
SELECT
    COALESCE(p.period, l.period) AS period,
    COALESCE(p.payroll_cost, 0) AS payroll_cost,
    COALESCE(l.ledger_cost, 0) AS ledger_cost,
    COALESCE(p.payroll_cost, 0) - COALESCE(l.ledger_cost, 0) AS difference
FROM payroll p
FULL OUTER JOIN ledger l USING (period)
WHERE ABS(COALESCE(p.payroll_cost, 0) - COALESCE(l.ledger_cost, 0)) > 0.01;
