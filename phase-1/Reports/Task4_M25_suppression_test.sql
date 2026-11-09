SELECT
    team_id,
    sprint_id,
    average_cycle_time_days,
    privacy_threshold_met
FROM dw.m25_average_cycle_time
WHERE privacy_threshold_met = FALSE
   OR average_cycle_time_days IS NULL
ORDER BY team_id, sprint_id
LIMIT 20;
