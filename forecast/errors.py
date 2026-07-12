"""
滚动预测误差计算 - forecast/errors.py
======================================

提供与具体预测算法解耦的滚动单步误差计算，用于离线批处理生成
fact_forecast_error_stats.csv 的 sigma。
"""

from typing import List, Optional

import numpy as np

from forecast.schemas import HistoricalDataPoint, ForecastErrorOutput
from forecast.calculator import EnsembleForecastCalculator
from forecast.utils import to_dataframe


class ForecastErrorCalculator:
    """滚动预测误差计算器。"""

    MIN_HISTORY_DAYS = EnsembleForecastCalculator.MIN_HISTORY_DAYS

    @classmethod
    def compute_errors(cls, historical_data: List[HistoricalDataPoint]) -> ForecastErrorOutput:
        """
        对每个至少有 MIN_HISTORY_DAYS 天历史的日期，用之前全部历史预测当天销量，
        返回 (实际 - 预测) 的误差序列与样本标准差。

        Args:
            historical_data: 按日期排序的历史销量数据点列表。

        Returns:
            ForecastErrorOutput，包含 errors 列表与 sigma（样本标准差，ddof=1）。
                当历史不足或有效误差少于 2 个时，sigma 为 None。
        """
        if not historical_data or len(historical_data) < cls.MIN_HISTORY_DAYS + 1:
            return ForecastErrorOutput(errors=[], sigma=None)

        df = to_dataframe(historical_data)
        calculator = EnsembleForecastCalculator()

        errors: List[float] = []
        for i in range(cls.MIN_HISTORY_DAYS, len(df)):
            train_df = df.iloc[:i]
            target_row = df.iloc[i]
            target_date = target_row["datetime"]

            pred = calculator.predict_single_day(train_df, target_date)
            actual = float(target_row["units_sold"])
            errors.append(actual - pred)

        sigma = cls._compute_sigma(errors)
        return ForecastErrorOutput(errors=errors, sigma=sigma)

    @staticmethod
    def _compute_sigma(errors: List[float]) -> Optional[float]:
        """计算样本标准差，有效误差少于 2 个时返回 None。"""
        if len(errors) < 2:
            return None
        return float(np.std(errors, ddof=1))
