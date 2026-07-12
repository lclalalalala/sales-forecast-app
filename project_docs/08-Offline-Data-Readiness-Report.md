# 离线计算数据完备性检查报告

> 检查日期：2026/07/12
> 检查范围：`mock_data/`、`data/processed_data/`、`api/infrastructure/`、`api/application/`、`api/domain/`
> 检查依据：`project_docs/07-API.md`、`project_docs/03-Offline-data-process.md`

## 1. 执行摘要

离线计算产物本身**已经生成且基本完整**，但存在**两个严重问题**导致当前 API 无法按设计消费这些预计算数据：

1. **路径不一致**：API 默认从 `data/processed_data/` 读取离线表，但该目录除数据质量报告外几乎为空；完整的离线产物实际在 `mock_data/` 中。
2. **接口未消费离线表**：`/api/rankings`、`/api/overview` 仍基于原始 `sales_data.csv` 实时计算，未使用 `fact_product_sales_summary.csv` / `fact_daily_sales_metrics.csv`。

此外，`mock_data/fact_forecast.csv` 末尾 3 个预测原点（2024-01-28 ~ 2024-01-30）共 2,100 行的预测上下界为 `NaN`，导致 `verify_demo_data.py` 数据质量校验失败。

## 2. 离线产物核对

### 2.1 文件完整性

| 文件 | `mock_data/` | `data/processed_data/` | 说明 |
|---|---|---|---|
| `data_quality_report.json/.csv` | ✓ | ✓ | 数据质量报告 |
| `dim_store.csv` | ✓ | ✗ | 门店维度表 |
| `dim_product.csv` | ✓ | ✗ | 商品维度表 |
| `fact_daily_inventory_sales.csv` | ✓ | ✗ | 每日库存销售事实表 |
| `fact_lead_time.csv` | ✓ | ✗ | 提前期 K 维度表 |
| `fact_forecast.csv` | ✓ | ✗ | 7 天滚动预测表 |
| `fact_forecast_error_stats.csv` | ✓ | ✗ | 预测误差标准差表 |
| `fact_daily_replenishment.csv` | ✓ | ✗ | 每日补货推荐表 |
| `fact_daily_sales_metrics.csv` | ✓ | ✗ | 门店-日期-类别销量汇总 |
| `fact_product_sales_summary.csv` | ✓ | ✗ | 商品多窗口销量汇总 |

### 2.2 数据覆盖范围

- **门店**：5 家（S001 ~ S005）
- **商品**：20 个（P0001 ~ P0020）
- **日期范围**：2022-01-01 ~ 2024-01-30，共 760 天
- **预测原点**：2022-01-07 ~ 2024-01-30，共 754 天

### 2.3 数据量

| 文件 | 数据行数 | 大小 |
|---|---|---|
| `fact_forecast.csv` | 527,800 | ~67.8 MiB |
| `fact_daily_replenishment.csv` | 76,000 | ~11.5 MiB |
| `fact_forecast_error_stats.csv` | 75,400 | ~7.0 MiB |
| `fact_daily_inventory_sales.csv` | 76,000 | ~3.8 MiB |
| `fact_daily_sales_metrics.csv` | 22,040 | ~727 KiB |
| `fact_product_sales_summary.csv` | 500 | ~37 KiB |
| `fact_lead_time.csv` | 100 | ~8.5 KiB |

### 2.4 数据质量校验结果

- `verify_outputs.py data/processed_data`：**通过**（因为该目录只有报告文件，无事实表需要校验）。
- `verify_demo_data.py`：**失败**，失败项为 `lower_bound <= forecast_units_sold`。

失败原因分析：

```text
总行数: 527,800
lower_bound NaN 数量: 2,100
lower_bound > forecast 数量: 0
```

`lower_bound` 的 2,100 个 `NaN` 集中在 `forecast_origin_date` 为 2024-01-28、2024-01-29、2024-01-30 的预测中，对应 `forecast_date` 超出了有效计算窗口。这些行的 `status` 标记为 `ready`，但上下界缺失，导致校验脚本中的 `le` 比较返回 `False`。

## 3. API 数据源一致性

### 3.1 Repository 读取路径

| Repository | 默认读取目录 | 读取文件 |
|---|---|---|
| `ForecastRepository` | `data/processed_data/` | `fact_forecast.csv`、`fact_forecast_error_stats.csv` |
| `ReplenishmentRepository` | `data/processed_data/` | `fact_daily_replenishment.csv` |
| `CsvRepository` / `NormalizedRepository` | `data/` | `sales_data.csv` |

### 3.2 各端点实际数据源

| 接口 | 设计数据源 | 实际数据源 | 级别 |
|---|---|---|---|
| `/api/replenishment` | `fact_daily_replenishment.csv` | `data/processed_data/`（空） | **严重** |
| `/api/products/{id}` 中 forecast | `fact_forecast.csv` | `data/processed_data/`（空） | **严重** |
| `/api/products/{id}` 中 replenishment | `fact_daily_replenishment.csv` | `data/processed_data/`（空） | **严重** |
| `/api/rankings` | `fact_product_sales_summary.csv` | `sales_data.csv` 实时计算 | **严重** |
| `/api/overview` | `fact_daily_sales_metrics.csv` + `fact_product_sales_summary.csv` | `sales_data.csv` 实时计算 | **严重** |
| `LeadTimeService.estimate_k` | `fact_lead_time.csv` | `sales_data.csv` 实时估计 | 中等 |
| `/api/replenishment` 的 `forecast_7d` | `fact_forecast.csv` | 硬编码 `[]` | 中等 |

### 3.3 未使用的离线产物

以下离线表已生成，但当前 API 未消费：

- `dim_store.csv`
- `dim_product.csv`
- `fact_daily_inventory_sales.csv`
- `fact_lead_time.csv`
- `fact_daily_sales_metrics.csv`
- `fact_product_sales_summary.csv`

## 4. 配置一致性

| 配置项 | `config/business.yaml` | `mock_data/generate_demo_data.py` | 实际 `mock_data/` 输出 | 结论 |
|---|---|---|---|---|
| `safety_stock.service_level_z` | 2.33 | 2.33 | 2.33 | 一致 |
| `error_window_days` | 30 | 90 | 90 | **不一致** |
| `inventory_status.critical_less_than` | 2 | 2 | 2 | 一致 |
| `inventory_status.low_less_than` | 4 | 4 | 4 | 一致 |
| `inventory_status.normal_less_than_or_equal` | 7 | 7 | 7 | 一致 |
| `lead_time.fallback_days` | 2 | 2 | 2 | 一致 |

`business.yaml` 中 `safety_stock.error_window_days` 为 30，但离线生成脚本和实际输出都使用 90 天窗口。这与 `project_docs/03-Offline-data-process.md` 3.2 节“过去 90 天”的描述一致，但配置文件未同步更新。

## 5. 关键问题与影响

### 5.1 严重问题

1. **API 读不到预计算数据**
   - `data/processed_data/` 中缺少 `fact_forecast.csv` 和 `fact_daily_replenishment.csv`。
   - `/api/replenishment` 会返回空 `suggestions[]`。
   - `/api/products/{id}` 的 `forecast` 会进入 `forecast_unavailable`，`replenishment` 会进入 `unavailable` 状态。

2. **排名与概览未使用离线预计算表**
   - `/api/rankings`、`/api/overview` 仍实时聚合原始 CSV。
   - 与“在线 API 只做最小计算、读取预计算表”的设计意图不符。
   - 性能较差，且结果可能与离线表不一致。

### 5.2 中等问题

3. **`LeadTimeService` 在线重新估计 K**
   - `fact_lead_time.csv` 已离线生成，但 API 未读取。
   - 在线估计结果可能与离线表不一致。

4. **`/api/replenishment` 的 `forecast_7d` 为空数组**
   - `ReplenishmentRepository._row_to_dict` 中硬编码 `forecast_7d: []`。
   - 前端补货列表页无法展示 7 天预测趋势。

### 5.3 轻微问题

5. **`mock_data/fact_forecast.csv` 末尾预测区间缺失**
   - 末尾 3 个原点共 2,100 行 `lower_bound` / `upper_bound` 为 `NaN`。
   - 不影响点预测，但影响预测区间展示。

6. **`fact_forecast_error_stats.csv` 缺少 `horizon` 列**
   - `offline_calculation/steps/build_error_stats.py` 会输出 `horizon` 列，但 `mock_data/` 中实际文件缺少该列。
   - 当前 API 未读取该表，暂无功能影响。

## 6. 修复建议

### 6.1 必须修复（恢复功能）

1. **统一离线数据读取路径**
   - **方案 A（最小改动）**：将 `ForecastRepository` 与 `ReplenishmentRepository` 的默认目录从 `data/processed_data/` 改为 `mock_data/`，或改为可通过环境变量/配置指定。
   - **方案 B（架构正确）**：执行 `python -m offline_calculation`，让离线流程输出到 `data/processed_data/`，保持 API 路径不变。
   - **推荐**：先按方案 A 恢复 Demo 可用性；长期按方案 B，让离线计算成为启动前标准步骤。

2. **回填 `/api/replenishment` 的 `forecast_7d`**
   - 在 `replenishment_query.py` 中对每个 suggestion 调用 `forecast_repository.get_forecast(...)` 回填 7 天预测明细。

### 6.2 建议修复（对齐离线架构）

3. 让 `/api/rankings` 优先读取 `fact_product_sales_summary.csv`。
4. 让 `/api/overview` 优先读取 `fact_daily_sales_metrics.csv` 与 `fact_product_sales_summary.csv`。
5. 让 `LeadTimeService` 优先读取 `fact_lead_time.csv`，缺失时再回退在线估计。
6. 将 `config/business.yaml` 中 `safety_stock.error_window_days` 从 30 改为 90，与文档和实际数据一致。

### 6.3 可选优化

7. 重新生成 `mock_data/`，修复 `fact_forecast.csv` 末尾预测区间 `NaN` 和 `fact_forecast_error_stats.csv` 缺少 `horizon` 列的问题。
8. 将离线数据目录外部化为环境变量或配置项。
9. 更新 `api/test_api.py`，增加对 `forecast_7d` 长度、补货 suggestions 非空、排名/概览使用预计算表的断言。

## 7. 验证方式

### 7.1 静态验证

```bash
# 文件完整性
ls -la mock_data/fact_*.csv data/processed_data/fact_*.csv

# mock_data 数据质量校验
cd mock_data && python verify_demo_data.py

# processed_data 输出校验
cd ..
python offline_calculation/verify_outputs.py data/processed_data

# 配置一致性检查
grep -E 'error_window_days|ERROR_WINDOW_DAYS' \
  config/business.yaml \
  offline_calculation/config.py \
  mock_data/generate_demo_data.py
```

### 7.2 动态端点验证

```bash
# 启动后端
cd api && python app.py &

# 补货接口
curl -s "http://localhost:8999/api/replenishment?store_id=S001" | python -m json.tool

# 商品详情
curl -s "http://localhost:8999/api/products/P0001?store_id=S001&range=90d" | python -m json.tool

# 排名与概览
curl -s "http://localhost:8999/api/rankings?store_id=S001&range=90d" | python -m json.tool
curl -s "http://localhost:8999/api/overview?store_id=S001&range=90d" | python -m json.tool
```

### 7.3 验收标准

- `/api/replenishment` 返回 20 条 suggestions（与商品数一致）。
- 每个 suggestion 的 `forecast_7d` 长度为 7。
- `/api/products/{id}` 的 `forecast.daily_forecast_units_sold` 长度为 7，`replenishment.status` 为 `ready`。
- `/api/rankings` 与 `/api/overview` 返回非空，且与离线预计算表结果一致（阶段 2 完成后）。
- `python api/test_api.py` 全部通过。

---

## 8. 结论

离线计算链路本身已打通，产物覆盖完整，但当前 API 因**路径不一致**和**部分接口未消费离线表**而无法真正使用这些预计算数据。建议先通过最小改动恢复 `/api/replenishment` 和 `/api/products/{id}` 的功能，再逐步将 `/api/rankings`、`/api/overview`、`LeadTimeService` 迁移到离线预计算表，最终实现“离线计算、在线只读”的架构目标。
