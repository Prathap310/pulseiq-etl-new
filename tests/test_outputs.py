import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class TestPipelineOutputs(unittest.TestCase):

    def test_summary_counts_reconcile(self):
        summary = pd.read_csv(ROOT / "Logs" / "etl_summary.csv")
        self.assertTrue(summary["counts_reconcile"].all())

    def test_attrition_batch_date_rows_quarantined(self):
        rejected = pd.read_csv(ROOT / "Data" / "Rejected" / "fact_attrition_risk.csv")
        self.assertEqual(len(rejected), 5)
        self.assertTrue(
            rejected["rejection_reason"]
            .str.contains("as_of_date: differs from batch date")
            .all()
        )

    def test_anomaly_timezone_issue_is_explicit(self):
        rejected = pd.read_csv(ROOT / "Data" / "Rejected" / "fact_anomaly.csv")
        self.assertEqual(len(rejected), 405)
        self.assertTrue(
            rejected["rejection_reason"]
            .str.contains("scored_at: invalid timestamp or missing timezone")
            .all()
        )

    def test_clean_attrition_and_forecast_counts(self):
        attrition = pd.read_csv(ROOT / "Data" / "Clean" / "fact_attrition_risk.csv")
        forecast = pd.read_csv(ROOT / "Data" / "Clean" / "fact_forecast.csv")
        self.assertEqual(len(attrition), 425)
        self.assertEqual(len(forecast), 72)


if __name__ == "__main__":
    unittest.main()
