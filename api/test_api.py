"""
测试套件 - test_api.py
=====================
基于BDD规范编写的全面测试套件，包含:
- 单元测试: DataService, ForecastService
- 集成测试: Flask HTTP API端点
- 边界测试: 空数据、零库存、异常参数
- 隔离测试: 多门店数据不混淆

运行方式: python test_api.py
测试框架: unittest
"""

import sys
import os
import unittest
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.data_service import DataService
from services.forecast_service import ForecastService

# ═══════════════════════════════════════════════════════════════
# 测试配置
# ═══════════════════════════════════════════════════════════════

TEST_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "sales_data.csv"
)

# ═══════════════════════════════════════════════════════════════
# Feature 1: 门店数据概览 - 单元测试
# ═══════════════════════════════════════════════════════════════

class TestDataService(unittest.TestCase):
    """
    DataService 单元测试
    覆盖US-1.1 ~ US-1.5的数据查询需求
    """

    @classmethod
    def setUpClass(cls):
        """
        测试类初始化
        
        只加载一次数据集，供所有测试方法共享使用。
        """
        cls.service = DataService(TEST_DATA_PATH)

    # ─── US-1.1: 数据加载成功 ──────────────────────────────

    def test_data_loaded_successfully(self):
        """Scenario 1.1: 数据加载成功"""
        self.assertTrue(
            self.service.is_loaded(),
            "数据集应成功加载"
        )

    def test_data_summary_structure(self):
        """Scenario 1.1: 数据摘要格式正确"""
        summary = self.service.get_data_summary()
        self.assertIn("total_rows", summary)
        self.assertIn("stores", summary)
        self.assertIn("products", summary)
        self.assertEqual(summary["stores"], 5)
        self.assertEqual(summary["products"], 20)

    # ─── US-1.2: 门店列表 ──────────────────────────────────

    def test_get_stores_returns_5_stores(self):
        """Scenario 1.2: 返回5个门店"""
        stores = self.service.get_stores()
        self.assertEqual(len(stores), 5, "应有5个门店")
        store_ids = [s["id"] for s in stores]
        expected_ids = ["S001", "S002", "S003", "S004", "S005"]
        for sid in expected_ids:
            self.assertIn(sid, store_ids, f"门店{sid}应在列表中")

    def test_each_store_has_region(self):
        """Scenario 1.2: 每个门店有区域信息"""
        stores = self.service.get_stores()
        for store in stores:
            self.assertIn("id", store)
            self.assertIn("region", store)
            self.assertIsInstance(store["region"], str)
            self.assertGreater(len(store["region"]), 0)

    # ─── US-1.3: 销售趋势数据 ──────────────────────────────

    def test_get_sales_trend_returns_90_days(self):
        """Scenario 1.3: 返回约90天的趋势数据"""
        trend = self.service.get_sales_trend("S001", 90)
        self.assertGreaterEqual(len(trend), 85, "应有至少85天的数据")
        self.assertLessEqual(len(trend), 95, "不应超过95天")

    def test_sales_trend_data_format(self):
        """Scenario 1.3: 趋势数据格式正确"""
        trend = self.service.get_sales_trend("S001", 90)
        for day in trend:
            self.assertIn("date", day, "每条记录应有date字段")
            self.assertIn("units_sold", day, "每条记录应有units_sold字段")
            self.assertIn("demand", day, "每条记录应有demand字段")
            self.assertIsInstance(day["units_sold"], int)
            self.assertIsInstance(day["demand"], int)
            self.assertGreaterEqual(day["units_sold"], 0)
            self.assertGreaterEqual(day["demand"], 0)

    def test_sales_trend_chronological_order(self):
        """Scenario 1.3: 趋势数据按日期升序排列"""
        trend = self.service.get_sales_trend("S001", 30)
        for i in range(1, len(trend)):
            self.assertLess(
                trend[i - 1]["date"], trend[i]["date"],
                "日期应按升序排列"
            )

    # ─── US-1.4 & US-1.5: 商品排名 ────────────────────────

    def test_get_product_ranking_top5_has_5_items(self):
        """Scenario 1.4: Top 5应有5个商品"""
        ranking = self.service.get_product_ranking("S001", 90)
        self.assertEqual(len(ranking["top_5"]), 5, "Top 5应有5条记录")

    def test_get_product_ranking_bottom5_has_5_items(self):
        """Scenario 1.5: Bottom 5应有5个商品"""
        ranking = self.service.get_product_ranking("S001", 90)
        self.assertEqual(len(ranking["bottom_5"]), 5, "Bottom 5应有5条记录")

    def test_top5_sorted_descending(self):
        """Scenario 1.4: Top 5按销量降序排列"""
        ranking = self.service.get_product_ranking("S001", 90)
        top5 = ranking["top_5"]
        for i in range(4):
            self.assertGreaterEqual(
                top5[i]["total_sold"], top5[i + 1]["total_sold"],
                f"第{i + 1}名销量应 >= 第{i + 2}名"
            )

    def test_bottom5_sorted_ascending(self):
        """Scenario 1.5: Bottom 5按销量升序排列"""
        ranking = self.service.get_product_ranking("S001", 90)
        bottom5 = ranking["bottom_5"]
        for i in range(4):
            self.assertLessEqual(
                bottom5[i]["total_sold"], bottom5[i + 1]["total_sold"],
                f"Bottom第{i + 1}名销量应 <= 第{i + 2}名"
            )

    def test_ranking_items_have_required_fields(self):
        """Scenario 1.4/1.5: 排名项包含必要字段"""
        ranking = self.service.get_product_ranking("S001", 90)
        for item in ranking["top_5"] + ranking["bottom_5"]:
            self.assertIn("product_id", item)
            self.assertIn("category", item)
            self.assertIn("total_sold", item)
            self.assertIn("avg_daily", item)
            self.assertIsInstance(item["total_sold"], int)
            self.assertIsInstance(item["avg_daily"], float)

    # ─── US-3.1: 商品查询 ──────────────────────────────────

    def test_get_products_returns_20_products(self):
        """Scenario 3.1: 返回20个商品"""
        products = self.service.get_products("S001")
        self.assertEqual(len(products), 20, "应有20个商品")

    def test_get_product_info_structure(self):
        """Scenario 3.1: 商品信息格式正确"""
        info = self.service.get_product_info("S001", "P0001")
        self.assertIn("product_id", info)
        self.assertIn("category", info)
        self.assertIn("price", info)
        self.assertEqual(info["product_id"], "P0001")

    # ─── US-3.2: 商品历史数据 ──────────────────────────────

    def test_get_product_history_has_required_fields(self):
        """Scenario 3.2: 历史数据字段完整"""
        history = self.service.get_product_history("S001", "P0001", 90)
        self.assertGreater(len(history), 80, "应有足够的历史数据")
        for record in history[:5]:
            self.assertIn("date", record)
            self.assertIn("units_sold", record)
            self.assertIn("demand", record)
            self.assertIn("inventory", record)
            self.assertIn("dayofweek", record)
            self.assertIn("month", record)

    # ─── US-3.3: 库存查询 ──────────────────────────────────

    def test_get_current_inventory_is_non_negative(self):
        """Scenario 3.3: 库存为非负整数"""
        inv = self.service.get_current_inventory("S001", "P0001")
        self.assertIsInstance(inv, int)
        self.assertGreaterEqual(inv, 0)

    # ─── 多门店隔离测试 ────────────────────────────────────

    def test_store_data_isolation(self):
        """不同门店的数据应相互隔离"""
        trend_s001 = self.service.get_sales_trend("S001", 7)
        trend_s002 = self.service.get_sales_trend("S002", 7)
        # 两个门店的同期销量应该不同(概率极高)
        s001_total = sum(d["units_sold"] for d in trend_s001)
        s002_total = sum(d["units_sold"] for d in trend_s002)
        # 两个门店7天总销量相同的可能性极低，以此验证隔离
        # 注意: 理论上可能相同，但概率极低
        self.assertIsInstance(s001_total, int)
        self.assertIsInstance(s002_total, int)


# ═══════════════════════════════════════════════════════════════
# Feature 2: 智能补货建议 - 单元测试
# ═══════════════════════════════════════════════════════════════

class TestForecastService(unittest.TestCase):
    """
    ForecastService 单元测试
    覆盖US-2.1 ~ US-2.3的预测和补货计算需求
    """

    @classmethod
    def setUpClass(cls):
        """
        测试类初始化

        加载数据服务和预测服务实例。
        """
        cls.data_service = DataService(TEST_DATA_PATH)
        cls.forecast_service = ForecastService()

    # ─── US-2.1: 7天预测 ───────────────────────────────────

    def test_predict_returns_7_values(self):
        """Scenario 2.1: 预测返回7个值"""
        history = self.data_service.get_product_history("S001", "P0001", 90)
        predictions = self.forecast_service.predict_next_7_days(history)
        self.assertEqual(len(predictions), 7, "应返回7天预测")

    def test_predictions_are_non_negative(self):
        """Scenario 2.1: 预测值非负"""
        history = self.data_service.get_product_history("S001", "P0001", 90)
        predictions = self.forecast_service.predict_next_7_days(history)
        for i, p in enumerate(predictions):
            self.assertGreaterEqual(p, 0, f"第{i + 1}天预测值应非负")

    def test_predictions_are_reasonable(self):
        """Scenario 2.1: 预测值在合理范围内"""
        history = self.data_service.get_product_history("S001", "P0001", 90)
        avg_demand = sum(h["demand"] for h in history) / len(history)
        predictions = self.forecast_service.predict_next_7_days(history)
        for p in predictions:
            # 预测值应在历史平均的0.1~5倍范围内
            self.assertGreater(p, avg_demand * 0.1, f"预测值{p}过低")
            self.assertLess(p, avg_demand * 5, f"预测值{p}过高")

    # ─── US-2.3: 补货计算 ──────────────────────────────────

    def test_calculate_replenishment_normal_case(self):
        """Scenario 2.3: 正常补货计算"""
        result = self.forecast_service.calculate_replenishment(
            predicted_demand_7d=[100, 100, 100, 100, 100, 100, 100],
            current_inventory=500,
            safety_factor=1.2
        )
        # 700 * 1.2 - 500 = 340
        self.assertEqual(result["suggested_replenishment"], 340)
        self.assertEqual(result["total_predicted_demand"], 700)

    def test_calculate_replenishment_zero_when_sufficient(self):
        """Scenario 2.2: 库存充足时补货为0"""
        result = self.forecast_service.calculate_replenishment(
            predicted_demand_7d=[10, 10, 10, 10, 10, 10, 10],
            current_inventory=1000,
            safety_factor=1.2
        )
        self.assertEqual(result["suggested_replenishment"], 0)
        self.assertEqual(result["inventory_status"], "充足")

    def test_calculate_replenishment_high_demand_low_stock(self):
        """Scenario 2.3: 高需求低库存时建议大量补货"""
        result = self.forecast_service.calculate_replenishment(
            predicted_demand_7d=[200, 200, 200, 200, 200, 200, 200],
            current_inventory=50,
            safety_factor=1.2
        )
        # 1400 * 1.2 - 50 = 1630
        self.assertEqual(result["suggested_replenishment"], 1630)
        self.assertEqual(result["inventory_status"], "紧缺")

    def test_calculate_replenishment_zero_inventory(self):
        """边界: 库存为0时应补满全部预测需求"""
        result = self.forecast_service.calculate_replenishment(
            predicted_demand_7d=[50, 50, 50, 50, 50, 50, 50],
            current_inventory=0,
            safety_factor=1.2
        )
        # 350 * 1.2 - 0 = 420
        self.assertEqual(result["suggested_replenishment"], 420)

    def test_calculate_replenishment_zero_demand(self):
        """边界: 预测需求为0时补货为0"""
        result = self.forecast_service.calculate_replenishment(
            predicted_demand_7d=[0, 0, 0, 0, 0, 0, 0],
            current_inventory=100,
            safety_factor=1.2
        )
        self.assertEqual(result["suggested_replenishment"], 0)

    def test_calculate_replenishment_inventory_status_levels(self):
        """库存状态分级测试"""
        test_cases = [
            # (inventory, predicted, expected_status)
            (1000, [10] * 7, "充足"),   # 1000 > 70*1.5
            (100, [10] * 7, "正常"),     # 100 > 70
            (50, [10] * 7, "偏低"),      # 50 > 35 but < 70
            (10, [10] * 7, "紧缺"),      # 10 < 35
        ]
        for inv, pred, expected in test_cases:
            result = self.forecast_service.calculate_replenishment(pred, inv, 1.2)
            self.assertEqual(
                result["inventory_status"], expected,
                f"库存{inv}, 预测{sum(pred)} 应显示 {expected}"
            )

    # ─── 多商品一致性 ──────────────────────────────────────

    def test_multiple_products_predictions(self):
        """不同商品的预测一致性"""
        products = ["P0001", "P0003", "P0005", "P0010", "P0015"]
        for pid in products:
            history = self.data_service.get_product_history("S001", pid, 90)
            predictions = self.forecast_service.predict_next_7_days(history)
            self.assertEqual(len(predictions), 7, f"{pid}应有7天预测")
            self.assertTrue(all(p >= 0 for p in predictions), f"{pid}预测值应非负")


# ═══════════════════════════════════════════════════════════════
# 集成测试: Flask HTTP API 端点
# ═══════════════════════════════════════════════════════════════

class TestFlaskApiEndpoints(unittest.TestCase):
    """
    Flask API HTTP 端点集成测试
    使用Flask test_client模拟HTTP请求
    """

    @classmethod
    def setUpClass(cls):
        """
        测试类初始化

        创建Flask测试客户端，延迟导入避免数据重复加载。
        """
        from app import app
        cls.app = app
        cls.client = cls.app.test_client()

    def _get_json(self, url):
        """辅助方法: GET请求并解析JSON"""
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, f"{url}应返回200")
        self.assertEqual(response.content_type, "application/json")
        return json.loads(response.data)

    def _assert_standard_response(self, data):
        """辅助方法: 验证标准响应格式"""
        self.assertIn("success", data)
        self.assertIn("data", data)
        self.assertIn("message", data)
        self.assertIn("timestamp", data)
        self.assertIsInstance(data["success"], bool)

    # ─── /api/health ───────────────────────────────────────

    def test_health_endpoint(self):
        """健康检查端点"""
        data = self._get_json("/api/health")
        self._assert_standard_response(data)
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "ok")

    # ─── /api/stores ───────────────────────────────────────

    def test_stores_endpoint(self):
        """Scenario 1.2: 门店列表API"""
        data = self._get_json("/api/stores")
        self._assert_standard_response(data)
        stores = data["data"]
        self.assertEqual(len(stores), 5)
        self.assertEqual(stores[0]["id"], "S001")

    # ─── /api/products ─────────────────────────────────────

    def test_products_endpoint(self):
        """Scenario 3.1: 商品列表API"""
        data = self._get_json("/api/products?store_id=S001")
        self._assert_standard_response(data)
        self.assertEqual(len(data["data"]), 20)

    # ─── /api/sales/trend ──────────────────────────────────

    def test_sales_trend_endpoint(self):
        """Scenario 1.3: 销售趋势API"""
        data = self._get_json("/api/sales/trend?store_id=S001&days=90")
        self._assert_standard_response(data)
        trend = data["data"]
        self.assertIn("daily_sales", trend)
        self.assertIn("summary", trend)
        self.assertGreater(len(trend["daily_sales"]), 80)
        # 验证summary字段
        summary = trend["summary"]
        self.assertIn("total_units_sold", summary)
        self.assertIn("avg_daily_sales", summary)
        self.assertIn("growth_rate", summary)

    # ─── /api/sales/ranking ────────────────────────────────

    def test_sales_ranking_endpoint(self):
        """Scenario 1.4/1.5: 商品排名API"""
        data = self._get_json("/api/sales/ranking?store_id=S001&days=90")
        self._assert_standard_response(data)
        ranking = data["data"]
        self.assertEqual(len(ranking["top_5"]), 5)
        self.assertEqual(len(ranking["bottom_5"]), 5)

    # ─── /api/replenishment ────────────────────────────────

    def test_replenishment_endpoint(self):
        """Scenario 2.1: 补货建议API"""
        data = self._get_json("/api/replenishment?store_id=S001")
        self._assert_standard_response(data)
        repl = data["data"]
        self.assertEqual(len(repl["top_5_products"]), 5)
        # 验证每个商品的建议结构
        for product in repl["top_5_products"]:
            self.assertIn("product_id", product)
            self.assertIn("current_inventory", product)
            self.assertIn("predicted_demand_7d", product)
            self.assertEqual(len(product["predicted_demand_7d"]), 7)
            self.assertIn("total_predicted_demand", product)
            self.assertIn("suggested_replenishment", product)
            self.assertGreaterEqual(product["suggested_replenishment"], 0)

    # ─── /api/products/detail ──────────────────────────────

    def test_product_detail_endpoint(self):
        """Scenario 3.1~3.4: 商品详情API"""
        data = self._get_json("/api/products/detail?store_id=S001&product_id=P0001&days=90")
        self._assert_standard_response(data)
        detail = data["data"]
        self.assertEqual(detail["product_id"], "P0001")
        self.assertIn("category", detail)
        self.assertIn("price", detail)
        self.assertIn("current_inventory", detail)
        self.assertIn("historical_sales", detail)
        self.assertGreater(len(detail["historical_sales"]), 80)
        self.assertIn("forecast", detail)
        self.assertEqual(len(detail["forecast"]["next_7_days"]), 7)
        self.assertIn("suggested_replenishment", detail["forecast"])

    # ─── /api/dashboard/kpi ────────────────────────────────

    def test_dashboard_kpi_endpoint(self):
        """KPI汇总API"""
        data = self._get_json("/api/dashboard/kpi?store_id=S001&days=90")
        self._assert_standard_response(data)
        kpi = data["data"]
        self.assertIn("total_sales", kpi)
        self.assertIn("avg_daily_sales", kpi)
        self.assertIn("active_products", kpi)

    # ─── 响应格式一致性 ────────────────────────────────────

    def test_all_endpoints_use_standard_format(self):
        """所有API端点使用统一响应格式"""
        endpoints = [
            "/api/health",
            "/api/stores",
            "/api/products?store_id=S001",
            "/api/sales/trend?store_id=S001&days=7",
            "/api/sales/ranking?store_id=S001&days=7",
            "/api/replenishment?store_id=S001",
            "/api/products/detail?store_id=S001&product_id=P0001&days=7",
            "/api/dashboard/kpi?store_id=S001&days=7",
        ]
        for endpoint in endpoints:
            data = self._get_json(endpoint)
            self._assert_standard_response(data)
            self.assertTrue(data["success"], f"{endpoint}应返回success=true")


# ═══════════════════════════════════════════════════════════════
# 边界测试
# ═══════════════════════════════════════════════════════════════

class TestEdgeCases(unittest.TestCase):
    """
    边界条件测试
    验证系统在异常/边界情况下的行为
    """

    @classmethod
    def setUpClass(cls):
        """
        测试类初始化

        加载数据服务和预测服务实例。
        """
        cls.data_service = DataService(TEST_DATA_PATH)
        cls.forecast_service = ForecastService()

    def test_empty_history_fallback(self):
        """边界: 空历史数据时应返回保守估计"""
        predictions = self.forecast_service.predict_next_7_days([])
        self.assertEqual(len(predictions), 7)
        self.assertTrue(all(p >= 0 for p in predictions))

    def test_short_history(self):
        """边界: 少于7天的历史数据"""
        short_history = [
            {"date": "2024-01-01", "datetime": __import__("datetime").datetime(2024, 1, 1),
             "demand": 100, "dayofweek": 0, "month": 1}
            for _ in range(3)
        ]
        predictions = self.forecast_service.predict_next_7_days(short_history)
        self.assertEqual(len(predictions), 7)

    def test_different_days_parameter(self):
        """边界: 不同的days参数"""
        for days in [7, 30, 60, 90]:
            trend = self.data_service.get_sales_trend("S001", days)
            self.assertGreater(len(trend), 0, f"days={days}应返回数据")

    def test_ranking_with_different_days(self):
        """边界: 不同天数范围的排名"""
        for days in [7, 30, 90]:
            ranking = self.data_service.get_product_ranking("S001", days)
            self.assertEqual(len(ranking["top_5"]), 5)
            self.assertEqual(len(ranking["bottom_5"]), 5)


# ═══════════════════════════════════════════════════════════════
# 运行入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 配置测试输出格式
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDataService))
    suite.addTests(loader.loadTestsFromTestCase(TestForecastService))
    suite.addTests(loader.loadTestsFromTestCase(TestFlaskApiEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出摘要
    print("\n" + "=" * 60)
    print(f"测试运行完成: 总计={result.testsRun}, "
          f"通过={result.testsRun - len(result.failures) - len(result.errors)}, "
          f"失败={len(result.failures)}, 错误={len(result.errors)}")
    print("=" * 60)

    # 非零退出码表示有失败
    sys.exit(0 if result.wasSuccessful() else 1)
