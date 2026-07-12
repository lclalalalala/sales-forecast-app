"""
商品销售窗口汇总仓储 - product_summary_repository.py
====================================================

读取离线批处理产出的 fact_product_sales_summary.csv，
为 /api/rankings 和 /api/overview 提供商品多窗口排名数据。

关联 fact_daily_replenishment.csv 补充 coverage_days 和 inventory_date。
"""

import os
from typing import Dict, List, Optional

import pandas as pd

from infrastructure.utils import default_data_dir


class ProductSummaryRepository:
    """商品销售窗口汇总表仓储。"""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._summary_path = os.path.join(data_dir, "fact_product_sales_summary.csv")
        self._replenishment_path = os.path.join(data_dir, "fact_daily_replenishment.csv")
        self._summary_df: Optional[pd.DataFrame] = None
        self._replenishment_lookup: Optional[pd.DataFrame] = None
        self._load()

    def _load(self) -> None:
        """加载汇总表与补货表（仅用于关联 coverage_days/inventory_date）。"""
        if os.path.exists(self._summary_path):
            self._summary_df = pd.read_csv(self._summary_path)
        else:
            self._summary_df = pd.DataFrame()

        # 加载补货表，取每个 (store_id, product_id) 最新 as_of_date 的行
        if os.path.exists(self._replenishment_path):
            repl_df = pd.read_csv(self._replenishment_path)
            repl_df["as_of_date"] = pd.to_datetime(repl_df["as_of_date"]).dt.strftime("%Y-%m-%d")
            # 取每个 (store_id, product_id) 最新日期
            repl_df = repl_df.sort_values("as_of_date")
            self._replenishment_lookup = repl_df.groupby(
                ["store_id", "product_id"]
            ).last().reset_index()
        else:
            self._replenishment_lookup = pd.DataFrame()

    def get_rankings(
        self,
        store_id: str,
        window_label: str = "90d",
        category: Optional[str] = None,
        inventory_status: Optional[str] = None,
        top_n: int = 5,
        bottom_n: int = 5,
    ) -> Dict:
        """
        获取商品排名（Top / Bottom）。

        Args:
            store_id: 门店 ID
            window_label: 时间窗口标签 (7d/30d/90d/180d/all)
            category: 类别过滤（可选）
            inventory_status: 库存状态过滤（可选）
            top_n: Top 数量
            bottom_n: Bottom 数量

        Returns:
            {top: [RankingItem], bottom: [RankingItem], total_candidates: int}
        """
        if self._summary_df is None or self._summary_df.empty:
            return {"top": [], "bottom": [], "total_candidates": 0}

        df = self._summary_df[
            (self._summary_df["store_id"] == store_id)
            & (self._summary_df["window_label"] == window_label)
        ]

        if category is not None:
            df = df[df["category"] == category]

        if df.empty:
            return {"top": [], "bottom": [], "total_candidates": 0}

        # 关联补货表获取 coverage_days 和 inventory_date
        df = self._enrich_with_replenishment(df)

        # 库存状态过滤
        if inventory_status is not None:
            df = df[df["inventory_status"] == inventory_status]

        if df.empty:
            return {"top": [], "bottom": [], "total_candidates": 0}

        total_candidates = len(df)

        # Top：销量降序，相同按 product_id 升序
        top_df = df.sort_values(
            ["total_units_sold", "product_id"],
            ascending=[False, True],
        ).head(top_n)

        # Bottom：销量升序，相同按 product_id 升序
        bottom_df = df.sort_values(
            ["total_units_sold", "product_id"],
            ascending=[True, True],
        ).head(bottom_n)

        top_items = [self._row_to_ranking_item(i + 1, row) for i, (_, row) in enumerate(top_df.iterrows())]
        bottom_items = [self._row_to_ranking_item(i + 1, row) for i, (_, row) in enumerate(bottom_df.iterrows())]

        return {
            "top": top_items,
            "bottom": bottom_items,
            "total_candidates": total_candidates,
        }

    def _enrich_with_replenishment(self, df: pd.DataFrame) -> pd.DataFrame:
        """关联补货表，补充 coverage_days 和 inventory_date。"""
        if self._replenishment_lookup is None or self._replenishment_lookup.empty:
            df = df.copy()
            df["coverage_days"] = None
            df["inventory_date"] = None
            return df

        # 选择补货表中需要的列
        repl_cols = self._replenishment_lookup[
            ["store_id", "product_id", "coverage_days", "inventory_date"]
        ].copy()

        merged = df.merge(
            repl_cols,
            on=["store_id", "product_id"],
            how="left",
        )
        return merged

    @staticmethod
    def _row_to_ranking_item(rank: int, row: pd.Series) -> Dict:
        """将 DataFrame 行转换为 RankingItem schema。"""
        avg_daily = float(row.get("avg_daily_units_sold", 0))
        current_inv = int(row.get("current_inventory", 0))

        # coverage_days: 优先使用关联值，否则从 current_inventory / avg_daily 计算
        coverage_days = row.get("coverage_days")
        if pd.isna(coverage_days):
            coverage_days = round(current_inv / avg_daily, 1) if avg_daily > 0 else None
        else:
            coverage_days = round(float(coverage_days), 1)

        inventory_date = row.get("inventory_date")
        if pd.isna(inventory_date):
            inventory_date = None
        else:
            inventory_date = str(inventory_date)

        return {
            "rank": rank,
            "product_id": str(row["product_id"]),
            "category": str(row.get("category", "")),
            "total_sold": int(row.get("total_units_sold", 0)),
            "avg_daily": round(avg_daily, 1),
            "current_inventory": current_inv,
            "inventory_date": inventory_date,
            "in_transit_inventory": int(row.get("in_transit_inventory", 0)),
            "coverage_days": coverage_days,
            "inventory_status": str(row.get("inventory_status", "undetermined")),
        }


# 模块级单例
product_summary_repository = ProductSummaryRepository(default_data_dir())
