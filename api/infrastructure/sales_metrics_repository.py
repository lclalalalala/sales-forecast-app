"""
门店类别日销量汇总仓储 - sales_metrics_repository.py
===================================================

读取离线批处理产出的 fact_daily_sales_metrics.csv，
为 /api/overview 提供门店-日期-类别维度的日销量汇总。
"""

import os
from typing import Dict, List, Optional

import pandas as pd

from infrastructure.utils import default_data_dir, normalize_date


class SalesMetricsRepository:
    """门店类别日销量汇总表仓储。"""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._metrics_path = os.path.join(data_dir, "fact_daily_sales_metrics.csv")
        self._metrics_df: Optional[pd.DataFrame] = None
        self._load()

    def _load(self) -> None:
        """加载销量汇总表。"""
        if os.path.exists(self._metrics_path):
            self._metrics_df = pd.read_csv(self._metrics_path)
            self._metrics_df["date"] = pd.to_datetime(
                self._metrics_df["date"]
            ).dt.strftime("%Y-%m-%d")
        else:
            self._metrics_df = pd.DataFrame()

    def get_daily_sales(
        self,
        store_id: str,
        category: str = "all",
        start_date=None,
        end_date=None,
    ) -> List[Dict]:
        """
        获取指定门店的每日销量趋势。

        Args:
            store_id: 门店 ID
            category: 类别过滤，默认 "all" 使用汇总行
            start_date: 起始日期（含）
            end_date: 结束日期（含）

        Returns:
            [{date, total_units_sold}] 列表，按日期升序
        """
        if self._metrics_df is None or self._metrics_df.empty:
            return []

        df = self._metrics_df[
            (self._metrics_df["store_id"] == store_id)
            & (self._metrics_df["category"] == category)
        ]

        if start_date is not None:
            start = normalize_date(start_date)
            df = df[df["date"] >= start]

        if end_date is not None:
            end = normalize_date(end_date)
            df = df[df["date"] <= end]

        df = df.sort_values("date")

        return [
            {"date": str(row["date"]), "total_units_sold": int(row["total_units_sold"])}
            for _, row in df.iterrows()
        ]

    def get_date_range(
        self,
        store_id: str,
        category: str = "all",
    ) -> Optional[Dict]:
        """
        获取指定门店销量数据的日期范围。

        Returns:
            {"min_date": "YYYY-MM-DD", "max_date": "YYYY-MM-DD"} 或 None
        """
        if self._metrics_df is None or self._metrics_df.empty:
            return None

        df = self._metrics_df[
            (self._metrics_df["store_id"] == store_id)
            & (self._metrics_df["category"] == category)
        ]

        if df.empty:
            return None

        return {
            "min_date": str(df["date"].min()),
            "max_date": str(df["date"].max()),
        }


# 模块级单例
sales_metrics_repository = SalesMetricsRepository(default_data_dir())
