# 前后端通讯 API 接口说明

> 文档对应后端版本：`api/app.py` 及其注册的新版 Flask 路由。  
> 更新日期：2026/07/12

## 1. 概述

本项目采用前后端分离架构：

- **后端**：`./api`，基于 Flask 提供 RESTful JSON API，监听端口 `8999`。
- **前端**：`./app`，基于 React + TypeScript，通过 `app/src/services/api.ts` 统一封装后端调用。

所有新版数据接口统一返回如下信封结构：

```json
{
  "context": {
    "store_id": "S001",
    "category": "all",
    "time_range": "90d",
    "as_of_date": "2023-12-31",
    "actual_data_start": "2023-10-03",
    "actual_data_end": "2023-12-31"
  },
  "data": { ... }
}
```

- `context`：说明本次查询的上下文（门店、类别、时间范围、数据截止日期、实际数据区间）。
- `data`：具体业务数据。

异常时返回：

```json
{
  "error": {
    "code": "INVALID_RANGE",
    "message": "time_range 必须是 7d、30d、90d、180d 或 all"
  }
}
```

错误 HTTP 状态码：参数校验失败返回 `400`，服务端内部错误返回 `500`。

---

## 2. 通用约定

### 2.1 Base URL

后端默认地址：

```
http://localhost:8999/api
```

前端通过环境变量覆盖：

```ts
const API_BASE = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8999/api';
```

### 2.2 CORS

后端对 `/api/*` 开启跨域，允许所有来源：

```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### 2.3 公共查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `store_id` | string | 否 | `S001` | 门店 ID，后端通过 `parse_store_id` 解析 |
| `category` | string | 否 | `None`（视为 `all`） | 商品类别过滤 |
| `range` | string | 否 | `None`（视为 `all`） | 时间范围：`7d`、`30d`、`90d`、`180d`、`all` |
| `inventory_status` | string | 否 | `None`（视为 `all`） | 库存状态过滤：`critical`、`low`、`normal`、`sufficient`、`undetermined` |

### 2.4 公共响应上下文字段

`context` 对象包含以下字段：

| 字段 | 类型 | 含义 |
|------|------|------|
| `store_id` | string | 查询门店 |
| `category` | string | 查询类别，未指定时为 `all` |
| `time_range` | string | 查询时间范围，如 `90d` 或 `all` |
| `as_of_date` | string | 门店最新数据日期（数据截止日期） |
| `actual_data_start` | string | 实际返回数据的最早日期 |
| `actual_data_end` | string | 实际返回数据的最晚日期 |

---

## 3. 接口清单

接口清单总览如下。各字段的详细类型、默认值、必填规则及嵌套结构参见下方 3.1–3.9 分节。

| 接口功能 | 前端调用场景 | 后端调用地址 | 传入参数 | 传出数据 |
|---|---|---|---|---|
| 健康检查 | 无（运维/启动自检） | `GET /api/health` | 无 | `context=null`，`data={status, data_loaded, stores_count, products_count, categories_count}` |
| 门店列表 | DashboardPage、RankingPage、ProductDetailPage、ReplenishmentPage、OrderForm | `GET /api/stores` | 无 | `context=null`，`data=[{id, name, region}]` |
| 类别列表 | DashboardPage、RankingPage、ProductDetailPage、ReplenishmentPage | `GET /api/categories` | 无 | `context=null`，`data=string[]` |
| 商品列表 | ProductDetailPage | `GET /api/products` | `store_id`、`category` | `data=[{id, name, category}]` |
| 商品详情 | ProductDetailPage、OrderForm | `GET /api/products/{product_id}` | `store_id`、`range` | `data={product_id, category, price, current_inventory, in_transit_inventory, inventory_date, historical_sales, forecast, replenishment}` |
| Dashboard 概览 | DashboardPage | `GET /api/overview` | `store_id`、`range`、`category` | `data={kpis, daily_sales, top_products, bottom_products, data_date_note}` |
| 商品排名 | RankingPage | `GET /api/rankings` | `store_id`、`range`、`category`、`inventory_status`、`top_n`、`bottom_n` | `data={top, bottom, total_candidates}` |
| 补货建议 | ReplenishmentPage | `GET /api/replenishment` | `store_id`、`category` | `data={suggestions[]}` |
| 提交补货订单 | OrderForm | 无（前端 Mock） | `OrderDraft: store_id, product_id, quantity, note` | `{success, orderId}` |



### 3.1 健康检查

- **Method**：`GET`
- **Path**：`/api/health`
- **前端调用**：无（运维/启动自检使用）
- **说明**：返回数据加载状态与数据集统计。

**响应示例**：

```json
{
  "context": null,
  "data": {
    "status": "ok",
    "data_loaded": true,
    "stores_count": 5,
    "products_count": 20,
    "categories_count": 4
  }
}
```

---

### 3.2 门店列表

- **Method**：`GET`
- **Path**：`/api/stores`
- **前端调用**：`api.getStores()` → `app/src/services/api.ts:81`
- **说明**：返回所有门店的元数据，前端用于门店筛选下拉框。

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 门店 ID |
| `name` | string | 展示名称，后端按 `门店 {id}` 组装 |
| `region` | string | 门店所属区域 |

---

### 3.3 商品类别列表

- **Method**：`GET`
- **Path**：`/api/categories`
- **前端调用**：`api.getCategories()` → `app/src/services/api.ts:85`
- **说明**：返回所有商品类别字符串列表，用于类别筛选。

**响应示例**：

```json
{
  "context": null,
  "data": ["Beauty", "Fragrance", "Hair Care", "Skin Care"]
}
```

---

### 3.4 商品列表

- **Method**：`GET`
- **Path**：`/api/products`
- **前端调用**：`api.getProducts(storeId?, category?)` → `app/src/services/api.ts:89`
- **说明**：按门店和类别过滤，返回商品基础信息。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `store_id` | string | 否 | `S001` | 门店 ID |
| `category` | string | 否 | - | 类别过滤 |

**响应字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 商品 ID |
| `name` | string | 当前实现与 `id` 一致 |
| `category` | string | 商品类别 |

**后端实现**：`api/routes/product_routes.py:16` → `normalized_repository.get_products`。

---

### 3.5 商品详情

- **Method**：`GET`
- **Path**：`/api/products/{product_id}`
- **前端调用**：`api.getProductDetail(productId, storeId, range)` → `app/src/services/api.ts:148`
- **说明**：返回单个商品的历史销量、预测、补货建议等完整信息，用于商品详情页。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `store_id` | string | 否 | `S001` | 门店 ID |
| `range` | string | 否 | `all` | 历史销量时间范围 |

**响应 `data` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `product_id` | string | 商品 ID |
| `category` | string | 商品类别 |
| `price` | number | 商品单价 |
| `current_inventory` | number | 当前库存 |
| `in_transit_inventory` | number | 在途库存 |
| `inventory_date` | string \| null | 库存日期 |
| `historical_sales` | array | 历史销量与库存记录 |
| `forecast` | object | 7 天销量预测与预测区间 |
| `replenishment` | object | 补货相关指标 |

**`historical_sales` 元素字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 日期 |
| `units_sold` | number | 销量 |
| `inventory_level` | number | 库存水平 |
| `demand` | number | 需求 |

**`forecast` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `daily_forecast_units_sold` | array | 未来 7 天每日预测销量 |
| `prediction_interval` | array | 预测区间（lower / upper） |
| `status` | string | `ready`、`insufficient_data`、`error`、`forecast_unavailable` |
| `message` | string \| null | 状态说明 |

**`replenishment` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `lead_time_k` | number | 提前期 K（天） |
| `lead_time_k_source` | string | `estimated`（估计） / `default`（默认值） |
| `forecast_k_total` | number | 提前期 K 内的预测总需求 |
| `safety_stock` | number | 安全库存 |
| `suggested_replenishment` | number | 建议补货量 |
| `inventory_status` | string | 库存状态 |

**后端实现**：`api/routes/product_routes.py:38` → `application.product_detail_query.execute` → `api/application/product_detail_query.py:41`。

---

### 3.6 数据概览

- **Method**：`GET`
- **Path**：`/api/overview`
- **前端调用**：`api.getOverview(storeId, range, category?)` → `app/src/services/api.ts:101`
- **说明**：返回 Dashboard 所需的核心 KPI、销售趋势、Top/Bottom 商品排名。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `store_id` | string | 否 | `S001` | 门店 ID |
| `range` | string | 否 | `all` | 时间范围 |
| `category` | string | 否 | - | 类别过滤 |

**响应 `data` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `kpis` | object | 关键指标 |
| `daily_sales` | array | 每日销量趋势 |
| `top_products` | array | Top N 商品排名 |
| `bottom_products` | array | Bottom N 商品排名 |
| `data_date_note` | string \| null | 数据日期备注 |

**`kpis` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `avg_daily_units_sold` | number | 日均销量 |
| `current_inventory_total` | number | 当前库存总量 |
| `low_stock_count` | number | 低库存商品数 |
| `critical_stock_count` | number | 紧缺库存商品数 |

**`daily_sales` 元素字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 日期 |
| `units_sold` | number | 销量 |

**`top_products` / `bottom_products` 元素字段**：与 `/api/rankings` 的 `RankingItem` 一致（见 3.7）。

**后端实现**：`api/routes/overview_routes.py:15` → `application.overview_query.execute` → `api/application/overview_query.py:38`。

---

### 3.7 商品排名

- **Method**：`GET`
- **Path**：`/api/rankings`
- **前端调用**：`api.getRankings(storeId, range, category?, inventoryStatus?, topN?, bottomN?)` → `app/src/services/api.ts:121`
- **说明**：返回商品销量的 Top / Bottom 排名，支持库存状态过滤。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `store_id` | string | 否 | `S001` | 门店 ID |
| `range` | string | 否 | `all` | 时间范围 |
| `category` | string | 否 | - | 类别过滤 |
| `inventory_status` | string | 否 | `all` | 库存状态过滤 |
| `top_n` | integer | 否 | `5` | Top 排名数量 |
| `bottom_n` | integer | 否 | `5` | Bottom 排名数量 |

**响应 `data` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `top` | array | Top N 商品 |
| `bottom` | array | Bottom N 商品 |
| `total_candidates` | integer | 符合过滤条件的候选商品总数 |

**`RankingItem` 元素字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `rank` | number | 排名 |
| `product_id` | string | 商品 ID |
| `category` | string | 类别 |
| `total_sold` | number | 区间总销量 |
| `avg_daily` | number | 日均销量 |
| `current_inventory` | number | 当前库存 |
| `inventory_date` | string \| null | 库存日期 |
| `in_transit_inventory` | number | 在途库存 |
| `coverage_days` | number \| null | 库存可覆盖天数 |
| `inventory_status` | string | 库存状态 |

**后端实现**：`api/routes/ranking_routes.py:16` → `application.ranking_query.execute` → `api/application/ranking_query.py:28`。

---

### 3.8 补货建议

- **Method**：`GET`
- **Path**：`/api/replenishment`
- **前端调用**：`api.getReplenishment(storeId, category?)` → `app/src/services/api.ts:140`
- **说明**：为指定门店（及类别）下所有商品计算补货建议，按建议补货量降序、商品 ID 升序排列。注意：补货建议基于离线预计算的 90 天数据，因此响应 `context.time_range` 固定为 `"90d"`，不受 URL `range` 参数影响。

**查询参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `store_id` | string | 否 | `S001` | 门店 ID |
| `category` | string | 否 | - | 类别过滤 |

**响应 `data` 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `suggestions` | array | 补货建议列表 |

**`ReplenishmentSuggestion` 元素字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `product_id` | string | 商品 ID |
| `category` | string | 类别 |
| `current_inventory` | number | 当前库存 |
| `in_transit_inventory` | number | 在途库存 |
| `inventory_date` | string \| null | 库存日期 |
| `lead_time_k` | number | 提前期 K |
| `lead_time_k_source` | string | `estimated` / `default` |
| `forecast_7d` | array | 未来 7 天每日预测 |
| `forecast_k_total` | number | 提前期 K 内预测总需求 |
| `safety_stock` | number | 安全库存 |
| `suggested_replenishment` | number | 建议补货量 |
| `inventory_status` | string | 库存状态 |
| `status` | string | 计算状态 |
| `message` | string \| null | 状态说明 |

**后端实现**：`api/routes/replenishment_routes.py:15` → `application.replenishment_query.execute` → `api/application/replenishment_query.py:27`。

---

### 3.9 提交补货订单（当前为前端 Mock）

- **前端调用**：`api.submitOrder(draft)` → `app/src/services/api.ts:166`
- **说明**：当前为前端本地 Mock，模拟异步提交并返回生成的订单号。后端尚未提供真实订单提交接口。

**请求参数 `OrderDraft`**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `store_id` | string | 是 | 门店 ID |
| `product_id` | string | 是 | 商品 ID |
| `quantity` | number | 是 | 下单数量 |
| `note` | string | 否 | 备注 |

**响应 `OrderSubmissionResult`**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `orderId` | string | 生成的订单号 |

> 后续如需真实下单能力，需在后端新增 `POST /api/orders` 接口，并将 `submitOrder` 替换为真实 POST 请求。

---

## 4. 前端 API 服务层

统一封装位于 `app/src/services/api.ts`，主要能力：

- 默认请求超时：`15s`。
- 所有 GET 接口函数均接受可选的 `signal?: AbortSignal` 参数，用于组件卸载或请求竞态时取消请求；内部通过 `AbortController` 合并外部 signal 与 15 秒超时。
- 自动拼接查询参数，过滤空值。
- 统一解析 `{context, data}` 响应结构。
- 将后端 `error` 字段转换为异常抛出。

### 4.1 函数与后端端点映射

| 前端函数 | 后端端点 | 主要用途 |
|----------|----------|----------|
| `getStores()` | `GET /api/stores` | 门店列表 |
| `getCategories()` | `GET /api/categories` | 类别列表 |
| `getProducts(storeId, category)` | `GET /api/products` | 商品列表 |
| `getOverview(storeId, range, category)` | `GET /api/overview` | Dashboard 概览 |
| `getRankings(storeId, range, category, inventoryStatus, topN, bottomN)` | `GET /api/rankings` | 商品排名 |
| `getReplenishment(storeId, category)` | `GET /api/replenishment` | 补货建议 |
| `getProductDetail(productId, storeId, range)` | `GET /api/products/{product_id}` | 商品详情 |
| `submitOrder(draft)` | **前端 Mock** | 提交补货订单 |

### 4.2 前端类型

主要类型定义位于：

- `app/src/types/api.ts`：`AnalysisContext`、`ApiResponse`、`ApiError`、`TimeRange`、`InventoryStatusKey`
- `app/src/types/sales.ts`：`Store`、`Product`、`DailySales`
- `app/src/types/inventory.ts`：`RankingItem`、`RankingData`、`InventorySummary`
- `app/src/types/replenishment.ts`：`ReplenishmentData`、`ReplenishmentSuggestion`、`ProductDetail`、`ForecastResult`
- `app/src/types/order.ts`：`OrderDraft`、`OrderSubmissionResult`

---

## 5. 后端关键业务逻辑

### 5.1 数据来源

- 后端启动时从 `data/sales_data.csv` 加载原始销售与库存数据。
- `CsvRepository` 负责原始 CSV 读取；`NormalizedRepository` 统一列名并提供标准化 DataFrame。
- 销量预测、预测误差统计、补货建议均已通过离线批处理预计算，分别存储在 `mock_data/fact_forecast.csv`、`mock_data/fact_forecast_error_stats.csv`、`mock_data/fact_daily_replenishment.csv`。
- 在线 API 通过 `ForecastRepository` 与 `ReplenishmentRepository` 直接读取这些预计算表，不再实时执行预测或补货公式。
- 数据加载失败会导致服务启动异常，`/api/health` 中 `data_loaded` 返回 `false`。

### 5.2 配置

业务配置来自 `config/business.yaml`：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `default.store_id` | `S001` | 默认门店 |
| `default.time_range_days` | `90` | 默认时间范围 |
| `ranking.top_n` | `5` | 默认 Top 排名数 |
| `ranking.bottom_n` | `5` | 默认 Bottom 排名数 |
| `lead_time.fallback_days` | `2` | 提前期无数据时的回退天数 |
| `safety_stock.service_level_z` | `2.33` | 安全库存服务水平系数 |
| `inventory_status.critical_less_than` | `2` | 紧缺库存阈值（天） |
| `inventory_status.low_less_than` | `4` | 低库存阈值（天） |
| `inventory_status.normal_less_than_or_equal` | `7` | 正常库存上限（天） |

### 5.3 库存状态规则

按 `coverage_days`（可覆盖天数）划分：

- `< 2`：`critical`（紧缺）
- `< 4`：`low`（低库存）
- `<= 7`：`normal`（正常）
- `> 7`：`sufficient`（充足）
- 无法计算时：`undetermined`

### 5.4 补货建议计算逻辑

补货建议量已在离线批处理中完成预计算，在线 API 直接读取 `fact_daily_replenishment.csv`。

预计算公式：

```
suggested_replenishment = max(0, ceil(forecast_k_total + safety_stock - current_inventory - in_transit_inventory))
```

- `forecast_k_total`：提前期 K 天内的预测总需求，来自 `fact_forecast.csv`。
- `safety_stock`：基于预计算误差标准差 `error_std` 与服务水平系数 `Z=2.33` 计算，来自 `fact_forecast_error_stats.csv`。
- `current_inventory`、`in_transit_inventory`：离线计算的销售后库存与在途库存。

在线端点 `/api/replenishment` 与 `/api/products/{product_id}` 中的 `replenishment` 字段均直接返回预计算结果；若预计算数据缺失，则返回 `forecast_unavailable` / `insufficient_data` 状态，不再在线重算。

---

## 6. 测试覆盖

后端集成与单元测试位于 `api/test_api.py`，覆盖：

- 基础设施：`CsvRepository`、`NormalizedRepository`、`ConfigRepository`
- 领域服务：库存、提前期、安全库存、补货、排名
- HTTP 端点：`/api/overview`、`/api/rankings`、`/api/replenishment`、`/api/products`、`/api/products/{id}`
- 跨端点一致性：商品详情与补货建议、排名与详情库存状态的一致性

运行方式：

```bash
conda activate dev
python api/test_api.py
```

---

## 7. 附录：状态码与错误码

| 错误码 | 触发场景 | HTTP 状态 |
|--------|----------|-----------|
| `INVALID_RANGE` | `range` 不是 `7d/30d/90d/180d/all` | `400` |
| `INVALID_PARAMETER` | `top_n`/`bottom_n` 非正整数 | `400` |
| `INVALID_INVENTORY_STATUS` | `inventory_status` 不在枚举范围内 | `400` |
| `INTERNAL_ERROR` | 服务端未捕获异常 | `500` |

---

## 8. 变更记录

| 日期 | 内容 |
|------|------|
| 2026/07/12 | 整理新版 `/api` 接口，统一 `{context, data}` 响应结构，新增本文档。 |
| 2026/07/12 | 销量预测与补货建议改为读取离线预计算表（`fact_forecast.csv`、`fact_forecast_error_stats.csv`、`fact_daily_replenishment.csv`），在线 API 不再实时计算。 |
