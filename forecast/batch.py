"""
离线销量预测批处理 - forecast/batch.py
=========================================

为所有 (store_id, product_id) 组合批量生成未来 7 天销量预测，
并输出符合 fact_forecast.csv / fact_forecast_error_stats.csv 的 DataFrame。

该模块属于 forecast 包，只依赖包内纯算法（calculator / schemas / utils），
不依赖 Flask 或在线服务，可被 offline_calculation 与 mock_data 直接调用。
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import pandas as pd
import yaml

# 允许从项目根目录导入 forecast 包内其它模块
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from forecast.calculator import EnsembleForecastCalculator
from forecast.utils import compute_error_std_by_origin, DEFAULT_ERROR_SIGMA

# 从 config/business.yaml 读取业务配置
_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "business.yaml")


def _load_config() -> Dict[str, Any]:
    """加载 YAML 配置文件。"""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_config = _load_config()

# 配置驱动的默认值（替代硬编码常量）
HISTORY_WINDOW_DAYS = int(_config.get("default", {}).get("time_range_days", 90))
FORECAST_HORIZON_DAYS = int(_config.get("default", {}).get("forecast_horizon_days", 7))
ERROR_WINDOW_DAYS = int(_config.get("forecast", {}).get("error_window_days", 30))
FORECAST_WINDOW_DAYS = int(_config.get("forecast", {}).get("forecast_window_days", 33))

# 预测区间 z 分数（95% 置信区间，非业务配置）
Z_95 = 1.96

# 组合参与预测所需的最少历史天数。取 7 天，与计算器 MIN_HISTORY_DAYS 一致，
# 保证新上市 SKU 也能尽早获得预测支持。
MIN_INITIAL_HISTORY_DAYS = 7


def _process_group(args: Tuple) -> List[Dict[str, Any]]:
    """处理单个 (store, product) 组合的预测，供 ProcessPoolExecutor 调用。"""
    store_id, product_id, group_df, demo_as_of_date, model_version, max_date, now_iso, forecast_window_days = args

    group = group_df.sort_values("date").reset_index(drop=True)
    if len(group) < MIN_INITIAL_HISTORY_DAYS:
        return []

    calculator = EnsembleForecastCalculator()

    full_history_df = pd.DataFrame({
        "date": group["date"].dt.date,
        "datetime": pd.to_datetime(group["date"]),
        "units_sold": group["units_sold"].astype(float),
        "dayofweek": group["date"].dt.weekday,
        "month": group["date"].dt.month,
    })

    # 构造实际值索引，用于快速查找
    actual_lookup = {}
    for idx in range(len(group)):
        d = group.loc[idx, "date"]
        for h in range(1, FORECAST_HORIZON_DAYS + 1):
            forecast_date = d + timedelta(days=h)
            actual_lookup[(store_id, product_id, forecast_date)] = int(group.loc[idx, "units_sold"])

    # 只处理最近 forecast_window_days 天的 origin_date
    window_start = demo_as_of_date - timedelta(days=forecast_window_days)

    rows: List[Dict[str, Any]] = []
    for i in range(MIN_INITIAL_HISTORY_DAYS - 1, len(group)):
        origin_date = group.loc[i, "date"]
        if origin_date > demo_as_of_date or origin_date < window_start:
            continue

        history_start_idx = max(0, i - HISTORY_WINDOW_DAYS + 1)
        train_df = full_history_df.iloc[history_start_idx : i + 1].reset_index(drop=True)

        target_dates = [origin_date + timedelta(days=h) for h in range(1, FORECAST_HORIZON_DAYS + 1)]
        target_timestamps = [pd.Timestamp(d) for d in target_dates]
        predictions = calculator.predict_points(train_df, target_timestamps)

        for forecast_date, pred in zip(target_dates, predictions):
            key = (store_id, product_id, forecast_date)
            if forecast_date <= max_date and key in actual_lookup:
                actual_units_sold = actual_lookup[key]
                forecast_error = actual_units_sold - pred
            else:
                actual_units_sold = None
                forecast_error = None

            rows.append({
                "forecast_origin_date": origin_date.strftime("%Y-%m-%d"),
                "forecast_date": forecast_date.strftime("%Y-%m-%d"),
                "store_id": store_id,
                "product_id": product_id,
                "forecast_units_sold": round(pred, 1),
                "actual_units_sold": actual_units_sold,
                "forecast_error": forecast_error,
                "status": "ready",
                "model_version": model_version,
                "calculated_at": now_iso,
            })

    return rows


def run(
    fact: pd.DataFrame,
    demo_as_of_date: datetime,
    model_version: str,
    error_window_days: int = ERROR_WINDOW_DAYS,
    z_score: float = Z_95,
    forecast_window_days: int = FORECAST_WINDOW_DAYS,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    批量生成预测表与误差统计表。

    Args:
        fact: 标准化事实表，必须包含
            date, store_id, product_id, units_sold, is_observed
        demo_as_of_date: 本次 demo 的基准日期，只生成 origin_date <= 该日期的预测
        model_version: 模型版本字符串，写入 forecast 与 error_stats
        error_window_days: 误差 std 滚动窗口天数（默认 90）
        z_score: 预测区间 z 分数（默认 1.96）

    Returns:
        (forecast_df, error_stats_df)
    """
    observed = fact[fact["is_observed"]].copy()
    observed_indexed = observed.set_index(["store_id", "product_id", "date"])

    max_date = fact["date"].max()
    now_iso = datetime.now().isoformat()

    groups = list(observed.groupby(["store_id", "product_id"]))
    print(f"  正在为 {len(groups)} 个 (store, product) 组合生成预测 ...")

    # 并行处理每个 (store, product) 组合
    args_list = [
        (store_id, product_id, group_df, demo_as_of_date, model_version, max_date, now_iso, forecast_window_days)
        for (store_id, product_id), group_df in groups
    ]
    forecast_rows: List[Dict[str, Any]] = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(_process_group, a): a[0:2] for a in args_list}
        for future in as_completed(futures):
            forecast_rows.extend(future.result())

    forecast_df = pd.DataFrame(forecast_rows)
    if forecast_df.empty:
        error_stats = pd.DataFrame(columns=[
            "as_of_date", "store_id", "product_id", "window_days", "error_std",
            "valid_error_count", "std_source", "model_version", "calculated_at",
        ])
        return forecast_df, error_stats

    forecast_df = forecast_df.sort_values([
        "store_id", "product_id", "forecast_origin_date", "forecast_date"
    ]).reset_index(drop=True)

    # 计算每个 origin_date 的滚动误差 std，并添加预测区间
    forecast_df = _add_prediction_interval(forecast_df, error_window_days, z_score)

    error_stats = _build_error_stats(forecast_df, model_version, error_window_days)
    return forecast_df, error_stats


def _add_prediction_interval(
    forecast_df: pd.DataFrame,
    error_window_days: int,
    z_score: float,
) -> pd.DataFrame:
    """为每条预测添加 95% 预测区间。"""
    error_std_df = compute_error_std_by_origin(forecast_df, error_window_days)
    forecast_df = forecast_df.merge(
        error_std_df,
        on=["store_id", "product_id", "forecast_origin_date"],
        how="left",
    )
    forecast_df["lower_bound"] = (
        forecast_df["forecast_units_sold"] - z_score * forecast_df["error_std"]
    ).clip(lower=0)
    forecast_df["upper_bound"] = forecast_df["forecast_units_sold"] + z_score * forecast_df["error_std"]

    # 调整列顺序
    cols = [
        "forecast_origin_date", "forecast_date", "store_id", "product_id",
        "forecast_units_sold", "lower_bound", "upper_bound",
        "actual_units_sold", "forecast_error", "status",
        "model_version", "calculated_at",
    ]
    return forecast_df[cols]


def _build_error_stats(
    forecast_df: pd.DataFrame,
    model_version: str,
    error_window_days: int,
) -> pd.DataFrame:
    """基于 fact_forecast 的预测误差生成滚动误差统计表。"""
    # 复用共享的误差 std 计算
    error_std_df = compute_error_std_by_origin(forecast_df, error_window_days)

    # 补充统计信息列
    df = forecast_df.copy()
    df["origin_dt"] = pd.to_datetime(df["forecast_origin_date"])
    error_df = df[df["forecast_error"].notna()].copy()

    rows: List[Dict[str, Any]] = []
    for _, err_row in error_std_df.iterrows():
        store_id = err_row["store_id"]
        product_id = err_row["product_id"]
        origin_dt = pd.to_datetime(err_row["forecast_origin_date"])

        # 计算有效误差数量
        window_start = origin_dt - timedelta(days=error_window_days - 1)
        combo_errors = error_df[
            (error_df["store_id"] == store_id)
            & (error_df["product_id"] == product_id)
        ]
        window_errors = combo_errors[
            (combo_errors["origin_dt"] >= window_start)
            & (combo_errors["origin_dt"] <= origin_dt)
        ]["forecast_error"].astype(float)

        valid_count = int(len(window_errors))
        source = "fallback_1" if valid_count < 2 else "calculated"

        rows.append({
            "as_of_date": err_row["forecast_origin_date"],
            "store_id": store_id,
            "product_id": product_id,
            "window_days": error_window_days,
            "error_std": err_row["error_std"],
            "valid_error_count": valid_count,
            "std_source": source,
            "model_version": model_version,
            "calculated_at": datetime.now().isoformat(),
        })

    return pd.DataFrame(rows)
