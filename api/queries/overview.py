"""
概览查询 - /api/overview
========================
合并原 routes/overview_routes.py 与 application/overview_query.py。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from flask import Blueprint, request

from infrastructure.config_repository import ConfigRepository, config_repository
from infrastructure.replenishment_repository import ReplenishmentRepository, replenishment_repository
from infrastructure.sales_metrics_repository import SalesMetricsRepository, sales_metrics_repository
from infrastructure.product_summary_repository import ProductSummaryRepository, product_summary_repository
from infrastructure.utils import range_to_window_label
from schemas import requests, responses


# ─── Blueprint ────────────────────────────────────────────────────
overview_bp = Blueprint("overview", __name__, url_prefix="/api")


@overview_bp.route("/overview", methods=["GET"])
def get_overview():
    """门店销售概览。"""
    try:
        store_id = requests.parse_store_id(request.args.get("store_id"), "S001")
        range_value = requests.parse_range(request.args.get("range"))
        category = requests.parse_category(request.args.get("category"))

        result = _query.execute(store_id, range_value, category)
        return responses.build_response(result["context"], result["data"])
    except requests.RequestValidationError as e:
        return responses.build_error(e.code, e.message)
    except Exception as e:
        return responses.build_internal_error(str(e))


# ─── Query ────────────────────────────────────────────────────────

class OverviewQuery:
    """门店概览查询。全部从离线预计算表读取。"""

    def __init__(
        self,
        sales_metrics_repository: SalesMetricsRepository,
        product_summary_repository: ProductSummaryRepository,
        replenishment_repository: ReplenishmentRepository,
        config: ConfigRepository,
    ):
        self._sales_metrics = sales_metrics_repository
        self._product_summary = product_summary_repository
        self._replenishment = replenishment_repository
        self._config = config

    def execute(
        self,
        store_id: str,
        range_days: Optional[int],
        category: Optional[str],
    ) -> Dict[str, Any]:
        """执行概览查询。"""
        as_of_date_str = self._replenishment.get_latest_as_of_date(store_id)
        if as_of_date_str is None:
            raise ValueError(f"门店 {store_id} 无数据")

        category_for_metrics = category if category else "all"
        date_range = self._sales_metrics.get_date_range(store_id, category_for_metrics)
        if date_range is None:
            actual_start = as_of_date_str
            actual_end = as_of_date_str
        else:
            actual_start = date_range["min_date"]
            actual_end = date_range["max_date"]

        # 根据 range_days 计算筛选起始日期
        if range_days is not None:
            end_dt = datetime.strptime(actual_end, "%Y-%m-%d")
            selected_start = (end_dt - timedelta(days=range_days - 1)).strftime("%Y-%m-%d")
            sales_start = max(actual_start, selected_start)
        else:
            sales_start = actual_start

        raw_daily_sales = self._sales_metrics.get_daily_sales(
            store_id, category_for_metrics, sales_start, actual_end
        )

        total_sold = sum(d["total_units_sold"] for d in raw_daily_sales)
        avg_daily = round(total_sold / len(raw_daily_sales), 1) if raw_daily_sales else 0.0

        # 对齐前端契约（07-API.md §3.6 / DailySales）：字段名统一为 units_sold
        daily_sales = [
            {"date": d["date"], "units_sold": d["total_units_sold"]}
            for d in raw_daily_sales
        ]

        repl_list = self._replenishment.get_replenishments_by_store(
            store_id=store_id,
            category=category,
            as_of_date=as_of_date_str,
        )

        current_inventory_total = sum(r["current_inventory"] for r in repl_list)
        low_stock_count = sum(1 for r in repl_list if r["inventory_status"] == "low")
        critical_stock_count = sum(1 for r in repl_list if r["inventory_status"] == "critical")

        window_label = range_to_window_label(range_days)
        display_rankings = self._product_summary.get_rankings(
            store_id=store_id,
            window_label=window_label,
            category=category,
            top_n=self._config.ranking_top_n,
            bottom_n=self._config.ranking_bottom_n,
        )

        return {
            "context": {
                "store_id": store_id,
                "category": category or "all",
                "time_range": f"{range_days}d" if range_days is not None else "all",
                "as_of_date": as_of_date_str,
                "actual_data_start": actual_start,
                "actual_data_end": actual_end,
            },
            "data": {
                "kpis": {
                    "avg_daily_units_sold": avg_daily,
                    "current_inventory_total": current_inventory_total,
                    "low_stock_count": low_stock_count,
                    "critical_stock_count": critical_stock_count,
                },
                "daily_sales": daily_sales,
                "top_products": display_rankings["top"],
                "bottom_products": display_rankings["bottom"],
                "data_date_note": None,
            },
        }


# ─── 单例 ─────────────────────────────────────────────────────────
_query = OverviewQuery(
    sales_metrics_repository,
    product_summary_repository,
    replenishment_repository,
    config_repository,
)
