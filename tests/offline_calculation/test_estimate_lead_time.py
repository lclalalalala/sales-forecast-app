"""
测试 K 估计 - tests/offline_calculation/test_estimate_lead_time.py
"""

import os
import tempfile
import unittest
from datetime import datetime

from offline_calculation.config import OfflineConfig
from offline_calculation.steps.build_fact import build_fact_daily_inventory_sales
from offline_calculation.steps.estimate_lead_time import estimate_lead_time
from offline_calculation.steps.load_validate import load_and_validate


class TestEstimateLeadTime(unittest.TestCase):
    """测试提前期 K 估计。"""

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_sales_data.csv"
        )
        self.config = OfflineConfig.from_file()

    def test_estimate_lead_time(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_df, _ = load_and_validate(self.fixture_path, tmpdir)
            fact = build_fact_daily_inventory_sales(raw_df)
            lead_time_df = estimate_lead_time(
                fact,
                config=self.config,
                calculated_at=datetime.now(),
            )

            self.assertIn("lead_time_days", lead_time_df.columns)
            self.assertIn("effective_lead_time_days", lead_time_df.columns)
            self.assertIn("k_source", lead_time_df.columns)
            self.assertTrue((lead_time_df["effective_lead_time_days"] >= 1).all())


if __name__ == "__main__":
    unittest.main()
