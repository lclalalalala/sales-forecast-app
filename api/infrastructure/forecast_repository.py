"""
预测预计算表仓储 - forecast_repository.py
==========================================

读取离线批处理产出的 fact_forecast.csv 与 fact_forecast_error_stats.csv，
为在线 API 提供只读查询能力。
"""

import os
from typing import List, Optional

import pandas as pd

from schemas.forecast import (
    ForecastOutput,
    ForecastPoint,
    PredictionInterval,
)
from infrastructure.utils import default_data_dir, normalize_date


class ForecastRepository:
    """预计算销量预测表仓储。"""

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._forecast_path = os.path.join(data_dir, "fact_forecast.csv")
        self._error_stats_path = os.path.join(data_dir, "fact_forecast_error_stats.csv")
        self._forecast_df: Optional[pd.DataFrame] = None
        self._error_stats_df: Optional[pd.DataFrame] = None
        self._load()

    def _load(self) -> None:
        """加载预计算表。"""
        if os.path.exists(self._forecast_path):
            self._forecast_df = pd.read_csv(self._forecast_path)
            self._forecast_df["forecast_origin_date"] = pd.to_datetime(
                self._forecast_df["forecast_origin_date"]
            ).dt.strftime("%Y-%m-%d")
            self._forecast_df["forecast_date"] = pd.to_datetime(
                self._forecast_df["forecast_date"]
            ).dt.strftime("%Y-%m-%d")
        else:
            self._forecast_df = pd.DataFrame()

        if os.path.exists(self._error_stats_path):
            self._error_stats_df = pd.read_csv(self._error_stats_path)
            self._error_stats_df["as_of_date"] = pd.to_datetime(
                self._error_stats_df["as_of_date"]
            ).dt.strftime("%Y-%m-%d")
        else:
            self._error_stats_df = pd.DataFrame()

    def get_forecast(
        self,
        store_id: str,
        product_id: str,
        origin_date,
    ) -> Optional[ForecastOutput]:
        """
        读取指定 (store_id, product_id, origin_date) 的 7 天预计算预测。

        Returns:
            ForecastOutput 或 None（无预计算数据时）。
        """
        if self._forecast_df is None or self._forecast_df.empty:
            return None

        origin = normalize_date(origin_date)
        mask = (
            (self._forecast_df["store_id"] == store_id)
            & (self._forecast_df["product_id"] == product_id)
            & (self._forecast_df["forecast_origin_date"] == origin)
        )
        subset = self._forecast_df[mask].sort_values("forecast_date")
        if subset.empty:
            return None

        daily: List[ForecastPoint] = []
        intervals: List[PredictionInterval] = []
        for _, row in subset.iterrows():
            date_str = row["forecast_date"]
            daily.append(ForecastPoint(date=date_str, units_sold=float(row["forecast_units_sold"])))
            intervals.append(
                PredictionInterval(
                    date=date_str,
                    lower=float(row["lower_bound"]),
                    upper=float(row["upper_bound"]),
                )
            )

        status_values = subset["status"].unique()
        status = "ready" if all(s == "ready" for s in status_values) else "insufficient_data"

        return ForecastOutput(
            status=status,
            message=None,
            daily_forecast=daily,
            prediction_interval=intervals,
        )



# 模块级单例
forecast_repository = ForecastRepository(default_data_dir())
