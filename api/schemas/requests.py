"""
请求参数校验 - Requests
======================
统一解析与校验 API 查询参数。
"""

from typing import Optional


class RequestValidationError(Exception):
    """请求参数校验失败。"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def parse_range(range_value: Optional[str]) -> Optional[int]:
    """
    解析时间范围字符串。

    支持：7d, 30d, 90d, 180d, all
    返回天数；all 返回 None。
    """
    if not range_value or range_value == "all":
        return None

    mapping = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "180d": 180,
    }
    if range_value not in mapping:
        raise RequestValidationError(
            "INVALID_RANGE",
            "time_range 必须是 7d、30d、90d、180d 或 all",
        )
    return mapping[range_value]


def parse_positive_int(value: Optional[str], default: int, field: str) -> int:
    """解析正整数查询参数。"""
    if value is None or value == "":
        return default
    try:
        n = int(value)
    except ValueError:
        raise RequestValidationError(
            "INVALID_PARAMETER",
            f"{field} 必须是整数",
        )
    if n < 1:
        raise RequestValidationError(
            "INVALID_PARAMETER",
            f"{field} 必须大于 0",
        )
    return n


def parse_inventory_status(status: Optional[str]) -> Optional[str]:
    """解析并校验库存状态参数。"""
    if not status or status == "all":
        return None

    valid = {"critical", "low", "normal", "sufficient", "undetermined"}
    if status not in valid:
        raise RequestValidationError(
            "INVALID_INVENTORY_STATUS",
            f"inventory_status 必须是 all、critical、low、normal、sufficient 或 undetermined",
        )
    return status


def parse_store_id(store_id: Optional[str], default: str) -> str:
    """解析门店 ID。"""
    return store_id.strip() if store_id else default


def parse_category(category: Optional[str]) -> Optional[str]:
    """解析类别参数；空字符串视为 None。"""
    return category.strip() if category else None
