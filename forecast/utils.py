"""
预测模块共享工具 - forecast/utils.py
====================================

calculator / errors / batch 共用的 DataFrame 构造与误差计算工具。
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from forecast.schemas import HistoricalDataPoint


# 误差计算默认 sigma（有效误差不足时的 fallback）
DEFAULT_ERROR_SIGMA: float = 1.0


def to_dataframe(historical_data: List[HistoricalDataPoint]) -> pd.DataFrame:
    """
    将历史数据点列表转换为内部 DataFrame。

    Returns:
        包含 date / datetime / units_sold / dayofweek / month 列，按日期升序排列。
    """
    rows = [
        {
            "date": h.date,
            "datetime": pd.Timestamp(h.date),
            "units_sold": h.units_sold,
            "dayofweek": h.dayofweek,
            "month": h.month,
        }
        for h in historical_data
    ]
    df = pd.DataFrame(rows)
    return df.sort_values("datetime").reset_index(drop=True)


def compute_error_std_by_origin(
    forecast_df: pd.DataFrame,
    error_window_days: int,
    horizon: Optional[int] = None,
) -> pd.DataFrame:
    """
    对每个 (store, product, origin_date)，在 error_window_days 滚动窗口内
    使用有效 forecast_error 计算样本标准差。

    有效误差少于 2 个时，fallback 为 DEFAULT_ERROR_SIGMA。

    Args:
        forecast_df: 必须包含 store_id, product_id, forecast_origin_date,
                     forecast_error 列；当指定 horizon 时还需 forecast_date 列
        error_window_days: 滚动窗口天数
        horizon: 若指定，仅使用 forecast_date - forecast_origin_date == horizon
                 的误差（离线安全库存/预测区间按固定 horizon 计算）；默认 None
                 表示使用窗口内全部有效误差。

    Returns:
        DataFrame，列: store_id, product_id, forecast_origin_date, error_std
    """
    result_rows: List[Dict[str, Any]] = []

    df = forecast_df.copy()
    df["origin_dt"] = pd.to_datetime(df["forecast_origin_date"])
    error_df = df[df["forecast_error"].notna()].copy()
    if horizon is not None:
        error_df["forecast_dt"] = pd.to_datetime(error_df["forecast_date"])
        error_df = error_df[
            (error_df["forecast_dt"] - error_df["origin_dt"]).dt.days == horizon
        ]

    for (store_id, product_id), group in df.groupby(["store_id", "product_id"]):
        group = group.sort_values("origin_dt").reset_index(drop=True)
        error_group = error_df[
            (error_df["store_id"] == store_id) & (error_df["product_id"] == product_id)
        ].copy()

        for origin_dt in group["origin_dt"].unique():
            window_start = origin_dt - pd.Timedelta(days=error_window_days - 1)
            window_errors = error_group[
                (error_group["origin_dt"] >= window_start)
                & (error_group["origin_dt"] <= origin_dt)
            ]["forecast_error"].astype(float)

            if len(window_errors) < 2:
                sigma = DEFAULT_ERROR_SIGMA
            else:
                sigma = float(window_errors.std(ddof=1))

            result_rows.append({
                "store_id": store_id,
                "product_id": product_id,
                "forecast_origin_date": origin_dt.strftime("%Y-%m-%d"),
                "error_std": sigma,
            })

    return pd.DataFrame(result_rows)
