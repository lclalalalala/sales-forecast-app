"""
测试事实表构建 - tests/offline_calculation/test_build_fact.py
"""

import os
import tempfile
import unittest

import pandas as pd

from offline_calculation.steps.build_fact import build_fact_daily_inventory_sales, build_dim_tables
from offline_calculation.steps.load_validate import load_and_validate


class TestBuildFact(unittest.TestCase):
    """测试标准化事实表构建。"""

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_sales_data.csv"
        )

    def test_build_fact_columns_and_inventory_relation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_df, _ = load_and_validate(self.fixture_path, tmpdir)
            fact = build_fact_daily_inventory_sales(raw_df)

            self.assertIn("closing_inventory", fact.columns)
            self.assertIn("is_observed", fact.columns)
            self.assertTrue(
                (fact["closing_inventory"] == fact["opening_inventory"] - fact["units_sold"]).all()
            )
            self.assertTrue(fact["is_observed"].any())

    def test_build_dim_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_df, _ = load_and_validate(self.fixture_path, tmpdir)
            dim_store, dim_product = build_dim_tables(raw_df)

            self.assertIn("store_id", dim_store.columns)
            self.assertIn("product_id", dim_product.columns)
            self.assertEqual(len(dim_store), raw_df["store_id"].nunique())
            self.assertEqual(len(dim_product), raw_df["product_id"].nunique())


if __name__ == "__main__":
    unittest.main()
