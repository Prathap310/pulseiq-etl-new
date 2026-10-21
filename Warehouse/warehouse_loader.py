
import argparse
import csv
import os
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_values

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FOLDER = os.path.join(BASE_DIR, "03_Data", "csv")
ENV_FILE = os.path.join(BASE_DIR, ".env")
SCHEMA = "dw"
BATCH_SIZE = 1000

load_dotenv(ENV_FILE)

LOAD_ORDER = [
    "dim_department", "dim_date", "dim_location", "dim_leave_type",
    "dim_client", "dim_account", "dim_sprint", "dim_role",
    "dim_employee", "dim_team", "dim_vendor", "fact_anomaly",
    "fact_attendance_monthly", "fact_attrition_risk", "fact_expense",
    "fact_forecast", "fact_headcount_monthly", "fact_invoice",
    "fact_invoice_payment", "fact_leave", "fact_ledger",
    "fact_payroll", "fact_task",
]

PRIMARY_KEYS = {
    "dim_account": ["account_code"],
    "dim_client": ["client_id"],
    "dim_date": ["date_key"],
    "dim_department": ["department_id"],
    "dim_employee": ["employee_key"],
    "dim_leave_type": ["leave_type_code"],
    "dim_location": ["work_location"],
    "dim_role": ["role_id"],
    "dim_sprint": ["sprint_id"],
    "dim_team": ["team_id"],
    "dim_vendor": ["vendor_id"],
    "fact_anomaly": ["result_id"],
    "fact_attendance_monthly": ["attendance_fact_id"],
    "fact_attrition_risk": ["prediction_id"],
    "fact_expense": ["expense_id"],
    "fact_forecast": ["forecast_id"],
    "fact_headcount_monthly": ["date_key", "department_id"],
    "fact_invoice": ["invoice_id"],
    "fact_invoice_payment": ["payment_id"],
    "fact_leave": ["leave_request_id"],
    "fact_ledger": ["line_id"],
    "fact_payroll": ["payroll_item_id"],
    "fact_task": ["task_id"],
}


def normalize_account_code(value):
    if value is None:
        return None
    value = value.strip()
    if value.endswith(".0") and value[:-2].isdigit():
        return value[:-2]
    return value


def normalize_value(table, column, value, data_type, line_number):
    """Normalize known source formats using the destination column type."""
    if value is None or value == "":
        return None

    value = value.strip()

    if table == "dim_account" and column in ("account_code", "parent_code"):
        return normalize_account_code(value)

    if (
        table == "fact_forecast"
        and column == "trained_through"
        and len(value) == 7
        and value[4] == "-"
    ):
        value = value + "-01"

    if data_type in ("smallint", "integer", "bigint"):
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(
                f"{table}.{column}, CSV line {line_number}: "
                f"{value!r} is not an integer."
            ) from error

        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError(
                f"{table}.{column}, CSV line {line_number}: "
                f"{value!r} is not a whole number."
            )

        return int(number)

    if data_type == "boolean":
        normalized = value.lower()
        if normalized in ("true", "t", "1", "yes", "y"):
            return True
        if normalized in ("false", "f", "0", "no", "n"):
            return False
        raise ValueError(
            f"{table}.{column}, CSV line {line_number}: "
            f"unrecognized boolean {value!r}."
        )

    # Let PostgreSQL parse numeric, date, timestamp and other types.
    return value


def get_connection(read_only=True):
    required = [
        "PGHOST", "PGPORT", "PGDATABASE",
        "PGUSER", "PGPASSWORD", "PGSCHEMA",
    ]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(
            "Missing settings in .env: " + ", ".join(missing)
        )

    if os.getenv("PGSCHEMA") != SCHEMA:
        raise ValueError("Expected PGSCHEMA=dw.")

    args = {
        "host": os.getenv("PGHOST"),
        "port": os.getenv("PGPORT"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
        "connect_timeout": 10,
    }

    if read_only:
        args["options"] = "-c default_transaction_read_only=on"

    return psycopg2.connect(**args)


def get_csv_files():
    if not os.path.isdir(CSV_FOLDER):
        raise FileNotFoundError(f"CSV folder not found: {CSV_FOLDER}")

    return sorted(
        name for name in os.listdir(CSV_FOLDER)
        if name.endswith(".csv")
        and name.startswith(("dim_", "fact_"))
    )


def get_database_columns(cursor, table):
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (SCHEMA, table),
    )
    return dict(cursor.fetchall())


def read_source_table(cursor, table):
    path = os.path.join(CSV_FOLDER, table + ".csv")

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing source CSV: {path}")

    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"Missing CSV header: {table}")

        columns = reader.fieldnames

        if len(columns) != len(set(columns)):
            raise ValueError(f"Duplicate column names in CSV: {table}")

        db_types = get_database_columns(cursor, table)

        if not db_types:
            raise ValueError(f"PostgreSQL table not found: {SCHEMA}.{table}")

        if set(columns) != set(db_types):
            raise ValueError(
                f"Column names differ for {table}.\n"
                f"Missing in DB: {sorted(set(columns) - set(db_types))}\n"
                f"Missing in CSV: {sorted(set(db_types) - set(columns))}"
            )

        keys = PRIMARY_KEYS[table]
        if any(key not in columns for key in keys):
            raise ValueError(f"{table} is missing primary-key columns: {keys}")

        rows = []
        seen_keys = set()

        for line_number, record in enumerate(reader, start=2):
            normalized = {}
            for column in columns:
                normalized[column] = normalize_value(
                    table,
                    column,
                    record[column],
                    db_types[column],
                    line_number,
                )

            key_values = tuple(normalized[key] for key in keys)

            if any(value is None or str(value).strip() == "" for value in key_values):
                raise ValueError(
                    f"{table}: blank primary key at CSV line {line_number}"
                )

            if key_values in seen_keys:
                raise ValueError(
                    f"{table}: duplicate primary key {key_values} "
                    f"at CSV line {line_number}"
                )

            seen_keys.add(key_values)
            rows.append(tuple(normalized[column] for column in columns))

    return columns, rows


def validate_account_parents(source_tables):
    columns, rows = source_tables["dim_account"]
    code_index = columns.index("account_code")
    parent_index = columns.index("parent_code")

    account_codes = {
        row[code_index] for row in rows if row[code_index] is not None
    }

    missing = sorted({
        row[parent_index]
        for row in rows
        if row[parent_index] is not None
        and row[parent_index] not in account_codes
    })

    if missing:
        raise ValueError(f"dim_account parent codes not found: {missing}")

    print(
        "VALID: dim_account parent references | "
        f"{len(account_codes)} account codes checked"
    )


def build_upsert_query(connection, table, columns):
    keys = PRIMARY_KEYS[table]
    updates = [column for column in columns if column not in keys]

    if not updates:
        action = sql.SQL("DO NOTHING")
    else:
        assignments = sql.SQL(", ").join(
            sql.SQL("{} = EXCLUDED.{}").format(
                sql.Identifier(column), sql.Identifier(column)
            )
            for column in updates
        )
        differences = sql.SQL(" OR ").join(
            sql.SQL("target.{} IS DISTINCT FROM EXCLUDED.{}").format(
                sql.Identifier(column), sql.Identifier(column)
            )
            for column in updates
        )
        action = sql.SQL("DO UPDATE SET {} WHERE {}").format(
            assignments, differences
        )

    query = sql.SQL(
        "INSERT INTO {}.{} AS target ({}) VALUES %s "
        "ON CONFLICT ({}) {}"
    ).format(
        sql.Identifier(SCHEMA),
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        sql.SQL(", ").join(sql.Identifier(k) for k in keys),
        action,
    )
    return query.as_string(connection)


def get_table_count(cursor, table):
    cursor.execute(
        sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
            sql.Identifier(SCHEMA), sql.Identifier(table)
        )
    )
    return cursor.fetchone()[0]


def verify_preserved_members(cursor):
    checks = [
        (
            "future dates",
            """
            SELECT COUNT(*) FROM dw.dim_date
            WHERE date > DATE '2026-12-31'
            """,
            lambda count: count >= 90,
        ),
        (
            "ALL department",
            """
            SELECT COUNT(*) FROM dw.dim_department
            WHERE department_id = 'ALL'
            """,
            lambda count: count >= 1,
        ),
        (
            "unknown employee",
            """
            SELECT COUNT(*) FROM dw.dim_employee
            WHERE employee_id = '__UNKNOWN__' AND employee_key = -1
            """,
            lambda count: count == 1,
        ),
    ]

    for label, query, predicate in checks:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        if not predicate(count):
            raise ValueError(f"Preservation check failed: {label}")
        print(f"VALID: preserved {label} | count={count}")


def main():
    parser = argparse.ArgumentParser(
        description="PulseIQ PostgreSQL warehouse loader"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply transactional upserts to PostgreSQL.",
    )
    args = parser.parse_args()

    expected_files = {table + ".csv" for table in LOAD_ORDER}
    actual_files = set(get_csv_files())

    if expected_files != actual_files:
        raise ValueError(
            "CSV inventory mismatch. "
            f"Missing={sorted(expected_files - actual_files)}; "
            f"unexpected={sorted(actual_files - expected_files)}"
        )

    print(f"PULSEIQ WAREHOUSE - {'APPLY' if args.apply else 'DRY RUN'}")
    print("=" * 70)
    print(
        "Write mode enabled: transactional upserts requested."
        if args.apply
        else "Read-only mode: no database changes will be made."
    )

    connection = get_connection(read_only=not args.apply)

    try:
        with connection:
            with connection.cursor() as cursor:
                if not args.apply:
                    cursor.execute("SET TRANSACTION READ ONLY")

                source_tables = {}

                for table in LOAD_ORDER:
                    columns, rows = read_source_table(cursor, table)
                    source_tables[table] = (columns, rows)
                    existing = get_table_count(cursor, table)
                    print(
                        f"VALID: {table} | source={len(rows)} "
                        f"| existing={existing} "
                        f"| key={', '.join(PRIMARY_KEYS[table])}"
                    )

                validate_account_parents(source_tables)

                if args.apply:
                    for table in LOAD_ORDER:
                        columns, rows = source_tables[table]
                        if rows:
                            query = build_upsert_query(
                                connection, table, columns
                            )
                            execute_values(
                                cursor, query, rows, page_size=BATCH_SIZE
                            )
                        print(
                            f"UPSERTED: {table} | "
                            f"source rows processed={len(rows)}"
                        )

                    for table in LOAD_ORDER:
                        _, rows = source_tables[table]
                        existing = get_table_count(cursor, table)

                        if table.startswith("fact_") and existing != len(rows):
                            raise ValueError(
                                f"Post-load count mismatch for {table}: "
                                f"source={len(rows)}, database={existing}"
                            )

                        if table.startswith("dim_") and existing < len(rows):
                            raise ValueError(
                                f"Dimension count unexpectedly smaller "
                                f"than source for {table}."
                            )

                    verify_preserved_members(cursor)
                    print("-" * 70)
                    print("Post-load validations passed; transaction can commit.")

                print("=" * 70)
                print(f"Tables validated: {len(LOAD_ORDER)}")
                print(
                    "Source rows checked: "
                    f"{sum(len(rows) for _, rows in source_tables.values())}"
                )
                print(
                    "RESULT: LOAD VALIDATIONS PASSED"
                    if args.apply else "RESULT: DRY-RUN PASSED"
                )
    finally:
        connection.close()

    if args.apply:
        print("TRANSACTION COMMITTED.")
        print("No records were deleted.")
    else:
        print("No records were inserted, updated, or deleted.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, psycopg2.Error, csv.Error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
