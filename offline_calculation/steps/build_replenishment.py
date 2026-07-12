"""
构建每日补货推荐表 - offline_calculation/steps/build_replenishment.py
====================================================================

整合在途库存、销量预测、安全库存、库存状态，计算每日补货推荐量。
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from offline_calculation.config import OfflineConfig


def build_daily_replenishment(
    fact: pd.DataFrame,
    lead_time_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    error_stats_df: pd.DataFrame,
    config: OfflineConfig,
    as_of_date: datetime,
    data_version: str,
    model_version: str,
    calculated_at: datetime,
) -> pd.DataFrame:
    """
    生成 fact_daily_replenishment.csv。

    Args:
        fact: fact_daily_inventory_sales DataFrame
        lead_time_df: fact_lead_time DataFrame
        forecast_df: fact_forecast DataFrame
        error_stats_df: fact_forecast_error_stats DataFrame
        config: 离线配置
        as_of_date: demo 基准日期
        data_version: 数据版本
        model_version: 模型版本
        calculated_at: 计算时间

    Returns:
        replenishment DataFrame
    """
    z = config.safety_stock_z
    critical_lt = config.inventory_status_critical_lt
    low_lt = config.inventory_status_low_lt
    normal_lte = config.inventory_status_normal_lte
    basis = config.inventory_status_basis

    # 构建 lead_time 查询字典
    lead_time_map = {}
    for _, row in lead_time_df.iterrows():
        key = (row["store_id"], row["product_id"])
        lead_time_map[key] = {
            "lead_time_days": int(row["lead_time_days"]),
            "effective_lead_time_days": int(row["effective_lead_time_days"]),
            "k_source": row["k_source"],
        }

    # 构建 forecast 查询字典: (store, product, origin_date, forecast_date) -> forecast_units_sold
    forecast_df = forecast_df.copy()
    forecast_df["origin_dt"] = pd.to_datetime(forecast_df["forecast_origin_date"])
    forecast_df["forecast_dt"] = pd.to_datetime(forecast_df["forecast_date"])
    forecast_indexed = forecast_df.set_index(["store_id", "product_id", "origin_dt", "forecast_dt"])

    # 构建 error_stats 查询字典: (store, product, as_of_date) -> error_std
    error_stats_df = error_stats_df.copy()
    error_stats_df["as_of_dt"] = pd.to_datetime(error_stats_df["as_of_date"])
    error_indexed = error_stats_df.set_index(["store_id", "product_id", "as_of_dt"])

    fact = fact.copy()
    fact["date"] = pd.to_datetime(fact["date"])
    observed = fact[fact["is_observed"]].copy()

    # 使用 as_of_date 过滤观察日期，与调用方意图一致
    as_of_ts = pd.Timestamp(as_of_date)
    max_date = min(fact["date"].max(), as_of_ts)

    rows: List[Dict] = []
    for (store_id, product_id), group in fact.groupby(["store_id", "product_id"]):
        lt_info = lead_time_map.get((store_id, product_id), {
            "lead_time_days": config.lead_time_fallback_days,
            "effective_lead_time_days": max(1, config.lead_time_fallback_days),
            "k_source": "default",
        })
        k = int(lt_info["lead_time_days"])
        k_effective = int(lt_info["effective_lead_time_days"])
        k_source = lt_info["k_source"]

        group = group.sort_values("date").reset_index(drop=True)

        # 只对最近 forecast_window_days 天的观测日期计算补货推荐
        # （更早的日期没有预测数据，计算也是空跑）
        output_window_start = max_date - timedelta(days=config.forecast_window_days)
        observed_group = group[group["is_observed"] & (group["date"] >= output_window_start)].copy()
        for i, row in observed_group.iterrows():
            d = row["date"]

            current_inventory = int(row["opening_inventory"]) - int(row["units_sold"])

            in_transit = _calc_in_transit(
                fact,
                store_id,
                product_id,
                d,
                k_effective,
            )

            # 未来 K 天预测
            forecast_k_total = 0.0
            forecast_7d_total = 0.0
            forecast_status = "insufficient_data"
            missing_forecast = False

            for h in range(1, 8):
                target_date = d + timedelta(days=h)
                key = (store_id, product_id, d, target_date)
                if key in forecast_indexed.index:
                    pred = float(forecast_indexed.loc[key, "forecast_units_sold"])
                    if h <= k_effective:
                        forecast_k_total += pred
                    forecast_7d_total += pred
                else:
                    if h <= k_effective:
                        missing_forecast = True

            if not missing_forecast:
                forecast_status = "ready"

            # 误差标准差：优先使用精确日期，否则回退到该组合最新可用误差 std
            error_key = (store_id, product_id, d)
            if error_key in error_indexed.index:
                sigma = float(error_indexed.loc[error_key, "error_std"])
            else:
                combo_errors = error_stats_df[
                    (error_stats_df["store_id"] == store_id)
                    & (error_stats_df["product_id"] == product_id)
                ]
                if combo_errors.empty:
                    sigma = config.safety_stock_insufficient_std
                else:
                    sigma = float(combo_errors.sort_values("as_of_dt").iloc[-1]["error_std"])

            safety_stock = z * sigma * math.sqrt(k_effective)

            # 日均销量（使用配置中的时间窗口）
            time_range_days = config.default_time_range_days
            window_start = d - timedelta(days=time_range_days - 1)
            window_sales = group[
                (group["date"] >= window_start) & (group["date"] <= d)
            ]["units_sold"].sum()
            avg_daily = window_sales / float(time_range_days)

            # 覆盖天数与库存状态
            total_inventory = current_inventory + in_transit
            if basis == "on_hand_inventory":
                numerator = current_inventory
            else:
                numerator = total_inventory

            if avg_daily <= 0:
                coverage_days = None
                inventory_status = "undetermined"
            else:
                coverage_days = numerator / avg_daily
                inventory_status = _inventory_status(coverage_days, critical_lt, low_lt, normal_lte)

            # 推荐订货量
            raw_replenishment = forecast_k_total - current_inventory - in_transit + safety_stock
            suggested_replenishment = int(math.ceil(max(0.0, raw_replenishment)))

            recommendation_status = "ready" if forecast_status == "ready" else "unavailable"
            message = None if recommendation_status == "ready" else "预测数据不足"

            rows.append({
                "as_of_date": d.strftime("%Y-%m-%d"),
                "store_id": store_id,
                "product_id": product_id,
                "category": row["category"],
                "inventory_date": d.strftime("%Y-%m-%d"),
                "current_inventory": current_inventory,
                "in_transit_inventory": in_transit,
                "lead_time_days": k,
                "effective_lead_time_days": k_effective,
                "forecast_during_lead_time": round(forecast_k_total, 1),
                "forecast_7d_total": round(forecast_7d_total, 1),
                "safety_stock": round(safety_stock, 1),
                "error_std": sigma,
                "avg_daily_units_sold_90d": round(avg_daily, 2),
                "coverage_days": None if coverage_days is None else round(coverage_days, 1),
                "inventory_status": inventory_status,
                "suggested_replenishment": suggested_replenishment,
                "forecast_status": forecast_status,
                "recommendation_status": recommendation_status,
                "message": message,
                "data_version": data_version,
                "model_version": model_version,
                "calculated_at": calculated_at.isoformat(),
            })

    return pd.DataFrame(rows)


def _calc_in_transit(
    fact: pd.DataFrame,
    store_id: str,
    product_id: str,
    inventory_date: datetime,
    k_effective: int,
) -> int:
    """计算在途库存。"""
    k = max(1, int(k_effective))
    if k <= 1:
        return 0

    start_date = inventory_date - timedelta(days=k - 1)
    end_date = inventory_date - timedelta(days=1)

    mask = (
        (fact["store_id"] == store_id)
        & (fact["product_id"] == product_id)
        & (fact["date"] >= start_date)
        & (fact["date"] <= end_date)
    )
    subset = fact[mask]
    if subset.empty:
        return 0
    return int(subset["units_ordered"].sum())


def _inventory_status(
    coverage_days: float,
    critical_lt: float,
    low_lt: float,
    normal_lte: float,
) -> str:
    """根据覆盖天数返回库存状态。"""
    if coverage_days < critical_lt:
        return "critical"
    if coverage_days < low_lt:
        return "low"
    if coverage_days <= normal_lte:
        return "normal"
    return "sufficient"
