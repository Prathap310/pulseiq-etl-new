from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import pandera.pandas as pa
from pandera_schemas import FACT_ANOMALY_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "03_Data" / "csv"
CLEAN = ROOT / "Data" / "Clean"
REJECTED = ROOT / "Data" / "Rejected"

FEEDS = {
    "fact_task": "Task board (fact_task)",
    "fact_anomaly": "AI anomaly results (fact_anomaly)",
    "fact_attrition_risk": "AI attrition risk (fact_attrition_risk)",
    "fact_forecast": "AI forecast (fact_forecast)",
}


def read_csv(name):
    return pd.read_csv(RAW / f"{name}.csv", dtype=str, keep_default_na=False)


def is_blank(value):
    return value is None or str(value).strip() == ""


def pandera_row_reasons(frame, schema):
    """Return row-level Pandera validation errors without stopping the pipeline."""
    row_reasons = [[] for _ in range(len(frame))]

    try:
        schema.validate(frame, lazy=True)
        return row_reasons
    except pa.errors.SchemaErrors as exc:
        failure_cases = exc.failure_cases

        if "index" not in failure_cases.columns:
            return row_reasons

        for _, failure in failure_cases.iterrows():
            index = failure.get("index")
            column = failure.get("column", "schema")
            check = failure.get("check", "validation failed")

            if isinstance(index, int) and 0 <= index < len(frame):
                row_reasons[index].append(
                    f"Pandera {column}: {check}"
                )

        return row_reasons
    except pa.errors.SchemaError as exc:
        # A schema-level error without row details is recorded for every row.
        message = f"Pandera schema error: {str(exc)[:200]}"
        return [[message] for _ in range(len(frame))]


def valid_date(value):
    if is_blank(value):
        return False
    value = str(value).strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            datetime.strptime(value, "%Y-%m-%d")
        else:
            pd.to_datetime(value, errors="raise")
        return True
    except (ValueError, TypeError, OverflowError, pd.errors.OutOfBoundsDatetime):
        return False


def valid_number(value):
    if is_blank(value):
        return False
    try:
        return pd.notna(float(value))
    except (ValueError, TypeError):
        return False


def valid_integer(value):
    if not valid_number(value):
        return False
    return float(value).is_integer()


def load_reference_values():
    employees = read_csv("dim_employee")
    departments = read_csv("dim_department")
    teams = read_csv("dim_team")
    sprints = read_csv("dim_sprint")

    current = employees[
        employees["is_current"].str.strip().str.upper().eq("Y")
    ]

    return {
        "employee_ids": set(employees["employee_id"]),
        "active_employee_ids": set(
            current.loc[
                current["employment_status"].str.strip().str.lower().eq("active"),
                "employee_id",
            ]
        ),
        "department_ids": set(departments["department_id"]),
        "team_ids": set(teams["team_id"]),
        "sprints": dict(zip(sprints["sprint_id"], sprints["end_date"])),
    }


def contract_columns(contracts, feed):
    rows = contracts[contracts["feed"].eq(feed)]
    result = {}
    for _, row in rows.iterrows():
        column = row["column_name"]
        if column == "top_reason_1..3":
            for expanded in ["top_reason_1", "top_reason_2", "top_reason_3"]:
                item = row.copy()
                item["column_name"] = expanded
                result[expanded] = item
        else:
            result[column] = row
    return result


def validate_feed(name, feed, contracts, refs):
    source = read_csv(name)
    original_columns = list(source.columns)
    rules = contract_columns(contracts, feed)

    reasons = [[] for _ in range(len(source))]
    seen_ids = {}

    def reject(mask, message):
        for position in range(len(source)):
            if bool(mask.iloc[position]):
                reasons[position].append(message)

    # Every contracted column must exist in the CSV.
    missing_columns = set(rules) - set(source.columns)
    if missing_columns:
        raise ValueError(
            f"{name}: missing contracted columns: {sorted(missing_columns)}"
        )

    # Required fields, data types and supported contract rules.
    for column, rule in rules.items():
        values = source[column]
        nullable = str(rule["nullable"]).strip().lower() == "yes"
        dtype = str(rule["data_type"]).strip().lower()
        specification = str(rule["rule_or_allowed_values"]).strip()

        if not nullable:
            reject(values.map(is_blank), f"{column}: required value is blank")

        nonblank = values.map(lambda value: not is_blank(value))

        if dtype == "date":
            reject(
                nonblank & ~values.map(valid_date),
                f"{column}: invalid date",
            )
        elif dtype.startswith("decimal") or dtype == "decimal":
            reject(
                nonblank & ~values.map(valid_number),
                f"{column}: invalid decimal",
            )
        elif dtype == "int":
            reject(
                nonblank & ~values.map(valid_integer),
                f"{column}: invalid integer",
            )
        elif dtype == "timestamp":
            def timestamp_ok(value):
                if is_blank(value):
                    return True
                try:
                    parsed = pd.Timestamp(value)
                    return parsed.tzinfo is not None
                except (ValueError, TypeError, OverflowError):
                    return False

            reject(
                nonblank & ~values.map(timestamp_ok),
                f"{column}: invalid timestamp or missing timezone",
            )

        allowed = None
        if "|" in specification:
            allowed = {
                item.strip().lower()
                for item in specification.split("|")
            }
        elif specification == "P1..P4":
            allowed = {"p1", "p2", "p3", "p4"}
        elif specification == "1,2,3,5,8,13":
            allowed = {"1", "2", "3", "5", "8", "13"}

        if allowed:
            reject(
                nonblank & ~values.str.strip().str.lower().isin(allowed),
                f"{column}: value outside allowed set",
            )

    # Unique identifiers.
    unique_columns = {
        "fact_task": ("task_id", r"TASK-\d{5}"),
        "fact_anomaly": ("result_id", r"AN-\d{4}"),
        "fact_attrition_risk": ("prediction_id", r"AR-\d{4}"),
        "fact_forecast": ("forecast_id", r"FC-\d{4}"),
    }
    id_column, id_pattern = unique_columns[name]

    reject(
        source[id_column].map(
            lambda value: not bool(re.fullmatch(id_pattern, value.strip()))
        ),
        f"{id_column}: invalid identifier format",
    )

    duplicate_ids = source[id_column].duplicated(keep=False)
    reject(duplicate_ids, f"{id_column}: duplicate identifier")

    # Feed-specific checks.
    if name == "fact_task":
        reject(
            ~source["team_id"].isin(refs["team_ids"]),
            "team_id: unknown team",
        )
        reject(
            ~source["sprint_id"].isin(refs["sprints"]),
            "sprint_id: unknown sprint",
        )
        reject(
            ~source["assignee_employee_id"].isin(refs["employee_ids"]),
            "assignee_employee_id: unknown employee",
        )
        reject(
            ~source["story_points"].isin(["1", "2", "3", "5", "8", "13"]),
            "story_points: unsupported value",
        )
        reject(
            ~source["priority"].isin(["P1", "P2", "P3", "P4"]),
            "priority: unsupported value",
        )
        reject(
            ~source["status"].isin(
                ["Done", "In Progress", "Blocked", "To Do", "Cancelled"]
            ),
            "status: unsupported value",
        )
        reject(
            ~source["reopened_count"].map(valid_integer)
            | source["reopened_count"].map(
                lambda value: valid_number(value) and float(value) < 0
            ),
            "reopened_count: must be a non-negative integer",
        )

        for i, row in source.iterrows():
            created = row["created_date"]
            started = row["started_date"]
            due = row["due_date"]
            completed = row["completed_date"]
            status = row["status"]

            if not is_blank(created) and not is_blank(started):
                if valid_date(created) and valid_date(started):
                    if pd.Timestamp(created) > pd.Timestamp(started):
                        reasons[i].append(
                            "created_date: later than started_date"
                        )

            if status == "To Do" and not is_blank(started):
                reasons[i].append(
                    "started_date: must be blank when status is To Do"
                )
            elif status != "To Do" and is_blank(started):
                reasons[i].append(
                    "started_date: blank when status is not To Do"
                )

            expected_due = refs["sprints"].get(row["sprint_id"], "")
            if expected_due and due != expected_due:
                reasons[i].append("due_date: does not match sprint end date")

            if status == "Done" and is_blank(completed):
                reasons[i].append(
                    "completed_date: required when status is Done"
                )
            if not is_blank(completed) and not is_blank(started):
                if valid_date(completed) and valid_date(started):
                    if pd.Timestamp(completed) < pd.Timestamp(started):
                        reasons[i].append(
                            "completed_date: earlier than started_date"
                        )

    elif name == "fact_anomaly":
        # Apply Pandera schema checks and preserve row-level rejection reasons.
        pandera_reasons = pandera_row_reasons(source, FACT_ANOMALY_SCHEMA)
        for position, row_reasons in enumerate(pandera_reasons):
            for reason in row_reasons:
                reasons[position].append(reason)

        reject(
            ~source["employee_id"].isin(refs["employee_ids"]),
            "employee_id: unknown employee",
        )
        reject(
            source["anomaly_score"].map(
                lambda value: valid_number(value)
                and not 0 <= float(value) <= 1
            ),
            "anomaly_score: must be between 0 and 1",
        )
        reject(
            ~source["flagged"].isin(["Y", "N"]),
            "flagged: must be Y or N",
        )

        allowed_reason_codes = {
            "FREQUENT_LATE",
            "GROSS_ABOVE_NORM",
            "GROSS_BELOW_EXPECTED",
            "LONG_UNPAID_ABSENCE",
            "NEGATIVE_NET_PAY",
            "NO_ATTENDANCE",
            "OVERTIME_ABOVE_CAP",
            "PATTERN_SHIFT",
            "PF_NOT_DEDUCTED",
            "STATISTICAL_OUTLIER",
            "ZERO_PAY",
        }
        reject(
            ~source["reason_code"].isin(allowed_reason_codes),
            "reason_code: not a published code",
        )

        # Accept the observed model naming convention with a numeric version suffix.
        reject(
            ~source["model_version"].astype(str).str.match(
                r"^[A-Za-z][A-Za-z0-9_-]*-\d+\.\d+$"
            ),
            "model_version: invalid semantic version text",
        )
        reject(
            ~source["source_dataset"].isin(
                ["attendance_monthly_features", "payroll_monthly_features"]
            ),
            "source_dataset: unsupported dataset",
        )
        reject(
            source["money_at_risk"].map(
                lambda value: not is_blank(value) and not valid_number(value)
            ),
            "money_at_risk: invalid decimal",
        )
        reject(
            source.apply(
                lambda row: (
                    row["source_dataset"] == "attendance_monthly_features"
                    and not is_blank(row["money_at_risk"])
                ),
                axis=1,
            ),
            "money_at_risk: must be blank for attendance rows",
        )

        # Validate payroll record references against the supplied payroll fact.
        payroll = read_csv("fact_payroll")
        payroll_ids = set(payroll["payroll_item_id"])
        payroll_employee = dict(
            zip(payroll["payroll_item_id"], payroll["employee_id"])
        )
        payroll_rows = source["source_dataset"].eq("payroll_monthly_features")
        payroll_records = source["record_id"].isin(payroll_ids)

        reject(
            payroll_rows & ~payroll_records,
            "record_id: not found in supplied fact_payroll source",
        )
        reject(
            payroll_rows & payroll_records & source.apply(
                lambda row: (
                    row["source_dataset"] == "payroll_monthly_features"
                    and row["record_id"] in payroll_employee
                    and payroll_employee[row["record_id"]] != row["employee_id"]
                ),
                axis=1,
            ),
            "record_id: employee_id does not match source payroll record",
        )

        # The separate attendance_monthly_features source is not supplied.
        # Its IDs cannot be verified against fact_attendance_monthly because
        # that table uses a different ID system.

    elif name == "fact_attrition_risk":
        reject(
            ~source["employee_id"].isin(refs["active_employee_ids"]),
            "employee_id: employee is not currently active",
        )
        reject(
            ~source["department_id"].isin(refs["department_ids"]),
            "department_id: unknown department",
        )
        reject(
            source["risk_score_12m"].map(
                lambda value: valid_number(value)
                and not 0 <= float(value) <= 1
            ),
            "risk_score_12m: must be between 0 and 1",
        )
        reject(
            ~source["risk_band"].isin(["Low", "Medium", "High"]),
            "risk_band: unsupported value",
        )

        # The contract requires one as_of_date for the whole batch.
        as_of_dates = source["as_of_date"].fillna("").astype(str).str.strip()
        valid_as_of_dates = as_of_dates.map(valid_date)

        reject(
            ~valid_as_of_dates,
            "as_of_date: missing or invalid date",
        )

        valid_dates = as_of_dates[valid_as_of_dates]
        if not valid_dates.empty:
            batch_date = valid_dates.mode().iloc[0]
            reject(
                valid_as_of_dates & as_of_dates.ne(batch_date),
                f"as_of_date: differs from batch date {batch_date}",
            )

    elif name == "fact_forecast":
        reject(
            ~source["metric"].isin(
                ["headcount_end", "attrition_rate_monthly_pct"]
            ),
            "metric: unsupported value",
        )
        reject(
            source["department_id"].map(
                lambda value: value != "ALL"
                and value not in refs["department_ids"]
            ),
            "department_id: unknown department",
        )
        reject(
            source["forecast_month"].map(
                lambda value: valid_date(value)
                and pd.Timestamp(value).day != 1
            ),
            "forecast_month: must be the first day of the month",
        )
        reject(
            source["forecast_value"].map(
                lambda value: valid_number(value) and float(value) < 0
            ),
            "forecast_value: must be non-negative",
        )
        reject(
            source.apply(
                lambda row: (
                    valid_number(row["lower_80"])
                    and valid_number(row["forecast_value"])
                    and float(row["lower_80"]) > float(row["forecast_value"])
                ),
                axis=1,
            ),
            "lower_80: exceeds forecast_value",
        )
        reject(
            source.apply(
                lambda row: (
                    valid_number(row["upper_80"])
                    and valid_number(row["forecast_value"])
                    and float(row["upper_80"]) < float(row["forecast_value"])
                ),
                axis=1,
            ),
            "upper_80: below forecast_value",
        )
        reject(
            source["trained_through"].map(
                lambda value: not bool(
                    re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value.strip())
                )
            ),
            "trained_through: expected YYYY-MM",
        )

    # Keep the original columns and attach all applicable rejection reasons.
    rejected_mask = pd.Series([bool(items) for items in reasons])
    clean = source.loc[~rejected_mask, original_columns].copy()
    rejected = source.loc[rejected_mask, original_columns].copy()
    rejected["rejection_reason"] = [
        "; ".join(reasons[i])
        for i in range(len(source))
        if rejected_mask.iloc[i]
    ]

    CLEAN.mkdir(parents=True, exist_ok=True)
    REJECTED.mkdir(parents=True, exist_ok=True)

    clean.to_csv(CLEAN / f"{name}.csv", index=False)
    rejected.to_csv(REJECTED / f"{name}.csv", index=False)

    return {
        "table": name,
        "rows_in": len(source),
        "rows_passed": len(clean),
        "rows_quarantined": len(rejected),
    }


def validate_all():
    contracts = pd.read_csv(RAW / "data_contracts.csv", dtype=str).fillna("")
    refs = load_reference_values()
    results = []

    for name, feed in FEEDS.items():
        results.append(validate_feed(name, feed, contracts, refs))

    summary = pd.DataFrame(results)
    summary["counts_reconcile"] = (
        summary["rows_in"]
        == summary["rows_passed"] + summary["rows_quarantined"]
    )

    log_dir = ROOT / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(log_dir / "etl_summary.csv", index=False)

    print("\nTASK 1 VALIDATION SUMMARY")
    print(summary.to_string(index=False))
    print("\nSummary saved to Logs/etl_summary.csv")
    print("Clean files saved to Data/Clean/")
    print("Rejected rows saved to Data/Rejected/")

    if not summary["counts_reconcile"].all():
        raise RuntimeError("Row counts do not reconcile.")


if __name__ == "__main__":
    validate_all()


