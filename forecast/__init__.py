"""
销量预测模块 - forecast
======================

与 Web/API 层解耦的纯销量预测模块。

公共入口：
- EnsembleForecastCalculator.predict(input: ForecastInput) -> ForecastOutput
- ForecastErrorCalculator.compute_errors(history) -> ForecastErrorOutput
- schemas: HistoricalDataPoint, ForecastInput, ForecastOutput 等
"""

from forecast.schemas import (
    HistoricalDataPoint,
    ForecastInput,
    ForecastPoint,
    PredictionInterval,
    ForecastOutput,
    ForecastErrorOutput,
)
from forecast.calculator import EnsembleForecastCalculator
from forecast.errors import ForecastErrorCalculator
from forecast.batch import run as run_forecast_batch
from forecast.utils import to_dataframe, compute_error_std_by_origin

__all__ = [
    "HistoricalDataPoint",
    "ForecastInput",
    "ForecastPoint",
    "PredictionInterval",
    "ForecastOutput",
    "ForecastErrorOutput",
    "EnsembleForecastCalculator",
    "ForecastErrorCalculator",
    "run_forecast_batch",
    "to_dataframe",
    "compute_error_std_by_origin",
]
