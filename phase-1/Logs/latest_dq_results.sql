SELECT check_id, status, bad_row_count, details
FROM (
    SELECT DISTINCT ON (check_id)
        check_id, status, bad_row_count, details, created_at
    FROM dw.dq_results
    ORDER BY check_id, created_at DESC
) latest
ORDER BY check_id;
