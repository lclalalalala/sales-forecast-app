/**
 * 数据概览页 - DashboardPage
 * =========================
 * 使用 /api/overview 展示 KPI、趋势图与可排序 Top/Bottom 排名。
 */

import { useEffect, useState, useRef, useMemo, memo } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';
import {
  Package, Boxes, TrendingDown, AlertTriangle,
  ArrowUp, ArrowDown, Medal, ChevronRight, BarChart3,
} from 'lucide-react';
import { api } from '@/services/api';
import { isAbortError, getErrorMessage } from '@/lib/errors';
import { ALL_TIME_RANGE_DAYS } from '@/lib/constants';
import FilterBar from '@/components/FilterBar';
import InventoryStatusBadge from '@/components/InventoryStatusBadge';
import DataState from '@/components/DataState';
import KpiCard from '@/components/KpiCard';
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable';
import { useAnalysis } from '@/state/analysisContext';
import type { Store, RankingItem, AnalysisContext } from '@/types';
import { formatInt as fmt, formatDecimal, formatLocalDate } from '@/lib/format';

const f1 = (n?: number | null) => formatDecimal(n, 1);

function parseDate(value: string): Date {
  return new Date(`${value}T00:00:00`);
}

function computeSelectedStart(range: string, asOfDate: string): string | null {
  if (range === 'all') return null;
  const days = parseInt(range, 10);
  if (Number.isNaN(days)) return null;
  const d = parseDate(asOfDate);
  d.setDate(d.getDate() - days + 1);
  return formatLocalDate(d);
}

interface TitleBlockProps {
  storeName: string;
  context: AnalysisContext;
  range: string;
}

const TitleBlock = memo(function TitleBlock({ storeName, context, range }: TitleBlockProps) {
  const selectedStart = computeSelectedStart(range, context.as_of_date);
  const showDataNote = selectedStart && parseDate(context.actual_data_start) > parseDate(selectedStart);

  return (
    <div className="mb-6">
      <div className="flex items-baseline gap-3">
        <h2 className="text-2xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
          <BarChart3 className="w-6 h-6 text-[var(--accent-primary)]" />
          数据概览
        </h2>
        <span className="text-sm text-[var(--text-secondary)]">
          {storeName && storeName !== context.store_id ? `${context.store_id} · ${storeName}` : context.store_id}
        </span>
        <span className="text-xs text-[var(--text-tertiary)]">
          数据截至：{context.as_of_date}
        </span>
      </div>
      {showDataNote && (
        <div className="rounded-lg border border-[var(--accent-warning)]/30 bg-[var(--accent-warning)]/10 px-3 py-2 text-xs text-[var(--text-secondary)] mt-2">
          当前选择近 {range}，实际可用数据为 {context.actual_data_start} ～ {context.actual_data_end}
          ，共 {fmt(Math.round((parseDate(context.actual_data_end).getTime() - parseDate(context.actual_data_start).getTime()) / 86400000) + 1)} 天。
        </div>
      )}
    </div>
  );
});

interface KpiCardsProps {
  kpis: {
    avg_daily_units_sold: number;
    current_inventory_total: number;
    low_stock_count: number;
    critical_stock_count: number;
  };
  days: number;
}

const KpiCards = memo(function KpiCards({ kpis, days }: KpiCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KpiCard
        icon={Package}
        label="平均日销售量"
        value={f1(kpis.avg_daily_units_sold)}
        sub={days >= ALL_TIME_RANGE_DAYS ? '全部时间范围' : `近${days}天平均`}
      />
      <KpiCard
        icon={Boxes}
        label="当前库存"
        value={fmt(kpis.current_inventory_total)}
        sub="含在途库存"
      />
      <KpiCard
        icon={TrendingDown}
        label="低库存商品数"
        value={fmt(kpis.low_stock_count)}
        sub="覆盖天数 < 4"
      />
      <KpiCard
        icon={AlertTriangle}
        label="紧缺商品数"
        value={fmt(kpis.critical_stock_count)}
        sub="覆盖天数 < 2"
      />
    </div>
  );
});

interface TrendChartProps {
  dailySales: { date: string; units_sold: number }[];
  category: string;
  days: number;
}

const TrendChart = memo(function TrendChart({ dailySales, category, days }: TrendChartProps) {
  if (!dailySales?.length) return null;
  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 mb-6">
      <h3 className="text-base font-semibold mb-4 text-[var(--text-primary)]">
        {category || '全部商品'} 销售趋势
        {days < ALL_TIME_RANGE_DAYS && (
          <span className="text-sm font-normal ml-2 text-[var(--text-tertiary)]">
            (近{days}天)
          </span>
        )}
      </h3>
      <div className="h-80" role="img" aria-label="销售趋势折线图">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dailySales} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              itemStyle={{ color: 'var(--text-primary)' }}
              labelStyle={{ color: 'var(--text-primary)' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} />
            <Line
              type="monotone"
              dataKey="units_sold"
              name="实际销量"
              stroke="var(--chart-sales)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: 'var(--chart-sales)' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

interface RankTablesProps {
  top: RankingItem[];
  bottom: RankingItem[];
  category: string;
  onProductClick: (productId: string) => void;
}

function createRankColumns(onProductClick: (productId: string) => void): DataTableColumn<RankingItem>[] {
  return [
    {
      key: 'rank',
      header: '排名',
      width: '60px',
      render: (item) => (
        <div className="flex items-center gap-1">
          {item.rank === 1 ? (
            <Medal className="w-4 h-4 text-[var(--accent-warning)]" />
          ) : (
            <span className="text-[var(--text-secondary)]">{item.rank}</span>
          )}
        </div>
      ),
    },
    {
      key: 'product_id',
      header: '商品编号',
      sortable: true,
      render: (item) => (
        <Link
          to={`/products/${item.product_id}`}
          onClick={() => onProductClick(item.product_id)}
          className="font-medium text-[var(--accent-primary)] hover:underline"
        >
          {item.product_id}
        </Link>
      ),
    },
    {
      key: 'category',
      header: '商品类别',
      sortable: true,
      render: (item) => (
        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs bg-[var(--bg-surface-hover)] text-[var(--accent-primary)]">
          {item.category}
        </span>
      ),
    },
    {
      key: 'total_sold',
      header: '总销量',
      align: 'right',
      sortable: true,
      render: (item) => <span className="font-medium text-[var(--text-primary)]">{fmt(item.total_sold)}</span>,
    },
    {
      key: 'avg_daily',
      header: '日均销量',
      align: 'right',
      sortable: true,
      render: (item) => <span className="text-[var(--text-secondary)]">{f1(item.avg_daily)}</span>,
    },
    {
      key: 'current_inventory',
      header: '当前库存',
      align: 'right',
      sortable: true,
      render: (item) => <span className="text-[var(--text-secondary)]">{fmt(item.current_inventory)}</span>,
    },
    {
      key: 'inventory_status',
      header: '库存状态',
      align: 'center',
      sortable: true,
      render: (item) => <InventoryStatusBadge status={item.inventory_status} />,
    },
    {
      key: 'action',
      header: '操作',
      align: 'center',
      fixed: true,
      render: (item) => (
        <Link
          to={`/products/${item.product_id}`}
          onClick={() => onProductClick(item.product_id)}
          className="inline-flex items-center gap-0.5 text-xs text-[var(--accent-primary)] hover:underline"
        >
          详情
          <ChevronRight className="w-3 h-3" />
        </Link>
      ),
    },
  ];
}

const RankTables = memo(function RankTables({ top, bottom, category, onProductClick }: RankTablesProps) {
  const titleClass = "flex items-center gap-2 text-base font-semibold text-[var(--text-primary)] mb-4";
  const chipClass = "text-xs px-2 py-0.5 rounded-full bg-[var(--bg-surface-hover)] text-[var(--accent-primary)]";
  const columns = useMemo(() => createRankColumns(onProductClick), [onProductClick]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
        <div className={titleClass}>
          <ArrowUp className="w-5 h-5 text-[var(--accent-secondary)]" />
          Top 5 畅销品
          {category && <span className={chipClass}>{category}</span>}
        </div>
        <DataTable
          columns={columns}
          data={top}
          rowKey={(item) => item.product_id}
          skeletonRows={5}
        />
      </div>

      <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
        <div className={titleClass}>
          <ArrowDown className="w-5 h-5 text-[var(--accent-alert)]" />
          Bottom 5 滞销品
          {category && <span className={chipClass}>{category}</span>}
        </div>
        <DataTable
          columns={columns}
          data={bottom}
          rowKey={(item) => item.product_id}
          skeletonRows={5}
        />
      </div>
    </div>
  );
});

export default function DashboardPage() {
  const { storeId, range, category, setProductId } = useAnalysis();
  const [stores, setStores] = useState<Store[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [kpis, setKpis] = useState<KpiCardsProps['kpis'] | null>(null);
  const [dailySales, setDailySales] = useState<{ date: string; units_sold: number }[]>([]);
  const [top, setTop] = useState<RankingItem[]>([]);
  const [bottom, setBottom] = useState<RankingItem[]>([]);
  const [context, setContext] = useState<AnalysisContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const staleRef = useRef(false);

  const rangeDays = range === 'all' ? ALL_TIME_RANGE_DAYS : parseInt(range, 10);
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
        const [s, c, overview] = await Promise.all([
          api.getStores(controller.signal),
          api.getCategories(controller.signal),
          api.getOverview(storeId, range, category || undefined, controller.signal),
        ]);
        if (staleRef.current) return;
        setStores(s);
        setCategories(c);
        setContext(overview.context);
        setKpis(overview.data.kpis);
        setDailySales(overview.data.daily_sales);
        setTop(overview.data.top_products);
        setBottom(overview.data.bottom_products);
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
  }, [storeId, range, category, refreshKey]);

  const handleProductClick = (productId: string) => {
    setProductId(productId);
  };

  return (
    <div>
      {context && (
        <TitleBlock storeName={storeName} context={context} range={range} />
      )}

      <FilterBar stores={stores} categories={categories} />

      <DataState
        status={loading ? 'loading' : error ? 'error' : 'ready'}
        error={error}
        onRetry={() => setRefreshKey((k) => k + 1)}
      >
        {kpis && <KpiCards kpis={kpis} days={rangeDays} />}
        <TrendChart dailySales={dailySales} category={category} days={rangeDays} />
        <RankTables top={top} bottom={bottom} category={category} onProductClick={handleProductClick} />
      </DataState>
    </div>
  );
}
