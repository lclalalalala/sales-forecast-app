/**
 * KPI 卡片组件
 * ============
 * 图标 + 指标名称 + 数值 + 辅助说明。
 */

import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  icon: LucideIcon;
  label: string;
  value: React.ReactNode;
  subtext?: string;
  sub?: string;
  className?: string;
}

export default function KpiCard({
  icon: Icon,
  label,
  value,
  subtext,
  sub,
  className,
}: KpiCardProps) {
  const subLabel = subtext ?? sub;
  return (
    <div
      className={cn(
        'rounded-xl border p-5 transition-shadow',
        'bg-[var(--bg-surface)] border-[var(--border-subtle)]',
        'hover:shadow-[var(--shadow-card-hover)]',
        className,
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--text-secondary)]">
            {label}
          </p>
          <div className="mt-2 text-2xl font-semibold text-[var(--text-primary)]">
            {value}
          </div>
          {subLabel && (
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">
              {subLabel}
            </p>
          )}
        </div>
        <div className="rounded-lg p-2 bg-[var(--bg-surface-hover)]">
          <Icon className="w-5 h-5 text-[var(--accent-primary)]" />
        </div>
      </div>
    </div>
  );
}
