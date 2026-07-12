"""
构建门店类别销售汇总 - offline_calculation/steps/build_sales_metrics.py
======================================================================

生成 fact_daily_sales_metrics：按门店、日期、类别汇总销量。
"""

import pandas as pd


def build_daily_sales_metrics(
    fact: pd.DataFrame,
    data_version: str = "v1",
) -> pd.DataFrame:
    """生成 fact_daily_sales_metrics.csv。"""
    fact = fact.copy()
    fact["date"] = pd.to_datetime(fact["date"])

    # 按 store, date, category 聚合
    category_metrics = fact.groupby(["store_id", "date", "category"]).agg(
        total_units_sold=("units_sold", "sum"),
        active_product_count=("units_sold", lambda x: int((x > 0).sum())),
    ).reset_index()

    # 按 store, date 汇总 all
    all_metrics = fact.groupby(["store_id", "date"]).agg(
        total_units_sold=("units_sold", "sum"),
        active_product_count=("units_sold", lambda x: int((x > 0).sum())),
    ).reset_index()
    all_metrics["category"] = "all"

    metrics = pd.concat([category_metrics, all_metrics], ignore_index=True)
    metrics["data_version"] = data_version
    metrics = metrics.sort_values(["store_id", "date", "category"]).reset_index(drop=True)

    return metrics[["store_id", "date", "category", "total_units_sold", "active_product_count", "data_version"]]
