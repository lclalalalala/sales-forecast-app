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
dim_repository_module = _load_module(
    "infrastructure.dim_repository", "infrastructure/dim_repository.py"
)
inventory_sales_repository_module = _load_module(
    "infrastructure.inventory_sales_repository", "infrastructure/inventory_sales_repository.py"
)

ForecastRepository = forecast_repository_module.ForecastRepository
ReplenishmentRepository = replenishment_repository_module.ReplenishmentRepository
DimRepository = dim_repository_module.DimRepository
InventorySalesRepository = inventory_sales_repository_module.InventorySalesRepository


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


class TestDimRepository(unittest.TestCase):
    """DimRepository 测试（读 dim_store / dim_product）。"""

    @classmethod
    def setUpClass(cls):
        cls.repo = DimRepository(DATA_DIR)

    def test_loaded(self):
        self.assertTrue(self.repo.is_loaded())

    def test_get_stores(self):
        stores = self.repo.get_stores()
        self.assertEqual(len(stores), 5)
        first = stores[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("region", first)

    def test_get_categories(self):
        categories = self.repo.get_categories()
        self.assertGreater(len(categories), 0)
        self.assertTrue(all(isinstance(c, str) for c in categories))

    def test_get_products(self):
        products = self.repo.get_products()
        self.assertEqual(len(products), 20)
        self.assertIn("id", products[0])
        self.assertIn("category", products[0])
        self.assertIn("price", products[0])

    def test_get_product_info(self):
        info = self.repo.get_product_info("S001", "P0001")
        self.assertEqual(info["product_id"], "P0001")
        self.assertNotEqual(info["category"], "")

    def test_counts(self):
        counts = self.repo.counts()
        self.assertEqual(counts["stores"], 5)
        self.assertEqual(counts["products"], 20)
        self.assertGreater(counts["categories"], 0)


class TestInventorySalesRepository(unittest.TestCase):
    """InventorySalesRepository 测试（读 fact_daily_inventory_sales）。"""

    @classmethod
    def setUpClass(cls):
        cls.repo = InventorySalesRepository(DATA_DIR)

    def test_loaded(self):
        self.assertTrue(self.repo.is_loaded())

    def test_get_history_shape(self):
        history = self.repo.get_history("S001", "P0001")
        self.assertGreater(len(history), 0)
        first = history[0]
        self.assertEqual(set(first.keys()), {"date", "units_sold", "inventory_level"})

    def test_get_history_sorted(self):
        history = self.repo.get_history("S001", "P0001")
        dates = [h["date"] for h in history]
        self.assertEqual(dates, sorted(dates))

    def test_get_history_missing_combo(self):
        history = self.repo.get_history("S999", "P9999")
        self.assertEqual(history, [])

    def test_get_observed_date_range(self):
        rng = self.repo.get_observed_date_range("S001", "P0001")
        self.assertIsNotNone(rng)
        self.assertLessEqual(rng["min_date"], rng["max_date"])


if __name__ == "__main__":
    unittest.main()
