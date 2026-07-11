# BDD 规范文档 v2.0

> 基于 User Story v2.0
> 日期: 2026-07-11

---

## Feature 1: 门店数据概览 (含多维筛选)

### Scenario 1.1: 默认门店概览
```gherkin
Given 系统已加载数据集
When 店长打开数据概览页
Then 默认展示 S001 门店数据
  And KPI 卡片显示 90天总销量、日均销量、商品数、平均库存
  And 90天趋势折线图加载完成
```

### Scenario 1.2: 门店切换
```gherkin
Given 店长在数据概览页
When 从门店下拉选择 S003
Then 所有数据更新为 S003
  And KPI、趋势图、排名表联动刷新
```

### Scenario 1.3: 时间范围筛选
```gherkin
Given 店长在数据概览页
When 点击时间范围按钮组的 "近7天"
Then KPI 重算为近7天数据
  And 趋势图显示7天数据点
  And 排名表基于7天销量重排
```

### Scenario 1.4: 类别筛选
```gherkin
Given 店长在数据概览页
When 从类别下拉选择 "Clothing"
Then 趋势图显示 Clothing 类别汇总
  And Top5/Bottom5 排名表只显示 Clothing 商品
  And KPI 卡片更新为 Clothing 类别数据
```

### Scenario 1.5: 库存状态筛选
```gherkin
Given 店长在数据概览页
When 从库存状态下拉选择 "紧缺"
Then 排名表只显示库存状态为 "紧缺" 的商品
  And 每个商品显示其库存数量和状态标签
```

### Scenario 1.6: 组合筛选
```gherkin
Given 店长在数据概览页
When 选择门店=S002 + 时间=30天 + 类别=Electronics + 库存状态=偏低
Then 所有筛选条件同时生效
  And 排名表只显示同时满足所有条件的商品
```

## Feature 2: 智能补货建议

### Scenario 2.1: Top 5 补货建议
```gherkin
Given 店长打开补货建议页
Then 自动显示 Top 5 畅销品
  And 每行包含: 商品ID、当前库存、库存状态、7天预测迷你图、建议补货量
  And 库存充足时显示"库存充足"绿色标签
  And 库存紧缺时显示建议补货量橙色高亮
```

## Feature 3: 商品深度分析

### Scenario 3.1: 类别联动筛选
```gherkin
Given 店长在商品详情页
When 从类别下拉选择 "Clothing"
Then 商品下拉列表只显示 Clothing 类别的商品
  And 默认选中该类别第一个商品
  And 页面数据自动刷新
```

### Scenario 3.2: 商品历史趋势和补货建议
```gherkin
Given 店长选择了某商品
Then 展示三线趋势图(销量/需求/库存)
  And 库存卡片用颜色标识状态(绿/黄/红)
  And 展示7天预测柱状图和补货建议量
```

---

## 测试覆盖映射

| Scenario | 测试文件 | 测试方法数 |
|----------|---------|-----------|
| 1.1~1.6 | test_api.py | DataService(14) + Flask(9) |
| 2.1 | test_api.py | ForecastService(10) |
| 3.1~3.2 | test_api.py | DataService + Flask |
| 全部边界 | test_api.py | EdgeCases(7) |
| **合计** | | **40** |
