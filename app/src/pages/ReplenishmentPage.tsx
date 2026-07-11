/**
 * 补货建议页 - ReplenishmentPage
 * 基于历史数据预测的 Top 5 畅销品补货建议
 */

import { useState, useEffect, memo } from 'react';
import { BarChart, Bar, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Package, AlertTriangle, CheckCircle, ArrowRight, RefreshCw, Calendar } from 'lucide-react';
import { api } from '@/services/api';
import StoreSelector from '@/components/StoreSelector';
import type { Store, ReplenishmentData, ReplenishmentSuggestion } from '@/types';

const cardStyle = { backgroundColor: 'var(--card-surface)', border: '1px solid var(--border-color)', borderRadius: '12px' } as const;

const fmt = (n?: number | null) => (n != null ? n.toLocaleString('zh-CN') : '0');
const fmtInt = (n?: number | null) => (n != null ? Math.round(n).toLocaleString('zh-CN') : '0');

const invStyle = (item: ReplenishmentSuggestion) => {
  const ratio = item.current_inventory / (item.total_predicted_demand || 1);
  if (ratio > 1.2) return { label: '充足', bg: 'var(--status-sufficient-bg)', c: 'var(--accent-secondary)' };
  if (ratio > 0.8) return { label: '正常', bg: 'var(--status-normal-bg)', c: 'var(--accent-primary)' };
  if (ratio > 0.5) return { label: '偏低', bg: 'var(--status-low-bg)', c: 'var(--accent-warning)' };
  return { label: '紧缺', bg: 'var(--status-critical-bg)', c: 'var(--accent-alert)' };
};

// ─── 子组件 ──────────────────────────────────────────────

interface MiniChartProps {
  predictions: number[];
  pid: string;
}

const MiniChart = memo(function MiniChart({ predictions, pid }: MiniChartProps) {
  const data = predictions.map((v, i) => ({ day: `${i + 1}`, value: v }));
  return (
    <div className="h-14 w-28">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barCategoryGap={2}>
          <Bar dataKey="value" radius={[2, 2, 0, 0]}>
            {predictions.map((_, i) => (
              <Cell key={`${pid}-${i}`} fill="var(--accent-primary)" fillOpacity={0.4 + i * 0.08} />
            ))}
          </Bar>
          <Tooltip
            contentStyle={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              fontSize: '11px',
              color: 'var(--text-primary)',
            }}
            formatter={(v: number) => [`${v}`, '预测']}
            labelFormatter={() => ''}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
});

interface SummaryCardsProps {
  data: ReplenishmentData;
}

const SummaryCards = memo(function SummaryCards({ data }: SummaryCardsProps) {
  const needCount = data.top_5_products.filter((p) => p.suggested_replenishment > 0).length;
  const total = data.top_5_products.reduce((s, p) => s + p.suggested_replenishment, 0);

  const items = [
    {
      title: '预测日期',
      value: data.forecast_date,
      icon: Calendar,
      color: 'var(--accent-primary)',
      bg: 'color-mix(in srgb, var(--accent-primary) 5%, transparent)',
      border: '1px solid color-mix(in srgb, var(--accent-primary) 15%, transparent)',
    },
    {
      title: '需补货商品',
      value: `${needCount} / 5`,
      icon: Package,
      color: 'var(--accent-warning)',
      bg: 'color-mix(in srgb, var(--accent-warning) 5%, transparent)',
      border: '1px solid color-mix(in srgb, var(--accent-warning) 15%, transparent)',
    },
    {
      title: '建议总补货量',
      value: fmtInt(total),
      icon: ArrowRight,
      color: 'var(--accent-purple)',
      bg: 'color-mix(in srgb, var(--accent-purple) 5%, transparent)',
      border: '1px solid color-mix(in srgb, var(--accent-purple) 15%, transparent)',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      {items.map((item) => (
        <div
          key={item.title}
          style={{ ...cardStyle, padding: '16px', background: item.bg, border: item.border }}
        >
          <div className="flex items-center gap-2 mb-2">
            <item.icon className="w-5 h-5" style={{ color: item.color }} />
            <span className="text-sm font-medium" style={{ color: item.color }}>{item.title}</span>
          </div>
          <p className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{item.value}</p>
        </div>
      ))}
    </div>
  );
});

interface ReplenishmentTableProps {
  products: ReplenishmentSuggestion[];
}

const headers = ['排名', '商品信息', '当前库存', '库存状态', '7天预测', '总需求', '建议补货'];

const ReplenishmentTable = memo(function ReplenishmentTable({ products }: ReplenishmentTableProps) {
  return (
    <div style={{ ...cardStyle, overflow: 'hidden' }}>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
              {headers.map((h) => (
                <th
                  key={h}
                  className="py-4 px-4 font-medium text-left"
                  style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map((item, idx) => {
              const st = invStyle(item);
              const need = item.suggested_replenishment > 0;
              return (
                <tr
                  key={item.product_id}
                  className="group hover:bg-[var(--table-row-hover)]"
                  style={{ borderBottom: '1px solid var(--border-subtle)' }}
                >
                  <td className="py-4 px-4">
                    <span
                      className="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold"
                      style={{ background: 'var(--status-normal-bg)', color: 'var(--accent-primary)' }}
                    >
                      {idx + 1}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{item.product_id}</div>
                    <div className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{item.category}</div>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{fmt(item.current_inventory)}</span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
                      style={{ background: st.bg, color: st.c }}
                    >
                      {st.label === '充足' && <CheckCircle className="w-3 h-3" />}
                      {(st.label === '紧缺' || st.label === '偏低') && <AlertTriangle className="w-3 h-3" />}
                      {st.label}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex justify-center">
                      <MiniChart predictions={item.predicted_demand_7d} pid={item.product_id} />
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{fmt(item.total_predicted_demand)}</span>
                  </td>
                  <td className="py-4 px-4 text-right">
                    {need ? (
                      <span
                        className="inline-flex items-center gap-1 text-lg font-bold"
                        style={{ color: 'var(--accent-warning)' }}
                      >
                        <Package className="w-4 h-4" /
                        >+{fmtInt(item.suggested_replenishment)}
                      </span>
                    ) : (
                      <span
                        className="inline-flex items-center gap-1 text-sm font-medium"
                        style={{ color: 'var(--accent-secondary)' }}
                      >
                        <CheckCircle className="w-4 h-4" /
                        >库存充足
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
});

// ─── 主组件 ──────────────────────────────────────────────

export default function ReplenishmentPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [storeId, setStoreId] = useState('S001');
  const [data, setData] = useState<ReplenishmentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let stale = false;

    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [s, d] = await Promise.all([
          api.getStores(controller.signal),
          api.getReplenishment(storeId, 1.2, controller.signal),
        ]);
        if (stale) return;
        setStores(s);
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
  }, [storeId, refreshKey]);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>补货建议</h2>
          <p className="text-sm mt-1" style={{ color: 'var(--text-tertiary)' }}>基于历史数据预测的 Top 5 畅销品补货建议</p>
        </div>
        <div className="flex items-center gap-3">
          <StoreSelector stores={stores} selectedStore={storeId} onChange={setStoreId} />
          <button
            type="button"
            onClick={() => setRefreshKey((k) => k + 1)}
            className="p-2 rounded-lg transition-colors"
            style={{ border: '1px solid var(--border-color)' }}
            title="刷新"
          >
            <RefreshCw className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2" style={{ borderColor: 'var(--accent-primary)' }} />
          <span className="ml-3 text-sm" style={{ color: 'var(--text-secondary)' }}>计算中...</span>
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
          <SummaryCards data={data} />
          <ReplenishmentTable products={data.top_5_products} />
          <div
            className="mt-6 rounded-xl p-4"
            style={{ background: 'var(--card-surface)', border: '1px solid var(--border-color)' }}
          >
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>计算说明:</strong>
              {' '}建议补货量 = max(0, 预测7天总需求 × 安全系数({data.safety_factor}) - 当前库存)。预测基于近期均值、星期模式和趋势调整的集成算法。
            </p>
          </div>
        </>
      )}
    </div>
  );
}
