"""
ForecastRepository 与 ReplenishmentRepository 单元测试
"""

import importlib.util
import os
import sys
import unittest
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_module(module_name: str, relative_path: str):
    """从 api/ 目录动态加载无 __init__.py 的模块。"""
    path = os.path.join(PROJECT_ROOT, "api", relative_path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 动态加载 repository 模块
forecast_repository_module = _load_module(
    "infrastructure.forecast_repository", "infrastructure/forecast_repository.py"
)
replenishment_repository_module = _load_module(
    "infrastructure.replenishment_repository", "infrastructure/replenishment_repository.py"
)

ForecastRepository = forecast_repository_module.ForecastRepository
ReplenishmentRepository = replenishment_repository_module.ReplenishmentRepository


DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed_data")


class TestForecastRepository(unittest.TestCase):
    """ForecastRepository 测试。"""

    @classmethod
    def setUpClass(cls):
        cls.repo = ForecastRepository(DATA_DIR)

    def test_get_forecast_returns_7_days(self):
        forecast = self.repo.get_forecast("S001", "P0001", "2024-01-15")
        self.assertIsNotNone(forecast)
        self.assertEqual(forecast.status, "ready")
        self.assertEqual(len(forecast.daily_forecast), 7)
        self.assertEqual(len(forecast.prediction_interval), 7)

    def test_get_forecast_returns_none_for_missing_combo(self):
        forecast = self.repo.get_forecast("S999", "P9999", "2023-10-31")
        self.assertIsNone(forecast)

    def test_prediction_interval_bounds(self):
        forecast = self.repo.get_forecast("S001", "P0001", "2024-01-15")
        self.assertIsNotNone(forecast)
        for interval in forecast.prediction_interval:
            self.assertGreaterEqual(interval.lower, 0)
            self.assertLessEqual(interval.lower, interval.upper)

    def test_get_forecast_accepts_datetime(self):
        dt = datetime(2024, 1, 15)
        forecast = self.repo.get_forecast("S001", "P0001", dt)
        self.assertIsNotNone(forecast)


class TestReplenishmentRepository(unittest.TestCase):
    """ReplenishmentRepository 测试。"""

    @classmethod
    def setUpClass(cls):
        cls.repo = ReplenishmentRepository(DATA_DIR)

    def test_get_replenishment(self):
        repl = self.repo.get_replenishment("S001", "P0001", "2024-01-15")
        self.assertIsNotNone(repl)
        self.assertIn("product_id", repl)
        self.assertIn("suggested_replenishment", repl)
        self.assertIn("forecast_k_total", repl)

    def test_get_replenishment_missing(self):
        repl = self.repo.get_replenishment("S999", "P9999", "2023-10-31")
        self.assertIsNone(repl)

    def test_get_replenishments_by_store(self):
        repls = self.repo.get_replenishments_by_store("S001")
        self.assertGreater(len(repls), 0)

    def test_get_replenishments_by_store_and_date(self):
        repls = self.repo.get_replenishments_by_store("S001", as_of_date="2024-01-15")
        self.assertGreater(len(repls), 0)

    def test_get_replenishments_by_store_and_category(self):
        repls = self.repo.get_replenishments_by_store("S001", category="Electronics")
        self.assertGreater(len(repls), 0)


if __name__ == "__main__":
    unittest.main()
