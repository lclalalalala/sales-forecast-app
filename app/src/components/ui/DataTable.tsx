/**
 * DataTable 可排序表格
 * ====================
 * 基于 shadcn/ui Table 封装，支持表头排序、加载骨架、空状态、固定操作列。
 */

import { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

export interface DataTableColumn<T> {
  key: string;
  header: React.ReactNode;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  width?: string;
  fixed?: boolean;
  render: (row: T, index: number) => React.ReactNode;
}

interface DataTableProps<T extends object> {
  columns: DataTableColumn<T>[];
  data: T[];
  loading?: boolean;
  skeletonRows?: number;
  emptyTitle?: string;
  emptyDescription?: string;
  onReset?: () => void;
  className?: string;
  rowKey: (row: T, index: number) => string | number;
}

type SortDirection = 'asc' | 'desc' | null;

interface SortState {
  key: string | null;
  direction: SortDirection;
}

export default function DataTable<T extends object>({
  columns,
  data,
  loading = false,
  skeletonRows = 5,
  emptyTitle = '当前筛选条件下暂无商品数据',
  emptyDescription = '请尝试切换门店、类别或时间范围',
  onReset,
  className,
  rowKey,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<SortState>({ key: null, direction: null });

  const sortedData = useMemo(() => {
    if (!sort.key || !sort.direction) return data;
    const col = columns.find((c) => c.key === sort.key);
    if (!col || !col.sortable) return data;

    return [...data].sort((a, b) => {
      const aValue = (a as Record<string, unknown>)[sort.key!];
      const bValue = (b as Record<string, unknown>)[sort.key!];
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sort.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }
      const aStr = String(aValue ?? '');
      const bStr = String(bValue ?? '');
      return sort.direction === 'asc'
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });
  }, [data, sort, columns]);

  const handleSort = (key: string, sortable?: boolean) => {
    if (!sortable) return;
    setSort((prev) => {
      if (prev.key !== key) return { key, direction: 'desc' };
      if (prev.direction === 'desc') return { key, direction: 'asc' };
      return { key: null, direction: null };
    });
  };

  const renderSortIcon = (key: string) => {
    if (sort.key !== key) return <ArrowUpDown className="w-3 h-3 text-[var(--text-tertiary)]" />;
    if (sort.direction === 'asc') return <ArrowUp className="w-3 h-3 text-[var(--accent-primary)]" />;
    return <ArrowDown className="w-3 h-3 text-[var(--accent-primary)]" />;
  };

  return (
    <div className={cn('rounded-xl border border-[var(--border-subtle)] overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-[var(--bg-surface-hover)]">
            <TableRow>
              {columns.map((col) => (
                <TableHead
                  key={col.key}
                  scope="col"
                  aria-sort={col.sortable ? (sort.key === col.key ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none') : undefined}
                  className={cn(
                    'text-[var(--text-secondary)] text-xs font-medium whitespace-nowrap',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.fixed && 'sticky right-0 bg-[var(--bg-surface-hover)]',
                  )}
                  style={{ width: col.width }}
                >
                  {col.sortable ? (
                    <button
                      type="button"
                      onClick={() => handleSort(col.key, col.sortable)}
                      className={cn(
                        'flex items-center gap-1 w-full',
                        col.align === 'right' && 'justify-end',
                      )}
                    >
                      {col.header}
                      {renderSortIcon(col.key)}
                    </button>
                  ) : (
                    <div className={cn('flex items-center gap-1', col.align === 'right' && 'justify-end')}>
                      {col.header}
                    </div>
                  )}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: skeletonRows }).map((_, i) => (
                <TableRow key={`skeleton-${i}`}>
                  {columns.map((col) => (
                    <TableCell key={col.key}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : sortedData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-32 text-center">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <p className="text-sm font-medium text-[var(--text-secondary)]">
                      {emptyTitle}
                    </p>
                    <p className="text-xs text-[var(--text-tertiary)]">
                      {emptyDescription}
                    </p>
                    {onReset && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-2"
                        onClick={onReset}
                      >
                        恢复默认条件
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              sortedData.map((row, index) => (
                <TableRow
                  key={rowKey(row, index)}
                  className="hover:bg-[var(--bg-surface-hover)] transition-colors"
                >
                  {columns.map((col) => (
                    <TableCell
                      key={col.key}
                      className={cn(
                        'text-sm text-[var(--text-primary)] whitespace-nowrap',
                        col.align === 'right' && 'text-right',
                        col.align === 'center' && 'text-center',
                        col.fixed && 'sticky right-0 bg-[var(--bg-surface)]',
                      )}
                    >
                      {col.render(row, index)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
