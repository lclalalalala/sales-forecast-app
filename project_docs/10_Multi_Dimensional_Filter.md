# 多维筛选功能设计文档

## 一、可筛选特征维度分析

### 数据集中所有维度

| 维度 | 类型 | 唯一值 | 筛选价值 | 决策 |
|------|------|--------|---------|------|
| Store ID | 分类 | 5 | 高 | 已实现(门店选择器) |
| Product ID | 分类 | 20 | 高 | 已实现(商品选择器) |
| **Category** | **分类** | **5** | **高** | **实现** |
| **Inventory Status** | **计算** | **4** | **高** | **实现** |
| **Time Range** | **时间** | **5档** | **高** | **实现** |
| Promotion | 分类 | 2 | 中 | 实现 |
| Price Range | 区间 | 自定义 | 中 | 实现 |
| Weather | 分类 | 4 | 低 | 不实现 |
| Seasonality | 分类 | 4 | 低 | 不实现 |
| Epidemic | 分类 | 2 | 低 | 不实现 |
| Competitor Pricing | 连续 | - | 低 | 不实现 |

### 排除理由

- **Weather/Season**: 这些是环境因素，不是店长日常管理可主动筛选的维度
- **Epidemic**: 特殊时期数据，非日常管理维度
- **Competitor Pricing**: 信息参考维度，非筛选维度

## 二、筛选功能设计

### 2.1 数据概览页筛选

```
┌─────────────────────────────────────────────────────────────┐
│  门店选择 [S001 ▼]  时间范围 [90天 ▼]  类别 [全部 ▼]  库存状态 [全部 ▼]  促销 [全部 ▼]  │
└─────────────────────────────────────────────────────────────┘
```

**筛选项说明**:

| 筛选项 | 选项 | 默认 | 说明 |
|--------|------|------|------|
| 门店 | S001~S005 | S001 | 单选 |
| 时间范围 | 7天/30天/90天/180天/全年 | 90天 | 单选 |
| 类别 | 全部/Electronics/Clothing/Groceries/Toys/Furniture | 全部 | 多选 |
| 库存状态 | 全部/充足/正常/偏低/紧缺 | 全部 | 单选 |
| 促销 | 全部/是/否 | 全部 | 单选 |

### 2.2 筛选对功能的影响

**类别筛选**:
- 影响: KPI卡片(按筛选类别重算)、趋势图(筛选类别汇总)、排名表(筛选类别内排名)

**库存状态筛选**:
- 影响: 排名表(只显示指定库存状态的商品)

**时间范围筛选**:
- 影响: 所有数据(KPI、趋势图、排名)

**促销筛选**:
- 影响: 趋势图和排名数据

### 2.3 商品详情页筛选

商品详情页新增类别筛选器，快速切换不同类别的商品:

```
门店 [S001 ▼]  类别 [全部 ▼]  商品 [P0001 ▼]
```

选择类别后，商品下拉列表联动过滤。

## 三、API更新

### 3.1 新增筛选参数

```
GET /api/sales/trend?store_id=S001&days=90&category=Clothing,Electronics
GET /api/sales/ranking?store_id=S001&days=90&category=Clothing&inventory_status=low
GET /api/products?store_id=S001&category=Clothing
```

### 3.2 新增接口

```
GET /api/products/by-category?store_id=S001&category=Clothing
  - 返回某类别的商品列表
```

## 四、实现计划

| 步骤 | 内容 | 文件 |
|------|------|------|
| 1 | 更新DataService支持筛选 | data_service.py |
| 2 | 更新API端点 | app.py |
| 3 | 更新DashboardPage添加筛选组件 | DashboardPage.tsx |
| 4 | 更新ProductDetailPage添加类别筛选 | ProductDetailPage.tsx |
| 5 | 更新测试 | test_api.py |
