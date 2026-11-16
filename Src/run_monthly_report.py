import os
import subprocess
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
REPORT_SCRIPT = ROOT / "Src" / "build_report.py"


def main():
    load_dotenv(ROOT / ".env")

    connection = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=10,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT MAX(month_start_date) "
                "FROM dw.m01_headcount"
            )
            latest_month = cursor.fetchone()[0]
    finally:
        connection.close()

    if latest_month is None:
        print("No warehouse reporting data is available.")
        return 1

    month = latest_month.strftime("%Y-%m")
    print(f"Generating scheduled report for latest available month: {month}")

    result = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), "--month", month],
        cwd=ROOT,
        check=False,
    )

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
