"""
维度表仓储 - dim_repository.py
==============================

读取离线批处理产出的 dim_store.csv 与 dim_product.csv，
为元数据接口（/api/stores、/api/categories、/api/products、商品详情）
提供门店 / 商品 / 类别的只读查询。

设计原则：在线层只读预计算维表，不再触碰原始 sales_data.csv。
"""

import os
from typing import Dict, List, Optional

import pandas as pd

from infrastructure.utils import default_data_dir


class DimRepository:
    """门店与商品维度表仓储（只读）。"""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._store_path = os.path.join(data_dir, "dim_store.csv")
        self._product_path = os.path.join(data_dir, "dim_product.csv")
        self._store_df: Optional[pd.DataFrame] = None
        self._product_df: Optional[pd.DataFrame] = None
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """加载门店与商品维表。"""
        store_ok = os.path.exists(self._store_path)
        product_ok = os.path.exists(self._product_path)
        self._store_df = pd.read_csv(self._store_path) if store_ok else pd.DataFrame()
        self._product_df = pd.read_csv(self._product_path) if product_ok else pd.DataFrame()
        self._loaded = store_ok and product_ok

    # ------------------------------------------------------------------
    # 数据状态
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        return self._loaded

    def counts(self) -> Dict[str, int]:
        """维表规模统计，供健康检查使用。"""
        stores = 0 if self._store_df is None else len(self._store_df)
        products = 0 if self._product_df is None else len(self._product_df)
        categories = len(self.get_categories())
        return {"stores": stores, "products": products, "categories": categories}

    # ------------------------------------------------------------------
    # 门店
    # ------------------------------------------------------------------

    def get_stores(self) -> List[Dict]:
        """返回门店列表，每项含 id、name、region。"""
        if self._store_df is None or self._store_df.empty:
            return []
        return [
            {
                "id": row["store_id"],
                "name": row["store_name"],
                "region": row["region"],
            }
            for _, row in self._store_df.iterrows()
        ]

    # ------------------------------------------------------------------
    # 商品与类别
    # ------------------------------------------------------------------

    def get_categories(self) -> List[str]:
        """返回所有商品类别（升序）。"""
        if self._product_df is None or self._product_df.empty:
            return []
        return sorted(self._product_df["category"].dropna().unique().tolist())

    def get_products(
        self,
        store_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """
        返回商品元数据列表。

        商品维表与门店无关，store_id 仅为接口兼容保留。
        """
        if self._product_df is None or self._product_df.empty:
            return []

        df = self._product_df
        if category:
            df = df[df["category"] == category]
        return [
            {
                "id": row["product_id"],
                "category": row["category"],
                "price": float(row["price"]),
            }
            for _, row in df.iterrows()
        ]

    def get_product_info(self, store_id: str, product_id: str) -> Dict:
        """返回指定商品的基本信息（store_id 保留以兼容调用方）。"""
        if self._product_df is None or self._product_df.empty:
            return {"product_id": product_id, "category": "", "price": 0.0}

        match = self._product_df[self._product_df["product_id"] == product_id]
        if match.empty:
            return {"product_id": product_id, "category": "", "price": 0.0}

        first = match.iloc[0]
        return {
            "product_id": product_id,
            "category": first["category"],
            "price": float(first["price"]),
        }


# 模块级单例
dim_repository = DimRepository(default_data_dir())
