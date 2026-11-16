import csv
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "03_Data" / "csv"
LOGS = ROOT / "Logs"

# Dimensions first, then facts. Parent tables precede dependent tables.
TABLES = [
    ("dim_account", ["account_code"]),
    ("dim_client", ["client_id"]),
    ("dim_date", ["date_key"]),
    ("dim_department", ["department_id"]),
    ("dim_leave_type", ["leave_type_code"]),
    ("dim_location", ["work_location"]),
    ("dim_role", ["role_id"]),
    ("dim_sprint", ["sprint_id"]),
    ("dim_team", ["team_id"]),
    ("dim_vendor", ["vendor_id"]),
    ("dim_employee", ["employee_key"]),
    ("fact_anomaly", ["result_id"]),
    ("fact_attendance_monthly", ["attendance_fact_id"]),
    ("fact_attrition_risk", ["prediction_id"]),
    ("fact_expense", ["expense_id"]),
    ("fact_forecast", ["forecast_id"]),
    ("fact_headcount_monthly", ["date_key", "department_id"]),
    ("fact_invoice", ["invoice_id"]),
    ("fact_invoice_payment", ["payment_id"]),
    ("fact_leave", ["leave_request_id"]),
    ("fact_ledger", ["line_id"]),
    ("fact_payroll", ["payroll_item_id"]),
    ("fact_task", ["task_id"]),
]


def connect():
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing database environment variables: " + ", ".join(missing))

    return psycopg2.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        sslmode=os.getenv("PGSSLMODE", "require"),
        connect_timeout=15,
    )


def load_table(cur, table, primary_key):
    path = SOURCE / f"{table}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Required source file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        headers = next(reader, None)
        if not headers:
            raise ValueError(f"{path.name} is empty")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path.name} contains duplicate column names")

        missing_keys = [key for key in primary_key if key not in headers]
        if missing_keys:
            raise ValueError(f"{path.name} is missing key columns: {missing_keys}")

        cur.execute("DROP TABLE IF EXISTS stage_load")
        cur.execute(
            sql.SQL("CREATE TEMP TABLE stage_load (LIKE dw.{} INCLUDING DEFAULTS) ON COMMIT DROP")
            .format(sql.Identifier(table))
        )
        # Allow YYYY-MM forecast training values to be copied before date conversion.
        if table == "fact_forecast" and "trained_through" in headers:
            cur.execute("ALTER TABLE stage_load ALTER COLUMN trained_through TYPE text")

        copy_sql = sql.SQL("COPY stage_load ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')").format(
            sql.SQL(", ").join(map(sql.Identifier, headers))
        )
        handle.seek(0)
        cur.copy_expert(copy_sql.as_string(cur), handle)

        # Source account parent codes were stored as values such as 1000.0;
        # normalize those identifiers to match dim_account.account_code.
        if table == "dim_account" and "parent_code" in headers:
            cur.execute("""
                UPDATE stage_load
                SET parent_code = regexp_replace(parent_code::text, '\\.0$', '')
                WHERE parent_code::text ~ '^[0-9]+\\.0$'
            """)

        # Convert forecast training month (YYYY-MM) to a valid month-end date.
        if table == "fact_forecast" and "trained_through" in headers:
            cur.execute("""
                UPDATE stage_load
                SET trained_through =
                    ((to_date(trained_through || '-01', 'YYYY-MM-DD')
                      + INTERVAL '1 month - 1 day')::date)::text
                WHERE trained_through ~ '^\\d{4}-\\d{2}$'
            """)
            cur.execute("""
                ALTER TABLE stage_load
                ALTER COLUMN trained_through TYPE date
                USING trained_through::date
            """)

        columns = sql.SQL(", ").join(map(sql.Identifier, headers))
        keys = sql.SQL(", ").join(map(sql.Identifier, primary_key))
        non_keys = [column for column in headers if column not in primary_key]

        if non_keys:
            updates = sql.SQL(", ").join(
                sql.SQL("{} = EXCLUDED.{}").format(
                    sql.Identifier(column), sql.Identifier(column)
                )
                for column in non_keys
            )
            conflict = sql.SQL("ON CONFLICT ({}) DO UPDATE SET {}").format(keys, updates)
        else:
            conflict = sql.SQL("ON CONFLICT ({}) DO NOTHING").format(keys)

        statement = sql.SQL(
            "INSERT INTO dw.{} ({}) SELECT {} FROM stage_load {}"
        ).format(
            sql.Identifier(table),
            columns,
            columns,
            conflict,
        )
        cur.execute(statement)
        return cur.rowcount



def ensure_special_dimensions(cur):
    """Create dimension members required by aggregate and unknown-key facts."""
    from datetime import date
    import calendar

    cur.execute("""
        INSERT INTO dw.dim_department
            (department_id, department_name, cost_center, description, is_leadership)
        VALUES ('ALL', 'All Departments', NULL,
                'Aggregate across all departments', 'N')
        ON CONFLICT (department_id) DO NOTHING
    """)

    cur.execute("""
        INSERT INTO dw.dim_employee
            (employee_key, employee_id, full_name, valid_from, is_current)
        VALUES (-1, 'UNKNOWN', 'Unknown Employee', DATE '1900-01-01', 'N')
        ON CONFLICT (employee_key) DO NOTHING
    """)

    for year, month in [(2027, 1), (2027, 2), (2027, 3)]:
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        month_start = date(year, month, 1)
        fiscal_month = ((month - 4) % 12) + 1
        fiscal_start = year if month >= 4 else year - 1
        fiscal_end = str(fiscal_start + 1)[-2:]
        fiscal_quarter = f"Q{((fiscal_month - 1) // 3) + 1}"

        cur.execute("""
            INSERT INTO dw.dim_date (
                date_key, date, year, quarter, month_number, month_name,
                year_month, week_of_year, day_of_week, is_weekend,
                is_holiday, is_working_day, financial_year, fiscal_quarter,
                fiscal_month_number, is_month_end, month_start_date, month_end_date
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                'N', %s, %s, %s, %s, 'Y', %s, %s
            )
            ON CONFLICT (date_key) DO NOTHING
        """, (
            int(month_end.strftime("%Y%m%d")),
            month_end,
            year,
            ((month - 1) // 3) + 1,
            month,
            month_end.strftime("%B"),
            month_end.strftime("%Y-%m"),
            month_end.isocalendar().week,
            month_end.strftime("%A"),
            "Y" if month_end.weekday() >= 5 else "N",
            "N" if month_end.weekday() >= 5 else "Y",
            f"FY{fiscal_start}-{fiscal_end}",
            fiscal_quarter,
            fiscal_month,
            month_start,
            month_end,
        ))


def main():
    connection = connect()
    results = []
    try:
        with connection:
            with connection.cursor() as cur:
                # Load all dimensions before facts.
                for table, primary_key in TABLES:
                    if table.startswith("fact_"):
                        continue
                    affected = load_table(cur, table, primary_key)
                    results.append((table, affected))
                    print(f"{table}: {affected} rows inserted or updated")

                ensure_special_dimensions(cur)
                print("Special dimension members and forecast dates verified")

                # Load facts after all required dimension members exist.
                for table, primary_key in TABLES:
                    if not table.startswith("fact_"):
                        continue
                    affected = load_table(cur, table, primary_key)
                    results.append((table, affected))
                    print(f"{table}: {affected} rows inserted or updated")

        LOGS.mkdir(parents=True, exist_ok=True)
        summary = LOGS / "etl_summary.csv"
        with summary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["table_name", "rows_inserted_or_updated"])
            writer.writerows(results)

        print(f"Production load completed: {len(results)} tables")
        print(f"ETL summary written: {summary}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PRODUCTION LOAD FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

