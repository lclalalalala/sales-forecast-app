# 技术规范文档 v2.0

> 基于 User Story 和 BDD 文档更新
> 版本: 2.0
> 日期: 2026-07-11

---

## 1. 架构设计 (保持不变)

前后端分离架构，技术栈不变:
- 前端: React 19 + TypeScript + Tailwind CSS + Recharts
- 后端: Python Flask + Pandas + NumPy

## 2. API 接口规范 (保持不变)

8个接口已完整覆盖所有 User Story，无需新增。

## 3. 预测算法规范 (保持不变)

集成预测算法，公式:
```
suggestion = max(0, predicted_7d_total x 1.2 - current_inventory)
```

## 4. 测试规范 (更新)

### 4.1 测试分层

```
单元测试 (Unit Tests)
├── DataService 测试          - 数据加载、查询正确性
├── ForecastService 测试      - 预测算法正确性
└── 补货计算测试              - 公式计算正确性

集成测试 (Integration Tests)
├── API HTTP 端点测试         - Flask test_client
├── 响应格式测试              - 统一响应格式验证
└── 多门店隔离测试            - 数据不混淆验证

边界测试 (Boundary Tests)
├── 空数据测试                - 无历史数据时行为
├── 零库存测试                - 库存为0时补货建议
└── 异常参数测试              - 非法store_id等
```

### 4.2 新增测试要求

| 测试项 | 测试方法 | 断言内容 |
|--------|---------|---------|
| API HTTP /api/stores | Flask test_client.get | status=200, 返回5个门店 |
| API HTTP /api/sales/trend | Flask test_client.get | status=200, daily_sales长度>80 |
| API HTTP /api/replenishment | Flask test_client.get | status=200, top_5_products长度为5 |
| API HTTP /api/products/detail | Flask test_client.get | status=200, 包含forecast字段 |
| 空历史数据预测 | forecast_service.predict | 返回保守估计值(非空) |
| 零库存补货 | calculate_replenishment | 建议量=预测需求x安全系数 |
| 多门店隔离 | data_service.get_store_data | S001和S002数据不重复 |
| 响应格式统一 | 所有API端点 | 均包含success/data/message/timestamp |

### 4.3 测试执行

```bash
cd api/
python test_api.py
# 预期: 全部测试通过
```

## 5. 代码规范 (更新)

### 5.1 Python 代码
- PEP 8 规范
- 函数docstring注释
- 类型注解
- 无未使用import

### 5.2 TypeScript 代码
- 严格模式
- Props接口定义
- 无any类型

## 6. 文件清单

| 文件 | 说明 | 状态 |
|------|------|------|
| api/app.py | Flask入口 | 不变 |
| api/services/data_service.py | 数据服务 | 不变 |
| api/services/forecast_service.py | 预测服务 | 不变 |
| api/test_api.py | 测试套件 | **需更新** |
| src/App.tsx | 路由配置 | 不变 |
| src/pages/DashboardPage.tsx | 数据概览 | 不变 |
| src/pages/ReplenishmentPage.tsx | 补货建议 | 不变 |
| src/pages/ProductDetailPage.tsx | 商品详情 | 不变 |
| src/types/index.ts | 类型定义 | 不变 |
| src/services/api.ts | API封装 | 不变 |
| src/components/Layout.tsx | 布局 | 不变 |
| src/components/StoreSelector.tsx | 门店选择 | 不变 |
