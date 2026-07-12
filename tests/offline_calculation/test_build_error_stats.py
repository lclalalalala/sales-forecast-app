"""
测试预测误差统计 - tests/offline_calculation/test_build_error_stats.py
"""

import os
import tempfile
import unittest
from datetime import datetime

import pandas as pd

from offline_calculation.config import OfflineConfig
from offline_calculation.steps.build_error_stats import build_error_stats
from offline_calculation.steps.build_fact import build_fact_daily_inventory_sales
from offline_calculation.steps.build_forecast import build_forecast
from offline_calculation.steps.load_validate import load_and_validate


class TestBuildErrorStats(unittest.TestCase):
    """测试 horizon=3 / 30 天误差标准差计算。"""

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_sales_data.csv"
        )
        self.config = OfflineConfig.from_file()

    def test_error_stats_horizon_and_window(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_df, _ = load_and_validate(self.fixture_path, tmpdir)
            fact = build_fact_daily_inventory_sales(raw_df)
            max_date = pd.to_datetime(fact["date"]).max()
            as_of_date = max_date - pd.Timedelta(days=7)

            forecast_df = build_forecast(
                fact,
                as_of_date=as_of_date,
                model_version="ensemble_v2",
                error_window_days=30,
            )

            error_stats_df = build_error_stats(
                forecast_df,
                config=self.config,
                model_version="ensemble_v2",
                calculated_at=datetime.now(),
            )

            self.assertFalse(error_stats_df.empty)
            self.assertTrue((error_stats_df["horizon"] == 3).all())
            self.assertTrue((error_stats_df["window_days"] == 30).all())


if __name__ == "__main__":
    unittest.main()
