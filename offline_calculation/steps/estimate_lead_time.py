"""
提前期 K 估计 - offline_calculation/steps/estimate_lead_time.py
==============================================================

按 (store_id, product_id) 基于最近 90 天历史数据估计固定 K。
"""

from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from offline_calculation.config import OfflineConfig


def estimate_lead_time(
    fact: pd.DataFrame,
    config: OfflineConfig,
    calculated_at: datetime,
    config_version: str = "v1",
) -> pd.DataFrame:
    """
    估计每个 (store_id, product_id) 的固定提前期 K。

    Args:
        fact: fact_daily_inventory_sales DataFrame
        config: 离线配置
        calculated_at: 计算时间
        config_version: 配置版本

    Returns:
        fact_lead_time DataFrame
    """
    min_k = config.lead_time_min_days
    max_k = config.lead_time_max_days
    fallback_k = config.lead_time_fallback_days
    window_days = config.lead_time_window_days

    rows: List[Dict] = []
    fact = fact.copy()
    fact["date"] = pd.to_datetime(fact["date"])

    max_date = fact["date"].max()
    window_start = max_date - timedelta(days=window_days - 1)

    observed = fact[fact["is_observed"]].copy()

    for (store_id, product_id), group in observed.groupby(["store_id", "product_id"]):
        group = group.sort_values("date").reset_index(drop=True)
        window_group = group[group["date"] >= window_start].copy()

        best_k, best_mse, window_start_date, window_end_date = _estimate_single(
            window_group,
            min_k,
            max_k,
            fallback_k,
        )

        if best_k is None:
            k_source = "default"
            lead_time_days = fallback_k
            selected_mse = None
            # 使用窗口内实际日期范围（若窗口为空则使用全局窗口边界）
            if not window_group.empty:
                ws = window_group["date"].min()
                we = window_group["date"].max()
            else:
                ws = window_start
                we = max_date
        else:
            k_source = "estimated"
            lead_time_days = best_k
            selected_mse = best_mse
            ws = window_group["date"].min()
            we = window_group["date"].max()

        effective_k = max(1, lead_time_days)

        rows.append({
            "store_id": store_id,
            "product_id": product_id,
            "lead_time_days": lead_time_days,
            "effective_lead_time_days": effective_k,
            "k_source": k_source,
            "selected_mse": selected_mse,
            "estimation_window_start": ws.strftime("%Y-%m-%d"),
            "estimation_window_end": we.strftime("%Y-%m-%d"),
            "calculated_at": calculated_at.isoformat(),
            "config_version": config_version,
        })

    return pd.DataFrame(rows)


def _estimate_single(
    group: pd.DataFrame,
    min_k: int,
    max_k: int,
    fallback_k: int,
) -> tuple:
    """
    对单个 (store, product) 估计 K。

    Returns:
        (best_k, best_mse, window_start_date, window_end_date)
    """
    if len(group) < 2:
        return None, None, None, None

    indexed = group.set_index("date")
    best_k = None
    best_mse = None

    for k in range(min_k, max_k + 1):
        errors = []
        for i in range(len(group) - 1):
            t_row = group.iloc[i]
            t1_row = group.iloc[i + 1]
            t_date = t_row["date"]
            tk_date = t_date - timedelta(days=k)

            units_ordered_tk = 0
            if tk_date in indexed.index:
                units_ordered_tk = int(indexed.loc[tk_date, "units_ordered"])

            predicted_inv_t1 = (
                int(t_row["opening_inventory"])
                - int(t_row["units_sold"])
                + units_ordered_tk
            )
            actual_inv_t1 = int(t1_row["opening_inventory"])
            errors.append((actual_inv_t1 - predicted_inv_t1) ** 2)

        if not errors:
            continue

        mse = sum(errors) / len(errors)
        if best_mse is None or mse < best_mse or (mse == best_mse and k > best_k):
            best_mse = mse
            best_k = k

    if best_k is None:
        return None, None, None, None

    return best_k, best_mse, group["date"].min(), group["date"].max()
