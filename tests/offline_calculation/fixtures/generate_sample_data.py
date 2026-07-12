"""
生成测试 fixtures 用的 sample_sales_data.csv。
运行: python tests/offline_calculation/fixtures/generate_sample_data.py
"""

import pandas as pd
from datetime import datetime, timedelta
import random

random.seed(42)

stores = ["S001", "S002"]
products = ["P0001", "P0002"]
start_date = datetime(2023, 10, 1)
days = 200  # 需要 >= 180 天初始数据（MIN_INITIAL_HISTORY_DAYS），留余量

rows = []
for store in stores:
    for product in products:
        inventory = random.randint(150, 300)
        for i in range(days):
            date = start_date + timedelta(days=i)
            sold = random.randint(20, 80)
            ordered = random.randint(30, 100)
            opening = inventory
            rows.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Store ID": store,
                "Product ID": product,
                "Category": "Electronics",
                "Region": "North",
                "Inventory Level": opening,
                "Units Sold": sold,
                "Units Ordered": ordered,
                "Price": 50.0,
                "Discount": 0,
                "Weather Condition": "Sunny",
                "Promotion": 0,
                "Competitor Pricing": 55.0,
                "Seasonality": "Winter",
                "Epidemic": 0,
                "Demand": sold + random.randint(-10, 10),
            })
            inventory = opening - sold + ordered

df = pd.DataFrame(rows)
df.to_csv("tests/offline_calculation/fixtures/sample_sales_data.csv", index=False)
print(f"Generated {len(df)} rows")
