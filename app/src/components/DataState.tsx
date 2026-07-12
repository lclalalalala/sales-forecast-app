/**
 * 数据状态组件 - DataState
 * =======================
 * 统一处理 loading / error / empty / 数据不可用状态。
 */

import type { ReactNode } from 'react';

interface DataStateProps {
  status: 'loading' | 'error' | 'empty' | 'insufficient_data' | 'forecast_unavailable' | 'ready';
  error?: string;
  onRetry?: () => void;
  children: ReactNode;
}

export default function DataState({
  status,
  error,
  onRetry,
  children,
}: DataStateProps) {
  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center py-20">
        <div
          className="animate-spin rounded-full h-10 w-10 border-b-2 border-[var(--accent-primary)]"
        />
        <span
          role="status"
          aria-live="polite"
          className="ml-3 text-sm text-[var(--text-secondary)]"
        >
          加载中...
        </span>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div
        className="rounded-xl p-4 mb-6 bg-[var(--status-critical-bg)] border border-[var(--status-bg-error)]"
      >
        <p role="status" aria-live="polite" className="text-[var(--accent-alert)]">{error || '加载失败，请稍后重试'}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 text-sm underline text-[var(--accent-alert)]"
          >
            重新加载
          </button>
        )}
      </div>
    );
  }

  if (status === 'empty') {
    return (
      <div
        className="rounded-xl p-8 text-center bg-[var(--card-surface)] border border-[var(--border-color)]"
      >
        <p role="status" aria-live="polite" className="text-[var(--text-secondary)]">当前筛选条件没有符合条件的数据</p>
      </div>
    );
  }

  if (status === 'insufficient_data' || status === 'forecast_unavailable') {
    return (
      <div
        className="rounded-xl p-4 mb-6 bg-[var(--status-low-bg)] border border-[var(--status-bg-warning)]"
      >
        <p role="status" aria-live="polite" className="text-[var(--accent-warning)]">
          {status === 'insufficient_data'
            ? '历史数据不足，无法生成可靠结果'
            : '预测服务暂不可用，该商品无法生成补货建议'}
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
