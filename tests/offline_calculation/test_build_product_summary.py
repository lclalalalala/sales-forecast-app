"""
测试商品销售汇总 - tests/offline_calculation/test_build_product_summary.py
"""

import os
import unittest

import pandas as pd

from offline_calculation.config import OfflineConfig
from offline_calculation.steps.build_product_summary import build_product_sales_summary


class TestBuildProductSummary(unittest.TestCase):
    """测试商品汇总的补货记录回退逻辑。"""

    def setUp(self):
        self.config = OfflineConfig.from_file()

    def test_stale_product_uses_latest_available_replenishment(self):
        """最近无观测的滞销商品应回退到 as_of 之前最近的补货记录，而非 0/undetermined。"""
        as_of = pd.Timestamp("2026-01-15")
        fact = pd.DataFrame({
            "store_id": "S001",
            "product_id": ["P002"] * 5,
            "category": "cat",
            "date": pd.date_range("2026-01-01", periods=5, freq="D"),
            "units_sold": 2,
        })
        # 该商品最新补货记录在 as_of（1/15）之前的 1/05，无精确匹配
        repl = pd.DataFrame([{
            "as_of_date": "2026-01-05", "store_id": "S001", "product_id": "P002",
            "current_inventory": 42, "in_transit_inventory": 7,
            "inventory_status": "normal",
        }])

        summary = build_product_sales_summary(
            fact, repl, as_of_date=as_of, config=self.config
        )

        self.assertFalse(summary.empty)
        self.assertTrue((summary["current_inventory"] == 42).all())
        self.assertTrue((summary["in_transit_inventory"] == 7).all())
        self.assertTrue((summary["inventory_status"] == "normal").all())

    def test_missing_replenishment_falls_back_to_undetermined(self):
        """完全没有补货记录时才回退到 0 库存 / undetermined。"""
        as_of = pd.Timestamp("2026-01-15")
        fact = pd.DataFrame({
            "store_id": "S001",
            "product_id": ["P003"] * 3,
            "category": "cat",
            "date": pd.date_range("2026-01-01", periods=3, freq="D"),
            "units_sold": 1,
        })
        repl = pd.DataFrame(columns=[
            "as_of_date", "store_id", "product_id",
            "current_inventory", "in_transit_inventory", "inventory_status",
        ])

        summary = build_product_sales_summary(
            fact, repl, as_of_date=as_of, config=self.config
        )

        self.assertFalse(summary.empty)
        self.assertTrue((summary["current_inventory"] == 0).all())
        self.assertTrue((summary["inventory_status"] == "undetermined").all())


if __name__ == "__main__":
    unittest.main()
