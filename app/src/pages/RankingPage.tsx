/**
 * 商品排名页 - RankingPage
 * =======================
 * 独立完整 Top/Bottom 排名，支持库存状态过滤与跳转商品详情。
 */

import { useEffect, useState, useRef, memo } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUp, ArrowDown, Medal, ListOrdered } from 'lucide-react';
import { api } from '@/services/api';
import { isAbortError, getErrorMessage } from '@/lib/errors';
import FilterBar from '@/components/FilterBar';
import InventoryStatusBadge from '@/components/InventoryStatusBadge';
import DataState from '@/components/DataState';
import { useAnalysis } from '@/state/analysisContext';
import type { Store, RankingItem } from '@/types';

const fmt = (n?: number | null) => (n != null ? n.toLocaleString('zh-CN') : '-');
const f1 = (n?: number | null) =>
  n != null && Number.isFinite(n) && !Number.isNaN(n) ? n.toFixed(1) : '-';
const f2 = (n?: number | null) =>
  n != null && Number.isFinite(n) && !Number.isNaN(n) ? n.toFixed(2) : '-';

interface RankingTableProps {
  title: string;
  items: RankingItem[];
  isTop: boolean;
  category: string;
}

const headers = ['排名', '商品', '类别', '总销量', '日均', '当前库存', '在途库存', '覆盖天数', '库存状态'];

const RankingTable = memo(function RankingTable({ title, items, isTop, category }: RankingTableProps) {
  return (
    <div className="rounded-xl border border-[var(--border-color)] bg-[var(--card-surface)] p-5">
      <div className="flex items-center gap-2 mb-4">
        {isTop ? (
          <ArrowUp className="w-5 h-5 text-[var(--accent-secondary)]" />
        ) : (
          <ArrowDown className="w-5 h-5 text-[var(--accent-alert)]" />
        )}
        <h3 className="text-base font-semibold text-[var(--text-primary)]">
          {title}
        </h3>
        {category && (
          <span
            className="text-xs px-2 py-0.5 rounded-full bg-[var(--status-normal-bg)] text-[var(--accent-primary)]"
          >
            {category}
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--border-color)]">
              {headers.map((h) => (
                <th
                  key={h}
                  className="text-left py-3 px-2 font-medium whitespace-nowrap text-[var(--text-tertiary)] uppercase tracking-wider"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => {
              const isChampion = isTop && idx === 0;
              return (
                <tr
                  key={item.product_id}
                  className="group hover:bg-[var(--table-row-hover)] border-b border-[var(--border-subtle)]"
                >
                  <td className="py-3 px-2">
                    {isChampion ? (
                      <Medal className="w-4 h-4 text-[var(--accent-warning)]" />
                    ) : (
                      <span className="text-[var(--text-secondary)]">{item.rank}</span>
                    )}
                  </td>
                  <td className="py-3 px-2">
                    <Link
                      to={`/products/${item.product_id}`}
                      className="font-medium hover:underline text-[var(--accent-primary)]"
                    >
                      {item.product_id}
                    </Link>
                  </td>
                  <td className="py-3 px-2">
                    <span
                      className="px-2 py-0.5 rounded-full text-xs bg-[var(--status-normal-bg)] text-[var(--accent-primary)]"
                    >
                      {item.category}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right font-medium text-[var(--text-primary)]">
                    {fmt(item.total_sold)}
                  </td>
                  <td className="py-3 px-2 text-right text-[var(--text-secondary)]">
                    {f1(item.avg_daily)}
                  </td>
                  <td className="py-3 px-2 text-right text-[var(--text-secondary)]">
                    {fmt(item.current_inventory)}
                  </td>
                  <td className="py-3 px-2 text-right text-[var(--text-secondary)]">
                    {fmt(item.in_transit_inventory)}
                  </td>
                  <td className="py-3 px-2 text-right text-[var(--text-secondary)]">
                    {item.coverage_days != null ? f2(item.coverage_days) : '-'}
                  </td>
                  <td className="py-3 px-2">
                    <InventoryStatusBadge status={item.inventory_status} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
});

const N_OPTIONS = [3, 5, 10, 20];

export default function RankingPage() {
  const { storeId, range, category, inventoryStatus, setProductId } = useAnalysis();
  const [stores, setStores] = useState<Store[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [top, setTop] = useState<RankingItem[]>([]);
  const [bottom, setBottom] = useState<RankingItem[]>([]);
  const [totalCandidates, setTotalCandidates] = useState(0);
  const [topN, setTopN] = useState(5);
  const [bottomN, setBottomN] = useState(5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const staleRef = useRef(false);

  useEffect(() => {
    staleRef.current = false;
    const controller = new AbortController();

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [s, c, ranking] = await Promise.all([
          api.getStores(controller.signal),
          api.getCategories(controller.signal),
          api.getRankings(
            storeId,
            range,
            category || undefined,
            inventoryStatus || undefined,
            topN,
            bottomN,
            controller.signal
          ),
        ]);
        if (staleRef.current) return;
        setStores(s);
        setCategories(c);
        setTop(ranking.data.top);
        setBottom(ranking.data.bottom);
        setTotalCandidates(ranking.data.total_candidates);
      } catch (e: unknown) {
        if (staleRef.current) return;
        if (!isAbortError(e)) {
          setError(getErrorMessage(e));
        }
      } finally {
        if (!staleRef.current) setLoading(false);
      }
    };

    load();
    return () => {
      staleRef.current = true;
      controller.abort();
    };
  }, [storeId, range, category, inventoryStatus, topN, bottomN, refreshKey]);

  const handleRowClick = (e: React.MouseEvent) => {
    const target = e.target;
    if (!(target instanceof HTMLElement)) return;
    const link = target.closest('a');
    if (link) {
      const pid = link.textContent?.trim();
      if (pid) setProductId(pid);
    }
  };

  const renderNSelector = (
    label: string,
    value: number,
    onChange: (n: number) => void
  ) => (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--text-tertiary)]">{label}</span>
      <div className="flex rounded-lg p-0.5 bg-[var(--bg-primary)] border border-[var(--border-color)]">
        {N_OPTIONS.map((n) => {
          const active = value === n;
          return (
            <button
              key={n}
              type="button"
              onClick={() => onChange(n)}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                active
                  ? 'bg-[var(--card-surface)] text-[var(--accent-primary)] font-medium shadow-[var(--shadow-dropdown)]'
                  : 'bg-transparent text-[var(--text-tertiary)]'
              }`}
            >
              {n}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
          <ListOrdered className="w-6 h-6 text-[var(--accent-primary)]" />
          商品排名
        </h2>
        <p className="text-sm mt-1 text-[var(--text-tertiary)]">
          按销量 Top/Bottom 排序，结合库存状态识别畅销缺货或滞销积压商品
        </p>
      </div>

      <FilterBar stores={stores} categories={categories} showInventoryStatus />

      <div
        className="rounded-xl border border-[var(--border-color)] bg-[var(--card-surface)] px-4 py-3 flex flex-wrap items-center justify-between gap-3 mb-4"
      >
        <div className="text-xs text-[var(--text-secondary)]">
          候选商品数：<span className="font-medium text-[var(--text-primary)]">{totalCandidates}</span>
        </div>
        <div className="flex items-center gap-4">
          {renderNSelector('Top', topN, setTopN)}
          {renderNSelector('Bottom', bottomN, setBottomN)}
        </div>
      </div>

      <DataState
        status={loading ? 'loading' : error ? 'error' : 'ready'}
        error={error}
        onRetry={() => setRefreshKey((k) => k + 1)}
      >
        <div className="grid grid-cols-1 gap-6" onClick={handleRowClick}>
          <RankingTable title={`Top ${topN} 畅销品`} items={top} isTop category={category} />
          <RankingTable title={`Bottom ${bottomN} 滞销品`} items={bottom} isTop={false} category={category} />
        </div>
      </DataState>
    </div>
  );
}
