"""
日库存销量事实表仓储 - inventory_sales_repository.py
===================================================

读取离线批处理产出的 fact_daily_inventory_sales.csv，
为商品详情的历史销量 / 库存序列提供只读查询。

字段映射（离线 build_fact 阶段将原始 "Inventory Level" 重命名为 opening_inventory）：
    opening_inventory  -> inventory_level（期初库存，等价于原始库存水位）
    units_sold         -> units_sold

设计原则：在线层只读预计算事实表，替代原先在线遍历 sales_data.csv 的实现。
"""

import os
from typing import Dict, List, Optional

import pandas as pd

from infrastructure.utils import default_data_dir, normalize_date


class InventorySalesRepository:
    """日库存销量事实表仓储（只读）。"""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._path = os.path.join(data_dir, "fact_daily_inventory_sales.csv")
        self._df: Optional[pd.DataFrame] = None
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """加载事实表并规整日期与观测标记。"""
        if not os.path.exists(self._path):
            self._df = pd.DataFrame()
            self._loaded = False
            return

        df = pd.read_csv(self._path)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        # is_observed 可能被解析为 bool 或字符串，统一为 bool
        df["is_observed"] = (
            df["is_observed"].astype(str).str.strip().str.lower().isin(["true", "1"])
        )
        self._df = df
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def _filter(
        self,
        store_id: str,
        product_id: str,
        observed_only: bool,
    ) -> pd.DataFrame:
        if self._df is None or self._df.empty:
            return pd.DataFrame()
        df = self._df[
            (self._df["store_id"] == store_id)
            & (self._df["product_id"] == product_id)
        ]
        if observed_only:
            df = df[df["is_observed"]]
        return df

    def get_history(
        self,
        store_id: str,
        product_id: str,
        start_date=None,
        end_date=None,
        observed_only: bool = True,
    ) -> List[Dict]:
        """
        返回指定门店+商品的历史序列，按日期升序。

        Returns:
            [{date, units_sold, inventory_level}]，其中 inventory_level 取期初库存。
        """
        df = self._filter(store_id, product_id, observed_only)
        if df.empty:
            return []

        if start_date is not None:
            df = df[df["date"] >= normalize_date(start_date)]
        if end_date is not None:
            df = df[df["date"] <= normalize_date(end_date)]

        df = df.sort_values("date")
        return [
            {
                "date": str(row["date"]),
                "units_sold": int(row["units_sold"]),
                "inventory_level": int(row["opening_inventory"]),
            }
            for _, row in df.iterrows()
        ]

    def get_observed_date_range(
        self,
        store_id: str,
        product_id: str,
    ) -> Optional[Dict]:
        """
        返回指定门店+商品观测数据的日期范围。

        Returns:
            {"min_date": "YYYY-MM-DD", "max_date": "YYYY-MM-DD"} 或 None
        """
        df = self._filter(store_id, product_id, observed_only=True)
        if df.empty:
            return None
        return {"min_date": str(df["date"].min()), "max_date": str(df["date"].max())}


# 模块级单例
inventory_sales_repository = InventorySalesRepository(default_data_dir())
