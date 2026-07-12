"""
配置仓储 - ConfigRepository
==========================
加载并校验 config/business.yaml，为各层提供类型化的业务配置访问。
"""

import os
from typing import Any, Dict

import yaml

from infrastructure.utils import resource_base


_CONFIG_PATH = os.path.join(resource_base(), "config", "business.yaml")


def _load_config() -> Dict[str, Any]:
    """加载 YAML 配置文件。"""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class ConfigRepository:
    """
    业务配置访问类。

    提供对 business.yaml 中各配置块的只读访问，若配置缺失则使用文档约定的默认值。
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = config

    @classmethod
    def from_file(cls, path: str = _CONFIG_PATH) -> "ConfigRepository":
        """从指定 YAML 文件创建实例。"""
        with open(path, "r", encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    @property
    def default_store_id(self) -> str:
        return str(self._config.get("default", {}).get("store_id", "S001"))

    @property
    def default_time_range_days(self) -> int:
        return int(self._config.get("default", {}).get("time_range_days", 90))

    @property
    def ranking_metric(self) -> str:
        return str(self._config.get("ranking", {}).get("metric", "units_sold"))

    @property
    def ranking_top_n(self) -> int:
        return int(self._config.get("ranking", {}).get("top_n", 5))

    @property
    def ranking_bottom_n(self) -> int:
        return int(self._config.get("ranking", {}).get("bottom_n", 5))

    @property
    def lead_time_window_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("estimation_window_days", 90))

    @property
    def lead_time_min_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("min_days", 0))

    @property
    def lead_time_max_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("max_days", 7))

    @property
    def lead_time_fallback_days(self) -> int:
        return int(self._config.get("lead_time", {}).get("fallback_days", 2))

    @property
    def safety_stock_z(self) -> float:
        return float(self._config.get("safety_stock", {}).get("service_level_z", 2.33))

    @property
    def safety_stock_error_window_days(self) -> int:
        return int(self._config.get("safety_stock", {}).get("error_window_days", 30))

    @property
    def safety_stock_insufficient_std(self) -> float:
        return float(self._config.get("safety_stock", {}).get("insufficient_error_std", 1))

    @property
    def offline_output_dir(self) -> str:
        return str(self._config.get("offline", {}).get("output_dir", "data/processed_data"))

    @property
    def offline_as_of_date_offset_days(self) -> int:
        return int(self._config.get("offline", {}).get("as_of_date_offset_days", 0))

    @property
    def forecast_window_days(self) -> int:
        return int(self._config.get("forecast", {}).get("forecast_window_days", 33))

    @property
    def inventory_status_basis(self) -> str:
        return str(self._config.get("inventory_status", {}).get("basis", "total_inventory"))

    @property
    def inventory_status_method(self) -> str:
        return str(self._config.get("inventory_status", {}).get("method", "coverage_days"))

    @property
    def inventory_status_critical_lt(self) -> float:
        return float(self._config.get("inventory_status", {}).get("critical_less_than", 2))

    @property
    def inventory_status_low_lt(self) -> float:
        return float(self._config.get("inventory_status", {}).get("low_less_than", 4))

    @property
    def inventory_status_normal_lte(self) -> float:
        return float(self._config.get("inventory_status", {}).get("normal_less_than_or_equal", 7))


# 模块级单例
config_repository = ConfigRepository(_load_config())
