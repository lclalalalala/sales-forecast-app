import { useState } from 'react'

// ── Architecture Diagram (SVG) ──────────────────────────────────────────
function ArchitectureDiagram() {
  return (
    <svg viewBox="0 0 800 520" className="w-full" role="img" aria-label="System architecture diagram">
      {/* Frontend Layer */}
      <rect x="250" y="10" width="300" height="56" rx="12" fill="var(--accent-primary)" opacity="0.12" stroke="var(--accent-primary)" strokeWidth="1.5" />
      <text x="400" y="44" textAnchor="middle" fill="var(--text-primary)" fontSize="15" fontWeight="600">Frontend (React + TypeScript)</text>

      {/* Arrow */}
      <line x1="400" y1="66" x2="400" y2="100" stroke="var(--text-tertiary)" strokeWidth="1.5" markerEnd="url(#arrow)" />

      {/* API Layer */}
      <rect x="250" y="100" width="300" height="56" rx="12" fill="var(--accent-primary)" opacity="0.12" stroke="var(--accent-primary)" strokeWidth="1.5" />
      <text x="400" y="134" textAnchor="middle" fill="var(--text-primary)" fontSize="15" fontWeight="600">API Layer (Flask REST)</text>

      {/* Arrow */}
      <line x1="400" y1="156" x2="400" y2="190" stroke="var(--text-tertiary)" strokeWidth="1.5" markerEnd="url(#arrow)" />

      {/* Infrastructure Layer */}
      <rect x="250" y="190" width="300" height="56" rx="12" fill="var(--accent-secondary)" opacity="0.12" stroke="var(--accent-secondary)" strokeWidth="1.5" />
      <text x="400" y="218" textAnchor="middle" fill="var(--text-primary)" fontSize="15" fontWeight="600">Infrastructure Layer</text>
      <text x="400" y="236" textAnchor="middle" fill="var(--text-secondary)" fontSize="11">CSV Repositories · Config · In-Memory Query</text>

      {/* Arrow down-left to Data Processing */}
      <line x1="320" y1="246" x2="220" y2="310" stroke="var(--text-tertiary)" strokeWidth="1.5" markerEnd="url(#arrow)" />
      {/* Arrow down-right to Forecast */}
      <line x1="480" y1="246" x2="580" y2="310" stroke="var(--text-tertiary)" strokeWidth="1.5" markerEnd="url(#arrow)" />

      {/* Data Processing Layer */}
      <rect x="40" y="310" width="340" height="56" rx="12" fill="var(--accent-warning)" opacity="0.12" stroke="var(--accent-warning)" strokeWidth="1.5" />
      <text x="210" y="338" textAnchor="middle" fill="var(--text-primary)" fontSize="15" fontWeight="600">Data Processing Layer (Offline Pipeline)</text>
      <text x="210" y="356" textAnchor="middle" fill="var(--text-secondary)" fontSize="11">8-Step ETL · Fact &amp; Dimension Tables</text>

      {/* Forecast Layer */}
      <rect x="420" y="310" width="340" height="56" rx="12" fill="var(--accent-error)" opacity="0.10" stroke="var(--accent-error)" strokeWidth="1.5" />
      <text x="590" y="338" textAnchor="middle" fill="var(--text-primary)" fontSize="15" fontWeight="600">Forecast Layer (Ensemble Model)</text>
      <text x="590" y="356" textAnchor="middle" fill="var(--text-secondary)" fontSize="11">Recent Avg · DOW Pattern · Trend · Seasonal</text>

      {/* Arrow from Data Processing to Forecast */}
      <line x1="380" y1="338" x2="420" y2="338" stroke="var(--text-tertiary)" strokeWidth="1.5" markerEnd="url(#arrow)" />

      {/* Raw Data */}
      <rect x="40" y="420" width="340" height="44" rx="10" fill="var(--bg-surface-hover)" stroke="var(--border-subtle)" strokeWidth="1" />
      <text x="210" y="448" textAnchor="middle" fill="var(--text-secondary)" fontSize="13">📄 Raw CSV (sales_data.csv)</text>

      {/* Pre-computed Output */}
      <rect x="420" y="420" width="340" height="44" rx="10" fill="var(--bg-surface-hover)" stroke="var(--border-subtle)" strokeWidth="1" />
      <text x="590" y="442" textAnchor="middle" fill="var(--text-secondary)" fontSize="13">📊 Pre-computed Fact Tables</text>
      <text x="590" y="458" textAnchor="middle" fill="var(--text-tertiary)" fontSize="10">forecast · error_stats · replenishment · metrics</text>

      {/* Arrows to/from data */}
      <line x1="210" y1="366" x2="210" y2="420" stroke="var(--text-tertiary)" strokeWidth="1" strokeDasharray="4 3" markerEnd="url(#arrow)" />
      <line x1="590" y1="366" x2="590" y2="420" stroke="var(--text-tertiary)" strokeWidth="1" strokeDasharray="4 3" markerEnd="url(#arrow)" />

      {/* Arrow from fact tables back to Infrastructure */}
      <path d="M 760 420 Q 780 300 550 220" fill="none" stroke="var(--text-tertiary)" strokeWidth="1" strokeDasharray="4 3" markerEnd="url(#arrow)" />

      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 Z" fill="var(--text-tertiary)" />
        </marker>
      </defs>
    </svg>
  )
}

// ── Collapsible Section ─────────────────────────────────────────────────
function Section({ title, defaultOpen = false, children }: {
  title: string
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-[var(--bg-surface-hover)] transition-colors"
      >
        <span className="text-base font-semibold text-[var(--text-primary)]">{title}</span>
        <svg className={`w-5 h-5 text-[var(--text-tertiary)] transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && <div className="px-5 pb-5 border-t border-[var(--border-subtle)]">{children}</div>}
    </div>
  )
}

// ── Formula Block ───────────────────────────────────────────────────────
function Formula({ label, formula, note }: { label: string; formula: string; note?: string }) {
  return (
    <div className="mb-3">
      <div className="text-sm font-medium text-[var(--text-primary)] mb-1">{label}</div>
      <code className="block px-4 py-2.5 rounded-lg bg-[var(--bg-surface-hover)] text-sm text-[var(--accent-primary)] font-mono leading-relaxed border border-[var(--border-subtle)]">
        {formula}
      </code>
      {note && <div className="text-xs text-[var(--text-tertiary)] mt-1">{note}</div>}
    </div>
  )
}

// ── Pipeline Step ───────────────────────────────────────────────────────
function Step({ num, title, desc }: { num: number; title: string; desc: string }) {
  return (
    <div className="flex gap-3 items-start">
      <span className="flex-none w-7 h-7 rounded-full bg-[var(--accent-primary)] text-white text-xs font-bold flex items-center justify-center mt-0.5">{num}</span>
      <div>
        <div className="text-sm font-semibold text-[var(--text-primary)]">{title}</div>
        <div className="text-sm text-[var(--text-secondary)] leading-relaxed">{desc}</div>
      </div>
    </div>
  )
}

// ── Layer Tag ───────────────────────────────────────────────────────────
function LayerTag({ color, label }: { color: string; label: string }) {
  const colors: Record<string, string> = {
    indigo: 'bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] border-[var(--accent-primary)]/20',
    green: 'bg-[var(--accent-secondary)]/10 text-[var(--accent-secondary)] border-[var(--accent-secondary)]/20',
    amber: 'bg-[var(--accent-warning)]/10 text-[var(--accent-warning)] border-[var(--accent-warning)]/20',
    red: 'bg-[var(--accent-error)]/10 text-[var(--accent-error)] border-[var(--accent-error)]/20',
  }
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium border ${colors[color]}`}>{label}</span>
}

// ── Table Helper ────────────────────────────────────────────────────────
function DataTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-[var(--border-subtle)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--bg-surface-hover)]">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-2.5 text-left font-semibold text-[var(--text-primary)] whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-t border-[var(--border-subtle)]">
              {row.map((cell, ci) => (
                <td key={ci} className="px-4 py-2.5 text-[var(--text-secondary)] whitespace-nowrap">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main Page ───────────────────────────────────────────────────────────
export default function TechnicalDocPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-page)]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* Header */}
        <header className="space-y-2">
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">技术架构文档</h1>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl">
            本文档面向开发人员，介绍系统的分层架构、各层职责与调用关系，以及核心业务逻辑的实现方式。
          </p>
        </header>

        {/* 1. Architecture Overview */}
        <Section title="1 · 分层架构总览" defaultOpen>
          <div className="space-y-5 mt-3">
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              系统采用 <strong className="text-[var(--text-primary)]">离线计算 + 在线服务</strong> 分离架构。
              重计算（预测、补货）全部在离线管线中批量完成，在线 API 仅读取预计算结果，保证响应速度。
            </p>

            <ArchitectureDiagram />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
              {[
                { color: 'indigo', layer: 'Frontend Layer', desc: 'React + TypeScript，仅负责渲染与交互，不包含任何业务公式。' },
                { color: 'indigo', layer: 'API Layer', desc: 'Flask REST 接口，参数校验、错误处理、响应组装。' },
                { color: 'green', layer: 'Infrastructure Layer', desc: 'CSV 仓库，启动时全量加载到内存，提供过滤查询。' },
                { color: 'amber', layer: 'Data Processing Layer', desc: '8 步离线 ETL 管线，产出所有预计算事实表。' },
                { color: 'red', layer: 'Forecast Layer', desc: '无状态集成预测引擎，被管线第 5 步调用。' },
              ].map(({ color, layer, desc }) => (
                <div key={layer} className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface-hover)] p-3">
                  <LayerTag color={color} label={layer} />
                  <p className="text-sm text-[var(--text-secondary)] mt-2 leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </Section>

        {/* 2. Calling Relationships */}
        <Section title="2 · 调用关系">
          <div className="mt-3 space-y-4">
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              请求从左到右流动，数据从右到左返回。离线管线在系统启动前独立运行。
            </p>
            <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface-hover)] p-4 font-mono text-xs text-[var(--text-secondary)] leading-loose">
              <div>Frontend ──HTTP──▶ API Layer ──▶ Query Class ──▶ Repository ──▶ CSV (内存)</div>
              <div className="mt-1 text-[var(--text-tertiary)]">│ (离线，启动前运行)</div>
              <div>Pipeline ──▶ Forecast Layer ──▶ CSV (磁盘)</div>
            </div>
            <DataTable
              headers={['调用方', '被调用方', '说明']}
              rows={[
                ['Frontend', 'API Layer', 'HTTP GET /api/* 请求 JSON 数据'],
                ['API Layer', 'Query Class', '解析参数 → 调用 query.execute()'],
                ['Query Class', 'Repository', '从内存 DataFrame 中过滤、聚合'],
                ['Pipeline (Step 5)', 'Forecast Layer', '为所有 (store, product) 生成 7 天预测'],
                ['Pipeline (Step 7)', 'Forecast + Error Stats', '基于预测结果和误差计算补货量'],
              ]}
            />
          </div>
        </Section>

        {/* 3. Data Processing Layer */}
        <Section title="3 · 数据处理层（离线管线）">
          <div className="mt-3 space-y-4">
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              离线管线由 <code className="text-[var(--accent-primary)] bg-[var(--bg-surface-hover)] px-1.5 py-0.5 rounded text-xs">offline_calculation/pipeline.py</code> 编排，
              依次执行 8 个步骤，将原始 CSV 转换为所有预计算事实表。
            </p>
            <div className="space-y-4">
              <Step num={1} title="数据加载与校验" desc="读取原始 CSV，重命名列，检查空值、重复键、负值、库存平衡。生成 data_quality_report.json。" />
              <Step num={2} title="构建事实表" desc="生成 fact_daily_inventory_sales：日期、门店、商品、期初库存、销量、订购量、期末库存。缺失日期用前值填充，销量补零。" />
              <Step num={3} title="构建维度表" desc="生成 dim_store（门店）和 dim_product（商品）维度表。" />
              <Step num={4} title="估算前置时间 K" desc="对每个 (store, product)，在 [0,7] 范围内用 MSE 最小化估算前置天数 K，失败时回退 K=2。" />
              <Step num={5} title="生成销量预测" desc="调用 Forecast Layer，为所有组合生成滚动 7 天预测及 95% 预测区间。" />
              <Step num={6} title="计算预测误差统计" desc="取 horizon=3 的误差，用 30 天滚动窗口计算标准差 sigma。不足 2 条时回退为 1.0。" />
              <Step num={7} title="计算补货建议" desc="核心补货逻辑，详见第 5 节。输出 fact_daily_replenishment.csv。" />
              <Step num={8} title="生成销售指标与商品摘要" desc="按门店/日期/品类聚合日销指标；为每个商品生成 5 个时间窗口的销售摘要。" />
            </div>
          </div>
        </Section>

        {/* 4. Forecast Layer */}
        <Section title="4 · 销量预测层">
          <div className="mt-3 space-y-4">
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              预测引擎位于 <code className="text-[var(--accent-primary)] bg-[var(--bg-surface-hover)] px-1.5 py-0.5 rounded text-xs">forecast/</code> 目录，
              是一个无状态、纯函数的集成模型，不依赖 Web 框架或数据库。
            </p>

            <div className="rounded-lg border border-[var(--border-subtle)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">集成预测公式</h4>
              <Formula
                label="单日预测"
                formula="prediction = (recent_avg × 0.3 + dow_avg × 0.4) × trend_factor × 0.7 + recent_avg × 0.3 × seasonal_factor"
              />
              <Formula label="recent_avg" formula="最近 14 天 units_sold 的均值" />
              <Formula label="dow_avg" formula="最近 8 个相同星期几的历史均值（至少 4 个样本，否则回退为 recent_avg）" />
              <Formula label="trend_factor" formula="clip(last_7d_avg / last_30d_avg, 0.7, 1.3)，数据不足时为 1.0" />
              <Formula label="seasonal_factor" formula="clip(target_month_avg / recent_avg, 0.7, 1.3)，无月数据时为 1.0" />
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">预测区间</h4>
              <Formula label="95% 置信带" formula="[prediction − 1.96 × σ, prediction + 1.96 × σ]" note="σ 来自滚动一步超前误差的样本标准差" />
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">降级策略</h4>
              <p className="text-sm text-[var(--text-secondary)]">
                当历史数据不足 7 天时，返回保守的固定值 <code className="text-[var(--accent-primary)] bg-[var(--bg-surface-hover)] px-1 py-0.5 rounded text-xs">max(5, global_mean × 0.8)</code>，
                状态标记为 <code className="text-[var(--accent-warning)] bg-[var(--bg-surface-hover)] px-1 py-0.5 rounded text-xs">insufficient_data</code>。
              </p>
            </div>
          </div>
        </Section>

        {/* 5. Replenishment Logic */}
        <Section title="5 · 补货量计算逻辑">
          <div className="mt-3 space-y-4">
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              补货建议在离线管线第 7 步计算，核心思想：<strong className="text-[var(--text-primary)]">覆盖前置时间内预期需求 + 安全库存 − 现有可用库存</strong>。
            </p>

            <div className="rounded-lg border border-[var(--border-subtle)] p-4 space-y-3">
              <h4 className="text-sm font-semibold text-[var(--text-primary)]">计算步骤</h4>
              <Formula label="① 当前库存" formula="current_inventory = opening_inventory − units_sold" note="当日销售后的在手库存" />
              <Formula label="② 在途库存" formula="in_transit = Σ units_ordered（过去 K−1 天）" note="已下单未到货的总量，K=1 时为 0" />
              <Formula label="③ 前置期预测需求" formula="forecast_k_total = Σ forecast[day 1..K]" note="预测未来 K 天的销量之和" />
              <Formula label="④ 预测误差标准差" formula="σ = rolling_std(actual − forecast, 30d 窗口)" note="不足 2 条有效误差时回退为 1.0" />
              <Formula label="⑤ 安全库存" formula="safety_stock = 2.33 × σ × √K" note="z=2.33 对应 99% 服务水平" />
              <Formula label="⑥ 库存覆盖天数" formula="coverage_days = (current + in_transit) / avg_daily_sales_90d" />
              <Formula
                label="⑦ 建议补货量"
                formula="suggested = ⌈ max(0, forecast_k_total − current_inventory − in_transit + safety_stock) ⌉"
                note="结果为非负整数，向上取整"
              />
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-3">库存状态判定</h4>
              <DataTable
                headers={['覆盖天数', '状态', '含义']}
                rows={[
                  ['< 2 天', 'critical', '缺货风险，需立即补货'],
                  ['2 ~ 4 天', 'low', '库存偏低，建议补货'],
                  ['4 ~ 7 天', 'normal', '正常水平'],
                  ['> 7 天', 'sufficient', '库存充足'],
                  ['= 0（无销量）', 'undetermined', '无法判定'],
                ]}
              />
            </div>
          </div>
        </Section>

        {/* 6. API Endpoints */}
        <Section title="6 · API 接口一览">
          <div className="mt-3">
            <DataTable
              headers={['接口', '说明']}
              rows={[
                ['GET /api/health', '健康检查，返回数据加载状态'],
                ['GET /api/stores', '门店列表'],
                ['GET /api/categories', '品类列表'],
                ['GET /api/overview', '门店概览：KPI、趋势、畅销/滞销、库存状态'],
                ['GET /api/rankings', '商品销量排名，支持品类/库存/时间筛选'],
                ['GET /api/replenishment', '补货建议列表，按建议量降序'],
                ['GET /api/products/:id', '商品详情：历史、预测、补货明细'],
              ]}
            />
          </div>
        </Section>

        {/* Footer */}
        <footer className="text-xs text-[var(--text-tertiary)] text-center pt-4 pb-8 border-t border-[var(--border-subtle)]">
          配置集中于 config/business.yaml · 数据粒度为 (store_id, product_id) · 所有计算在离线管线中完成
        </footer>
      </div>
    </div>
  )
}
