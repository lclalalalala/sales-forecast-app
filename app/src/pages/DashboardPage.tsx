/**
 * 数据概览页 - DashboardPage
 * 含多维筛选工具栏、KPI、趋势图与排名表格
 */

import { useState, useEffect, useRef, memo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp, TrendingDown, Package, RotateCw,
  ArrowUp, ArrowDown, Medal, AlertTriangle, CheckCircle,
  Filter,
} from 'lucide-react';
import { api } from '@/services/api';
import StoreSelector from '@/components/StoreSelector';
import type { Store, SalesTrendData, RankingData, KpiData, ProductRanking } from '@/types';

const TIME_OPTIONS = [
  { value: 7, label: '7天' },
  { value: 30, label: '30天' },
  { value: 90, label: '90天' },
  { value: 180, label: '180天' },
  { value: 759, label: '全部' },
] as const;

const INV_STATUS = [
  { value: '', label: '全部' },
  { value: '充足', label: '充足' },
  { value: '正常', label: '正常' },
  { value: '偏低', label: '偏低' },
  { value: '紧缺', label: '紧缺' },
] as const;

const cardBase = {
  backgroundColor: 'var(--card-surface)',
  border: '1px solid var(--border-color)',
  borderRadius: '12px',
} as const;

const fmt = (n?: number | null) => (n != null ? n.toLocaleString('zh-CN') : '-');
const f1 = (n?: number | null) => (n != null && !Number.isNaN(n) ? n.toFixed(1) : '-');

const statusStyle = (s?: string) => {
  switch (s) {
    case '充足': return { bg: 'var(--status-sufficient-bg)', c: 'var(--accent-secondary)' };
    case '正常': return { bg: 'var(--status-normal-bg)', c: 'var(--accent-primary)' };
    case '偏低': return { bg: 'var(--status-low-bg)', c: 'var(--accent-warning)' };
    case '紧缺': return { bg: 'var(--status-critical-bg)', c: 'var(--accent-alert)' };
    default: return { bg: 'var(--bg-surface-hover)', c: 'var(--text-secondary)' };
  }
};

// ─── 子组件 ──────────────────────────────────────────────

interface FilterBarProps {
  stores: Store[];
  storeId: string;
  onStoreChange: (id: string) => void;
  days: number;
  onDaysChange: (days: number) => void;
  categories: string[];
  category: string;
  onCategoryChange: (category: string) => void;
  invStatus: string;
  onInvStatusChange: (status: string) => void;
}

const FilterBar = memo(function FilterBar({
  stores, storeId, onStoreChange, days, onDaysChange,
  categories, category, onCategoryChange, invStatus, onInvStatusChange,
}: FilterBarProps) {
  return (
    <div style={{ ...cardBase, padding: '16px 20px', marginBottom: '24px' }}>
      <div className="flex items-center gap-2 mb-3">
        <Filter className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
        <span className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>
          筛选条件
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <StoreSelector stores={stores} selectedStore={storeId} onChange={onStoreChange} />

        {/* 时间范围 */}
        <div className="flex items-center gap-2">
          <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>时间</span>
          <div
            className="flex rounded-lg p-0.5"
            style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)' }}
          >
            {TIME_OPTIONS.map((o) => {
              const active = days === o.value;
              return (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => onDaysChange(o.value)}
                  className="px-3 py-1.5 text-xs rounded-md transition-colors"
                  style={{
                    background: active ? 'var(--card-surface)' : 'transparent',
                    color: active ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                    fontWeight: active ? 500 : 400,
                    boxShadow: active ? 'var(--shadow-dropdown)' : 'none',
                  }}
                >
                  {o.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 类别 */}
        <div className="flex items-center gap-2">
          <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>类别</span>
          <select
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="rounded-lg px-3 py-1.5 text-xs outline-none cursor-pointer transition-colors focus:ring-2 focus:ring-[var(--border-focus)]"
            style={{ background: 'var(--card-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
          >
            <option value="">全部</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* 库存状态 */}
        <div className="flex items-center gap-2">
          <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>库存</span>
          <select
            value={invStatus}
            onChange={(e) => onInvStatusChange(e.target.value)}
            className="rounded-lg px-3 py-1.5 text-xs outline-none cursor-pointer transition-colors focus:ring-2 focus:ring-[var(--border-focus)]"
            style={{ background: 'var(--card-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
          >
            {INV_STATUS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
});

interface KpiCardsProps {
  kpi: KpiData;
  days: number;
}

const KpiCards = memo(function KpiCards({ kpi, days }: KpiCardsProps) {
  const up = kpi.avg_daily_sales > 0;
  const items = [
    {
      label: `${days >= 759 ? '总' : days + '天总'}销量`,
      val: fmt(kpi.total_sales),
      icon: Package,
      iconBg: 'var(--status-normal-bg)',
      iconC: 'var(--accent-primary)',
    },
    {
      label: '日均销量',
      val: f1(kpi.avg_daily_sales),
      icon: up ? TrendingUp : TrendingDown,
      iconBg: up ? 'var(--status-sufficient-bg)' : 'var(--status-critical-bg)',
      iconC: up ? 'var(--accent-secondary)' : 'var(--accent-alert)',
    },
    {
      label: '活跃商品',
      val: fmt(kpi.active_products),
      icon: Package,
      iconBg: 'var(--status-bg-info)',
      iconC: 'var(--accent-purple)',
    },
    {
      label: '平均库存',
      val: f1(kpi.avg_inventory),
      icon: RotateCw,
      iconBg: 'var(--status-low-bg)',
      iconC: 'var(--accent-warning)',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {items.map((item) => (
        <div
          key={item.label}
          className="group"
          style={{ ...cardBase, padding: '20px', cursor: 'default' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span
              className="text-xs font-medium uppercase tracking-wider transition-colors group-hover:text-[var(--text-primary)]"
              style={{ color: 'var(--text-tertiary)' }}
            >
              {item.label}
            </span>
            <div
              className="p-2 rounded-lg transition-transform group-hover:scale-110"
              style={{ background: item.iconBg }}
            >
              <item.icon className="w-5 h-5" style={{ color: item.iconC }} />
            </div>
          </div>
          <p
            className="text-3xl font-bold transition-transform group-hover:translate-x-1"
            style={{ color: 'var(--text-primary)' }}
          >
            {item.val}
          </p>
        </div>
      ))}
    </div>
  );
});

interface TrendChartProps {
  trend: SalesTrendData;
  category: string;
  days: number;
}

const TrendChart = memo(function TrendChart({ trend, category, days }: TrendChartProps) {
  if (!trend?.daily_sales?.length) return null;
  return (
    <div style={{ ...cardBase, padding: '20px', marginBottom: '24px' }}>
      <h3 className="text-base font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
        {category || '全部商品'} 销售趋势
        {days < 759 && (
          <span className="text-sm font-normal ml-2" style={{ color: 'var(--text-tertiary)' }}>
            (近{days}天)
          </span>
        )}
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trend.daily_sales} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                fontSize: '12px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} />
            <Line type="monotone" dataKey="units_sold" name="实际销量" stroke="var(--chart-sales)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'var(--chart-sales)' }} />
            <Line type="monotone" dataKey="demand" name="需求量" stroke="var(--chart-demand)" strokeWidth={2} strokeDasharray="5 5" dot={false} activeDot={{ r: 4, fill: 'var(--chart-demand)' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

interface RankTablesProps {
  ranking: RankingData;
  category: string;
}

const tableHeaders = ['排名', '商品', '类别', '总销量', '日均', '库存状态'];

const RankTables = memo(function RankTables({ ranking, category }: RankTablesProps) {
  const renderTable = (title: string, items: ProductRanking[], isTop: boolean) => (
    <div style={{ ...cardBase, padding: '20px' }}>
      <div className="flex items-center gap-2 mb-4">
        {isTop ? (
          <ArrowUp className="w-5 h-5" style={{ color: 'var(--accent-secondary)' }} />
        ) : (
          <ArrowDown className="w-5 h-5" style={{ color: 'var(--accent-alert)' }} />
        )}
        <h3 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</h3>
        {category && (
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: 'var(--status-normal-bg)', color: 'var(--accent-primary)' }}
          >
            {category}
          </span>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              {tableHeaders.map((h) => (
                <th
                  key={h}
                  className="text-left py-3 px-2 font-medium"
                  style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => {
              const sc = statusStyle(item.inventory_status);
              const isFirstTop = isTop && idx === 0;
              return (
                <tr
                  key={item.product_id}
                  className="group hover:bg-[var(--table-row-hover)]"
                  style={{ borderBottom: '1px solid var(--border-subtle)' }}
                >
                  <td className="py-3 px-2">
                    {isFirstTop ? (
                      <Medal className="w-4 h-4" style={{ color: 'var(--accent-warning)' }} />
                    ) : (
                      <span style={{ color: 'var(--text-secondary)' }}>{item.rank}</span>
                    )}
                  </td>
                  <td className="py-3 px-2 font-medium" style={{ color: 'var(--text-primary)' }}>
                    {item.product_id}
                  </td>
                  <td className="py-3 px-2">
                    <span
                      className="px-2 py-0.5 rounded-full text-xs"
                      style={{ background: 'var(--status-normal-bg)', color: 'var(--accent-primary)' }}
                    >
                      {item.category}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right font-medium" style={{ color: 'var(--text-primary)' }}>
                    {fmt(item.total_sold)}
                  </td>
                  <td className="py-3 px-2 text-right" style={{ color: 'var(--text-secondary)' }}>
                    {f1(item.avg_daily)}
                  </td>
                  <td className="py-3 px-2">
                    {item.inventory_status && (
                      <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                        style={{ background: sc.bg, color: sc.c }}
                      >
                        {item.inventory_status === '充足' && <CheckCircle className="w-3 h-3" />}
                        {(item.inventory_status === '紧缺' || item.inventory_status === '偏低') && <AlertTriangle className="w-3 h-3" />}
                        {item.inventory_status}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {renderTable('Top 5 畅销品', ranking.top_5, true)}
      {renderTable('Bottom 5 滞销品', ranking.bottom_5, false)}
    </div>
  );
});

// ─── 主组件 ──────────────────────────────────────────────

export default function DashboardPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [storeId, setStoreId] = useState('S001');
  const [days, setDays] = useState(90);
  const [category, setCategory] = useState('');
  const [invStatus, setInvStatus] = useState('');
  const [kpi, setKpi] = useState<KpiData | null>(null);
  const [trend, setTrend] = useState<SalesTrendData | null>(null);
  const [ranking, setRanking] = useState<RankingData | null>(null);
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
        const [s, c, k, t, r] = await Promise.all([
          api.getStores(controller.signal),
          api.getCategories(controller.signal),
          api.getDashboardKpi(storeId, days, controller.signal),
          api.getSalesTrend(storeId, days, category || undefined, controller.signal),
          api.getSalesRanking(storeId, days, category || undefined, invStatus || undefined, controller.signal),
        ]);
        if (staleRef.current) return;
        setStores(s);
        setCategories(c);
        setKpi(k);
        setTrend(t);
        setRanking(r);
      } catch (e: unknown) {
        if (staleRef.current) return;
        if ((e as Error)?.name !== 'AbortError') {
          setError((e as Error)?.message || '加载失败，请稍后重试');
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
  }, [storeId, days, category, invStatus, refreshKey]);

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>数据概览</h2>
        <p className="text-sm mt-1" style={{ color: 'var(--text-tertiary)' }}>多维筛选查看门店销售趋势和商品排名</p>
      </div>

      <FilterBar
        stores={stores}
        storeId={storeId}
        onStoreChange={setStoreId}
        days={days}
        onDaysChange={setDays}
        categories={categories}
        category={category}
        onCategoryChange={setCategory}
        invStatus={invStatus}
        onInvStatusChange={setInvStatus}
      />

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div
            className="animate-spin rounded-full h-10 w-10 border-b-2"
            style={{ borderColor: 'var(--accent-primary)' }}
          />
          <span className="ml-3 text-sm" style={{ color: 'var(--text-secondary)' }}>加载中...</span>
        </div>
      )}

      {error && (
        <div
          className="rounded-xl p-4 mb-6"
          style={{ background: 'var(--status-critical-bg)', border: '1px solid var(--status-bg-error)' }}
        >
          <p style={{ color: 'var(--accent-alert)' }}>{error}</p>
          <button
            type="button"
            onClick={() => setRefreshKey((k) => k + 1)}
            className="mt-2 text-sm underline"
            style={{ color: 'var(--accent-alert)' }}
          >
            重新加载
          </button>
        </div>
      )}

      {!loading && !error && kpi && trend && ranking && (
        <>
          <KpiCards kpi={kpi} days={days} />
          <TrendChart trend={trend} category={category} days={days} />
          <RankTables ranking={ranking} category={category} />
        </>
      )}
    </div>
  );
}
