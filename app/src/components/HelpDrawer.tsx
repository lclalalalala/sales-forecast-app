/**
 * HelpDrawer 帮助抽屉
 * ===================
 * 全局帮助入口，展示指标说明与补货规则概要，提供完整文档链接。
 */

import { Link } from 'react-router-dom';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  HelpCircle, Package, Clock, TrendingUp, ShieldAlert,
  Calculator, ExternalLink,
} from 'lucide-react';

interface HelpDrawerProps {
  children?: React.ReactNode;
}

export default function HelpDrawer({ children }: HelpDrawerProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        {children || (
          <Button variant="ghost" size="icon" aria-label="打开帮助说明">
            <HelpCircle className="w-5 h-5" />
          </Button>
        )}
      </SheetTrigger>
      <SheetContent className="w-[min(100%,624px)] sm:max-w-xl bg-[var(--bg-surface)] border-[var(--border-subtle)]">
        <SheetHeader className="pb-4 border-b border-[var(--border-subtle)]">
          <div className="flex items-start justify-between">
            <SheetTitle className="flex items-center gap-2 text-lg font-semibold text-[var(--text-primary)]">
              <HelpCircle className="w-5 h-5 text-[var(--accent-primary)]" />
              补货系统说明
            </SheetTitle>
            <div className="flex flex-col items-end gap-1 mr-8">
              <Link
                to="/help"
                className="flex items-center gap-1.5 text-xs text-[var(--accent-primary)] hover:underline"
              >
                <ExternalLink className="w-3 h-3" />
                查看完整补货系统说明文档
              </Link>
              <Link
                to="/tech-doc"
                className="flex items-center gap-1.5 text-xs text-[var(--accent-secondary)] hover:underline transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                系统架构文档
              </Link>
            </div>
          </div>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-100px)] mt-4">
          <div className="space-y-5 px-6 pr-8">
            {/* 核心概念 */}
            <section>
              <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
                <Package className="w-4 h-4 text-[var(--accent-primary)]" />
                核心概念
              </h3>
              <div className="space-y-2">
                <QuickCard
                  icon={<Clock className="w-3.5 h-3.5 text-[var(--accent-primary)]" />}
                  title="提前期 K"
                  desc="下单到入库的天数，系统按商品自动计算（0~7天）。"
                />
                <QuickCard
                  icon={<Package className="w-3.5 h-3.5 text-[var(--accent-primary)]" />}
                  title="当前库存 / 在途库存"
                  desc="当前库存是实际剩余量；在途库存是已下单未到货量。"
                />
                <QuickCard
                  icon={<TrendingUp className="w-3.5 h-3.5 text-[var(--accent-primary)]" />}
                  title="覆盖天数"
                  desc="(当前库存 + 在途库存) ÷ 日均销量 = 还能卖几天。"
                />
                <QuickCard
                  icon={<ShieldAlert className="w-3.5 h-3.5 text-[var(--accent-primary)]" />}
                  title="安全库存"
                  desc="2.33 × 预测标准差 × √K，用于吸收销量波动。"
                />
              </div>
            </section>

            {/* 库存状态 */}
            <section>
              <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
                <TrendingUp className="w-4 h-4 text-[var(--accent-primary)]" />
                库存状态
              </h3>
              <div className="rounded-lg border border-[var(--border-subtle)] overflow-hidden">
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
                      <td className="py-2 px-3"><span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-critical-bg)] text-[var(--accent-alert)]">紧缺</span></td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">&lt; 2天</td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">立即补货</td>
                    </tr>
                    <tr className="border-t border-[var(--border-subtle)]">
                      <td className="py-2 px-3"><span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-low-bg)] text-[var(--accent-warning)]">偏低</span></td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">&lt; 4天</td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">尽快补货</td>
                    </tr>
                    <tr className="border-t border-[var(--border-subtle)]">
                      <td className="py-2 px-3"><span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-normal-bg)] text-[var(--accent-primary)]">正常</span></td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">4~7天</td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">库存合理</td>
                    </tr>
                    <tr className="border-t border-[var(--border-subtle)]">
                      <td className="py-2 px-3"><span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-sufficient-bg)] text-[var(--accent-secondary)]">充足</span></td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">&gt; 7天</td>
                      <td className="py-2 px-3 text-[var(--text-secondary)]">暂不需补货</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* 补货公式 */}
            <section>
              <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)] mb-3">
                <Calculator className="w-4 h-4 text-[var(--accent-primary)]" />
                补货计算
              </h3>
              <div className="rounded-lg bg-[var(--bg-surface-hover)] p-3 text-center">
                <p className="font-mono text-xs text-[var(--text-primary)]">
                  补货量 = max(0, K天预测 + 安全库存 - 当前库存 - 在途库存)
                </p>
              </div>
            </section>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

function QuickCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="rounded-lg bg-[var(--bg-surface-hover)] p-3 flex items-start gap-2.5">
      <div className="mt-0.5">{icon}</div>
      <div>
        <p className="text-xs font-medium text-[var(--text-primary)]">{title}</p>
        <p className="text-[11px] text-[var(--text-secondary)] mt-0.5">{desc}</p>
      </div>
    </div>
  );
}
