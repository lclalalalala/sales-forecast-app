"""
补货查询 - /api/replenishment
=============================
合并原 routes/replenishment_routes.py 与 application/replenishment_query.py。
"""

from typing import Any, Dict, Optional

from flask import Blueprint, request

from infrastructure.config_repository import ConfigRepository, config_repository
from infrastructure.forecast_repository import ForecastRepository, forecast_repository
from infrastructure.replenishment_repository import ReplenishmentRepository, replenishment_repository
from schemas import requests, responses


# ─── Blueprint ────────────────────────────────────────────────────
replenishment_bp = Blueprint("replenishment", __name__, url_prefix="/api")


@replenishment_bp.route("/replenishment", methods=["GET"])
def get_replenishment():
    """补货建议。"""
    try:
        store_id = requests.parse_store_id(request.args.get("store_id"), "S001")
        category = requests.parse_category(request.args.get("category"))

        result = _query.execute(store_id, category)
        return responses.build_response(result["context"], result["data"])
    except requests.RequestValidationError as e:
        return responses.build_error(e.code, e.message)
    except Exception as e:
        return responses.build_internal_error(str(e))


# ─── Query ────────────────────────────────────────────────────────

class ReplenishmentQuery:
    """补货建议查询。全部从离线预计算表读取。"""

    def __init__(
        self,
        replenishment_repository: ReplenishmentRepository,
        forecast_repository: ForecastRepository,
        config: ConfigRepository,
    ):
        self._replenishment_repository = replenishment_repository
        self._forecast_repository = forecast_repository
        self._config = config

    def execute(
        self,
        store_id: str,
        category: Optional[str],
    ) -> Dict[str, Any]:
        """执行补货查询。"""
        as_of_date_str = self._replenishment_repository.get_latest_as_of_date(store_id)
        if as_of_date_str is None:
            raise ValueError(f"门店 {store_id} 无数据")

        suggestions = self._replenishment_repository.get_replenishments_by_store(
            store_id=store_id, category=category, as_of_date=as_of_date_str,
        )

        for s in suggestions:
            forecast_output = self._forecast_repository.get_forecast(
                store_id, s["product_id"], as_of_date_str
            )
            if forecast_output is not None:
                s["forecast_7d"] = [
                    {"date": p.date, "units_sold": p.units_sold}
                    for p in forecast_output.daily_forecast
                ]
            else:
                s["forecast_7d"] = []

        suggestions.sort(key=lambda x: (-x["suggested_replenishment"], x["product_id"]))

        return {
            "context": {
                "store_id": store_id, "category": category or "all",
                "time_range": "90d", "as_of_date": as_of_date_str,
                "actual_data_start": as_of_date_str, "actual_data_end": as_of_date_str,
            },
            "data": {"suggestions": suggestions},
        }


# ─── 单例 ─────────────────────────────────────────────────────────
_query = ReplenishmentQuery(
    replenishment_repository,
    forecast_repository,
    config_repository,
)
