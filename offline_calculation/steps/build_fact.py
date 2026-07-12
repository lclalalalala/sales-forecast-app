"""
构建标准化事实表 - offline_calculation/steps/build_fact.py
==========================================================

生成 fact_daily_inventory_sales：补齐自然日期、计算售后库存、标记 is_observed。
"""

from typing import Tuple

import pandas as pd


def build_fact_daily_inventory_sales(raw_df: pd.DataFrame, data_version: str = "v1") -> pd.DataFrame:
    """
    构建每日库存销售事实表。

    Args:
        raw_df: 已标准化的原始 DataFrame，包含 date, store_id, product_id, category,
                inventory_level, units_sold, units_ordered
        data_version: 数据版本

    Returns:
        fact DataFrame
    """
    fact = raw_df[[
        "date", "store_id", "product_id", "category",
        "inventory_level", "units_sold", "units_ordered"
    ]].copy()

    fact = fact.rename(columns={"inventory_level": "opening_inventory"})
    fact["date"] = pd.to_datetime(fact["date"])
    fact["opening_inventory"] = fact["opening_inventory"].astype(int)
    fact["units_sold"] = fact["units_sold"].astype(int)
    fact["units_ordered"] = fact["units_ordered"].astype(int)
    fact["closing_inventory"] = fact["opening_inventory"] - fact["units_sold"]
    fact["is_observed"] = True

    # 补齐自然日期
    min_date = fact["date"].min().normalize()
    max_date = fact["date"].max().normalize()
    date_range = pd.date_range(start=min_date, end=max_date, freq="D")

    groups = []
    for (store_id, product_id), group in fact.groupby(["store_id", "product_id"]):
        category = group["category"].iloc[0]
        group = group.sort_values("date").reset_index(drop=True)
        group_dates = set(group["date"])
        missing_dates = [d for d in date_range if d not in group_dates]

        if missing_dates:
            full_dates = pd.DataFrame({"date": date_range})
            full_group = full_dates.merge(
                group,
                on="date",
                how="left",
            )
            full_group["store_id"] = store_id
            full_group["product_id"] = product_id
            full_group["category"] = category
            full_group["opening_inventory"] = full_group["opening_inventory"].ffill().fillna(0).astype(int)
            full_group["units_sold"] = full_group["units_sold"].fillna(0).astype(int)
            full_group["units_ordered"] = full_group["units_ordered"].fillna(0).astype(int)
            full_group["is_observed"] = full_group["is_observed"].fillna(False)
            full_group["closing_inventory"] = (
                full_group["opening_inventory"] - full_group["units_sold"]
            )
            groups.append(full_group)
        else:
            groups.append(group)

    fact = pd.concat(groups, ignore_index=True)
    fact = fact.sort_values(["store_id", "product_id", "date"]).reset_index(drop=True)
    fact["data_version"] = data_version

    # 列顺序
    cols = [
        "date", "store_id", "product_id", "category",
        "opening_inventory", "units_sold", "units_ordered",
        "closing_inventory", "is_observed", "data_version",
    ]
    return fact[cols]


def build_dim_tables(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """构建门店与商品维度表。"""
    raw_df = raw_df.copy()
    raw_df["date"] = pd.to_datetime(raw_df["date"])
    latest = raw_df.sort_values("date").groupby(["store_id", "product_id"]).last().reset_index()

    dim_store = raw_df.groupby("store_id").agg(
        region=("region", "first"),
    ).reset_index()
    dim_store["store_name"] = "门店 " + dim_store["store_id"]
    dim_store["is_active"] = True
    dim_store = dim_store[["store_id", "store_name", "region", "is_active"]]

    dim_product = latest.groupby("product_id").agg(
        category=("category", "first"),
        price=("price", "last"),
    ).reset_index()
    dim_product["is_active"] = True
    dim_product = dim_product[["product_id", "category", "price", "is_active"]]

    return dim_store, dim_product
