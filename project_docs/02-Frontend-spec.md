下面是一套面向店长的前端信息架构和页面设计方案。整体建议采用“顶部全局上下文 + 左侧主导航 + 页面内筛选”的结构，保证门店、数据日期和筛选条件在不同页面之间保持一致。

---

# 一、页面清单

| 页面 | 路由示例 | 主要目标 | 优先级 |
|---|---|---|---|
| 数据概览 | `/overview` | 查看门店整体销售、库存、畅销品和滞销品 | P0 |
| 补货建议 | `/replenishment` | 查看商品未来 7 天预测销量和建议补货量 | P0 |
| 商品详情 | `/products/:productId` | 查看单个商品的销售、库存和补货情况 | P0 |
| 补货下单详情 | `/orders/new?store_id=...&product_id=...&quantity=...` | 查看商品补货明细并生成下单草稿，由店长确认 | P0 |
| 指标与规则说明 | `/help` 或抽屉弹窗 | 解释指标、库存状态和补货算法规则 | P0 |
| 全局异常/空数据状态 | 页面内状态 | 处理加载失败、无数据和筛选无结果 | P0 |

建议先实现 4 个核心页面：

1. 数据概览
2. 补货建议
3. 商品详情
4. 补货下单详情

指标说明可以先做成全局帮助抽屉，不必单独成为完整页面。

---

# 二、整体布局

## 1. 顶部导航栏

顶部导航建议固定显示以下内容：

- 系统名称：`门店销售与智能补货`
- 当前门店选择器：
  - 门店编号，如 `S001`
  - 门店名称，如 `人民广场店`
- 数据截至日期：
  - `数据截至：2024-06-30`
- 全局帮助入口：
  - `指标说明`
  - `补货规则`
- 用户信息：
  - `店长`
  - 当前版本暂不需要登录权限

门店选择后，概览页、补货建议页和商品详情页统一使用该门店。

## 2. 左侧主导航

建议导航顺序：

```text
数据概览
补货建议
商品分析
```

其中：

- `数据概览`：默认进入页面
- `补货建议`：进入全部商品补货列表
- `商品分析`：进入商品详情页，页面内选择具体商品
- 点击商品排名、补货列表中的商品名称，可直接进入商品详情

## 3. 全局筛选条件

建议在页面顶部统一提供：

- 门店
- 商品类别
- 时间范围
- 重置筛选

时间范围选项：

```text
近 7 天
近 30 天
近 90 天
近 180 天
全部时间
```

默认值：

```text
门店：S001
时间范围：近 90 天
商品类别：全部类别
```

注意：

- 时间范围主要影响历史销量、趋势图和畅销/滞销排名。
- 当前库存和库存状态应展示库存数据对应日期。
- 补货建议使用预测起始日期和未来 7 天预测区间，不应与历史时间范围混淆。

---

# 三、页面跳转关系

```text
数据概览
├── 点击 Top 5 商品 ──────> 商品详情
├── 点击 Bottom 5 商品 ───> 商品详情
├── 点击补货风险商品 ──────> 商品详情
└── 点击“补货建议” ───────> 补货建议

补货建议
├── 点击商品名称/编号 ─────> 商品详情
├── 点击“查看原因” ──────> 补货原因抽屉
├── 点击“去下单” ────────> 补货下单详情
└── 点击“查看全部预测” ──> 商品详情

商品详情
├── 更换类别 ─────────────> 更新商品选择列表
├── 更换商品 ─────────────> 更新当前商品数据
├── 点击“去下单” ────────> 补货下单详情
└── 点击返回 ─────────────> 上一页面并尽量恢复原筛选条件

补货下单详情
├── 返回商品详情
├── 返回补货建议
└── 生成下单草稿/确认补货
```

由于当前版本不涉及真实采购下单，`去下单`建议先进入“补货下单详情”页面，支持查看和确认补货草稿，但不连接真实采购系统。

---

# 四、数据概览页

## 页面目标

帮助店长快速了解当前门店在指定时间范围和商品类别下的：

- 销售表现
- 销售趋势
- 畅销商品
- 滞销商品
- 库存风险

## 页面结构

### 1. 页面标题区

```text
数据概览
S001 人民广场店
统计范围：2024-04-01 ～ 2024-06-30
数据截至：2024-06-30
```

右侧提供：

- 门店切换
- 时间范围
- 商品类别
- 重置筛选

如果实际数据不足 90 天，应提示：

```text
当前选择近 90 天，实际可用数据为 2024-05-15 ～ 2024-06-30，共 47 天
```

---

## 2. 核心指标卡片

建议展示 4 个核心指标：

| 指标 | 展示内容 | 辅助信息 |
|---|---|---|
| 平均日销售量 | `1,286 件` | 统计周期内平均每日实际销量 |
| 当前库存 | `8,420 件` | 库存日期：2024-06-30 |
| 低库存商品数 | `23 个` | 状态为“偏低”的商品数量 |
| 紧缺商品数 | `8 个` | 状态为“紧缺”的商品数量 |

指标卡片底部可添加简短说明：

```text
基于当前门店、类别和时间范围
```

注意：

- 平均销售量使用“实际销量”。
- 当前库存不应随着历史时间范围变成历史平均库存。
- 库存指标必须标注库存日期。

---

## 3. 门店销售趋势折线图

### 图表标题

```text
销售趋势
```

### 图表内容

- 横轴：日期
- 纵轴：实际销量
- 单位：件
- 默认展示近 90 天
- 支持悬停查看：
  - 日期
  - 当日实际销量
- 切换门店、类别和时间范围后同步更新

Tooltip 示例：

```text
2024-06-18
实际销量：1,326 件
```

如果需要增强分析，可以增加：

- 7 日移动平均线
- 周同比或环比

但第一版建议只保留实际销量线，避免将预测销量和历史销量混在一起。

### 空状态

```text
当前门店和筛选条件下暂无销售趋势数据
请尝试扩大时间范围或清除商品类别筛选
```

---

## 4. Top 5 畅销品

建议使用卡片或表格展示。由于用户需要快速识别重点商品，推荐表格形式。

### 表头

| 排名 | 商品编号 | 商品名称 | 商品类别 | 当日销量 | 日均销量 | 当前库存 | 库存状态 | 操作 |
|---:|---|---|---|---:|---:|---:|---|---|

### 示例

| 排名 | 商品编号 | 商品名称 | 商品类别 | 当日销量 | 日均销量 | 当前库存 | 库存状态 | 操作 |
|---:|---|---|---|---:|---:|---:|---|---|
| 1 | P001 | 瓶装矿泉水 | 饮料 | 3,280 | 36.4 | 120 | 偏低 | 查看详情 |
| 2 | P018 | 纯牛奶 | 乳制品 | 2,940 | 32.7 | 286 | 正常 | 查看详情 |

排序规则：

1. 按当前时间范围内累计实际销量降序。
2. 销量相同时使用稳定排序，例如商品编号升序。
3. 如果当前条件下商品少于 5 个，则展示实际数量。

---

## 5. Bottom 5 滞销品

### 表头

| 排名 | 商品编号 | 商品名称 | 商品类别 | 当日销量 | 日均销量 | 当前库存 | 库存状态 | 销售提示 | 操作 |
|---:|---|---|---|---:|---:|---:|---|---|---|


排序规则：

1. 按当前时间范围内累计实际销量升序。
2. 销量为 0 的商品优先显示。
3. 销量相同时使用稳定排序。
4. 销售表现和库存风险使用两个独立字段，不能合并成一个结论。

---

# 五、补货建议页

## 页面目标

帮助店长查看：

- 哪些商品需要补货
- 未来 7 天销量的预测
- 当前库存是否足够
- 建议补多少货
- 默认展示全部商品；
- 按当前销量倒序排序；
- 提供“重点商品”和“库存风险”快捷筛选。

## 页面标题区

```text
补货建议
S001 人民广场店
预测周期：2024-07-01 ～ 2024-07-07
预测生成时间：2024-06-30
```


筛选项：
- 门店
- 商品类别
- 库存状态
- 是否需要补货
- 排序方式：
  - 当前销量
  - 建议补货量
  - 缺货风险

---

## 补货建议主表

### 推荐表头

| 店铺ID | 商品ID | 商品类别 | 当日销量 | 90 天日均销量 | 当日售前库存 | 当日售后库存 | 在途库存 | 预测趋势  | 建议补货量 | 库存状态 | 操作 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|

### 字段说明

- `当日销量`：数据截至日当天的实际销量。
- `90 天日均销量`：最近 90 天实际销量平均值。
- `售前库存`：当天营业开始时库存。
- `售后库存`：当天营业结束时库存。
- `在途库存`：已安排但尚未完成入库的库存。
- `预测趋势`：展示未来 7 天每日预测销量的 mini chart。
- `建议补货量`：系统计算出的建议补货数量，不得小于 0，整数
- `库存状态`：充足、正常、偏低、紧缺。

### Mini chart

建议使用小型柱状图或折线图，展示 7 个数据点：


悬停时展示：

```text
2024-07-03
预测销量：42 件
```

图表必须使用独立颜色或标签标识为：

```text
预测销量
```

不能与历史实际销量使用相同图例。

建议补货量可以采用整数展示：

```text
0 件
18 件
126 件
```
---

## 查看补货原因

点击“查看原因”后打开右侧抽屉。

### 抽屉标题

```text
P001 瓶装矿泉水 · 补货建议依据
```

### 内容

| 项目 | 数值 |
|---|---:|
| 当前售后库存 | 120 件 |
| 在途库存 | 30 件 |
| 补货提前期 | 3天 ｜
| 补货提前期内预计销量 | 168 件 |
| 安全库存要求 | 40 件 |
| 建议补货数量 | 58 件 |

note： 补货提前期 就是商品送货时间 即 K 值

下方显示计算过程：

```text
168 + 40 - 120 - 30 = 58 件
```

同时补充说明：

```text
预测基于历史实际销量计算，不使用需求字段作为预测结果。
```

---

# 六、商品详情页

## 页面目标

让店长查看任意商品的完整信息，包括：

- 历史销售趋势
- 历史库存变化
- 当前库存
- 未来 7 天预测销量
- 建议补货量
- 补货原因
- 跳转下单

## 页面结构

### 1. 商品选择区

建议提供级联选择：

```text
商品类别：[全部类别 v]
商品：[搜索商品编号或名称 v]
```

商品选择器中展示：

```text
P001
P002
P003
```

选择类别后，商品下拉列表只展示对应类别商品。

页面进入方式：

- 从导航进入时，默认选择第一个商品或提示选择商品。
- 从排名或补货表进入时，自动带入商品。
- 从排名进入时，自动带入当前门店。
- 返回上一页时，尽量恢复原筛选条件。

---

## 2. 商品信息摘要卡片

### 商品基础信息

```text
商品编号：P001
商品名称：瓶装矿泉水
商品类别：饮料
当前门店：S001 人民广场店
```

### 指标卡片

| 指标 | 数值 |
|---|---:|
| 当日销量 | 36 件 |
| 90 天日均销量 | 36.4 件 |
| 当前库存 | 120 件 |
| 在途库存 | 30 件 |
| 未来 7 天预计销量 | 168 件 |
| 建议补货量 | 58 件 |

右侧突出显示：

```text
库存状态：偏低
库存日期：2024-06-30
```

建议补货数量使用高辨识度颜色，但不要只使用颜色，应同时显示文字。

---

## 3. 历史销售趋势

### 图表标题

```text
历史实际销量
```

内容：

- 默认展示近 90 天
- 支持切换 7 天、30 天、90 天、180 天、全部时间
- 横轴：日期
- 纵轴：实际销量
- 支持 Tooltip
- 不显示预测数据，避免和历史实际销量混淆

Tooltip：

```text
2024-06-18
实际销量：42 件
```

---

## 4. 历史库存变化

### 图表标题

```text
历史库存变化
```

内容：

- 横轴：日期
- 纵轴：库存量
- 展示每日库存变化
- 当前库存点突出显示
- 标记补货入库日期，如数据支持
- 标记库存阈值线：
  - 安全库存
  - 低库存线

Tooltip：

```text
2024-06-18
库存：136 件
库存状态：正常
```

图表下方显示：

```text
当前库存数据日期：2024-06-30
```

销售趋势和库存趋势建议上下排列，或者使用左右两列布局，避免将两个指标放在同一坐标轴中造成误读。

---

## 5. 未来 7 天预测与补货建议

### 未来销量预测表

| 日期 | 预测销量 | 预测库存变化 | 是否存在库存风险 |
|---|---:|---:|---|
| 07-01 | 24 | 126 | 否 |
| 07-02 | 25 | 101 | 否 |
| 07-03 | 28 | 73 | 否 |
| 07-04 | 26 | 47 | 是 |
| 07-05 | 23 | 24 | 是 |
| 07-06 | 21 | 3 | 是 |
| 07-07 | 21 | -18 | 是 |

如果系统不具备逐日库存预测能力，可以只展示：

| 日期 | 预测销量 |
|---|---:|

并将库存风险放在汇总区域中。

### 补货建议区域

```text
未来 7 天预计销量：168 件
当前售后库存：120 件
在途库存：30 件
安全库存：40 件
建议补货量：58 件
```

按钮：

```text
查看计算依据
去下单
```

---

# 七、补货下单详情页

当前版本不涉及真实采购下单，因此建议定位为“补货下单草稿页”。

## 页面目标

让店长在确认补货数量前，查看单个商品的补货依据，并生成下单草稿。

## 页面内容

### 商品信息

| 字段 | 内容 |
|---|---|
| 门店 | S001 人民广场店 |
| 商品编号 | P001 |
| 商品名称 | 瓶装矿泉水 |
| 商品类别 | 饮料 |
| 当前库存 | 120 件 |
| 在途库存 | 30 件 |
| 未来 7 天预计销量 | 168 件 |
| 系统建议补货量 | 58 件 |

### 下单字段

| 字段 | 类型 |
|---|---|
| 补货数量 | 数字输入框，默认填入系统建议量 |
| 预计到货日期 | 日期选择器 |
| 备注 | 文本输入框 |
| 当前库存状态 | 只读 |
| 补货依据 | 只读 |

操作按钮：

```text
取消
保存补货草稿
确认补货
```

如果当前版本不需要保存订单，可以将按钮命名为：

```text
生成补货记录
```

避免让用户误以为已经真实提交采购订单。

---

# 八、库存状态设计

建议统一使用四级库存状态，并在帮助说明中解释。

| 状态 | 展示颜色建议 | 业务含义 |
|---|---|---|
| 充足 | 绿色 | 当前库存能够覆盖未来销量，并高于安全库存 |
| 正常 | 蓝色 | 当前库存基本能够覆盖预计销量 |
| 偏低 | 橙色 | 库存接近风险线，建议关注 |
| 紧缺 | 红色 | 当前库存可能无法覆盖未来销量，存在缺货风险 |

状态判断应同时考虑：

- 当前售后库存
- 在途库存
- 未来 7 天预计销量
- 安全库存
- 商品历史销量波动

需要注意：

- `滞销` 是销售表现标签。
- `紧缺` 是库存风险标签。
- 一个商品可能“滞销但库存充足”。
- 一个商品也可能“畅销且库存紧缺”。

---

# 九、统一表格规范

## 表格通用能力

所有商品表建议支持：

- 商品编号点击进入详情
- 商品名称点击进入详情
- 表头排序
- 空状态
- 加载状态
- 错误重试
- 分页或虚拟滚动
- 固定操作列
- 数字右对齐
- 单位明确显示为“件”
- 库存状态使用文字加颜色标签

## 空数据状态

不要显示空白表格，也不要把无数据直接显示为 `0`。

建议显示：

```text
当前筛选条件下暂无商品数据
请尝试切换门店、类别或时间范围
```

按钮：

```text
清除筛选
恢复默认条件
```

## 局部异常状态

如果某个模块加载失败，建议模块内显示：

```text
销售趋势暂时加载失败
请稍后重试
[重新加载]
```

不要因为趋势图失败而阻塞排名表和指标卡片。

---

# 十、关键交互和状态

## 加载状态

页面首次加载时：

- 筛选区域保留骨架
- 指标卡片显示 Skeleton
- 图表显示加载占位
- 表格显示 5～8 行骨架数据

## 筛选联动

当切换门店、类别或时间范围时：

1. 保留筛选控件当前值。
2. 相关模块显示局部加载状态。
3. 所有指标、图表和排名同步刷新。
4. 页面顶部更新当前门店和统计范围。
5. 如果无结果，显示明确空状态。

## 门店一致性

建议使用以下方式保存门店：

- URL 参数，例如 `?store=S001`
- 或全局状态管理
- 或本地缓存最近选择的门店

页面跳转示例：

```text
/overview?store=S001&range=90d&category=all
/products/P001?store=S001
/replenishment?store=S001
```

## 返回行为

从商品详情返回概览时，尽量保留：

- 当前门店
- 时间范围
- 商品类别
- 原来的滚动位置
- 原来的排名或列表页码

---

# 十二、推荐页面主流程

店长打开系统后的典型操作流程：

```text
打开系统
  ↓
默认进入 S001 数据概览
  ↓
查看销售趋势和 Top 5 / Bottom 5
  ↓
发现某个畅销品库存偏低
  ↓
点击商品进入商品详情
  ↓
查看历史销量、库存变化和未来 7 天预测
  ↓
查看系统建议补货量及计算原因
  ↓
点击“去下单”
  ↓
确认或调整补货数量
  ↓
生成补货草稿
```

---

# 十三、主题与视觉规范

新版主要描述业务页面结构，本章节补充技术实现层面的主题与视觉 token 要求。

## 1. 设计系统 token

前端使用 `project_docs/dev_guide/design_system.md` 定义的设计 token，禁止在组件中硬编码色值。

核心 token 类别：

- 背景色：`--bg-page`、`--bg-surface`、`--bg-surface-hover`
- 文字色：`--text-primary`、`--text-secondary`、`--text-tertiary`
- 强调色：`--accent-primary`、`--accent-primary-hover`、`--accent-secondary`
- 状态色：`--status-critical`、`--status-low`、`--status-normal`、`--status-sufficient`
- 图表色：`--chart-sales`、`--chart-forecast`、`--chart-inventory`
- 圆角/阴影/间距：`--radius-md`、`--shadow-card-hover`、`--space-4`

## 2. Light / Dark 模式

- 使用 `next-themes` 或自定义 `ThemeProvider` 管理主题。
- 支持三种模式：`light`、`dark`、`system`。
- `system` 模式通过 `window.matchMedia('(prefers-color-scheme: dark)')` 自动切换。
- 用户偏好持久化到 `localStorage`，键名：`sephora-theme`。
- 在 `<html>` 上切换 `.theme-light` / `.theme-dark` 类。
- `ThemeToggle` 组件位于 `app/src/components/ThemeToggle.tsx`，需暴露 `light / dark / system` 选项。

## 3. Tailwind 集成

- `tailwind.config.js` 通过 `theme.extend` 将设计系统 token 映射为颜色、间距、圆角。
- 配置 `darkMode: ["variant", "&:where(.theme-dark, .theme-dark *)"]`。
- 组件优先使用 Tailwind 工具类或 CSS 变量，禁止写死色值。

---

# 十四、公共组件清单

新版只描述页面字段，本章节补充可复用公共组件目录。当前已实现部分用 **✓ 已存在** 标注，尚未独立提取的用 **待提取** 标注。

| 组件 | 文件路径 | 说明 | 状态 |
|---|---|---|---|
| `ThemeToggle` | `components/ThemeToggle.tsx` | light/dark/system 切换 | 已存在，需补 system 选项 |
| `Layout` / `TopNav` | `components/Layout.tsx` | 顶部粘性导航、移动端抽屉 | 已存在，可拆分为 `Layout/TopNav.tsx` |
| `FilterBar` | `components/FilterBar.tsx` | 门店、时间范围、类别、库存状态筛选 + 重置 | 已存在 |
| `StoreSelector` | `components/StoreSelector.tsx` | 门店下拉选择器 | 已存在 |
| `InventoryStatusBadge` | `components/InventoryStatusBadge.tsx` | 库存状态可视化徽章 | 已存在 |
| `DataState` | `components/DataState.tsx` | loading / error / empty / insufficient_data 状态 | 已存在 |
| `SearchModal` | `components/SearchModal.tsx` | ⌘K / Ctrl+K 全局搜索商品/门店 | **待实现** |
| `KpiCard` | `components/KpiCard.tsx` | 图标 + 标签 + 数值 + 说明 | **待提取** |
| `DataTable` | `components/ui/DataTable.tsx` | 可排序、hover、固定操作列 | **待提取** |
| `Chip` | `components/ui/Chip.tsx` | Pill 标签，active 状态 | **待实现** |
| `LineChart` | `components/charts/LineChart.tsx` | 销量/库存折线图 | **待提取** |
| `BarChart` | `components/charts/BarChart.tsx` | 预测销量柱状图 | **待提取** |
| `Sparkline` | `components/charts/Sparkline.tsx` | 迷你趋势图，用于表格 | **待实现** |
| `Skeleton` | `components/ui/Skeleton.tsx` | 加载占位 | shadcn/ui 已有 |
| `EmptyState` | `components/ui/EmptyState.tsx` | 空状态展示 | 可复用 `DataState` 空状态 |

### 组件实现约束

- 所有 UI 组件必须接受 `className` 以支持外部扩展。
- 组件内部必须使用设计系统 token，禁止硬编码颜色。
- 交互状态遵循 Trigger-Target 分离原则。
- 可交互组件须支持 `disabled` 状态并附带合适的视觉反馈。

---

# 十五、数据接口契约

前端类型定义必须以后端接口文档 `project_docs/07-API.md` 为唯一依据，禁止在本规范中定义与 `07-API.md` 冲突的字段。

## 1. 类型文件位置

```
app/src/types/
├── api.ts          # ApiResponse<T>, Context, ApiError, TimeRange, InventoryStatusKey
├── sales.ts        # Store, Product, DailySales
├── inventory.ts    # RankingItem, RankingData, InventorySummary
├── replenishment.ts # ReplenishmentData, ReplenishmentSuggestion, ProductDetail, ForecastResult
└── order.ts        # OrderDraft, OrderSubmissionResult
```

## 2. 主要类型与 `07-API.md` 的对应关系

| 前端类型 | 对应 `07-API.md` 章节 | 说明 |
|---|---|---|
| `ApiResponse<T>` | §2 信封结构 | `{ context, data }` |
| `Context` | §2.4 公共响应上下文字段 | 查询上下文 |
| `ApiError` | §2 异常结构 | `{ error: { code, message } }` |
| `Store` | §3.2 门店列表 | `id`, `name`, `region` |
| `Product` | §3.4 商品列表 | `id`, `name`, `category` |
| `DailySales` | §3.6 数据概览 | `date`, `units_sold` |
| `RankingItem` | §3.7 商品排名 | 含 `product_id`、`total_sold`、`inventory_status` 等 |
| `ReplenishmentSuggestion` | §3.8 补货建议 | 含 `forecast_7d`、`safety_stock`、`suggested_replenishment` 等 |
| `ProductDetail` | §3.5 商品详情 | 含 `historical_sales`、`forecast`、`replenishment` |
| `OrderDraft` / `OrderSubmissionResult` | §3.9 提交补货订单 | 当前为前端 Mock |

## 3. 字段命名约束

- 旧版中的 `sku`、`currentStock`、`forecastDemand`、`suggestedQty` 等命名已全部废弃。
- 统一使用新版命名：`product_id`、`current_inventory`、`units_sold`、`forecast_units_sold`、`suggested_replenishment`。
- 类型中如需示例，直接引用 `07-API.md` 中的字段表格。

---

# 十六、响应式实现要求

- 断点：`sm` 640px、`md` 768px、`lg` 1024px、`xl` 1280px。
- KPI 网格：
  - Desktop（`xl:`）：4 列
  - Tablet（`md:`）：2 列
  - Mobile：1 列
- 排名卡片网格：
  - Desktop：2 列
  - Tablet / Mobile：1 列
- 导航栏：
  - Desktop：水平链接
  - Mobile：汉堡菜单 + 侧边抽屉
- 筛选栏：
  - Desktop：水平排列
  - Mobile：垂直堆叠或折叠为抽屉
- 表格：
  - 桌面端完整展示所有列；
  - 小屏幕下允许横向滚动，关键列（商品编号、建议补货量、库存状态）固定可见。

---

# 十七、性能要求

1. 首屏加载时间 < 2s（本地开发环境）。
2. 图表数据更新使用 Recharts 动画过渡，避免全量重绘。
3. 补货建议表格数据量 > 200 行时启用虚拟滚动。
4. 图标使用 SVG（Lucide React），避免大图资源。
5. 启用 Tree Shaking，页面组件使用 `React.lazy + Suspense` 按需加载。
6. 全局筛选状态变化时，仅刷新依赖该状态的模块，避免整页重新挂载。

---

# 十八、可访问性要求

1. 所有按钮、链接、表单元素须有明确的 focus 样式。
2. 图表须提供替代文本或数据表格（`aria-label`、`role`）。
3. 颜色不能作为唯一信息传递方式：状态标签须同时显示文字。
4. 支持键盘导航（Tab、Enter、Escape）。
5. 遵循 `prefers-reduced-motion`，在 reduced-motion 模式下禁用非必要动画。
6. 表单输入须关联 `label`，错误信息通过 `aria-describedby` 关联。

---

# 十九、文件结构规范

建议的前端目录结构：

```text
app/src/
├── components/
│   ├── ui/                 # shadcn/ui 基础组件（Button、Card、Dialog、Table 等）
│   ├── charts/             # 复用图表组件：LineChart、BarChart、Sparkline
│   ├── Layout/             # TopNav、Sidebar、Layout
│   ├── FilterBar.tsx
│   ├── ThemeToggle.tsx
│   ├── StoreSelector.tsx
│   ├── InventoryStatusBadge.tsx
│   ├── DataState.tsx
│   ├── KpiCard.tsx         # 待提取
│   ├── SearchModal.tsx     # 待实现
│   └── Chip.tsx            # 待实现
├── pages/
│   ├── DashboardPage.tsx
│   ├── RankingPage.tsx
│   ├── ReplenishmentPage.tsx
│   ├── ProductDetailPage.tsx
│   └── OrderPage.tsx
├── hooks/
│   ├── use-mobile.ts
│   └── useKeyboardShortcut.ts   # 待实现（⌘K 等快捷键）
├── state/
│   └── analysisContext.tsx      # 全局筛选状态，持久化到 sessionStorage
├── lib/
│   ├── utils.ts
│   └── mockData.ts              # 前端 Mock 数据/提交逻辑（可选）
├── types/
│   ├── api.ts
│   ├── sales.ts
│   ├── inventory.ts
│   ├── replenishment.ts
│   └── order.ts
├── services/
│   └── api.ts                   # 统一 API 封装，参见 07-API.md §4
├── index.css                    # 设计系统 token
├── App.tsx
└── main.tsx
```

---

# 二十、实现优先级

| 优先级 | 任务 |
|--------|------|
| P0 | 全局 CSS 变量、Tailwind 配置、`ThemeProvider` / `ThemeToggle` system 选项 |
| P0 | `Layout`、`FilterBar`、`KpiCard`、`DataState`、`InventoryStatusBadge` |
| P0 | DashboardPage：KPI、趋势图、Top/Bottom 排名 |
| P1 | ReplenishmentPage：筛选、表格、Mini Chart、补货原因抽屉 |
| P1 | ProductDetailPage：商品信息、历史销量/库存图、未来 7 天预测、补货依据 |
| P1 | OrderPage：补货草稿、预计到货日期、补货依据只读展示 |
| P2 | `SearchModal`（⌘K 全局搜索） |
| P2 | 可复用 `DataTable`、`Chip`、`Sparkline` |
| P2 | 响应式细节优化、骨架屏、空状态 |
| P3 | 单元测试、可访问性审计、性能优化 |

---

# 二十一、验收标准

## 1. 视觉验收

- [ ] Light 与 Dark 模式均完整呈现，无裸色值泄漏。
- [ ] 所有组件在两种模式下对比度符合 WCAG AA。
- [ ] 响应式断点切换无布局错位。
- [ ] 动画流畅，无卡顿；`prefers-reduced-motion` 下动画被禁用。

## 2. 功能验收

- [ ] 主题切换即时生效，刷新后保持用户选择（含 `system`）。
- [ ] Dashboard 三大模块（KPI、趋势图、排名）数据正确渲染。
- [ ] 补货建议表格支持筛选、排序、行 hover、查看原因抽屉。
- [ ] 商品详情页展示完整信息，含历史销量、库存变化、未来 7 天预测、补货依据。
- [ ] ⌘K 搜索可触发并展示结果。
- [ ] 去下单页面预填门店、商品、建议补货量，支持调整数量与备注。

## 3. 代码验收

- [ ] 所有 UI 组件使用设计系统 token。
- [ ] TypeScript 类型完整，无 `any` 滥用。
- [ ] 数据类型与 `07-API.md` 完全一致。
- [ ] 组件实现遵循 Trigger-Target 分离原则。
- [ ] 通过 ESLint / Prettier 检查。
- [ ] 核心组件具备单元测试：Dashboard、Ranking、ProductDetail、Layout、FilterBar、StoreSelector、ThemeToggle、InventoryStatusBadge、DataState、API service。

---

# 二十二、参考文档

- [设计系统](./dev_guide/design_system.md)
- [前后端通讯 API 接口说明](./07-API.md)
- [后端架构与计算逻辑](./01_Architecture_Design.md)
- [计算公式与配置](./formular_and_config.md)

---

# 二十三、前端实现记录（2026-07-12）

## 已实现内容

本次迭代已按新版前端设计规范完成 `app/src/` 的核心改造，并补充了可复用组件与单元测试。

### 新增可复用组件

| 组件 | 路径 | 说明 |
|------|------|------|
| `KpiCard` | `app/src/components/KpiCard.tsx` | 图标 + 指标名称 + 数值 + 辅助说明 |
| `Sparkline` | `app/src/components/charts/Sparkline.tsx` | 基于 Recharts 的迷你趋势图，用于表格内预测趋势 |
| `DataTable` | `app/src/components/ui/DataTable.tsx` | 支持表头排序、loading 骨架、空状态、固定操作列 |
| `ReasonDrawer` | `app/src/components/ReasonDrawer.tsx` | 单个商品补货建议依据抽屉 |
| `HelpDrawer` | `app/src/components/HelpDrawer.tsx` | 全局帮助抽屉，涵盖指标说明、预测说明、补货规则、注意事项 |
| `OrderForm` | `app/src/components/OrderForm.tsx` | 补货下单表单，被页面与弹层复用 |
| `useKeyboardShortcut` | `app/src/hooks/useKeyboardShortcut.ts` | 键盘快捷键封装 |

### 页面改造

- **DashboardPage**：新增标题块（门店、统计范围、数据截至日期、实际可用数据不足提示），KPI 卡片使用 `KpiCard`，Top/Bottom 排名表替换为可排序 `DataTable`。
- **ReplenishmentPage**：新增标题块、重点商品/库存风险快捷筛选、排序下拉、预测趋势 Sparkline、补货原因抽屉；表格中的“去下单”以 Dialog 弹层形式打开 `OrderForm`，无需离开当前页面。
- **ProductDetailPage**：新增级联商品选择器（类别 + 商品）、商品摘要 KPI、独立历史销量/库存图表、未来 7 天预测表、补货建议区域与去下单按钮。
- **OrderPage**：将补货下单表单抽取为可复用 `OrderForm`；页面主体仍可通过 `/orders/new?store_id=...&product_id=...&quantity=...` 直接访问。表单整合必要商品上下文（门店、商品 ID、商品类别、当前库存、系统建议补货量），避免与下单信息重复；同时提供预计到货日期选择器、只读库存状态与补货依据，按钮改为“取消 / 保存补货草稿 / 确认补货”，成功提示改为“已生成补货记录”。
- **Layout**：导航项对齐规范（数据概览、补货建议、商品分析），新增帮助入口与移动端抽屉导航；`ThemeToggle` 支持 `light / dark / system`。
- **AnalysisContext**：全局筛选状态同步 URL 查询参数，刷新/返回后可恢复；同步时保留上下文未管理的参数（如 `store_id`、`product_id`、`quantity`），避免影响下单页等独立流程。

### 类型更新

- `OrderDraft` 增加 `expected_arrival_date?: string`。

### 测试

新增 / 更新测试文件：

- `app/src/components/KpiCard.test.tsx`
- `app/src/components/charts/Sparkline.test.tsx`
- `app/src/components/ui/DataTable.test.tsx`
- `app/src/components/HelpDrawer.test.tsx`
- `app/src/components/ThemeToggle.test.tsx`
- `app/src/pages/OrderPage.test.tsx`
- `app/src/pages/ReplenishmentPage.test.tsx`

验证结果：

```bash
cd app && npm run build   # 通过，无 TypeScript 错误
cd app && npm run test    # 7 个测试文件，24 条用例全部通过
```

## 已知限制与后续优化

1. **商品名称**：后端 `/api/products` 当前返回的 `name` 与 `id` 相同，商品名称列暂以 `product_id` 展示。
2. **⌘K 全局搜索**：本次未实现，标记为 P2，后续可基于 `useKeyboardShortcut` 与 `SearchModal` 补充。
3. **实时后端**：当前订单提交仍为前端 mock，生成“补货草稿记录”，未接入真实采购接口。
4. **响应式/动画细节**：主要布局已适配移动端，部分复杂表格的横向滚动和 `prefers-reduced-motion` 可在后续迭代继续打磨。

## 补充调整（2026-07-12）

- **OrderPage 精简**：根据反馈移除了独立的“商品摘要信息”卡片，将商品类别、当前库存、系统建议补货量等必要信息以只读字段形式并入下单表单，避免与门店、商品 ID 等下单字段重复，页面更聚焦。
- **去下单改为弹层**：补货建议页表格中的“去下单”按钮不再跳转新页面，而是以 `Dialog` 浮层打开 `OrderForm`，减少页面切换并保留当前筛选上下文；独立下单页路由 `/orders/new` 继续保留，支持直接链接访问。

## 代码审查修复（2026-07-12）

依据 `project_docs/dev_guide/frontend-dev-guide.md` 对 `app/src/` 进行系统性审查，按 High → Medium → Low 优先级完成以下修复与补充：

### 健壮性 / 防御式编程

- **ProductDetailPage**：对未来 7 天预测 `data.forecast`、补货建议 `data.replenishment` 及汇总计算添加可选链与空数组兜底，避免 API 缺失字段导致白屏；同时用 `reduce` 重写预测表累计库存计算，消除 `let` 重新赋值并满足 lint。
- **Sparkline**：移除“全零序列视为无数据”的逻辑，仅空数组显示“无数据”；为 `data` 参数提供默认空数组。
- **ReplenishmentPage**：表格预测趋势列对 `s.forecast_7d` 使用可选链兜底。
- **api.ts**：`fetchApi` 在反序列化后校验 `data` 字段；`getStores` / `getCategories` / `getProducts` 返回 `r.data ?? []`。
- **DashboardPage**：RankingItem 增加可选 `product_name`，商品名称列渲染 `item.product_name || item.product_id`；后端暂无真实名称时自然回退到商品编号。

### 可访问性

- **OrderForm**：`<form>` 绑定 `onSubmit`，主按钮改为 `type="submit"`，支持回车提交。
- **DataTable**：排序表头内部渲染 `<button>`，并补充 `scope="col"` 与 `aria-sort`；`rowKey` 改为 required prop，禁止默认使用 index。
- **DataState**：loading / error / empty / insufficient_data / forecast_unavailable 状态文案容器增加 `role="status" aria-live="polite"`，便于屏幕阅读器播报。
- **HelpDrawer**：新增 Esc 关闭与焦点归还触发按钮的测试。
- **useKeyboardShortcut**：增加输入框/文本框/可编辑元素焦点保护，避免在表单内输入单键时误触发全局快捷键。

### 状态管理 / 性能

- **AnalysisContext**：
  - 增加 URL → state 反向同步，浏览器前进/后退或外链改变 URL 时 context state 会跟随更新；
  - 明确数据源优先级：URL 参数 > sessionStorage > 默认值；
  - Provider value 使用 `useMemo` 包裹，避免消费者在 state 未变化时无意义重渲染。
- **ProductDetailPage**：移除多余的 `localCategory` state，类别选择直接复用全局 `globalCategory`，消除 effect 内同步 state 的 lint 警告。

### 样式 / 工程

- **index.css**：移除全局 `*` 上的 `box-shadow` 过渡，避免非合成属性动画触发重排/重绘；保留 `background-color` 等主题色过渡与 `prefers-reduced-motion` 处理。
- **HelpDrawer**：移除未使用的 `helpSections` 命名导出，解决 `react-refresh/only-export-components` lint 错误。
- **useKeyboardShortcut**：将 callbackRef 更新移入 `useEffect`，解决 `react-hooks/refs` lint 错误。

### 测试补充

新增 / 更新测试用例后总计 7 个测试文件、24 条用例：

- `Sparkline.test.tsx`：增加空数据用例，调整全零数据预期。
- `DataTable.test.tsx`：改用 `userEvent`，新增排序表头 `aria-sort` 与键盘 Enter 触发排序测试。
- `HelpDrawer.test.tsx`：新增 Esc 关闭与焦点管理测试。
- `ThemeToggle.test.tsx`：新增主题切换后 `html` 元素 class 变化断言。
- `ReplenishmentPage.test.tsx`：新增快速筛选、排序、空状态、错误重试测试。

验证结果：

```bash
cd app && npm run build   # 通过，无 TypeScript 错误
cd app && npm run test    # 7 个测试文件，24 条用例全部通过
cd app && npm run lint    # 0 errors, 0 warnings
```

### 已知限制更新

1. **商品名称**：`RankingItem` 已增加可选 `product_name` 字段并在单元格中兜底显示 `product_id`；后端返回真实名称后将自动展示。

## 第二轮代码审查修复（2026-07-13）

对 `app/src/` 进行第二轮系统性审查，聚焦运行时风险、一致性与代码质量。

### High — 运行时风险

- **H1 统一 catch 块类型守卫**：新建 `lib/errors.ts`，提供 `isAbortError()` 和 `getErrorMessage()` 工具函数；替换 `OrderForm`、`DashboardPage`、`RankingPage`、`ProductDetailPage`、`ReplenishmentPage` 中共 11 处 `(e as Error)?.name` 模式，改用 `instanceof Error` 安全判断。
- **H2 sessionStorage 反序列化校验**：`analysisContext.tsx` 的 `loadStoredState()` 在 `JSON.parse` 后增加运行时类型检查，逐字段校验 `storeId`、`range`（含 `isValidRange` 守卫）、`category`、`inventoryStatus`、`productId` 的类型与合法性，丢弃不合法数据回退默认值。
- **H3 event.target 类型守卫**：`RankingPage.tsx`、`DashboardPage.tsx`、`useKeyboardShortcut.ts` 中的 `event.target as HTMLElement` 改用 `instanceof HTMLElement` 守卫，避免非元素 target 导致的运行时崩溃。

### Medium — 一致性与可维护性

- **M1 cardBase 去重**：`FilterBar.tsx` 和 `RankingPage.tsx` 中重复的 `cardBase` 内联样式对象移除，改为 Tailwind 类 `rounded-xl border border-[var(--border-color)] bg-[var(--card-surface)]`。
- **M3 魔法字符串提取**：新建 `lib/constants.ts`，集中管理 `DEFAULT_PRODUCT_ID`、`DEFAULT_TIME_RANGE`、`PARAM_STORE_ID`、`PARAM_PRODUCT_ID`、`PARAM_QUANTITY`、`ALL_TIME_RANGE_DAYS`、`REPLENISHMENT_DISPLAY_LIMIT`；更新 `analysisContext.tsx`、`Layout.tsx`、`ProductDetailPage.tsx`、`OrderPage.tsx`、`OrderForm.tsx`、`DashboardPage.tsx`、`ReplenishmentPage.tsx` 引用。
- **M5 transition-all 收窄**：`Layout.tsx` 导航链接 `transition-all` 改为 `transition-colors`；`StoreSelector.tsx` 选择框 `transition-all` 改为 `transition-colors`；`Layout.tsx` 顶栏 `style={{ height: '56px' }}` 改为 `h-14`。

### Low — 代码质量

- **L1 inline style → Tailwind**：`FilterBar.tsx`（9 处）、`DataState.tsx`（9 处）、`RankingPage.tsx`（24 处）、`StoreSelector.tsx`（3 处）的 `style={{}}` 迁移为 Tailwind 任意值类，消除运行时 JS 样式开销并启用 hover/focus 伪类支持。
- **L2 useKeyboardShortcut ref 赋值**：`callbackRef.current = callback` 移入 `useEffect`（无依赖数组），满足 `react-hooks/refs` lint 规则。
- **L3 ReplenishmentPage let→const**：`displayed` 计算从 `let list = [...suggestions]` + 原地 filter/sort 重构为 `const filtered = suggestions.filter(...)` + `[...filtered].sort(...)` 链式不可变操作。
- **L4 import.meta.env 去可选链**：`api.ts` 中 `import.meta.env?.VITE_API_BASE_URL` 改为 `import.meta.env.VITE_API_BASE_URL`（Vite 环境下 `env` 始终存在）。

验证结果：

```bash
cd app && npm run build   # 通过，无 TypeScript 错误
cd app && npm run test    # 7 个测试文件，24 条用例全部通过
cd app && npm run lint    # 0 errors, 0 warnings
```
