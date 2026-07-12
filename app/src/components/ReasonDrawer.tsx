/**
 * ReasonDrawer 补货原因抽屉
 * ========================
 * 展示单个商品的补货建议依据，可在补货建议页与商品详情页复用。
 */

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Calculator, Info } from 'lucide-react';
import InventoryStatusBadge from '@/components/InventoryStatusBadge';
import type { InventoryStatusKey } from '@/types';
import { cn } from '@/lib/utils';

export interface ReasonDrawerProps {
  productId: string;
  category?: string;
  currentInventory: number;
  inTransitInventory: number;
  leadTimeK: number;
  leadTimeKSource?: 'estimated' | 'default';
  forecastKTotal: number;
  safetyStock: number;
  suggestedReplenishment: number;
  inventoryStatus: InventoryStatusKey;
  status?: 'ready' | 'insufficient_data' | 'error' | 'forecast_unavailable';
  message?: string | null;
  children?: React.ReactNode;
}

const fmt = (n?: number | null) => (n != null && Number.isFinite(n) ? n.toLocaleString('zh-CN') : '-');
const f1 = (n?: number | null) => (n != null && Number.isFinite(n) && !Number.isNaN(n) ? n.toFixed(1) : '-');

export default function ReasonDrawer({
  productId,
  category,
  currentInventory,
  inTransitInventory,
  leadTimeK,
  leadTimeKSource,
  forecastKTotal,
  safetyStock,
  suggestedReplenishment,
  inventoryStatus,
  status,
  message,
  children,
}: ReasonDrawerProps) {
  const formula = `建议补货量 = ceil(max(0, 未来 K 天预测销量 + 安全库存 - 当前库存 - 在途库存))`;
  const computed = Math.ceil(
    Math.max(0, forecastKTotal + safetyStock - currentInventory - inTransitInventory),
  );

  return (
    <Sheet>
      <SheetTrigger asChild>
        {children || (
          <Button variant="ghost" size="sm" className="text-[var(--accent-primary)]">
            <Calculator className="w-3.5 h-3.5 mr-1" />
            查看原因
          </Button>
        )}
      </SheetTrigger>
      <SheetContent className="w-[min(100%,480px)] sm:max-w-md bg-[var(--bg-surface)] border-[var(--border-subtle)] px-6">
        <SheetHeader className="pb-4 border-b border-[var(--border-subtle)]">
          <SheetTitle className="text-lg font-semibold text-[var(--text-primary)]">
            {productId}
            {category && (
              <span className="ml-2 text-xs font-normal px-2 py-0.5 rounded-full bg-[var(--bg-surface-hover)] text-[var(--accent-primary)]">
                {category}
              </span>
            )}
            <div className="mt-1 text-sm font-normal text-[var(--text-secondary)]">补货建议依据</div>
          </SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-100px)] mt-4 pr-1">
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-3">
              <Metric label="当前库存" value={fmt(currentInventory)} />
              <Metric label="在途库存" value={fmt(inTransitInventory)} />
              <Metric label="补货提前期 K" value={`${leadTimeK} 天`} sub={leadTimeKSource === 'estimated' ? 'MSE 估计' : '默认值'} />
              <Metric label="提前期内预计销量" value={f1(forecastKTotal)} />
              <Metric label="安全库存" value={fmt(safetyStock)} />
              <Metric label="建议补货量" value={fmt(suggestedReplenishment)} highlight />
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] p-3">
              <h4 className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-primary)] mb-2">
                <Calculator className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
                计算公式
              </h4>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)] mb-2">
                {formula}
              </p>
              <div className="rounded bg-[var(--bg-surface-hover)] px-2 py-1.5 font-mono text-[11px] text-[var(--text-primary)]">
                {fmt(suggestedReplenishment)} = ceil(max(0, {f1(forecastKTotal)} + {fmt(safetyStock)} - {fmt(currentInventory)} - {fmt(inTransitInventory)}))
              </div>
              {computed !== suggestedReplenishment && (
                <p className="mt-2 text-[11px] text-[var(--accent-warning)]">
                  注：显示值已按最小补货单位取整。
                </p>
              )}
            </div>

            <div className="rounded-lg border border-[var(--border-subtle)] p-3">
              <h4 className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-primary)] mb-2">
                库存状态
              </h4>
              <InventoryStatusBadge status={inventoryStatus} />
            </div>

            {status && status !== 'ready' && (
              <div className="rounded-lg border border-[var(--accent-warning)]/30 bg-[var(--accent-warning)]/10 p-3">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold text-[var(--accent-warning)] mb-1">
                  <Info className="w-3.5 h-3.5" />
                  计算状态
                </h4>
                <p className="text-xs text-[var(--text-secondary)]">
                  {status === 'insufficient_data' && '历史数据不足，建议扩大时间范围或检查数据完整性。'}
                  {status === 'forecast_unavailable' && '预测服务暂不可用，建议稍后刷新。'}
                  {status === 'error' && '计算过程发生错误。'}
                </p>
                {message && <p className="mt-1 text-[11px] text-[var(--text-tertiary)]">{message}</p>}
              </div>
            )}

            <div className="rounded-lg border border-[var(--border-subtle)] p-3">
              <h4 className="text-xs font-semibold text-[var(--text-primary)] mb-2">预测说明</h4>
              <p className="text-xs leading-relaxed text-[var(--text-secondary)]">
                未来 7 天预测销量基于历史实际销量模型计算。安全库存使用 2.33 倍滚动预测误差标准差与 √K 估计，用于吸收需求波动。
              </p>
            </div>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

function Metric({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-lg bg-[var(--bg-surface-hover)] p-3">
      <p className="text-[11px] text-[var(--text-tertiary)]">{label}</p>
      <p className={cn('text-sm font-semibold', highlight ? 'text-[var(--accent-primary)]' : 'text-[var(--text-primary)]')}>
        {value}
      </p>
      {sub && <p className="text-[10px] text-[var(--text-tertiary)]">{sub}</p>}
    </div>
  );
}
