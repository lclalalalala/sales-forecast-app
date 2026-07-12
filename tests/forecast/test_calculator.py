"""
EnsembleForecastCalculator 单元测试
"""

import os
import sys
import unittest
from datetime import date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from forecast.schemas import HistoricalDataPoint, ForecastInput
from forecast.calculator import EnsembleForecastCalculator


class TestEnsembleForecastCalculator(unittest.TestCase):
    """集成预测计算器测试。"""

    def setUp(self):
        self.calculator = EnsembleForecastCalculator()

    def _history(self, days: int, base_value: float = 10.0) -> list:
        """构造简单的历史数据序列。"""
        start = date(2024, 1, 1)
        return [
            HistoricalDataPoint(
                date=start + timedelta(days=i),
                units_sold=base_value + (i % 7),
            )
            for i in range(days)
        ]

    def test_ready_when_history_sufficient(self):
        history = self._history(30)
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
        )
        result = self.calculator.predict(inp)
        self.assertEqual(result.status, "ready")
        self.assertIsNone(result.message)
        self.assertEqual(len(result.daily_forecast), 7)
        self.assertEqual(len(result.prediction_interval), 7)

    def test_fallback_when_history_insufficient(self):
        history = self._history(5)
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 6),
        )
        result = self.calculator.predict(inp)
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(len(result.daily_forecast), 7)
        self.assertTrue(all(p.units_sold >= 0 for p in result.daily_forecast))

    def test_fallback_when_empty_history(self):
        inp = ForecastInput(
            historical_data=[],
            forecast_start_date=date(2024, 1, 1),
        )
        result = self.calculator.predict(inp)
        self.assertEqual(result.status, "insufficient_data")
        self.assertEqual(len(result.daily_forecast), 7)
        self.assertEqual(result.daily_forecast[0].units_sold, 10.0)

    def test_prediction_non_negative(self):
        history = [HistoricalDataPoint(date=date(2024, 1, 1) + timedelta(days=i), units_sold=0) for i in range(30)]
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
        )
        result = self.calculator.predict(inp)
        self.assertEqual(result.status, "ready")
        self.assertTrue(all(p.units_sold >= 0 for p in result.daily_forecast))

    def test_prediction_interval_bounds(self):
        history = self._history(30, base_value=20.0)
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
        )
        result = self.calculator.predict(inp)
        for interval in result.prediction_interval:
            self.assertGreaterEqual(interval.lower, 0)
            self.assertLessEqual(interval.lower, interval.upper)

    def test_custom_horizon(self):
        history = self._history(30)
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
            horizon_days=14,
        )
        result = self.calculator.predict(inp)
        self.assertEqual(len(result.daily_forecast), 14)
        self.assertEqual(len(result.prediction_interval), 14)

    def test_sigma_affects_interval_width(self):
        history = self._history(30, base_value=20.0)
        base = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
        )
        with_sigma = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
            sigma=5.0,
        )
        base_result = self.calculator.predict(base)
        sigma_result = self.calculator.predict(with_sigma)
        base_width = base_result.prediction_interval[0].upper - base_result.prediction_interval[0].lower
        sigma_width = sigma_result.prediction_interval[0].upper - sigma_result.prediction_interval[0].lower
        self.assertGreater(sigma_width, base_width)

    def test_trend_and_seasonal_clipped(self):
        # 构造最近 7 天远高于最近 30 天的数据，验证 trend factor 被 clip
        values = [10.0] * 23 + [100.0] * 7
        history = [
            HistoricalDataPoint(date=date(2024, 1, 1) + timedelta(days=i), units_sold=v)
            for i, v in enumerate(values)
        ]
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
        )
        result = self.calculator.predict(inp)
        # 由于 clip，预测值不应无限放大
        self.assertTrue(all(p.units_sold < 200 for p in result.daily_forecast))

    def test_predict_points_returns_correct_count(self):
        """predict_points 对 N 个目标日期返回 N 个预测值。"""
        import pandas as pd
        from forecast.utils import to_dataframe

        history = self._history(30, base_value=15.0)
        df = to_dataframe(history)
        target_dates = [
            pd.Timestamp(date(2024, 1, 31) + timedelta(days=i))
            for i in range(7)
        ]
        predictions = self.calculator.predict_points(df, target_dates)
        self.assertEqual(len(predictions), 7)
        self.assertTrue(all(isinstance(p, float) for p in predictions))
        self.assertTrue(all(p >= 0 for p in predictions))

    def test_predict_points_matches_predict(self):
        """predict_points 与 predict 对同一天应返回相同预测值。"""
        import pandas as pd
        from forecast.utils import to_dataframe

        history = self._history(30, base_value=15.0)
        df = to_dataframe(history)

        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 31),
            horizon_days=1,
        )
        result = self.calculator.predict(inp)
        expected = result.daily_forecast[0].units_sold

        predictions = self.calculator.predict_points(df, [pd.Timestamp(date(2024, 1, 31))])
        self.assertAlmostEqual(predictions[0], expected, places=1)

    def test_predict_single_day_public_api(self):
        """predict_single_day 公共接口正常工作。"""
        import pandas as pd
        from forecast.utils import to_dataframe

        history = self._history(30, base_value=15.0)
        df = to_dataframe(history)
        pred = self.calculator.predict_single_day(df, date(2024, 1, 31))
        self.assertIsInstance(pred, float)
        self.assertGreaterEqual(pred, 0)

    def test_fallback_zero_sales_uses_min(self):
        """全部销量为 0 时，降级应使用 FALLBACK_CONSERVATIVE_MIN=5.0。"""
        history = [
            HistoricalDataPoint(date=date(2024, 1, 1) + timedelta(days=i), units_sold=0)
            for i in range(5)
        ]
        inp = ForecastInput(
            historical_data=history,
            forecast_start_date=date(2024, 1, 6),
        )
        result = self.calculator.predict(inp)
        self.assertEqual(result.status, "insufficient_data")
        # avg=0, avg*0.8=0, max(5.0, 0)=5.0
        self.assertEqual(result.daily_forecast[0].units_sold, 5.0)


if __name__ == "__main__":
    unittest.main()
