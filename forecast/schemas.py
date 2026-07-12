"""
销量预测模块公共契约 - forecast/schemas.py
==========================================

定义离线批处理与在线 API 共享的输入输出数据结构。
所有字段类型均为 Python 原生类型或标准库类型，避免暴露 pandas/numpy 细节。
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class HistoricalDataPoint:
    """单个历史销量数据点。"""

    date: date
    units_sold: float
    dayofweek: Optional[int] = None
    month: Optional[int] = None

    def __post_init__(self):
        if self.dayofweek is None:
            self.dayofweek = self.date.weekday()
        if self.month is None:
            self.month = self.date.month


@dataclass
class ForecastInput:
    """销量预测输入。"""

    historical_data: List[HistoricalDataPoint]
    forecast_start_date: date
    horizon_days: int = 7
    sigma: Optional[float] = None

    def __post_init__(self):
        if self.horizon_days <= 0:
            raise ValueError("horizon_days 必须为正整数")


@dataclass
class ForecastPoint:
    """单日期销量预测值。"""

    date: str  # YYYY-MM-DD
    units_sold: float


@dataclass
class PredictionInterval:
    """单日期预测区间。"""

    date: str  # YYYY-MM-DD
    lower: float
    upper: float


@dataclass
class ForecastOutput:
    """销量预测输出。"""

    status: str  # "ready" | "insufficient_data" | "error"
    message: Optional[str]
    daily_forecast: List[ForecastPoint] = field(default_factory=list)
    prediction_interval: List[PredictionInterval] = field(default_factory=list)


@dataclass
class ForecastErrorOutput:
    """滚动预测误差统计输出。"""

    errors: List[float] = field(default_factory=list)
    sigma: Optional[float] = None
