"""
商品详情查询 - /api/products 与 /api/products/{product_id}
=========================================================
合并原 routes/product_routes.py、application/product_detail_query.py、domain/sales_service.py。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Blueprint, request

from infrastructure.config_repository import ConfigRepository, config_repository
from infrastructure.dim_repository import DimRepository, dim_repository
from infrastructure.forecast_repository import ForecastRepository, forecast_repository
from infrastructure.inventory_sales_repository import (
    InventorySalesRepository,
    inventory_sales_repository,
)
from infrastructure.replenishment_repository import ReplenishmentRepository, replenishment_repository
from schemas import requests, responses


# ─── Blueprint ────────────────────────────────────────────────────
product_bp = Blueprint("product", __name__, url_prefix="/api")


@product_bp.route("/products", methods=["GET"])
def get_products():
    """商品列表。"""
    try:
        store_id = requests.parse_store_id(request.args.get("store_id"), "S001")
        category = requests.parse_category(request.args.get("category"))

        products = dim_repository.get_products(store_id=store_id, category=category)
        return responses.build_response(None, [
            {"id": p["id"], "name": p["id"], "category": p["category"]}
            for p in products
        ])
    except requests.RequestValidationError as e:
        return responses.build_error(e.code, e.message)
    except Exception as e:
        return responses.build_internal_error(str(e))


@product_bp.route("/products/<product_id>", methods=["GET"])
def get_product_detail(product_id: str):
    """商品详情。"""
    try:
        store_id = requests.parse_store_id(request.args.get("store_id"), "S001")
        range_value = requests.parse_range(request.args.get("range"))

        result = _query.execute(store_id, product_id, range_value)
        return responses.build_response(result["context"], result["data"])
    except requests.RequestValidationError as e:
        return responses.build_error(e.code, e.message)
    except Exception as e:
        return responses.build_internal_error(str(e))


# ─── Query ────────────────────────────────────────────────────────

class ProductDetailQuery:
    """商品详情查询。"""

    def __init__(
        self,
        dim_repo: DimRepository,
        inventory_repo: InventorySalesRepository,
        forecast_repository: ForecastRepository,
        replenishment_repository: ReplenishmentRepository,
        config: ConfigRepository,
    ):
        self._dim = dim_repo
        self._inventory = inventory_repo
        self._forecast_repository = forecast_repository
        self._replenishment_repository = replenishment_repository
        self._config = config

    def execute(
        self,
        store_id: str,
        product_id: str,
        range_days: Optional[int],
    ) -> Dict[str, Any]:
        """执行商品详情查询。"""
        as_of_date_str = self._replenishment_repository.get_latest_as_of_date(store_id)
        if as_of_date_str is None:
            raise ValueError(f"门店 {store_id} 无数据")

        as_of_date = datetime.strptime(as_of_date_str, "%Y-%m-%d")
        product_info = self._dim.get_product_info(store_id, product_id)

        # 历史销量与库存（读预计算事实表 fact_daily_inventory_sales）
        history_start = (
            as_of_date - timedelta(days=range_days - 1) if range_days is not None else None
        )
        historical_sales = self._inventory.get_history(
            store_id, product_id, start_date=history_start, end_date=as_of_date,
        )

        # 补货相关明细（来自预计算表）
        repl = self._replenishment_repository.get_replenishment(store_id, product_id, as_of_date)
        if repl is None:
            repl = {
                "current_inventory": 0, "in_transit_inventory": 0,
                "inventory_date": None, "lead_time_k": self._config.lead_time_fallback_days,
                "lead_time_k_source": "default", "forecast_k_total": 0.0,
                "safety_stock": 0, "suggested_replenishment": 0,
                "inventory_status": "undetermined", "status": "forecast_unavailable",
                "message": "无预计算补货数据",
            }

        inventory_date_str = repl.get("inventory_date")

        # 预测对象（来自预计算表）
        forecast = {
            "daily_forecast_units_sold": [], "prediction_interval": [],
            "status": repl.get("status", "forecast_unavailable"),
            "message": repl.get("message"),
        }
        if inventory_date_str:
            forecast_output = self._forecast_repository.get_forecast(store_id, product_id, inventory_date_str)
            if forecast_output is not None:
                forecast["daily_forecast_units_sold"] = [
                    {"date": p.date, "units_sold": p.units_sold}
                    for p in forecast_output.daily_forecast
                ]
                forecast["prediction_interval"] = [
                    {"date": p.date, "lower": p.lower, "upper": p.upper}
                    for p in forecast_output.prediction_interval
                ]
                forecast["status"] = forecast_output.status
                forecast["message"] = None

        # 实际数据范围（读预计算事实表的观测区间）
        observed_range = self._inventory.get_observed_date_range(store_id, product_id)
        if observed_range is None:
            actual_start = as_of_date_str
            actual_end = as_of_date_str
        else:
            actual_start = observed_range["min_date"]
            actual_end = observed_range["max_date"]
            if range_days is not None:
                requested_start = (as_of_date - timedelta(days=range_days - 1)).strftime("%Y-%m-%d")
                actual_start = max(actual_start, requested_start)

        return {
            "context": {
                "store_id": store_id, "category": product_info.get("category", "all"),
                "time_range": f"{range_days}d" if range_days is not None else "all",
                "as_of_date": as_of_date_str,
                "actual_data_start": actual_start, "actual_data_end": actual_end,
            },
            "data": {
                "product_id": product_id, "category": product_info.get("category", ""),
                "price": product_info.get("price", 0.0),
                "current_inventory": repl["current_inventory"],
                "in_transit_inventory": repl["in_transit_inventory"],
                "inventory_date": inventory_date_str,
                "historical_sales": historical_sales, "forecast": forecast,
                "replenishment": {
                    "lead_time_k": repl["lead_time_k"],
                    "lead_time_k_source": repl["lead_time_k_source"],
                    "forecast_k_total": repl["forecast_k_total"],
                    "safety_stock": repl["safety_stock"],
                    "suggested_replenishment": repl["suggested_replenishment"],
                    "inventory_status": repl["inventory_status"],
                },
            },
        }


# ─── 单例 ─────────────────────────────────────────────────────────
_query = ProductDetailQuery(
    dim_repository,
    inventory_sales_repository,
    forecast_repository,
    replenishment_repository,
    config_repository,
)
