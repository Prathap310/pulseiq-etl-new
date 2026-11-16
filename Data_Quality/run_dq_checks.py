from pathlib import Path
import os
import sys
import csv
import re
from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def load_metric_thresholds():
    """Load numeric minimum group sizes from the project metric dictionary."""
    import pandas as pd

    path = ROOT / "03_Data" / "csv" / "metric_dictionary.csv"
    if not path.exists():
        raise FileNotFoundError(f"Metric dictionary not found: {path}")

    df = pd.read_csv(path)
    thresholds = {}

    for _, row in df.iterrows():
        value = row["minimum_group_size"]
        if pd.isna(value):
            continue

        match = re.search(r"\d+", str(value))
        if match:
            thresholds[str(row["metric_id"]).strip()] = int(match.group())

    return thresholds


CHECKS = [
    ("DQ-C01", "Payroll equals ledger", "dw.fact_payroll + dw.fact_ledger", "critical", """
        WITH p AS (
            SELECT TO_CHAR(period_end_date, 'YYYY-MM') AS period,
                   SUM(employer_cost) AS amount
            FROM dw.fact_payroll GROUP BY 1
        ),
        l AS (
            SELECT posting_period AS period, SUM(debit) AS amount
            FROM dw.fact_ledger
            WHERE account_code::text IN ('5001','5002','5003','5004','5005')
            GROUP BY 1
        )
        SELECT COALESCE(p.period,l.period) AS period
        FROM p FULL OUTER JOIN l USING (period)
        WHERE ABS(COALESCE(p.amount,0)-COALESCE(l.amount,0)) > 0.01
    """),
    ("DQ-C02", "Ledger balanced", "dw.fact_ledger", "critical", """
        SELECT entry_id FROM dw.fact_ledger
        GROUP BY entry_id
        HAVING ABS(SUM(debit)-SUM(credit)) > 0.005
    """),
    ("DQ-C03", "Unique payroll rows", "dw.fact_payroll", "critical", """
        SELECT employee_id, run_id FROM dw.fact_payroll
        GROUP BY employee_id, run_id HAVING COUNT(*) > 1
    """),
    ("DQ-C04", "No orphan employees", "dw.fact_payroll + dw.dim_employee", "critical", """
        SELECT p.payroll_item_id FROM dw.fact_payroll p
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.dim_employee d WHERE d.employee_id=p.employee_id
        )
    """),
    ("DQ-C05", "No attendance after exit month", "dw.fact_attendance_monthly + dw.dim_employee", "warning", """
        SELECT a.attendance_fact_id
        FROM dw.fact_attendance_monthly a
        JOIN dw.dim_employee d
          ON d.employee_id=a.employee_id AND d.is_current='Y'
        WHERE d.exit_date IS NOT NULL
          AND a.period_end_date >
              (DATE_TRUNC('month',d.exit_date)+INTERVAL '1 month - 1 day')::date
    """),
    ("DQ-C06", "Unpaid leave deducted", "dw.fact_attendance_monthly + dw.fact_payroll", "warning", """
        WITH a AS (
            SELECT employee_id, DATE_TRUNC('month',period_end_date)::date AS period,
                   SUM(
                       COALESCE(unpaid_absence_days,0)
                       + COALESCE(half_days_unpaid,0) * 0.5
                   ) AS unpaid_days
            FROM dw.fact_attendance_monthly
            GROUP BY 1,2
        ),
        p AS (
            SELECT employee_id, DATE_TRUNC('month',period_end_date)::date AS period,
                   SUM(COALESCE(lop_days,0)) AS lop_days
            FROM dw.fact_payroll GROUP BY 1,2
        )
        SELECT a.employee_id, a.period
        FROM a JOIN p USING (employee_id,period)
        WHERE ABS(a.unpaid_days-p.lop_days) > 0.5
    """),
    ("DQ-C07", "Invoice arithmetic", "dw.fact_invoice", "warning", """
        SELECT invoice_id FROM dw.fact_invoice
        WHERE amount_paid > total_amount OR balance_due < 0
    """),
    ("DQ-C08", "Expense arithmetic", "dw.fact_expense", "warning", """
        SELECT expense_id FROM dw.fact_expense
        WHERE ABS(total_amount-(amount_excl_gst+gst_amount)) > 0.01
    """),
    ("DQ-C09", "Task dates sensible", "dw.fact_task", "warning", """
        SELECT task_id FROM dw.fact_task
        WHERE completed_date < started_date
           OR (LOWER(TRIM(status))='done' AND completed_date IS NULL)
    """),
    ("DQ-C10", "Leave dates sensible", "dw.fact_leave", "warning", """
        SELECT leave_request_id FROM dw.fact_leave
        WHERE end_date < start_date
    """),
    ("DQ-C11", "AI feeds fresh", "dw.fact_attrition_risk + dw.fact_anomaly", "warning", """
        SELECT 'stale_attrition_prediction' AS issue, prediction_id::text AS record_id
        FROM dw.fact_attrition_risk
        WHERE as_of_date < CURRENT_DATE-7
        UNION ALL
        SELECT 'stale_anomaly_score', result_id::text
        FROM dw.fact_anomaly
        WHERE scored_at < NOW()-INTERVAL '24 hours' OR scored_at IS NULL
    """),
    ("DQ-C12", "Dimension history does not overlap", "dw.dim_employee", "critical", """
        SELECT a.employee_id
        FROM dw.dim_employee a
        JOIN dw.dim_employee b
          ON a.employee_id=b.employee_id
         AND a.employee_key < b.employee_key
         AND a.valid_from < b.valid_from
         AND COALESCE(a.valid_to,DATE '9999-12-31') >= b.valid_from
    """),
    ("DQ-C13", "Pipeline freshness", "Logs/pipeline_runs.csv", "critical", None),
    ("DQ-C14", "Minimum group size", "metric_dictionary.csv + published metric views", "critical", None),
]


def connect_db():
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError("Missing database settings: " + ", ".join(missing))

    return psycopg2.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        sslmode=os.getenv("PGSSLMODE", "require"),
        connect_timeout=15,
    )


def pipeline_bad_rows():
    """Check whether the latest ETL summary artifact is fresh."""
    summary_path = ROOT / "Logs" / "etl_summary.csv"
    if not summary_path.exists():
        return 1

    age_seconds = (
        datetime.now(timezone.utc)
        - datetime.fromtimestamp(
            summary_path.stat().st_mtime, tz=timezone.utc
        )
    ).total_seconds()

    return 1 if age_seconds < 0 or age_seconds > 24 * 60 * 60 else 0


def dq_c14_bad_groups(cur, thresholds):
    """Detect published metric values exposed below privacy thresholds."""

    exposure_queries = {
        "M01": ("dw.m01_headcount", "headcount"),
        "M02": ("dw.m02_hires", "hires"),
        "M03": ("dw.m03_exits", "exits"),
        "M04": ("dw.m04_monthly_attrition", "attrition_rate_pct"),
        "M05": ("dw.m05_rolling_12m_attrition", "rolling_12m_attrition_pct"),
        "M06": ("dw.m06_voluntary_attrition", "voluntary_attrition_rate_pct"),
        "M10": ("dw.m10_cost_per_head", "cost_per_head"),
        "M11": ("dw.m11_overtime_share", "overtime_share_pct"),
        "M12": ("dw.m12_variable_pay_share", "variable_pay_share_pct"),
        "M13": ("dw.m13_attendance_rate", "attendance_rate"),
        "M14": ("dw.m14_late_arrival_rate", "late_arrival_rate_pct"),
        "M22": ("dw.m22_task_completion_rate", "task_completion_rate_pct"),
        "M23": ("dw.m23_on_time_delivery_rate", "on_time_delivery_rate_pct"),
        "M25": ("dw.m25_average_cycle_time", "average_cycle_time_days"),
        "M27": ("dw.m27_high_risk_share", "high_risk_share_pct"),
    }

    missing = set(exposure_queries) - set(thresholds)
    if missing:
        raise RuntimeError(
            "Metric dictionary is missing thresholds: "
            + ", ".join(sorted(missing))
        )

    counts = {}
    for metric_id, (view_name, value_column) in exposure_queries.items():
        query = f"""
            SELECT COUNT(*)
            FROM {view_name}
            WHERE COALESCE(privacy_threshold_met, FALSE) = FALSE
              AND {value_column} IS NOT NULL
        """
        cur.execute(query)
        counts[metric_id] = cur.fetchone()[0]

    total = sum(counts.values())
    breakdown = ", ".join(
        f"{metric_id}={count}" for metric_id, count in counts.items()
    )
    details = (
        f"severity=critical; published_view_exposures={total}; "
        f"by_metric=[{breakdown}]; "
        "M07/M08/M09/M15 excluded pending a separate "
        "employee-level exposure-policy decision."
    )
    return total, details



def main():
    results = []
    print("PulseIQ Data Quality Gatekeeper")
    print(f"Started UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")

    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('dw.dq_results')")
                if cur.fetchone()[0] is None:
                    raise RuntimeError("dw.dq_results is missing; apply dq_results.sql first")

                for check_id, name, table_name, severity, query in CHECKS:
                    check_details = None
                    cur.execute("SAVEPOINT dq_check")
                    try:
                        if check_id == "DQ-C13":
                            bad_count = pipeline_bad_rows()
                        elif check_id == "DQ-C14":
                            thresholds = load_metric_thresholds()
                            bad_count, check_details = dq_c14_bad_groups(cur, thresholds)
                        else:
                            cur.execute(f"SELECT COUNT(*) FROM ({query}) AS bad_rows")
                            bad_count = cur.fetchone()[0]

                        status = "PASS" if bad_count == 0 else "FAIL"
                        details = check_details if check_id == "DQ-C14" and check_details else f"severity={severity}; bad_rows={bad_count}"
                    except Exception as exc:
                        cur.execute("ROLLBACK TO SAVEPOINT dq_check")
                        status = "ERROR"
                        bad_count = 0
                        details = f"severity={severity}; {type(exc).__name__}: {exc}"
                        print(f"ERROR {check_id}: {exc}")

                    results.append((check_id, name, table_name, bad_count, status, details))
                    cur.execute("""
                        INSERT INTO dw.dq_results
                            (check_id, check_name, table_name, bad_row_count, status, details)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (check_id, name, table_name, bad_count, status, details))
                    cur.execute("RELEASE SAVEPOINT dq_check")

        print("\nDATA QUALITY SUMMARY")
        print("-" * 78)
        for check_id, name, table_name, bad_count, status, details in results:
            print(f"{check_id} | {status:5} | bad rows: {bad_count:4} | {name}")
        print("-" * 78)
        print(
            f"Total: {len(results)} | PASS: {sum(r[4]=='PASS' for r in results)}"
            f" | FAIL: {sum(r[4]=='FAIL' for r in results)}"
            f" | ERROR: {sum(r[4]=='ERROR' for r in results)}"
        )
        return 1 if any(r[4] in ("FAIL", "ERROR") for r in results) else 0

    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
