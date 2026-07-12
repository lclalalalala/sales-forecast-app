/**
 * 补货建议页 - ReplenishmentPage
 * =============================
 * 展示基于提前期 K、在途库存与安全库存的补货建议，支持排序、重点商品筛选、补货原因抽屉。
 */

import { useEffect, useMemo, useState, useRef, memo } from 'react';
import { Link } from 'react-router-dom';
import {
  Package, AlertTriangle, TrendingUp, ShieldAlert,
  ClipboardCheck,
} from 'lucide-react';
import { api } from '@/services/api';
import { isAbortError, getErrorMessage } from '@/lib/errors';
import { REPLENISHMENT_DISPLAY_LIMIT } from '@/lib/constants';
import FilterBar from '@/components/FilterBar';
import InventoryStatusBadge from '@/components/InventoryStatusBadge';
import DataState from '@/components/DataState';
import KpiCard from '@/components/KpiCard';
import Sparkline from '@/components/charts/Sparkline';
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable';
import ReasonDrawer from '@/components/ReasonDrawer';
import OrderForm from '@/components/OrderForm';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAnalysis } from '@/state/analysisContext';
import type { Store, ReplenishmentSuggestion, AnalysisContext } from '@/types';
import { formatInt as fmt, formatDecimal } from '@/lib/format';

const f1 = (n?: number | null) => formatDecimal(n, 1);

const QUICK_FILTERS = [
  { key: 'all', label: '全部商品' },
  { key: 'pending', label: '待补货' },
] as const;

type QuickFilter = (typeof QUICK_FILTERS)[number]['key'];

interface TitleBlockProps {
  storeName: string;
  context: AnalysisContext;
}

const TitleBlock = memo(function TitleBlock({ storeName, context }: TitleBlockProps) {
  return (
    <div className="mb-6">
      <div className="flex items-baseline gap-3">
        <h2 className="text-2xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
          <Package className="w-6 h-6 text-[var(--accent-primary)]" />
          补货建议
        </h2>
        <span className="text-sm text-[var(--text-secondary)]">
          {storeName && storeName !== context.store_id ? `${context.store_id} · ${storeName}` : context.store_id}
        </span>
        <span className="text-xs text-[var(--text-tertiary)]">
          数据截至：{context.as_of_date}
        </span>
      </div>
    </div>
  );
});

interface SummaryCardsProps {
  suggestions: ReplenishmentSuggestion[];
}

const SummaryCards = memo(function SummaryCards({ suggestions }: SummaryCardsProps) {
  const totalReplenish = suggestions.reduce(
    (sum, s) => sum + (s.suggested_replenishment || 0),
    0,
  );
  const riskCount = suggestions.filter(
    (s) => s.inventory_status === 'critical' || s.inventory_status === 'low',
  ).length;
  const focusCount = suggestions.filter(
    (s) => s.suggested_replenishment > 0 || s.inventory_status === 'critical' || s.inventory_status === 'low',
  ).length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KpiCard
        icon={Package}
        label="建议补货商品数"
        value={fmt(suggestions.length)}
      />
      <KpiCard
        icon={TrendingUp}
        label="建议补货总量"
        value={fmt(totalReplenish)}
      />
      <KpiCard
        icon={ShieldAlert}
        label="高缺货风险商品"
        value={fmt(riskCount)}
      />
      <KpiCard
        icon={AlertTriangle}
        label="重点商品数"
        value={fmt(focusCount)}
        sub="建议补货量 > 0 或库存风险"
      />
    </div>
  );
});

interface SuggestionTableProps {
  items: ReplenishmentSuggestion[];
  onProductClick: (productId: string) => void;
  onOrderClick: (productId: string, suggestedQuantity: number) => void;
}

const SuggestionTable = memo(function SuggestionTable({
  items,
  onProductClick,
  onOrderClick,
}: SuggestionTableProps) {

  const columns: DataTableColumn<ReplenishmentSuggestion>[] = [
    {
      key: 'product_id',
      header: '商品ID',
      sortable: true,
      render: (s) => (
        <Link
          to={`/products/${s.product_id}`}
          data-product-id={s.product_id}
          onClick={() => onProductClick(s.product_id)}
          className="font-medium text-[var(--accent-primary)] hover:underline"
        >
          {s.product_id}
        </Link>
      ),
    },
    {
      key: 'category',
      header: '商品类别',
      sortable: true,
      render: (s) => (
        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs bg-[var(--bg-surface-hover)] text-[var(--accent-primary)]">
          {s.category}
        </span>
      ),
    },
    {
      key: 'current_inventory',
      header: '当前库存',
      align: 'right',
      sortable: true,
      render: (s) => <span className="text-[var(--text-primary)]">{fmt(s.current_inventory)}</span>,
    },
    {
      key: 'in_transit_inventory',
      header: '在途库存',
      align: 'right',
      sortable: true,
      render: (s) => <span className="text-[var(--text-secondary)]">{fmt(s.in_transit_inventory)}</span>,
    },
    {
      key: 'lead_time_k',
      header: 'K',
      align: 'right',
      sortable: true,
      width: '60px',
      render: (s) => (
        <span className="font-medium text-[var(--text-primary)]">
          {s.lead_time_k}
          <span className="ml-1 text-[10px] text-[var(--text-tertiary)]">
            {s.lead_time_k_source === 'estimated' ? '估' : '默'}
          </span>
        </span>
      ),
    },
    {
      key: 'forecast_trend',
      header: '预测趋势',
      render: (s) => (
        <Sparkline
          data={(s.forecast_7d ?? []).map((p) => p.units_sold)}
          labels={(s.forecast_7d ?? []).map((p) => p.date.slice(5))}
          height={36}
        />
      ),
    },
    {
      key: 'forecast_k_total',
      header: 'K天预测合计',
      align: 'right',
      sortable: true,
      render: (s) => <span className="text-[var(--text-secondary)]">{f1(s.forecast_k_total)}</span>,
    },
    {
      key: 'safety_stock',
      header: '安全库存',
      align: 'right',
      sortable: true,
      render: (s) => <span className="text-[var(--text-secondary)]">{fmt(s.safety_stock)}</span>,
    },
    {
      key: 'suggested_replenishment',
      header: '建议补货量',
      align: 'right',
      sortable: true,
      render: (s) => <span className="font-semibold text-[var(--accent-primary)]">{fmt(s.suggested_replenishment)}</span>,
    },
    {
      key: 'inventory_status',
      header: '库存状态',
      align: 'center',
      sortable: true,
      render: (s) => <InventoryStatusBadge status={s.inventory_status} />,
    },
    {
      key: 'status',
      header: '计算状态',
      align: 'center',
      sortable: true,
      render: (s) => {
        if (s.status === 'ready') return <span className="text-xs text-[var(--accent-secondary)]">就绪</span>;
        return (
          <span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-low-bg)] text-[var(--accent-warning)]">
            {s.status === 'insufficient_data' && '数据不足'}
            {s.status === 'forecast_unavailable' && '预测不可用'}
            {s.status === 'error' && '错误'}
          </span>
        );
      },
    },
    {
      key: 'action',
      header: '操作',
      align: 'center',
      fixed: true,
      render: (s) => (
        <div className="flex items-center justify-center gap-1">
          <ReasonDrawer
            productId={s.product_id}
            category={s.category}
            currentInventory={s.current_inventory}
            inTransitInventory={s.in_transit_inventory}
            leadTimeK={s.lead_time_k}
            leadTimeKSource={s.lead_time_k_source}
            forecastKTotal={s.forecast_k_total}
            safetyStock={s.safety_stock}
            suggestedReplenishment={s.suggested_replenishment}
            inventoryStatus={s.inventory_status}
            status={s.status}
            message={s.message}
          >
            <Button variant="ghost" size="sm" className="h-8 px-2 text-sky-400 hover:text-sky-500">
              补货分析
            </Button>
          </ReasonDrawer>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 px-2 text-sky-400 hover:text-sky-500"
            onClick={() => onOrderClick(s.product_id, s.suggested_replenishment)}
            aria-label="下单补货"
            title="下单补货"
          >
            下单补货
          </Button>
          <Button asChild size="sm" variant="ghost" className="h-8 px-2 text-sky-400 hover:text-sky-500">
            <Link to={`/products/${s.product_id}`} data-product-id={s.product_id}>
              商品详情
            </Link>
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
      <DataTable
        columns={columns}
        data={items}
        rowKey={(item) => item.product_id}
        skeletonRows={8}
      />
    </div>
  );
});

export default function ReplenishmentPage() {
  const { storeId, category, setProductId } = useAnalysis();
  const [stores, setStores] = useState<Store[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<ReplenishmentSuggestion[]>([]);
  const [context, setContext] = useState<AnalysisContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [quickFilter, setQuickFilter] = useState<QuickFilter>('all');
  const [refreshKey, setRefreshKey] = useState(0);
  const [orderItem, setOrderItem] = useState<{ productId: string; suggestedQuantity: number } | null>(null);
  const staleRef = useRef(false);

  const storeName = useMemo(
    () => stores.find((s) => s.id === storeId)?.name || '',
    [stores, storeId],
  );

  useEffect(() => {
    staleRef.current = false;
    const controller = new AbortController();

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [s, c, res] = await Promise.all([
          api.getStores(controller.signal),
          api.getCategories(controller.signal),
          api.getReplenishment(storeId, category || undefined, controller.signal),
        ]);
        if (staleRef.current) return;
        setStores(s);
        setCategories(c);
        setContext(res.context);
        setSuggestions(res.data.suggestions);
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
  }, [storeId, category, refreshKey]);

  const displayed = useMemo(() => {
    const filtered = suggestions.filter((s) => {
      if (quickFilter === 'pending') {
        return s.suggested_replenishment > 0 || s.inventory_status === 'critical' || s.inventory_status === 'low';
      }
      return true;
    });
    return filtered.slice(0, REPLENISHMENT_DISPLAY_LIMIT);
  }, [suggestions, quickFilter]);

  const handleProductClick = (productId: string) => {
    setProductId(productId);
  };

  const handleOrderClick = (productId: string, suggestedQuantity: number) => {
    setOrderItem({ productId, suggestedQuantity });
  };

  const handleOrderClose = () => {
    setOrderItem(null);
  };

  return (
    <div>
      {context && <TitleBlock storeName={storeName} context={context} />}

      <FilterBar
        stores={stores}
        categories={categories}
        showTimeRange={false}
        extra={
          <div className="flex items-center gap-1.5 justify-self-end">
            <span className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">状态</span>
            <div className="flex rounded-md p-0.5 bg-[var(--bg-primary)] border border-[var(--border-color)]">
              {QUICK_FILTERS.map((o) => {
                const active = quickFilter === o.key;
                return (
                  <button
                    key={o.key}
                    type="button"
                    onClick={() => setQuickFilter(o.key)}
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
            <span className="text-[11px] text-[var(--text-tertiary)]">
              {displayed.length}/{suggestions.length}
            </span>
          </div>
        }
      />

      <DataState
        status={loading ? 'loading' : error ? 'error' : 'ready'}
        error={error}
        onRetry={() => setRefreshKey((k) => k + 1)}
      >
        <SummaryCards suggestions={suggestions} />

        <SuggestionTable
          items={displayed}
          onProductClick={handleProductClick}
          onOrderClick={handleOrderClick}
        />

        <div className="mt-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-primary)] p-5">
          <h4 className="text-sm font-semibold mb-2 text-[var(--text-primary)]">计算说明</h4>
          <ul className="text-xs space-y-1 list-disc pl-4 text-[var(--text-secondary)]">
            <li>提前期 K：通过库存平衡方程 MSE 估计，默认 fallback 为 2 天</li>
            <li>在途库存：前 K-1 天 Units Ordered 之和</li>
            <li>安全库存：2.33 × 滚动预测误差标准差 × √K</li>
            <li>建议补货量 = ceil(max(0, 未来 K 天预测 + 安全库存 - 当前库存 - 在途库存))</li>
          </ul>
        </div>
      </DataState>

      <Dialog open={!!orderItem} onOpenChange={(open) => { if (!open) setOrderItem(null); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-[var(--text-primary)]">
              <ClipboardCheck className="w-5 h-5 text-[var(--accent-primary)]" />
              补货下单
            </DialogTitle>
            <DialogDescription>
              请核对补货依据并填写数量与到货日期
            </DialogDescription>
          </DialogHeader>
          {orderItem && (
            <OrderForm
              storeId={storeId}
              productId={orderItem.productId}
              suggestedQuantity={orderItem.suggestedQuantity}
              onClose={handleOrderClose}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
