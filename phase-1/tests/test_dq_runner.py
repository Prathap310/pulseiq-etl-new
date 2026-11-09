import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import os
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Data_Quality"))

import run_dq_checks as dq


class TestDQRunner(unittest.TestCase):

    def test_all_14_checks_are_defined(self):
        self.assertEqual(len(dq.CHECKS), 14)
        self.assertEqual(len({check[0] for check in dq.CHECKS}), 14)

    def test_critical_and_warning_severities_are_defined(self):
        severities = {check[3] for check in dq.CHECKS}
        self.assertEqual(severities, {"critical", "warning"})

    def test_missing_pipeline_summary_fails_freshness_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(dq, "ROOT", Path(temp_dir)):
                self.assertEqual(dq.pipeline_bad_rows(), 1)

    def test_fresh_pipeline_summary_passes_freshness_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logs = Path(temp_dir) / "Logs"
            logs.mkdir()
            summary = logs / "etl_summary.csv"
            summary.write_text("status\nsuccess\n", encoding="utf-8")

            with patch.object(dq, "ROOT", Path(temp_dir)):
                self.assertEqual(dq.pipeline_bad_rows(), 0)

    def test_stale_pipeline_summary_fails_freshness_check(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            logs = Path(temp_dir) / "Logs"
            logs.mkdir()
            summary = logs / "etl_summary.csv"
            summary.write_text("status\nsuccess\n", encoding="utf-8")
            old_time = time.time() - (25 * 60 * 60)
            os.utime(summary, (old_time, old_time))

            with patch.object(dq, "ROOT", Path(temp_dir)):
                self.assertEqual(dq.pipeline_bad_rows(), 1)

    def test_c14_counts_mocked_metric_group_violations(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,)
        thresholds = {
            metric_id: 5
            for metric_id in [
                "M01", "M02", "M03", "M04", "M05", "M06",
                "M10", "M11", "M12", "M13", "M14", "M22",
                "M23", "M25", "M27"
            ]
        }

        total, details = dq.dq_c14_bad_groups(cursor, thresholds)

        self.assertEqual(total, len(thresholds))
        self.assertEqual(cursor.execute.call_count, len(thresholds))
        self.assertIn("M07/M08/M09/M15 excluded", details)


if __name__ == "__main__":
    unittest.main()
