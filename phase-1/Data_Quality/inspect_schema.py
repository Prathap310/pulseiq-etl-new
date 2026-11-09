
from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

conn = psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=os.getenv("PGPORT", "5433"),
    dbname=os.getenv("PGDATABASE", "pulseiq_wh"),
    user=os.getenv("PGUSER", "wos"),
    password=os.getenv("PGPASSWORD"),
)

tables = [
    "dim_employee",
    "fact_headcount_monthly",
    "fact_payroll",
    "fact_attendance_monthly",
    "fact_task",
    "fact_anomaly",
    "fact_attrition_risk",
]

try:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'dw'
              AND table_name = ANY(%s)
            ORDER BY table_name, ordinal_position
            """,
            (tables,),
        )

        for table, column, data_type in cur.fetchall():
            print(f"{table}.{column} ({data_type})")
finally:
    conn.close()
