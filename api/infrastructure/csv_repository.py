"""
CSV 数据仓储 - CsvRepository
==========================
负责加载 sales_data.csv 并提供原始数据查询。
只读、无业务逻辑，是基础设施层的最底层。
"""

import os
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd

from infrastructure.utils import resource_base


class CsvRepository:
    """
    CSV 文件仓库。

    - 首次实例化时加载并缓存 DataFrame
    - 所有查询返回副本，避免外部修改
    """

    _RAW_COLUMN_NAMES = [
        "Date",
        "Store ID",
        "Product ID",
        "Category",
        "Region",
        "Inventory Level",
        "Units Sold",
        "Units Ordered",
        "Price",
        "Discount",
        "Weather Condition",
        "Promotion",
        "Competitor Pricing",
        "Seasonality",
        "Epidemic",
        "Demand",
    ]

    def __init__(self, data_path: Optional[str] = None):
        """
        初始化仓库。

        Args:
            data_path: CSV 文件路径，默认定位到项目根目录 data/sales_data.csv
        """
        if data_path is None:
            data_path = os.path.join(resource_base(), "data", "sales_data.csv")

        self._data_path = data_path
        self._df: Optional[pd.DataFrame] = None
        self._loaded = False
        self._load_data()

    def _load_data(self) -> None:
        """加载并校验 CSV。"""
        try:
            if not os.path.exists(self._data_path):
                raise FileNotFoundError(f"数据文件不存在: {self._data_path}")

            df = pd.read_csv(self._data_path)

            missing = [c for c in self._RAW_COLUMN_NAMES if c not in df.columns]
            if missing:
                raise ValueError(f"CSV 缺少必要列: {missing}")

            df["Date"] = pd.to_datetime(df["Date"])
            df["Promotion"] = df["Promotion"].astype(int)

            self._df = df
            self._loaded = True
        except Exception as e:
            self._loaded = False
            raise RuntimeError(f"数据加载失败: {e}") from e

    # ------------------------------------------------------------------
    # 数据状态
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        return self._loaded

    def get_summary(self) -> Dict:
        """数据集摘要。"""
        if self._df is None:
            return {}
        return {
            "total_rows": len(self._df),
            "date_range": {
                "start": self._df["Date"].min().strftime("%Y-%m-%d"),
                "end": self._df["Date"].max().strftime("%Y-%m-%d"),
            },
            "stores": self._df["Store ID"].nunique(),
            "products": self._df["Product ID"].nunique(),
            "categories": self._df["Category"].nunique(),
        }

    # ------------------------------------------------------------------
    # 元数据查询
    # ------------------------------------------------------------------

    def get_stores(self) -> List[Dict]:
        """返回门店列表，每项含 id 与 region。"""
        if self._df is None:
            return []
        stores = self._df[["Store ID", "Region"]].drop_duplicates()
        return [
            {"id": row["Store ID"], "region": row["Region"]}
            for _, row in stores.iterrows()
        ]

    def get_categories(self) -> List[str]:
        """返回所有类别。"""
        if self._df is None:
            return []
        return sorted(self._df["Category"].dropna().unique().tolist())

    def get_products(self, store_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        """
        返回商品元数据列表。

        当前实现按 Product ID 去重，取首个类别和价格；store_id 仅用于未来扩展。
        """
        if self._df is None:
            return []

        df = self._df.copy()
        if store_id:
            df = df[df["Store ID"] == store_id]
        if category:
            df = df[df["Category"] == category]

        products = (
            df.groupby("Product ID")
            .agg({"Category": "first", "Price": "first"})
            .reset_index()
        )
        return [
            {"id": row["Product ID"], "category": row["Category"], "price": float(row["Price"])}
            for _, row in products.iterrows()
        ]

    def get_product_info(self, store_id: str, product_id: str) -> Dict:
        """返回指定门店+商品的基本信息。"""
        if self._df is None:
            return {"product_id": product_id, "category": "", "price": 0.0}

        mask = (self._df["Store ID"] == store_id) & (self._df["Product ID"] == product_id)
        data = self._df[mask]
        if data.empty:
            return {"product_id": product_id, "category": "", "price": 0.0}

        first = data.iloc[0]
        return {
            "product_id": product_id,
            "category": first["Category"],
            "price": float(first["Price"]),
        }

    # ------------------------------------------------------------------
    # 原始数据查询
    # ------------------------------------------------------------------

    def get_rows(
        self,
        store_id: Optional[str] = None,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        按条件筛选原始行，返回副本。

        所有边界均包含。
        """
        if self._df is None:
            return pd.DataFrame()

        df = self._df.copy()
        if store_id:
            df = df[df["Store ID"] == store_id]
        if product_id:
            df = df[df["Product ID"] == product_id]
        if category:
            df = df[df["Category"] == category]
        if start_date is not None:
            df = df[df["Date"] >= start_date]
        if end_date is not None:
            df = df[df["Date"] <= end_date]

        return df.copy()


# 模块级单例，使用默认路径
csv_repository = CsvRepository()
