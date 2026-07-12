"""
离线计算流程编排 - offline_calculation/pipeline.py
=================================================

按 project_docs/03-Offline-data-process.md 的 8 步流程编排离线批处理。
"""

import os
from datetime import datetime
from typing import Optional

import pandas as pd

from offline_calculation.config import (
    DATA_VERSION,
    MODEL_VERSION,
    OfflineConfig,
    OUTPUT_DIR,
    RAW_DATA_PATH,
)
from offline_calculation.steps.build_error_stats import build_error_stats
from offline_calculation.steps.build_fact import build_dim_tables, build_fact_daily_inventory_sales
from offline_calculation.steps.build_forecast import build_forecast
from offline_calculation.steps.build_product_summary import build_product_sales_summary
from offline_calculation.steps.build_replenishment import build_daily_replenishment
from offline_calculation.steps.build_sales_metrics import build_daily_sales_metrics
from offline_calculation.steps.estimate_lead_time import estimate_lead_time
from offline_calculation.steps.load_validate import load_and_validate


def run_pipeline(
    raw_path: str = RAW_DATA_PATH,
    output_dir: str = OUTPUT_DIR,
    config: Optional[OfflineConfig] = None,
    as_of_date: Optional[datetime] = None,
) -> None:
    """
    执行完整离线计算流程。

    Args:
        raw_path: 原始 sales_data.csv 路径
        output_dir: 输出目录
        config: 业务配置
        as_of_date: 计算基准日期，默认 max(date) - 7 days
    """
    calculated_at = datetime.now()
    if config is None:
        config = OfflineConfig.from_file()

    os.makedirs(output_dir, exist_ok=True)

    print("[1/8] 加载并校验原始数据 ...")
    raw_df, _ = load_and_validate(raw_path, output_dir)

    print("[2/8] 构建标准化事实表 ...")
    fact = build_fact_daily_inventory_sales(raw_df, data_version=DATA_VERSION)

    print("[3/8] 构建维度表 ...")
    dim_store, dim_product = build_dim_tables(raw_df)

    print("[4/8] 估计提前期 K ...")
    lead_time_df = estimate_lead_time(
        fact,
        config=config,
        calculated_at=calculated_at,
        config_version=DATA_VERSION,
    )

    print("[5/8] 生成 walk-forward 预测 ...")
    max_date = fact["date"].max()
    if as_of_date is None:
        offset_days = config.offline_as_of_date_offset_days
        as_of_date = max_date - pd.Timedelta(days=offset_days)

    forecast_df = build_forecast(
        fact,
        as_of_date=as_of_date,
        model_version=MODEL_VERSION,
        error_horizon=config.forecast_error_horizon,
        error_window_days=config.forecast_error_window_days,
        forecast_window_days=config.forecast_window_days,
    )

    print("[6/8] 生成预测误差统计 ...")
    error_stats_df = build_error_stats(
        forecast_df,
        config=config,
        model_version=MODEL_VERSION,
        calculated_at=calculated_at,
    )

    print("[7/8] 计算每日补货推荐 ...")
    replenishment_df = build_daily_replenishment(
        fact,
        lead_time_df,
        forecast_df,
        error_stats_df,
        config=config,
        as_of_date=as_of_date,
        data_version=DATA_VERSION,
        model_version=MODEL_VERSION,
        calculated_at=calculated_at,
    )

    print("[8/8] 生成销售汇总表 ...")
    sales_metrics_df = build_daily_sales_metrics(fact, data_version=DATA_VERSION)
    product_summary_df = build_product_sales_summary(
        fact,
        replenishment_df,
        as_of_date=as_of_date,
        config=config,
        data_version=DATA_VERSION,
    )

    print("写入输出文件 ...")
    _write_csv(dim_store, output_dir, "dim_store.csv")
    _write_csv(dim_product, output_dir, "dim_product.csv")
    _write_csv(fact, output_dir, "fact_daily_inventory_sales.csv")
    _write_csv(lead_time_df, output_dir, "fact_lead_time.csv")
    _write_csv(forecast_df, output_dir, "fact_forecast.csv")
    _write_csv(error_stats_df, output_dir, "fact_forecast_error_stats.csv")
    _write_csv(replenishment_df, output_dir, "fact_daily_replenishment.csv")
    _write_csv(sales_metrics_df, output_dir, "fact_daily_sales_metrics.csv")
    _write_csv(product_summary_df, output_dir, "fact_product_sales_summary.csv")

    print(f"离线计算完成，输出目录: {output_dir}")


def _write_csv(df: pd.DataFrame, output_dir: str, filename: str) -> None:
    """写入 CSV 文件，日期列格式化为 YYYY-MM-DD。"""
    path = os.path.join(output_dir, filename)
    out_df = df.copy()
    for col in out_df.columns:
        if pd.api.types.is_datetime64_any_dtype(out_df[col]):
            out_df[col] = out_df[col].dt.strftime("%Y-%m-%d")
    out_df.to_csv(path, index=False)
    print(f"  - {filename}: {len(df)} 行")
