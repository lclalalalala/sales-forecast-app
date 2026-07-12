import pandas as pd
import numpy as np

df = pd.read_csv('/Users/lucy/CodeSpace/sephora/data/sales_data.csv')
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(['Store ID', 'Product ID', 'Date']).reset_index(drop=True)

# 基础列
df['Inventory_Lag1'] = df.groupby(['Store ID', 'Product ID'])['Inventory Level'].shift(1)
df['Units_Sold_Lag1'] = df.groupby(['Store ID', 'Product ID'])['Units Sold'].shift(1)

# 计算每个 lag k 下的预测库存和差异
K_MAX = 15
results = []

for k in range(0, K_MAX + 1):
    col_name = f'Units_Ordered_Lag{k}'
    df[col_name] = df.groupby(['Store ID', 'Product ID'])['Units Ordered'].shift(k)
    df[f'Pred_Inv_Lag{k}'] = df['Inventory_Lag1'] - df['Units_Sold_Lag1'] + df[col_name]
    df[f'Diff_Lag{k}'] = df['Inventory Level'] - df[f'Pred_Inv_Lag{k}']

    # 只保留有效行
    valid = df.dropna(subset=['Inventory_Lag1', 'Units_Sold_Lag1', col_name])
    n = len(valid)
    exact = (valid[f'Diff_Lag{k}'] == 0).sum()
    mae = valid[f'Diff_Lag{k}'].abs().mean()
    rmse = np.sqrt((valid[f'Diff_Lag{k}'] ** 2).mean())
    within_1 = (valid[f'Diff_Lag{k}'].abs() <= 1).sum()
    within_5 = (valid[f'Diff_Lag{k}'].abs() <= 5).sum()
    within_10 = (valid[f'Diff_Lag{k}'].abs() <= 10).sum()

    results.append({
        'lag_k': k,
        'valid_rows': n,
        'exact_match': exact,
        'exact_pct': exact / n * 100,
        'within_1_pct': within_1 / n * 100,
        'within_5_pct': within_5 / n * 100,
        'within_10_pct': within_10 / n * 100,
        'mae': mae,
        'rmse': rmse
    })

results_df = pd.DataFrame(results)
print("=" * 80)
print("全局：不同 lag_k 的验证结果")
print("=" * 80)
print(results_df.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()

# 找出全局最优 lag
best_by_exact = results_df.loc[results_df['exact_pct'].idxmax()]
best_by_rmse = results_df.loc[results_df['rmse'].idxmin()]
print(f"按精确匹配最优: lag_k={int(best_by_exact['lag_k'])}, 精确匹配率={best_by_exact['exact_pct']:.2f}%")
print(f"按 RMSE 最优: lag_k={int(best_by_rmse['lag_k'])}, RMSE={best_by_rmse['rmse']:.2f}")
print()

# 按 Category 分析
def analyze_by_group(group_cols, name):
    print("=" * 80)
    print(f"按 {name} 分组：各组最优 lag_k（按精确匹配率）")
    print("=" * 80)

    best_lags = []
    for k in range(0, K_MAX + 1):
        valid = df.dropna(subset=['Inventory_Lag1', 'Units_Sold_Lag1', f'Units_Ordered_Lag{k}'])
        grouped = valid.groupby(group_cols)
        for g, sub in grouped:
            exact = (sub[f'Diff_Lag{k}'] == 0).sum()
            n = len(sub)
            best_lags.append({
                'group': g if isinstance(g, tuple) else (g,),
                'lag_k': k,
                'exact_pct': exact / n * 100,
                'rmse': np.sqrt((sub[f'Diff_Lag{k}'] ** 2).mean()),
                'mae': sub[f'Diff_Lag{k}'].abs().mean(),
                'n': n
            })

    best_lags_df = pd.DataFrame(best_lags)
    # 对每个组找最优
    group_best = best_lags_df.loc[best_lags_df.groupby('group')['exact_pct'].idxmax()]
    group_best = group_best.sort_values('exact_pct', ascending=False)
    print(group_best.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
    print()

    # 也输出 lag 分布
    print(f"按 {name} 分组的最优 lag 分布:")
    print(group_best['lag_k'].value_counts().sort_index().to_string())
    print()
    return group_best

# 按 Category
cat_best = analyze_by_group(['Category'], 'Category')

# 按 Store ID
store_best = analyze_by_group(['Store ID'], 'Store ID')

# 按 Product ID
product_best = analyze_by_group(['Product ID'], 'Product ID')

# 按 Store + Category
store_cat_best = analyze_by_group(['Store ID', 'Category'], 'Store ID + Category')

# 按 Product ID（只看最优 lag 和匹配率）
print("=" * 80)
print("按 Product ID 的详细最优 lag（按精确匹配率排序）")
print("=" * 80)
product_best_sorted = product_best.sort_values('exact_pct', ascending=False)
print(product_best_sorted.to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()

# 看看 Units Ordered 为 0 的比例
df['Has_Order'] = df['Units Ordered'] > 0
order_stats = df.groupby(['Store ID', 'Product ID'])['Has_Order'].agg(['sum', 'count', 'mean']).reset_index()
order_stats['zero_order_pct'] = (1 - order_stats['mean']) * 100
order_stats = order_stats.sort_values('mean')
print("=" * 80)
print("各 (Store, Product) 时间序列的下单频率（Ordered > 0 的天数占比）")
print("=" * 80)
print(order_stats.head(20).to_string(index=False, float_format=lambda x: f'{x:.2f}'))
print()
print("下单频率描述统计:")
print(order_stats['mean'].describe())
print()

# 输出每个 lag 的误差分布基本统计
print("=" * 80)
print("全局不同 lag 的 RMSE 对比")
print("=" * 80)
print(results_df[['lag_k', 'exact_pct', 'within_10_pct', 'mae', 'rmse']].to_string(index=False, float_format=lambda x: f'{x:.2f}'))
