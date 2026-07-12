"""
构建预测误差统计表 - offline_calculation/steps/build_error_stats.py
=================================================================

基于 fact_forecast 中 horizon=3 的有效误差，滚动 30 天窗口计算 sigma。
"""

from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from offline_calculation.config import OfflineConfig


def build_error_stats(
    forecast_df: pd.DataFrame,
    config: OfflineConfig,
    model_version: str,
    calculated_at: datetime,
) -> pd.DataFrame:
    """
    生成 fact_forecast_error_stats.csv。

    仅使用 forecast_date - forecast_origin_date == error_horizon 的有效误差。
    """
    if forecast_df.empty:
        return pd.DataFrame(columns=[
            "as_of_date", "store_id", "product_id", "horizon", "window_days",
            "error_std", "valid_error_count", "std_source", "model_version", "calculated_at",
        ])

    error_horizon = config.forecast_error_horizon
    error_window_days = config.forecast_error_window_days
    insufficient_std = config.safety_stock_insufficient_std
    min_count = 2

    df = forecast_df.copy()
    df["origin_dt"] = pd.to_datetime(df["forecast_origin_date"])
    df["forecast_dt"] = pd.to_datetime(df["forecast_date"])
    df["horizon"] = (df["forecast_dt"] - df["origin_dt"]).dt.days

    # 只保留目标 horizon 的有效误差
    horizon_df = df[
        (df["horizon"] == error_horizon) & (df["forecast_error"].notna())
    ].copy()

    rows: List[Dict] = []
    for (store_id, product_id), group in horizon_df.groupby(["store_id", "product_id"]):
        group = group.sort_values("origin_dt").reset_index(drop=True)

        for origin_dt in group["origin_dt"].unique():
            window_start = origin_dt - timedelta(days=error_window_days - 1)
            window_errors = group[
                (group["origin_dt"] >= window_start)
                & (group["origin_dt"] <= origin_dt)
            ]["forecast_error"].astype(float)

            valid_count = int(len(window_errors))
            if valid_count < min_count:
                sigma = insufficient_std
                source = "fallback_1"
            else:
                sigma = float(window_errors.std(ddof=1))
                source = "calculated"

            rows.append({
                "as_of_date": origin_dt.strftime("%Y-%m-%d"),
                "store_id": store_id,
                "product_id": product_id,
                "horizon": error_horizon,
                "window_days": error_window_days,
                "error_std": sigma,
                "valid_error_count": valid_count,
                "std_source": source,
                "model_version": model_version,
                "calculated_at": calculated_at.isoformat(),
            })

    return pd.DataFrame(rows)
