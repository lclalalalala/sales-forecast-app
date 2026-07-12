# 销量预测算法说明

## 1. 概述

本系统销量预测算法封装在 `api/services/forecast_service.py` 的 `ForecastService` 类中，采用 **集成预测模型（Ensemble Forecasting）**。该模型无需训练，即插即用，对异常值鲁棒，计算高效且可解释性强。

预测目标：基于商品历史销售数据，预测未来 7 天的每日需求量，并据此给出补货建议。

核心入口：

- `ForecastService.predict_next_7_days(historical_data)` —— 预测未来 7 天每日需求
- `ForecastService.calculate_replenishment(...)` —— 基于预测结果计算补货建议

---

## 2. 输入数据

预测算法接收由 `DataService.get_product_history()` 准备的历史数据列表，每条记录包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | `str` | 日期字符串，格式 `YYYY-MM-DD` |
| `datetime` | `datetime` | 日期时间对象，用于排序和目标日期推算 |
| `units_sold` | `int` | 实际销量 |
| `demand` | `int` | 需求量，作为预测的主要目标字段 |
| `dayofweek` | `int` | 星期几（0=周一，6=周日）|
| `month` | `int` | 月份（1-12）|

默认使用最近 90 天的数据（`days=90`），由 API 层调用 `data_service.get_product_history(store_id, product_id, days=90)` 提供。

---

## 3. 算法流程

### 3.1 整体流程

```
predict_next_7_days(historical_data)
│
├─ 数据不足（<7天 或 为空）→ _fallback_prediction()
│
└─ 数据充足
   ├─ 转换为 DataFrame，按 datetime 排序
   ├─ 对 i = 0..6 循环调用 _predict_single_day(df, i)
   │   ├─ 计算近期均值 recent_avg（最近14天）
   │   ├─ 推算目标日期 → 目标星期 target_dow / 目标月份 target_month
   │   ├─ 计算星期模式 dow_avg（历史同期平均，最近8个同星期）
   │   ├─ 计算趋势因子 trend_factor（最近7天 vs 最近30天）
   │   ├─ 计算季节因子 seasonal_factor（同月份历史平均 vs 近期均值）
   │   └─ 集成预测：
   │        main_term = (recent_avg×0.3 + dow_avg×0.4) × trend_factor × 0.7
   │        remainder_term = recent_avg × 0.3 × seasonal_factor
   │        prediction = main_term + remainder_term
   └─ 返回 7 个预测值（保留1位小数）
```

### 3.2 单日预测公式

预测第 \(i\) 天（明天为 \(i=0\)）的需求量：

$$
\hat{y}_i = \underbrace{(0.3 \cdot \bar{y}_{recent} + 0.4 \cdot \bar{y}_{dow}) \cdot f_{trend} \cdot 0.7}_{\text{主项}} + \underbrace{0.3 \cdot \bar{y}_{recent} \cdot f_{seasonal}}_{\text{余项}}
$$

其中：

- \(\bar{y}_{recent}\)：最近 14 天需求量均值（不足 14 天则用全部数据均值）
- \(\bar{y}_{dow}\)：历史中与目标日期相同星期几的最近 8 条记录均值；若样本不足 4 条，则退化为 \(\bar{y}_{recent}\)
- \(f_{trend}\)：趋势因子，见 3.3
- \(f_{seasonal}\)：季节因子，见 3.4

最终结果进行非负截断：

$$
\hat{y}_i = \max(0.0, \hat{y}_i)
$$

### 3.3 趋势因子

比较最近 7 天与最近 30 天的平均需求量，判断趋势方向：

$$
f_{trend} = \text{clip}\left(\frac{\bar{y}_{last7}}{\bar{y}_{last30}},\ 0.7,\ 1.3\right)
$$

- 当数据不足 30 天，或最近 30 天均值 ≤ 0 时，默认 \(f_{trend} = 1.0\)（平稳）
- 裁剪范围 `[0.7, 1.3]` 防止趋势过度反应

### 3.4 季节因子

比较目标月份的历史平均需求量与近期均值：

$$
f_{seasonal} = \text{clip}\left(\frac{\bar{y}_{target\_month}}{\bar{y}_{recent}},\ 0.7,\ 1.3\right)
$$

- 若历史数据中不存在目标月份记录，或近期均值 ≤ 0，则默认 \(f_{seasonal} = 1.0\)
- 裁剪范围同样为 `[0.7, 1.3]`

---

## 4. 算法常量

`ForecastService` 中定义的常量及其含义：

| 常量 | 值 | 说明 |
|------|-----|------|
| `SAFETY_FACTOR` | `1.2` | 默认安全库存系数（20% 缓冲）|
| `RECENT_DAYS` | `14` | 近期均值计算窗口 |
| `TREND_CLIP_MIN` | `0.7` | 趋势/季节因子下限 |
| `TREND_CLIP_MAX` | `1.3` | 趋势/季节因子上限 |
| `RECENT_WEIGHT` | `0.3` | 近期均值在主项中的权重 |
| `DOW_WEIGHT` | `0.4` | 星期模式在主项中的权重 |
| `TREND_WEIGHT` | `0.7` | 趋势因子对主项的额外缩放权重 |
| `SEASONAL_WEIGHT` | `0.3` | 季节因子在余项中的权重 |

---

## 5. 降级预测

当历史数据不足 7 天，或完全为空时，触发 `_fallback_prediction()`：

- 无数据：返回 `[10.0] * 7`
- 有少量数据：返回全局均值的 80% 与 `5.0` 的较大值，共 7 个相同预测值

该策略保证在冷启动或数据缺失场景下，系统仍能给出一个保守且非负的预测。

---

## 6. 补货建议计算

### 6.1 核心公式

基于未来 7 天预测总需求，计算建议补货量：

$$
Q_{replenish} = \max(0,\ \sum_{i=0}^{6}\hat{y}_i \times safety\_factor - inventory_{current})
$$

### 6.2 库存状态评估

根据当前库存与未来 7 天总预测需求的比值，划分库存状态：

| 条件 | 状态 | 颜色 |
|------|------|------|
| `current_inventory > total_predicted × 1.5` | 充足 | green |
| `current_inventory > total_predicted` | 正常 | blue |
| `current_inventory > total_predicted × 0.5` | 偏低 | yellow |
| 其他 | 紧缺 | red |

### 6.3 库存可维持天数

$$
\text{days_of_inventory} = \frac{inventory_{current}}{total\_predicted / 7}
$$

当总预测需求为 0 时，返回 `float('inf')`。

---

## 7. API 调用链路

### 7.1 补货建议接口

`GET /api/replenishment?store_id=S001&safety_factor=1.2`

流程：

1. 调用 `data_service.get_product_ranking(store_id, days=90)` 获取 Top 5 畅销品
2. 对每个 Top 5 商品：
   - `data_service.get_product_history(store_id, pid, days=90)` 获取历史数据
   - `forecast_service.predict_next_7_days(product_data)` 预测未来 7 天需求
   - `data_service.get_current_inventory(store_id, pid)` 获取当前库存
   - 计算建议补货量 `max(0, total_predicted * safety_factor - current_inventory)`
3. 置信度判断：历史数据 ≥ 60 天为 `high`，否则为 `medium`

### 7.2 商品详情接口

`GET /api/products/detail?store_id=S001&product_id=P0001&days=90&safety_factor=1.2`

流程：

1. 获取商品历史数据与基本信息
2. 调用 `forecast_service.predict_next_7_days(history)`
3. 基于预测总量与当前库存计算建议补货量
4. 返回 `historical_sales` 与 `forecast` 对象

---

## 8. 前端展示

### 8.1 商品详情页 `ProductDetailPage.tsx`

- 使用柱状图展示未来 7 天每日预测需求
- 以网格卡片形式展示每日预测值
- 信息卡展示：当前库存、商品价格、建议补货量、7 天预测总量
- 库存状态按可维持天数分三档：充足（>7天）、偏低（3-7天）、紧缺（≤3天）

### 8.2 补货建议页 `ReplenishmentPage.tsx`

- 展示 Top 5 畅销品的补货建议表格
- 底部计算说明：

```
建议补货量 = max(0, 预测7天总需求 × 安全系数 - 当前库存)
```

---

## 9. 当前实现的特点与局限

### 9.1 特点

- **无需训练**：不依赖模型训练，启动即用
- **可解释性强**：每个预测值都可拆解为近期均值、星期模式、趋势、季节四个组成部分
- **鲁棒性好**：对历史数据中的异常值通过均值和裁剪机制进行平滑
- **计算高效**：单次预测时间复杂度为 O(n)，n 为历史数据天数

### 9.2 局限与改进方向

| 局限 | 改进方向 |
|------|---------|
| 仅使用需求量 `demand` 作为目标，未区分促销、折扣、竞品价格等外部变量 | 引入多元回归或 XGBoost/LightGBM 等监督模型 |
| 趋势和季节因子采用简单比值，未做平滑或分解 | 引入 STL 分解、Holt-Winters 指数平滑或 Prophet |
| 预测窗口固定为 7 天，灵活性不足 | 支持参数化预测天数 |
| 未量化预测不确定性 | 增加预测区间（如 95% 置信区间）|
| 所有商品共用一套权重超参数 | 按品类或商品维度进行参数调优或自动学习 |
| 未考虑库存约束对销量的影响 | 引入因果推断或需求删失（censored demand）建模 |

---

## 10. 文件索引

| 文件 | 说明 |
|------|------|
| `api/services/forecast_service.py` | 预测算法核心实现 |
| `api/services/data_service.py` | 历史数据准备与特征提取 |
| `api/app.py` | API 路由与预测服务调用 |
| `app/src/pages/ProductDetailPage.tsx` | 商品详情页预测展示 |
| `app/src/pages/ReplenishmentPage.tsx` | 补货建议页展示 |
| `app/src/types/index.ts` | 前后端共享类型定义 |
