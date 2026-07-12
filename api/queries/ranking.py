"""
排名查询 - /api/rankings
========================
合并原 routes/ranking_routes.py 与 application/ranking_query.py。
"""

from typing import Any, Dict, Optional

from flask import Blueprint, request

from infrastructure.config_repository import ConfigRepository, config_repository
from infrastructure.replenishment_repository import ReplenishmentRepository, replenishment_repository
from infrastructure.product_summary_repository import ProductSummaryRepository, product_summary_repository
from infrastructure.sales_metrics_repository import SalesMetricsRepository, sales_metrics_repository
from infrastructure.utils import range_to_window_label
from schemas import requests, responses


# ─── Blueprint ────────────────────────────────────────────────────
ranking_bp = Blueprint("ranking", __name__, url_prefix="/api")


@ranking_bp.route("/rankings", methods=["GET"])
def get_rankings():
    """商品销量排名。"""
    try:
        store_id = requests.parse_store_id(request.args.get("store_id"), "S001")
        range_value = requests.parse_range(request.args.get("range"))
        category = requests.parse_category(request.args.get("category"))
        inventory_status = requests.parse_inventory_status(request.args.get("inventory_status"))
        top_n = requests.parse_positive_int(
            request.args.get("top_n"), config_repository.ranking_top_n, "top_n",
        )
        bottom_n = requests.parse_positive_int(
            request.args.get("bottom_n"), config_repository.ranking_bottom_n, "bottom_n",
        )

        result = _query.execute(store_id, range_value, category, inventory_status, top_n, bottom_n)
        return responses.build_response(result["context"], result["data"])
    except requests.RequestValidationError as e:
        return responses.build_error(e.code, e.message, e.status_code)
    except Exception as e:
        return responses.build_internal_error(str(e))


# ─── Query ────────────────────────────────────────────────────────

class RankingQuery:
    """商品排名查询。全部从离线预计算表读取。"""

    def __init__(
        self,
        product_summary_repository: ProductSummaryRepository,
        replenishment_repository: ReplenishmentRepository,
        sales_metrics_repository: SalesMetricsRepository,
        config: ConfigRepository,
    ):
        self._product_summary = product_summary_repository
        self._replenishment = replenishment_repository
        self._sales_metrics = sales_metrics_repository
        self._config = config

    def execute(
        self,
        store_id: str,
        range_days: Optional[int],
        category: Optional[str],
        inventory_status: Optional[str],
        top_n: int,
        bottom_n: int,
    ) -> Dict[str, Any]:
        """执行排名查询。"""
        as_of_date_str = self._replenishment.get_latest_as_of_date(store_id)
        if as_of_date_str is None:
            raise requests.RequestValidationError(
                "STORE_NOT_FOUND", f"门店 {store_id} 不存在或无数据", status_code=404
            )

        category_for_metrics = category if category else "all"
        date_range = self._sales_metrics.get_date_range(store_id, category_for_metrics)
        if date_range is None:
            actual_start = as_of_date_str
            actual_end = as_of_date_str
        else:
            actual_start = date_range["min_date"]
            actual_end = date_range["max_date"]

        window_label = range_to_window_label(range_days)
        rankings = self._product_summary.get_rankings(
            store_id=store_id, window_label=window_label,
            category=category, inventory_status=inventory_status,
            top_n=top_n, bottom_n=bottom_n,
        )

        return {
            "context": {
                "store_id": store_id, "category": category or "all",
                "time_range": f"{range_days}d" if range_days is not None else "all",
                "as_of_date": as_of_date_str,
                "actual_data_start": actual_start, "actual_data_end": actual_end,
            },
            "data": {
                "top": rankings["top"], "bottom": rankings["bottom"],
                "total_candidates": rankings["total_candidates"],
            },
        }


# ─── 单例 ─────────────────────────────────────────────────────────
_query = RankingQuery(
    product_summary_repository,
    replenishment_repository,
    sales_metrics_repository,
    config_repository,
)
