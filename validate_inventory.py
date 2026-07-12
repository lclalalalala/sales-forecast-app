import pandas as pd
import numpy as np

df = pd.read_csv('/Users/lucy/CodeSpace/sephora/data/sales_data.csv')

# 解析日期
df['Date'] = pd.to_datetime(df['Date'])

# 按 Store ID, Product ID, Date 排序
df = df.sort_values(['Store ID', 'Product ID', 'Date']).reset_index(drop=True)

# 计算 lag 值
df['Inventory_Lag1'] = df.groupby(['Store ID', 'Product ID'])['Inventory Level'].shift(1)
df['Units_Sold_Lag1'] = df.groupby(['Store ID', 'Product ID'])['Units Sold'].shift(1)
df['Units_Ordered_Lag2'] = df.groupby(['Store ID', 'Product ID'])['Units Ordered'].shift(2)

# 根据公式计算预测库存
df['Predicted_Inventory'] = df['Inventory_Lag1'] - df['Units_Sold_Lag1'] + df['Units_Ordered_Lag2']

# 计算差异
df['Diff'] = df['Inventory Level'] - df['Predicted_Inventory']

# 只保留可以用于验证的行（lag 都存在）
valid = df.dropna(subset=['Inventory_Lag1', 'Units_Sold_Lag1', 'Units_Ordered_Lag2']).copy()

print(f"总行数: {len(df)}")
print(f"可用于验证的行数: {len(valid)} (因为前2天缺少lag值)")
print()

# 精确匹配
exact_match = (valid['Diff'] == 0).sum()
print(f"精确匹配行数: {exact_match} / {len(valid)} ({exact_match/len(valid)*100:.2f}%)")

# 近似匹配（差异绝对值 <= 1, <= 5, <= 10）
for threshold in [1, 5, 10, 50]:
    approx = (valid['Diff'].abs() <= threshold).sum()
    print(f"差异绝对值 <= {threshold}: {approx} / {len(valid)} ({approx/len(valid)*100:.2f}%)")

print()
print("差异统计:")
print(valid['Diff'].describe())

print()
print("差异绝对值分布:")
print(valid['Diff'].abs().describe())

print()
print("差异非零的样本（前20行）:")
nonzero = valid[valid['Diff'] != 0][['Date', 'Store ID', 'Product ID', 'Inventory Level', 'Inventory_Lag1', 'Units Sold', 'Units_Sold_Lag1', 'Units Ordered', 'Units_Ordered_Lag2', 'Predicted_Inventory', 'Diff']].head(20)
print(nonzero.to_string(index=False))

print()
print("结论:")
if exact_match == len(valid):
    print("公式完全成立：对所有可验证数据，Inventory(t) = Inventory(t-1) - Units Sold(t-1) + Units Ordered(t-2)")
else:
    print(f"公式不完全成立。精确匹配率为 {exact_match/len(valid)*100:.2f}%。")
    print("如需判断是否近似成立，请参考差异绝对值分布。")
