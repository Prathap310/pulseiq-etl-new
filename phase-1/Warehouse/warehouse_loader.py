
import csv
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FOLDER = os.path.join(BASE_DIR, "03_Data", "csv")
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


def get_connection():
    required = [
        "PGHOST",
        "PGPORT",
        "PGDATABASE",
        "PGUSER",
        "PGPASSWORD",
        "PGSCHEMA",
    ]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(
            "Missing settings in .env: " + ", ".join(missing)
        )

    if os.getenv("PGSCHEMA") != "dw":
        raise ValueError("Expected PGSCHEMA=dw for this audit.")

    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
    )


def get_csv_files():
    if not os.path.isdir(CSV_FOLDER):
        raise FileNotFoundError(
            f"CSV folder not found: {CSV_FOLDER}"
        )

    return sorted(
        name for name in os.listdir(CSV_FOLDER)
        if name.endswith(".csv")
        and (name.startswith("dim_") or name.startswith("fact_"))
    )


def get_source_count(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        next(reader, None)
        return sum(1 for _ in reader)


def main():
    files = get_csv_files()
    differences = []

    print("PULSEIQ WAREHOUSE — READ-ONLY ROW COUNT AUDIT")
    print("=" * 70)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")

            for filename in files:
                table = filename[:-4]
                source_path = os.path.join(CSV_FOLDER, filename)
                source_count = get_source_count(source_path)

                cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                        sql.Identifier("dw"),
                        sql.Identifier(table),
                    )
                )
                destination_count = cursor.fetchone()[0]
                difference = destination_count - source_count
                status = "MATCH" if difference == 0 else "DIFFERENCE"

                print(
                    f"{status}: {table} | CSV={source_count} "
                    f"| PostgreSQL={destination_count} "
                    f"| difference={difference}"
                )

                if difference:
                    differences.append(table)

    print("=" * 70)
    print(f"Tables checked: {len(files)}")
    print(f"Tables with count differences: {len(differences)}")

    if differences:
        print("RESULT: REVIEW DIFFERENCES BEFORE LOADING")
        print("Tables:", ", ".join(differences))
    else:
        print("RESULT: ALL ROW COUNTS MATCH")

    print("READ-ONLY AUDIT: No warehouse data was changed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (
        OSError,
        ValueError,
        psycopg2.Error,
    ) as error:
        print(f"ERROR: {error}")
        sys.exit(1)
	