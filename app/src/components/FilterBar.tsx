/**
 * 筛选工具栏 - FilterBar
 * =====================
 * 统一的门店、时间范围、类别、库存状态筛选。
 */

import type { ReactNode } from 'react';
import { RotateCcw } from 'lucide-react';
import StoreSelector from '@/components/StoreSelector';
import { useAnalysis } from '@/state/analysisContext';
import type { Store } from '@/types';

const TIME_OPTIONS = [
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: '90d', label: '90天' },
  { value: '180d', label: '180天' },
  { value: 'all', label: '全部' },
] as const;

const INV_STATUS_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'sufficient', label: '充足' },
  { value: 'normal', label: '正常' },
  { value: 'low', label: '偏低' },
  { value: 'critical', label: '紧缺' },
] as const;

interface FilterBarProps {
  stores: Store[];
  categories: string[];
  showTimeRange?: boolean;
  showInventoryStatus?: boolean;
  /** 额外的筛选项，如商品选择器 */
  extra?: ReactNode;
}

export default function FilterBar({
  stores,
  categories,
  showTimeRange = true,
  showInventoryStatus = false,
  extra,
}: FilterBarProps) {
  const {
    storeId,
    setStoreId,
    range,
    setRange,
    category,
    setCategory,
    inventoryStatus,
    setInventoryStatus,
    resetFilters,
  } = useAnalysis();

  return (
    <div className="rounded-xl border border-[var(--border-color)] bg-[var(--card-surface)] px-5 py-3 mb-6">
      <div className="grid items-center gap-4 grid-cols-[auto_auto_1fr_auto_auto]">
        <StoreSelector stores={stores} selectedStore={storeId} onChange={setStoreId} />

        {/* 类别 */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">类别</span>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-md px-2 py-1 text-xs outline-none cursor-pointer transition-colors focus:ring-2 focus:ring-[var(--border-focus)] bg-[var(--card-surface)] text-[var(--text-primary)] border border-[var(--border-color)] w-[140px]"
          >
            <option value="">全部</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {extra}

        {/* 时间范围 */}
        {showTimeRange && (
          <div className="flex items-center gap-1.5 justify-end">
            <span className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">时间</span>
            <div className="flex rounded-md p-0.5 bg-[var(--bg-primary)] border border-[var(--border-color)]">
              {TIME_OPTIONS.map((o) => {
                const active = range === o.value;
                return (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => setRange(o.value)}
                    className={`px-2.5 py-1 text-[11px] rounded transition-colors ${
                      active
                        ? 'bg-[var(--card-surface)] text-[var(--accent-primary)] font-medium shadow-sm'
                        : 'bg-transparent text-[var(--text-tertiary)]'
                    }`}
                  >
                    {o.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* 库存状态 */}
        {showInventoryStatus && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">库存</span>
            <select
              value={inventoryStatus}
              onChange={(e) => setInventoryStatus(e.target.value)}
              className="rounded-md px-2 py-1 text-xs outline-none cursor-pointer transition-colors focus:ring-2 focus:ring-[var(--border-focus)] bg-[var(--card-surface)] text-[var(--text-primary)] border border-[var(--border-color)] w-[140px]"
            >
              {INV_STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        )}

        <button
          type="button"
          onClick={resetFilters}
          className="flex items-center gap-1 text-[11px] font-medium px-2 py-1 rounded-md transition-colors text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] whitespace-nowrap justify-self-end"
          title="重置筛选"
        >
          <RotateCcw className="w-3 h-3" />
          重置
        </button>
      </div>
    </div>
  );
}
