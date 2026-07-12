"""
测试套件 - test_api.py
=====================
基于离线预计算架构的测试套件，覆盖：
- 基础设施与配置
- Flask HTTP API 端点
- 端点间一致性校验

运行方式：pytest tests/test_api.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))

from infrastructure.config_repository import ConfigRepository
from infrastructure.csv_repository import CsvRepository
from infrastructure.normalized_repository import NormalizedRepository

TEST_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "sales_data.csv",
)


# ═══════════════════════════════════════════════════════════════
# 基础设施与配置
# ═══════════════════════════════════════════════════════════════

class TestInfrastructure:
    """基础设施测试。"""

    @classmethod
    def setup_class(cls):
        cls.csv_repo = CsvRepository(TEST_DATA_PATH)
        cls.norm_repo = NormalizedRepository(cls.csv_repo)
        cls.config = ConfigRepository.from_file()

    def test_csv_loaded(self):
        summary = self.csv_repo.get_summary()
        assert summary["total_rows"] >= 75000
        assert summary["stores"] == 5
        assert summary["products"] == 20

    def test_normalized_columns(self):
        df = self.norm_repo.get_rows(store_id="S001", product_id="P0001")
        assert not df.empty
        for col in ["store_id", "product_id", "date", "units_sold", "units_ordered", "inventory_level", "demand"]:
            assert col in df.columns

    def test_config_values(self):
        assert self.config.default_store_id == "S001"
        assert self.config.lead_time_fallback_days == 2
        assert self.config.safety_stock_z == 2.33
        assert self.config.inventory_status_critical_lt == 2
        assert self.config.inventory_status_low_lt == 4
        assert self.config.inventory_status_normal_lte == 7

    def test_get_stores_and_categories(self):
        stores = self.norm_repo.get_stores()
        assert len(stores) == 5
        assert "S001" in [s["id"] for s in stores]
        categories = self.norm_repo.get_categories()
        assert len(categories) > 0


# ═══════════════════════════════════════════════════════════════
# Flask HTTP API 端点
# ═══════════════════════════════════════════════════════════════

class TestNewApiEndpoints:
    """新版 API 端点集成测试。"""

    @classmethod
    def setup_class(cls):
        from app import app
        cls.app = app
        cls.client = cls.app.test_client()

    def _get_json(self, url, expected_status=200):
        response = self.client.get(url)
        assert response.status_code == expected_status, f"{url} 应返回 {expected_status}"
        assert response.content_type == "application/json"
        return json.loads(response.data)

    def _assert_envelope(self, data):
        assert "context" in data
        assert "data" in data

    def _assert_error(self, data):
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    def test_overview_endpoint(self):
        data = self._get_json("/api/overview?store_id=S001&range=90d")
        self._assert_envelope(data)
        ctx = data["context"]
        assert ctx["store_id"] == "S001"
        assert ctx["time_range"] == "90d"
        assert "actual_data_start" in ctx
        assert "actual_data_end" in ctx
        d = data["data"]
        for key in ["kpis", "daily_sales", "top_products", "bottom_products", "data_date_note"]:
            assert key in d
        assert "avg_daily_units_sold" in d["kpis"]
        assert len(d["top_products"]) == 5
        assert len(d["bottom_products"]) == 5
        # daily_sales 元素字段须为 {date, units_sold}（对齐前端 DailySales 与 07-API.md §3.6）
        assert isinstance(d["daily_sales"], list) and len(d["daily_sales"]) > 0
        assert set(d["daily_sales"][0].keys()) == {"date", "units_sold"}

    def test_rankings_endpoint(self):
        data = self._get_json("/api/rankings?store_id=S001&range=90d&top_n=3&bottom_n=3")
        self._assert_envelope(data)
        assert len(data["data"]["top"]) == 3
        assert len(data["data"]["bottom"]) == 3
        assert "total_candidates" in data["data"]

    def test_replenishment_endpoint(self):
        data = self._get_json("/api/replenishment?store_id=S001")
        self._assert_envelope(data)
        suggestions = data["data"]["suggestions"]
        assert len(suggestions) > 0
        for s in suggestions:
            assert "product_id" in s
            assert "lead_time_k" in s
            assert "suggested_replenishment" in s
            assert s["suggested_replenishment"] >= 0

    def test_replenishment_forecast_7d_filled(self):
        """验证补货建议的 forecast_7d 字段已从离线预测表回填。"""
        data = self._get_json("/api/replenishment?store_id=S001")
        suggestions = data["data"]["suggestions"]
        has_forecast = any(len(s["forecast_7d"]) > 0 for s in suggestions)
        assert has_forecast, "至少应有一个 suggestion 的 forecast_7d 非空"

    def test_products_list_endpoint(self):
        data = self._get_json("/api/products?store_id=S001")
        self._assert_envelope(data)
        products = data["data"]
        assert len(products) == 20
        assert "id" in products[0]
        assert "category" in products[0]

    def test_product_detail_endpoint(self):
        data = self._get_json("/api/products/P0001?store_id=S001&range=90d")
        self._assert_envelope(data)
        d = data["data"]
        assert d["product_id"] == "P0001"
        assert "category" in d
        assert "price" in d
        assert "current_inventory" in d
        assert "historical_sales" in d
        # historical_sales 读预计算事实表，字段固定为 {date, units_sold, inventory_level}
        assert isinstance(d["historical_sales"], list) and len(d["historical_sales"]) > 0
        assert set(d["historical_sales"][0].keys()) == {"date", "units_sold", "inventory_level"}
        assert "forecast" in d
        assert "daily_forecast_units_sold" in d["forecast"]
        assert len(d["forecast"]["daily_forecast_units_sold"]) == 7
        assert "prediction_interval" in d["forecast"]
        assert "replenishment" in d
        for key in ["lead_time_k", "safety_stock", "suggested_replenishment", "inventory_status"]:
            assert key in d["replenishment"]

    def test_invalid_range_returns_error(self):
        data = self._get_json("/api/overview?store_id=S001&range=invalid", expected_status=400)
        self._assert_error(data)

    def test_context_date_range_present(self):
        for endpoint in [
            "/api/overview?store_id=S001&range=90d",
            "/api/rankings?store_id=S001&range=90d",
            "/api/replenishment?store_id=S001",
            "/api/products/P0001?store_id=S001&range=90d",
        ]:
            data = self._get_json(endpoint)
            self._assert_envelope(data)
            ctx = data["context"]
            assert "as_of_date" in ctx
            assert "actual_data_start" in ctx
            assert "actual_data_end" in ctx
            assert ctx["actual_data_end"] >= ctx["actual_data_start"]


# ═══════════════════════════════════════════════════════════════
# 元数据端点
# ═══════════════════════════════════════════════════════════════

class TestMetadataEndpoints:
    """健康检查 / 门店 / 类别端点（context=null）。"""

    @classmethod
    def setup_class(cls):
        from app import app
        cls.client = app.test_client()

    def _get_json(self, url):
        response = self.client.get(url)
        assert response.status_code == 200, f"{url} 应返回 200"
        assert response.content_type == "application/json"
        return json.loads(response.data)

    def test_health_endpoint(self):
        data = self._get_json("/api/health")
        assert data["context"] is None
        d = data["data"]
        assert d["status"] == "ok"
        assert d["data_loaded"] is True
        assert d["stores_count"] == 5
        assert d["products_count"] == 20
        assert d["categories_count"] > 0

    def test_stores_endpoint(self):
        data = self._get_json("/api/stores")
        assert data["context"] is None
        stores = data["data"]
        assert len(stores) == 5
        first = stores[0]
        assert {"id", "name", "region"} <= set(first.keys())
        assert first["name"] == f"门店 {first['id']}"

    def test_categories_endpoint(self):
        data = self._get_json("/api/categories")
        assert data["context"] is None
        categories = data["data"]
        assert isinstance(categories, list) and len(categories) > 0
        assert all(isinstance(c, str) for c in categories)


# ═══════════════════════════════════════════════════════════════
# 一致性校验
# ═══════════════════════════════════════════════════════════════

class TestCrossEndpointConsistency:
    """跨端点一致性测试。"""

    @classmethod
    def setup_class(cls):
        from app import app
        cls.client = app.test_client()

    def _get_json(self, url):
        response = self.client.get(url)
        assert response.status_code == 200
        return json.loads(response.data)

    def test_product_detail_matches_replenishment(self):
        detail = self._get_json("/api/products/P0001?store_id=S001&range=90d")["data"]
        repl_endpoint = self._get_json("/api/replenishment?store_id=S001")["data"]
        found = next(
            (s for s in repl_endpoint["suggestions"] if s["product_id"] == "P0001"),
            None,
        )
        assert found is not None
        assert detail["replenishment"]["suggested_replenishment"] == found["suggested_replenishment"]
        assert detail["replenishment"]["inventory_status"] == found["inventory_status"]

    def test_ranking_inventory_status_matches_detail(self):
        ranking = self._get_json("/api/rankings?store_id=S001&range=90d&top_n=20")["data"]
        detail = self._get_json("/api/products/P0001?store_id=S001&range=90d")["data"]
        found = next(
            (r for r in ranking["top"] if r["product_id"] == "P0001"),
            None,
        )
        assert found is not None
        valid_statuses = {"critical", "low", "normal", "sufficient", "undetermined"}
        assert found["inventory_status"] in valid_statuses
        assert detail["replenishment"]["inventory_status"] in valid_statuses
