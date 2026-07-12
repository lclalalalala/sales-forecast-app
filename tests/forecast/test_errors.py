"""
ForecastErrorCalculator 单元测试
"""

import os
import sys
import unittest
from datetime import date, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from forecast.schemas import HistoricalDataPoint
from forecast.errors import ForecastErrorCalculator


class TestForecastErrorCalculator(unittest.TestCase):
    """滚动预测误差计算器测试。"""

    def _history(self, days: int, base_value: float = 10.0) -> list:
        start = date(2024, 1, 1)
        return [
            HistoricalDataPoint(
                date=start + timedelta(days=i),
                units_sold=base_value + (i % 7),
            )
            for i in range(days)
        ]

    def test_insufficient_history_returns_none_sigma(self):
        history = self._history(5)
        result = ForecastErrorCalculator.compute_errors(history)
        self.assertEqual(result.errors, [])
        self.assertIsNone(result.sigma)

    def test_minimal_history_returns_empty_errors(self):
        # 恰好 MIN_HISTORY_DAYS 天，无法产生误差
        history = self._history(ForecastErrorCalculator.MIN_HISTORY_DAYS)
        result = ForecastErrorCalculator.compute_errors(history)
        self.assertEqual(result.errors, [])
        self.assertIsNone(result.sigma)

    def test_enough_history_returns_sigma(self):
        history = self._history(30)
        result = ForecastErrorCalculator.compute_errors(history)
        self.assertGreater(len(result.errors), 0)
        self.assertIsNotNone(result.sigma)
        self.assertGreaterEqual(result.sigma, 0)

    def test_sigma_matches_sample_std(self):
        import numpy as np
        history = self._history(30, base_value=20.0)
        result = ForecastErrorCalculator.compute_errors(history)
        expected_sigma = float(np.std(result.errors, ddof=1))
        self.assertAlmostEqual(result.sigma, expected_sigma, places=6)

    def test_error_values_reasonable(self):
        history = self._history(30)
        result = ForecastErrorCalculator.compute_errors(history)
        # 误差不应全部相同（周期性数据应该有一些波动）
        self.assertGreater(len(set(result.errors)), 1)


if __name__ == "__main__":
    unittest.main()
