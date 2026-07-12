import pandas as pd
import numpy as np

# 读取已保存的 (Store, Product) lead time 映射
sp_lead = pd.read_csv('/Users/lucy/CodeSpace/sephora/store_product_lead_time.csv')

# 读取原始数据以补充 Category、Region 信息
df = pd.read_csv('/Users/lucy/CodeSpace/sephora/data/sales_data.csv')
product_meta = df[['Product ID', 'Category']].drop_duplicates()
store_region = df[['Store ID', 'Region']].drop_duplicates()

sp_lead = sp_lead.merge(product_meta, on='Product ID', how='left')
sp_lead = sp_lead.merge(store_region, on='Store ID', how='left')

print("=" * 80)
print("(Store, Product) lead time 分布")
print("=" * 80)
print(sp_lead['lead_time_k'].value_counts().sort_index().to_string())
print()

print("=" * 80)
print("按 Category 的 lead time 分布")
print("=" * 80)
cat_dist = pd.crosstab(sp_lead['Category'], sp_lead['lead_time_k'], margins=True)
print(cat_dist.to_string())
print()

print("=" * 80)
print("按 Store ID 的 lead time 分布")
print("=" * 80)
store_dist = pd.crosstab(sp_lead['Store ID'], sp_lead['lead_time_k'], margins=True)
print(store_dist.to_string())
print()

print("=" * 80)
print("按 Region 的 lead time 分布")
print("=" * 80)
region_dist = pd.crosstab(sp_lead['Region'], sp_lead['lead_time_k'], margins=True)
print(region_dist.to_string())
print()

print("=" * 80)
print("每个 Category 的最常见 lead time（众数）")
print("=" * 80)
for cat in sorted(sp_lead['Category'].unique()):
    mode_k = sp_lead[sp_lead['Category'] == cat]['lead_time_k'].mode().values
    print(f"{cat}: 众数 lag = {list(mode_k)}")
print()

print("=" * 80)
print("每个 Store 的最常见 lead time（众数）")
print("=" * 80)
for store in sorted(sp_lead['Store ID'].unique()):
    mode_k = sp_lead[sp_lead['Store ID'] == store]['lead_time_k'].mode().values
    print(f"{store}: 众数 lag = {list(mode_k)}")
print()

# 完整映射表
print("=" * 80)
print("完整 (Store, Product) lead time 映射表")
print("=" * 80)
sp_lead_sorted = sp_lead.sort_values(['Store ID', 'Product ID'])
print(sp_lead_sorted[['Store ID', 'Product ID', 'Category', 'Region', 'lead_time_k']].to_string(index=False))
print()

# 找出是否有异常：比如同一个 Product 在不同 Store 的 lead time 差异
print("=" * 80)
print("同一 Product 在不同 Store 的 lead time 差异")
print("=" * 80)
product_var = sp_lead.groupby('Product ID')['lead_time_k'].agg(['min', 'max', 'std', 'nunique']).reset_index()
product_var['range'] = product_var['max'] - product_var['min']
product_var = product_var.sort_values('range', ascending=False)
print(product_var.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()

# 统计有多少 product 在所有 store 的 lead time 一致
consistent_products = product_var[product_var['nunique'] == 1]
print(f"在所有 Store 中 lead time 一致的 Product: {len(consistent_products)} / {len(product_var)}")
print()

# 找出按 Product 聚合的 lead time（取众数）
print("=" * 80)
print("按 Product 的众数 lead time")
print("=" * 80)
product_mode = sp_lead.groupby('Product ID')['lead_time_k'].apply(lambda x: x.mode().iloc[0]).reset_index(name='mode_lead_time')
product_mode = product_mode.merge(product_meta, on='Product ID', how='left')
print(product_mode.to_string(index=False))
print()

# 保存完整映射
sp_lead_sorted[['Store ID', 'Product ID', 'Category', 'Region', 'lead_time_k']].to_csv(
    '/Users/lucy/CodeSpace/sephora/store_product_lead_time_full.csv', index=False)
print("完整映射表已保存到 store_product_lead_time_full.csv")
