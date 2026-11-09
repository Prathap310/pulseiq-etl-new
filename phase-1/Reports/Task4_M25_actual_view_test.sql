
BEGIN;

-- Task 4: M25 average cycle time privacy-threshold test
-- Run ONLY in the isolated pulseiq_dq_test database.
-- All test changes are rolled back at the end.

CREATE OR REPLACE VIEW dw.m25_average_cycle_time AS
SELECT
    team_id,
    sprint_id,
    CASE
        WHEN COUNT(*) FILTER (
            WHERE status = 'Done'
              AND started_date IS NOT NULL
              AND completed_date IS NOT NULL
        ) >= 5
        THEN ROUND(
            AVG(completed_date::date - started_date::date) FILTER (
                WHERE status = 'Done'
                  AND started_date IS NOT NULL
                  AND completed_date IS NOT NULL
            )::numeric,
            2
        )
        ELSE NULL
    END AS average_cycle_time_days,
    COUNT(*) FILTER (
        WHERE status = 'Done'
          AND started_date IS NOT NULL
          AND completed_date IS NOT NULL
    ) >= 5 AS privacy_threshold_met
FROM dw.fact_task
GROUP BY team_id, sprint_id;


-- Create test-only dimension records.
INSERT INTO dw.dim_team (team_id)
VALUES
    ('M25_TEST_TEAM_4'),
    ('M25_TEST_TEAM_5');

INSERT INTO dw.dim_sprint (sprint_id)
VALUES
    ('M25_TEST_SPRINT_4'),
    ('M25_TEST_SPRINT_5');


-- Below-threshold scenario: 4 eligible tasks.
-- Expected result: NULL average and privacy_threshold_met = false.
INSERT INTO dw.fact_task
    (task_id, team_id, sprint_id, status, started_date, completed_date)
VALUES
    ('M25_TASK_401', 'M25_TEST_TEAM_4', 'M25_TEST_SPRINT_4',
     'Done', DATE '2026-01-01', DATE '2026-01-03'),
    ('M25_TASK_402', 'M25_TEST_TEAM_4', 'M25_TEST_SPRINT_4',
     'Done', DATE '2026-01-01', DATE '2026-01-04'),
    ('M25_TASK_403', 'M25_TEST_TEAM_4', 'M25_TEST_SPRINT_4',
     'Done', DATE '2026-01-01', DATE '2026-01-05'),
    ('M25_TASK_404', 'M25_TEST_TEAM_4', 'M25_TEST_SPRINT_4',
     'Done', DATE '2026-01-01', DATE '2026-01-06');


-- At-threshold scenario: 5 eligible tasks.
-- Durations: 1, 2, 3, 4, 1 days.
-- Expected average: 2.20 days and privacy_threshold_met = true.
INSERT INTO dw.fact_task
    (task_id, team_id, sprint_id, status, started_date, completed_date)
VALUES
    ('M25_TASK_501', 'M25_TEST_TEAM_5', 'M25_TEST_SPRINT_5',
     'Done', DATE '2026-02-01', DATE '2026-02-02'),
    ('M25_TASK_502', 'M25_TEST_TEAM_5', 'M25_TEST_SPRINT_5',
     'Done', DATE '2026-02-01', DATE '2026-02-03'),
    ('M25_TASK_503', 'M25_TEST_TEAM_5', 'M25_TEST_SPRINT_5',
     'Done', DATE '2026-02-01', DATE '2026-02-04'),
    ('M25_TASK_504', 'M25_TEST_TEAM_5', 'M25_TEST_SPRINT_5',
     'Done', DATE '2026-02-01', DATE '2026-02-05'),
    ('M25_TASK_505', 'M25_TEST_TEAM_5', 'M25_TEST_SPRINT_5',
     'Done', DATE '2026-02-01', DATE '2026-02-02');


-- Display and validate both scenarios.
SELECT
    team_id,
    sprint_id,
    average_cycle_time_days,
    privacy_threshold_met,
    CASE
        WHEN team_id = 'M25_TEST_TEAM_4'
         AND average_cycle_time_days IS NULL
         AND privacy_threshold_met = FALSE
            THEN 'PASS'
        WHEN team_id = 'M25_TEST_TEAM_5'
         AND average_cycle_time_days = 2.20
         AND privacy_threshold_met = TRUE
            THEN 'PASS'
        ELSE 'FAIL'
    END AS test_result
FROM dw.m25_average_cycle_time
WHERE team_id IN ('M25_TEST_TEAM_4', 'M25_TEST_TEAM_5')
ORDER BY team_id;


-- Stop the script if either scenario fails.
DO $$
DECLARE
    below_threshold RECORD;
    at_threshold RECORD;
BEGIN
    SELECT *
    INTO below_threshold
    FROM dw.m25_average_cycle_time
    WHERE team_id = 'M25_TEST_TEAM_4'
      AND sprint_id = 'M25_TEST_SPRINT_4';

    IF NOT FOUND
       OR below_threshold.average_cycle_time_days IS NOT NULL
       OR below_threshold.privacy_threshold_met IS DISTINCT FROM FALSE
    THEN
        RAISE EXCEPTION 'M25 below-threshold test failed';
    END IF;

    SELECT *
    INTO at_threshold
    FROM dw.m25_average_cycle_time
    WHERE team_id = 'M25_TEST_TEAM_5'
      AND sprint_id = 'M25_TEST_SPRINT_5';

    IF NOT FOUND
       OR at_threshold.average_cycle_time_days IS DISTINCT FROM 2.20
       OR at_threshold.privacy_threshold_met IS DISTINCT FROM TRUE
    THEN
        RAISE EXCEPTION 'M25 at-threshold test failed';
    END IF;

    RAISE NOTICE 'PASS: Both M25 privacy-threshold tests passed.';
END $$;

ROLLBACK;
