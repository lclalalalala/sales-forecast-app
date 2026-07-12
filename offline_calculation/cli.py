"""
离线计算 CLI 入口 - offline_calculation/cli.py
===============================================

用法:
    python -m offline_calculation
    python -m offline_calculation --as-of-date 2024-01-23
    python -m offline_calculation --output ./custom_output
"""

import argparse
from datetime import date, datetime

from offline_calculation.config import OUTPUT_DIR, RAW_DATA_PATH, OfflineConfig
from offline_calculation.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Sephora 离线计算模块")
    parser.add_argument(
        "--input",
        default=RAW_DATA_PATH,
        help=f"原始数据 CSV 路径 (默认: {RAW_DATA_PATH})",
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_DIR,
        help=f"输出目录 (默认: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="business.yaml 路径 (默认: config/business.yaml)",
    )
    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=None,
        help="计算基准日期 (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    # 将 date 转换为 datetime，与 pipeline 签名一致
    as_of_date = datetime.combine(args.as_of_date, datetime.min.time()) if args.as_of_date else None

    config = OfflineConfig.from_file(args.config) if args.config else OfflineConfig.from_file()
    run_pipeline(
        raw_path=args.input,
        output_dir=args.output,
        config=config,
        as_of_date=as_of_date,
    )


if __name__ == "__main__":
    main()
