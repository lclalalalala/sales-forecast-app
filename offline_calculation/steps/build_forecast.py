"""
构建销量预测表 - offline_calculation/steps/build_forecast.py
===========================================================

调用 forecast.batch 生成 walk-forward 7 天预测，
并使用 horizon=3 / 30 天窗口重新计算预测区间，以符合 project_docs/03-Offline-data-process.md。
"""

import os
import sys
from datetime import datetime

import pandas as pd

# 允许从项目根目录导入 forecast 包
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from forecast.batch import run as forecast_batch_run
from forecast.utils import compute_error_std_by_origin


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
    # 复用 forecast.utils 的共享实现（horizon 过滤按固定 error_horizon）
    error_std_df = compute_error_std_by_origin(
        forecast_df, error_window_days, horizon=error_horizon
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
