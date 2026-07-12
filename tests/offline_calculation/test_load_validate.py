"""
测试加载与校验步骤 - tests/offline_calculation/test_load_validate.py
"""

import os
import tempfile
import unittest

import pandas as pd

from offline_calculation.steps.load_validate import load_and_validate


class TestLoadValidate(unittest.TestCase):
    """测试原始数据加载与校验。"""

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_sales_data.csv"
        )

    def test_load_and_validate_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_df, report = load_and_validate(self.fixture_path, tmpdir)
            self.assertGreater(len(raw_df), 0)
            self.assertEqual(report["status"], "pass")
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "data_quality_report.json")))

    def test_missing_columns_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_df = pd.DataFrame({"Date": ["2024-01-01"], "Store ID": ["S001"]})
            bad_path = os.path.join(tmpdir, "bad.csv")
            bad_df.to_csv(bad_path, index=False)
            with self.assertRaises(ValueError):
                load_and_validate(bad_path, tmpdir)

    def test_negative_values_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.read_csv(self.fixture_path)
            df.loc[0, "Units Sold"] = -1
            bad_path = os.path.join(tmpdir, "bad.csv")
            df.to_csv(bad_path, index=False)
            with self.assertRaises(ValueError):
                load_and_validate(bad_path, tmpdir)


if __name__ == "__main__":
    unittest.main()
