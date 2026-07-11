# 前端技术需求文档

> 基于《Sephora 零售门店库存与需求预测系统 — 设计系统》实现
> 本文档聚焦前端功能实现、组件清单、主题机制与验收标准

---

## 1. 目标与范围

### 1.1 目标

为零售门店库存与需求预测系统构建一套完整的前端实现，满足以下要求：

1. 严格遵循设计系统的 Light / Dark 双模式视觉规范。
2. 实现数据仪表盘、补货建议、商品详情等核心页面。
3. 提供响应式布局，覆盖 Desktop / Tablet / Mobile 三种断点。
4. 保证高性能数据渲染、可访问性与可维护性。

### 1.2 范围

- **范围内**:
  - 全局主题与 CSS 变量系统
  - 公共组件（导航、卡片、按钮、输入、表格、图表等）
  - 业务页面（Dashboard、补货建议、商品详情）
  - 主题切换、搜索、筛选、数据可视化
- **范围外**:
  - 后端 API 具体实现（前端仅定义接口契约与 mock 数据）
  - 用户权限与认证系统（预留入口，不实现完整逻辑）

---

## 2. 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | React 18+ |
| 语言 | TypeScript |
| 样式 | Tailwind CSS 3.4+ |
| 路由 | React Router 6+ |
| 状态管理 | Zustand 或 React Context（主题、全局筛选） |
| 图表 | Recharts |
| 图标 | Lucide React |
| 构建 | Vite |
| 测试 | Vitest + React Testing Library |

---

## 3. 主题实现要求

### 3.1 CSS 变量架构

在 `src/index.css` 中定义两套主题变量：

```css
:root.theme-light {
  --bg-page: #FAFAFA;
  --bg-surface: #FFFFFF;
  /* ... 全部 Light 模式 token ... */
}

:root.theme-dark {
  --bg-page: #121212;
  --bg-surface: #1E1E1E;
  /* ... 全部 Dark 模式 token ... */
}
```

### 3.2 主题切换逻辑

- 实现 `ThemeProvider`（React Context 或 Zustand store）。
- 主题状态：`'light' | 'dark' | 'system'`。
- 当为 `'system'` 时，读取 `window.matchMedia('(prefers-color-scheme: dark)')`。
- 将用户偏好持久化到 `localStorage`，键名为 `theme-preference`。
- 在 `<html>` 元素上切换 `.theme-light` / `.theme-dark` 类。
- 主题切换按钮位于导航栏右侧，显示当前主题图标。

### 3.3 Tailwind 集成

- 使用 Tailwind 的 `theme.extend` 将设计系统 token 映射为颜色、间距、圆角、阴影、字体。
- 禁止在组件中写死色值，优先使用 Tailwind 工具类或 CSS 变量。
- 为颜色 token 配置 `darkMode: 'class'`，但本项目的 Dark 模式由 `.theme-dark` 类控制，不依赖 Tailwind 的默认 dark 策略。

---

## 4. 公共组件实现清单

| 组件 | 文件路径 | 功能要求 |
|------|----------|----------|
| `ThemeToggle` | `src/components/ThemeToggle.tsx` | 切换 Light/Dark/System 模式，图标反映当前主题 |
| `TopNav` | `src/components/Layout/TopNav.tsx` | 粘性导航，56px 高，backdrop-blur，移动端抽屉 |
| `SearchBar` | `src/components/SearchBar.tsx` | ⌘K 触发，圆角搜索条，支持快捷键 |
| `Card` | `src/components/ui/Card.tsx` | 基础卡片容器，支持 hover 动效 |
| `Button` | `src/components/ui/Button.tsx` | Primary / Secondary / Ghost / Destructive，支持尺寸 |
| `Input` | `src/components/ui/Input.tsx` | 文本输入，focus/error 状态 |
| `Select` | `src/components/ui/Select.tsx` | 下拉选择器，原生或自定义样式 |
| `Chip` | `src/components/ui/Chip.tsx` | Pill 标签，支持 active 状态 |
| `StatusBadge` | `src/components/ui/StatusBadge.tsx` | 充足/正常/偏低/紧缺 四种状态 |
| `DataTable` | `src/components/ui/DataTable.tsx` | 可排序表格，支持行 hover |
| `KpiCard` | `src/components/KpiCard.tsx` | 图标 + 标签 + 数字 + 状态 |
| `LineChart` | `src/components/charts/LineChart.tsx` | 销量/需求/库存水位折线图 |
| `BarChart` | `src/components/charts/BarChart.tsx` | 预测需求柱状图 |
| `Sparkline` | `src/components/charts/Sparkline.tsx` | 迷你趋势图，用于表格 |
| `FilterGroup` | `src/components/FilterGroup.tsx` | 筛选按钮组，支持单选 |
| `StoreSelector` | `src/components/StoreSelector.tsx` | 门店下拉选择器 |
| `Skeleton` | `src/components/ui/Skeleton.tsx` | 数据加载占位 |
| `EmptyState` | `src/components/ui/EmptyState.tsx` | 空状态展示 |

### 4.1 组件实现约束

- 所有 UI 组件必须接受 `className` 以支持外部扩展。
- 组件内部必须使用设计系统 token，禁止硬编码颜色。
- 交互状态必须遵循 Trigger-Target 分离原则（见设计系统 §11）。
- 所有可交互组件须支持 `disabled` 状态并附带合适的视觉反馈。

---

## 5. 页面实现清单

### 5.1 Dashboard 页面

**文件**: `src/pages/DashboardPage.tsx`

**功能模块**:

1. 页面标题 + 全局筛选栏
   - 门店选择器
   - 时间范围选择器（近7天 / 近30天 / 本季度 / 自定义）
   - 商品类别筛选
   - 库存状态筛选
2. KPI 卡片区域
   - 总 SKU 数
   - 库存总量
   - 预测需求总量
   - 紧缺 SKU 数
   - 每个 KPI 显示对应状态标签
3. 趋势图卡片
   - 折线图：销量、需求、库存水位随时间变化
   - 支持图例开关
4. 排名卡片
   - Top 5 热销商品
   - Bottom 5 滞销商品
   - 表格形式展示，带迷你趋势图

### 5.2 补货建议页面

**文件**: `src/pages/ReplenishmentPage.tsx`

**功能模块**:

1. 筛选栏
   - 门店
   - 商品类别
   - 库存状态（紧缺 / 偏低 / 正常 / 充足）
   - 排序方式
2. 补货建议表格
   - 列：商品名称、SKU、当前库存、预测需求、建议补货量、状态、操作
   - 行 hover 高亮
   - 操作列：查看详情、标记已处理
3. 批量操作
   - 多选行
   - 批量导出建议清单

### 5.3 商品详情页面

**文件**: `src/pages/ProductDetailPage.tsx`

**功能模块**:

1. 商品基础信息卡片
   - 名称、SKU、类别、当前库存、状态
2. 历史销量与预测图
   - 折线图 + 柱状图组合
3. 门店库存分布
   - 按门店展示库存量与状态
4. 近期补货记录
   - 时间线或表格展示

### 5.4 全局搜索页面/弹窗

**文件**: `src/components/SearchModal.tsx`

**功能**:

- ⌘K / Ctrl+K 触发
- 搜索商品、SKU、门店
- 结果列表支持键盘导航

---

## 6. 数据与接口契约

前端需 mock 以下数据接口，接口路径与结构如下：

### 6.1 Dashboard 数据

```typescript
interface DashboardSummary {
  totalSkus: number;
  totalInventory: number;
  forecastDemand: number;
  shortageSkus: number;
  kpis: KpiItem[];
}

interface TrendDataPoint {
  date: string;
  sales: number;
  demand: number;
  inventory: number;
}

interface ProductRanking {
  rank: number;
  sku: string;
  name: string;
  value: number;
  trend: number[]; // 近7天数据，用于 sparkline
  status: 'sufficient' | 'normal' | 'low' | 'critical';
}
```

### 6.2 补货建议数据

```typescript
interface ReplenishmentItem {
  id: string;
  sku: string;
  name: string;
  category: string;
  currentStock: number;
  forecastDemand: number;
  suggestedQty: number;
  status: 'sufficient' | 'normal' | 'low' | 'critical';
  storeId: string;
}
```

### 6.3 商品详情数据

```typescript
interface ProductDetail {
  sku: string;
  name: string;
  category: string;
  currentStock: number;
  status: 'sufficient' | 'normal' | 'low' | 'critical';
  history: TrendDataPoint[];
  storeDistribution: { storeId: string; storeName: string; stock: number; status: string }[];
  replenishmentHistory: { date: string; qty: number; type: string }[];
}
```

---

## 7. 响应式实现要求

- 使用 Tailwind 断点：`sm` (640px)、`md` (768px)、`lg` (1024px)、`xl` (1280px)。
- KPI 网格：
  - Desktop (`xl:`): 4 列
  - Tablet (`md:`): 2 列
  - Mobile: 1 列
- 排名卡片网格：
  - Desktop: 2 列
  - Tablet/Mobile: 1 列
- 导航栏：
  - Desktop: 水平链接
  - Mobile: 汉堡菜单 + 侧边抽屉
- 筛选栏：
  - Desktop: 水平排列
  - Mobile: 垂直堆叠或折叠为抽屉

---

## 8. 性能要求

1. 首屏加载时间 < 2s（在本地开发环境）。
2. 图表数据更新使用 Recharts 的动画过渡，避免全量重绘。
3. 大数据量表格使用虚拟滚动（可选，数据量 > 200 行时启用）。
4. 图片/图标使用 SVG，避免大图资源。
5. 启用 Tree Shaking，按需加载页面组件（React.lazy + Suspense）。

---

## 9. 可访问性要求

1. 所有按钮、链接、表单元素须有明确的 focus 样式。
2. 图表须提供替代文本或数据表格（aria-label、role）。
3. 颜色不能作为唯一信息传递方式（状态标签须同时有文字）。
4. 支持键盘导航（Tab、Enter、Escape）。
5. 遵循 `prefers-reduced-motion` 减少动画。

---

## 10. 文件结构规范

```
src/
├── components/
│   ├── ui/              # 通用 UI 组件
│   ├── charts/          # 图表组件
│   ├── Layout/          # 布局相关（TopNav、Sidebar、Footer）
│   ├── SearchBar.tsx
│   ├── ThemeToggle.tsx
│   ├── KpiCard.tsx
│   ├── FilterGroup.tsx
│   └── StoreSelector.tsx
├── pages/
│   ├── DashboardPage.tsx
│   ├── ReplenishmentPage.tsx
│   └── ProductDetailPage.tsx
├── hooks/
│   ├── useTheme.ts
│   ├── useKeyboardShortcut.ts
│   └── useDashboardData.ts
├── stores/
│   └── themeStore.ts
├── lib/
│   ├── utils.ts
│   └── mockData.ts
├── types/
│   └── index.ts
├── index.css
├── App.tsx
└── main.tsx
```

---

## 11. 实现优先级

| 优先级 | 任务 |
|--------|------|
| P0 | 全局 CSS 变量、Tailwind 配置、ThemeProvider、ThemeToggle |
| P0 | TopNav、Layout、Card、Button、Input、Select、Chip、StatusBadge |
| P0 | DashboardPage：KPI、趋势图、排名卡片 |
| P1 | ReplenishmentPage：筛选、表格、批量操作 |
| P1 | ProductDetailPage：商品信息、组合图、门店分布 |
| P2 | SearchModal（⌘K 全局搜索） |
| P2 | 响应式细节优化、骨架屏、空状态 |
| P3 | 单元测试、可访问性审计、性能优化 |

---

## 12. 验收标准

### 12.1 视觉验收

- [ ] Light 与 Dark 模式均完整呈现，无裸色值泄漏。
- [ ] 所有组件在两种模式下对比度符合 WCAG AA。
- [ ] 响应式断点切换无布局错位。
- [ ] 动画流畅，无卡顿，reduced-motion 下动画被禁用。

### 12.2 功能验收

- [ ] 主题切换即时生效，且刷新后保持用户选择。
- [ ] Dashboard 三大模块（KPI、趋势图、排名）数据正确渲染。
- [ ] 补货建议表格支持筛选、排序、行选择。
- [ ] 商品详情页展示完整信息。
- [ ] ⌘K 搜索可触发并展示结果。

### 12.3 代码验收

- [ ] 所有 UI 组件使用设计系统 token。
- [ ] TypeScript 类型完整，无 `any` 滥用。
- [ ] 组件实现遵循 Trigger-Target 分离原则。
- [ ] 通过 ESLint / Prettier 检查。
- [ ] 核心组件具备单元测试。

---

## 13. 参考文档

- [设计系统](./design_system.md)
