"""
离线计算输出校验 - offline_calculation/verify_outputs.py
=========================================================

验证 data/processed_data/ 下的输出文件是否存在、schema 是否正确、业务规则是否满足。
"""

import os
import sys

import pandas as pd

from offline_calculation.config import OfflineConfig


def verify(output_dir: str, config: OfflineConfig = None) -> bool:
    """校验离线计算输出。"""
    if config is None:
        config = OfflineConfig.from_file()
    expected_files = [
        "data_quality_report.json",
        "data_quality_report.csv",
        "dim_store.csv",
        "dim_product.csv",
        "fact_daily_inventory_sales.csv",
        "fact_lead_time.csv",
        "fact_forecast.csv",
        "fact_forecast_error_stats.csv",
        "fact_daily_replenishment.csv",
        "fact_daily_sales_metrics.csv",
        "fact_product_sales_summary.csv",
    ]

    all_ok = True
    for filename in expected_files:
        path = os.path.join(output_dir, filename)
        if not os.path.exists(path):
            print(f"[FAIL] 缺失文件: {filename}")
            all_ok = False

    if not all_ok:
        return False

    # 校验 fact_daily_inventory_sales 库存关系
    fact = pd.read_csv(os.path.join(output_dir, "fact_daily_inventory_sales.csv"))
    if not (fact["closing_inventory"] == fact["opening_inventory"] - fact["units_sold"]).all():
        print("[FAIL] fact_daily_inventory_sales closing_inventory 计算错误")
        all_ok = False

    # 校验 fact_lead_time K 范围（从配置读取上下界，避免写死）
    min_k = config.lead_time_min_days
    max_k = config.lead_time_max_days
    lead_time = pd.read_csv(os.path.join(output_dir, "fact_lead_time.csv"))
    if not (
        (lead_time["lead_time_days"] >= min_k) & (lead_time["lead_time_days"] <= max_k)
    ).all():
        print(f"[FAIL] fact_lead_time lead_time_days 超出 [{min_k}, {max_k}] 范围")
        all_ok = False

    # 校验补货推荐非负
    repl = pd.read_csv(os.path.join(output_dir, "fact_daily_replenishment.csv"))
    if not (repl["suggested_replenishment"] >= 0).all():
        print("[FAIL] fact_daily_replenishment suggested_replenishment 存在负值")
        all_ok = False

    # 校验预测区间
    forecast = pd.read_csv(os.path.join(output_dir, "fact_forecast.csv"))
    if not (
        (forecast["lower_bound"] >= 0)
        & (forecast["lower_bound"] <= forecast["forecast_units_sold"])
        & (forecast["forecast_units_sold"] <= forecast["upper_bound"])
    ).all():
        print("[FAIL] fact_forecast 预测区间关系错误")
        all_ok = False

    if all_ok:
        print(f"[PASS] 输出校验通过: {output_dir}")
    return all_ok


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "data/processed_data"
    ok = verify(output_dir)
    sys.exit(0 if ok else 1)
