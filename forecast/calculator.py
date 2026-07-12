"""
集成销量预测算法 - forecast/calculator.py
=========================================

不依赖 Web 层或数据层的纯预测算法。
输入输出遵循 forecast/schemas.py 定义的契约。

算法：近期均值 + 星期模式 + 趋势因子 + 季节因子 的加权集成。
"""

from datetime import date, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd

from forecast.schemas import (
    ForecastInput,
    ForecastOutput,
    ForecastPoint,
    PredictionInterval,
)
from forecast.utils import to_dataframe


class EnsembleForecastCalculator:
    """集成预测计算器。"""

    # 算法常量（沿用原 forecast_service / forecast_adapter 的参数）
    RECENT_DAYS = 14
    TREND_CLIP_MIN = 0.7
    TREND_CLIP_MAX = 1.3
    RECENT_WEIGHT = 0.3
    DOW_WEIGHT = 0.4
    TREND_WEIGHT = 0.7
    SEASONAL_WEIGHT = 0.3
    MIN_HISTORY_DAYS = 7

    # 降级响应常量
    FALLBACK_CONSERVATIVE_DEFAULT = 10.0
    FALLBACK_CONSERVATIVE_MIN = 5.0
    FALLBACK_CONSERVATIVE_RATIO = 0.8

    def predict(self, input_data: ForecastInput) -> ForecastOutput:
        """
        基于历史销量预测未来 horizon_days 天每日销量。

        Args:
            input_data: 包含历史数据、预测起始日期、预测 horizon 的 ForecastInput。

        Returns:
            ForecastOutput，包含每日预测值、预测区间、状态与消息。
        """
        historical_data = input_data.historical_data
        forecast_start_date = input_data.forecast_start_date
        horizon_days = input_data.horizon_days
        sigma = input_data.sigma

        if not historical_data or len(historical_data) < self.MIN_HISTORY_DAYS:
            return self._fallback_response(historical_data, forecast_start_date, horizon_days)

        df = to_dataframe(historical_data)
        predictions: List[float] = []
        for i in range(horizon_days):
            pred = self._predict_single_day(df, i)
            predictions.append(pred)

        if sigma is None:
            sigma = self._estimate_sigma(historical_data)

        daily: List[ForecastPoint] = []
        intervals: List[PredictionInterval] = []
        current_date = forecast_start_date
        for pred in predictions:
            date_str = current_date.strftime("%Y-%m-%d")
            daily.append(ForecastPoint(date=date_str, units_sold=round(pred, 1)))

            if sigma is not None and sigma > 0:
                lower = max(0.0, pred - 1.96 * sigma)
                upper = pred + 1.96 * sigma
            else:
                lower = 0.0
                upper = pred

            intervals.append(
                PredictionInterval(
                    date=date_str,
                    lower=round(lower, 1),
                    upper=round(upper, 1),
                )
            )
            current_date += timedelta(days=1)

        return ForecastOutput(
            status="ready",
            message=None,
            daily_forecast=daily,
            prediction_interval=intervals,
        )

    def predict_single_day(self, df: pd.DataFrame, target_date) -> float:
        """
        公共接口：对已准备好的 DataFrame 预测指定目标日期的销量。

        Args:
            df: 内部 DataFrame，包含 datetime / units_sold / dayofweek / month 列。
            target_date: 目标日期（pd.Timestamp 或 date）。

        Returns:
            预测值（非负）。
        """
        target_ts = pd.Timestamp(target_date)
        return self._predict_single_day_for_date(df, target_ts)

    def predict_points(
        self,
        df: pd.DataFrame,
        target_dates: List[pd.Timestamp],
    ) -> List[float]:
        """
        对已经准备好的内部 DataFrame 批量预测多个目标日期。

        Args:
            df: 内部 DataFrame，包含 datetime / units_sold / dayofweek / month 列。
            target_dates: 目标日期列表。

        Returns:
            每个目标日期的预测值列表。
        """
        return [self._predict_single_day_for_date(df, d) for d in target_dates]

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _predict_single_day(self, df: pd.DataFrame, day_offset: int) -> float:
        """预测未来第 day_offset 天（0=forecast_start_date）。"""
        last_date = df["datetime"].iloc[-1]
        target_date = last_date + timedelta(days=day_offset + 1)
        return self._predict_single_day_for_date(df, target_date)

    def _predict_single_day_for_date(self, df: pd.DataFrame, target_date: pd.Timestamp) -> float:
        """预测指定目标日期的销量。"""
        values = df["units_sold"].values.astype(float)

        recent_avg = (
            np.mean(values[-self.RECENT_DAYS:])
            if len(values) >= self.RECENT_DAYS
            else np.mean(values)
        )

        target_dow = target_date.weekday()
        target_month = target_date.month

        if "dayofweek" in df.columns:
            dow_mask = df["dayofweek"] == target_dow
            if dow_mask.sum() >= 4:
                dow_avg = df[dow_mask]["units_sold"].tail(8).mean()
            else:
                dow_avg = recent_avg
        else:
            dow_avg = recent_avg

        trend_factor = self._calculate_trend_factor(values)
        seasonal_factor = self._calculate_seasonal_factor(df, target_month, recent_avg)

        main_term = (
            recent_avg * self.RECENT_WEIGHT + dow_avg * self.DOW_WEIGHT
        ) * trend_factor * self.TREND_WEIGHT
        remainder_term = recent_avg * self.SEASONAL_WEIGHT * seasonal_factor
        prediction = main_term + remainder_term

        return float(max(0.0, prediction))

    def _calculate_trend_factor(self, values: np.ndarray) -> float:
        """趋势因子：最近 7 天 / 最近 30 天，限制在 [0.7, 1.3]。"""
        if len(values) < 30:
            return 1.0

        last_7_avg = np.mean(values[-7:])
        last_30_avg = np.mean(values[-30:])
        if last_30_avg <= 0:
            return 1.0

        trend = last_7_avg / last_30_avg
        return float(np.clip(trend, self.TREND_CLIP_MIN, self.TREND_CLIP_MAX))

    def _calculate_seasonal_factor(
        self, df: pd.DataFrame, target_month: int, recent_avg: float
    ) -> float:
        """季节因子：目标月份历史均值 / 近期均值，限制在 [0.7, 1.3]。"""
        if "month" not in df.columns or recent_avg <= 0:
            return 1.0

        month_mask = df["month"] == target_month
        if month_mask.sum() == 0:
            return 1.0

        month_avg = df[month_mask]["units_sold"].mean()
        seasonal = month_avg / recent_avg
        return float(np.clip(seasonal, self.TREND_CLIP_MIN, self.TREND_CLIP_MAX))

    def _fallback_response(
        self,
        historical_data: List,
        forecast_start_date: date,
        horizon_days: int,
    ) -> ForecastOutput:
        """数据不足时的降级响应。"""
        if historical_data:
            avg = np.mean([h.units_sold for h in historical_data])
            conservative = max(
                self.FALLBACK_CONSERVATIVE_MIN,
                avg * self.FALLBACK_CONSERVATIVE_RATIO,
            )
        else:
            conservative = self.FALLBACK_CONSERVATIVE_DEFAULT

        daily: List[ForecastPoint] = []
        intervals: List[PredictionInterval] = []
        current_date = forecast_start_date
        for _ in range(horizon_days):
            date_str = current_date.strftime("%Y-%m-%d")
            daily.append(ForecastPoint(date=date_str, units_sold=round(conservative, 1)))
            intervals.append(
                PredictionInterval(date=date_str, lower=0.0, upper=round(conservative, 1))
            )
            current_date += timedelta(days=1)

        status = "insufficient_data"
        message = "历史数据不足，使用保守估计"
        return ForecastOutput(
            status=status,
            message=message,
            daily_forecast=daily,
            prediction_interval=intervals,
        )

    def _estimate_sigma(self, historical_data: List) -> Optional[float]:
        """基于历史数据估计预测误差标准差（内部辅助，非公共误差计算接口）。"""
        from forecast.errors import ForecastErrorCalculator

        error_output = ForecastErrorCalculator.compute_errors(historical_data)
        return error_output.sigma
