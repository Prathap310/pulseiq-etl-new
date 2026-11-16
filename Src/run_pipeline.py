from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import csv

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "Logs"
RUN_LOG = LOG_DIR / "pipeline_runs.csv"
ETL_SCRIPT = ROOT / "Src" / "etl.py"
DQ_SCRIPT = ROOT / "Data_Quality" / "run_dq_checks.py"


def run_script(script):
    print(f"\nRunning: {script.relative_to(ROOT)}")
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=False,
    )


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"Pipeline started at {started}")

    etl_result = run_script(ETL_SCRIPT)
    exit_code = etl_result.returncode

    if exit_code == 0:
        dq_result = run_script(DQ_SCRIPT)
        if dq_result.returncode != 0:
            print("Data-quality gate failed; pipeline will report FAILED.")
            exit_code = dq_result.returncode
    else:
        print("ETL failed; skipping data-quality checks.")

    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = "SUCCESS" if exit_code == 0 else "FAILED"

    write_header = not RUN_LOG.exists() or RUN_LOG.stat().st_size == 0
    with RUN_LOG.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow([
                "started_at_utc", "finished_at_utc", "status", "exit_code"
            ])
        writer.writerow([started, finished, status, exit_code])

    print(f"\nPipeline finished at {finished}")
    print(f"Status: {status}")
    print(f"Run log: {RUN_LOG.relative_to(ROOT)}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
