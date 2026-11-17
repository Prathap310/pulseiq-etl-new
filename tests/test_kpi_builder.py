import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Src.kpi_builder import (
    EXAMPLES,
    approved_metrics,
    approve_metric,
    build_query,
    validate_definition,
)


class TestCustomKPIBuilder(unittest.TestCase):

    def test_all_five_examples_validate(self):
        self.assertEqual(len(EXAMPLES), 5)
        for definition in EXAMPLES:
            with self.subTest(metric=definition["name"]):
                validate_definition(definition)

    def test_all_five_examples_generate_queries(self):
        for definition in EXAMPLES:
            with self.subTest(metric=definition["name"]):
                sql, params = build_query(definition)
                self.assertIn("FROM dw.", sql)
                self.assertIn("privacy_threshold_met", sql)
                self.assertIsInstance(params, list)

    def test_ratio_protects_against_division_by_zero(self):
        sql, _ = build_query(EXAMPLES[0])
        self.assertIn("NULLIF", sql)

    def test_injection_in_filter_is_bound_parameter(self):
        definition = copy.deepcopy(EXAMPLES[1])
        malicious = "'; DROP TABLE dw.fact_payroll; --"
        definition["filters"] = [
            {
                "column": "department_id",
                "operator": "=",
                "value": malicious,
            }
        ]

        sql, params = build_query(definition)

        self.assertNotIn(malicious, sql)
        self.assertIn("%s", sql)
        self.assertIn(malicious, params)

    def test_unknown_column_is_rejected(self):
        definition = copy.deepcopy(EXAMPLES[1])
        definition["group_by"] = ["employee_id; DROP TABLE dw.fact_payroll"]

        with self.assertRaises(ValueError):
            validate_definition(definition)

    def test_unknown_table_is_rejected(self):
        definition = copy.deepcopy(EXAMPLES[1])
        definition["source_table"] = "dw.users"

        with self.assertRaises(ValueError):
            validate_definition(definition)

    def test_invalid_operator_is_rejected(self):
        definition = copy.deepcopy(EXAMPLES[1])
        definition["filters"] = [
            {
                "column": "department_id",
                "operator": "OR 1=1",
                "value": "x",
            }
        ]

        with self.assertRaises(ValueError):
            validate_definition(definition)

    def test_invalid_aggregation_is_rejected(self):
        definition = copy.deepcopy(EXAMPLES[1])
        definition["measure"]["aggregation"] = "DROP TABLE"

        with self.assertRaises(ValueError):
            validate_definition(definition)

    def test_invoice_query_excludes_draft_and_cancelled(self):
        sql, _ = build_query(EXAMPLES[4])
        self.assertIn("due_date < CURRENT_DATE", sql)
        self.assertIn("status NOT IN ('DRAFT', 'CANCELLED')", sql)
        self.assertIn("client_id", sql)

    def test_invoice_query_has_minimum_group_size(self):
        sql, _ = build_query(EXAMPLES[4], minimum_group_size=5)
        self.assertIn("HAVING COUNT(DISTINCT invoice_id) >= 5", sql)

    def test_approval_requires_approver(self):
        with self.assertRaises(ValueError):
            approve_metric(EXAMPLES[0], "")

    def test_only_approved_metrics_are_visible(self):
        approved = approve_metric(EXAMPLES[0], "Admin")
        results = approved_metrics([EXAMPLES[1], approved])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "approved")
        self.assertEqual(results[0]["approved_by"], "Admin")


if __name__ == "__main__":
    unittest.main()
