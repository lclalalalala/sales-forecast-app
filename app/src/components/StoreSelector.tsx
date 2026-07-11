/**
 * 门店选择器组件 - StoreSelector
 */

import { useId } from 'react';
import { Store } from 'lucide-react';
import type { Store as StoreType } from '@/types';

interface StoreSelectorProps {
  stores: StoreType[];
  selectedStore: string;
  onChange: (storeId: string) => void;
  label?: string;
}

export default function StoreSelector({
  stores,
  selectedStore,
  onChange,
  label = '门店',
}: StoreSelectorProps) {
  const selectId = useId();

  return (
    <div className="flex items-center gap-2">
      <Store className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
      <label
        htmlFor={selectId}
        className="text-sm font-medium"
        style={{ color: 'var(--text-secondary)' }}
      >
        {label}
      </label>
      <select
        id={selectId}
        value={selectedStore}
        onChange={(e) => onChange(e.target.value)}
        className="block rounded-lg px-3 py-1.5 text-sm cursor-pointer outline-none transition-all focus:ring-2 focus:ring-[var(--border-focus)] focus:border-[var(--border-focus)]"
        style={{
          backgroundColor: 'var(--card-surface)',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-color)',
          minWidth: '120px',
        }}
      >
        {stores.map((store) => (
          <option key={store.id} value={store.id}>
            {store.name} ({store.region})
          </option>
        ))}
      </select>
    </div>
  );
}
