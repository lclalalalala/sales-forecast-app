"""
测试完整流程 - tests/offline_calculation/test_pipeline.py
"""

import os
import tempfile
import unittest

from offline_calculation.pipeline import run_pipeline


class TestPipeline(unittest.TestCase):
    """测试离线计算完整流程。"""

    def setUp(self):
        self.fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_sales_data.csv"
        )

    def test_pipeline_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_pipeline(raw_path=self.fixture_path, output_dir=tmpdir)

            expected_files = [
                "data_quality_report.json",
                "data_quality_report.csv",
                "dim_store.csv",
                "dim_product.csv",
                "fact_daily_inventory_sales.csv",
                "fact_lead_time.csv",
                "fact_forecast.csv",
                "fact_forecast_error_stats.csv",
                "fact_daily_replenishment.csv",
                "fact_daily_sales_metrics.csv",
                "fact_product_sales_summary.csv",
            ]
            for filename in expected_files:
                path = os.path.join(tmpdir, filename)
                self.assertTrue(os.path.exists(path), f"缺少输出文件: {filename}")


if __name__ == "__main__":
    unittest.main()
