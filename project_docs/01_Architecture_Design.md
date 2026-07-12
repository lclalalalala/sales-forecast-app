# 零售门店销售、库存与补货决策系统架构设计

## 1. 目标与范围

系统为店长提供：

- 门店销售概览；
- 畅销品与滞销品分析；
- 库存风险识别；
- 未来销量预测；
- 基于提前期的补货建议；
- 商品销售、库存和补货详情。

当前版本使用 CSV 离线数据，不包含登录、权限、真实采购下单和多门店对比。

预测目标统一为：

```text
Units Sold
```

`Demand` 不作为系统主要展示指标。是否作为预测模型输入，由独立的预测模型规范决定。

---

## 2. 总体架构

采用模块化单体架构，不拆分微服务。

```text
┌─────────────────────────────────────┐
│ React 前端                           │
│ 概览 / 排名 / 补货建议 / 商品详情       │
└──────────────────┬──────────────────┘
                   │ REST/JSON
┌──────────────────▼──────────────────┐
│ API 层                               │
│ 参数校验 / 错误处理 / 响应组装          │
└──────────────────┬──────────────────┘
┌──────────────────▼──────────────────┐
│ 应用层                               │
│ OverviewQuery                        │
│ RankingQuery                         │
│ ReplenishmentQuery                   │
│ ProductDetailQuery                   │
└──────────┬──────────┬──────────┬─────┘
           │          │          │
┌──────────▼───┐ ┌────▼─────┐ ┌──▼────────────┐
│ 销售分析服务  │ │ 库存服务  │ │ 预测适配器      │
└──────────────┘ └──────────┘ └──────┬─────────┘
                                     │
                              ┌──────▼─────────┐
                              │ 补货计算服务     │
                              └──────┬─────────┘
                                     │
                              ┌──────▼─────────┐
                              │ 数据仓储与配置   │
                              │ CSV / 标准化数据 │
                              └────────────────┘
```

---

## 3. 技术选型

| 层级 | 技术 |
|---|---|
| 前端 | React + TypeScript |
| 样式 | Tailwind CSS + shadcn/ui |
| 图表 | Recharts |
| 路由 | React Router |
| 后端 | Python Flask |
| 数据处理 | Pandas + NumPy |
| 数据存储 | CSV，必要时转换为 Parquet |
| 配置 | YAML |
| 构建 | Vite |

---

## 4. 后端模块

建议目录结构：

```text
api/
├── app.py
├── routes/
│   ├── overview_routes.py
│   ├── ranking_routes.py
│   ├── replenishment_routes.py
│   └── product_routes.py
├── application/
│   ├── overview_query.py
│   ├── ranking_query.py
│   ├── replenishment_query.py
│   └── product_detail_query.py
├── domain/
│   ├── sales_service.py
│   ├── inventory_service.py
│   ├── lead_time_service.py
│   ├── forecast_adapter.py
│   ├── safety_stock_service.py
│   ├── replenishment_service.py
│   └── ranking_service.py
├── infrastructure/
│   ├── csv_repository.py
│   ├── normalized_repository.py
│   └── config_repository.py
├── schemas/
│   ├── requests.py
│   └── responses.py
└── config/
    └── business.yaml
```

职责划分：

- `Repository`：读取和查询数据；
- `Normalizer`：统一字段、日期和库存口径；
- `SalesService`：销售趋势、日均销量和销售汇总；
- `InventoryService`：库存、在途库存、覆盖天数和库存状态；
- `LeadTimeService`：估算商品提前期 `K`；
- `ForecastAdapter`：调用外部预测模型；
- `SafetyStockService`：计算安全库存；
- `ReplenishmentService`：计算唯一的补货建议；
- `Query`：根据页面需求组合领域服务结果。

前端不得自行实现补货、库存状态或排名计算。

---

## 5. 核心业务口径

### 5.1 数据粒度

```text
Date + Store ID + Product ID
```

所有销售、库存、预测和补货计算均按：

```text
(store_id, product_id)
```

隔离，不混用不同门店或商品的数据。

### 5.2 当前库存

`Inventory Level` 表示当天销售前库存。

```text
closing_inventory =
Inventory Level - Units Sold
```

门店当前库存基准日：

```text
store_as_of_date =
当前门店的最新有效日期
```

商品在基准日无数据时，使用该商品在基准日前最近的有效日期。

### 5.3 在途库存

以商品实际采用的库存日期 `D` 为基准：

```text
in_transit_inventory =
最近 K - 1 个自然日的 Units Ordered 总和
```

规则：

- 不包含日期 `D`；
- 缺失日期的 `Units Ordered` 按 `0` 处理；
- `K = 1` 时在途库存为 `0`；
- 估算出的 `K = 0` 按 `K = 1` 执行。

### 5.4 日均销量

统一使用最近 90 天：

```text
avg_daily_units_sold =
最近 90 天累计 Units Sold / 90
```

缺失销售日期按 `0` 补齐。

---

## 6. 提前期 `K` 估算

`K` 是下单到入库的提前期，不是安全库存系数。

### 6.1 估算范围

- 分组：`store_id + product_id`；
- 历史窗口：最近 90 天；
- 候选范围：`0～7` 天；
- 无法估算时：默认 `K = 2`。

### 6.2 估算公式

对每个候选 `K`：

```text
predicted_inventory[t+1] =
  Inventory Level[t]
  - Units Sold[t]
  + Units Ordered[t-K]
```

```text
MSE(K) =
mean(
  (
    Inventory Level[t+1]
    - predicted_inventory[t+1]
  )²
)
```

规则：

- 缺少 `t`、`t+1` 或 `t-K` 数据时跳过该样本；
- 选择 MSE 最小的 `K`；
- MSE 完全相同时选择较大的 `K`；
- 所有候选值都无法计算时使用 `K = 2`；
- 返回 `K` 的来源：`estimated` 或 `default`。

---

## 7. 预测模型接口

预测模型由独立规范定义，当前架构不规定具体算法。

### 7.1 输入

模型可接收所有可用历史字段，包括：

- `Units Sold`；
- `Inventory Level`；
- `Units Ordered`；
- 价格、折扣、促销；
- 天气、季节等外部字段；
- `Demand` 是否使用由预测模型规范决定。

### 7.2 输出

模型固定输出未来 7 天：

```json
{
  "daily_forecast_units_sold": [
    {
      "date": "2024-02-01",
      "units_sold": 63.7
    }
  ],
  "prediction_interval": [
    {
      "date": "2024-02-01",
      "lower": 45.2,
      "upper": 82.1
    }
  ],
  "status": "ready",
  "message": null
}
```

`status` 示例：

```text
ready
insufficient_data
error
```

补货计算只使用点预测 `daily_forecast_units_sold`，不使用预测区间上界。

预测模型非 `ready` 时，该商品标记为“无法生成建议”，不影响其他商品。

历史滚动预测和预测误差由外部服务生成，补货服务只消费误差结果。

---

## 8. 安全库存与补货计算

### 8.1 预测误差标准差

```text
error =
实际 Units Sold - 历史预测 Units Sold
```

使用最近 90 天有效预测误差。

```text
sigma =
std(最近 90 天有效预测误差)
```

当有效误差不足 2 个时：

```text
sigma = 1
```

### 8.2 安全库存

```text
safety_stock =
2.33 × sigma × sqrt(K)
```

### 8.3 补货数量

补货目标为未来 `K` 天预测销量：

```text
forecast_during_lead_time =
sum(未来 7 天预测销量的前 K 天)
```

```text
raw_replenishment =
forecast_during_lead_time
+ safety_stock
- current_inventory
- in_transit_inventory
```

```text
suggested_replenishment =
ceil(max(0, raw_replenishment))
```

建议补货数量始终为非负整数。

---

## 9. 库存状态

库存覆盖天数使用含在途库存：

```text
coverage_days =
(current_inventory + in_transit_inventory)
/
avg_daily_units_sold
```

日均销量为 `0` 时：

```text
coverage_days = N/A
inventory_status = undetermined
```

库存状态由配置文件定义：

```yaml
inventory_status:
  basis: total_inventory
  method: coverage_days
  critical_less_than: 2
  low_less_than: 4
  normal_less_than_or_equal: 7
```

含义：

```text
< 2 天       紧缺
>= 2 且 < 4   偏低
>= 4 且 <= 7  正常
> 7 天        充足
```

---

## 10. REST API

### 10.1 门店列表

```http
GET /api/stores
```

### 10.2 门店概览

```http
GET /api/overview?store_id=S001&range=90d&category=all
```

返回：

- 当前分析上下文；
- 数据实际范围；
- 门店核心指标；
- 每日实际销量趋势；
- Top 商品；
- Bottom 商品；
- 当前库存和库存状态。

### 10.3 商品排名

```http
GET /api/rankings
  ?store_id=S001
  &range=90d
  &category=all
  &inventory_status=all
  &top_n=5
  &bottom_n=5
```

排名规则：

- Top：累计 `Units Sold` 降序；
- Bottom：累计 `Units Sold` 升序；
- 销量相同时按 `Product ID` 升序；
- 候选范围为当前门店全部商品；
- 无销售记录按 `0` 处理。

### 10.4 补货建议

```http
GET /api/replenishment?store_id=S001&category=all
```

每个商品返回：

- 商品信息；
- 当前库存；
- 在途库存；
- 库存数据日期；
- `K` 和 `K` 来源；
- 未来 7 天预测销量；
- 未来 `K` 天预测销量；
- 安全库存；
- 建议补货量；
- 库存状态；
- 计算状态和异常原因。

### 10.5 商品详情

```http
GET /api/products/{product_id}
  ?store_id=S001
  &range=90d
```

返回：

- 商品基本信息；
- 实际销量趋势；
- 历史库存变化；
- 当前库存和在途库存；
- 未来 7 天预测；
- 补货计算明细；
- 数据日期和状态信息。

---

## 11. 统一响应上下文

所有主要接口应返回：

```json
{
  "context": {
    "store_id": "S001",
    "category": "all",
    "time_range": "90d",
    "as_of_date": "2024-01-31",
    "actual_data_start": "2022-01-01",
    "actual_data_end": "2024-01-31"
  },
  "data": {}
}
```

时间范围超过可用数据时：

- 使用实际可用数据计算；
- 返回实际数据范围；
- 前端显示数据范围提示。

---

## 12. 配置文件

```yaml
default:
  store_id: S001
  time_range_days: 90

ranking:
  metric: units_sold
  top_n: 5
  bottom_n: 5

lead_time:
  estimation_window_days: 90
  min_days: 0
  max_days: 7
  fallback_days: 2

safety_stock:
  service_level_z: 2.33
  error_window_days: 90
  insufficient_error_std: 1

inventory_status:
  basis: total_inventory
  method: coverage_days
  critical_less_than: 2
  low_less_than: 4
  normal_less_than_or_equal: 7
```

---

## 13. 前端结构

```text
src/
├── components/
│   ├── Layout.tsx
│   ├── StoreSelector.tsx
│   ├── FilterBar.tsx
│   ├── InventoryStatusBadge.tsx
│   └── DataState.tsx
├── pages/
│   ├── DashboardPage.tsx
│   ├── RankingPage.tsx
│   ├── ReplenishmentPage.tsx
│   └── ProductDetailPage.tsx
├── services/
│   └── api.ts
├── types/
│   ├── api.ts
│   ├── sales.ts
│   ├── inventory.ts
│   └── replenishment.ts
├── state/
│   └── analysisContext.ts
└── App.tsx
```

前端统一维护：

- 当前门店；
- 时间范围；
- 商品类别；
- 库存状态；
- 商品选择；
- 返回时的筛选上下文。

前端只负责展示后端计算结果，不复制业务公式。

---

## 14. 异常与数据状态

系统需要支持：

```text
loading
error
empty
insufficient_data
forecast_unavailable
ready
```

错误响应示例：

```json
{
  "error": {
    "code": "FORECAST_UNAVAILABLE",
    "message": "该商品暂时无法生成预测和补货建议"
  }
}
```

单个商品预测失败时：

- 该商品显示异常状态；
- 不展示无法解释的补货数量；
- 其他商品正常展示。

