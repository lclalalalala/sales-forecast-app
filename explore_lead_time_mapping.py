import pandas as pd
import numpy as np

df = pd.read_csv('/Users/lucy/CodeSpace/sephora/data/sales_data.csv')
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(['Store ID', 'Product ID', 'Date']).reset_index(drop=True)

# 基础 lag
df['Inventory_Lag1'] = df.groupby(['Store ID', 'Product ID'])['Inventory Level'].shift(1)
df['Units_Sold_Lag1'] = df.groupby(['Store ID', 'Product ID'])['Units Sold'].shift(1)

K_MAX = 10

# 计算所有 lag
def compute_lag(df, k):
    df[f'Ordered_Lag{k}'] = df.groupby(['Store ID', 'Product ID'])['Units Ordered'].shift(k)
    df[f'Pred_Lag{k}'] = df['Inventory_Lag1'] - df['Units_Sold_Lag1'] + df[f'Ordered_Lag{k}']
    df[f'Diff_Lag{k}'] = df['Inventory Level'] - df[f'Pred_Lag{k}']

for k in range(K_MAX + 1):
    compute_lag(df, k)

# 1. 建立 Store+Category 的 lead time 映射
print("=" * 80)
print("Step 1: 每个 (Store, Category) 组合的最优 lead time")
print("=" * 80)

records = []
for (store, cat), sub in df.groupby(['Store ID', 'Category']):
    best_k = -1
    best_pct = -1
    best_rmse = float('inf')
    for k in range(K_MAX + 1):
        valid_sub = sub.dropna(subset=[f'Ordered_Lag{k}'])
        if len(valid_sub) == 0:
            continue
        exact = (valid_sub[f'Diff_Lag{k}'] == 0).sum()
        pct = exact / len(valid_sub) * 100
        rmse = np.sqrt((valid_sub[f'Diff_Lag{k}'] ** 2).mean())
        if pct > best_pct:
            best_pct = pct
            best_k = k
            best_rmse = rmse
    records.append({
        'Store ID': store,
        'Category': cat,
        'lead_time_k': best_k,
        'exact_pct': best_pct,
        'rmse': best_rmse,
        'n': len(sub)
    })

store_cat_lead = pd.DataFrame(records)
print(store_cat_lead.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()

# 用 Store+Category 映射生成预测
df = df.merge(store_cat_lead[['Store ID', 'Category', 'lead_time_k']], on=['Store ID', 'Category'], how='left')

def get_pred_by_lead(row):
    k = int(row['lead_time_k'])
    return row[f'Pred_Lag{k}']

df['Pred_StoreCat'] = df.apply(get_pred_by_lead, axis=1)
df['Diff_StoreCat'] = df['Inventory Level'] - df['Pred_StoreCat']
valid_store_cat = df.dropna(subset=['Pred_StoreCat'])
print(f"使用 Store+Category 级别 lead time 后:")
print(f"  可验证行数: {len(valid_store_cat)}")
print(f"  精确匹配: {(valid_store_cat['Diff_StoreCat'] == 0).sum()} / {len(valid_store_cat)} ({(valid_store_cat['Diff_StoreCat'] == 0).mean()*100:.2f}%)")
print(f"  RMSE: {np.sqrt((valid_store_cat['Diff_StoreCat'] ** 2).mean()):.2f}")
print()

# 2. 建立 Product ID 级别的 lead time 映射
print("=" * 80)
print("Step 2: 每个 Product ID 的最优 lead time")
print("=" * 80)

records = []
for (product,), sub in df.groupby(['Product ID']):
    best_k = -1
    best_pct = -1
    best_rmse = float('inf')
    for k in range(K_MAX + 1):
        valid_sub = sub.dropna(subset=[f'Ordered_Lag{k}'])
        if len(valid_sub) == 0:
            continue
        exact = (valid_sub[f'Diff_Lag{k}'] == 0).sum()
        pct = exact / len(valid_sub) * 100
        rmse = np.sqrt((valid_sub[f'Diff_Lag{k}'] ** 2).mean())
        if pct > best_pct:
            best_pct = pct
            best_k = k
            best_rmse = rmse
    records.append({
        'Product ID': product,
        'lead_time_k': best_k,
        'exact_pct': best_pct,
        'rmse': best_rmse,
        'n': len(sub)
    })

product_lead = pd.DataFrame(records)
print(product_lead.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()

# 用 Product ID 映射生成预测
df = df.merge(product_lead[['Product ID', 'lead_time_k']].rename(columns={'lead_time_k': 'lead_time_k_product'}), on='Product ID', how='left')

def get_pred_by_product_lead(row):
    k = int(row['lead_time_k_product'])
    return row[f'Pred_Lag{k}']

df['Pred_Product'] = df.apply(get_pred_by_product_lead, axis=1)
df['Diff_Product'] = df['Inventory Level'] - df['Pred_Product']
valid_product = df.dropna(subset=['Pred_Product'])
print(f"使用 Product ID 级别 lead time 后:")
print(f"  可验证行数: {len(valid_product)}")
print(f"  精确匹配: {(valid_product['Diff_Product'] == 0).sum()} / {len(valid_product)} ({(valid_product['Diff_Product'] == 0).mean()*100:.2f}%)")
print(f"  RMSE: {np.sqrt((valid_product['Diff_Product'] ** 2).mean()):.2f}")
print()

# 3. 建立 (Store, Product) 级别的 lead time 映射
print("=" * 80)
print("Step 3: 每个 (Store, Product) 组合的最优 lead time")
print("=" * 80)

records = []
for (store, product), sub in df.groupby(['Store ID', 'Product ID']):
    best_k = -1
    best_pct = -1
    best_rmse = float('inf')
    for k in range(K_MAX + 1):
        valid_sub = sub.dropna(subset=[f'Ordered_Lag{k}'])
        if len(valid_sub) == 0:
            continue
        exact = (valid_sub[f'Diff_Lag{k}'] == 0).sum()
        pct = exact / len(valid_sub) * 100
        rmse = np.sqrt((valid_sub[f'Diff_Lag{k}'] ** 2).mean())
        if pct > best_pct:
            best_pct = pct
            best_k = k
            best_rmse = rmse
    records.append({
        'Store ID': store,
        'Product ID': product,
        'lead_time_k': best_k,
        'exact_pct': best_pct,
        'rmse': best_rmse,
        'n': len(sub)
    })

store_product_lead = pd.DataFrame(records)
print(store_product_lead.head(30).to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print(f"... 共 {len(store_product_lead)} 个组合")
print()

# 用 (Store, Product) 映射生成预测
df = df.merge(store_product_lead[['Store ID', 'Product ID', 'lead_time_k']].rename(columns={'lead_time_k': 'lead_time_k_sp'}), on=['Store ID', 'Product ID'], how='left')

def get_pred_by_sp_lead(row):
    k = int(row['lead_time_k_sp'])
    return row[f'Pred_Lag{k}']

df['Pred_StoreProduct'] = df.apply(get_pred_by_sp_lead, axis=1)
df['Diff_StoreProduct'] = df['Inventory Level'] - df['Pred_StoreProduct']
valid_sp = df.dropna(subset=['Pred_StoreProduct'])
print(f"使用 (Store, Product) 级别 lead time 后:")
print(f"  可验证行数: {len(valid_sp)}")
print(f"  精确匹配: {(valid_sp['Diff_StoreProduct'] == 0).sum()} / {len(valid_sp)} ({(valid_sp['Diff_StoreProduct'] == 0).mean()*100:.2f}%)")
print(f"  RMSE: {np.sqrt((valid_sp['Diff_StoreProduct'] ** 2).mean()):.2f}")
print()

# 4. 汇总对比
print("=" * 80)
print("汇总对比")
print("=" * 80)
summary = pd.DataFrame([
    {'粒度': '全局固定 lag=1', '精确匹配率%': (valid_sp['Diff_Lag1'] == 0).mean()*100, 'RMSE': np.sqrt((valid_sp['Diff_Lag1'] ** 2).mean())},
    {'粒度': '全局固定 lag=2', '精确匹配率%': (valid_sp['Diff_Lag2'] == 0).mean()*100, 'RMSE': np.sqrt((valid_sp['Diff_Lag2'] ** 2).mean())},
    {'粒度': 'Store+Category 级别 lead time', '精确匹配率%': (valid_store_cat['Diff_StoreCat'] == 0).mean()*100, 'RMSE': np.sqrt((valid_store_cat['Diff_StoreCat'] ** 2).mean())},
    {'粒度': 'Product ID 级别 lead time', '精确匹配率%': (valid_product['Diff_Product'] == 0).mean()*100, 'RMSE': np.sqrt((valid_product['Diff_Product'] ** 2).mean())},
    {'粒度': '(Store, Product) 级别 lead time', '精确匹配率%': (valid_sp['Diff_StoreProduct'] == 0).mean()*100, 'RMSE': np.sqrt((valid_sp['Diff_StoreProduct'] ** 2).mean())},
])
print(summary.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()

# 5. 导出 lead time 映射表
print("=" * 80)
print("Store+Category lead time 映射表（可用于后续建模）")
print("=" * 80)
print(store_cat_lead.to_string(index=False))
print()

print("=" * 80)
print("Product ID lead time 映射表（可用于后续建模）")
print("=" * 80)
print(product_lead.to_string(index=False))
print()

# 保存到 CSV
store_cat_lead.to_csv('/Users/lucy/CodeSpace/sephora/store_category_lead_time.csv', index=False)
product_lead.to_csv('/Users/lucy/CodeSpace/sephora/product_lead_time.csv', index=False)
store_product_lead.to_csv('/Users/lucy/CodeSpace/sephora/store_product_lead_time.csv', index=False)
print("Lead time 映射表已保存为:")
print("  - store_category_lead_time.csv")
print("  - product_lead_time.csv")
print("  - store_product_lead_time.csv")
