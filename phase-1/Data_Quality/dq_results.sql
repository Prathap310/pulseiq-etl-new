-- PulseIQ Task 3: Data quality results history
CREATE TABLE IF NOT EXISTS dw.dq_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    check_id VARCHAR(20) NOT NULL,
    check_name VARCHAR(150) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    bad_row_count BIGINT NOT NULL CHECK (bad_row_count >= 0),
    status VARCHAR(10) NOT NULL CHECK (status IN ('PASS', 'FAIL', 'ERROR')),
    run_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_dq_results_run_at
    ON dw.dq_results (run_at DESC);

CREATE INDEX IF NOT EXISTS idx_dq_results_check_id
    ON dw.dq_results (check_id, run_at DESC);
