"""
forecast.utils 单元测试
"""

import os
import sys
import unittest
from datetime import date, timedelta

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from forecast.schemas import HistoricalDataPoint
from forecast.utils import to_dataframe, compute_error_std_by_origin, DEFAULT_ERROR_SIGMA


class TestToDataframe(unittest.TestCase):
    """to_dataframe 测试。"""

    def test_output_columns_and_sorting(self):
        points = [
            HistoricalDataPoint(date=date(2024, 1, 3), units_sold=30.0),
            HistoricalDataPoint(date=date(2024, 1, 1), units_sold=10.0),
            HistoricalDataPoint(date=date(2024, 1, 2), units_sold=20.0),
        ]
        df = to_dataframe(points)
        self.assertEqual(list(df.columns), ["date", "datetime", "units_sold", "dayofweek", "month"])
        # 应按日期升序
        self.assertEqual(df.iloc[0]["units_sold"], 10.0)
        self.assertEqual(df.iloc[2]["units_sold"], 30.0)

    def test_dayofweek_and_month_populated(self):
        points = [HistoricalDataPoint(date=date(2024, 6, 15), units_sold=5.0)]
        df = to_dataframe(points)
        self.assertEqual(df.iloc[0]["dayofweek"], date(2024, 6, 15).weekday())
        self.assertEqual(df.iloc[0]["month"], 6)


class TestComputeErrorStdByOrigin(unittest.TestCase):
    """compute_error_std_by_origin 测试。"""

    def _make_forecast_df(self):
        """构造一个简单的 forecast_df 用于测试。

        每个 origin_date 有 1 个 forecast_error（horizon=1），误差值随 origin_day 变化，
        确保 std(ddof=1) > 0。
        """
        rows = []
        for origin_day in range(1, 20):
            origin_date = date(2024, 1, origin_day)
            forecast_date = origin_date + timedelta(days=1)
            has_actual = forecast_date <= date(2024, 1, 20)
            # 使用随 origin_day 变化的误差值，避免 std=0
            error = float(origin_day) if has_actual else None
            rows.append({
                "forecast_origin_date": origin_date.strftime("%Y-%m-%d"),
                "forecast_date": forecast_date.strftime("%Y-%m-%d"),
                "store_id": "S001",
                "product_id": "P001",
                "forecast_units_sold": 10.0,
                "actual_units_sold": 10.0 + error if error is not None else None,
                "forecast_error": error,
                "status": "ready",
                "model_version": "test",
                "calculated_at": "2024-01-01T00:00:00",
            })
        return pd.DataFrame(rows)

    def test_returns_error_std_for_all_origins(self):
        df = self._make_forecast_df()
        result = compute_error_std_by_origin(df, error_window_days=30)
        # 每个 origin_date 应有一行
        origins_in = df["forecast_origin_date"].nunique()
        self.assertEqual(len(result), origins_in)

    def test_fallback_sigma_when_insufficient_errors(self):
        df = self._make_forecast_df()
        # 用极小窗口，使得某些 origin 只有 0 或 1 个误差
        result = compute_error_std_by_origin(df, error_window_days=1)
        # 第一天 (2024-01-01) 的误差在窗口内只有 1 个 → fallback
        first = result[result["forecast_origin_date"] == "2024-01-01"]
        self.assertEqual(float(first.iloc[0]["error_std"]), DEFAULT_ERROR_SIGMA)

    def test_computed_sigma_matches_sample_std(self):
        df = self._make_forecast_df()
        result = compute_error_std_by_origin(df, error_window_days=30)
        # 取最后一个有误差的 origin_date，应该有足够误差来计算真实 std
        # origin_day=20 没有误差（forecast_date > 2024-01-20），所以取 origin_day=19
        last = result[result["forecast_origin_date"] == "2024-01-19"]
        self.assertGreater(float(last.iloc[0]["error_std"]), 0)


if __name__ == "__main__":
    unittest.main()
