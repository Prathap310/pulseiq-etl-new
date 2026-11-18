import argparse
import os
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from openpyxl.chart import BarChart, Reference
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "Reports" / "Task16"

METRICS = [
    {
        "title": "Monthly Department Headcount",
        "view": "m01_headcount",
        "date_column": "month_start_date",
        "value_column": "headcount",
        "sql": """
            SELECT month_start_date, department_id, headcount
            FROM dw.m01_headcount
            WHERE month_start_date >= %s AND month_start_date < %s
              AND privacy_threshold_met IS TRUE
            ORDER BY department_id
        """,
    },
    {
        "title": "Monthly Department Attrition",
        "view": "m04_monthly_attrition",
        "date_column": "month_start_date",
        "value_column": "attrition_rate_pct",
        "sql": """
            SELECT month_start_date, department_id, attrition_rate_pct
            FROM dw.m04_monthly_attrition
            WHERE month_start_date >= %s AND month_start_date < %s
              AND privacy_threshold_met IS TRUE
            ORDER BY department_id
        """,
    },
    {
        "title": "Department Employer Payroll Cost",
        "view": "m09_employer_payroll_cost",
        "date_column": "period_end_date",
        "value_column": "employer_cost",
        "sql": """
            SELECT period_end_date, department_id, employer_cost
            FROM dw.m09_employer_payroll_cost
            WHERE period_end_date >= %s AND period_end_date < %s
              AND privacy_threshold_met IS TRUE
            ORDER BY department_id
        """,
    },
    {
        "title": "Department Attendance Rate",
        "view": "m13_attendance_rate",
        "date_column": "period_end_date",
        "value_column": "attendance_rate",
        "sql": """
            SELECT period_end_date, department_id, attendance_rate
            FROM dw.m13_attendance_rate
            WHERE period_end_date >= %s AND period_end_date < %s
              AND privacy_threshold_met IS TRUE
            ORDER BY department_id
        """,
    },
    {
        "title": "Monthly Company Net Profit",
        "view": "m17_net_profit",
        "date_column": "month_start_date",
        "value_column": "net_profit",
        "sql": """
            SELECT month_start_date, net_profit
            FROM dw.m17_net_profit
            WHERE month_start_date >= %s AND month_start_date < %s
            ORDER BY month_start_date
        """,
    },
]


def connect_database():
    load_dotenv(ROOT / ".env")

    required = [
        "PGHOST", "PGPORT", "PGDATABASE",
        "PGUSER", "PGPASSWORD"
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing database settings in .env: " + ", ".join(missing)
        )

    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=10,
    )


def fetch_data(connection, start_date, end_date):
    results = {}

    with connection.cursor() as cursor:
        for metric in METRICS:
            cursor.execute(metric["sql"], (start_date, end_date))
            rows = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            results[metric["title"]] = pd.DataFrame(
                rows, columns=columns
            )

        cutoff_dates = []
        for metric in METRICS:
            cursor.execute(
                f"SELECT MAX({metric['date_column']}) "
                f"FROM dw.{metric['view']}"
            )
            result = cursor.fetchone()[0]
            if result:
                cutoff_dates.append(result)

    data_cutoff = max(cutoff_dates) if cutoff_dates else None
    return results, data_cutoff


def create_excel(results, month_text, start_date, end_date, data_cutoff):
    output = OUTPUT_DIR / f"management_report_{month_text}.xlsx"

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary = pd.DataFrame([
            ["Reporting month", month_text],
            ["Reporting period", f"{start_date} to {end_date}"],
            ["Warehouse data cut-off", str(data_cutoff or "Unavailable")],
            ["Generated at (UTC)", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")],
            ["Source", "PulseIQ governed metric views"],
        ], columns=["Report detail", "Value"])

        summary.to_excel(writer, sheet_name="Summary", index=False)

        for metric in METRICS:
            title = metric["title"]
            frame = results[title]
            sheet_name = metric["view"][:31]

            frame.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

            for column_cells in worksheet.columns:
                width = max(
                    len(str(cell.value or "")) for cell in column_cells
                ) + 3
                worksheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = min(width, 35)

            value_column = metric["value_column"]
            if not frame.empty and value_column in frame.columns:
                value_index = list(frame.columns).index(value_column) + 1
                category_index = (
                    list(frame.columns).index("department_id") + 1
                    if "department_id" in frame.columns else
                    list(frame.columns).index(metric["date_column"]) + 1
                )

                chart = BarChart()
                chart.title = title
                chart.y_axis.title = value_column
                chart.x_axis.title = "Department / Month"
                chart.height = 8
                chart.width = 16

                data = Reference(
                    worksheet, min_col=value_index,
                    min_row=1, max_row=len(frame) + 1
                )
                categories = Reference(
                    worksheet, min_col=category_index,
                    min_row=2, max_row=len(frame) + 1
                )
                chart.add_data(data, titles_from_data=True)
                chart.set_categories(categories)
                worksheet.add_chart(chart, "E2")

        summary_ws = writer.sheets["Summary"]
        summary_ws.column_dimensions["A"].width = 28
        summary_ws.column_dimensions["B"].width = 55
        summary_ws.freeze_panes = "A2"

    return output


def create_pdf(results, month_text, start_date, end_date, data_cutoff):
    output = OUTPUT_DIR / f"management_report_{month_text}.pdf"

    document = SimpleDocTemplate(
        str(output),
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=19,
        spaceAfter=12,
    ))

    story = [
        Paragraph("PulseIQ Monthly Management Report", styles["ReportTitle"]),
        Paragraph(f"<b>Reporting month:</b> {month_text}", styles["Normal"]),
        Paragraph(
            f"<b>Reporting period:</b> {start_date} to {end_date}",
            styles["Normal"],
        ),
        Paragraph(
            f"<b>Warehouse data cut-off:</b> {data_cutoff or 'Unavailable'}",
            styles["Normal"],
        ),
        Paragraph(
            f"<b>Generated at (UTC):</b> "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        ),
        Spacer(1, 8 * mm),
        Paragraph(
            "This report uses existing governed PulseIQ metric views. "
            "Department-level rows that do not meet the configured "
            "privacy threshold are excluded.",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
    ]

    for index, metric in enumerate(METRICS):
        title = metric["title"]
        frame = results[title]

        story.append(Paragraph(title, styles["Heading2"]))

        if frame.empty:
            story.append(Paragraph(
                "No eligible records are available for this month.",
                styles["Normal"],
            ))
        else:
            data = [list(frame.columns)]
            for row in frame.itertuples(index=False, name=None):
                data.append([
                    value.strftime("%Y-%m-%d")
                    if isinstance(value, (date, datetime))
                    else f"{value:,.2f}"
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                    else str(value)
                    for value in row
                ])

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#EAF0F6")]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(table)

        if index < len(METRICS) - 1:
            story.append(PageBreak())

    document.build(story)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Generate PulseIQ monthly PDF and Excel reports."
    )
    parser.add_argument(
        "--month",
        required=True,
        help="Reporting month in YYYY-MM format, for example 2026-09",
    )
    args = parser.parse_args()

    try:
        month_start = pd.Period(args.month, freq="M").start_time.date()
    except Exception as exc:
        raise SystemExit("Invalid month. Use YYYY-MM, for example 2026-09.") from exc

    next_month = (pd.Timestamp(month_start) + pd.offsets.MonthBegin(1)).date()
    month_end = (pd.Timestamp(next_month) - pd.Timedelta(days=1)).date()
    month_text = month_start.strftime("%Y_%m")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    connection = None
    try:
        connection = connect_database()
        results, data_cutoff = fetch_data(
            connection, month_start, next_month
        )

        excel_path = create_excel(
            results, month_text, month_start, month_end, data_cutoff
        )
        pdf_path = create_pdf(
            results, month_text, month_start, month_end, data_cutoff
        )

        print("\nPulseIQ report generation completed.")
        print(f"Reporting month: {month_text}")
        print(f"Reporting period: {month_start} to {month_end}")
        print(f"Warehouse data cut-off: {data_cutoff or 'Unavailable'}")
        for title, frame in results.items():
            print(f"{title}: {len(frame)} eligible rows")
        print(f"\nExcel report: {excel_path}")
        print(f"PDF report:   {pdf_path}")

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
