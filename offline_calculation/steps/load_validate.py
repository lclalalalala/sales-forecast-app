"""
加载与校验原始数据 - offline_calculation/steps/load_validate.py
===============================================================

读取原始 sales_data.csv，执行数据质量校验，输出数据质量报告。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Tuple

import pandas as pd


REQUIRED_COLUMNS = {
    "date": "Date",
    "store_id": "Store ID",
    "product_id": "Product ID",
    "category": "Category",
    "region": "Region",
    "inventory_level": "Inventory Level",
    "units_sold": "Units Sold",
    "units_ordered": "Units Ordered",
    "price": "Price",
}


def load_and_validate(raw_path: str, output_dir: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    加载原始数据并执行质量校验。

    Returns:
        (raw_df, quality_report)
    """
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"原始数据文件不存在: {raw_path}")

    raw_df = pd.read_csv(raw_path)

    # 检查必需列
    missing = [col for col in REQUIRED_COLUMNS.values() if col not in raw_df.columns]
    if missing:
        raise ValueError(f"原始数据缺少必需列: {missing}")

    # 标准化列名
    rename_map = {v: k for k, v in REQUIRED_COLUMNS.items()}
    raw_df = raw_df.rename(columns=rename_map).copy()

    # 基础类型转换
    raw_df["date"] = pd.to_datetime(raw_df["date"])
    raw_df["units_sold"] = pd.to_numeric(raw_df["units_sold"], errors="coerce")
    raw_df["units_ordered"] = pd.to_numeric(raw_df["units_ordered"], errors="coerce")
    raw_df["inventory_level"] = pd.to_numeric(raw_df["inventory_level"], errors="coerce")

    # 空值检查
    null_count = int(raw_df[list(REQUIRED_COLUMNS.keys())].isnull().sum().sum())

    # 重复检查
    duplicate_count = int(raw_df.duplicated(subset=["date", "store_id", "product_id"]).sum())

    # 负值检查
    negative_count = int(
        (raw_df["units_sold"] < 0).sum() + (raw_df["units_ordered"] < 0).sum()
    )

    # 库存平衡检查（粗略）
    raw_df_sorted = raw_df.sort_values(["store_id", "product_id", "date"]).reset_index(drop=True)
    raw_df_sorted["closing_inventory"] = raw_df_sorted["inventory_level"] - raw_df_sorted["units_sold"]
    raw_df_sorted["next_opening"] = raw_df_sorted.groupby(["store_id", "product_id"])["inventory_level"].shift(-1)
    raw_df_sorted["inventory_balance_error"] = (
        raw_df_sorted["next_opening"] - raw_df_sorted["closing_inventory"]
    ).abs()
    # 允许一定容差
    inventory_balance_error_count = int(
        (raw_df_sorted["inventory_balance_error"] > 10).sum()
    )

    quality_report = {
        "data_version": "v1",
        "row_count": int(len(raw_df)),
        "store_count": int(raw_df["store_id"].nunique()),
        "product_count": int(raw_df["product_id"].nunique()),
        "date_start": str(raw_df["date"].min()),
        "date_end": str(raw_df["date"].max()),
        "duplicate_count": duplicate_count,
        "null_count": null_count,
        "negative_value_count": negative_count,
        "inventory_balance_error_count": inventory_balance_error_count,
        "status": "pass" if all([
            duplicate_count == 0,
            null_count == 0,
            negative_count == 0,
        ]) else "fail",
        "calculated_at": datetime.now().isoformat(),
    }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "data_quality_report.json"), "w", encoding="utf-8") as f:
        json.dump(quality_report, f, ensure_ascii=False, indent=2)

    report_df = pd.DataFrame([quality_report])
    report_df.to_csv(os.path.join(output_dir, "data_quality_report.csv"), index=False)

    if quality_report["status"] == "fail":
        raise ValueError(f"数据质量校验失败: {quality_report}")

    return raw_df, quality_report
