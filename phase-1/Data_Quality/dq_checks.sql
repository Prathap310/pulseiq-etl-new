-- PulseIQ Task 3: Data Quality Gatekeeper
-- DQ-C01: Payroll employer cost versus ledger salary expense.
-- DQ-C02: Ledger debits and credits balance per journal entry.
-- DQ-C03: One payroll row per employee per run.
-- DQ-C04: Every payroll employee exists in dim_employee.

-- DQ-C01
SELECT
    p.run_id,
    SUM(p.employer_cost) AS payroll_cost,
    SUM(l.credit - l.debit) AS ledger_salary_cost,
    SUM(p.employer_cost) - SUM(l.credit - l.debit) AS difference
FROM dw.fact_payroll p
JOIN dw.fact_ledger l
    ON l.posting_period = p.run_id
   AND l.account_code IN ('5001', '5002', '5003', '5004', '5005')
GROUP BY p.run_id
HAVING ABS(SUM(p.employer_cost) - SUM(l.credit - l.debit)) > 0.01;

-- DQ-C02
SELECT
    entry_id,
    SUM(debit) AS total_debits,
    SUM(credit) AS total_credits
FROM dw.fact_ledger
GROUP BY entry_id
HAVING ABS(SUM(debit) - SUM(credit)) > 0.005;

-- DQ-C03
SELECT
    employee_id,
    run_id,
    COUNT(*) AS duplicate_count
FROM dw.fact_payroll
GROUP BY employee_id, run_id
HAVING COUNT(*) > 1;

-- DQ-C04
SELECT
    p.payroll_item_id,
    p.employee_id
FROM dw.fact_payroll p
WHERE NOT EXISTS (
    SELECT 1
    FROM dw.dim_employee d
    WHERE d.employee_id = p.employee_id
);

-- DQ-C05: Attendance must not occur after the employee exit date.
SELECT
    a.attendance_fact_id,
    a.employee_id,
    a.period_end_date,
    d.exit_date
FROM dw.fact_attendance_monthly a
JOIN dw.dim_employee d
    ON d.employee_id = a.employee_id
   AND d.is_current = 'Y'
WHERE d.exit_date IS NOT NULL
  AND a.period_end_date > d.exit_date;

-- DQ-C06: Unpaid absence days must be reflected in payroll LOP days.
SELECT
    a.employee_id,
    a.period_end_date,
    a.unpaid_absence_days,
    p.lop_days
FROM dw.fact_attendance_monthly a
JOIN dw.fact_payroll p
    ON p.employee_id = a.employee_id
   AND date_trunc('month', p.period_end_date)::date =
       date_trunc('month', a.period_end_date)::date
WHERE ABS(COALESCE(a.unpaid_absence_days, 0) - COALESCE(p.lop_days, 0)) > 0.5;

-- DQ-C07: Invoice paid amount must not exceed total; balance must not be negative.
SELECT
    invoice_id,
    total_amount,
    amount_paid,
    balance_due
FROM dw.fact_invoice
WHERE amount_paid > total_amount
   OR balance_due < 0;

-- DQ-C08: Expense total must equal amount excluding GST plus GST.
SELECT
    expense_id,
    amount_excl_gst,
    gst_amount,
    total_amount
FROM dw.fact_expense
WHERE ABS(total_amount - (amount_excl_gst + gst_amount)) > 0.01;

-- DQ-C09: Completed date must not precede start date; Done tasks need a completion date.
SELECT
    task_id,
    status,
    started_date,
    completed_date
FROM dw.fact_task
WHERE completed_date < started_date
   OR (LOWER(status) = 'done' AND completed_date IS NULL);

-- DQ-C10: Leave end date must not precede start date.
SELECT
    leave_request_id,
    start_date,
    end_date
FROM dw.fact_leave
WHERE end_date < start_date;

-- DQ-C11: Attrition predictions must be no more than 7 days older than the latest as-of date.
SELECT
    prediction_id,
    as_of_date
FROM dw.fact_attrition_risk
WHERE as_of_date < (
    SELECT MAX(as_of_date) - 7
    FROM dw.fact_attrition_risk
);

-- DQ-C12: Employee history versions must not overlap.
SELECT
    a.employee_id,
    a.employee_key AS earlier_employee_key,
    b.employee_key AS later_employee_key,
    a.valid_from AS earlier_valid_from,
    a.valid_to AS earlier_valid_to,
    b.valid_from AS later_valid_from,
    b.valid_to AS later_valid_to
FROM dw.dim_employee a
JOIN dw.dim_employee b
    ON a.employee_id = b.employee_id
   AND a.employee_key < b.employee_key
   AND a.valid_from < b.valid_from
   AND COALESCE(a.valid_to, DATE '9999-12-31') >= b.valid_from;

-- DQ-C13: Latest successful pipeline load must be within 24 hours.
-- This check requires etl_run_log to exist and contain status and finished_at.
SELECT
    MAX(finished_at) AS latest_successful_load
FROM etl_run_log
WHERE LOWER(status) = 'success'
HAVING MAX(finished_at) < NOW() - INTERVAL '24 hours'
    OR MAX(finished_at) IS NULL;

-- DQ-C14: Example privacy guard for a department-month employee aggregate.
-- Use the metric's minimum group size from the metric dictionary.
SELECT
    department_id,
    date_key,
    COUNT(DISTINCT employee_id) AS employee_count
FROM dw.fact_payroll
GROUP BY department_id, date_key
HAVING COUNT(DISTINCT employee_id) < 5;
