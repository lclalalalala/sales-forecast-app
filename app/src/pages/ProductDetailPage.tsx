/**
 * 商品详情页 - ProductDetailPage
 * ==============================
 * 展示单个商品的历史销量、库存变化、未来 7 天预测与补货建议。
 * 支持级联商品选择器切换商品。
 */

import { useEffect, useMemo, useState, useRef, memo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  Package, TrendingUp, Box, ShoppingCart, Calculator,
} from 'lucide-react';
import { api } from '@/services/api';
import { isAbortError, getErrorMessage } from '@/lib/errors';
import { DEFAULT_PRODUCT_ID, PARAM_STORE_ID, PARAM_PRODUCT_ID, PARAM_QUANTITY } from '@/lib/constants';
import FilterBar from '@/components/FilterBar';
import InventoryStatusBadge from '@/components/InventoryStatusBadge';
import DataState from '@/components/DataState';
import KpiCard from '@/components/KpiCard';
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable';
import ReasonDrawer from '@/components/ReasonDrawer';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAnalysis } from '@/state/analysisContext';
import type { Store, Product, ProductDetail, ProductHistoryRecord } from '@/types';
import { cn } from '@/lib/utils';

const fmt = (n?: number | null) => (n != null && Number.isFinite(n) ? n.toLocaleString('zh-CN') : '-');
const f1 = (n?: number | null) => (n != null && Number.isFinite(n) && !Number.isNaN(n) ? n.toFixed(1) : '-');

interface SummaryCardsProps {
  data: ProductDetail;
  dailySales: number;
  avgDaily: number;
  forecast7Total: number;
}

const SummaryCards = memo(function SummaryCards({
  data,
  dailySales,
  avgDaily,
  forecast7Total,
}: SummaryCardsProps) {
  const r = data.replenishment ?? {};
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KpiCard
        icon={Package}
        label="商品编号"
        value={data.product_id}
        sub={data.category}
      />
      <KpiCard
        icon={TrendingUp}
        label="当日销量 / 日均销量"
        value={`${fmt(dailySales)} / ${f1(avgDaily)}`}
        sub="件/天"
      />
      <KpiCard
        icon={Box}
        label="当前库存 / 在途库存"
        value={`${fmt(data.current_inventory)} / ${fmt(data.in_transit_inventory)}`}
        sub={data.inventory_date || ''}
      />
      <KpiCard
        icon={ShoppingCart}
        label="未来 7 天预计销量 / 建议补货量"
        value={`${f1(forecast7Total)} / ${fmt(r.suggested_replenishment)}`}
        sub={`库存状态：${r.inventory_status}`}
      />
    </div>
  );
});

interface SalesChartProps {
  data: ProductHistoryRecord[];
}

const SalesChart = memo(function SalesChart({ data }: SalesChartProps) {
  if (!data?.length) return null;
  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-[var(--accent-primary)]" />
        <h3 className="text-base font-semibold text-[var(--text-primary)]">历史销量</h3>
      </div>
      <div className="h-72" role="img" aria-label="历史销量折线图">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
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
              activeDot={{ r: 3, fill: 'var(--chart-sales)' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

interface InventoryChartProps {
  data: ProductHistoryRecord[];
  safetyStock: number;
}

const InventoryChart = memo(function InventoryChart({ data, safetyStock }: InventoryChartProps) {
  if (!data?.length) return null;
  const lowStockLine = Math.max(0, safetyStock * 0.5);
  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Box className="w-5 h-5 text-[var(--accent-purple)]" />
        <h3 className="text-base font-semibold text-[var(--text-primary)]">历史库存变化</h3>
      </div>
      <div className="h-72" role="img" aria-label="历史库存变化折线图">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
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
            <ReferenceLine
              y={safetyStock}
              label={{ value: '安全库存', position: 'right', fill: 'var(--accent-warning)', fontSize: 10 }}
              stroke="var(--accent-warning)"
              strokeDasharray="5 5"
            />
            <ReferenceLine
              y={lowStockLine}
              label={{ value: '低库存线', position: 'right', fill: 'var(--accent-alert)', fontSize: 10 }}
              stroke="var(--accent-alert)"
              strokeDasharray="3 3"
            />
            <Line
              type="monotone"
              dataKey="inventory_level"
              name="库存水位"
              stroke="var(--chart-inventory)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, fill: 'var(--chart-inventory)' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

interface ForecastTableProps {
  data: ProductDetail;
}

const ForecastTable = memo(function ForecastTable({ data }: ForecastTableProps) {
  const rows = useMemo(() => {
    const forecast = data.forecast?.daily_forecast_units_sold ?? [];
    const interval = data.forecast?.prediction_interval ?? [];
    const currentInventory = data.current_inventory ?? 0;
    const safetyStock = data.replenishment?.safety_stock ?? 0;

    return forecast.reduce<
      { date: string; units_sold: number; lower: number; upper: number; projected_inventory: number; risk: boolean }[]
    >((acc, p, i) => {
      const prev = acc[acc.length - 1];
      const cumulative = (prev ? currentInventory - prev.projected_inventory : 0) + p.units_sold;
      const projected = Math.max(0, currentInventory - cumulative);
      const risk = projected <= safetyStock;
      return [
        ...acc,
        {
          date: p.date,
          units_sold: p.units_sold,
          lower: interval?.[i]?.lower ?? p.units_sold,
          upper: interval?.[i]?.upper ?? p.units_sold,
          projected_inventory: projected,
          risk,
        },
      ];
    }, []);
  }, [data]);

  const columns: DataTableColumn<typeof rows[number]>[] = [
    {
      key: 'date',
      header: '日期',
      sortable: true,
      render: (r) => <span className="text-[var(--text-primary)]">{r.date}</span>,
    },
    {
      key: 'units_sold',
      header: '预测销量',
      align: 'right',
      sortable: true,
      render: (r) => <span className="font-medium text-[var(--text-primary)]">{fmt(r.units_sold)}</span>,
    },
    {
      key: 'prediction_interval',
      header: '95% 预测区间',
      align: 'right',
      render: (r) => (
        <span className="text-xs text-[var(--text-secondary)]">
          [{fmt(r.lower)} , {fmt(r.upper)}]
        </span>
      ),
    },
    {
      key: 'projected_inventory',
      header: '预测库存变化',
      align: 'right',
      sortable: true,
      render: (r) => (
        <span className={cn('text-[var(--text-secondary)]', r.risk && 'text-[var(--accent-alert)] font-medium')}>
          {fmt(r.projected_inventory)}
        </span>
      ),
    },
    {
      key: 'risk',
      header: '库存风险',
      align: 'center',
      sortable: true,
      render: (r) => (
        r.risk ? (
          <span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-critical-bg)] text-[var(--accent-alert)]">
            有风险
          </span>
        ) : (
          <span className="inline-flex rounded-full px-2 py-0.5 text-xs bg-[var(--status-sufficient-bg)] text-[var(--accent-secondary)]">
            正常
          </span>
        )
      ),
    },
  ];

  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Package className="w-5 h-5 text-[var(--accent-purple)]" />
        <h3 className="text-base font-semibold text-[var(--text-primary)]">未来 7 天预测</h3>
      </div>
      <DataTable
        columns={columns}
        data={rows}
        rowKey={(r) => r.date}
      />
    </div>
  );
});

interface ReplenishmentSectionProps {
  data: ProductDetail;
  storeId: string;
}

const ReplenishmentSection = memo(function ReplenishmentSection({ data, storeId }: ReplenishmentSectionProps) {
  const r = data.replenishment ?? {};
  const forecast7Total = (data.forecast?.daily_forecast_units_sold ?? []).reduce(
    (sum, p) => sum + p.units_sold,
    0,
  );
  const orderLink = `/orders/new?${PARAM_STORE_ID}=${encodeURIComponent(storeId)}` +
    `&${PARAM_PRODUCT_ID}=${encodeURIComponent(data.product_id)}` +
    `&${PARAM_QUANTITY}=${encodeURIComponent(r.suggested_replenishment ?? 0)}`;

  return (
    <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <ShoppingCart className="w-5 h-5 text-[var(--accent-primary)]" />
        <h3 className="text-base font-semibold text-[var(--text-primary)]">补货建议</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
        <Metric label="未来 7 天预计销量" value={f1(forecast7Total)} unit="件" />
        <Metric label="当前售后库存" value={fmt(data.current_inventory)} unit="件" />
        <Metric label="在途库存" value={fmt(data.in_transit_inventory)} unit="件" />
        <Metric label="安全库存" value={fmt(r.safety_stock)} unit="件" />
        <Metric label="建议补货量" value={fmt(r.suggested_replenishment)} unit="件" highlight />
        <Metric label="库存状态" value={<InventoryStatusBadge status={r.inventory_status} />} />
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <ReasonDrawer
          productId={data.product_id}
          category={data.category}
          currentInventory={data.current_inventory}
          inTransitInventory={data.in_transit_inventory}
          leadTimeK={r.lead_time_k}
          leadTimeKSource={r.lead_time_k_source}
          forecastKTotal={r.forecast_k_total}
          safetyStock={r.safety_stock}
          suggestedReplenishment={r.suggested_replenishment}
          inventoryStatus={r.inventory_status}
        >
          <Button variant="outline" size="sm">
            <Calculator className="w-4 h-4 mr-1" />
            查看计算依据
          </Button>
        </ReasonDrawer>
        <Button asChild size="sm" className="bg-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/90">
          <Link to={orderLink}>
            <ShoppingCart className="w-4 h-4 mr-1" />
            去下单
          </Link>
        </Button>
      </div>
    </div>
  );
});

function Metric({
  label,
  value,
  unit,
  highlight,
}: {
  label: string;
  value: React.ReactNode;
  unit?: string;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-lg bg-[var(--bg-surface-hover)] p-3">
      <p className="text-[11px] text-[var(--text-tertiary)]">{label}</p>
      <div className={cn('text-sm font-semibold', highlight ? 'text-[var(--accent-primary)]' : 'text-[var(--text-primary)]')}>
        {value}
        {unit && <span className="ml-1 text-xs font-normal text-[var(--text-tertiary)]">{unit}</span>}
      </div>
    </div>
  );
}

export default function ProductDetailPage() {
  const { productId: routeProductId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const { storeId, range, category: globalCategory, setProductId } = useAnalysis();

  const [stores, setStores] = useState<Store[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [data, setData] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const staleRef = useRef(false);

  const productId = routeProductId || DEFAULT_PRODUCT_ID;

  useEffect(() => {
    if (routeProductId) setProductId(routeProductId);
  }, [routeProductId, setProductId]);

  useEffect(() => {
    staleRef.current = false;
    const controller = new AbortController();

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [s, c, productsRes, detail] = await Promise.all([
          api.getStores(controller.signal),
          api.getCategories(controller.signal),
          api.getProducts(storeId, globalCategory || undefined, controller.signal),
          api.getProductDetail(productId, storeId, range, controller.signal),
        ]);
        if (staleRef.current) return;
        setStores(s);
        setCategories(c);
        setProducts(productsRes);
        setData(detail.data);
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
  }, [productId, storeId, range, globalCategory, refreshKey]);

  const dailySales = useMemo(() => {
    if (!data?.historical_sales.length) return 0;
    return data.historical_sales[data.historical_sales.length - 1].units_sold;
  }, [data]);

  const avgDaily = useMemo(() => {
    if (!data?.historical_sales.length) return 0;
    const sum = data.historical_sales.reduce((acc, r) => acc + r.units_sold, 0);
    return sum / data.historical_sales.length;
  }, [data]);

  const forecast7Total = useMemo(() => {
    if (!data) return 0;
    return data.forecast?.daily_forecast_units_sold?.reduce((sum, p) => sum + p.units_sold, 0) ?? 0;
  }, [data]);

  const handleProductChange = (value: string) => {
    if (value && value !== productId) {
      navigate(`/products/${value}`);
    }
  };

  const storeName = useMemo(
    () => stores.find((s) => s.id === storeId)?.name || '',
    [stores, storeId],
  );

  return (
    <div>
      <div className="flex items-baseline gap-3 mb-6">
        <h2 className="text-2xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
          <Box className="w-6 h-6 text-[var(--accent-primary)]" />
          商品详情
        </h2>
        <span className="text-sm text-[var(--text-secondary)]">
          {storeName && storeName !== storeId ? `${storeId} · ${storeName}` : storeId}
        </span>
        {data && (
          <>
            <span className="text-sm font-medium text-[var(--text-primary)]">{data.product_id}</span>
            <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--bg-surface-hover)] text-[var(--accent-primary)]">
              {data.category}
            </span>
          </>
        )}
      </div>

      <FilterBar
        stores={stores}
        categories={categories}
        extra={
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">商品</span>
            <Select value={productId} onValueChange={handleProductChange}>
              <SelectTrigger className="h-9 text-xs w-[140px] bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-primary)]">
                <SelectValue placeholder="选择商品" />
              </SelectTrigger>
              <SelectContent className="bg-[var(--bg-surface)] border-[var(--border-subtle)]">
                {products.length === 0 && (
                  <SelectItem value="__empty__" disabled className="text-xs">
                    暂无商品
                  </SelectItem>
                )}
                {products.map((p) => (
                  <SelectItem key={p.id} value={p.id} className="text-xs focus:bg-[var(--bg-surface-hover)]">
                    {p.id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      <DataState
        status={loading ? 'loading' : error ? 'error' : 'ready'}
        error={error}
        onRetry={() => setRefreshKey((k) => k + 1)}
      >
        {data && (
          <>
            <SummaryCards
              data={data}
              dailySales={dailySales}
              avgDaily={avgDaily}
              forecast7Total={forecast7Total}
            />
            <SalesChart data={data.historical_sales} />
            <InventoryChart
              data={data.historical_sales}
              safetyStock={data.replenishment?.safety_stock ?? 0}
            />
            <ForecastTable data={data} />
            <ReplenishmentSection data={data} storeId={storeId} />
          </>
        )}
      </DataState>
    </div>
  );
}
