"""
基础设施层共享工具 - utils.py
============================
"""

import os
from datetime import date, datetime


def default_data_dir() -> str:
    """返回默认的预计算数据目录路径。"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "processed_data",
    )


def normalize_date(value) -> str:
    """统一日期为 YYYY-MM-DD 字符串。"""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def range_to_window_label(range_days: int | None) -> str:
    """将 range_days 转换为离线表的 window_label。"""
    mapping = {7: "7d", 30: "30d", 90: "90d", 180: "180d"}
    return mapping.get(range_days, "all")
