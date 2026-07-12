"""
预测读模型 - schemas/forecast.py
================================
在线 API 只读消费预计算预测表（fact_forecast.csv）所需的输出结构。

说明：销量预测的算法与训练属于离线独立模块 `forecast/`（由离线批处理调度），
在线 API 不依赖该模块，仅从预计算表读取结果。此处定义 API 层自有的读模型，
避免在线服务在导入期耦合离线 `forecast` 包。
"""

from dataclasses import dataclass, field
from typing import List, Optional


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
    """销量预测输出（读模型）。"""

    status: str  # "ready" | "insufficient_data" | "error"
    message: Optional[str]
    daily_forecast: List[ForecastPoint] = field(default_factory=list)
    prediction_interval: List[PredictionInterval] = field(default_factory=list)
