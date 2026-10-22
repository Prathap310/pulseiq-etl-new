-- PulseIQ Task 4: Governed Metric Layer
-- Source schema: dw
-- M01-M06: Headcount and attrition metrics
-- Privacy thresholds use department headcount as a group-size proxy.
-- Rolling metrics are NULL until 12 monthly rows are available.

CREATE OR REPLACE VIEW dw.m01_headcount AS
SELECT
    month_start_date,
    department_id,
    CASE
        WHEN headcount_end >= 5 THEN headcount_end
        ELSE NULL
    END AS headcount,
    headcount_end >= 5 AS privacy_threshold_met
FROM dw.fact_headcount_monthly;

CREATE OR REPLACE VIEW dw.m02_hires AS
SELECT
    month_start_date,
    department_id,
    CASE
        WHEN hires >= 5 THEN hires
        ELSE NULL
    END AS hires,
    hires >= 5 AS privacy_threshold_met
FROM dw.fact_headcount_monthly;

CREATE OR REPLACE VIEW dw.m03_exits AS
SELECT
    month_start_date,
    department_id,
    CASE
        WHEN exits >= 5 THEN exits
        ELSE NULL
    END AS exits,
    exits >= 5 AS privacy_threshold_met
FROM dw.fact_headcount_monthly;

CREATE OR REPLACE VIEW dw.m04_monthly_attrition AS
SELECT
    month_start_date,
    department_id,
    CASE
        WHEN headcount_start >= 10
        THEN ROUND(
            100.0 * exits / NULLIF(headcount_start, 0),
            2
        )
        ELSE NULL
    END AS attrition_rate_pct,
    headcount_start >= 10 AS privacy_threshold_met
FROM dw.fact_headcount_monthly;

CREATE OR REPLACE VIEW dw.m05_rolling_12m_attrition AS
WITH rolling AS (
    SELECT
        month_start_date,
        department_id,
        COUNT(*) OVER w AS months_in_window,
        SUM(exits) OVER w AS exits_12m,
        AVG(headcount_end) OVER w AS avg_headcount_12m
    FROM dw.fact_headcount_monthly
    WINDOW w AS (
        PARTITION BY department_id
        ORDER BY month_start_date
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )
)
SELECT
    month_start_date,
    department_id,
    CASE
        WHEN months_in_window = 12
         AND avg_headcount_12m >= 10
        THEN ROUND(
            100.0 * exits_12m / NULLIF(avg_headcount_12m, 0),
            2
        )
        ELSE NULL
    END AS rolling_12m_attrition_pct,
    (months_in_window = 12 AND avg_headcount_12m >= 10)
        AS privacy_threshold_met
FROM rolling;

CREATE OR REPLACE VIEW dw.m06_voluntary_attrition AS
WITH rolling AS (
    SELECT
        month_start_date,
        department_id,
        COUNT(*) OVER w AS months_in_window,
        SUM(voluntary_exits) OVER w AS voluntary_exits_12m,
        AVG(headcount_end) OVER w AS avg_headcount_12m
    FROM dw.fact_headcount_monthly
    WINDOW w AS (
        PARTITION BY department_id
        ORDER BY month_start_date
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )
)
SELECT
    month_start_date,
    department_id,
    CASE
        WHEN months_in_window = 12
         AND avg_headcount_12m >= 10
        THEN ROUND(
            100.0 * voluntary_exits_12m / NULLIF(avg_headcount_12m, 0),
            2
        )
        ELSE NULL
    END AS voluntary_attrition_rate_pct,
    (months_in_window = 12 AND avg_headcount_12m >= 10)
        AS privacy_threshold_met
FROM rolling;

-- M07-M12: Payroll metrics

CREATE OR REPLACE VIEW dw.m07_gross_pay AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(SUM(gross_pay)::numeric, 2)
        ELSE NULL
    END AS gross_pay,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m08_net_pay AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(SUM(net_pay)::numeric, 2)
        ELSE NULL
    END AS net_pay,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m09_employer_payroll_cost AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(SUM(employer_cost)::numeric, 2)
        ELSE NULL
    END AS employer_cost,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m10_cost_per_head AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(
            SUM(employer_cost)::numeric /
            NULLIF(COUNT(DISTINCT employee_id), 0),
            2
        )
        ELSE NULL
    END AS cost_per_head,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m11_overtime_share AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(
            100.0 * SUM(overtime_pay) /
            NULLIF(SUM(employer_cost), 0),
            2
        )
        ELSE NULL
    END AS overtime_share_pct,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m12_variable_pay_share AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(
            100.0 * SUM(variable_pay) /
            NULLIF(SUM(gross_pay), 0),
            2
        )
        ELSE NULL
    END AS variable_pay_share_pct,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;


-- M13-M18: Attendance and financial metrics

CREATE OR REPLACE VIEW dw.m13_attendance_rate AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(
            (
                SUM(present_days) + 0.5 * SUM(half_days_unpaid)
            ) / NULLIF(SUM(scheduled_days), 0),
            2
        )
        ELSE NULL
    END AS attendance_rate,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_attendance_monthly
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m14_late_arrival_rate AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN ROUND(
            100.0 * SUM(late_arrivals) /
            NULLIF(SUM(present_days), 0),
            2
        )
        ELSE NULL
    END AS late_arrival_rate_pct,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_attendance_monthly
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m15_leave_without_pay_days AS
SELECT
    period_end_date,
    department_id,
    CASE
        WHEN COUNT(DISTINCT employee_id) >= 5
        THEN SUM(lop_days)
        ELSE NULL
    END AS leave_without_pay_days,
    COUNT(DISTINCT employee_id) >= 5 AS privacy_threshold_met
FROM dw.fact_payroll
GROUP BY period_end_date, department_id;

CREATE OR REPLACE VIEW dw.m16_revenue AS
SELECT
    d.month_start_date,
    SUM(-l.signed_amount_debit_positive) AS revenue
FROM dw.fact_ledger l
JOIN dw.dim_date d ON d.date_key = l.date_key
WHERE l.account_code::text IN ('4001', '4002', '4003', '4004')
GROUP BY d.month_start_date;

CREATE OR REPLACE VIEW dw.m17_net_profit AS
SELECT
    d.month_start_date,
    SUM(-l.signed_amount_debit_positive) AS net_profit
FROM dw.fact_ledger l
JOIN dw.dim_date d ON d.date_key = l.date_key
WHERE l.account_code::text LIKE '4%'
   OR l.account_code::text LIKE '5%'
GROUP BY d.month_start_date;

CREATE OR REPLACE VIEW dw.m18_operating_margin AS
SELECT
    p.month_start_date,
    ROUND(
        100.0 * p.net_profit / NULLIF(r.revenue, 0),
        2
    ) AS operating_margin_pct
FROM dw.m17_net_profit p
JOIN dw.m16_revenue r
    ON r.month_start_date = p.month_start_date;


-- M19-M24: Financial, receivables, and delivery metrics

CREATE OR REPLACE VIEW dw.m19_payroll_as_pct_revenue AS
SELECT
    p.month_start_date,
    ROUND(
        100.0 * p.payroll_cost / NULLIF(r.revenue, 0),
        2
    ) AS payroll_pct_revenue
FROM (
    SELECT
        d.month_start_date,
        SUM(f.employer_cost) AS payroll_cost
    FROM dw.fact_payroll f
    JOIN dw.dim_date d ON d.date_key = f.date_key
    GROUP BY d.month_start_date
) p
JOIN dw.m16_revenue r
    ON r.month_start_date = p.month_start_date;

CREATE OR REPLACE VIEW dw.m20_days_sales_outstanding AS
WITH latest_date AS (
    SELECT MAX(invoice_date) AS report_date
    FROM dw.fact_invoice
),
receivables AS (
    SELECT SUM(i.balance_due) AS closing_receivables
    FROM dw.fact_invoice i
    CROSS JOIN latest_date l
    WHERE i.invoice_date <= l.report_date
      AND i.status NOT IN ('DRAFT', 'CANCELLED')
),
recent_revenue AS (
    SELECT SUM(i.total_amount) AS revenue_90d
    FROM dw.fact_invoice i
    CROSS JOIN latest_date l
    WHERE i.invoice_date > l.report_date - INTERVAL '90 days'
      AND i.invoice_date <= l.report_date
      AND i.status NOT IN ('DRAFT', 'CANCELLED')
)
SELECT
    ROUND(
        receivables.closing_receivables * 90.0 /
        NULLIF(recent_revenue.revenue_90d, 0),
        2
    ) AS dso_days
FROM receivables
CROSS JOIN recent_revenue;

CREATE OR REPLACE VIEW dw.m21_overdue_receivables AS
WITH latest_date AS (
    SELECT MAX(invoice_date) AS report_date
    FROM dw.fact_invoice
)
SELECT
    SUM(i.balance_due) AS overdue_receivables
FROM dw.fact_invoice i
CROSS JOIN latest_date l
WHERE i.due_date < l.report_date
  AND i.status NOT IN ('DRAFT', 'CANCELLED');

CREATE OR REPLACE VIEW dw.m22_task_completion_rate AS
SELECT
    CASE
        WHEN COUNT(*) FILTER (
            WHERE status <> 'Cancelled'
        ) >= 5
        THEN ROUND(
            100.0 * COUNT(*) FILTER (WHERE status = 'Done') /
            NULLIF(
                COUNT(*) FILTER (WHERE status <> 'Cancelled'),
                0
            ),
            2
        )
        ELSE NULL
    END AS task_completion_rate_pct,
    COUNT(*) FILTER (
        WHERE status <> 'Cancelled'
    ) >= 5 AS privacy_threshold_met
FROM dw.fact_task;

CREATE OR REPLACE VIEW dw.m23_on_time_delivery_rate AS
SELECT
    CASE
        WHEN COUNT(*) FILTER (WHERE status = 'Done') >= 5
        THEN ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE status = 'Done'
                  AND completed_on_time = 'Y'
            ) /
            NULLIF(COUNT(*) FILTER (WHERE status = 'Done'), 0),
            2
        )
        ELSE NULL
    END AS on_time_delivery_rate_pct,
    COUNT(*) FILTER (WHERE status = 'Done') >= 5
        AS privacy_threshold_met
FROM dw.fact_task;

CREATE OR REPLACE VIEW dw.m24_velocity AS
SELECT
    sprint_id,
    team_id,
    SUM(story_points) FILTER (WHERE status = 'Done') AS completed_story_points
FROM dw.fact_task
GROUP BY sprint_id, team_id;


-- M25-M28: Cycle time, anomaly, risk, and forecast metrics

CREATE OR REPLACE VIEW dw.m25_average_cycle_time AS
SELECT
    team_id,
    sprint_id,
    CASE
        WHEN COUNT(*) FILTER (
            WHERE status = 'Done'
              AND started_date IS NOT NULL
              AND completed_date IS NOT NULL
        ) >= 5
        THEN ROUND(
            AVG(completed_date::date - started_date::date) FILTER (
                WHERE status = 'Done'
                  AND started_date IS NOT NULL
                  AND completed_date IS NOT NULL
            )::numeric,
            2
        )
        ELSE NULL
    END AS average_cycle_time_days,
    COUNT(*) FILTER (
        WHERE status = 'Done'
          AND started_date IS NOT NULL
          AND completed_date IS NOT NULL
    ) >= 5 AS privacy_threshold_met
FROM dw.fact_task
GROUP BY team_id, sprint_id;

CREATE OR REPLACE VIEW dw.m26_anomaly_flag_rate AS
SELECT
    source_dataset,
    period,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE flagged = 'Y') /
        NULLIF(COUNT(*), 0),
        2
    ) AS anomaly_flag_rate_pct,
    COUNT(*) AS records_scored
FROM dw.fact_anomaly
GROUP BY source_dataset, period;

CREATE OR REPLACE VIEW dw.m27_high_risk_share AS
SELECT
    department_id,
    as_of_date,
    CASE
        WHEN COUNT(*) >= 10
        THEN ROUND(
            100.0 * COUNT(*) FILTER (WHERE risk_band = 'High') /
            NULLIF(COUNT(*), 0),
            2
        )
        ELSE NULL
    END AS high_risk_share_pct,
    COUNT(*) >= 10 AS privacy_threshold_met
FROM dw.fact_attrition_risk
GROUP BY department_id, as_of_date;

-- Forecast data is company-wide (department_id = 'ALL').
-- Department-level MAPE is unavailable until department forecasts exist.
CREATE OR REPLACE VIEW dw.m28_forecast_error_mape AS
SELECT
    forecast.forecast_month,
    ROUND(
        100.0 * ABS(actual.headcount_end - forecast.forecast_value) /
        NULLIF(ABS(actual.headcount_end), 0),
        2
    ) AS forecast_error_mape_pct,
    'ALL'::varchar AS reporting_scope
FROM dw.fact_forecast forecast
LEFT JOIN dw.fact_headcount_monthly actual
    ON actual.month_start_date = forecast.forecast_month
   AND actual.department_id = 'ALL'
WHERE forecast.metric = 'headcount_end'
  AND forecast.department_id = 'ALL';

-- Governed metric catalog sourced from metric_dictionary.csv
CREATE OR REPLACE VIEW dw.metric_catalog AS
SELECT 'M01' AS metric_id, 'Headcount' AS metric_name, 'Active employees on the last day of the month (permanent and contract).' AS business_definition, 'COUNT(DISTINCT employee_id) with hire_date <= month_end AND (exit_date IS NULL OR exit_date > month_end)' AS formula, 'fact_headcount_monthly / dim_employee' AS source_table, 'Department x month' AS grain, 'Month end' AS time_period, 'HR Analytics' AS owner_team, 'count' AS unit, 'Context dependent' AS good_direction, 'Excludes CEO if you compare departments only' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M02' AS metric_id, 'Hires' AS metric_name, 'Employees whose hire_date falls in the month.' AS business_definition, 'COUNT(employee_id) where hire_date in month' AS formula, 'fact_headcount_monthly' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'HR Analytics' AS owner_team, 'count' AS unit, 'Context dependent' AS good_direction, 'Transfers are not hires' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M03' AS metric_id, 'Exits' AS metric_name, 'Employees whose exit_date falls in the month (resigned, terminated or contract ended).' AS business_definition, 'COUNT(employee_id) where exit_date in month' AS formula, 'fact_headcount_monthly' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'HR Analytics' AS owner_team, 'count' AS unit, 'Lower is better' AS good_direction, NULL AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M04' AS metric_id, 'Attrition rate (monthly)' AS metric_name, 'Share of people who left in the month.' AS business_definition, 'Exits / headcount_start x 100' AS formula, 'fact_headcount_monthly' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'HR Analytics' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, 'Very noisy for small departments' AS caveat, '10' AS minimum_group_size
UNION ALL
SELECT 'M05' AS metric_id, 'Attrition rate (rolling 12 months)' AS metric_name, 'Leavers in the last 12 months divided by average headcount over the same months.' AS business_definition, 'SUM(exits, 12m) / AVG(headcount_end, 12m) x 100' AS formula, 'fact_headcount_monthly' AS source_table, 'Department x month' AS grain, '12 months' AS time_period, 'HR Analytics' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, 'Use for headline reporting; monthly is too noisy' AS caveat, '10' AS minimum_group_size
UNION ALL
SELECT 'M06' AS metric_id, 'Voluntary attrition rate' AS metric_name, 'Same as M05 but only resignations (voluntary_exits).' AS business_definition, 'SUM(voluntary_exits, 12m) / AVG(headcount_end, 12m) x 100' AS formula, 'fact_headcount_monthly' AS source_table, 'Department x month' AS grain, '12 months' AS time_period, 'HR Analytics' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, NULL AS caveat, '10' AS minimum_group_size
UNION ALL
SELECT 'M07' AS metric_id, 'Gross pay' AS metric_name, 'Total earnings before deductions for the month.' AS business_definition, 'SUM(gross_pay)' AS formula, 'fact_payroll' AS source_table, 'Employee x month' AS grain, 'Month' AS time_period, 'Payroll' AS owner_team, 'INR' AS unit, 'Context dependent' AS good_direction, 'Includes overtime and variable pay' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M08' AS metric_id, 'Net pay' AS metric_name, 'Take-home pay after employee deductions.' AS business_definition, 'SUM(net_pay)' AS formula, 'fact_payroll' AS source_table, 'Employee x month' AS grain, 'Month' AS time_period, 'Payroll' AS owner_team, 'INR' AS unit, 'Context dependent' AS good_direction, NULL AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M09' AS metric_id, 'Payroll cost (employer cost)' AS metric_name, 'Full cost of employees to the company: gross pay plus employer PF and ESI.' AS business_definition, 'SUM(employer_cost)' AS formula, 'fact_payroll' AS source_table, 'Employee x month' AS grain, 'Month' AS time_period, 'Finance' AS owner_team, 'INR' AS unit, 'Lower is better when output is equal' AS good_direction, 'Must reconcile with ledger accounts 5001-5005' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M10' AS metric_id, 'Cost per head' AS metric_name, 'Average employer cost per paid employee.' AS business_definition, 'SUM(employer_cost) / COUNT(DISTINCT employee_id)' AS formula, 'fact_payroll' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'Finance' AS owner_team, 'INR' AS unit, 'Context dependent' AS good_direction, 'Part-month joiners lower the average' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M11' AS metric_id, 'Overtime share' AS metric_name, 'How much of payroll cost is overtime pay.' AS business_definition, 'SUM(overtime_pay) / SUM(employer_cost) x 100' AS formula, 'fact_payroll' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'Payroll' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, 'Only overtime-eligible roles earn overtime' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M12' AS metric_id, 'Variable pay share' AS metric_name, 'Bonus, incentive and award pay as a share of gross pay.' AS business_definition, 'SUM(variable_pay) / SUM(gross_pay) x 100' AS formula, 'fact_payroll' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'Payroll' AS owner_team, 'percent' AS unit, 'Context dependent' AS good_direction, 'April bonus and quarter-end incentives create spikes' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M13' AS metric_id, 'Attendance rate' AS metric_name, 'Days present (half day counts 0.5) divided by scheduled working days.' AS business_definition, '(SUM(present_days) + 0.5 x SUM(half_days_unpaid)) / SUM(scheduled_days)' AS formula, 'fact_attendance_monthly' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'HR Analytics' AS owner_team, 'ratio' AS unit, 'Higher is better' AS good_direction, 'Paid leave counts as not present' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M14' AS metric_id, 'Late arrival rate' AS metric_name, 'Late check-ins per present day.' AS business_definition, 'SUM(late_arrivals) / SUM(present_days)' AS formula, 'fact_attendance_monthly' AS source_table, 'Department x month' AS grain, 'Month' AS time_period, 'HR Analytics' AS owner_team, 'ratio' AS unit, 'Lower is better' AS good_direction, 'Work-from-home days use web check-in time' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M15' AS metric_id, 'Leave without pay days' AS metric_name, 'Unpaid absence and unpaid leave days.' AS business_definition, 'SUM(lop_days) in fact_payroll' AS formula, 'fact_payroll' AS source_table, 'Employee x month' AS grain, 'Month' AS time_period, 'Payroll' AS owner_team, 'days' AS unit, 'Lower is better' AS good_direction, 'Half-day unpaid counts 0.5' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M16' AS metric_id, 'Revenue' AS metric_name, 'Income booked in the ledger (accounts 4001-4004).' AS business_definition, '-SUM(signed_amount) for accounts 4001-4004' AS formula, 'fact_ledger' AS source_table, 'Account x month' AS grain, 'Month' AS time_period, 'Finance' AS owner_team, 'INR' AS unit, 'Higher is better' AS good_direction, 'Excludes GST (booked to 2200)' AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M17' AS metric_id, 'Net profit' AS metric_name, 'Revenue minus all expenses (4xxx less 5xxx).' AS business_definition, '-SUM(signed_amount) for accounts 4xxx and 5xxx' AS formula, 'fact_ledger' AS source_table, 'Month' AS grain, 'Month' AS time_period, 'Finance' AS owner_team, 'INR' AS unit, 'Higher is better' AS good_direction, 'Interest income (4900) is included' AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M18' AS metric_id, 'Operating margin' AS metric_name, 'Net profit as a share of revenue.' AS business_definition, 'Net profit / Revenue x 100' AS formula, 'fact_ledger' AS source_table, 'Month' AS grain, 'Month' AS time_period, 'Finance' AS owner_team, 'percent' AS unit, 'Higher is better' AS good_direction, NULL AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M19' AS metric_id, 'Payroll as % of revenue' AS metric_name, 'Share of revenue consumed by payroll cost.' AS business_definition, 'Payroll cost / Revenue x 100' AS formula, 'fact_payroll + fact_ledger' AS source_table, 'Month' AS grain, 'Month' AS time_period, 'Finance' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, 'Use ledger payroll accounts to avoid mismatch' AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M20' AS metric_id, 'Days sales outstanding (DSO)' AS metric_name, 'Average days to collect: receivables divided by credit sales x days.' AS business_definition, 'Closing receivables / revenue incl GST (last 90 days) x 90' AS formula, 'fact_invoice, fact_ledger' AS source_table, 'Month' AS grain, '90 days' AS time_period, 'Finance' AS owner_team, 'days' AS unit, 'Lower is better' AS good_direction, 'Carried-in invoices included' AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M21' AS metric_id, 'Overdue receivables' AS metric_name, 'Unpaid invoice balance past due date at the report date.' AS business_definition, 'SUM(balance_due) where due_date < report date and status not DRAFT/CANCELLED' AS formula, 'fact_invoice' AS source_table, 'Client x date' AS grain, 'Point in time' AS time_period, 'Finance' AS owner_team, 'INR' AS unit, 'Lower is better' AS good_direction, NULL AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M22' AS metric_id, 'Task completion rate' AS metric_name, 'Tasks done divided by tasks planned in the sprint (cancelled tasks excluded).' AS business_definition, 'COUNT(status = Done) / COUNT(status != Cancelled)' AS formula, 'fact_task' AS source_table, 'Team x sprint' AS grain, 'Sprint' AS time_period, 'Engineering Ops' AS owner_team, 'percent' AS unit, 'Higher is better' AS good_direction, 'Sample feed until the live board is ready' AS caveat, '5 tasks' AS minimum_group_size
UNION ALL
SELECT 'M23' AS metric_id, 'On-time delivery rate' AS metric_name, 'Done tasks completed on or before the sprint end date.' AS business_definition, 'COUNT(completed_on_time = Y) / COUNT(status = Done)' AS formula, 'fact_task' AS source_table, 'Team x sprint' AS grain, 'Sprint' AS time_period, 'Engineering Ops' AS owner_team, 'percent' AS unit, 'Higher is better' AS good_direction, NULL AS caveat, '5 tasks' AS minimum_group_size
UNION ALL
SELECT 'M24' AS metric_id, 'Velocity' AS metric_name, 'Story points completed in the sprint.' AS business_definition, 'SUM(story_points) where status = Done' AS formula, 'fact_task' AS source_table, 'Team x sprint' AS grain, 'Sprint' AS time_period, 'Engineering Ops' AS owner_team, 'points' AS unit, 'Context dependent' AS good_direction, 'Do not compare across teams' AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M25' AS metric_id, 'Average cycle time' AS metric_name, 'Days from start to completion for done tasks.' AS business_definition, 'AVG(completed_date - started_date)' AS formula, 'fact_task' AS source_table, 'Team x sprint' AS grain, 'Sprint' AS time_period, 'Engineering Ops' AS owner_team, 'days' AS unit, 'Lower is better' AS good_direction, 'Negative values are data errors' AS caveat, '5 tasks' AS minimum_group_size
UNION ALL
SELECT 'M26' AS metric_id, 'Anomaly flag rate' AS metric_name, 'Share of scored records flagged by the AI anomaly service.' AS business_definition, 'COUNT(flagged = Y) / COUNT(*)' AS formula, 'fact_anomaly' AS source_table, 'Source x month' AS grain, 'Month' AS time_period, 'AI/ML' AS owner_team, 'percent' AS unit, 'Context dependent' AS good_direction, 'Flags are leads, not proof' AS caveat, NULL AS minimum_group_size
UNION ALL
SELECT 'M27' AS metric_id, 'High-risk share' AS metric_name, 'Share of employees in the High attrition-risk band.' AS business_definition, 'COUNT(risk_band = High) / COUNT(*)' AS formula, 'fact_attrition_risk' AS source_table, 'Department' AS grain, 'Point in time' AS time_period, 'AI/ML' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, 'Show by group only; never rank named people' AS caveat, '10' AS minimum_group_size
UNION ALL
SELECT 'M28' AS metric_id, 'Forecast error (MAPE)' AS metric_name, 'Average absolute percentage error of headcount forecasts versus actuals.' AS business_definition, 'AVG(ABS(actual - forecast) / actual) x 100' AS formula, 'fact_forecast vs fact_headcount' AS source_table, 'Department x month' AS grain, 'Rolling' AS time_period, 'AI/ML' AS owner_team, 'percent' AS unit, 'Lower is better' AS good_direction, 'Needs actuals for the forecast months' AS caveat, NULL AS minimum_group_size;
