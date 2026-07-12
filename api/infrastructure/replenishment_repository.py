"""
补货推荐预计算表仓储 - replenishment_repository.py
====================================================

读取离线批处理产出的 fact_daily_replenishment.csv，
为在线 API 提供只读查询能力。
"""

import os
from typing import Dict, List, Optional

import pandas as pd

from infrastructure.utils import default_data_dir, normalize_date


class ReplenishmentRepository:
    """预计算补货推荐表仓储。"""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._replenishment_path = os.path.join(data_dir, "fact_daily_replenishment.csv")
        self._replenishment_df: Optional[pd.DataFrame] = None
        self._load()

    def _load(self) -> None:
        """加载预计算补货推荐表。"""
        if os.path.exists(self._replenishment_path):
            self._replenishment_df = pd.read_csv(self._replenishment_path)
            self._replenishment_df["as_of_date"] = pd.to_datetime(
                self._replenishment_df["as_of_date"]
            ).dt.strftime("%Y-%m-%d")
            self._replenishment_df["inventory_date"] = pd.to_datetime(
                self._replenishment_df["inventory_date"]
            ).dt.strftime("%Y-%m-%d")
        else:
            self._replenishment_df = pd.DataFrame()

    def get_latest_as_of_date(
        self,
        store_id: str,
        as_of_date=None,
    ) -> Optional[str]:
        """
        返回指定门店在预计算补货表中的最新可用 as_of_date。

        若提供 as_of_date，则返回不超过该日期的最近日期；
        否则返回全局最新日期。
        """
        if self._replenishment_df is None or self._replenishment_df.empty:
            return None

        df = self._replenishment_df[self._replenishment_df["store_id"] == store_id]
        if df.empty:
            return None

        if as_of_date is not None:
            as_of = normalize_date(as_of_date)
            df = df[df["as_of_date"] <= as_of]
            if df.empty:
                return None

        return str(df["as_of_date"].max())

    def get_replenishment(
        self,
        store_id: str,
        product_id: str,
        as_of_date,
    ) -> Optional[Dict]:
        """
        读取指定 (store_id, product_id, as_of_date) 的预计算补货推荐。

        若指定日期无数据，回退到该组合最近的预计算日期。

        Returns:
            dict 或 None（无预计算数据时）。
        """
        if self._replenishment_df is None or self._replenishment_df.empty:
            return None

        as_of = normalize_date(as_of_date)
        df = self._replenishment_df[
            (self._replenishment_df["store_id"] == store_id)
            & (self._replenishment_df["product_id"] == product_id)
        ]
        if df.empty:
            return None

        # 精确匹配
        exact = df[df["as_of_date"] == as_of]
        if not exact.empty:
            return self._row_to_dict(exact.iloc[0])

        # 回退到最近的前序日期
        prior = df[df["as_of_date"] <= as_of]
        if prior.empty:
            return None
        latest = prior.sort_values("as_of_date").iloc[-1]
        return self._row_to_dict(latest)

    def get_replenishments_by_store(
        self,
        store_id: str,
        category: Optional[str] = None,
        as_of_date=None,
    ) -> List[Dict]:
        """
        读取指定门店的预计算补货推荐列表。

        Args:
            store_id: 门店 ID
            category: 类别过滤（可选）
            as_of_date: 指定日期，不提供则使用最新日期；若无精确匹配则回退到最近前序日期

        Returns:
            补货推荐 dict 列表。
        """
        if self._replenishment_df is None or self._replenishment_df.empty:
            return []

        df = self._replenishment_df[self._replenishment_df["store_id"] == store_id]

        if as_of_date is not None:
            as_of = normalize_date(as_of_date)
            # 回退到最近的前序日期
            prior = df[df["as_of_date"] <= as_of]
            if prior.empty:
                return []
            target_date = prior["as_of_date"].max()
            df = df[df["as_of_date"] == target_date]
        else:
            # 使用最新日期
            if df.empty:
                return []
            latest = df["as_of_date"].max()
            df = df[df["as_of_date"] == latest]

        if df.empty:
            return []

        # 若需要按 category 过滤，需要关联 dim_product；此处仅当 replenishment 表包含 category 时直接过滤
        if category is not None and "category" in df.columns:
            df = df[df["category"] == category]

        return [self._row_to_dict(row) for _, row in df.iterrows()]

    def _row_to_dict(self, row: pd.Series) -> Dict:
        """将 DataFrame 行转换为 API 响应 schema。"""
        return {
            "product_id": str(row["product_id"]),
            "current_inventory": int(row["current_inventory"]),
            "in_transit_inventory": int(row["in_transit_inventory"]),
            "inventory_date": str(row["inventory_date"]),
            "lead_time_k": int(row["effective_lead_time_days"]),
            "lead_time_k_source": str(row.get("k_source", "estimated")),
            "forecast_7d": [],  # 预计算表不存储 7 天明细，由 ForecastRepository 提供
            "forecast_k_total": float(row["forecast_during_lead_time"]),
            "safety_stock": int(row["safety_stock"]),
            "suggested_replenishment": int(row["suggested_replenishment"]),
            "inventory_status": str(row["inventory_status"]),
            "status": "ready" if row.get("forecast_status") == "ready" else "unavailable",
            "message": row.get("message") if pd.notna(row.get("message")) else None,
        }


# 模块级单例
replenishment_repository = ReplenishmentRepository(default_data_dir())
