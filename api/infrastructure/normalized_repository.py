"""
标准化数据仓储 - NormalizedRepository
====================================
在 CsvRepository 之上提供字段名统一、类型规整后的 DataFrame，
使领域服务不再依赖 CSV 原始列名。
"""

from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd

from infrastructure.csv_repository import CsvRepository, csv_repository


class NormalizedRepository:
    """
    标准化仓库。

    输出 DataFrame 使用以下标准列名：
        date, store_id, product_id, category, region,
        units_sold, units_ordered, inventory_level,
        price, discount, promotion, competitor_price,
        weather, seasonality, epidemic, demand,
        dayofweek, month, dayofyear, year
    """

    _COLUMN_MAP = {
        "Date": "date",
        "Store ID": "store_id",
        "Product ID": "product_id",
        "Category": "category",
        "Region": "region",
        "Inventory Level": "inventory_level",
        "Units Sold": "units_sold",
        "Units Ordered": "units_ordered",
        "Price": "price",
        "Discount": "discount",
        "Weather Condition": "weather",
        "Promotion": "promotion",
        "Competitor Pricing": "competitor_price",
        "Seasonality": "seasonality",
        "Epidemic": "epidemic",
        "Demand": "demand",
    }

    def __init__(self, csv_repo: CsvRepository):
        self._csv_repo = csv_repo

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """将原始 DataFrame 重命名并补充时间特征。"""
        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns=self._COLUMN_MAP).copy()
        df["dayofweek"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["dayofyear"] = df["date"].dt.dayofyear
        df["year"] = df["date"].dt.year
        return df

    def get_rows(
        self,
        store_id: Optional[str] = None,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """返回标准化后的行。"""
        raw = self._csv_repo.get_rows(
            store_id=store_id,
            product_id=product_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )
        return self._normalize(raw)

    def get_stores(self) -> List[Dict]:
        return self._csv_repo.get_stores()

    def get_categories(self) -> List[str]:
        return self._csv_repo.get_categories()

    def get_products(self, store_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        return self._csv_repo.get_products(store_id=store_id, category=category)

    def get_product_info(self, store_id: str, product_id: str) -> Dict:
        return self._csv_repo.get_product_info(store_id, product_id)

    def get_summary(self) -> Dict:
        return self._csv_repo.get_summary()


# 模块级单例
normalized_repository = NormalizedRepository(csv_repository)
