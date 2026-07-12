/**
 * 库存状态徽章 - InventoryStatusBadge
 * ===================================
 */

import { CheckCircle, AlertTriangle, MinusCircle } from 'lucide-react';
import type { InventoryStatusKey } from '@/types';

interface InventoryStatusBadgeProps {
  status: InventoryStatusKey;
}

const STATUS_META: Record<
  InventoryStatusKey,
  { label: string; bg: string; color: string; icon: typeof CheckCircle }
> = {
  sufficient: {
    label: '充足',
    bg: 'var(--status-sufficient-bg)',
    color: 'var(--accent-secondary)',
    icon: CheckCircle,
  },
  normal: {
    label: '正常',
    bg: 'var(--status-normal-bg)',
    color: 'var(--accent-primary)',
    icon: CheckCircle,
  },
  low: {
    label: '偏低',
    bg: 'var(--status-low-bg)',
    color: 'var(--accent-warning)',
    icon: AlertTriangle,
  },
  critical: {
    label: '紧缺',
    bg: 'var(--status-critical-bg)',
    color: 'var(--accent-alert)',
    icon: AlertTriangle,
  },
  undetermined: {
    label: '未知',
    bg: 'var(--bg-surface-hover)',
    color: 'var(--text-secondary)',
    icon: MinusCircle,
  },
};

export default function InventoryStatusBadge({ status }: InventoryStatusBadgeProps) {
  const meta = STATUS_META[status] || STATUS_META.undetermined;
  const Icon = meta.icon;

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
      style={{ background: meta.bg, color: meta.color }}
    >
      <Icon className="w-3 h-3" />
      {meta.label}
    </span>
  );
}
