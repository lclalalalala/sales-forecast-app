# Sephora 零售门店库存与需求预测系统 — 设计系统

> 版本: 1.0
> 适用项目: 零售门店库存与需求预测系统
> 主题模式: Light / Dark 双模式

---

## 1. 设计哲学

**核心风格**: 专业数据仪表盘（Dashboard）+ 编辑式界面（Editorial Precision）。

界面传递技术可靠性和控制感，服务于高信息密度的数据决策场景。整体视觉保持克制、现代、专业，不过度装饰，以数据和状态为核心。

- **信息优先**: 数据、图表、状态标签是视觉焦点。
- **呼吸感**: 通过 4px 基间距网格和充足的留白平衡高密度信息。
- **一致性**: 所有颜色、字体、间距、圆角均来自本设计系统的 token，禁止随意取值。
- **可访问性**: Light 与 Dark 模式均须满足 WCAG 2.1 AA 对比度要求。

---

## 2. 颜色系统

所有颜色以 CSS 自定义属性（变量）形式定义，按主题作用域切换。设计稿与实现代码必须使用下表中的 token 名称，禁止直接使用裸色值。

### 2.1 语义化颜色 Token

| Token | Light Mode | Dark Mode | 用途 |
|-------|------------|-----------|------|
| `--bg-page` | `#FAFAFA` | `#121212` | 页面主背景 |
| `--bg-surface` | `#FFFFFF` | `#1E1E1E` | 卡片、面板、弹窗、导航背景 |
| `--bg-surface-hover` | `#F5F5F5` | `#2A2A2A` | 卡片/行悬停背景 |
| `--bg-surface-active` | `rgba(99,102,241,0.08)` | `rgba(0,229,255,0.10)` | 选中态背景 |
| `--border-subtle` | `#E8E8EC` | `#2C2C2E` | 卡片边框、分隔线、输入框边框 |
| `--border-focus` | `#6366F1` | `#00E5FF` | 焦点环、激活边框 |
| `--text-primary` | `#0A0A0A` | `#FFFFFF` | 主标题、正文、关键标签 |
| `--text-secondary` | `#6B6B6B` | `#98989D` | 次要文字、说明、元数据 |
| `--text-tertiary` | `#9C9C9C` | `#636366` | 占位符、时间戳、辅助信息 |
| `--accent-primary` | `#6366F1` | `#00E5FF` | 主强调色：CTA、链接、选中、焦点、数据高亮 |
| `--accent-primary-hover` | `#4F46E5` | `#80F0FF` | 主强调色悬停 |
| `--accent-secondary` | `#20970B` | `#32D74B` | 成功、充足状态 |
| `--accent-warning` | `#F59E0B` | `#FF9500` | 警告、偏低状态 |
| `--accent-error` | `#EF4444` | `#FF453A` | 错误、紧缺、删除操作 |
| `--status-bg-success` | `rgba(32,151,11,0.10)` | `rgba(50,215,75,0.10)` | 成功/充足状态背景 |
| `--status-bg-info` | `rgba(99,102,241,0.10)` | `rgba(0,229,255,0.10)` | 正常/信息状态背景 |
| `--status-bg-warning` | `rgba(245,158,11,0.10)` | `rgba(255,149,0,0.10)` | 警告/偏低状态背景 |
| `--status-bg-error` | `rgba(239,68,68,0.10)` | `rgba(255,69,58,0.10)` | 错误/紧缺状态背景 |

### 2.2 图表专用颜色

| Token | Light Mode | Dark Mode | 用途 |
|-------|------------|-----------|------|
| `--chart-sales` | `#6366F1` | `#00E5FF` | 实际销量 |
| `--chart-demand` | `#20970B` | `#32D74B` | 需求量 |
| `--chart-inventory` | `#F59E0B` | `#FF9500` | 库存水位 |
| `--chart-forecast` | `#9333EA` | `#BF5AF2` | 预测需求 |
| `--chart-grid` | `rgba(0,0,0,0.05)` | `rgba(255,255,255,0.05)` | 图表网格线 |
| `--chart-axis-text` | `#6B6B6B` | `#98989D` | 坐标轴文字 |

### 2.3 状态色映射

| 状态 | 背景 Token | 文字/图标 Token | 使用场景 |
|------|------------|-----------------|----------|
| 充足 | `--status-bg-success` | `--accent-secondary` | 库存充足、正向指标 |
| 正常 | `--status-bg-info` | `--accent-primary` | 正常范围、信息提示 |
| 偏低 | `--status-bg-warning` | `--accent-warning` | 库存偏低、需要注意 |
| 紧缺 | `--status-bg-error` | `--accent-error` | 库存紧缺、紧急预警 |

### 2.4 颜色使用原则

- **Light 模式**: 以近黑文字、白色表面、靛蓝强调色构建清晰层级。
- **Dark 模式**: 以深色背景、青色强调色、高饱和数据色突出图表与状态。
- 禁止在文字上使用纯黑 `#000000` 或纯白 `#FFFFFF`（除非 Dark 模式主文字允许 `#FFFFFF`）。
- 交互元素必须使用 `--accent-primary`；禁止将强调色用于静态装饰。
- 所有状态背景色必须基于语义 token，确保双模式下对比度一致。

---

## 3. 字体系统

### 3.1 字体族

| 用途 | 字体 | 来源 |
|------|------|------|
| 显示/标题 | General Sans | Fontshare |
| 正文/UI | DM Sans | Google Fonts |
| 数字/KPI/代码 | JetBrains Mono | Google Fonts |

### 3.2 字号与字重

| Token | 字体 | 大小 | 字重 | 行高 | 字间距 | 用途 |
|-------|------|------|------|------|--------|------|
| `--text-display` | General Sans | 48px | 700 | 1.1 | -0.03em | 页面大标题 |
| `--text-headline` | General Sans | 32px | 700 | 1.2 | -0.02em | 区块标题 |
| `--text-section` | General Sans | 24px | 600 | 1.3 | -0.02em | 小标题 |
| `--text-subhead` | DM Sans | 18px | 500 | 1.4 | -0.01em | 副标题 |
| `--text-body` | DM Sans | 15px | 400 | 1.6 | 0 | 正文 |
| `--text-ui` | DM Sans | 14px | 500 | 1.5 | 0 | UI 标签、按钮 |
| `--text-small` | DM Sans | 13px | 400 | 1.5 | 0 | 表格、KPI 标签 |
| `--text-caption` | DM Sans | 12px | 400 | 1.4 | 0 | 说明、时间戳 |
| `--text-overline` | DM Sans | 11px | 500 | 1.3 | 0.05em | 大写标签 |
| `--text-kpi` | JetBrains Mono | 32px | 700 | 1.2 | -0.02em | KPI 数字 |
| `--text-kpi-label` | DM Sans | 13px | 400 | 1.4 | 0 | KPI 标签 |
| `--text-code` | JetBrains Mono | 13px | 400 | 1.5 | 0 | 代码、数值 |

### 3.3 字体使用原则

- 标题使用 General Sans，正文与 UI 使用 DM Sans，严禁互换。
- 单屏内不要使用超过两种字重。
- 数字类信息（KPI、库存量、百分比）优先使用 JetBrains Mono，增强数据可读性。

---

## 4. 间距系统

### 4.1 基础间距 Token

| Token | 值 | 用途 |
|-------|-----|------|
| `--space-1` | 4px | 图标与文字间隙、紧凑内边距 |
| `--space-2` | 8px | 小组件内部间隙 |
| `--space-3` | 12px | 列表行内边距、按钮小间距 |
| `--space-4` | 16px | 标准卡片内边距、组件间隙 |
| `--space-5` | 20px | 卡片内边距（大屏）、网格间隙 |
| `--space-6` | 24px | 页面级水平内边距、区块间隙 |
| `--space-8` | 32px | 区块间距（移动端） |
| `--space-10` | 40px | 区块间距（平板端） |
| `--space-12` | 48px | 区块间距（桌面端） |
| `--space-16` | 64px | 大区块间距 |
| `--space-20` | 80px | 页面顶部/底部大间距 |
| `--space-24` | 96px | 特大间距 |

### 4.2 组件内边距

| 组件 | 内边距 |
|------|--------|
| Button Small | 8px × 12px |
| Button Medium | 10px × 16px |
| Button Large | 12px × 24px |
| Input | 10px × 14px |
| Card | 16px–20px |
| KPI Card | 20px |
| Table Cell | 12px × 16px |
| Chip | 4px × 12px |
| List Row | 12px × 16px |

### 4.3 布局常量

| Token | 值 | 用途 |
|-------|-----|------|
| `--container-max` | 1280px | 内容区最大宽度 |
| `--nav-height` | 56px | 顶部导航高度 |
| `--page-padding-x` | 24px | 页面水平内边距 |
| `--section-gap` | 24px–48px | 区块间距 |
| `--card-grid-gap` | 20px–24px | 卡片网格间隙 |

---

## 5. 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-sm` | 4px | 标签、chip、行内代码 |
| `--radius-md` | 6px | 按钮、输入框、下拉选择 |
| `--radius-lg` | 8px | 元数据卡片、下拉面板 |
| `--radius-xl` | 12px | 卡片、搜索栏、图表卡片 |
| `--radius-full` | 9999px | 头像、状态点、 pill 标签 |

---

## 6. 阴影与 elevation

设计系统使用克制的阴影，仅在悬停、焦点、弹出层使用。

| Token | Light Mode | Dark Mode | 用途 |
|-------|------------|-----------|------|
| `--shadow-card-hover` | `0 8px 30px rgba(0,0,0,0.08)` | `0 8px 30px rgba(0,0,0,0.25)` | 卡片悬停 |
| `--shadow-button-glow` | `0 4px 12px rgba(99,102,241,0.35)` | `0 4px 12px rgba(0,229,255,0.35)` | 主按钮悬停光晕 |
| `--shadow-dropdown` | `0 10px 40px rgba(0,0,0,0.12)` | `0 10px 40px rgba(0,0,0,0.40)` | 下拉、弹窗 |
| `--focus-ring` | `0 0 0 3px rgba(99,102,241,0.12)` | `0 0 0 3px rgba(0,229,255,0.20)` | 焦点环 |

- 静态元素不使用阴影。
- 导航栏使用 `backdrop-blur` 而非阴影表达层级。
- 卡片悬停时配合 `-2px` 垂直位移。

---

## 7. 组件规范

### 7.1 按钮 (Button)

| 类型 | 背景 | 边框 | 文字 | 悬停效果 |
|------|------|------|------|----------|
| Primary | `--accent-primary` | none | `#FFFFFF` / `#121212`（Dark 模式下若需要） | 背景变 `--accent-primary-hover`，上移 1px，添加 glow 阴影 |
| Secondary | transparent | `1px solid --border-subtle` | `--text-primary` | 背景变为 `--bg-surface-hover` |
| Ghost | transparent | none | `--text-secondary` | 文字变为 `--text-primary`，背景 `--bg-surface-hover` |
| Destructive | transparent | `1px solid --accent-error` | `--accent-error` | 背景变为 `--status-bg-error` |

- 圆角: `--radius-md`
- 字号: `--text-ui`
- 高度: Small 32px / Medium 38px / Large 44px
- 所有按钮悬停时上移 1px

### 7.2 卡片 (Card)

```css
card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

card:hover {
  background: var(--bg-surface-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}
```

### 7.3 输入框 / 选择器 (Input / Select)

```css
input, select {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 14px;
  font-size: var(--text-ui);
}

input:focus, select:focus {
  border-color: var(--border-focus);
  box-shadow: var(--focus-ring);
}

input::placeholder {
  color: var(--text-tertiary);
}
```

### 7.4 标签 / Chip

- 形状: pill（`--radius-full`）
- 背景: `--bg-surface-hover`
- 文字: `--text-secondary`
- 字号: `--text-caption`
- 内边距: 4px × 12px
- Active: 背景 `--accent-primary`，文字 `#FFFFFF`

### 7.5 状态标签 (Status Badge)

形状同 Chip，颜色使用 2.3 状态色映射。

### 7.6 表格 (Table)

```css
table-header {
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-caption);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-subtle);
  padding: var(--space-3) var(--space-4);
}

table-row {
  background: transparent;
  border-bottom: 1px solid var(--border-subtle);
  padding: var(--space-3) var(--space-4);
  transition: background 0.15s ease;
}

table-row:hover {
  background: rgba(99,102,241,0.04); /* Light */
  background: rgba(255,255,255,0.03); /* Dark */
}
```

### 7.7 导航栏 (Navigation)

```css
nav {
  position: sticky;
  top: 0;
  height: var(--nav-height);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  backdrop-filter: blur(12px);
  padding: 0 var(--space-6);
}
```

- 链接默认色: `--text-secondary`
- 链接悬停: `--text-primary`，背景 `--bg-surface-hover`
- 链接选中: `--accent-primary`，背景 `--bg-surface-active`

### 7.8 搜索栏 (Search)

- 形状: 圆角条（`--radius-xl`）
- 背景: `--bg-surface`
- 边框: `1px solid --border-subtle`
- 左侧搜索图标，右侧 ⌘K 快捷键提示

### 7.9 KPI 卡片

```
┌─────────────────────────────┐
│ [图标]  KPI 标签              │
│                             │
│ 32,456                      │  ← KPI 数字 (JetBrains Mono Bold 32px)
│                             │
│ [状态标签]                   │
└─────────────────────────────┘
```

- 图标使用 `--text-secondary`
- 数字使用 `--text-kpi`，颜色 `--text-primary`
- 状态标签使用 2.3 状态色映射

---

## 8. 图表与数据可视化规范

### 8.1 折线图

| 数据系列 | 颜色 Token | 线宽 | 样式 |
|----------|------------|------|------|
| 实际销量 | `--chart-sales` | 2px | 实线 |
| 需求量 | `--chart-demand` | 2px | 虚线 |
| 库存水位 | `--chart-inventory` | 1.5px | 实线 |

- 网格线: `--chart-grid`
- 坐标轴文字: `--chart-axis-text`，12px
- Tooltip: `--bg-surface` 背景，`--text-primary` 文字，`--radius-lg` 圆角

### 8.2 柱状图

| 数据系列 | 颜色 Token | 圆角 |
|----------|------------|------|
| 预测需求 | `--chart-forecast` | 顶部 6px |

### 8.3 数据点 / 迷你图

- 使用语义颜色表示状态（充足、正常、偏低、紧缺）。
- 悬停时数据点放大 1.2 倍，显示 Tooltip。

---

## 9. 布局规范

### 9.1 页面结构

```
┌──────────────────────────────────────────────────────┐
│  导航栏 (56px)                                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  页面标题 + 筛选工具栏                                 │
│  ┌─────────────────────────────────────────────────┐ │
│  │  门店 | 时间 | 类别 | 库存状态                     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ KPI Card │ │ KPI Card │ │ KPI Card │ │ KPI Card ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  趋势图卡片                                       │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────┐ ┌─────────────────────┐ │
│  │  Top 5 排名卡片          │ │  Bottom 5 排名卡片   │ │
│  └─────────────────────────┘ └─────────────────────┘ │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 9.2 响应式断点

| 断点 | 宽度 | 布局变化 |
|------|------|---------|
| Mobile | < 768px | 1 列 KPI，1 列排名，筛选堆叠，侧边抽屉导航 |
| Tablet | 768px – 1279px | 2 列 KPI，1 列排名 |
| Desktop | >= 1280px | 4 列 KPI，2 列排名 |

### 9.3 容器

- 最大宽度: `--container-max`
- 水平内边距: `--page-padding-x`
- 居中对齐

---

## 10. 动效规范

| 效果 | 时长 | 缓动函数 |
|------|------|---------|
| 按钮悬停 | 150ms | ease |
| 卡片悬停 | 200ms | ease |
| 行悬停 | 150ms | ease |
| 页面切换 | 300ms | ease-out |
| 数据加载淡入 | 400ms | ease-in-out |
| Tooltip 出现 | 150ms | ease-out |
| 主题切换 | 250ms | ease-in-out |

-  prefers-reduced-motion 启用时，禁用非必要动画。

---

## 11. 交互状态原则 (Trigger-Target 分离)

Hover、Focus、Selected 等交互状态，应由稳定的父容器（Trigger）承载，子元素（Target）各自响应。禁止在同一个元素上同时做"触发"和"执行"。

**推荐写法 (Tailwind `group` + `group-hover`):**

```html
<!-- Trigger: 父容器承载 hover 状态 -->
<div class="group">
  <!-- Target: 图标在 hover 时放大 -->
  <Icon class="transition-transform group-hover:scale-110" />
  <!-- Target: 文字在 hover 时变色 -->
  <span class="transition-colors group-hover:text-[var(--text-primary)]">
    标签
  </span>
  <!-- Target: 数字在 hover 时位移 -->
  <span class="transition-all group-hover:translate-x-1">
    32,456
  </span>
</div>
```

**禁止写法 (`onMouseEnter` 直接修改 currentTarget 样式):**

```html
<!-- 错误: Trigger 和 Target 是同一个元素 -->
<div
  onMouseEnter={(e) => (e.currentTarget.style.background = '...')}
  onMouseLeave={(e) => (e.currentTarget.style.background = '...')}
>
  内容
</div>
```

---

## 12. 主题切换机制

- 主题状态由 CSS 类 `.theme-light` / `.theme-dark` 控制，挂载在 `<html>` 元素上。
- 所有颜色、阴影 token 必须在 `.theme-light` 和 `.theme-dark` 作用域下分别定义。
- 主题切换应保存用户偏好到 `localStorage`，并支持跟随系统 `prefers-color-scheme`。
- 切换动画时长 250ms，通过 CSS transition 在支持的颜色属性上生效。
- 主题切换按钮应位于导航栏右侧，图标反映当前主题。

---

## 13. Do's and Don'ts

### Do

- 使用本文件定义的 token 名称，禁止在代码中直接写死色值。
- 同时设计 Light 与 Dark 模式下的样式。
- 使用 4px 间距网格对齐所有 padding、margin、gap。
- 标题使用 General Sans，正文/UI 使用 DM Sans，数字使用 JetBrains Mono。
- 为交互状态提供足够的颜色对比。
- 在 `prefers-reduced-motion` 下减少或禁用动画。

### Don't

- 不要将 `--accent-primary` 用于非交互装饰。
- 不要混用圆角值（如把按钮圆角用于卡片）。
- 不要在静态元素上使用阴影。
- 不要在一个屏幕上使用超过两种字重。
- 不要忽略 Light 模式的可访问性对比度。
