# 零售门店库存与需求预测系统 - 架构设计文档

## 1. 项目概述

基于 Kaggle 数据集 "Retail Store Inventory and Demand Forecasting" 构建全栈数据分析应用，为零售门店提供销售趋势分析、需求预测和智能补货建议。

## 2. 系统架构

### 2.1 整体架构 (分层架构)

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  数据概览页   │ │  补货建议页   │ │  商品详情页   │           │
│  │  (Dashboard) │ │  (Replenish) │ │  (Product)   │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│       │ Recharts        │ Recharts       │ Recharts            │
│       │ KPI Cards       │ Data Table     │ Trend Chart         │
│  ┌──────────────────────────────────────────────────────┐     │
│  │          React + TypeScript + Tailwind CSS            │     │
│  │          shadcn/ui + Recharts + React Router          │     │
│  └──────────────────────────────────────────────────────┘     │
└──────────────────────────┬────────────────────────────────────┘
                           │ HTTP REST API (JSON)
┌──────────────────────────┴────────────────────────────────────┐
│                        网关层 (API Layer)                     │
│                    Flask REST API Server                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ /api/stores │ │ /api/sales  │ │ /api/replenishment      │ │
│  │ /api/products│ │ /api/trends │ │ /api/forecast           │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────┴────────────────────────────────────┐
│                    服务层 (Service Layer)                      │
│  ┌──────────────────────┐ ┌────────────────────────────────┐ │
│  │   DataService        │ │   ForecastService              │ │
│  │   - load_data()      │ │   - predict_next_7_days()      │ │
│  │   - get_store_data() │ │   - calculate_replenishment()  │ │
│  │   - get_product_list()│ │   - get_feature_engineering()  │ │
│  └──────────────────────┘ └────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┴────────────────────────────────────┐
│                    数据层 (Data Layer)                         │
│              sales_data.csv (Kaggle Dataset)                   │
│     ┌─────────────────────────────────────────────────┐       │
│     │  76,000 rows × 16 columns                      │       │
│     │  Date | Store | Product | Category | Inventory  │       │
│     │  Units Sold | Demand | Price | Discount | ...   │       │
│     └─────────────────────────────────────────────────┘       │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | React 19 + TypeScript | UI框架 |
| 样式 | Tailwind CSS + shadcn/ui | 组件库和样式 |
| 图表 | Recharts | 数据可视化 |
| 路由 | React Router v7 | 页面路由 |
| 后端 | Python Flask | REST API 服务 |
| 算法 | NumPy + Pandas + Scikit-learn | 数据处理和预测 |
| 数据 | CSV 文件 | 离线数据集 |
| 构建 | Vite | 前端构建工具 |

## 3. API 接口设计

### 3.1 门店相关接口

```
GET /api/stores
响应:
{
  "stores": [
    {"id": "S001", "name": "门店 S001", "region": "North"},
    ...
  ]
}
```

### 3.2 商品相关接口

```
GET /api/products?store_id=S001
响应:
{
  "products": [
    {"id": "P0001", "name": "P0001", "category": "Electronics"},
    ...
  ]
}
```

### 3.3 销售趋势接口

```
GET /api/sales/trend?store_id=S001&days=90
响应:
{
  "daily_sales": [
    {"date": "2023-11-01", "units_sold": 120, "demand": 135},
    ...
  ],
  "summary": {
    "total_units_sold": 15000,
    "avg_daily_sales": 167.5,
    "growth_rate": 0.05
  }
}
```

### 3.4 Top/Bottom 商品接口

```
GET /api/sales/ranking?store_id=S001&days=90
响应:
{
  "top_5": [
    {"product_id": "P0003", "category": "Clothing", "total_sold": 8200, "avg_daily": 91.1},
    ...
  ],
  "bottom_5": [
    {"product_id": "P0019", "category": "Furniture", "total_sold": 3200, "avg_daily": 35.6},
    ...
  ]
}
```

### 3.5 补货建议接口

```
GET /api/replenishment?store_id=S001
响应:
{
  "store_id": "S001",
  "forecast_date": "2024-02-01",
  "top_5_products": [
    {
      "product_id": "P0003",
      "category": "Clothing",
      "current_inventory": 570,
      "predicted_demand_7d": [91.7, 84.9, 92.8, 89.8, 87.8, 90.7, 89.1],
      "total_predicted_demand": 626.8,
      "suggested_replenishment": 56.8,
      "confidence": "high"
    },
    ...
  ]
}
```

### 3.6 商品详情接口

```
GET /api/products/detail?store_id=S001&product_id=P0001&days=90
响应:
{
  "product_id": "P0001",
  "category": "Electronics",
  "current_inventory": 245,
  "price": 72.72,
  "historical_sales": [
    {"date": "2023-11-01", "units_sold": 102, "demand": 115, "inventory": 195},
    ...
  ],
  "forecast": {
    "next_7_days": [63.7, 68.7, 67.8, 69.2, 64.9, 66.6, 69.0],
    "total_predicted": 469.9,
    "suggested_replenishment": 224.9
  }
}
```

## 4. 数据模型

### 4.1 核心数据实体

```typescript
// Store 门店
interface Store {
  id: string;           // 门店ID (S001-S005)
  region: string;       // 区域
}

// Product 商品
interface Product {
  id: string;           // 商品ID (P0001-P0020)
  category: string;     // 类别
  price: number;        // 价格
}

// DailySales 每日销售记录
interface DailySales {
  date: string;         // 日期
  store_id: string;     // 门店ID
  product_id: string;   // 商品ID
  units_sold: number;   // 销售数量
  demand: number;       // 需求量
  inventory_level: number; // 库存水平
  price: number;        // 价格
  discount: number;     // 折扣
  promotion: boolean;   // 是否促销
}

// SalesTrend 销售趋势
interface SalesTrend {
  date: string;
  units_sold: number;
  demand: number;
}

// ProductRanking 商品排名
interface ProductRanking {
  product_id: string;
  category: string;
  total_sold: number;
  avg_daily: number;
}

// ReplenishmentSuggestion 补货建议
interface ReplenishmentSuggestion {
  product_id: string;
  category: string;
  current_inventory: number;
  predicted_demand_7d: number[];
  total_predicted_demand: number;
  suggested_replenishment: number;
  confidence: string;
}

// ProductDetail 商品详情
interface ProductDetail {
  product_id: string;
  category: string;
  current_inventory: number;
  price: number;
  historical_sales: DailySales[];
  forecast: {
    next_7_days: number[];
    total_predicted: number;
    suggested_replenishment: number;
  };
}
```

## 5. 预测算法设计

### 5.1 算法选型: 集成预测模型

采用多方法集成策略，结合以下三种方法的加权平均：

1. **近期均值法 (30%)**: 最近14天的平均需求量
2. **星期模式法 (40%)**: 历史同期（相同星期几）的平均需求量
3. **趋势调整**: 最近7天 vs 最近30天的趋势系数
4. **季节因子**: 同月份历史平均的的季节调整

### 5.2 预测公式

```
prediction = (recent_avg × 0.3 + dow_avg × 0.4) × trend_factor × 0.7 
           + recent_avg × 0.3 × seasonal_factor

where:
  recent_avg = mean(demand[last 14 days])
  dow_avg = mean(demand[same day-of-week, last 4 weeks])
  trend_factor = clip(mean(demand[last 7]) / mean(demand[last 30]), 0.7, 1.3)
  seasonal_factor = clip(mean(demand[same month]) / mean(demand[last 30]), 0.7, 1.3)
```

### 5.3 补货量计算公式

```
suggested_replenishment = max(0, total_predicted_demand × safety_factor - current_inventory)

where:
  safety_factor = 1.2 (20%安全库存缓冲)
  total_predicted_demand = sum(next_7_days_predictions)
```

## 6. 页面设计

### 6.1 数据概览页 (Dashboard)
- 顶部: 门店选择器 + KPI 卡片 (总销量、日均销量、活跃商品数)
- 中部: 过去3个月销售趋势折线图 (双轴: 销量 + 需求)
- 底部: 左右并排 - Top 5 畅销品 + Bottom 5 滞销品排名表格

### 6.2 补货建议页 (Replenishment)
- 顶部: 门店选择器 + 预测日期说明
- 中部: Top 5 畅销品补货建议表格
  - 商品ID、类别、当前库存
  - 未来7天每日预测需求量 (可视化迷你图)
  - 7天总预测需求、建议补货量
  - 置信度标识

### 6.3 商品详情页 (Product Detail)
- 顶部: 商品选择器 (门店 + 商品联动下拉)
- 左上: 商品基本信息卡片 (当前库存、价格、类别)
- 右上: 补货建议摘要
- 中部: 历史销售趋势图 (过去3个月，含销量/需求/库存三线)
- 底部: 未来7天预测需求柱状图

## 7. 项目目录结构

```
/mnt/agents/output/app/
├── src/                          # 前端代码
│   ├── components/               # 公共组件
│   │   ├── Layout.tsx            # 页面布局 (导航栏+内容区)
│   │   ├── StoreSelector.tsx     # 门店选择器
│   │   └── ProductSelector.tsx   # 商品选择器
│   ├── pages/                    # 页面组件
│   │   ├── DashboardPage.tsx     # 数据概览页
│   │   ├── ReplenishmentPage.tsx # 补货建议页
│   │   └── ProductDetailPage.tsx # 商品详情页
│   ├── services/                 # API 服务
│   │   └── api.ts                # 所有API调用
│   ├── types/                    # TypeScript 类型定义
│   │   └── index.ts              # 所有类型
│   ├── App.tsx                   # 主应用组件 (路由配置)
│   ├── main.tsx                  # 入口文件
│   └── index.css                 # 全局样式
├── api/                          # 后端代码 (Flask)
│   ├── app.py                    # Flask 应用入口
│   ├── services/                 # 服务层
│   │   ├── data_service.py       # 数据加载与查询
│   │   └── forecast_service.py   # 预测算法
│   └── utils/                    # 工具函数
│       └── helpers.py            # 辅助函数
├── data/                         # 数据文件
│   └── sales_data.csv            # Kaggle数据集
├── docs/                         # 项目文档
│   ├── Architecture_Design.md    # 架构设计文档
│   ├── Acceptance_Document.md    # 验收文档
│   └── Deployment_Guide.md       # 部署说明
├── package.json                  # 前端依赖
├── requirements.txt              # Python依赖
├── vite.config.ts                # Vite配置
└── README.md                     # 项目说明
```

## 8. 非功能性需求

| 需求项 | 目标 |
|--------|------|
| 页面加载时间 | < 2秒 |
| API响应时间 | < 500ms |
| 预测准确率 | MAE < 50 (平均需求约100) |
| 并发支持 | 单用户，无需高并发 |
| 浏览器兼容 | Chrome, Firefox, Safari 最新版 |
| 代码质量 | 高内聚低耦合，完整注释 |
