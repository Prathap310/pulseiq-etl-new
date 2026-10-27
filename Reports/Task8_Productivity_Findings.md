# Task 8 — Team Productivity Dashboard

## 1. Metric definitions and rules

- **Velocity:** Sum of story points for tasks with status `Done`, grouped by team and sprint.
- **Average cycle time:** Average of completed date minus start date for `Done` tasks with both dates available. Display only when at least 5 qualifying tasks exist.
- **Completion rate:** Done tasks divided by non-cancelled tasks, multiplied by 100. Display only when at least 5 non-cancelled tasks exist.
- **On-time delivery:** On-time Done tasks divided by all Done tasks, multiplied by 100. Display only when at least 5 Done tasks exist.
- **Cancelled tasks:** Excluded from the completion-rate denominator and delivery-performance metrics.
- **Blocked and reopened work:** Reported separately as delivery signals, not as standalone proof of poor performance.
- **Minimum sample rule:** Suppress rates and averages when fewer than 5 qualifying tasks are available.

## 2. Manual verification

Source: `03_Data/csv/fact_task.csv`, joined to `03_Data/csv/dim_team.csv`.

The independent calculations match the dashboard for both selected teams.

| Team | Metric | Verified value | Status |
|---|---|---:|---|
| Analytics & BI | Total tasks | 1,135 | PASS |
| Analytics & BI | Non-cancelled tasks | 1,093 | PASS |
| Analytics & BI | Done tasks | 983 | PASS |
| Analytics & BI | On-time completed tasks | 921 | PASS |
| Analytics & BI | Completion rate | 89.94% | PASS |
| Analytics & BI | On-time delivery | 93.69% | PASS |
| Data Platform | Total tasks | 1,061 | PASS |
| Data Platform | Non-cancelled tasks | 1,025 | PASS |
| Data Platform | Done tasks | 889 | PASS |
| Data Platform | On-time completed tasks | 841 | PASS |
| Data Platform | Completion rate | 86.73% | PASS |
| Data Platform | On-time delivery | 94.60% | PASS |

**Verification result:** 12 of 12 comparisons passed; every difference was zero.

Detailed verification output: `Reports/Task8_Team_Verification.csv`.

## 3. Three dashboard findings

1. **Highest completed story-point total:** Support Tooling recorded 401 points in Sprint 37 within the selected dashboard scope.
2. **Longest average cycle time among groups meeting the five-task threshold:** Growth Marketing recorded 7.64 days in Sprint 13.
3. **Blocked and reopened work:** Support Tooling had 177 blocked tasks and 142 reopened events in the selected scope. These counts indicate areas for investigation, not a standalone judgment of team performance.

## 4. Dashboard features

- Team selector
- Sprint selector
- Delivery overview metrics
- Velocity by sprint and team
- Cycle time by sprint and team
- Completion and on-time delivery by team
- Blocked tasks and reopened events
- Numerical findings section

## 5. Evidence checklist

- [x] Dashboard renders successfully
- [x] Metric definitions and rules displayed
- [x] Team and sprint filters displayed
- [x] Delivery charts and summary tables displayed
- [x] Blocked and reopened work displayed
- [x] Three numerical findings displayed
- [x] Two teams manually verified against source data
- [x] Verification CSV created
- [ ] Dashboard screenshots saved in the Reports folder
- [ ] Final Git commit and push completed
