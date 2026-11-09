
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03_Data" / "csv"
OUTPUT = ROOT / "Reports" / "Task13"

START_MONTH = pd.Timestamp("2025-04-01")
END_MONTH = pd.Timestamp("2026-09-01")

MIN_GROUP_SIZE = 5
ATTRITION_MIN_GROUP_SIZE = 10


def read_csv(name):
    return pd.read_csv(DATA / name)


def month_start(value):
    return pd.Timestamp(value).to_period("M").to_timestamp()


def allocate_leave(leave, employees):
    """
    Allocate approved source leave days across the full request period
    using weekday proportions.

    Only reporting-period months are included in the output.
    Department is assigned using the employee's department at leave start.
    """

    records = []

    employees = employees.copy()

    employees["employee_id"] = employees["employee_id"].astype(str)

    employees["valid_from"] = pd.to_datetime(
        employees["valid_from"], errors="coerce"
    )

    employees["valid_to"] = pd.to_datetime(
        employees["valid_to"], errors="coerce"
    )

    for row in leave.itertuples(index=False):

        if str(row.status).strip().lower() != "approved":
            continue

        start = pd.to_datetime(row.start_date, errors="coerce")
        end = pd.to_datetime(row.end_date, errors="coerce")
        source_days = pd.to_numeric(row.days, errors="coerce")

        if pd.isna(start) or pd.isna(end) or pd.isna(source_days):
            continue

        if end < start or source_days <= 0:
            continue

        # Find employee department valid at the leave start date.
        matches = employees[
            (employees["employee_id"] == str(row.employee_id))
            & (
                employees["valid_from"].isna()
                | (employees["valid_from"] <= start)
            )
            & (
                employees["valid_to"].isna()
                | (employees["valid_to"] >= start)
            )
        ]

        if matches.empty:
            continue

        department_id = matches.iloc[0]["department_id"]

        # Calculate weekday weights across the complete leave request.
        month_weights = []

        month = month_start(start)
        final_month = month_start(end)

        while month <= final_month:

            month_end = month + pd.offsets.MonthEnd(0)

            overlap_start = max(start, month)
            overlap_end = min(end, month_end)

            weekdays = len(
                pd.bdate_range(overlap_start, overlap_end)
            )

            if weekdays > 0:
                month_weights.append((month, weekdays))

            month += pd.DateOffset(months=1)

        total_weight = sum(
            weight for _, weight in month_weights
        )

        if total_weight == 0:
            continue

        # Do not redistribute days from months outside the
        # reporting period into the reporting period.
        for month, weight in month_weights:

            if not START_MONTH <= month <= END_MONTH:
                continue

            allocated_days = (
                source_days * weight / total_weight
            )

            records.append({
                "department_id": department_id,
                "month_start_date": month,
                "approved_leave_days": allocated_days
            })

    if not records:
        return pd.DataFrame(columns=[
            "department_id",
            "month_start_date",
            "approved_leave_days"
        ])

    return (
        pd.DataFrame(records)
        .groupby(
            ["department_id", "month_start_date"],
            as_index=False
        )["approved_leave_days"]
        .sum()
    )


def main():

    OUTPUT.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Load source datasets
    # ---------------------------------------------------------

    headcount = read_csv("fact_headcount_monthly.csv")
    payroll = read_csv("fact_payroll.csv")
    attendance = read_csv("fact_attendance_monthly.csv")
    leave = read_csv("fact_leave.csv")

    departments = read_csv("dim_department.csv")
    employees = read_csv("dim_employee.csv")

    departments["department_id"] = (
        departments["department_id"].astype(str)
    )

    # ---------------------------------------------------------
    # 2. Standardize reporting month
    # ---------------------------------------------------------

    headcount["month_start_date"] = pd.to_datetime(
        headcount["month_start_date"]
    ).dt.to_period("M").dt.to_timestamp()

    payroll["month_start_date"] = pd.to_datetime(
        payroll["period_end_date"]
    ).dt.to_period("M").dt.to_timestamp()

    attendance["month_start_date"] = pd.to_datetime(
        attendance["period_end_date"]
    ).dt.to_period("M").dt.to_timestamp()

    for frame in (headcount, payroll, attendance):
        frame["department_id"] = (
            frame["department_id"].astype(str)
        )

    # ---------------------------------------------------------
    # 3. Restrict reporting period
    # ---------------------------------------------------------

    def reporting_period(frame):
        return frame[
            frame["month_start_date"].between(
                START_MONTH, END_MONTH
            )
        ].copy()

    headcount = reporting_period(headcount)
    payroll = reporting_period(payroll)
    attendance = reporting_period(attendance)

    # ---------------------------------------------------------
    # 4. Aggregate headcount at department-month grain
    # ---------------------------------------------------------

    hc = headcount.groupby(
        ["department_id", "month_start_date"],
        as_index=False
    ).agg(
        headcount_start=("headcount_start", "sum"),
        headcount_end=("headcount_end", "sum"),
        hires=("hires", "sum"),
        exits=("exits", "sum"),
        voluntary_exits=("voluntary_exits", "sum")
    )

    # ---------------------------------------------------------
    # 5. Aggregate payroll independently
    # ---------------------------------------------------------

    payroll["employee_id"] = (
        payroll["employee_id"].astype(str)
    )

    payroll_agg = payroll.groupby(
        ["department_id", "month_start_date"],
        as_index=False
    ).agg(
        payroll_employee_count=("employee_id", "nunique"),
        employer_cost=("employer_cost", "sum"),
        overtime_cost=("overtime_pay", "sum"),
        gross_pay=("gross_pay", "sum"),
        net_pay=("net_pay", "sum"),
        lop_days=("lop_days", "sum")
    )

    payroll_agg["cost_per_head"] = (
        payroll_agg["employer_cost"]
        / payroll_agg["payroll_employee_count"].replace(0, pd.NA)
    )

    # ---------------------------------------------------------
    # 6. Aggregate attendance independently
    # ---------------------------------------------------------

    attendance["employee_id"] = (
        attendance["employee_id"].astype(str)
    )

    attendance_agg = attendance.groupby(
        ["department_id", "month_start_date"],
        as_index=False
    ).agg(
        attendance_employee_count=("employee_id", "nunique"),
        scheduled_days=("scheduled_days", "sum"),
        present_days=("present_days", "sum"),
        half_days_unpaid=("half_days_unpaid", "sum"),
        overtime_hours=("overtime_hours", "sum")
    )

    attendance_agg["attendance_rate"] = (
        attendance_agg["present_days"]
        + 0.5 * attendance_agg["half_days_unpaid"]
    ) / attendance_agg["scheduled_days"].replace(0, pd.NA)

    # ---------------------------------------------------------
    # 7. Allocate approved leave independently
    # ---------------------------------------------------------

    leave_agg = allocate_leave(leave, employees)

    # ---------------------------------------------------------
    # 8. Build complete department-month reporting grid
    # ---------------------------------------------------------

    months = pd.date_range(
        START_MONTH,
        END_MONTH,
        freq="MS"
    )

    department_ids = (
        departments["department_id"].dropna().unique()
    )

    grid = pd.MultiIndex.from_product(
        [department_ids, months],
        names=["department_id", "month_start_date"]
    ).to_frame(index=False)

    # ---------------------------------------------------------
    # 9. Join only aggregated datasets
    # ---------------------------------------------------------

    result = (
        grid
        .merge(
            hc,
            on=["department_id", "month_start_date"],
            how="left"
        )
        .merge(
            payroll_agg,
            on=["department_id", "month_start_date"],
            how="left"
        )
        .merge(
            attendance_agg,
            on=["department_id", "month_start_date"],
            how="left"
        )
        .merge(
            leave_agg,
            on=["department_id", "month_start_date"],
            how="left"
        )
        .merge(
            departments,
            on="department_id",
            how="left"
        )
    )

    # ---------------------------------------------------------
    # 10. Calculate leave days per head
    # ---------------------------------------------------------

    result["approved_leave_days"] = (
        result["approved_leave_days"].fillna(0)
    )

    result["leave_days_per_head"] = (
        result["approved_leave_days"]
        / result["headcount_end"].replace(0, pd.NA)
    )

    # ---------------------------------------------------------
    # 11. Calculate monthly attrition (M04)
    # Formula: Exits / Headcount Start * 100
    # ---------------------------------------------------------

    result["attrition_rate_monthly_pct"] = (
        result["exits"]
        / result["headcount_start"].replace(0, pd.NA)
    ) * 100

    # ---------------------------------------------------------
    # 12. Apply general minimum group-size suppression
    # ---------------------------------------------------------

    result["is_suppressed"] = (
        result["payroll_employee_count"].fillna(0)
        < MIN_GROUP_SIZE
    )

    protected_metrics = [
        "headcount_start",
        "headcount_end",
        "hires",
        "exits",
        "voluntary_exits",
        "payroll_employee_count",
        "employer_cost",
        "overtime_cost",
        "gross_pay",
        "net_pay",
        "lop_days",
        "cost_per_head",
        "attendance_employee_count",
        "scheduled_days",
        "present_days",
        "half_days_unpaid",
        "attendance_rate",
        "overtime_hours",
        "approved_leave_days",
        "leave_days_per_head"
    ]

    result.loc[
        result["is_suppressed"],
        protected_metrics
    ] = pd.NA

    # ---------------------------------------------------------
    # 13. Apply M04 attrition minimum group-size suppression
    # ---------------------------------------------------------

    attrition_suppressed = (
        result["headcount_start"].fillna(0)
        < ATTRITION_MIN_GROUP_SIZE
    )

    result.loc[
        attrition_suppressed | result["is_suppressed"],
        "attrition_rate_monthly_pct"
    ] = pd.NA

    # ---------------------------------------------------------
    # 14. Record leave allocation methodology
    # ---------------------------------------------------------

    result["leave_allocation_method"] = (
        "Approved source days; weekday-proportional allocation "
        "across the full leave request period"
    )

    # ---------------------------------------------------------
    # 15. Sort and export
    # ---------------------------------------------------------

    result = result.sort_values(
        ["department_id", "month_start_date"]
    ).reset_index(drop=True)

    output_file = (
        OUTPUT / "task13_department_month.csv"
    )

    result.to_csv(output_file, index=False)

    # ---------------------------------------------------------
    # 16. Validate output grain and suppression
    # ---------------------------------------------------------

    duplicate_keys = result.duplicated(
        ["department_id", "month_start_date"]
    ).sum()

    expected_rows = len(department_ids) * len(months)

    print("\nTask 13 aggregation completed.")
    print("--------------------------------")
    print("Output:", output_file)
    print("Rows:", len(result))
    print("Expected rows:", expected_rows)
    print("Departments:", result["department_id"].nunique())
    print("Months:", result["month_start_date"].nunique())
    print("Duplicate department-month keys:", duplicate_keys)

    print(
        "General suppressed groups:",
        int(result["is_suppressed"].sum())
    )

    print(
        "Attrition suppressed groups:",
        int(
            (
                result["attrition_rate_monthly_pct"].isna()
            ).sum()
        )
    )

    print(
        "Unsuppressed general groups:",
        int((~result["is_suppressed"]).sum())
    )

    if len(result) != expected_rows or duplicate_keys != 0:
        raise ValueError(
            "Task 13 department-month grain validation failed."
        )

    if len(result) != 198:
        raise ValueError(
            "Expected 198 rows for 11 departments and 18 months."
        )

    print("\nTask 13 validation passed.")


if __name__ == "__main__":
    main()
