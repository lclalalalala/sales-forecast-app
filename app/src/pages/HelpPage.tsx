/**
 * 帮助文档页 - HelpPage
 * =====================
 * 补货系统完整说明，供门店店长理解补货逻辑。
 */

import { Link } from 'react-router-dom';
import {
  HelpCircle, ArrowLeft, Package, Clock, TrendingUp, ShieldAlert,
  Calculator, AlertTriangle, MessageCircle,
} from 'lucide-react';

export default function HelpPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-baseline gap-3 mb-8">
        <Link
          to="/"
          className="p-2 rounded-lg transition-colors hover:bg-[var(--bg-surface-hover)] border border-[var(--border-subtle)]"
        >
          <ArrowLeft className="w-4 h-4 text-[var(--text-secondary)]" />
        </Link>
        <h1 className="text-2xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
          <HelpCircle className="w-6 h-6 text-[var(--accent-primary)]" />
          补货系统说明
        </h1>
      </div>

      {/* 核心概念 */}
      <section className="mb-8">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)] mb-4">
          <Package className="w-5 h-5 text-[var(--accent-primary)]" />
          核心概念
        </h2>

        <div className="space-y-4">
          <Card title="提前期（K）" icon={<Clock className="w-4 h-4 text-[var(--accent-primary)]" />}>
            <p>从下单到货物入库需要的天数。</p>
            <p>系统根据每个商品的历史数据自动计算，每个商品的提前期可能不同（0~7天）。</p>
          </Card>

          <Card title="当前库存与在途库存" icon={<Package className="w-4 h-4 text-[var(--accent-primary)]" />}>
            <ul className="list-disc pl-4 space-y-1">
              <li><strong>当前库存</strong>：今天营业结束后的实际剩余库存</li>
              <li><strong>在途库存</strong>：已下单、还在路上、尚未到货的数量</li>
            </ul>
            <p className="text-[var(--text-tertiary)] text-[11px] mt-2">提前期为1天的商品没有在途库存。</p>
          </Card>

          <Card title="覆盖天数" icon={<TrendingUp className="w-4 h-4 text-[var(--accent-primary)]" />}>
            <p>还能卖几天 = (当前库存 + 在途库存) ÷ 日均销量</p>
            <div className="mt-3 rounded-lg overflow-hidden border border-[var(--border-subtle)]">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[var(--bg-surface-hover)]">
                    <th className="text-left py-2 px-3 font-medium text-[var(--text-tertiary)]">状态</th>
                    <th className="text-left py-2 px-3 font-medium text-[var(--text-tertiary)]">覆盖天数</th>
                    <th className="text-left py-2 px-3 font-medium text-[var(--text-tertiary)]">含义</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-[var(--border-subtle)]">
                    <td className="py-2 px-3"><StatusBadge label="紧缺" color="alert" /></td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">不到 2 天</td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">需要立即补货</td>
                  </tr>
                  <tr className="border-t border-[var(--border-subtle)]">
                    <td className="py-2 px-3"><StatusBadge label="偏低" color="warning" /></td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">不到 4 天</td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">建议尽快补货</td>
                  </tr>
                  <tr className="border-t border-[var(--border-subtle)]">
                    <td className="py-2 px-3"><StatusBadge label="正常" color="info" /></td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">4~7 天</td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">库存合理</td>
                  </tr>
                  <tr className="border-t border-[var(--border-subtle)]">
                    <td className="py-2 px-3"><StatusBadge label="充足" color="success" /></td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">超过 7 天</td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">暂时不用补货</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="安全库存" icon={<ShieldAlert className="w-4 h-4 text-[var(--accent-primary)]" />}>
            <p>为了应对销量波动而额外保留的缓冲量。</p>
            <p className="font-mono text-xs bg-[var(--bg-surface-hover)] rounded px-2 py-1 mt-2 inline-block">
              安全库存 = 2.33 × 预测标准差 × √K
            </p>
            <p className="mt-2">预测波动越大，安全库存越多；销量稳定时，安全库存较少。</p>
          </Card>
        </div>
      </section>

      {/* 补货计算 */}
      <section className="mb-8">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)] mb-4">
          <Calculator className="w-5 h-5 text-[var(--accent-primary)]" />
          建议补货量计算
        </h2>

        <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
          <p className="text-sm text-[var(--text-secondary)] mb-4">系统按以下公式计算建议补货量：</p>
          <div className="rounded-lg bg-[var(--bg-surface-hover)] p-4 text-center mb-4">
            <p className="font-mono text-sm text-[var(--text-primary)]">
              建议补货量 = max(0, 未来K天预测 + 安全库存 - 当前库存 - 在途库存)
            </p>
          </div>
          <div className="space-y-2 text-xs text-[var(--text-secondary)]">
            <p>• <strong>未来K天预测</strong>：系统预测该商品在未来提前期K天内的总销量</p>
            <p>• <strong>安全库存</strong>：防缺货的缓冲量</p>
            <p>• <strong>当前库存</strong>：现有实际库存</p>
            <p>• <strong>在途库存</strong>：已下单未到货的数量</p>
            <p>• 结果向上取整，最小为0（不补货）</p>
          </div>
        </div>
      </section>

      {/* 常见问题 */}
      <section className="mb-8">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)] mb-4">
          <MessageCircle className="w-5 h-5 text-[var(--accent-primary)]" />
          常见问题
        </h2>

        <div className="space-y-3">
          <QA
            q="建议补货量是怎么算出来的？"
            a="系统会预测这个商品未来几天的销量，减去现有的库存和在途的货，再加上一个安全缓冲量，得出建议补货量。"
          />
          <QA
            q="为什么有些商品在途库存是0？"
            a="两种情况：一是这个商品的提前期只有1天，昨天下的单今天就到了，没有「在路上」的状态；二是最近没有下过单，自然没有在途。"
          />
          <QA
            q="显示「数据不足」是什么意思？"
            a="这个商品在我们门店的销售记录太少（不到7天），系统没办法做出可靠的预测。建议根据经验判断是否需要补货。"
          />
          <QA
            q="建议补货量显示0，是不是不用补货？"
            a="不一定。0表示按系统预测，现有库存加上在途的货够用。但仍建议关注库存状态，如果临近节假日或有促销活动，可以适当多补。"
          />
          <QA
            q="安全库存为什么有时候多有时候少？"
            a="安全库存和销量波动有关。如果最近销量忽高忽低，系统会加大安全库存来防缺货；如果销量稳定，安全库存就会少一些。"
          />
          <QA
            q="库存状态显示「充足」，是不是可以不管了？"
            a="充足说明近期不会缺货，但仍建议定期查看。库存状态是动态变化的，今天的充足可能过几天就变成正常了。"
          />
          <QA
            q="系统多久更新一次数据？"
            a="每天更新一次，基于前一天结束时的库存和销量数据。"
          />
          <QA
            q="如果我觉得系统的建议不合理怎么办？"
            a="系统建议仅供参考。门店最了解实际情况（如周边活动、天气、节假日等），请结合经验做最终判断。"
          />
        </div>
      </section>

      {/* 注意事项 */}
      <section className="mb-8">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)] mb-4">
          <AlertTriangle className="w-5 h-5 text-[var(--accent-primary)]" />
          注意事项
        </h2>
        <div className="rounded-xl border border-[var(--accent-warning)]/30 bg-[var(--accent-warning)]/5 p-4 space-y-2 text-xs text-[var(--text-secondary)]">
          <p>• 当前补货下单为演示功能，不会向真实供应链系统提交采购订单。</p>
          <p>• 数据截至日期可能晚于实际可用销量的起始日期，页面会有相应提示。</p>
          <p>• 系统建议仅供参考，请结合门店实际情况做最终判断。</p>
        </div>
      </section>
    </div>
  );
}

/* ── 辅助组件 ────────────────────────────────────── */

function Card({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
        {icon}
        {title}
      </h3>
      <div className="text-xs leading-relaxed text-[var(--text-secondary)] space-y-2">
        {children}
      </div>
    </div>
  );
}

function QA({ q, a }: { q: string; a: string }) {
  return (
    <div className="rounded-lg bg-[var(--bg-surface-hover)] p-4">
      <p className="text-xs font-medium text-[var(--text-primary)] mb-1">Q：{q}</p>
      <p className="text-xs text-[var(--text-secondary)]">A：{a}</p>
    </div>
  );
}

function StatusBadge({ label, color }: { label: string; color: 'alert' | 'warning' | 'info' | 'success' }) {
  const colorMap = {
    alert: 'bg-[var(--status-critical-bg)] text-[var(--accent-alert)]',
    warning: 'bg-[var(--status-low-bg)] text-[var(--accent-warning)]',
    info: 'bg-[var(--status-normal-bg)] text-[var(--accent-primary)]',
    success: 'bg-[var(--status-sufficient-bg)] text-[var(--accent-secondary)]',
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs ${colorMap[color]}`}>
      {label}
    </span>
  );
}
