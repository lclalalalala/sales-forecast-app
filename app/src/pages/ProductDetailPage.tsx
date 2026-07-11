/**
 * 商品详情页 - ProductDetailPage
 * 含类别联动筛选、历史趋势与预测图表
 */

import { useState, useEffect, useMemo, useRef, memo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, BarChart, Bar,
} from 'recharts';
import {
  Package, AlertTriangle, CheckCircle, TrendingUp, DollarSign, Tag, Box, Filter,
} from 'lucide-react';
import { api } from '@/services/api';
import StoreSelector from '@/components/StoreSelector';
import type { Store, Product, ProductDetail, ProductHistoryRecord } from '@/types';

const cardS = { backgroundColor: 'var(--card-surface)', border: '1px solid var(--border-color)', borderRadius: '12px' } as const;

const fmt = (n?: number | null) => (n != null ? n.toLocaleString('zh-CN') : '-');
const fmtInt = (n?: number | null) => (n != null ? Math.round(n).toLocaleString('zh-CN') : '-');
const f1 = (n?: number | null) => (n != null && !Number.isNaN(n) ? n.toFixed(1) : '-');

const invStyle = (inv: number, pred7d: number) => {
  const ratio = inv / (pred7d / 7 || 1);
  if (ratio > 7) {
    return {
      bg: 'var(--status-sufficient-bg)',
      border: '1px solid color-mix(in srgb, var(--accent-secondary) 20%, transparent)',
      c: 'var(--accent-secondary)',
      label: '充足',
    };
  }
  if (ratio > 3) {
    return {
      bg: 'var(--status-low-bg)',
      border: '1px solid color-mix(in srgb, var(--accent-warning) 20%, transparent)',
      c: 'var(--accent-warning)',
      label: '偏低',
    };
  }
  return {
    bg: 'var(--status-critical-bg)',
    border: '1px solid color-mix(in srgb, var(--accent-error) 20%, transparent)',
    c: 'var(--accent-error)',
    label: '紧缺',
  };
};

interface InfoCardsProps {
  data: ProductDetail;
}

const InfoCards = memo(function InfoCards({ data }: InfoCardsProps) {
  const inv = invStyle(data.current_inventory, data.forecast.total_predicted);
  const replenish = data.forecast.suggested_replenishment > 0;
  const rep = replenish
    ? {
        bg: 'var(--status-low-bg)',
        border: '1px solid color-mix(in srgb, var(--accent-warning) 20%, transparent)',
        c: 'var(--accent-warning)',
      }
    : {
        bg: 'var(--status-sufficient-bg)',
        border: '1px solid color-mix(in srgb, var(--accent-secondary) 20%, transparent)',
        c: 'var(--accent-secondary)',
      };

  const cards = [
    {
      title: '当前库存',
      value: fmt(data.current_inventory),
      sub: inv.label,
      icon: Box,
      style: inv,
      isInv: true,
    },
    {
      title: '商品价格',
      value: `¥${f1(data.price)}`,
      sub: data.category,
      icon: DollarSign,
      style: {
        bg: 'var(--card-surface)',
        border: '1px solid var(--border-color)',
        c: 'var(--text-primary)',
      },
      isInv: false,
    },
    {
      title: '建议补货量',
      value: replenish ? `+${fmtInt(data.forecast.suggested_replenishment)}` : '充足',
      sub: `7天预测: ${fmt(data.forecast.total_predicted)}`,
      icon: Package,
      style: rep,
      isInv: false,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="p-5"
          style={{
            background: card.isInv ? inv.bg : card.style.bg,
            border: card.isInv ? inv.border : card.style.border,
            borderRadius: '12px',
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>{card.title}</span>
            <card.icon className="w-5 h-5" style={{ color: card.isInv ? inv.c : card.style.c }} />
          </div>
          <p
            className="text-3xl font-bold"
            style={{ color: card.isInv ? inv.c : card.style.c }}
          >
            {card.value}
          </p>
          <p className="text-xs mt-2" style={{ color: 'var(--text-secondary)' }}>
            {card.isInv && (
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                style={{ background: inv.bg, color: inv.c }}
              >
                {inv.label === '充足' && <CheckCircle className="w-3 h-3" />}
                {(inv.label === '紧缺' || inv.label === '偏低') && <AlertTriangle className="w-3 h-3" />}
                {inv.label}
              </span>
            )}
            {!card.isInv && card.sub}
          </p>
        </div>
      ))}
    </div>
  );
});

interface TrendChartProps {
  data: ProductHistoryRecord[];
}

const TrendChart = memo(function TrendChart({ data }: TrendChartProps) {
  return (
    <div style={{ ...cardS, padding: '20px', marginBottom: '24px' }}>
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5" style={{ color: 'var(--accent-primary)' }} />
        <h3 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>历史销售趋势 (过去3个月)</h3>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '12px' }} />
            <Legend wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} />
            <Line type="monotone" dataKey="units_sold" name="实际销量" stroke="var(--chart-sales)" strokeWidth={2} dot={false} activeDot={{ r: 3, fill: 'var(--chart-sales)' }} />
            <Line type="monotone" dataKey="demand" name="需求量" stroke="var(--chart-demand)" strokeWidth={2} strokeDasharray="4 4" dot={false} activeDot={{ r: 3, fill: 'var(--chart-demand)' }} />
            <Line type="monotone" dataKey="inventory" name="库存水位" stroke="var(--chart-inventory)" strokeWidth={1.5} dot={false} activeDot={{ r: 3, fill: 'var(--chart-inventory)' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

interface ForecastChartProps {
  days: number[];
}

const ForecastChart = memo(function ForecastChart({ days }: ForecastChartProps) {
  const data = useMemo(() => days.map((v, i) => ({ day: `第${i + 1}天`, predicted: v })), [days]);
  return (
    <div style={{ ...cardS, padding: '20px', marginBottom: '24px' }}>
      <div className="flex items-center gap-2 mb-4">
        <Package className="w-5 h-5" style={{ color: 'var(--accent-purple)' }} />
        <h3 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>未来7天预测需求</h3>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
            <XAxis dataKey="day" tick={{ fontSize: 12, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <YAxis tick={{ fontSize: 12, fill: 'var(--chart-axis-text)' }} tickLine={false} axisLine={{ stroke: 'var(--border-subtle)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '8px', color: 'var(--text-primary)', fontSize: '12px' }} formatter={(v: number) => [`${v}`, '预测需求']} />
            <Bar dataKey="predicted" name="预测需求量" fill="var(--chart-forecast)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-7 gap-2">
        {days.map((v, i) => (
          <div
            key={i}
            className="text-center rounded-lg py-2"
            style={{ background: 'color-mix(in srgb, var(--accent-purple) 8%, transparent)' }}
          >
            <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>第{i + 1}天</div>
            <div className="text-sm font-bold" style={{ color: 'var(--accent-purple)' }}>{f1(v)}</div>
          </div>
        ))}
      </div>
    </div>
  );
});

// ─── 主组件 ──────────────────────────────────────────────

export default function ProductDetailPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [storeId, setStoreId] = useState('S001');
  const [category, setCategory] = useState('');
  const [productId, setProductId] = useState('P0001');
  const [data, setData] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const productIdRef = useRef(productId);

  useEffect(() => {
    productIdRef.current = productId;
  }, [productId]);

  const filteredProducts = useMemo(() => {
    if (!category) return allProducts;
    return allProducts.filter((p) => p.category === category);
  }, [category, allProducts]);

  useEffect(() => {
    api.getStores().then(setStores).catch(console.error);
    api.getCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    let stale = false;
    api.getProducts(storeId)
      .then((prods) => {
        if (stale) return;
        setAllProducts(prods);
        const currentPid = productIdRef.current;
        if (prods.length > 0 && !prods.find((p) => p.id === currentPid)) {
          setProductId(prods[0].id);
        }
      })
      .catch(console.error);
    return () => { stale = true; };
  }, [storeId]);

  useEffect(() => {
    if (!productId) return;
    const controller = new AbortController();
    let stale = false;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const d = await api.getProductDetail(storeId, productId, 90, controller.signal);
        if (stale) return;
        setData(d);
      } catch (e: unknown) {
        if (stale) return;
        if ((e as Error)?.name !== 'AbortError') {
          setError((e as Error)?.message || '加载失败');
        }
      } finally {
        if (!stale) setLoading(false);
      }
    };

    load();
    return () => {
      stale = true;
      controller.abort();
    };
  }, [storeId, productId]);

  const handleCategoryChange = (next: string) => {
    setCategory(next);
    const pool = next ? allProducts.filter((p) => p.category === next) : allProducts;
    if (pool.length > 0 && !pool.find((p) => p.id === productId)) {
      setProductId(pool[0].id);
    }
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>商品详情</h2>
          <p className="text-sm mt-1" style={{ color: 'var(--text-tertiary)' }}>查看商品历史趋势、库存水位和补货建议</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <StoreSelector stores={stores} selectedStore={storeId} onChange={setStoreId} />
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
            <select
              value={category}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="rounded-lg px-3 py-1.5 text-xs outline-none cursor-pointer focus:ring-2 focus:ring-[var(--border-focus)] focus:border-[var(--border-focus)]"
              style={{ background: 'var(--card-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
            >
              <option value="">全部类别</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              className="rounded-lg px-3 py-1.5 text-xs outline-none cursor-pointer focus:ring-2 focus:ring-[var(--border-focus)] focus:border-[var(--border-focus)]"
              style={{ background: 'var(--card-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', minWidth: '140px' }}
            >
              {filteredProducts.map((p) => (
                <option key={p.id} value={p.id}>{p.id} - {p.category}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2" style={{ borderColor: 'var(--accent-primary)' }} />
          <span className="ml-3 text-sm" style={{ color: 'var(--text-secondary)' }}>加载中...</span>
        </div>
      )}

      {error && (
        <div
          className="rounded-xl p-4 mb-6"
          style={{ background: 'var(--status-critical-bg)', border: '1px solid var(--status-bg-error)' }}
        >
          <p style={{ color: 'var(--accent-alert)' }}>{error}</p>
        </div>
      )}

      {!loading && !error && data && (
        <>
          <div className="mb-6">
            <h3 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              {data.product_id}
              <span
                className="ml-3 text-xs font-normal px-2 py-1 rounded-md"
                style={{ background: 'var(--status-normal-bg)', color: 'var(--accent-primary)' }}
              >
                {data.category}
              </span>
            </h3>
          </div>

          <InfoCards data={data} />
          <TrendChart data={data.historical_sales} />
          <ForecastChart days={data.forecast.next_7_days} />
        </>
      )}
    </div>
  );
}
