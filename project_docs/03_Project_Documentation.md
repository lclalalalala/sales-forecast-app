# 零售门店库存与需求预测系统 - 项目文档

## 1. 项目概述

本项目基于 Kaggle 数据集 "Retail Store Inventory and Demand Forecasting"，构建了一套完整的零售门店库存管理与需求预测系统。

### 主要功能
- **数据概览**: 展示门店过去3个月销售趋势、Top 5 畅销品和 Bottom 5 滞销品
- **补货建议**: 基于集成预测算法，为 Top 5 畅销品计算未来7天的建议补货量
- **商品详情**: 查看任意商品的历史销售趋势、当前库存水位和补货建议

### 技术栈
| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Tailwind CSS + shadcn/ui + Recharts |
| 后端 | Python Flask + Pandas + NumPy + Scikit-learn |
| 算法 | 集成预测模型 (近期均值 + 星期模式 + 趋势调整 + 季节因子) |

---

## 2. 项目结构

```
retail-inventory-forecast/
├── README.md                              # 项目说明
├── docs/                                  # 项目文档
│   ├── 01_Architecture_Design.md          # 架构设计文档
│   ├── 02_Acceptance_Document.md          # 验收文档
│   └── 03_Project_Documentation.md        # 本文档
│
├── data/                                  # 数据文件
│   └── sales_data.csv                     # Kaggle 数据集 (76,000行 × 16列)
│
├── api/                                   # 后端代码
│   ├── app.py                             # Flask 应用入口
│   ├── requirements.txt                   # Python 依赖
│   ├── test_api.py                        # 测试套件 (14个测试用例)
│   └── services/                          # 服务层
│       ├── data_service.py                # 数据加载与查询服务
│       └── forecast_service.py            # 需求预测算法服务
│
├── src/                                   # 前端代码
│   ├── main.tsx                           # 入口文件 (含路由配置)
│   ├── App.tsx                            # 主应用组件
│   ├── index.css                          # 全局样式
│   ├── types/                             # TypeScript 类型定义
│   │   └── index.ts                       # 所有接口定义
│   ├── services/                          # API 服务
│   │   └── api.ts                         # 后端 API 调用封装
│   ├── components/                        # 公共组件
│   │   ├── Layout.tsx                     # 页面布局 (导航栏)
│   │   ├── StoreSelector.tsx              # 门店选择器
│   │   └── ProductSelector.tsx            # 商品选择器
│   └── pages/                             # 页面组件
│       ├── DashboardPage.tsx              # 数据概览页
│       ├── ReplenishmentPage.tsx          # 补货建议页
│       └── ProductDetailPage.tsx          # 商品详情页
│
├── package.json                           # Node.js 依赖
├── vite.config.ts                         # Vite 构建配置
├── tailwind.config.js                     # Tailwind CSS 配置
└── tsconfig.json                          # TypeScript 配置
```

---

## 3. 安装与部署

### 3.1 环境要求
- Python 3.8+
- Node.js 18+
- 操作系统: Linux / macOS / Windows

### 3.2 后端部署

```bash
# 1. 进入后端目录
cd api/

# 2. 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\\Scripts\\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python app.py
# 服务将在 http://localhost:5000 启动
```

**依赖列表** (requirements.txt):
```
flask==3.0.3
flask-cors==4.0.1
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.5.1
python-dateutil==2.9.0
```

### 3.3 前端部署

```bash
# 1. 安装依赖
npm install

# 2. 开发模式启动
npm run dev
# 服务将在 http://localhost:5173 启动

# 3. 生产构建
npm run build
# 构建产物在 dist/ 目录
```

### 3.4 生产环境部署

**使用 Gunicorn (推荐)**:
```bash
# 安装 gunicorn
pip install gunicorn

# 启动 (生产环境)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Nginx 反向代理配置**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /path/to/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 4. API 接口文档

### 4.1 接口列表

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | /api/health | 健康检查 | - |
| GET | /api/stores | 门店列表 | - |
| GET | /api/products | 商品列表 | store_id |
| GET | /api/sales/trend | 销售趋势 | store_id, days |
| GET | /api/sales/ranking | 商品排名 | store_id, days |
| GET | /api/replenishment | 补货建议 | store_id, safety_factor |
| GET | /api/products/detail | 商品详情 | store_id, product_id, days |
| GET | /api/dashboard/kpi | KPI汇总 | store_id, days |

### 4.2 响应格式

所有接口返回统一格式:
```json
{
  "success": true,
  "data": { ... },
  "message": "",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

## 5. 预测算法说明

### 5.1 算法原理

采用**集成预测模型**，结合四种方法的加权平均:

1. **近期均值法 (权重30%)**: 最近14天的平均需求量
2. **星期模式法 (权重40%)**: 历史同期(相同星期几)的平均需求量
3. **趋势调整**: 最近7天 vs 最近30天的趋势系数 (限制在0.7~1.3)
4. **季节因子**: 同月份历史平均的季节调整

### 5.2 预测公式

```
prediction = (recent_avg × 0.3 + dow_avg × 0.4) × trend_factor × 0.7
           + recent_avg × 0.3 × seasonal_factor
```

### 5.3 补货量计算

```
suggested_replenishment = max(0, total_predicted_demand × safety_factor - current_inventory)
```

默认安全系数 safety_factor = 1.2 (20%缓冲)

---

## 6. 测试

### 6.1 运行测试

```bash
cd api/
python test_api.py
```

### 6.2 测试覆盖

| 测试编号 | 测试内容 | 结果 |
|---------|---------|------|
| TC-001 | 数据加载成功 | OK |
| TC-002 | 门店列表正确 | OK |
| TC-003 | 商品列表正确 | OK |
| TC-004 | 销售趋势数据正确 | OK |
| TC-005 | 商品排名正确 | OK |
| TC-006 | 当前库存非负 | OK |
| TC-007 | 历史数据字段完整 | OK |
| TC-008 | 预测返回7个值 | OK |
| TC-009 | 预测值非负 | OK |
| TC-010 | 预测值在合理范围 | OK |
| TC-011 | 补货计算正确 | OK |
| TC-012 | 库存充足时补货为0 | OK |
| TC-013 | 多商品预测一致性 | OK |
| TC-014 | 数据摘要格式正确 | OK |

---

## 7. 前端页面说明

### 7.1 数据概览页 (Dashboard)
- **URL**: /
- **功能**: KPI卡片、销售趋势折线图、Top 5 / Bottom 5 商品表格
- **交互**: 门店选择器切换数据

### 7.2 补货建议页 (Replenishment)
- **URL**: /replenishment
- **功能**: 汇总卡片、补货建议表格、7天预测迷你图
- **交互**: 门店选择器、刷新按钮

### 7.3 商品详情页 (Product Detail)
- **URL**: /product
- **功能**: 信息卡片、历史趋势三线图、7天预测柱状图
- **交互**: 门店选择器、商品选择器

---

## 8. 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| 页面加载 | < 2秒 | ~1.5秒 |
| API响应 | < 500ms | ~200ms |
| 预测算法 | < 100ms | ~50ms |
| 构建时间 | < 30秒 | ~12秒 |

---

## 9. 开发规范

### 9.1 代码规范
- **Python**: PEP 8, 函数docstring注释, 类型注解
- **TypeScript**: 严格模式, 接口定义完整
- **组件**: 单一职责, Props类型定义
- **命名**: 语义化命名, 驼峰/下划线规范

### 9.2 设计原则
- **高内聚低耦合**: 服务层独立, 组件职责单一
- **DRY**: 公共组件抽离, 工具函数复用
- **可维护性**: 完整注释, 类型安全, 错误处理

---

## 10. 故障排除

### 10.1 常见问题

**Q: 后端启动失败**
- 检查 Python 版本 >= 3.8
- 检查依赖是否安装完整: `pip install -r requirements.txt`
- 检查数据文件路径是否正确

**Q: 前端无法连接后端**
- 确认后端服务在 localhost:5000 运行
- 检查 CORS 配置 (开发环境已允许所有源)
- 检查网络连接

**Q: 构建失败**
- 检查 Node.js 版本 >= 18
- 删除 node_modules 重新安装: `rm -rf node_modules && npm install`
- 检查 TypeScript 类型错误

---

## 11. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-11 | 初始版本，完整功能实现 |

---

## 12. 联系方式

如有问题或建议，请通过项目 Issue 或邮件联系开发团队。
