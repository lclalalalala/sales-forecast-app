# 零售门店库存与需求预测系统

基于 Kaggle 数据集 "Retail Store Inventory and Demand Forecasting" 构建的全栈数据分析应用，为零售门店提供销售趋势分析、需求预测和智能补货建议。

## 功能特性

### 数据概览页（含多维筛选）
- **多维筛选**: 门店 / 时间范围(7/30/90/180/全部) / 类别 / 库存状态
- KPI 卡片（总销量、日均销量、商品数、平均库存）
- 销售趋势折线图（实际销量 + 需求量）
- Top 5 畅销品 / Bottom 5 滞销品排名（含库存状态标签）

### 补货建议页
- 自动计算 Top 5 畅销品未来7天建议补货量
- 7天预测需求迷你图 + 库存状态标识
- 汇总卡片（预测日期 / 需补货商品数 / 建议总补货量）

### 商品详情页（含类别联动筛选）
- **类别联动筛选**: 选择类别后商品下拉自动过滤
- 历史销售趋势三线图（销量/需求/库存）
- 当前库存水位颜色标识（充足/正常/偏低/紧缺）
- 未来7天预测需求柱状图 + 补货建议量

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Tailwind CSS + Recharts(深色主题) |
| 后端 | Python Flask + Pandas + NumPy |
| 算法 | 集成预测模型（近期均值 + 星期模式 + 趋势调整 + 季节因子）|
| 设计 | WattVision 深色主题设计系统 |
| 测试 | unittest（40个测试用例） |

## 快速开始

### 1. 环境要求
- Python 3.8+
- Node.js 18+

### 2. 启动后端

```bash
cd api/
pip install -r requirements.txt
python app.py
# 后端运行在 http://localhost:5000
```

### 3. 启动前端

```bash
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

### 4. 打包为桌面应用（可选）

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

| 路径 | 说明 |
|------|------|
| GET /api/stores | 门店列表 |
| GET /api/products | 商品列表 |
| GET /api/sales/trend | 销售趋势 |
| GET /api/sales/ranking | 商品排名 |
| GET /api/replenishment | 补货建议 |
| GET /api/products/detail | 商品详情 |
| GET /api/dashboard/kpi | KPI汇总 |

## 项目文档

| # | 文档 | 路径 |
|---|------|------|
| 1 | 架构设计文档 | docs/01_Architecture_Design.md |
| 2 | 验收文档 | docs/02_Acceptance_Document.md |
| 3 | 项目文档(安装部署说明) | docs/03_Project_Documentation.md |
| 4 | User Story需求(含多维筛选) | docs/04_User_Stories.md |
| 5 | User Story Review | docs/05_User_Story_Review.md |
| 6 | BDD规范(含筛选Scenario) | docs/06_BDD_Specification.md |
| 7 | 架构Review | docs/07_Architecture_Review.md |
| 8 | 技术规范 | docs/08_Technical_Specification.md |
| 9 | Code Review报告 | docs/09_Code_Review_Report.md |
| 10 | 多维筛选功能设计 | docs/10_Multi_Dimensional_Filter.md |
| 11 | 前端设计规范(深色主题) | docs/11_Frontend_Design_Spec.md |

## 测试

```bash
cd api/
python test_api.py
```

**40个测试用例全部通过**，包括：
- 14个 DataService 单元测试
- 10个 ForecastService 单元测试
- 9个 Flask HTTP API 集成测试
- 7个边界条件测试

## 项目结构

```
├── data/              # 数据集 (sales_data.csv)
├── api/               # 后端 (Flask)
│   ├── services/      # 数据服务 + 预测服务
│   └── test_api.py    # 40个测试用例
├── src/               # 前端 (React)
│   ├── types/         # TypeScript类型
│   ├── services/      # API封装
│   ├── components/    # 公共组件
│   └── pages/         # 页面组件
└── docs/              # 项目文档 (11份)
```

## 预测算法

采用集成预测模型，结合四种方法的加权平均：

```
预测值 = (近期均值 * 0.3 + 星期模式 * 0.4) * 趋势调整 * 0.7
       + 近期均值 * 0.3 * 季节因子

补货量 = max(0, 7天总预测 * 1.2 - 当前库存)
```

## 敏捷开发流程

本项目遵循完整的敏捷开发流程：

1. **需求分析** → User Story文档（12个Story，3个Epic）
2. **需求Review** → 确认无过度设计，排除6项非必要功能
3. **BDD规范** → 13个Scenario，Given-When-Then格式
4. **架构Review** → 确认架构完整覆盖所有Story
5. **技术规范** → 分层测试规范（单元/集成/边界）
6. **编码实现** → 前后端代码实现
7. **Code Review** → 发现并修复3个问题
8. **测试验证** → 40个测试全部通过

## License

MIT
