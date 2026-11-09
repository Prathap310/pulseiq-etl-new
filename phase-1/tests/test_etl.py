import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Src"))

from validate_data import valid_date, valid_number, valid_integer


class TestETLValidation(unittest.TestCase):

    def test_valid_date(self):
        self.assertTrue(valid_date("2026-09-30"))

    def test_invalid_date(self):
        self.assertFalse(valid_date("2026-13-40"))

    def test_valid_number(self):
        self.assertTrue(valid_number("12.5"))

    def test_invalid_number(self):
        self.assertFalse(valid_number("not-a-number"))

    def test_valid_integer(self):
        self.assertTrue(valid_integer("10"))

    def test_invalid_integer(self):
        self.assertFalse(valid_integer("10.5"))


if __name__ == "__main__":
    unittest.main()
