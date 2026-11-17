
import unittest
from unittest.mock import MagicMock, patch

from Src.kpi_repository import save_draft, load_kpis, approve_kpi
from Src.kpi_builder import EXAMPLES


class TestKPIRepository(unittest.TestCase):

    def setUp(self):
        self.definition = dict(EXAMPLES[0])
        self.definition["name"] = "Repository test KPI"

    @patch("Src.kpi_repository.RealDictCursor")
    @patch("Src.kpi_repository.Json")
    def test_save_draft(self, mock_json, mock_cursor):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        cursor.fetchone.side_effect = [
            {"next_version": 1},
            {
                "kpi_id": 1,
                "name": "Repository test KPI",
                "version": 1,
                "status": "draft",
                "created_by": "admin",
                "created_at": None,
            },
        ]

        result = save_draft(
            connection, self.definition, "admin"
        )

        self.assertEqual(result["status"], "draft")
        self.assertEqual(result["version"], 1)
        connection.commit.assert_called_once()

    @patch("Src.kpi_repository.RealDictCursor")
    def test_load_drafts(self, mock_cursor):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchall.return_value = [
            {"kpi_id": 1, "status": "draft"}
        ]

        result = load_kpis(connection, "draft")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "draft")

    @patch("Src.kpi_repository.RealDictCursor")
    def test_approve_draft(self, mock_cursor):
        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {
            "kpi_id": 1,
            "status": "approved",
            "approved_by": "admin",
        }

        result = approve_kpi(connection, 1, "admin")

        self.assertEqual(result["status"], "approved")
        connection.commit.assert_called_once()

    def test_save_requires_creator(self):
        connection = MagicMock()

        with self.assertRaises(ValueError):
            save_draft(connection, self.definition, "")

    def test_approve_requires_approver(self):
        connection = MagicMock()

        with self.assertRaises(ValueError):
            approve_kpi(connection, 1, "")


if __name__ == "__main__":
    unittest.main()
