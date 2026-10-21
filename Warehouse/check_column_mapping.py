
import csv
import os
import subprocess
import sys

CSV_FOLDER = os.path.join("03_Data", "csv")
CONTAINER_NAME = "pulseiq-warehouse-db"
DB_USER = "wos"
DB_NAME = "pulseiq_wh"


def get_csv_tables():
    """Find dimension and fact CSV files."""
    if not os.path.isdir(CSV_FOLDER):
        raise FileNotFoundError(
            f"CSV folder not found: {CSV_FOLDER}"
        )

    return sorted(
        filename[:-4]
        for filename in os.listdir(CSV_FOLDER)
        if filename.lower().endswith(".csv")
        and (
            filename.lower().startswith("dim_")
            or filename.lower().startswith("fact_")
        )
    )


def get_database_columns():
    """Read PostgreSQL column metadata through Docker."""
    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'dw'
      AND (
          table_name LIKE 'dim_%'
          OR table_name LIKE 'fact_%'
      )
    ORDER BY table_name, ordinal_position;
    """

    command = [
        "docker", "exec", CONTAINER_NAME,
        "psql", "-X", "-U", DB_USER, "-d", DB_NAME,
        "-A", "-t", "-F", "|", "-c", query
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Could not read PostgreSQL metadata.\n"
            + result.stderr.strip()
        )

    columns = {}

    for line in result.stdout.splitlines():
        parts = line.strip().split("|", 1)

        if len(parts) == 2:
            table_name, column_name = parts
            columns.setdefault(table_name, []).append(column_name)

    return columns


def main():
    try:
        tables = get_csv_tables()
        database_columns = get_database_columns()

        if not tables:
            print("ERROR: No dimension or fact CSV files found.")
            return 1

        issues_found = False

        print("\nPOSTGRESQL WAREHOUSE COLUMN MAPPING CHECK")
        print("=" * 55)

        for table in tables:
            csv_path = os.path.join(
                CSV_FOLDER, table + ".csv"
            )

            with open(
                csv_path,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                csv_columns = next(csv.reader(file), [])

            db_columns = database_columns.get(table, [])

            if not db_columns:
                issues_found = True
                print(f"\nFAIL: {table}")
                print("  PostgreSQL table or columns not found.")
                continue

            missing_in_db = [
                column for column in csv_columns
                if column not in db_columns
            ]

            missing_in_csv = [
                column for column in db_columns
                if column not in csv_columns
            ]

            if not missing_in_db and not missing_in_csv:
                print(
                    f"PASS: {table} "
                    f"({len(csv_columns)} columns match)"
                )
            else:
                issues_found = True
                print(f"\nCHECK: {table}")

                if missing_in_db:
                    print(
                        "  CSV columns absent from PostgreSQL:",
                        missing_in_db
                    )

                if missing_in_csv:
                    print(
                        "  PostgreSQL columns absent from CSV:",
                        missing_in_csv
                    )

        print("\n" + "=" * 55)
        print(f"CSV tables checked: {len(tables)}")

        if issues_found:
            print("RESULT: MAPPING ISSUES FOUND")
            print("Review the CHECK and FAIL messages above.")
            return 1

        print("RESULT: ALL COLUMN NAMES MATCH")
        print("No data was inserted, updated, or deleted.")
        return 0

    except (OSError, RuntimeError, StopIteration, subprocess.TimeoutExpired) as error:
        print(f"\nERROR: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
