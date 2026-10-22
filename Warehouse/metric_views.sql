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
-- M07, M08, M09, and M15 use Department x month in the implemented
-- views to retain group-level privacy. The metric dictionary specifies
-- Employee x month for these four metrics; this discrepancy requires
-- review by the relevant business owners.

CREATE OR REPLACE VIEW dw.metric_catalog AS
SELECT 'M01' AS metric_id, 'Headcount' AS metric_name, 'Active employees on the last day of the month (permanent and contract).' AS business_definition, 'COUNT(DISTINCT employee_id) with hire_date <= month_end AND (exit_date IS NULL OR exit_date > month_end)' AS formula, 'fact_headcount_monthly / dim_employee' AS source_table, 'Department x month' AS grain, 'Month end' AS time_period, 'HR Analytics' AS owner_team, 'count' AS unit, 'Context dependent' AS good_direction, 'Excludes CEO if you compare departments only' AS caveat, '5' AS minimum_group_size
UNION ALL
SELECT 'M02', 'Hires', 'Employees whose hire_date falls in the month.', 'COUNT(employee_id) where hire_date in month', 'fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'count', 'Context dependent', 'Transfers are not hires', '5'
UNION ALL
SELECT 'M03', 'Exits', 'Employees whose exit_date falls in the month (resigned, terminated or contract ended).', 'COUNT(employee_id) where exit_date in month', 'fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'count', 'Lower is better', NULL, '5'
UNION ALL
SELECT 'M04', 'Attrition rate (monthly)', 'Share of people who left in the month.', 'Exits / headcount_start x 100', 'fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'percent', 'Lower is better', 'Very noisy for small departments', '10'
UNION ALL
SELECT 'M05', 'Attrition rate (rolling 12 months)', 'Leavers in the last 12 months divided by average headcount over the same months.', 'SUM(exits, 12m) / AVG(headcount_end, 12m) x 100', 'fact_headcount_monthly', 'Department x month', '12 months', 'HR Analytics', 'percent', 'Lower is better', 'Use for headline reporting; monthly is too noisy', '10'
UNION ALL
SELECT 'M06', 'Voluntary attrition rate', 'Same as M05 but only resignations (voluntary_exits).', 'SUM(voluntary_exits, 12m) / AVG(headcount_end, 12m) x 100', 'fact_headcount_monthly', 'Department x month', '12 months', 'HR Analytics', 'percent', 'Lower is better', NULL, '10'
UNION ALL
SELECT 'M07', 'Gross pay', 'Total earnings before deductions for the month.', 'SUM(gross_pay)', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'INR', 'Context dependent', 'Includes overtime and variable pay. Metric dictionary specifies Employee x month; current view aggregates by department and month to retain group-level privacy.', '5'
UNION ALL
SELECT 'M08', 'Net pay', 'Take-home pay after employee deductions.', 'SUM(net_pay)', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'INR', 'Context dependent', 'Metric dictionary specifies Employee x month; current view aggregates by department and month to retain group-level privacy.', '5'
UNION ALL
SELECT 'M09', 'Payroll cost (employer cost)', 'Full cost of employees to the company: gross pay plus employer PF and ESI.', 'SUM(employer_cost)', 'fact_payroll', 'Department x month', 'Month', 'Finance', 'INR', 'Lower is better when output is equal', 'Must reconcile with ledger accounts 5001-5005. Metric dictionary specifies Employee x month; current view aggregates by department and month to retain group-level privacy.', '5'
UNION ALL
SELECT 'M10', 'Cost per head', 'Average employer cost per paid employee.', 'SUM(employer_cost) / COUNT(DISTINCT employee_id)', 'fact_payroll', 'Department x month', 'Month', 'Finance', 'INR', 'Context dependent', 'Part-month joiners lower the average', '5'
UNION ALL
SELECT 'M11', 'Overtime share', 'How much of payroll cost is overtime pay.', 'SUM(overtime_pay) / SUM(employer_cost) x 100', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'percent', 'Lower is better', 'Only overtime-eligible roles earn overtime', '5'
UNION ALL
SELECT 'M12', 'Variable pay share', 'Bonus, incentive and award pay as a share of gross pay.', 'SUM(variable_pay) / SUM(gross_pay) x 100', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'percent', 'Context dependent', 'April bonus and quarter-end incentives create spikes', '5'
UNION ALL
SELECT 'M13', 'Attendance rate', 'Days present (half day counts 0.5) divided by scheduled working days.', '(SUM(present_days) + 0.5 x SUM(half_days_unpaid)) / SUM(scheduled_days)', 'fact_attendance_monthly', 'Department x month', 'Month', 'HR Analytics', 'ratio', 'Higher is better', 'Paid leave counts as not present', '5'
UNION ALL
SELECT 'M14', 'Late arrival rate', 'Late check-ins per present day.', 'SUM(late_arrivals) / SUM(present_days)', 'fact_attendance_monthly', 'Department x month', 'Month', 'HR Analytics', 'ratio', 'Lower is better', 'Work-from-home days use web check-in time', '5'
UNION ALL
SELECT 'M15', 'Leave without pay days', 'Unpaid absence and unpaid leave days.', 'SUM(lop_days) in fact_payroll', 'fact_payroll', 'Department x month', 'Month', 'Payroll', 'days', 'Lower is better', 'Half-day unpaid counts 0.5. Metric dictionary specifies Employee x month; current view aggregates by department and month to retain group-level privacy.', '5'
UNION ALL
SELECT 'M16', 'Revenue', 'Income booked in the ledger (accounts 4001-4004).', '-SUM(signed_amount) for accounts 4001-4004', 'fact_ledger', 'Account x month', 'Month', 'Finance', 'INR', 'Higher is better', 'Excludes GST (booked to 2200)', NULL
UNION ALL
SELECT 'M17', 'Net profit', 'Revenue minus all expenses (4xxx less 5xxx).', '-SUM(signed_amount) for accounts 4xxx and 5xxx', 'fact_ledger', 'Month', 'Month', 'Finance', 'INR', 'Higher is better', 'Interest income (4900) is included', NULL
UNION ALL
SELECT 'M18', 'Operating margin', 'Net profit as a share of revenue.', 'Net profit / Revenue x 100', 'fact_ledger', 'Month', 'Month', 'Finance', 'percent', 'Higher is better', NULL, NULL
UNION ALL
SELECT 'M19', 'Payroll as % of revenue', 'Share of revenue consumed by payroll cost.', 'Payroll cost / Revenue x 100', 'fact_payroll + fact_ledger', 'Month', 'Month', 'Finance', 'percent', 'Lower is better', 'Use ledger payroll accounts to avoid mismatch', NULL
UNION ALL
SELECT 'M20', 'Days sales outstanding (DSO)', 'Average days to collect: receivables divided by credit sales x days.', 'Closing receivables / revenue incl GST (last 90 days) x 90', 'fact_invoice, fact_ledger', 'Month', '90 days', 'Finance', 'days', 'Lower is better', 'Carried-in invoices included', NULL
UNION ALL
SELECT 'M21', 'Overdue receivables', 'Unpaid invoice balance past due date at the report date.', 'SUM(balance_due) where due_date < report date and status not DRAFT/CANCELLED', 'fact_invoice', 'Client x date', 'Point in time', 'Finance', 'INR', 'Lower is better', NULL, NULL
UNION ALL
SELECT 'M22', 'Task completion rate', 'Tasks done divided by tasks planned in the sprint (cancelled tasks excluded).', 'COUNT(status = Done) / COUNT(status != Cancelled)', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'percent', 'Higher is better', 'Sample feed until the live board is ready', '5 tasks'
UNION ALL
SELECT 'M23', 'On-time delivery rate', 'Done tasks completed on or before the sprint end date.', 'COUNT(completed_on_time = Y) / COUNT(status = Done)', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'percent', 'Higher is better', NULL, '5 tasks'
UNION ALL
SELECT 'M24', 'Velocity', 'Story points completed in the sprint.', 'SUM(story_points) where status = Done', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'points', 'Context dependent', 'Do not compare across teams', NULL
UNION ALL
SELECT 'M25', 'Average cycle time', 'Days from start to completion for done tasks.', 'AVG(completed_date - started_date)', 'fact_task', 'Team x sprint', 'Sprint', 'Engineering Ops', 'days', 'Lower is better', 'Negative values are data errors', '5 tasks'
UNION ALL
SELECT 'M26', 'Anomaly flag rate', 'Share of scored records flagged by the AI anomaly service.', 'COUNT(flagged = Y) / COUNT(*)', 'fact_anomaly', 'Source x month', 'Month', 'AI/ML', 'percent', 'Context dependent', 'Flags are leads, not proof', NULL
UNION ALL
SELECT 'M27', 'High-risk share', 'Share of employees in the High attrition-risk band.', 'COUNT(risk_band = High) / COUNT(*)', 'fact_attrition_risk', 'Department', 'Point in time', 'AI/ML', 'percent', 'Lower is better', 'Show by group only; never rank named people', '10'
UNION ALL
SELECT 'M28', 'Forecast error (MAPE)', 'Average absolute percentage error of headcount forecasts versus actuals.', 'AVG(ABS(actual - forecast) / actual) x 100', 'fact_forecast vs fact_headcount', 'Department x month', 'Rolling', 'AI/ML', 'percent', 'Lower is better', 'Needs actuals for the forecast months', NULL;
