"""
离线计算模块配置 - offline_calculation/config.py
================================================

集中管理离线计算常量、路径与 business.yaml 配置读取。
"""

import os
from typing import Any, Dict

import yaml


# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 默认路径
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "sales_data.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed_data")
BUSINESS_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "business.yaml")

# 业务常量（与 project_docs/03-Offline-data-process.md 保持一致）
DATA_VERSION = "v1"
MODEL_VERSION = "ensemble_v2"

SAFETY_STOCK_Z = 2.33
LEAD_TIME_WINDOW_DAYS = 90
ERROR_HORIZON = 3
ERROR_WINDOW_DAYS = 30
FORECAST_WINDOW_DAYS = 33

LEAD_TIME_MIN_DAYS = 0
LEAD_TIME_MAX_DAYS = 7
LEAD_TIME_FALLBACK_DAYS = 2

INSUFFICIENT_ERROR_STD = 1.0
MIN_ERROR_COUNT_FOR_STD = 2

# 库存状态阈值（默认值，会被 business.yaml 覆盖）
INVENTORY_STATUS_CRITICAL_LT = 2
INVENTORY_STATUS_LOW_LT = 4
INVENTORY_STATUS_NORMAL_LTE = 7


class OfflineConfig:
    """离线计算配置。"""

    def __init__(self, config: Dict[str, Any]):
        self._config = config or {}

    @classmethod
    def from_file(cls, path: str = BUSINESS_CONFIG_PATH) -> "OfflineConfig":
        """从 YAML 文件加载配置。"""
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    @property
    def default_store_id(self) -> str:
        return str(self._config.get("default", {}).get("store_id", "S001"))

    @property
    def default_time_range_days(self) -> int:
        return int(self._config.get("default", {}).get("time_range_days", 90))

    @property
    def lead_time_window_days(self) -> int:
        return int(
            self._config.get("lead_time", {}).get("estimation_window_days", LEAD_TIME_WINDOW_DAYS)
        )

    @property
    def lead_time_min_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("min_days", LEAD_TIME_MIN_DAYS))

    @property
    def lead_time_max_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("max_days", LEAD_TIME_MAX_DAYS))

    @property
    def lead_time_fallback_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("fallback_days", LEAD_TIME_FALLBACK_DAYS))

    @property
    def safety_stock_z(self) -> float:
        return float(self._config.get("safety_stock", {}).get("service_level_z", SAFETY_STOCK_Z))

    @property
    def safety_stock_error_window_days(self) -> int:
        return int(
            self._config.get("safety_stock", {}).get("error_window_days", ERROR_WINDOW_DAYS)
        )

    @property
    def safety_stock_insufficient_std(self) -> float:
        return float(
            self._config.get("safety_stock", {}).get("insufficient_error_std", INSUFFICIENT_ERROR_STD)
        )

    @property
    def safety_stock_min_error_count(self) -> int:
        return int(
            self._config.get("safety_stock", {}).get("min_error_count", MIN_ERROR_COUNT_FOR_STD)
        )

    @property
    def forecast_error_horizon(self) -> int:
        return int(self._config.get("forecast", {}).get("error_horizon", ERROR_HORIZON))

    @property
    def forecast_error_window_days(self) -> int:
        return int(self._config.get("forecast", {}).get("error_window_days", ERROR_WINDOW_DAYS))

    @property
    def forecast_window_days(self) -> int:
        return int(self._config.get("forecast", {}).get("forecast_window_days", FORECAST_WINDOW_DAYS))

    @property
    def offline_as_of_date_offset_days(self) -> int:
        return int(self._config.get("offline", {}).get("as_of_date_offset_days", 0))

    @property
    def inventory_status_basis(self) -> str:
        return str(
            self._config.get("inventory_status", {}).get("basis", "total_inventory")
        )

    @property
    def inventory_status_critical_lt(self) -> float:
        return float(
            self._config.get("inventory_status", {}).get(
                "critical_less_than", INVENTORY_STATUS_CRITICAL_LT
            )
        )

    @property
    def inventory_status_low_lt(self) -> float:
        return float(
            self._config.get("inventory_status", {}).get("low_less_than", INVENTORY_STATUS_LOW_LT)
        )

    @property
    def inventory_status_normal_lte(self) -> float:
        return float(
            self._config.get("inventory_status", {}).get(
                "normal_less_than_or_equal", INVENTORY_STATUS_NORMAL_LTE
            )
        )

    @property
    def ranking_top_n(self) -> int:
        return int(self._config.get("ranking", {}).get("top_n", 5))

    @property
    def ranking_bottom_n(self) -> int:
        return int(self._config.get("ranking", {}).get("bottom_n", 5))
