"""
基础设施层共享工具 - utils.py
============================
"""

import os
import sys
from datetime import date, datetime


def resource_base() -> str:
    """返回资源（数据、配置、前端静态文件）的根目录。

    - PyInstaller 冻结环境：解包目录 ``sys._MEIPASS``（打包进去的 data/config/app 等）。
    - 开发环境：项目根目录（本文件位于 ``<root>/api/infrastructure/utils.py``，上溯三级）。

    所有依赖磁盘资源的路径都应基于此函数，以保证开发态与打包态一致。
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def default_data_dir() -> str:
    """返回默认的预计算数据目录路径。"""
    return os.path.join(resource_base(), "data", "processed_data")


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
