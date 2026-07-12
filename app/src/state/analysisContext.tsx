/**
 * 全局分析上下文 - AnalysisContext
 * ================================
 * 维护门店、时间范围、类别、库存状态、当前商品，并在 sessionStorage 与 URL 查询参数中持久化，
 * 实现跨页面筛选条件保持一致，且刷新/返回后可恢复。
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { useSearchParams } from 'react-router-dom';
import type { TimeRange } from '@/types';
import { DEFAULT_PRODUCT_ID, DEFAULT_TIME_RANGE } from '@/lib/constants';

const STORAGE_KEY = 'sephora-analysis-context';

export interface AnalysisState {
  storeId: string;
  range: TimeRange;
  category: string;
  inventoryStatus: string;
  productId: string;
}

interface AnalysisContextValue extends AnalysisState {
  setStoreId: (id: string) => void;
  setRange: (range: TimeRange) => void;
  setCategory: (category: string) => void;
  setInventoryStatus: (status: string) => void;
  setProductId: (id: string) => void;
  resetFilters: () => void;
}

const DEFAULT_STATE: AnalysisState = {
  storeId: 'S001',
  range: DEFAULT_TIME_RANGE,
  category: '',
  inventoryStatus: '',
  productId: DEFAULT_PRODUCT_ID,
};

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

function isValidRange(value: string): value is TimeRange {
  return ['7d', '30d', '90d', '180d', 'all'].includes(value);
}

function loadStoredState(): Partial<AnalysisState> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed: unknown = JSON.parse(raw);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        const obj = parsed as Record<string, unknown>;
        const result: Partial<AnalysisState> = {};
        if (typeof obj.storeId === 'string') result.storeId = obj.storeId;
        if (typeof obj.range === 'string' && isValidRange(obj.range)) result.range = obj.range;
        if (typeof obj.category === 'string') result.category = obj.category;
        if (typeof obj.inventoryStatus === 'string') result.inventoryStatus = obj.inventoryStatus;
        if (typeof obj.productId === 'string') result.productId = obj.productId;
        return result;
      }
    }
  } catch {
    // ignore
  }
  return {};
}

function parseUrlParams(searchParams: URLSearchParams): Partial<AnalysisState> {
  const parsed: Partial<AnalysisState> = {};
  const store = searchParams.get('store');
  if (store) parsed.storeId = store;

  const range = searchParams.get('range');
  if (range && isValidRange(range)) parsed.range = range;

  const category = searchParams.get('category');
  if (category) parsed.category = category === 'all' ? '' : category;

  const inventoryStatus = searchParams.get('inventory_status');
  if (inventoryStatus) parsed.inventoryStatus = inventoryStatus;

  const product = searchParams.get('product');
  if (product) parsed.productId = product;

  return parsed;
}

function buildInitialState(searchParams: URLSearchParams): AnalysisState {
  // 优先级：URL 参数 > sessionStorage > 默认值
  const fromStorage = loadStoredState();
  const fromUrl = parseUrlParams(searchParams);
  return { ...DEFAULT_STATE, ...fromStorage, ...fromUrl };
}

const MANAGED_KEYS = ['store', 'range', 'category', 'inventory_status', 'product'] as const;

function buildSearchParams(state: AnalysisState, current?: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams();
  // 保留上下文不管理的查询参数（如下单页的 store_id / product_id / quantity）
  if (current) {
    current.forEach((value, key) => {
      if (!MANAGED_KEYS.includes(key as (typeof MANAGED_KEYS)[number])) {
        next.set(key, value);
      }
    });
  }
  if (state.storeId && state.storeId !== DEFAULT_STATE.storeId) {
    next.set('store', state.storeId);
  }
  if (state.range && state.range !== DEFAULT_STATE.range) {
    next.set('range', state.range);
  }
  if (state.category) {
    next.set('category', state.category);
  }
  if (state.inventoryStatus) {
    next.set('inventory_status', state.inventoryStatus);
  }
  if (state.productId && state.productId !== DEFAULT_STATE.productId) {
    next.set('product', state.productId);
  }
  return next;
}

interface AnalysisProviderProps {
  children: ReactNode;
}

export function AnalysisProvider({ children }: AnalysisProviderProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, setState] = useState<AnalysisState>(() =>
    buildInitialState(searchParams),
  );

  useEffect(() => {
    // 浏览器前进/后退或外链改变 URL 时，将 URL 参数反向同步到 context state
    const fromUrl = parseUrlParams(searchParams);
    setState((prev) => {
      const next = { ...prev, ...fromUrl };
      const changed = (Object.keys(fromUrl) as (keyof AnalysisState)[]).some(
        (k) => prev[k] !== next[k],
      );
      return changed ? next : prev;
    });
  }, [searchParams]);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  useEffect(() => {
    const current = new URLSearchParams(searchParams);
    const next = buildSearchParams(state, current);
    if (next.toString() !== current.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [state, searchParams, setSearchParams]);

  const setStoreId = useCallback((storeId: string) => {
    setState((prev) => ({ ...prev, storeId }));
  }, []);

  const setRange = useCallback((range: TimeRange) => {
    setState((prev) => ({ ...prev, range }));
  }, []);

  const setCategory = useCallback((category: string) => {
    setState((prev) => ({ ...prev, category }));
  }, []);

  const setInventoryStatus = useCallback((inventoryStatus: string) => {
    setState((prev) => ({ ...prev, inventoryStatus }));
  }, []);

  const setProductId = useCallback((productId: string) => {
    setState((prev) => ({ ...prev, productId }));
  }, []);

  const resetFilters = useCallback(() => {
    setState(DEFAULT_STATE);
  }, []);

  const value = useMemo(
    () => ({
      ...state,
      setStoreId,
      setRange,
      setCategory,
      setInventoryStatus,
      setProductId,
      resetFilters,
    }),
    [state, setStoreId, setRange, setCategory, setInventoryStatus, setProductId, resetFilters],
  );

  return (
    <AnalysisContext.Provider
      value={value}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis(): AnalysisContextValue {
  const ctx = useContext(AnalysisContext);
  if (!ctx) {
    throw new Error('useAnalysis 必须在 AnalysisProvider 内使用');
  }
  return ctx;
}
