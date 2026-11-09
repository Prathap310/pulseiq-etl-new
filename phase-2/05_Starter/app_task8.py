
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PulseIQ | Task 8 Team Productivity",
    page_icon="📊",
    layout="wide",
)

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "03_Data" / "csv"
MIN_SAMPLE = 5

st.title("Task 8 — Team Productivity Dashboard")
st.caption(
    "Productivity metrics are descriptive measures of delivery. "
    "Velocity should be compared within a team over time, not across teams."
)

with st.expander("Metric definitions and rules", expanded=True):
    st.markdown(
        """
        - **Velocity:** sum of story points for tasks with status `Done`,
          grouped by team and sprint.
        - **Average cycle time:** average of completed date minus start
          date for `Done` tasks with both dates available. Display only
          when at least 5 qualifying tasks exist.
        - **Completion rate:** `Done` tasks divided by non-cancelled tasks,
          multiplied by 100. Display only when at least 5 non-cancelled
          tasks exist.
        - **On-time delivery:** on-time `Done` tasks divided by all `Done`
          tasks, multiplied by 100. Display only when at least 5 `Done`
          tasks exist.
        - **Cancelled tasks:** excluded from completion-rate denominator
          and excluded from delivery-performance metrics.
        - **Blocked and reopened work:** reported separately as delivery
          signals, not proof of poor performance.
        - **Privacy/sample rule:** suppress rates and averages when fewer
          than 5 qualifying tasks are available.
        """
    )


@st.cache_data
def load_csv(filename):
    path = CSV_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


try:
    tasks = load_csv("fact_task.csv")
    teams = load_csv("dim_team.csv")
    sprints = load_csv("dim_sprint.csv")
except Exception as exc:
    st.error(f"Could not load Task 8 source data: {exc}")
    st.stop()

required_task_columns = {
    "task_id", "team_id", "sprint_id", "story_points", "status",
    "started_date", "completed_date", "completed_on_time",
    "reopened_count", "cycle_time_days",
}
missing = required_task_columns - set(tasks.columns)
if missing:
    st.error(f"Missing task columns: {', '.join(sorted(missing))}")
    st.stop()

tasks["story_points"] = pd.to_numeric(
    tasks["story_points"], errors="coerce"
).fillna(0)
tasks["reopened_count"] = pd.to_numeric(
    tasks["reopened_count"], errors="coerce"
).fillna(0)
tasks["started_date"] = pd.to_datetime(
    tasks["started_date"], errors="coerce"
)
tasks["completed_date"] = pd.to_datetime(
    tasks["completed_date"], errors="coerce"
)
tasks["status"] = tasks["status"].astype(str).str.strip()
tasks["completed_on_time"] = (
    tasks["completed_on_time"].astype(str).str.upper().str.strip()
)

team_map = teams.set_index("team_id")["team_name"].to_dict()
sprint_map = sprints.set_index("sprint_id")["sprint_name"].to_dict()

tasks["team_name"] = tasks["team_id"].map(team_map).fillna(tasks["team_id"])
tasks["sprint_name"] = (
    tasks["sprint_id"].map(sprint_map).fillna(tasks["sprint_id"])
)

st.sidebar.header("Filters")
team_options = sorted(tasks["team_name"].dropna().unique().tolist())
sprint_options = sprints.sort_values("start_date")[
    ["sprint_id", "sprint_name"]
].drop_duplicates()

selected_teams = st.sidebar.multiselect(
    "Team", team_options, default=team_options
)
selected_sprints = st.sidebar.multiselect(
    "Sprint",
    sprint_options["sprint_name"].tolist(),
    default=sprint_options["sprint_name"].tolist(),
)

filtered = tasks[
    tasks["team_name"].isin(selected_teams)
    & tasks["sprint_name"].isin(selected_sprints)
].copy()

if filtered.empty:
    st.warning("No tasks match the selected team and sprint filters.")
    st.stop()

# Historical delivery calculations use non-cancelled work.
non_cancelled = filtered[filtered["status"] != "Cancelled"].copy()
done = filtered[filtered["status"] == "Done"].copy()
valid_cycle = done[
    done["started_date"].notna()
    & done["completed_date"].notna()
    & done["completed_date"].ge(done["started_date"])
].copy()
valid_cycle["calculated_cycle_days"] = (
    valid_cycle["completed_date"] - valid_cycle["started_date"]
).dt.total_seconds() / 86400

done_count = len(done)
planned_count = len(non_cancelled)
completion_rate = (
    100 * done_count / planned_count if planned_count >= MIN_SAMPLE else None
)
on_time_count = int((done["completed_on_time"] == "Y").sum())
on_time_rate = (
    100 * on_time_count / done_count if done_count >= MIN_SAMPLE else None
)
velocity = done["story_points"].sum()
avg_cycle = (
    valid_cycle["calculated_cycle_days"].mean()
    if len(valid_cycle) >= MIN_SAMPLE else None
)

blocked_count = int((filtered["status"] == "Blocked").sum())
reopened_total = int(filtered["reopened_count"].sum())
cancelled_count = int((filtered["status"] == "Cancelled").sum())

st.header("Delivery overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Completed story points", f"{velocity:,.0f}")
c2.metric(
    "Completion rate",
    f"{completion_rate:.1f}%" if completion_rate is not None else "Suppressed (<5 tasks)",
)
c3.metric(
    "On-time delivery",
    f"{on_time_rate:.1f}%" if on_time_rate is not None else "Suppressed (<5 Done tasks)",
)
c4.metric(
    "Average cycle time",
    f"{avg_cycle:.1f} days" if avg_cycle is not None else "Suppressed (<5 valid tasks)",
)

st.caption(
    f"Selected scope: {len(filtered):,} tasks · "
    f"{done_count:,} Done · {cancelled_count:,} Cancelled"
)

st.divider()
st.header("Velocity by sprint and team")
velocity_table = (
    done.groupby(["sprint_name", "team_name"], as_index=False)
    .agg(completed_story_points=("story_points", "sum"))
)
if velocity_table.empty:
    st.info("No completed tasks in the selected scope.")
else:
    st.bar_chart(
        velocity_table.pivot(
            index="sprint_name",
            columns="team_name",
            values="completed_story_points",
        ).fillna(0)
    )
    st.dataframe(
        velocity_table.sort_values(
            ["sprint_name", "team_name"]
        ),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.header("Cycle time by sprint and team")
cycle_table = (
    valid_cycle.groupby(["sprint_name", "team_name"], as_index=False)
    .agg(
        valid_tasks=("task_id", "count"),
        average_cycle_time_days=("calculated_cycle_days", "mean"),
    )
)
cycle_table["average_cycle_time_days"] = cycle_table[
    "average_cycle_time_days"
].round(2)
cycle_table.loc[
    cycle_table["valid_tasks"] < MIN_SAMPLE,
    "average_cycle_time_days",
] = float("nan")

if cycle_table.empty:
    st.info("No valid cycle-time records in the selected scope.")
else:
    st.bar_chart(
        cycle_table.pivot(
            index="sprint_name",
            columns="team_name",
            values="average_cycle_time_days",
        )
    )
    st.dataframe(cycle_table, use_container_width=True, hide_index=True)

st.divider()
st.header("Completion and on-time delivery by team")
team_delivery = (
    filtered.groupby("team_name")
    .apply(
        lambda g: pd.Series(
            {
                "total_tasks": len(g),
                "non_cancelled_tasks": int((g["status"] != "Cancelled").sum()),
                "done_tasks": int((g["status"] == "Done").sum()),
                "on_time_done": int(
                    (
                        (g["status"] == "Done")
                        & (g["completed_on_time"] == "Y")
                    ).sum()
                ),
            }
        ),
        include_groups=False,
    )
    .reset_index()
)
team_delivery["completion_rate_pct"] = (
    100 * team_delivery["done_tasks"]
    / team_delivery["non_cancelled_tasks"].replace(0, pd.NA)
)
team_delivery["on_time_delivery_pct"] = (
    100 * team_delivery["on_time_done"]
    / team_delivery["done_tasks"].replace(0, pd.NA)
)
team_delivery.loc[
    team_delivery["non_cancelled_tasks"] < MIN_SAMPLE,
    "completion_rate_pct",
] = pd.NA
team_delivery.loc[
    team_delivery["done_tasks"] < MIN_SAMPLE,
    "on_time_delivery_pct",
] = pd.NA
team_delivery[["completion_rate_pct", "on_time_delivery_pct"]] = (
    team_delivery[["completion_rate_pct", "on_time_delivery_pct"]].round(2)
)
st.dataframe(team_delivery, use_container_width=True, hide_index=True)

st.divider()
st.header("Blocked and reopened work")
issue_summary = (
    filtered.groupby(["team_name", "sprint_name"], as_index=False)
    .agg(
        blocked_tasks=("status", lambda s: int((s == "Blocked").sum())),
        reopened_events=("reopened_count", "sum"),
        cancelled_tasks=("status", lambda s: int((s == "Cancelled").sum())),
    )
)
left, right = st.columns(2)
with left:
    st.subheader("Blocked tasks")
    st.bar_chart(
        issue_summary.pivot(
            index="sprint_name",
            columns="team_name",
            values="blocked_tasks",
        ).fillna(0)
    )
with right:
    st.subheader("Reopened events")
    st.bar_chart(
        issue_summary.pivot(
            index="sprint_name",
            columns="team_name",
            values="reopened_events",
        ).fillna(0)
    )
st.dataframe(issue_summary, use_container_width=True, hide_index=True)

st.divider()
st.header("Three biggest findings")
findings = []

if not velocity_table.empty:
    top_velocity = velocity_table.loc[
        velocity_table["completed_story_points"].idxmax()
    ]
    findings.append(
        f"Highest completed story-point total in the selected scope: "
        f"{top_velocity['completed_story_points']:.0f} points for "
        f"{top_velocity['team_name']} in {top_velocity['sprint_name']}."
    )

if not cycle_table.empty:
    valid_cycle_rows = cycle_table.dropna(
        subset=["average_cycle_time_days"]
    )
    if not valid_cycle_rows.empty:
        slowest = valid_cycle_rows.loc[
            valid_cycle_rows["average_cycle_time_days"].idxmax()
        ]
        findings.append(
            f"Longest average cycle time among groups meeting the "
            f"{MIN_SAMPLE}-task threshold: "
            f"{slowest['average_cycle_time_days']:.2f} days for "
            f"{slowest['team_name']} in {slowest['sprint_name']}."
        )

if not issue_summary.empty:
    team_issues = issue_summary.groupby("team_name", as_index=False).agg(
        blocked_tasks=("blocked_tasks", "sum"),
        reopened_events=("reopened_events", "sum"),
    )
    busiest = team_issues.sort_values(
        ["blocked_tasks", "reopened_events"], ascending=False
    ).iloc[0]
    findings.append(
        f"{busiest['team_name']} has the most blocked tasks in the selected "
        f"scope ({busiest['blocked_tasks']:.0f}) and "
        f"{busiest['reopened_events']:.0f} reopened events."
    )

if findings:
    for i, finding in enumerate(findings, 1):
        st.markdown(f"**{i}.** {finding}")
else:
    st.info("Not enough data to generate findings for this selection.")

st.caption(
    "Source files: fact_task.csv, dim_team.csv, dim_sprint.csv. "
    "Findings are descriptive signals, not standalone performance judgments."
)
