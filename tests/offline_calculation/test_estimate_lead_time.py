"""
测试 K 估计 - tests/offline_calculation/test_estimate_lead_time.py
"""

import os
import tempfile
import unittest
from datetime import datetime

import pandas as pd

from offline_calculation.config import OfflineConfig
from offline_calculation.steps.build_fact import build_fact_daily_inventory_sales
from offline_calculation.steps.estimate_lead_time import (
    _estimate_single,
    estimate_lead_time,
)
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

    def test_skip_non_consecutive_pairs(self):
        """观测缺口处（相邻两行相差 >1 天）的行对必须跳过，否则平衡方程被污染。

        构造一段满足 K=2 平衡方程的序列，缺失 01-04 形成缺口。仅当跳过缺口
        行对 (01-03, 01-05) 时，K=2 才能取得 MSE=0；若不跳过，该缺口对会引入
        残差 100，使 best_mse≠0。
        """
        group = pd.DataFrame({
            "date": pd.to_datetime([
                "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-05", "2026-01-06",
            ]),
            "opening_inventory": [100, 90, 80, 80, 85],
            "units_sold": [10, 10, 10, 10, 10],
            "units_ordered": [20, 0, 15, 0, 0],
        })

        best_k, best_mse, _, _ = _estimate_single(group, min_k=0, max_k=7, fallback_k=2)

        self.assertEqual(best_k, 2)
        self.assertEqual(best_mse, 0.0)


if __name__ == "__main__":
    unittest.main()
