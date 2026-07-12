"""
测试补货推荐计算 - tests/offline_calculation/test_build_replenishment.py
"""

import math
import os
import tempfile
import unittest
from datetime import datetime

import pandas as pd

from offline_calculation.config import OfflineConfig
from offline_calculation.steps.build_error_stats import build_error_stats
from offline_calculation.steps.build_fact import build_fact_daily_inventory_sales
from offline_calculation.steps.build_forecast import build_forecast
from offline_calculation.steps.build_replenishment import build_daily_replenishment
from offline_calculation.steps.estimate_lead_time import estimate_lead_time
from offline_calculation.steps.load_validate import load_and_validate


class TestBuildReplenishment(unittest.TestCase):
    """测试补货推荐计算逻辑。"""

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_sales_data.csv"
        )
        self.config = OfflineConfig.from_file()

    def test_replenishment_formula(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_df, _ = load_and_validate(self.fixture_path, tmpdir)
            fact = build_fact_daily_inventory_sales(raw_df)
            max_date = pd.to_datetime(fact["date"]).max()
            as_of_date = max_date - pd.Timedelta(days=7)

            lead_time_df = estimate_lead_time(fact, config=self.config, calculated_at=datetime.now())
            forecast_df = build_forecast(
                fact,
                as_of_date=as_of_date,
                model_version="ensemble_v2",
            )
            error_stats_df = build_error_stats(
                forecast_df,
                config=self.config,
                model_version="ensemble_v2",
                calculated_at=datetime.now(),
            )
            repl_df = build_daily_replenishment(
                fact,
                lead_time_df,
                forecast_df,
                error_stats_df,
                config=self.config,
                as_of_date=as_of_date,
                data_version="v1",
                model_version="ensemble_v2",
                calculated_at=datetime.now(),
            )

            self.assertFalse(repl_df.empty)
            self.assertTrue((repl_df["suggested_replenishment"] >= 0).all())

            # 抽查第一条记录的公式
            row = repl_df.iloc[0]
            k = int(row["effective_lead_time_days"])
            expected_safety = self.config.safety_stock_z * row["error_std"] * math.sqrt(k)
            self.assertAlmostEqual(row["safety_stock"], expected_safety, places=1)


if __name__ == "__main__":
    unittest.main()
