
-- ============================================================
-- Task 10: Budget vs Actual + KPI Targets
-- ============================================================
-- Creates Task 10-specific warehouse tables and views.
-- Does not modify Tasks 1-9 tables or metric views.
--
-- Payroll variance sign rule:
--   variance = actual payroll - budget payroll
--   Positive variance = overspend
--   Negative variance = underspend
--
-- Privacy rule:
--   Payroll actuals and variance metrics are exposed only when
--   at least 5 distinct employees exist in the department-month.
--
-- KPI traffic-light tolerance rules must be confirmed before
-- assigning yellow status. Do not invent tolerance values.
-- ============================================================

CREATE TABLE IF NOT EXISTS dw.budget_payroll_dept_month (
    department_id VARCHAR(20) NOT NULL,
    month DATE NOT NULL,
    budget_payroll_cost NUMERIC(16,2) NOT NULL
        CHECK (budget_payroll_cost >= 0),
    PRIMARY KEY (department_id, month)
);

CREATE TABLE IF NOT EXISTS dw.kpi_targets (
    month DATE NOT NULL,
    department_id VARCHAR(20) NOT NULL,
    attendance_rate_target NUMERIC(8,4),
    overtime_share_target_pct NUMERIC(8,2),
    attrition_monthly_target_pct NUMERIC(8,2),
    task_completion_target_pct NUMERIC(8,2),
    PRIMARY KEY (department_id, month)
);

-- ------------------------------------------------------------
-- Budget vs actual payroll
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW dw.task10_budget_vs_actual AS
WITH payroll_actuals AS (
    SELECT
        period_end_date,
        department_id,
        ROUND(SUM(employer_cost)::NUMERIC, 2)
            AS raw_actual_payroll_cost,
        COUNT(DISTINCT employee_id) >= 5
            AS privacy_threshold_met
    FROM dw.fact_payroll
    GROUP BY period_end_date, department_id
)
SELECT
    b.department_id,
    b.month,
    b.budget_payroll_cost,

    CASE
        WHEN COALESCE(a.privacy_threshold_met, FALSE)
        THEN a.raw_actual_payroll_cost
        ELSE NULL
    END AS actual_payroll_cost,

    CASE
        WHEN COALESCE(a.privacy_threshold_met, FALSE)
        THEN ROUND(
            a.raw_actual_payroll_cost - b.budget_payroll_cost,
            2
        )
        ELSE NULL
    END AS variance,

    CASE
        WHEN COALESCE(a.privacy_threshold_met, FALSE)
         AND b.budget_payroll_cost <> 0
        THEN ROUND(
            100.0 * (
                a.raw_actual_payroll_cost - b.budget_payroll_cost
            ) / b.budget_payroll_cost,
            2
        )
        ELSE NULL
    END AS variance_pct,

    COALESCE(a.privacy_threshold_met, FALSE)
        AS privacy_threshold_met

FROM dw.budget_payroll_dept_month b
LEFT JOIN payroll_actuals a
    ON a.department_id = b.department_id
   AND a.period_end_date =
       (b.month + INTERVAL '1 month - 1 day')::DATE;

-- ------------------------------------------------------------
-- Departments ranked by positive monthly overspend
-- Ranking is calculated separately for each month.
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW dw.task10_overspend_ranking AS
SELECT
    department_id,
    month,
    budget_payroll_cost,
    actual_payroll_cost,
    variance,
    variance_pct,
    RANK() OVER (
        PARTITION BY month
        ORDER BY variance DESC NULLS LAST
    ) AS overspend_rank
FROM dw.task10_budget_vs_actual
WHERE variance IS NOT NULL
  AND variance > 0;

-- ------------------------------------------------------------
-- KPI targets are loaded separately.
-- Actual KPI status scoring is not assigned here because
-- yellow tolerances have not yet been confirmed.
-- Task-completion actuals must not be treated as department-
-- month values until a valid department-month metric exists.
-- ------------------------------------------------------------
