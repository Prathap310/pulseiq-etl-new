from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import csv

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "Logs"
RUN_LOG = LOG_DIR / "pipeline_runs.csv"
VALIDATOR = ROOT / "Src" / "etl.py"


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"Pipeline started at {started}")

    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        check=False,
    )

    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = "SUCCESS" if result.returncode == 0 else "FAILED"

    write_header = not RUN_LOG.exists() or RUN_LOG.stat().st_size == 0
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["started_at_utc", "finished_at_utc", "status", "exit_code"])
        writer.writerow([started, finished, status, result.returncode])

    print(f"Pipeline finished at {finished}")
    print(f"Status: {status}")
    print(f"Run log: {RUN_LOG.relative_to(ROOT)}")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
