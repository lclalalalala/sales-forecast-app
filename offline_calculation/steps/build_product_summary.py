"""
构建商品销售汇总 - offline_calculation/steps/build_product_summary.py
====================================================================

生成 fact_product_sales_summary：预计算 7d/30d/90d/180d/all 窗口的销量排名基础数据。
"""

from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from offline_calculation.config import OfflineConfig


WINDOW_LABELS = ["7d", "30d", "90d", "180d", "all"]


def build_product_sales_summary(
    fact: pd.DataFrame,
    replenishment_df: pd.DataFrame,
    as_of_date: datetime,
    config: OfflineConfig,
    data_version: str = "v1",
) -> pd.DataFrame:
    """生成 fact_product_sales_summary.csv。"""
    fact = fact.copy()
    fact["date"] = pd.to_datetime(fact["date"])
    as_of_dt = pd.Timestamp(as_of_date)

    # 获取每个 (store, product) 在 as_of_date 的最新补货记录
    repl = replenishment_df.copy()
    repl["as_of_dt"] = pd.to_datetime(repl["as_of_date"])
    latest_repl = repl[repl["as_of_dt"] == as_of_dt].copy()
    repl_map = {}
    if not latest_repl.empty:
        for _, row in latest_repl.iterrows():
            repl_map[(row["store_id"], row["product_id"])] = {
                "current_inventory": int(row["current_inventory"]),
                "in_transit_inventory": int(row["in_transit_inventory"]),
                "inventory_status": row["inventory_status"],
            }

    rows: List[Dict] = []
    for (store_id, product_id), group in fact.groupby(["store_id", "product_id"]):
        category = group["category"].iloc[0]

        for label in WINDOW_LABELS:
            if label == "all":
                window_start = group["date"].min()
            else:
                days = int(label[:-1])
                window_start = as_of_dt - timedelta(days=days - 1)

            window_group = group[
                (group["date"] >= window_start) & (group["date"] <= as_of_dt)
            ]
            total_sold = int(window_group["units_sold"].sum())
            days_span = max(1, (window_group["date"].max() - window_group["date"].min()).days + 1)
            avg_daily = total_sold / days_span

            repl_info = repl_map.get((store_id, product_id), {
                "current_inventory": 0,
                "in_transit_inventory": 0,
                "inventory_status": "undetermined",
            })

            rows.append({
                "window_start": window_start.strftime("%Y-%m-%d"),
                "window_end": as_of_dt.strftime("%Y-%m-%d"),
                "window_label": label,
                "store_id": store_id,
                "product_id": product_id,
                "category": category,
                "total_units_sold": total_sold,
                "avg_daily_units_sold": round(avg_daily, 2),
                "current_inventory": repl_info["current_inventory"],
                "in_transit_inventory": repl_info["in_transit_inventory"],
                "inventory_status": repl_info["inventory_status"],
                "data_version": data_version,
            })

    return pd.DataFrame(rows)
