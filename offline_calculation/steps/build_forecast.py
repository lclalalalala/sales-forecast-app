"""
构建销量预测表 - offline_calculation/steps/build_forecast.py
===========================================================

调用 forecast.batch 生成 walk-forward 7 天预测，
并使用 horizon=3 / 30 天窗口重新计算预测区间，以符合 project_docs/03-Offline-data-process.md。
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

# 允许从项目根目录导入 forecast 包
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from forecast.batch import run as forecast_batch_run


def build_forecast(
    fact: pd.DataFrame,
    as_of_date: datetime,
    model_version: str,
    error_horizon: int = 3,
    error_window_days: int = 30,
    forecast_window_days: int = 33,
    z_score: float = 1.96,
) -> pd.DataFrame:
    """
    生成 fact_forecast.csv。

    Args:
        fact: fact_daily_inventory_sales DataFrame
        as_of_date: demo 基准日期
        model_version: 模型版本
        error_window_days: 预测区间 std 滚动窗口天数
        forecast_window_days: 预测 origin date 窗口天数
        z_score: 预测区间 z 分数

    Returns:
        forecast_df DataFrame
    """
    forecast_df, _ = forecast_batch_run(
        fact=fact,
        demo_as_of_date=as_of_date,
        model_version=model_version,
        forecast_window_days=forecast_window_days,
    )

    if forecast_df.empty:
        return forecast_df

    # 使用配置的 error_horizon 和 error_window_days 重新计算预测区间
    error_std_df = _compute_error_std_by_origin(
        forecast_df, error_window_days, error_horizon
    )
    forecast_df = forecast_df.drop(columns=["lower_bound", "upper_bound"], errors="ignore")
    forecast_df = forecast_df.merge(
        error_std_df,
        on=["store_id", "product_id", "forecast_origin_date"],
        how="left",
    )
    forecast_df["error_std"] = forecast_df["error_std"].fillna(1.0)
    forecast_df["lower_bound"] = (
        forecast_df["forecast_units_sold"] - z_score * forecast_df["error_std"]
    ).clip(lower=0)
    forecast_df["upper_bound"] = forecast_df["forecast_units_sold"] + z_score * forecast_df["error_std"]

    cols = [
        "forecast_origin_date", "forecast_date", "store_id", "product_id",
        "forecast_units_sold", "lower_bound", "upper_bound",
        "actual_units_sold", "forecast_error", "status",
        "model_version", "calculated_at",
    ]
    return forecast_df[cols]


def _compute_error_std_by_origin(
    forecast_df: pd.DataFrame,
    error_window_days: int,
    error_horizon: int,
    default_sigma: float = 1.0,
) -> pd.DataFrame:
    """
    对每个 (store, product, origin_date)，使用固定 horizon=3 的有效误差
    在 error_window_days 窗口内计算样本标准差。
    """
    df = forecast_df.copy()
    df["origin_dt"] = pd.to_datetime(df["forecast_origin_date"])
    df["forecast_dt"] = pd.to_datetime(df["forecast_date"])
    df["horizon"] = (df["forecast_dt"] - df["origin_dt"]).dt.days
    horizon_df = df[(df["horizon"] == error_horizon) & (df["forecast_error"].notna())].copy()

    rows: List[Dict] = []
    for (store_id, product_id), group in horizon_df.groupby(["store_id", "product_id"]):
        group = group.sort_values("origin_dt").reset_index(drop=True)
        for origin_dt in group["origin_dt"].unique():
            window_start = origin_dt - timedelta(days=error_window_days - 1)
            window_errors = group[
                (group["origin_dt"] >= window_start)
                & (group["origin_dt"] <= origin_dt)
            ]["forecast_error"].astype(float)

            if len(window_errors) < 2:
                sigma = default_sigma
            else:
                sigma = float(window_errors.std(ddof=1))

            rows.append({
                "store_id": store_id,
                "product_id": product_id,
                "forecast_origin_date": origin_dt.strftime("%Y-%m-%d"),
                "error_std": sigma,
            })

    return pd.DataFrame(rows)
