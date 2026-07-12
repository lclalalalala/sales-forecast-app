/**
 * Sparkline 迷你趋势图
 * ====================
 * 用于表格内展示预测趋势或销量趋势。
 */

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  YAxis,
  Tooltip,
} from 'recharts';
import { cn } from '@/lib/utils';

interface SparklineProps {
  data: number[];
  labels?: string[];
  color?: string;
  className?: string;
  height?: number;
}

export default function Sparkline({
  data = [],
  labels,
  color = 'var(--accent-primary)',
  className,
  height = 40,
}: SparklineProps) {
  const chartData = data.map((value, index) => ({
    index,
    value,
    label: labels?.[index] ?? index,
  }));

  const hasData = data.length > 0;

  if (!hasData) {
    return (
      <div
        className={cn(
          'flex items-center justify-center text-xs text-[var(--text-tertiary)]',
          className,
        )}
        style={{ height }}
      >
        无数据
      </div>
    );
  }

  return (
    <div
      className={cn('w-full', className)}
      style={{ height }}
      role="img"
      aria-label="迷你趋势图"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <YAxis domain={['dataMin', 'dataMax']} hide />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload as { label: string | number; value: number };
                return (
                  <div className="rounded-md border bg-[var(--bg-surface)] border-[var(--border-subtle)] px-2 py-1 text-xs shadow-sm">
                    <div className="text-[var(--text-secondary)]">{String(item.label)}</div>
                    <div className="font-medium text-[var(--text-primary)]">
                      预测销量：{item.value} 件
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            fill={color}
            fillOpacity={0.15}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
