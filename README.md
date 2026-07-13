# 零售门店库存与需求预测系统

基于 Kaggle 数据集 "Retail Store Inventory and Demand Forecasting" 构建的全栈数据分析应用，为零售门店提供销售趋势分析、需求预测和智能补货建议。

系统采用 **「离线预计算 + 在线只读服务」** 架构：所有重活（数据清洗、需求预测、补货计算）都在**离线批处理管道**中完成并落地为 CSV，在线 Flask 服务只是一层薄薄的**只读查询层**，前端为 React 单页应用。

## 系统架构

```
data/sales_data.csv                原始 Kaggle 数据集
        │
        ▼
offline_calculation/  ──调用──▶  forecast/           离线批处理管道 + 预测引擎
（8 步 pandas 管道）             （walk-forward 预测）
        │
        ▼
data/processed_data/*.csv          预计算结果（dim_* / fact_* / 数据质量报告）
        │
        ▼
api/  (Flask 只读薄层)             仓储 + 查询蓝图，启动时把 CSV 载入内存 DataFrame
        │  GET /api/*  →  { context, data }
        ▼
app/  (React + Vite 前端)
```

要点：
- **无在线预测、无定时任务/cron**。离线管道需**手动运行** `python -m offline_calculation` 重新生成 `data/processed_data/`。
- 全链路以基准日 `as_of_date`（= `max(date) - offset`，默认 offset=0 即最新日期）对齐；每个 API 响应的 `context` 都会回传该基准日与实际数据区间。
- 后端不做业务计算，只负责按筛选条件查询预计算表并组装响应，因此响应快、逻辑简单、可测试性强。

## 离线计算

离线部分是本系统的核心，位于两个顶层模块：

| 模块 | 职责 |
|------|------|
| `offline_calculation/` | 批处理管道编排（`cli.py` / `pipeline.py` / `steps/` / `config.py` / `verify_outputs.py`）|
| `forecast/` | 需求预测引擎（`calculator.py` / `batch.py` / `errors.py`），供管道调用 |

管道（`pipeline.py` → `run_pipeline`）按序执行约 8 个步骤（见 `offline_calculation/steps/`）：

1. `load_validate` — 加载并校验原始 CSV，产出数据质量报告
2. `build_fact` — 构建每日库存/销售明细事实表
3. 构建维度表 `dim_store` / `dim_product`
4. `build_sales_metrics` — 门店×类别每日销售指标
5. `build_product_summary` — 商品销售汇总
6. `estimate_lead_time` — 估计补货提前期 K
7. `build_forecast` + `build_error_stats` — walk-forward 未来 7 天预测 + 误差统计（预测区间）
8. `build_replenishment` — 基于提前期与安全库存计算每日补货建议

运行方式：

```bash
conda activate dev
python -m offline_calculation \
  [--as-of-date YYYY-MM-DD] \  # 计算基准日，默认取数据最新日期
  [--input data/sales_data.csv] \
  [--output data/processed_data] \
  [--config config/business.yaml]

# 校验产出
python offline_calculation/verify_outputs.py
```

产出表（`data/processed_data/`）：

| 文件 | 内容 |
|------|------|
| `dim_store.csv` / `dim_product.csv` | 门店 / 商品维度 |
| `fact_daily_inventory_sales.csv` | 每日库存与销量明细 |
| `fact_daily_sales_metrics.csv` | 门店×类别每日销售指标 |
| `fact_product_sales_summary.csv` | 商品销售汇总 |
| `fact_lead_time.csv` | 各商品补货提前期估计 |
| `fact_forecast.csv` / `fact_forecast_error_stats.csv` | 7 天需求预测 + 误差/预测区间 |
| `fact_daily_replenishment.csv` | 每日补货建议 |
| `data_quality_report.csv/.json` | 数据质量报告 |

所有业务参数集中在 `config/business.yaml`：排名 Top/Bottom N、提前期上下限、安全库存服务水平 Z 值、预测窗口、库存状态阈值（按可覆盖天数划分 紧缺/偏低/正常/充足）等。

参考文档：`project_docs/03-Offline-data-process.md`、`05-sales_forecast.md`、`06-Replenishment_Calculation_Guide.md`、`08-Offline-Data-Readiness-Report.md`、`formular_and_config.md`。

## 功能特性

### 数据概览页（含多维筛选）
- **多维筛选**: 门店 / 时间范围(7/30/90/180/全部) / 类别 / 库存状态
- KPI 卡片（日均销量、总库存、低库存/紧缺商品数等）
- 销售趋势折线图（实际销量 + 需求量）
- Top 5 畅销品 / Bottom 5 滞销品排名（含库存状态标签）

### 补货建议页
- 按门店列出补货建议，携带未来 7 天预测（`forecast_7d`），按建议补货量排序
- 7 天预测需求迷你图 + 库存状态标识
- 汇总信息（基准日期 / 需补货商品数 / 建议总补货量）

### 商品详情页（含类别联动筛选）
- **类别联动筛选**: 选择类别后商品下拉自动过滤
- 历史销售趋势三线图（销量/需求/库存）
- 当前库存水位颜色标识（充足/正常/偏低/紧缺）
- 未来 7 天预测需求柱状图 + 补货建议量

> 前端页面位于 `app/src/pages/`：Dashboard / Ranking / Replenishment / ProductDetail / Order / Help / TechnicalDoc。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite 7 + Tailwind CSS 3 + Recharts + Radix UI/shadcn + react-router v7 |
| 在线后端 | Python Flask 3 + Pandas + NumPy（只读薄层：仓储 + 查询蓝图） |
| 离线计算 | Pandas + NumPy + scikit-learn（`offline_calculation/` + `forecast/`）|
| 预测算法 | walk-forward 集成预测 + 误差统计（预测区间），基于提前期与安全库存计算补货 |
| 设计 | 深色主题设计系统（shadcn/ui）|
| 测试 | 后端 unittest/pytest（`tests/`，77 个测试函数）+ 前端 Vitest |

## 快速开始

### 1. 环境要求
- Python 3.8+（推荐 `conda activate dev`）
- Node.js 18+

### 2. 生成离线数据（首次必需）

在线服务依赖 `data/processed_data/` 下的预计算表，首次运行前需先生成：

```bash
conda activate dev
python -m offline_calculation
```

### 3. 启动后端

```bash
cd api/
pip install -r requirements.txt
python app.py
# 后端运行在 http://localhost:8999
```

### 4. 启动前端

```bash
cd app/
npm install
npm run dev
# 前端运行在 http://localhost:3000
```

> 也可用根目录一键脚本同时启动前后端：`./run.sh`（conda dev 环境，后端 8999 / 前端 3000）。

### 5. 打包为桌面应用（可选）

将前后端打包为 macOS / Windows 原生应用，双击即用：

```bash
conda activate dev
pip install -r requirements-desktop.txt
cd app && npm install && cd ..

# macOS
./build_mac.sh          # 产物：dist/库存预测系统.app

# Windows
build_win.bat           # 产物：dist\库存预测系统.exe
```

详见 [project_docs/09-Desktop-Packaging.md](project_docs/09-Desktop-Packaging.md)。

## API 接口

所有接口均为 GET，统一返回 `{ context, data }` 响应信封；`context` 携带 `store_id / category / time_range / as_of_date / actual_data_start / actual_data_end`。

| 路径 | 说明 |
|------|------|
| GET /api/health | 健康检查（数据加载状态）|
| GET /api/stores | 门店列表 |
| GET /api/categories | 类别列表 |
| GET /api/overview | 数据概览（KPI + 趋势 + Top/Bottom）|
| GET /api/rankings | 商品排名（支持类别 / 库存状态筛选）|
| GET /api/products | 商品列表 |
| GET /api/products/&lt;product_id&gt; | 商品详情（历史序列 + 7 天预测 + 补货）|
| GET /api/replenishment | 门店补货建议（含 forecast_7d）|

详细字段见 [project_docs/07-API.md](project_docs/07-API.md)。

## 项目结构

```
├── data/
│   ├── sales_data.csv          # 原始数据集
│   └── processed_data/         # 离线预计算产出 (dim_* / fact_* / 质量报告)
├── config/
│   └── business.yaml           # 业务参数配置
├── offline_calculation/        # 离线批处理管道
│   ├── cli.py / pipeline.py / config.py / verify_outputs.py
│   └── steps/                  # load_validate / build_fact / build_forecast ...
├── forecast/                   # 预测引擎 (calculator / batch / errors)
├── api/                        # 在线后端 (Flask 只读薄层)
│   ├── app.py                  # 入口 + 元数据路由 (:8999)
│   ├── infrastructure/         # 仓储层（读取 processed_data CSV）
│   ├── queries/                # 查询蓝图 (overview / ranking / product_detail / replenishment)
│   └── schemas/                # 请求校验 / 响应信封 / DTO
├── app/                        # 前端 (React + Vite)
│   └── src/                    # pages / components / services / types / state / hooks / lib
├── tests/                      # 测试 (test_api.py / test_repositories.py / offline_calculation/ / forecast/)
├── project_docs/               # 项目文档
├── run.sh                      # 一键启动前后端
└── build_mac.sh / build_win.bat / desktop.py   # 桌面打包
```

## 测试

```bash
# 后端 / 离线计算（顶层 tests/，共 77 个测试函数）
conda activate dev
pytest tests/

# 前端
cd app/
npm test
```

覆盖范围：
- `tests/test_api.py` — Flask HTTP API 与基础设施集成测试
- `tests/test_repositories.py` — 仓储层单元测试
- `tests/test_resource_path.py` — 资源路径 / 打包路径解析
- `tests/offline_calculation/` — 离线管道各步骤测试
- `tests/forecast/` — 预测引擎测试
- `app/src/**/*.test.tsx` — 前端组件与页面测试（Vitest）

## 项目文档

| 文档 | 路径 |
|------|------|
| 架构设计 | project_docs/01_Architecture_Design.md · project_docs/01-Architecture-new.md |
| 前端规范 | project_docs/02-Frontend-spec.md |
| 离线数据处理 | project_docs/03-Offline-data-process.md |
| 项目文档（安装部署） | project_docs/03_Project_Documentation.md |
| User Story 需求 | project_docs/04_User_Stories.md |
| 销售预测算法 | project_docs/05-sales_forecast.md |
| 补货计算指南 | project_docs/06-Replenishment_Calculation_Guide.md |
| API 文档 | project_docs/07-API.md |
| 离线数据就绪报告 | project_docs/08-Offline-Data-Readiness-Report.md |
| 桌面打包 | project_docs/09-Desktop-Packaging.md |
| 公式与配置 | project_docs/formular_and_config.md |
| 数据字段说明 | project_docs/000-data_explain.md |
| 开发指南 | project_docs/dev_guide/ |

## 预测与补货算法

预测在**离线**阶段由 `forecast/` 引擎以 walk-forward 方式生成：对每个 (门店, 商品) 逐日滚动预测未来需求，并基于近期误差估计预测区间（`fact_forecast_error_stats.csv`）。

补货量在 `offline_calculation/steps/build_replenishment.py` 中计算，结合预测需求、补货提前期（`estimate_lead_time`）与安全库存（服务水平 Z 值），得出每日建议补货量。具体公式与参数以 `config/business.yaml` 为准，详见 [project_docs/06-Replenishment_Calculation_Guide.md](project_docs/06-Replenishment_Calculation_Guide.md) 与 [project_docs/05-sales_forecast.md](project_docs/05-sales_forecast.md)。

## License

MIT
